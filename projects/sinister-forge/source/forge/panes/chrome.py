# Sinister Forge :: panes/chrome.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Top chrome bar + status footer + project chip strip. Replaces Textual's
# default Header (which the operator screenshot showed as ugly white) with
# our own purple-tinted bars.

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from textual.widgets import Static

from forge.theme import (
    PURPLE_HALO, PURPLE_BRIGHT, CYAN, GREEN, YELLOW, RED, SOFT, DIM,
)


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
HEARTBEATS_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"


class ChromeBar(Static):
    """Top bar - replaces Textual Header. Shows brand + clock + live agents."""

    DEFAULT_CSS = ""

    def __init__(self) -> None:
        # Textual 8.x: pass initial content positionally so first paint has Content.
        super().__init__(
            "[bold]◈ SINISTER FORGE[/bold]  [dim]:: operator console[/]",
            id="chrome-bar",
            markup=True,
        )

    def on_mount(self) -> None:
        self.set_interval(1.0, self._refresh)
        self._refresh()

    def _refresh(self) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        alive = self._count_alive_heartbeats()
        # Render: glyph + brand + spacer + clock + spacer + fleet
        self.update(
            f"[bold]◈ SINISTER FORGE[/bold]"
            f"  [{SOFT}]:: operator console[/]"
            f"        "
            f"[{CYAN}]{alive} live[/]"
            f"  [{DIM}]·[/]  "
            f"[{PURPLE_HALO}]{now}[/]"
        )

    def _count_alive_heartbeats(self) -> int:
        if not HEARTBEATS_DIR.exists():
            return 0
        now = time.time()
        return sum(
            1 for hb in HEARTBEATS_DIR.glob("*.json")
            if (now - hb.stat().st_mtime) < 1800  # 30 min
        )


class ProjectChip(Static):
    """Strip showing which project the user is focused on."""

    def __init__(self) -> None:
        # Textual 8.x: pass initial content positionally so first paint has Content.
        super().__init__(
            f"[{DIM}]no project selected · press Ctrl+W to spawn[/]",
            id="project-chip",
            markup=True,
        )
        self._project_display = ""
        self._accent = PURPLE_BRIGHT

    def set_project(self, display: str, accent: str = PURPLE_BRIGHT) -> None:
        self._project_display = display
        self._accent = accent
        self._refresh_view()

    def _refresh_view(self) -> None:
        # Do NOT name this _render - that shadows textual.widget.Widget._render
        # which must return a Visual. The override returns None and crashes
        # Visual.to_strips at first paint with AttributeError.
        if not self._project_display:
            self.update(f"[{DIM}]no project selected · press Ctrl+W to spawn[/]")
            return
        self.update(
            f"[{self._accent}]▸[/] [bold]{self._project_display}[/]   "
            f"[{DIM}]Ctrl+W new · Ctrl+P palette · Ctrl+Tab cycle · Ctrl+M memory · F2 RKOJ[/]"
        )


class StatusFooter(Static):
    """Bottom info row beneath Footer. Branch / agent-count / mode."""

    def __init__(self) -> None:
        # Textual 8.x: pass initial content positionally so first paint has Content.
        super().__init__(
            f"[{DIM}]branch[/] [{PURPLE_HALO}]?[/]   "
            f"[{DIM}]agents[/] [{CYAN}]0[/]   "
            f"[{DIM}]mode[/] [{GREEN}]idle[/]",
            id="status-footer",
            markup=True,
        )
        self._branch = ""
        self._agents_active = 0
        self._mode = ""

    def on_mount(self) -> None:
        self.set_interval(5.0, self._read_branch)
        self._read_branch()

    def _read_branch(self) -> None:
        try:
            head_file = SANCTUM_ROOT / ".git" / "HEAD"
            if head_file.exists():
                head = head_file.read_text(encoding="utf-8").strip()
                if head.startswith("ref: refs/heads/"):
                    self._branch = head.removeprefix("ref: refs/heads/")
                else:
                    self._branch = head[:7]
        except Exception:
            pass
        self._refresh_view()

    def set_state(self, agents_active: int, mode: str) -> None:
        self._agents_active = agents_active
        self._mode = mode
        self._refresh_view()

    def _refresh_view(self) -> None:
        # Do NOT name this _render (see ProjectChip._refresh_view for rationale).
        self.update(
            f"[{DIM}]branch[/] [{PURPLE_HALO}]{self._branch or '?'}[/]   "
            f"[{DIM}]agents[/] [{CYAN}]{self._agents_active}[/]   "
            f"[{DIM}]mode[/] [{GREEN}]{self._mode or 'idle'}[/]"
        )
