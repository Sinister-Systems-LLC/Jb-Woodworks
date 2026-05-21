# Sinister Forge :: app.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# PH1 minimal Textual app. Boot animation -> single placeholder agent pane
# with bold project-name header. Multi-pane, picker, subprocess spawning
# all land in PH2-PH4.

from __future__ import annotations

import asyncio
from typing import Iterable

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Vertical
    from textual.widgets import Footer, Header, Static, RichLog
except ImportError as e:
    raise ImportError(
        "Sinister Forge requires Textual. Install with: pip install -e ."
    ) from e

from forge.art import BOOT_FRAMES, BOOT_DURATION_SEC
from forge.theme import SINISTER_CSS, PURPLE_BRIGHT


class BootScreen(Static):
    """The Vault Boy ASCII boot animation. Cycles BOOT_FRAMES over BOOT_DURATION_SEC."""

    def __init__(self) -> None:
        super().__init__(classes="boot-logo")
        self._frame_idx = 0
        self.update(BOOT_FRAMES[0])

    async def animate(self) -> None:
        per_frame = BOOT_DURATION_SEC / max(len(BOOT_FRAMES), 1)
        for frame in BOOT_FRAMES:
            self.update(frame)
            await asyncio.sleep(per_frame)


class AgentPane(Vertical):
    """One agent's pane: bold header + scrolling buffer.

    PH1 ships a placeholder. PH2 wires multiple panes side-by-side.
    PH3 wires subprocess stdout into the RichLog.
    """

    def __init__(self, project: str, mode: str, agent_name: str) -> None:
        super().__init__(classes="agent-pane")
        self.project = project
        self.mode = mode
        self.agent_name = agent_name

    def compose(self) -> ComposeResult:
        header_text = f"  {self.project.upper()}  ::  {self.agent_name}  ::  {self.mode}  "
        yield Static(header_text, classes="agent-header")
        log = RichLog(highlight=True, markup=True, wrap=False, auto_scroll=True, id="agent-log")
        log.write(f"[dim]Sinister Forge :: PH1 placeholder pane[/dim]")
        log.write(f"[bold {PURPLE_BRIGHT}]Project:[/] {self.project}")
        log.write(f"[bold {PURPLE_BRIGHT}]Agent:[/]   {self.agent_name}")
        log.write(f"[bold {PURPLE_BRIGHT}]Mode:[/]    {self.mode}")
        log.write("")
        log.write("[dim]PH2+: subprocess output streams here.[/dim]")
        log.write("[dim]Ctrl+W for new agent, Ctrl+Tab to cycle, F1 for help.[/dim]")
        yield log


class ForgeApp(App):
    """Sinister Forge main Textual app."""

    CSS = SINISTER_CSS
    TITLE = "Sinister Forge"
    SUB_TITLE = "operator console"

    BINDINGS = [
        Binding("ctrl+w", "new_agent", "New Agent"),
        Binding("ctrl+tab", "cycle_agent", "Cycle"),
        Binding("ctrl+shift+w", "close_agent", "Close Agent"),
        Binding("ctrl+l", "clear_log", "Clear"),
        Binding("ctrl+s", "write_resume_point", "Resume Pt"),
        Binding("f1", "help", "Help"),
        Binding("f2", "toggle_rkoj", "RKOJ"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._booted = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self._boot = BootScreen()
        yield self._boot
        yield Footer()

    async def on_mount(self) -> None:
        """Run boot animation then swap in the agent pane."""
        await self._boot.animate()
        await self._show_main_ui()

    async def _show_main_ui(self) -> None:
        """Replace the boot screen with the main multi-agent UI."""
        self._boot.remove()
        # PH1 single placeholder pane; PH2+ multi-pane.
        pane = AgentPane(project="Sanctum", mode="resume", agent_name="test")
        await self.mount(pane)
        self._booted = True

    # --- Action handlers (PH1 stubs; PH2-PH4 wire them up) ---

    def action_new_agent(self) -> None:
        self.notify("Ctrl+W: new agent (PH3)", severity="information")

    def action_cycle_agent(self) -> None:
        self.notify("Ctrl+Tab: cycle (PH2)", severity="information")

    def action_close_agent(self) -> None:
        self.notify("Ctrl+Shift+W: close (PH3)", severity="information")

    def action_clear_log(self) -> None:
        try:
            log = self.query_one("#agent-log", RichLog)
            log.clear()
        except Exception:
            pass

    def action_write_resume_point(self) -> None:
        self.notify("Ctrl+S: resume-point write (PH6)", severity="information")

    def action_help(self) -> None:
        self.notify(
            "Keys: Ctrl+W new agent / Ctrl+Tab cycle / Ctrl+Shift+W close / "
            "Ctrl+L clear / Ctrl+S resume-pt / F2 RKOJ / Ctrl+Q quit",
            timeout=8,
        )

    def action_toggle_rkoj(self) -> None:
        self.notify("F2: RKOJ panel (PH7)", severity="information")
