# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
"""
Sinister Sanctum :: Codex Companion (OpenAI-powered peer-review skill)

A thin wrapper around the OpenAI SDK that lets a Claude agent ask a Codex-grade
model "is this correct, secure, well-designed?" and receive structured feedback.

Public surface:
    review(content, *, context="", language="python", depth="standard") -> dict

Depth tiers:
    quick     -> gpt-4o-mini    (cheap, 30s budget)
    standard  -> gpt-4o         (balanced, 60s budget)   [default]
    deep      -> o1-mini        (deep reasoning, 180s budget)

Returns one of:
    {ok: True,  verdict: pass|warn|fail,
     findings: [{severity:high|medium|low, area, body}, ...],
     summary: <one paragraph>,
     log_path: <abs path>, model: <id>, depth: <tier>, elapsed_s: <float>}
    {ok: False, error: <str>, log_path?: <abs path>}

Graceful failure modes:
    - OPENAI_API_KEY missing  -> {ok: False, error: "no API key - set OPENAI_API_KEY"}
    - openai package missing  -> {ok: False, error: "openai SDK not installed ..."}
    - API call failure        -> {ok: False, error: <error string>}
    - malformed JSON reply    -> retries ONCE; if still malformed, returns ok=False

Every successful review is persisted to:
    D:\\Sinister Sanctum\\_shared-memory\\codex-reviews\\<UTC-iso>-<sha1-of-content>.json

CLI:
    python tools/codex-companion/codex.py --review path/to/file.py [--depth standard]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- constants --------------------------------------------------------------

SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
LOG_DIR = SANCTUM_ROOT / "_shared-memory" / "codex-reviews"

DEPTH_MAP: dict[str, dict[str, Any]] = {
    "quick":    {"model": "gpt-4o-mini",  "timeout": 30.0,  "max_tokens": 1500},
    "standard": {"model": "gpt-4o",       "timeout": 60.0,  "max_tokens": 2500},
    "deep":     {"model": "o1-mini",      "timeout": 180.0, "max_tokens": 4000},
}

SYSTEM_PROMPT = (
    "You are Codex, a code review specialist. You peer-review code written by "
    "another AI agent (Claude). Your job is to determine if the code is correct, "
    "secure, well-designed, and free of obvious bugs or smells. Be terse, blunt, "
    "and concrete. Cite line ranges or symbol names where possible.\n"
    "\n"
    "You MUST return strict JSON only - no prose, no code fences, no preamble. "
    "Schema:\n"
    '{\n'
    '  "verdict":  "pass" | "warn" | "fail",\n'
    '  "findings": [\n'
    '    {"severity": "high" | "medium" | "low", "area": "<short label>", '
    '"body": "<concrete description + recommendation>"}\n'
    '  ],\n'
    '  "summary":  "<one-paragraph overall assessment>"\n'
    '}\n'
    "\n"
    "Verdict guide:\n"
    "  pass = no high-severity findings, ship it\n"
    "  warn = ship-able after addressing findings, or risk-accepted by operator\n"
    "  fail = BLOCK push - high-severity issue (security, correctness, data loss)"
)


# --- helpers ----------------------------------------------------------------

def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha1_short(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:10]


def _log_path_for(content: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR / f"{_utc_iso()}-{_sha1_short(content)}.json"


def _persist(log_path: Path, payload: dict[str, Any]) -> None:
    """Write the review JSON to disk. Best-effort - never raises."""
    try:
        log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    except Exception:
        pass


def _build_user_prompt(content: str, context: str, language: str) -> str:
    parts = [f"LANGUAGE: {language}"]
    if context.strip():
        parts.append(f"CONTEXT:\n{context.strip()}")
    parts.append("CODE / DIFF TO REVIEW:\n```\n" + content + "\n```")
    parts.append(
        "Return JSON only matching the schema. Do not wrap in code fences. "
        "Do not include any text outside the JSON object."
    )
    return "\n\n".join(parts)


def _validate_shape(obj: Any) -> tuple[bool, str]:
    if not isinstance(obj, dict):
        return False, "top-level is not an object"
    if obj.get("verdict") not in ("pass", "warn", "fail"):
        return False, f"verdict must be pass|warn|fail, got: {obj.get('verdict')!r}"
    findings = obj.get("findings")
    if not isinstance(findings, list):
        return False, "findings must be a list"
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            return False, f"finding[{i}] is not an object"
        if f.get("severity") not in ("high", "medium", "low"):
            return False, f"finding[{i}].severity must be high|medium|low"
        if not isinstance(f.get("area"), str) or not isinstance(f.get("body"), str):
            return False, f"finding[{i}].area and .body must be strings"
    if not isinstance(obj.get("summary"), str):
        return False, "summary must be a string"
    return True, ""


def _parse_response(raw: str) -> tuple[bool, Any, str]:
    """Try to parse the model's reply as the expected JSON shape.
    Returns (ok, parsed_or_None, err)."""
    text = raw.strip()
    # Strip code fences if the model ignored instructions.
    if text.startswith("```"):
        # remove first fence line + last fence line
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        obj = json.loads(text)
    except Exception as e:
        return False, None, f"JSON parse error: {e}"
    ok, err = _validate_shape(obj)
    if not ok:
        return False, obj, err
    return True, obj, ""


def _call_openai(client: Any, *, model: str, system: str, user: str,
                 timeout: float, max_tokens: int) -> tuple[bool, str, str]:
    """Single OpenAI Chat Completions call. Returns (ok, raw_text, err).

    NOTE: this is the only place we touch the OpenAI SDK; it is intentionally
    kept thin so the rest of the module stays testable without the network.
    """
    try:
        # o1-* family rejects `temperature` and `max_tokens` (uses
        # `max_completion_tokens`). gpt-4o family accepts the classic kwargs.
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            "timeout": timeout,
        }
        if model.startswith("o1"):
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = 0.1
            # Encourage JSON-only when the model supports it (gpt-4o family does).
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        text = (resp.choices[0].message.content or "").strip()
        return True, text, ""
    except Exception as e:
        return False, "", f"{type(e).__name__}: {e}"


# --- public API -------------------------------------------------------------

def review(content: str, *, context: str = "", language: str = "python",
           depth: str = "standard") -> dict[str, Any]:
    """Peer-review the given code/diff via an OpenAI Codex-grade model.

    Args:
        content:  the code blob or unified diff to review (required).
        context:  optional free-form context (what's this for, what changed, etc.).
        language: source language hint (python/typescript/rust/go/...).
        depth:    quick | standard | deep. See DEPTH_MAP.

    Returns: dict matching the schema documented at module top.
    """
    if not isinstance(content, str) or not content.strip():
        return {"ok": False, "error": "content is empty"}

    cfg = DEPTH_MAP.get(depth)
    if cfg is None:
        return {"ok": False, "error": f"unknown depth {depth!r} (use quick|standard|deep)"}

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {"ok": False, "error": "no API key - set OPENAI_API_KEY"}

    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        return {"ok": False,
                "error": f"openai SDK not installed (pip install openai>=1.20.0): {e}"}

    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        return {"ok": False, "error": f"OpenAI client init failed: {e}"}

    user_prompt = _build_user_prompt(content, context, language)
    started = time.time()

    raw_attempts: list[str] = []
    parse_errors: list[str] = []
    parsed: dict[str, Any] | None = None

    for attempt in (1, 2):
        ok, raw, err = _call_openai(
            client,
            model=cfg["model"],
            system=SYSTEM_PROMPT,
            user=user_prompt if attempt == 1 else (
                user_prompt + "\n\nREMINDER: return STRICT JSON only "
                "matching the schema. Previous reply did not parse: "
                + (parse_errors[-1] if parse_errors else "(unknown)")
            ),
            timeout=cfg["timeout"],
            max_tokens=cfg["max_tokens"],
        )
        if not ok:
            return {"ok": False, "error": err, "model": cfg["model"], "depth": depth}
        raw_attempts.append(raw)
        good, obj, perr = _parse_response(raw)
        if good:
            parsed = obj  # type: ignore[assignment]
            break
        parse_errors.append(perr)

    elapsed = round(time.time() - started, 3)
    log_path = _log_path_for(content)

    if parsed is None:
        err_payload = {
            "ok": False,
            "error": "model returned malformed JSON after retry",
            "parse_errors": parse_errors,
            "raw_attempts": raw_attempts,
            "model": cfg["model"],
            "depth": depth,
            "elapsed_s": elapsed,
            "log_path": str(log_path),
        }
        _persist(log_path, err_payload)
        return err_payload

    record = {
        "ok": True,
        "verdict": parsed["verdict"],
        "findings": parsed["findings"],
        "summary": parsed["summary"],
        "model": cfg["model"],
        "depth": depth,
        "language": language,
        "context": context,
        "content_sha1": hashlib.sha1(content.encode("utf-8", errors="replace")).hexdigest(),
        "content_len": len(content),
        "elapsed_s": elapsed,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "log_path": str(log_path),
    }
    _persist(log_path, record)
    return record


# --- CLI --------------------------------------------------------------------

def _cli() -> int:
    p = argparse.ArgumentParser(
        prog="codex",
        description="Sinister Sanctum :: Codex Companion peer-review CLI."
    )
    p.add_argument("--review", required=True, metavar="PATH",
                   help="Path to a source file (or '-' for stdin) to review.")
    p.add_argument("--depth", default="standard", choices=("quick", "standard", "deep"),
                   help="Review depth (default: standard).")
    p.add_argument("--context", default="",
                   help="Free-form context to pass to Codex.")
    p.add_argument("--language", default="",
                   help="Language hint (auto-detected from extension if omitted).")
    args = p.parse_args()

    if args.review == "-":
        content = sys.stdin.read()
        lang = args.language or "text"
    else:
        path = Path(args.review)
        if not path.exists():
            print(f"[FAIL] no such file: {path}", file=sys.stderr)
            return 2
        content = path.read_text(encoding="utf-8", errors="replace")
        ext_to_lang = {
            ".py": "python", ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript", ".rs": "rust",
            ".go": "go", ".java": "java", ".rb": "ruby", ".cs": "csharp",
            ".cpp": "cpp", ".c": "c", ".h": "c", ".hpp": "cpp",
            ".sh": "bash", ".ps1": "powershell", ".sql": "sql",
            ".md": "markdown", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        }
        lang = args.language or ext_to_lang.get(path.suffix.lower(), "text")

    result = review(content, context=args.context, language=lang, depth=args.depth)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result.get("ok"):
        return 1
    return 0 if result.get("verdict") != "fail" else 3


if __name__ == "__main__":
    sys.exit(_cli())
