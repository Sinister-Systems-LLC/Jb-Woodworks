# Author: RKOJ-ELENO :: 2026-05-24
"""Lightweight config IO for the attached-projects registry.

P0: file-based JSON read; P1+ adds write + lock.
"""

from __future__ import annotations

import json
from pathlib import Path

# Resolve config relative to package; tolerate dev-time absence
_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "attached-projects.json"


def list_attachments(config_path: Path | None = None) -> list[dict]:
    """Return the attachments list from config/attached-projects.json.

    Empty list if file missing (P0 default state).
    """
    p = config_path or _DEFAULT_CONFIG
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data.get("attachments", [])


def attachments_by_status(status: str, config_path: Path | None = None) -> list[dict]:
    """Filter attachments to a given status (prepared / active / detached / suspended)."""
    return [a for a in list_attachments(config_path) if a.get("status") == status]
