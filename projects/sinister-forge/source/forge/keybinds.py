# Sinister Forge :: keybinds.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
from textual.binding import Binding

FORGE_BINDINGS: list[Binding] = [
    Binding("ctrl+w", "new_agent", "New Agent", priority=True),
    Binding("ctrl+tab", "cycle_next", "Next"),
    Binding("ctrl+shift+tab", "cycle_prev", "Prev"),
    Binding("ctrl+shift+w", "close_agent", "Close"),
    Binding("ctrl+l", "clear_log", "Clear"),
    Binding("ctrl+s", "write_resume_point", "Resume Pt"),
    Binding("f1", "help", "Help"),
    Binding("f2", "toggle_rkoj", "RKOJ"),
    Binding("f5", "refresh", "Refresh"),
    Binding("ctrl+q", "quit", "Quit", priority=True),
]
