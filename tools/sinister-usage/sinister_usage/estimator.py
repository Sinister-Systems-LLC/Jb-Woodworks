# Sinister Sanctum :: sinister-usage :: estimator
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Stdlib-only token-count estimator. Trade-off: deliberately NO tiktoken
dependency — that pulls in regex + cython compile chain. Our heuristic
overestimates by ~5-10% vs cl100k_base on English prose; close enough for
back-of-envelope quota math.

Heuristic:
- Treat whitespace + punctuation runs as boundaries.
- Each "token" = chars/4 (BPE rule-of-thumb), but lower-bound = word count.
- Add small fixed overhead per non-ASCII char (CJK / emoji push BPE up).
"""
from __future__ import annotations
import re
from typing import Any

SCHEMA_VERSION = "sinister.usage.estimator.v1"

# Word boundary: any run of non-letter / non-digit / non-underscore chars
_WORD_RE = re.compile(r"\w+", re.UNICODE)
# Non-ASCII (anything outside basic Latin) costs ~1.3x in BPE
_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")


def estimate_tokens(text: str) -> int:
    """Estimate token count for arbitrary text. Stdlib-only.

    Returns max(words, ceil(chars/4) + non_ascii_penalty). 0-length safe.
    """
    if not text:
        return 0
    chars = len(text)
    words = len(_WORD_RE.findall(text))
    non_ascii = len(_NON_ASCII_RE.findall(text))
    chars_estimate = (chars + 3) // 4
    non_ascii_penalty = (non_ascii + 1) // 2
    return max(words, chars_estimate + non_ascii_penalty)


def estimate_text_breakdown(text: str) -> dict[str, Any]:
    """Detailed breakdown for `sinister-usage estimate --verbose`."""
    if not text:
        return {
            "chars": 0,
            "words": 0,
            "lines": 0,
            "non_ascii": 0,
            "tokens_estimate": 0,
            "schema_version": SCHEMA_VERSION,
        }
    return {
        "chars": len(text),
        "words": len(_WORD_RE.findall(text)),
        "lines": text.count("\n") + 1,
        "non_ascii": len(_NON_ASCII_RE.findall(text)),
        "tokens_estimate": estimate_tokens(text),
        "schema_version": SCHEMA_VERSION,
    }
