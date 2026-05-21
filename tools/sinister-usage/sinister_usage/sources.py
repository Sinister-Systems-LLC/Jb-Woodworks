# Sinister Sanctum :: sinister-usage :: local-state sources
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Local-only sources for usage estimation. NO network. Reads:
- ~/.claude/                        Claude Code state (projects/, settings.json, statsig.json, history JSONL)
- Optional: sinister-login provider registry (when installed)

Everything returned is a dict; no objects leak across the module boundary.
Network operations live in `api.py` behind opt-in --probe / --remote flags.
"""
from __future__ import annotations
import datetime
import importlib
import json
import os
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "sinister.usage.sources.v1"

DEFAULT_CLAUDE_DIR = Path.home() / ".claude"


def _safe_size(p: Path) -> int:
    try:
        return p.stat().st_size
    except OSError:
        return 0


def _is_today_utc(ts: float) -> bool:
    try:
        d = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
        return d == datetime.datetime.now(datetime.timezone.utc).date()
    except (OverflowError, OSError, ValueError):
        return False


def scan_claude_local(claude_dir: Path | str | None = None) -> dict[str, Any]:
    """Scan ~/.claude/ for state files. Returns a flat summary dict.

    Looked-for entries (any subset may be missing — degrade gracefully):
    - projects/                 conversation transcripts (.jsonl per session)
    - settings.json             user-level config
    - statsig.json              telemetry-toggle marker
    - history.jsonl             cross-session command history
    """
    root = Path(claude_dir) if claude_dir else DEFAULT_CLAUDE_DIR
    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "exists": root.exists(),
        "projects_count": 0,
        "sessions_count": 0,
        "sessions_today": 0,
        "total_session_bytes": 0,
        "today_session_bytes": 0,
        "settings_present": False,
        "history_lines": 0,
    }
    if not root.exists():
        return out
    projects = root / "projects"
    if projects.is_dir():
        proj_dirs = [p for p in projects.iterdir() if p.is_dir()]
        out["projects_count"] = len(proj_dirs)
        for pd in proj_dirs:
            for ssn in pd.glob("*.jsonl"):
                out["sessions_count"] += 1
                size = _safe_size(ssn)
                out["total_session_bytes"] += size
                try:
                    mtime = ssn.stat().st_mtime
                except OSError:
                    mtime = 0
                if _is_today_utc(mtime):
                    out["sessions_today"] += 1
                    out["today_session_bytes"] += size
    if (root / "settings.json").is_file():
        out["settings_present"] = True
    hist = root / "history.jsonl"
    if hist.is_file():
        try:
            with hist.open("r", encoding="utf-8", errors="replace") as fh:
                out["history_lines"] = sum(1 for _ in fh)
        except OSError:
            pass
    return out


def scan_provider_registry() -> list[dict[str, Any]]:
    """If sinister-login is installed, return its 11-provider status list.
    Otherwise return [] — the registry is optional.
    """
    try:
        mod = importlib.import_module("sinister_login")
    except ImportError:
        return []
    fn = getattr(mod, "status_all", None)
    if not callable(fn):
        return []
    try:
        return list(fn())
    except Exception:
        return []


def today_summary(claude_dir: Path | str | None = None) -> dict[str, Any]:
    """Rolled-up `sinister-usage today` payload. Local-only.

    Estimates UTC-today tokens by combining session transcript bytes with a
    bytes→tokens divisor (4 bytes per token on JSONL-wrapped text). Coarse
    upper-bound; reality is lower because metadata wrapping inflates bytes.
    """
    local = scan_claude_local(claude_dir)
    bytes_today = int(local.get("today_session_bytes", 0))
    rough_tokens_today = bytes_today // 4
    sessions_today = int(local.get("sessions_today", 0))
    return {
        "schema_version": SCHEMA_VERSION,
        "as_of_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "claude_local": local,
        "sessions_today": sessions_today,
        "bytes_today": bytes_today,
        "rough_tokens_today": rough_tokens_today,
        "notes": (
            "rough_tokens_today divides transcript bytes by 4. "
            "Real per-session token usage is lower because JSONL wrapping inflates bytes. "
            "Authoritative quota fetch requires --remote (network + auth)."
        ),
    }
