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
from typing import NamedTuple, Optional, Sequence


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


_BATCH_PROMPT = (
    "You are grading a BATCH of stored agent memories against a single source-of-truth. "
    "Return a single JSON ARRAY on ONE line. Each element: "
    '{"index": <int>, "verdict": "fresh"|"stale"|"wrong", "reason": "<=20 words"}.\n\n'
    "fresh = memory accurately reflects source\n"
    "stale = memory was once true but source has moved on\n"
    "wrong = memory contradicts source / was never true\n"
)

_CONTRADICTION_PROMPT = (
    "You are a contradiction detector. Answer in a single JSON object on ONE line: "
    '{"contradicts": true|false, "reason": "<=20 words"}. '
    "contradicts=true means the NEW memory directly negates / replaces / refutes the OLD one.\n"
)


def grade_batch(
    candidates: Sequence[tuple],
    source_text: str,
    model: str = "claude-haiku-4-5-20251001",
    prefer: str = "auto",
) -> list:
    """Batch-grade multiple memories with ONE Haiku call. Cherry-picked from
    jcode batch pattern (recommendation from Sub-D audit, brain entry
    jcode-memory-audit-and-cherry-picks-2026-05-25).

    Args:
      candidates  : sequence of (id, text) tuples
      source_text : single shared source-of-truth
      model       : Anthropic model id
      prefer      : "auto" | "online" | "heuristic"

    Returns: list of Verdict (same order as `candidates`).
    Cost: ~1x Haiku call total instead of N x Haiku calls.
    """
    from .cluster import jaccard, tokenize

    if not candidates:
        return []

    modes = available_modes()
    use_online = (prefer == "online") or (prefer == "auto" and modes["online"])

    if not use_online:
        src_toks = tokenize(source_text)
        out: list = []
        for _id, text in candidates:
            j = jaccard(tokenize(text), src_toks)
            v = "fresh" if j >= 0.6 else ("stale" if j < 0.25 else "fresh")
            out.append(Verdict(verdict=v, reason=f"jaccard={j:.2f}", model="heuristic-jaccard", cost_estimate_usd=0.0))
        return out

    try:
        import anthropic
    except ImportError:
        return [Verdict("ungraded", "anthropic SDK not installed", "none", 0.0) for _ in candidates]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return [Verdict("ungraded", "ANTHROPIC_API_KEY not set", "none", 0.0) for _ in candidates]

    items: list[str] = []
    for i, (_id, text) in enumerate(candidates):
        snip = (text or "")[:500]
        items.append(f"[{i}] {snip}")
    user_block = "SOURCE:\n" + (source_text or "(no source)")[:6000] + "\n\nMEMORIES:\n" + "\n".join(items)
    user_block = user_block[:12000]

    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=800,
            system=_BATCH_PROMPT,
            messages=[{"role": "user", "content": user_block}],
        )
    except Exception as exc:  # noqa: BLE001
        return [Verdict("ungraded", f"haiku batch failed: {type(exc).__name__}", model, 0.0) for _ in candidates]

    raw = ""
    try:
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                raw += getattr(block, "text", "")
    except Exception:  # noqa: BLE001
        pass

    import json
    parsed: list = []
    verdicts_by_idx: dict[int, dict] = {}
    try:
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            arr = json.loads(raw[start : end + 1])
            for item in arr:
                if isinstance(item, dict) and "index" in item:
                    verdicts_by_idx[int(item["index"])] = item
    except (json.JSONDecodeError, ValueError, KeyError):
        pass

    cost_total = 0.00005
    cost_per_item = cost_total / max(1, len(candidates))
    for i, _ in enumerate(candidates):
        item = verdicts_by_idx.get(i)
        if item:
            parsed.append(Verdict(
                verdict=str(item.get("verdict", "ungraded")).lower(),
                reason=str(item.get("reason", ""))[:200],
                model=model,
                cost_estimate_usd=cost_per_item,
            ))
        else:
            parsed.append(Verdict("ungraded", "no verdict in batch response", model, cost_per_item))
    return parsed


def check_contradiction(
    new_text: str,
    old_text: str,
    model: str = "claude-haiku-4-5-20251001",
    prefer: str = "auto",
) -> tuple:
    """Returns (contradicts: bool, reason: str). Used by supersede.mark_edge(check_contradiction=True).

    HEURISTIC: jaccard >= 0.4 AND negation-token asymmetry -> True.
    ONLINE: single Haiku call returning {"contradicts": bool, "reason": str}.
    """
    from .cluster import jaccard, tokenize

    modes = available_modes()
    use_online = (prefer == "online") or (prefer == "auto" and modes["online"])

    if not use_online:
        tn = tokenize(new_text)
        to = tokenize(old_text)
        j = jaccard(tn, to)
        if j < 0.4:
            return False, f"jaccard {j:.2f} too low; different topics"
        neg = {"not", "no", "never", "stop", "remove", "removed", "deprecated", "disabled", "wrong", "ban", "banned", "deleted"}
        new_neg = tn & neg
        old_neg = to & neg
        if (new_neg and not old_neg) or (old_neg and not new_neg):
            return True, f"negation asymmetry: new={sorted(new_neg)} old={sorted(old_neg)}"
        return False, f"jaccard {j:.2f}, no negation asymmetry"

    try:
        import anthropic
    except ImportError:
        return False, "anthropic SDK not installed (heuristic-skip)"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "ANTHROPIC_API_KEY not set (heuristic-skip)"

    user = f"NEW:\n{(new_text or '')[:3000]}\n\nOLD:\n{(old_text or '')[:3000]}"
    try:
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=120,
            system=_CONTRADICTION_PROMPT,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"haiku failed: {type(exc).__name__}"

    raw = ""
    try:
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                raw += getattr(block, "text", "")
    except Exception:  # noqa: BLE001
        pass

    import json
    try:
        s = raw.find("{")
        e = raw.rfind("}")
        if s >= 0 and e > s:
            obj = json.loads(raw[s : e + 1])
            return bool(obj.get("contradicts")), str(obj.get("reason", ""))[:200]
    except (json.JSONDecodeError, ValueError):
        pass
    return False, "no parseable verdict"


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
