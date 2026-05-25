# Sinister Term :: status.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Lightweight, cached status helpers for the prompt + bottom toolbar.
# Every call here runs on each keystroke via prompt_toolkit's redraw -
# so each helper TTL-caches its result to stay under the per-keypress
# latency budget (<2ms) mined from handterm's philosophy.

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

from term.commands import SANCTUM_ROOT, load_projects

# RKOJ-ELENO :: 2026-05-25 :: migrated to term.cache shared primitive
# (iter-47). Local _cached helper removed in favor of one source of truth +
# stampede protection. Namespace = "status" so different modules can't
# accidentally collide on key names.
from term.cache import cached as _shared_cached


_TTL_SECONDS = 2.0  # refresh status pieces no more than twice a second


def _cached(key: str, ttl: float, factory):
    """Thin wrapper preserving the legacy signature; routes to term.cache."""
    return _shared_cached("status", key, ttl, factory)


def detect_project_for_cwd() -> Optional[str]:
    cwd = Path.cwd().resolve()
    for p in load_projects():
        root = p.get("root")
        if not root:
            continue
        try:
            if cwd.is_relative_to(Path(root).resolve()):
                return p.get("display") or p.get("key")
        except Exception:
            continue
    return None


def _git_branch_raw() -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(Path.cwd()), text=True, stderr=subprocess.DEVNULL, timeout=2,
        ).strip()
        return out or None
    except Exception:
        return None


def git_branch() -> Optional[str]:
    return _cached("git_branch", _TTL_SECONDS, _git_branch_raw)


def _freshest_sibling_heartbeat_raw() -> Optional[tuple[str, int]]:
    """Return (agent_name, age_minutes) of the most recently-updated heartbeat
    OTHER than our own. None if none found.
    """
    hb_dir = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return None
    self_stem = "sinister-term"
    candidates: list[tuple[float, str]] = []
    for hb in hb_dir.glob("*.json"):
        if hb.stem == self_stem:
            continue
        try:
            mtime = hb.stat().st_mtime
        except OSError:
            continue
        agent = hb.stem
        try:
            data = json.loads(hb.read_text(encoding="utf-8", errors="replace"))
            if isinstance(data, dict) and "agent" in data:
                agent = data["agent"]
        except Exception:
            pass
        candidates.append((mtime, agent))
    if not candidates:
        return None
    mtime, agent = max(candidates, key=lambda x: x[0])
    age_min = max(0, int((time.time() - mtime) // 60))
    return agent, age_min


def freshest_sibling_heartbeat() -> Optional[tuple[str, int]]:
    return _cached("freshest_hb", _TTL_SECONDS, _freshest_sibling_heartbeat_raw)


def _pending_inbox_count_raw() -> int:
    inbox = SANCTUM_ROOT / "_shared-memory" / "inbox" / "sinister-term"
    if not inbox.exists():
        return 0
    return sum(1 for _ in inbox.glob("*.json"))


def pending_inbox_count() -> int:
    return _cached("inbox_count", _TTL_SECONDS, _pending_inbox_count_raw)


def short_cwd(max_len: int = 40) -> str:
    s = str(Path.cwd())
    if len(s) <= max_len:
        return s
    return "..." + s[-(max_len - 3):]


def short_cwd_relative_to_project(max_len: int = 50) -> str:
    """If cwd is inside a known Sinister project, render as `<project-key>/<rel>`.
    Otherwise fall back to short_cwd().
    """
    cwd = Path.cwd().resolve()
    for p in load_projects():
        root = p.get("root")
        key = p.get("key")
        if not root or not key:
            continue
        try:
            root_path = Path(root).resolve()
            if cwd.is_relative_to(root_path):
                rel = cwd.relative_to(root_path)
                rel_str = str(rel).replace("\\", "/")
                if rel_str == ".":
                    return key
                composed = f"{key}/{rel_str}"
                if len(composed) <= max_len:
                    return composed
                return composed[: max_len - 3] + "..."
        except Exception:
            continue
    return short_cwd(max_len)
