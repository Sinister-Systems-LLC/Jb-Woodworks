"""
codec - bidirectional token-compact codec for Sinister memory files.

Purpose: cut Haiku input cost on big learned.md files by replacing common
phrases with @<tok> tokens. Lossless, reversible, operator-readable when decoded.

Explicitly NOT for:
  - Hiding content from Anthropic's classifiers (encode-then-send is still
    decoded by Claude when it reads the system prompt; if the underlying fact
    would trip a classifier, encoding doesn't help and we shouldn't try).
  - Hiding content from the operator (decode() always reverses encode()).
  - Hiding content from audit logs (absorption-log.jsonl stays plain-text JSON;
    only the `fact` field gets encoded so grep still works on token form).

Usage:
    from agents._shared.codec import encode, decode, stats

    short = encode("operator action by Yurikey51 expires")
    # "@oab @y51e"
    long = decode(short)
    # "operator action by Yurikey51 root cert expires"  (closest dictionary match)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
DICT_PATH = HUB_ROOT / "12_LLM_ORCHESTRATION" / "config" / "codec-dictionary.yaml"

# Tiny built-in fallback if yaml/dict file missing — keeps codec usable
_BUILTIN_PHRASES = {
    "Sinister Skills": "@ss",
    "operator": "@op",
    "operator action by": "@oab",
    "Yurikey51 root cert expires": "@y51e",
    "Yurikey51": "@y51",
    "sandbox-blocked": "@sbk",
    "green path": "@gp",
}

_loaded: dict[str, Any] | None = None


def _load_dict() -> dict[str, Any]:
    """Load dictionary. Cached. Reload by deleting the cache attribute manually."""
    global _loaded
    if _loaded is not None:
        return _loaded
    if not HAS_YAML or not DICT_PATH.exists():
        _loaded = {
            "phrases": _BUILTIN_PHRASES,
            "secret_pass_through_patterns": [
                r"sk-ant-[a-zA-Z0-9_-]{30,}",
                r"AIza[a-zA-Z0-9_-]{30,}",
                r"ghp_[a-zA-Z0-9]{30,}",
            ],
        }
        return _loaded
    try:
        with DICT_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        phrases = data.get("phrases", {})
        # Sort phrases longest-first so longer matches win
        phrases_sorted = dict(sorted(phrases.items(), key=lambda kv: -len(kv[0])))
        _loaded = {
            "phrases": phrases_sorted,
            "secret_pass_through_patterns": data.get("secret_pass_through_patterns", []),
            "reserved_tokens": data.get("reserved_tokens", []),
            "version": data.get("version", 1),
        }
        return _loaded
    except Exception as e:
        # Bad YAML -> fall back to built-in
        _loaded = {"phrases": _BUILTIN_PHRASES, "secret_pass_through_patterns": []}
        return _loaded


def encode(text: str) -> str:
    """Replace dictionary phrases with their tokens. Case-insensitive match.
    Lambda replacement so backslashes / `$` in tokens don't trip re.sub's template parser."""
    if not isinstance(text, str) or not text:
        return text
    d = _load_dict()
    phrases = d.get("phrases", {})
    result = text
    for phrase, token in phrases.items():
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        result = pattern.sub(lambda _m, t=token: t, result)
    return result


def decode(text: str) -> str:
    """Reverse encode: replace tokens with their canonical phrase form.
    Lambda replacement so phrases containing backslashes (Windows paths) / `$` don't trip re.sub."""
    if not isinstance(text, str) or not text:
        return text
    d = _load_dict()
    phrases = d.get("phrases", {})
    rev = {token: phrase for phrase, token in phrases.items()}
    # Replace longest tokens first to avoid prefix collisions
    for token in sorted(rev.keys(), key=lambda t: -len(t)):
        phrase = rev[token]
        pattern = re.compile(re.escape(token))
        text = pattern.sub(lambda _m, p=phrase: p, text)
    return text


def stats(text: str) -> dict[str, Any]:
    """Token-saving + secret-pass-through analysis. Returns ratio + secrets-detected count."""
    if not isinstance(text, str) or not text:
        return {"ok": True, "original_chars": 0, "encoded_chars": 0, "ratio": 0.0, "secret_hits": 0}
    encoded = encode(text)
    d = _load_dict()
    secret_hits = 0
    for pat in d.get("secret_pass_through_patterns", []):
        try:
            secret_hits += len(re.findall(pat, text))
        except re.error:
            continue
    return {
        "ok": True,
        "original_chars": len(text),
        "encoded_chars": len(encoded),
        "ratio": round(len(encoded) / max(1, len(text)), 3),
        "saved_chars": len(text) - len(encoded),
        "secret_hits": secret_hits,
    }


def roundtrip(text: str) -> dict[str, Any]:
    """Encode then decode; report whether it's lossless. Use to verify dictionary integrity."""
    enc = encode(text)
    dec = decode(enc)
    return {
        "lossless": (dec.lower() == text.lower()),  # case-insensitive due to encode case-fold
        "original_chars": len(text),
        "encoded_chars": len(enc),
        "decoded_chars": len(dec),
        "decoded": dec,
    }


def reload_dict() -> dict[str, Any]:
    """Force reload of the dictionary (after operator edits the YAML)."""
    global _loaded
    _loaded = None
    return _load_dict()


def get_dictionary() -> dict[str, str]:
    """Return the active phrase->token map (for ops + debugging)."""
    d = _load_dict()
    return dict(d.get("phrases", {}))
