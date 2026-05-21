# Sinister Forge :: panes/statusbar.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Bottom status bar — jcode chrome parity (one-line, height=1).
# Renders:
#   [agents: N live]  [inbox: N]  [memory: N]  [tokens used: X/200K]  [Ctrl+P palette]
#
# Updates every 5s via a textual Timer. Every counter is best-effort —
# helpers return 0 on any failure so the widget never crashes the TUI.

from __future__ import annotations

import time
from pathlib import Path

from textual.widgets import Static

from forge.theme import (
    PURPLE_VOID, PURPLE_BORDER, GRAY, GREEN_ACCENT, DIM,
)


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox"
FORGE_MEMORY_DIR = SANCTUM_ROOT / "_shared-memory" / "forge-memory"

# Sinister Panel chrome (sourced from forge.theme — single source of truth).
STATUSBAR_BG     = PURPLE_VOID    # #0E0A14
STATUSBAR_BORDER = PURPLE_BORDER  # #3A2A55
STATUSBAR_TEXT   = GRAY           # #999AB0
STATUSBAR_ACCENT = GREEN_ACCENT   # #85C86E live counters
STATUSBAR_DIM    = DIM            # #6E6E84


# Heartbeat freshness window (jcode parity: 30 min).
HEARTBEAT_ALIVE_SEC = 1800
# Soft 200K context budget (Opus 4.7 1M overall; UI shows 200K visible window).
TOKEN_BUDGET = 200_000


def _count_agents_live() -> int:
    try:
        if not HEARTBEATS_DIR.exists():
            return 0
        now = time.time()
        return sum(
            1 for hb in HEARTBEATS_DIR.glob("*.json")
            if (now - hb.stat().st_mtime) < HEARTBEAT_ALIVE_SEC
        )
    except Exception:
        return 0


def _count_inbox() -> int:
    """Total unread items across every inbox/<slug>/ subdir."""
    try:
        if not INBOX_DIR.exists():
            return 0
        n = 0
        for sub in INBOX_DIR.iterdir():
            if sub.is_dir():
                n += sum(1 for _ in sub.glob("*.json"))
                n += sum(1 for _ in sub.glob("*.md"))
        return n
    except Exception:
        return 0


def _count_memory() -> int:
    """Total forge-memory entries (json files across all project subdirs)."""
    try:
        if not FORGE_MEMORY_DIR.exists():
            return 0
        # cheap recursive glob; bounded by directory size and called every 5s
        return sum(1 for _ in FORGE_MEMORY_DIR.rglob("*.json"))
    except Exception:
        return 0


def _tokens_used() -> int:
    """Placeholder — we don't have a live session-token meter yet.
    Returns 0 so the field renders as 0/200K instead of crashing."""
    return 0


class Statusbar(Static):
    """One-line bottom status bar — jcode chrome parity.

    Polls disk-backed counters every 5 sec. All helpers are best-effort and
    return 0 on any failure, so the widget never crashes the TUI.
    """

    DEFAULT_CSS = f"""
    Statusbar {{
        dock: bottom;
        height: 1;
        background: {STATUSBAR_BG};
        color: {STATUSBAR_TEXT};
        border-top: solid {STATUSBAR_BORDER};
        padding: 0 1;
    }}
    """

    def __init__(self) -> None:
        super().__init__("", id="forge-statusbar", markup=True)
        self._agents = 0
        self._inbox = 0
        self._memory = 0
        self._tokens = 0

    def on_mount(self) -> None:
        self._refresh()
        self.set_interval(5.0, self._refresh)

    def _refresh(self) -> None:
        try:
            self._agents = _count_agents_live()
        except Exception:
            self._agents = 0
        try:
            self._inbox = _count_inbox()
        except Exception:
            self._inbox = 0
        try:
            self._memory = _count_memory()
        except Exception:
            self._memory = 0
        try:
            self._tokens = _tokens_used()
        except Exception:
            self._tokens = 0

        # Render — '--' fallback if any helper returned None (defensive; the
        # _count_* functions return 0 on failure but keep this for symmetry).
        agents = self._agents if self._agents is not None else "--"
        inbox = self._inbox if self._inbox is not None else "--"
        memory = self._memory if self._memory is not None else "--"
        tokens = self._tokens if self._tokens is not None else "--"

        self.update(
            f"[{STATUSBAR_TEXT}]agents:[/] [{STATUSBAR_ACCENT}]{agents} live[/]"
            f"  [{STATUSBAR_DIM}]·[/]  "
            f"[{STATUSBAR_TEXT}]inbox:[/] [{STATUSBAR_ACCENT}]{inbox}[/]"
            f"  [{STATUSBAR_DIM}]·[/]  "
            f"[{STATUSBAR_TEXT}]memory:[/] [{STATUSBAR_ACCENT}]{memory}[/]"
            f"  [{STATUSBAR_DIM}]·[/]  "
            f"[{STATUSBAR_TEXT}]tokens used:[/] [{STATUSBAR_ACCENT}]{tokens}/{TOKEN_BUDGET//1000}K[/]"
            f"  [{STATUSBAR_DIM}]·[/]  "
            f"[{STATUSBAR_TEXT}]Ctrl+P palette[/]"
        )
