# Sinister Forge :: panes/status_bar.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
from textual.widgets import Static


class StatusBar(Static):
    def __init__(self) -> None:
        super().__init__(classes="status-bar", markup=True)
        self._agent_count = 0
        self._current_idx = -1
        self._render()

    def update_state(self, agent_count: int, current_idx: int) -> None:
        self._agent_count = agent_count
        self._current_idx = current_idx
        self._render()

    def _render(self) -> None:
        cur = self._current_idx + 1 if self._current_idx >= 0 else 0
        self.update(
            f" [b]SINISTER FORGE[/b]  ::  agents [b]{cur}[/]/[b]{self._agent_count}[/]  "
            f"::  [dim]Ctrl+W new  Ctrl+Tab cycle  F1 help[/]"
        )
