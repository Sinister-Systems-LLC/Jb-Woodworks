# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: verify.

Feature-detected Haiku-grader wrapper. Grades a stored memory against the
current state of the corresponding source-of-truth (a brain row, a PROGRESS
entry, a file in the repo) and returns a verdict in {fresh, stale, wrong,
ungraded}.

Three execution modes:
  1. ONLINE  -- `anthropic` SDK importable AND `ANTHROPIC_API_KEY` set
                -> call Haiku, parse verdict
  2. HEURISTIC -- no SDK / no key BUT we have access to the source file
                -> jaccard(memory_tokens, source_tokens) -> {fresh|stale}
  3. OFFLINE -- neither -> verdict='ungraded', reason='no grader available'

Conservative by design: the caller decides WHEN to verify (NOT every recall hit;
typically on iter-close + before promoting a memory to brain). One grader call
per invocation -- no batching, no auto-retry, no implicit budget burn.

Public API:
  Verdict NamedTuple (verdict, reason, model, cost_estimate_usd)
  verify_memory(memory_text, source_text=None, model="claude-haiku-4-5-20251001") -> Verdict
  available_modes() -> dict[str, bool]   # diagnostic helper
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import NamedTuple, Optional


class Verdict(NamedTuple):
    verdict: str        # "fresh" | "stale" | "wrong" | "ungraded"
    reason: str
    model: str          # "claude-haiku-4-5-20251001" | "heuristic-jaccard" | "none"
    cost_estimate_usd: float  # 0.0 for heuristic/offline; tiny positive for Haiku


_GRADER_PROMPT = (
    "You are grading a stored agent memory against the current state of its "
    "source-of-truth. Return a single JSON object on ONE line with keys: "
    "verdict (one of: fresh, stale, wrong), reason (<=30 words).\n\n"
    "fresh = memory accurately reflects source\n"
    "stale = memory was once true but source has moved on\n"
    "wrong = memory contradicts source / was never true\n"
)

_VERDICT_RE = re.compile(r'"verdict"\s*:\s*"(fresh|stale|wrong)"', re.IGNORECASE)
_REASON_RE = re.compile(r'"reason"\s*:\s*"([^"]{1,400})"')


def available_modes() -> dict:
    """Tell the caller which verify modes are usable right now."""
    sdk_ok = False
    try:
        import anthropic  # noqa: F401
        sdk_ok = True
    except ImportError:
        pass
    return {
        "online": sdk_ok and bool(os.environ.get("ANTHROPIC_API_KEY")),
        "heuristic": True,
        "offline": True,
    }


def _heuristic_grade(memory_text: str, source_text: str, stale_threshold: float = 0.25) -> Verdict:
    """Jaccard-token overlap. >= 0.6 -> fresh; < stale_threshold -> stale; else fresh-ish."""
    from .cluster import jaccard, tokenize

    j = jaccard(tokenize(memory_text), tokenize(source_text))
    if j >= 0.6:
        verdict = "fresh"
    elif j < stale_threshold:
        verdict = "stale"
    else:
        verdict = "fresh"
    return Verdict(
        verdict=verdict,
        reason=f"jaccard={j:.2f} (>=0.6=fresh; <{stale_threshold}=stale)",
        model="heuristic-jaccard",
        cost_estimate_usd=0.0,
    )


def _online_grade(memory_text: str, source_text: Optional[str], model: str) -> Verdict:
    """Call Haiku via anthropic SDK. Returns Verdict; on any error returns ungraded.

    Caller is responsible for not flooding -- this function does ONE call, no retry.
    """
    try:
        import anthropic
    except ImportError:
        return Verdict("ungraded", "anthropic SDK not installed", "none", 0.0)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return Verdict("ungraded", "ANTHROPIC_API_KEY not set", "none", 0.0)

    user_block = f"MEMORY:\n{memory_text}\n\nSOURCE:\n{source_text or '(no source provided)'}"
    user_block = user_block[:8000]  # clamp

    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=200,
            system=_GRADER_PROMPT,
            messages=[{"role": "user", "content": user_block}],
        )
    except Exception as exc:  # noqa: BLE001 -- top-level grader guard
        return Verdict("ungraded", f"haiku call failed: {type(exc).__name__}", model, 0.0)

    # Parse response
    raw = ""
    try:
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                raw += getattr(block, "text", "")
    except Exception:  # noqa: BLE001
        pass

    m_verdict = _VERDICT_RE.search(raw or "")
    m_reason = _REASON_RE.search(raw or "")
    verdict = (m_verdict.group(1).lower() if m_verdict else "ungraded")
    reason = (m_reason.group(1) if m_reason else (raw[:200] if raw else "no parseable verdict"))

    # Conservative cost estimate: Haiku ~ $1/Mtok input, $5/Mtok output. We sent ~8k chars in / max 200 tok out.
    cost = 0.000020  # ~2e-5 USD per call; tunable, NOT precise

    return Verdict(verdict=verdict, reason=reason, model=model, cost_estimate_usd=cost)


def verify_memory(
    memory_text: str,
    source_text: Optional[str] = None,
    source_path: Optional[Path] = None,
    model: str = "claude-haiku-4-5-20251001",
    prefer: str = "auto",
) -> Verdict:
    """Grade a memory against its source. Returns Verdict.

    Args:
      memory_text  : the stored memory body
      source_text  : current source-of-truth text. If None and source_path is set,
                     reads the file. If both None, online mode still possible (just
                     asks Haiku to grade the memory standalone, but lower quality).
      source_path  : alternative to source_text -- pass a path, we read it
      model        : Anthropic model id (default Haiku 4.5)
      prefer       : "auto" (online if available, else heuristic), "heuristic"
                     (always jaccard), "online" (force online; ungraded if no key)

    Cost: 0.0 for heuristic/offline; ~2e-5 USD for one Haiku call.
    """
    if source_text is None and source_path is not None:
        try:
            source_text = Path(source_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            source_text = None

    modes = available_modes()

    if prefer == "online" or (prefer == "auto" and modes["online"]):
        return _online_grade(memory_text, source_text, model)

    if source_text is not None:
        return _heuristic_grade(memory_text, source_text)

    return Verdict(
        verdict="ungraded",
        reason="no source_text/source_path provided and online mode unavailable",
        model="none",
        cost_estimate_usd=0.0,
    )
