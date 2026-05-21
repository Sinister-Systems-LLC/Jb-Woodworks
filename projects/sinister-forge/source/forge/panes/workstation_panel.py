# Sinister Forge :: panes/workstation_panel.py — RKOJ Workstation entry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator 2026-05-21: *"still no ui and rkoj workstation thing i asked for"*.
# Then 2026-05-21 ~18:00 (verbatim): *"we are working on rkoj exe not fucking
# bat ... we are combingin all thigns we have been working on rkoj workstation,
# jcode, all the skills we ahve made, mcp, our new console system"* — so the
# panel now actually LAUNCHES the workstation daemon (if port :5077 is idle)
# instead of only pointing at it.

from __future__ import annotations

import socket
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


# Path FIX 2026-05-21: was r"D:/Sinister/Sanctum/automations/window-manager"
# (extra slash splitting "Sinister Sanctum" into two segments). The real path
# is "D:/Sinister Sanctum/automations/window-manager".
WORKSTATION_DIR = Path(r"D:/Sinister Sanctum/automations/window-manager")
RKOJ_EXE_HINT = WORKSTATION_DIR / "dist" / "RKOJ.exe"
DAEMON_SCRIPT = WORKSTATION_DIR / "desktop_app.py"
RKOJ_URL = "http://127.0.0.1:5077/"


def _port_in_use(port: int = 5077, host: str = "127.0.0.1") -> bool:
    """Cheap port check — connect() succeeds iff something is listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


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
            f"or click the buttons below. This view stays inside the Agents tab "
            f"so the UI chrome remains around the console."
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
            # Auto-spawn daemon if port :5077 idle BEFORE opening the browser,
            # so the operator clicks ONE button instead of two.
            if not _port_in_use(5077):
                self._spawn_daemon()
            webbrowser.open(RKOJ_URL)
            self.app.notify(f"opened {RKOJ_URL}", timeout=3)
            return
        if bid == "ws-btn-launch":
            # Prefer the in-tree daemon script over the dist EXE — the daemon
            # is what serves :5077 + pywebview UI. The dist EXE is the Forge
            # TUI build, not the workstation daemon.
            if DAEMON_SCRIPT.exists():
                self._spawn_daemon()
                return
            if RKOJ_EXE_HINT.exists():
                try:
                    subprocess.Popen(
                        [str(RKOJ_EXE_HINT), "workstation"],
                        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                    )
                    self.app.notify("launched RKOJ.exe workstation", timeout=4)
                except Exception as e:
                    self.app.notify(f"launch failed: {e}", severity="error", timeout=5)
                return
            self.app.notify(
                f"workstation daemon not found — see {WORKSTATION_DIR}",
                severity="warning",
                timeout=5,
            )

    def _spawn_daemon(self) -> None:
        """Start the workstation daemon (python desktop_app.py) detached.

        2026-05-21 OPERATOR FIX: dropped CREATE_NEW_CONSOLE (was opening a
        visible cmd window the operator saw as "another terminal"). Now uses
        CREATE_NO_WINDOW so the daemon spawns silently — operator's only
        interaction surface is the browser tab the Open-Browser button opens.
        """
        if not DAEMON_SCRIPT.exists():
            self.app.notify(
                f"daemon script missing: {DAEMON_SCRIPT}",
                severity="error",
                timeout=5,
            )
            return
        try:
            subprocess.Popen(
                ["python", str(DAEMON_SCRIPT)],
                cwd=str(WORKSTATION_DIR),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                              | getattr(subprocess, "DETACHED_PROCESS", 0),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.app.notify("workstation daemon spawned :5077 (silent)", timeout=4)
        except Exception as e:
            self.app.notify(f"spawn failed: {e}", severity="error", timeout=5)
