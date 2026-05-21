# Sinister Forge :: panes/command_palette.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Ctrl+P command palette. jcode-style fuzzy launcher. Lists every action
# the user can take (spawn / cycle / clear / toggle memory / open mind /
# spawn swarm / etc) with fuzzy filtering.

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option


COMMANDS: list[tuple[str, str, str]] = [
    ("new_agent",        "Spawn new agent",            "Open the picker (Ctrl+W)"),
    ("swarm",            "Swarm N agents",             "Spawn N parallel agents on current project"),
    ("cycle_agent",      "Cycle next agent",           "Ctrl+Tab"),
    ("close_agent",      "Close current agent",        "Ctrl+Shift+W (SIGTERM, escalates to SIGKILL)"),
    ("clear_log",        "Clear current pane",         "Ctrl+L"),
    ("toggle_memory",    "Toggle memory panel",        "Ctrl+M"),
    ("toggle_rkoj",      "Open RKOJ workbench",        "F2"),
    ("open_mind",        "Open Sinister Mind",         "F3 - http://localhost:5079/"),
    ("write_resume",     "Write resume-point now",     "Ctrl+S"),
    ("focus_all",        "Switch to All tab",          ""),
    ("help",             "Help",                       "F1"),
    ("quit",             "Quit Forge",                 "Ctrl+Q"),
]


class CommandPalette(ModalScreen[str | None]):
    """jcode-style palette. Returns the chosen command id (or None if cancelled)."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="palette-screen"):
            with Vertical(id="palette-card"):
                yield Static("◈ COMMAND PALETTE", id="palette-title")
                yield Input(placeholder="type to filter...", id="palette-input")
                self._list = OptionList(
                    *[Option(self._row(c, l, d), id=c) for c, l, d in COMMANDS],
                    id="palette-list",
                )
                yield self._list

    @staticmethod
    def _row(cmd_id: str, label: str, desc: str) -> str:
        return f"[bold]{label}[/]  [dim]· {desc}[/]" if desc else label

    def on_mount(self) -> None:
        self.query_one("#palette-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower().strip()
        self._list.clear_options()
        for cmd_id, label, desc in COMMANDS:
            if not q or q in label.lower() or q in desc.lower() or q in cmd_id.lower():
                self._list.add_option(Option(self._row(cmd_id, label, desc), id=cmd_id))

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        if self._list.option_count:
            opt = self._list.get_option_at_index(0)
            self.dismiss(opt.id)
        else:
            self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.id)
