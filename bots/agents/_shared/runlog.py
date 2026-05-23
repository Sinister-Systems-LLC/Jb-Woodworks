"""
runlog - shared reader for runlog manifests produced by operator-run scripts.

Manifests are written by `08_AUTOMATIONS/_runlog.ps1` to
`12_LLM_ORCHESTRATION/runtime-state/script-runs/<script>-<utc>.json`.

The bus exposes these as MCP tools so any Claude session can:
  - list recent script runs
  - read the latest manifest for a given script
  - get a one-paragraph plain-text summary (no LLM cost)
  - see operator-pending next_actions from any unconsumed runs

Format (sinister-runlog/v1):
  {
    "schema": "sinister-runlog/v1",
    "script": "...", "started": "...", "finished": "...",
    "exit_code": 0, "ok": true,
    "steps": [{"step": 1, "name": "...", "ok": true, "ms": N, "produced": "...", "summary": "..."}],
    "outputs": {...},
    "warnings": [...], "errors": [...],
    "next_actions": [...],
    "auto_close": true
  }
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HUB_ROOT = Path(os.environ.get("SINISTER_HUB_ROOT", r"D:\Sinister\Sinister Skills"))
SCRIPT_RUNS_DIR = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "script-runs"
PENDING_PATH = HUB_ROOT / "12_LLM_ORCHESTRATION" / "runtime-state" / "PENDING-NEXT-ACTIONS.md"


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    """Read JSON tolerantly. PowerShell's Set-Content writes UTF-8 with BOM by
    default; utf-8-sig strips it. Plain utf-8 also works."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None


def list_recent(limit: int = 20) -> list[dict[str, Any]]:
    """Return up to N most-recent manifests (metadata only, not steps)."""
    if not SCRIPT_RUNS_DIR.exists():
        return []
    files = sorted(SCRIPT_RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    out = []
    for f in files:
        m = _safe_read_json(f)
        if not m:
            continue
        out.append({
            "id": f.stem,
            "path": str(f),
            "script": m.get("script"),
            "started": m.get("started"),
            "finished": m.get("finished"),
            "ok": m.get("ok"),
            "exit_code": m.get("exit_code"),
            "step_count": len(m.get("steps", [])),
            "warning_count": len(m.get("warnings", [])),
            "error_count": len(m.get("errors", [])),
            "next_action_count": len(m.get("next_actions", [])),
        })
    return out


def read(id_or_path: str) -> dict[str, Any]:
    """Read a single manifest by file id (no extension) or absolute path."""
    p = Path(id_or_path)
    if not p.is_absolute():
        p = SCRIPT_RUNS_DIR / f"{id_or_path}.json"
    if not p.exists():
        return {"ok": False, "error": f"manifest not found: {p}"}
    m = _safe_read_json(p)
    if m is None:
        return {"ok": False, "error": f"manifest unreadable: {p}"}
    return {"ok": True, "id": p.stem, "manifest": m}


def read_latest(script_name: str) -> dict[str, Any]:
    """Read the most recent manifest matching a script name (case-insensitive prefix)."""
    if not SCRIPT_RUNS_DIR.exists():
        return {"ok": False, "error": "no manifests directory yet"}
    candidates = []
    sn = script_name.lower()
    for f in SCRIPT_RUNS_DIR.glob("*.json"):
        if f.stem.lower().startswith(sn) or f.stem.lower().split("-")[0] == sn:
            candidates.append(f)
        else:
            m = _safe_read_json(f)
            if m and m.get("script", "").lower() == sn:
                candidates.append(f)
    if not candidates:
        return {"ok": False, "error": f"no manifests for script: {script_name}"}
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return read(latest.stem)


def summary_text(manifest: dict[str, Any]) -> str:
    """Plain-text one-paragraph rollup. No LLM cost. Format-friendly for any session."""
    if not manifest:
        return "(empty manifest)"
    script = manifest.get("script", "?")
    ok = "OK" if manifest.get("ok") else "FAIL"
    started = manifest.get("started", "?")
    finished = manifest.get("finished", "?")
    steps = manifest.get("steps", [])
    step_ok = sum(1 for s in steps if s.get("ok"))
    step_fail = len(steps) - step_ok
    warnings = len(manifest.get("warnings", []))
    errors = len(manifest.get("errors", []))
    next_actions = manifest.get("next_actions", [])

    parts = [
        f"{script}: {ok} (exit {manifest.get('exit_code', '?')}) — {started} -> {finished}",
        f"steps: {step_ok}/{len(steps)} ok" + (f", {step_fail} failed" if step_fail else ""),
    ]
    if warnings:
        parts.append(f"warnings: {warnings}")
    if errors:
        parts.append(f"errors: {errors}")
    if next_actions:
        parts.append(f"next_actions ({len(next_actions)}): " + "; ".join(next_actions[:3]) + ("..." if len(next_actions) > 3 else ""))
    return " | ".join(parts)


def pending_actions() -> dict[str, Any]:
    """Read PENDING-NEXT-ACTIONS.md (curated by Save-Runlog). Returns text + entry count."""
    if not PENDING_PATH.exists():
        return {"ok": True, "text": "", "entries": 0}
    text = PENDING_PATH.read_text(encoding="utf-8")
    # Count headers and bullets
    entries = text.count("\n## ")
    bullets = text.count("\n- [")
    return {
        "ok": True,
        "path": str(PENDING_PATH),
        "entries": entries,
        "unchecked_bullets": text.count("- [ ]"),
        "checked_bullets": text.count("- [x]"),
        "text": text,
    }


def consume_pending(mark_checked: bool = True, archive: bool = True) -> dict[str, Any]:
    """Mark all unchecked next-actions in PENDING-NEXT-ACTIONS.md as done (operator confirms).

    With archive=True (default), any block whose actions are ALL checked is moved
    out of the live file into runtime-state/_archive/PENDING-<date>.md so the
    live file shows only what's still outstanding. Prevents noise accumulation.
    """
    if not PENDING_PATH.exists():
        return {"ok": True, "consumed": 0}
    text = PENDING_PATH.read_text(encoding="utf-8")
    if not mark_checked:
        return {"ok": True, "would_consume": text.count("- [ ]"), "dry": True}
    consumed = text.count("- [ ]")
    new = text.replace("- [ ]", "- [x]")
    archived_blocks = 0
    if archive:
        import re
        blocks = re.split(r'(?m)^(?=## )', new)
        live, done = [], []
        for b in blocks:
            if not b.strip():
                if b:
                    live.append(b)
                continue
            if b.startswith('## ') and '- [ ]' not in b:
                done.append(b)
            else:
                live.append(b)
        if done:
            arc_dir = PENDING_PATH.parent / '_archive'
            arc_dir.mkdir(parents=True, exist_ok=True)
            day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            arc_path = arc_dir / f'PENDING-{day}.md'
            header = f'\n# Archived {datetime.now(timezone.utc).isoformat()}\n'
            with arc_path.open('a', encoding='utf-8') as f:
                f.write(header)
                for b in done:
                    f.write(b)
            archived_blocks = len(done)
            new = ''.join(live)
    tmp = PENDING_PATH.with_suffix(PENDING_PATH.suffix + f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(new, encoding="utf-8")
    os.replace(tmp, PENDING_PATH)
    return {"ok": True, "consumed": consumed, "archived_blocks": archived_blocks}


def stats() -> dict[str, Any]:
    """Quick health view of the runlog system."""
    files = list(SCRIPT_RUNS_DIR.glob("*.json")) if SCRIPT_RUNS_DIR.exists() else []
    return {
        "ok": True,
        "script_runs_dir": str(SCRIPT_RUNS_DIR),
        "manifest_count": len(files),
        "pending_actions_file": str(PENDING_PATH),
        "pending_exists": PENDING_PATH.exists(),
    }
