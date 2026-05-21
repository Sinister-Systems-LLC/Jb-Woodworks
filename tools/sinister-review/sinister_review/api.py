# Sinister Sanctum :: sinister-review :: core API
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Disk-first scaffolding for the autoreview / autojudge pattern (jcode parity).
LLM backend is caller-provides in v0.1.0 (dispatch_llm raises NotImplementedError);
v0.2.0 wires per agent-host-routing.md.
"""

from __future__ import annotations
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "sinister.review.v1"
_AUTHOR = "RKOJ-ELENO :: 2026-05-21"
DEFAULT_REVIEWS_ROOT = Path(
    os.environ.get(
        "SINISTER_REVIEWS_ROOT",
        r"D:\Sinister Sanctum\_shared-memory\reviews",
    )
)
_root: Path = DEFAULT_REVIEWS_ROOT


def set_reviews_root(p):
    global _root
    _root = Path(p)


def get_reviews_root() -> Path:
    return _root


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _detect_my_slug():
    s = os.environ.get("SINISTER_AGENT_SLUG")
    if s:
        return s
    n = os.environ.get("SINISTER_AGENT_NAME")
    if n:
        return n.lower().replace(" ", "-")
    return "unknown-caller"


def _safe(s):
    return re.sub(r"[^A-Za-z0-9_-]+", "-", s)[:48]


def _persist(verdict_record):
    _root.mkdir(parents=True, exist_ok=True)
    stamp = _stamp()
    from_slug = verdict_record.get("from", _detect_my_slug())
    topic = _safe(verdict_record.get("kind", "review") + "-" + (verdict_record.get("input", {}).get("summary", "")[:24] or "x"))
    path = _root / f"{stamp}-{from_slug}-{topic}.json"
    path.write_text(json.dumps(verdict_record, indent=2, default=str), encoding="utf-8")
    verdict_record["_path"] = str(path)
    return verdict_record


def dispatch_llm(prompt, *, model="opus-4-7", max_tokens=4000):
    """STUB v0.1.0 - raises NotImplementedError. Wire per agent-host-routing.md in v0.2.0.

    Suggested wiring options:
    - Anthropic SDK call (`anthropic.messages.create(...)`)
    - Subprocess `claude --json -p "..."` if Claude CLI is on PATH
    - Subprocess `codex -q "..."` for OpenAI peer-review
    - Subprocess `ollama run <model> "..."` for local
    """
    raise NotImplementedError(
        f"dispatch_llm v0.1.0 is a stub. Wire per agent-host-routing.md. "
        f"Asked model={model} max_tokens={max_tokens} on prompt len={len(prompt)}."
    )


def _safe_dispatch(prompt, model, max_tokens):
    """v0.1.0 wrapper: catch NotImplementedError and return a stub verdict
    so disk infrastructure works for tests without API costs."""
    t0 = time.time()
    try:
        out = dispatch_llm(prompt, model=model, max_tokens=max_tokens)
        return out, time.time() - t0, None
    except NotImplementedError as e:
        return None, time.time() - t0, str(e)


def _build_review_prompt(kind, content, focus=None):
    parts = [
        f"You are a senior reviewer judging a Sinister fleet agent's {kind}.",
        "Provide structured critique in JSON shape: rating (approve|approve-with-changes|revise|reject), confidence (0-1), headline (1 line), concerns (bullets), suggestions (bullets), rationale (2-3 paragraphs).",
    ]
    if focus:
        parts.append(f"Focus area: {focus}")
    parts.append("---")
    parts.append("Content to review:")
    parts.append(content[:50000])
    return "\n\n".join(parts)


def _build_judge_prompt(question, context=None, options=None):
    parts = [
        "You are a senior judge giving a binary verdict on a Sinister fleet decision.",
        "Provide JSON shape: rating (yes|no|uncertain), confidence (0-1), headline, rationale.",
    ]
    if options:
        parts.append(f"Options: {', '.join(options)}")
    parts.append("---")
    parts.append(f"Question: {question}")
    if context:
        parts.append("Context:")
        parts.append(context[:20000])
    return "\n\n".join(parts)


def _wrap_verdict(kind, summary, verdict_text, error=None, model="opus-4-7", duration_s=0.0, source_path=None, from_slug=None):
    verdict = {
        "_author": _AUTHOR,
        "schema_version": SCHEMA_VERSION,
        "ts_utc": _now_iso(),
        "from": from_slug or _detect_my_slug(),
        "model": model,
        "kind": kind,
        "input": {"summary": (summary or "")[:200], "source_path": source_path},
        "verdict": {
            "rating": "stub" if error else "see_raw",
            "confidence": 0.0 if error else 0.5,
            "headline": "stub verdict (v0.1.0; dispatch_llm not wired)" if error else "see raw verdict",
            "concerns": [error] if error else [],
            "suggestions": [],
            "rationale": verdict_text or error or "(no content)",
        },
        "cost_estimate_usd": 0.0,
        "duration_s": round(duration_s, 3),
        "stub": bool(error),
    }
    return _persist(verdict)


def review_diff(diff_text, *, model="opus-4-7", focus=None):
    prompt = _build_review_prompt("code diff", diff_text, focus=focus)
    out, dur, err = _safe_dispatch(prompt, model, 4000)
    return _wrap_verdict("diff", diff_text[:200], out, error=err, model=model, duration_s=dur)


def review_transcript(transcript_path, *, model="opus-4-7", focus=None):
    p = Path(transcript_path)
    if not p.exists():
        return _wrap_verdict("transcript", str(p), None, error=f"not found: {p}", model=model, source_path=str(p))
    content = p.read_text(encoding="utf-8", errors="replace")
    prompt = _build_review_prompt("turn transcript", content, focus=focus)
    out, dur, err = _safe_dispatch(prompt, model, 4000)
    return _wrap_verdict("transcript", str(p), out, error=err, model=model, duration_s=dur, source_path=str(p))


def review_commit(sha, *, model="opus-4-7", focus=None, cwd=None):
    try:
        res = subprocess.run(
            ["git", "show", "--format=%H%n%s%n%b%n---DIFF---", sha],
            capture_output=True, text=True, timeout=15, cwd=cwd,
        )
        if res.returncode != 0:
            return _wrap_verdict("commit", sha, None, error=f"git show failed: {res.stderr.strip()}", model=model, source_path=f"git:{sha}")
        diff = res.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return _wrap_verdict("commit", sha, None, error=str(e), model=model, source_path=f"git:{sha}")
    prompt = _build_review_prompt("git commit", diff, focus=focus)
    out, dur, err = _safe_dispatch(prompt, model, 4000)
    return _wrap_verdict("commit", sha, out, error=err, model=model, duration_s=dur, source_path=f"git:{sha}")


def judge(question, context=None, *, model="opus-4-7", options=None):
    prompt = _build_judge_prompt(question, context=context, options=options)
    out, dur, err = _safe_dispatch(prompt, model, 2000)
    return _wrap_verdict("judgment", question[:200], out, error=err, model=model, duration_s=dur)


def recent_reviews(limit=10, *, namespace=None):
    if not _root.exists():
        return []
    files = sorted(_root.glob("*.json"), key=lambda f: f.name, reverse=True)
    out = []
    for f in files:
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if namespace and rec.get("from") != namespace:
            continue
        out.append({
            "path": str(f),
            "ts_utc": rec.get("ts_utc"),
            "from": rec.get("from"),
            "kind": rec.get("kind"),
            "model": rec.get("model"),
            "rating": rec.get("verdict", {}).get("rating"),
            "headline": rec.get("verdict", {}).get("headline"),
            "stub": rec.get("stub", False),
        })
        if len(out) >= limit:
            break
    return out
