# Sinister Forge :: panes/workstation_panel.py — RKOJ Workstation entry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator 2026-05-21: *"still no ui and rkoj workstation thing i asked for"*.
# Read-only stub surfacing the workstation console location + launch instruction.
# Activated when the operator clicks the WORKSTATION sidebar tab.

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Button

from forge.theme import (
    BG, BG_GLASS_1, BG_GLOW, BORDER_GLASS,
    PURPLE_ACCENT, PURPLE_DEEP, SOFT, DIM,
)


WORKSTATION_DIR = Path(r"D:/Sinister Sanctum/automations/window-manager")
RKOJ_EXE_HINT = WORKSTATION_DIR / "dist" / "RKOJ.exe"
RKOJ_URL = "http://127.0.0.1:5077/"


class WorkstationPanel(Vertical):
    """Read-only landing for the RKOJ workstation console.

    Surfaces the source path, the EXE hint, and two action buttons
    (Open Browser :5077, Launch EXE). No live process management yet —
    the workstation runs as its own EXE; Forge just points operator at it.
    """

    DEFAULT_CSS = f"""
    WorkstationPanel {{
        background: {BG};
        padding: 2 3;
    }}
    WorkstationPanel #ws-title {{
        color: {PURPLE_ACCENT};
        text-style: bold;
        margin-bottom: 1;
    }}
    WorkstationPanel #ws-body {{
        background: {BG_GLASS_1};
        border: round {BORDER_GLASS};
        padding: 1 2;
        color: {SOFT};
        margin-bottom: 1;
    }}
    WorkstationPanel #ws-hint {{
        color: {DIM};
        margin-bottom: 1;
    }}
    WorkstationPanel Button {{
        margin: 0 1 1 0;
        background: {BG_GLOW};
        color: {PURPLE_ACCENT};
        border: round {PURPLE_DEEP};
    }}
    WorkstationPanel Button:hover {{
        background: {PURPLE_DEEP};
        color: {SOFT};
    }}
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]RKOJ WORKSTATION CONSOLE[/]", id="ws-title")
        exe_status = "found on disk" if RKOJ_EXE_HINT.exists() else "not built yet"
        body = (
            f"Workstation Console source:\n"
            f"  [bold]{WORKSTATION_DIR}[/]\n\n"
            f"Built EXE ({exe_status}):\n"
            f"  [bold]{RKOJ_EXE_HINT}[/]\n\n"
            f"Web UI (when RKOJ daemon is running):\n"
            f"  [bold]{RKOJ_URL}[/]\n\n"
            f"Launch [bold]RKOJ.exe workstation[/] from a terminal to run it, "
            f"or click the buttons below."
        )
        yield Static(body, id="ws-body")
        yield Static(
            "[dim]F2 toggles the RKOJ browser view anywhere in Forge.[/]",
            id="ws-hint",
        )
        yield Button("Open RKOJ in Browser (:5077)", id="ws-btn-browser")
        yield Button("Launch RKOJ.exe", id="ws-btn-launch")

    def on_button_pressed(self, event) -> None:
        bid = event.button.id
        if bid == "ws-btn-browser":
            webbrowser.open(RKOJ_URL)
            self.app.notify(f"opened {RKOJ_URL}", timeout=3)
            return
        if bid == "ws-btn-launch":
            if not RKOJ_EXE_HINT.exists():
                self.app.notify(
                    f"RKOJ.exe not built — see {WORKSTATION_DIR}",
                    severity="warning",
                    timeout=5,
                )
                return
            try:
                subprocess.Popen(
                    [str(RKOJ_EXE_HINT), "workstation"],
                    creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                )
                self.app.notify("launched RKOJ.exe workstation", timeout=4)
            except Exception as e:
                self.app.notify(f"launch failed: {e}", severity="error", timeout=5)
