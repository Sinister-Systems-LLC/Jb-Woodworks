# Sinister Forge :: panes/status_bar.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
from textual.widgets import Static


class StatusBar(Static):
    def __init__(self) -> None:
        # Textual 8.x: pass initial content positionally so first paint has Content.
        super().__init__(
            " [b]SINISTER FORGE[/b]  ::  agents [b]0[/]/[b]0[/]  "
            "::  [dim]Ctrl+W new  Ctrl+Tab cycle  F1 help[/]",
            classes="status-bar",
            markup=True,
        )
        self._agent_count = 0
        self._current_idx = -1

    def update_state(self, agent_count: int, current_idx: int) -> None:
        self._agent_count = agent_count
        self._current_idx = current_idx
        self._refresh_view()

    def _refresh_view(self) -> None:
        # Do NOT name this _render - shadows textual.widget.Widget._render.
        cur = self._current_idx + 1 if self._current_idx >= 0 else 0
        self.update(
            f" [b]SINISTER FORGE[/b]  ::  agents [b]{cur}[/]/[b]{self._agent_count}[/]  "
            f"::  [dim]Ctrl+W new  Ctrl+Tab cycle  F1 help[/]"
        )
