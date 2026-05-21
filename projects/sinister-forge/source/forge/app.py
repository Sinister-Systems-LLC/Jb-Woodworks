# Sinister Forge :: app.py (v2 - liquid-glass chrome + tabbed multi-pane)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Operator directive 2026-05-21: "this looks nothing like the jcode liquid
# glass system he has. I want all features he has etc with what we need i
# asked for and expanded onto it."
#
# Major overhaul vs v1:
#   - White Textual Header REPLACED by ChromeBar (purple chrome, live clock,
#     live fleet heartbeat count)
#   - Project chip strip below chrome (Ctrl+W spawn hint)
#   - TabbedMultiPane is the default home (All + per-project tabs)
#   - Memory side panel (Ctrl+M) - jcode's killer feature, expanded:
#       brain entries tagged with project + recent cross-agent + latest
#       resume-point
#   - Command palette (Ctrl+P) - jcode-style fuzzy launcher
#   - Status footer with branch / agent count / mode
#   - Boot screen properly themed (centered, purple, tagline)
#   - Spawn picker modal (Ctrl+W) - 5-question flow (project / agent name
#     / objective / host / focus)
#   - F3 opens Mind in browser

from __future__ import annotations

import asyncio
import webbrowser
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Footer, Static
except ImportError as e:
    raise ImportError(
        "Sinister Forge requires Textual. Install with: pip install -e ."
    ) from e

from forge.art import BOOT_FRAMES, BOOT_DURATION_SEC
from forge.theme import SINISTER_CSS, PURPLE_BRIGHT, PROJECT_BORDER_PALETTE
from forge.panes.chrome import ChromeBar, ProjectChip, StatusFooter
from forge.panes.memory_panel import MemoryPanel
from forge.panes.command_palette import CommandPalette
from forge.panes.tabs import TabbedMultiPane
from forge.panes.agent_pane import AgentPane
from forge.panes.picker import AgentPicker, PickerResult


class BootScreen(Static):
    """Boot animation. Centered. Cycles BOOT_FRAMES."""

    def __init__(self) -> None:
        super().__init__(classes="boot-logo")
        self.update(BOOT_FRAMES[0])

    async def animate(self) -> None:
        per_frame = BOOT_DURATION_SEC / max(len(BOOT_FRAMES), 1)
        for frame in BOOT_FRAMES:
            self.update(frame)
            await asyncio.sleep(per_frame)


class ForgeApp(App):
    """Sinister Forge - liquid-glass operator console."""

    CSS = SINISTER_CSS
    TITLE = "Sinister Forge"
    SUB_TITLE = "operator console"

    BINDINGS = [
        Binding("ctrl+w", "new_agent", "New Agent"),
        Binding("ctrl+tab", "cycle_agent", "Cycle"),
        Binding("ctrl+shift+w", "close_agent", "Close"),
        Binding("ctrl+l", "clear_log", "Clear"),
        Binding("ctrl+s", "write_resume_point", "Resume"),
        Binding("ctrl+m", "toggle_memory", "Memory"),
        Binding("ctrl+p", "command_palette", "Palette"),
        Binding("f1", "help", "Help"),
        Binding("f2", "toggle_rkoj", "RKOJ"),
        Binding("f3", "open_mind", "Mind"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._booted = False
        self._memory_visible = False

    def compose(self) -> ComposeResult:
        self._chrome = ChromeBar()
        yield self._chrome
        self._chip = ProjectChip()
        yield self._chip
        self._boot = BootScreen()
        yield self._boot
        self._status = StatusFooter()
        yield self._status
        yield Footer()

    async def on_mount(self) -> None:
        await self._boot.animate()
        await self._swap_to_main()

    async def _swap_to_main(self) -> None:
        """Remove boot screen, mount the real workspace."""
        self._boot.remove()
        # Workspace = horizontal split: main panes + optional memory panel
        self._workspace = Horizontal(id="workspace")
        await self.mount(self._workspace, after=self._chip)
        self._tabs = TabbedMultiPane()
        await self._workspace.mount(self._tabs)
        # Default project chip shows "no project"
        self._chip.set_project("", PURPLE_BRIGHT)
        self._booted = True
        self._refresh_status()

        # Welcome notification
        self.notify(
            "Ctrl+W to spawn · Ctrl+P palette · Ctrl+M memory · F1 help",
            timeout=6,
        )

    # ---------- helpers ----------

    def _refresh_status(self) -> None:
        active = sum(1 for p in self._tabs.panes if getattr(p, "_status", "") == "running")
        cur = self._tabs.current_pane
        mode = cur.mode if cur else ""
        self._status.set_state(active, mode)

    def _update_chip_from_current(self) -> None:
        cur = self._tabs.current_pane
        if cur:
            accent = PROJECT_BORDER_PALETTE.get(cur.project_key, PURPLE_BRIGHT)
            self._chip.set_project(cur.project_display, accent)
            if hasattr(self, "_memory"):
                self._memory.set_project(cur.project_key, cur.project_display)
        else:
            self._chip.set_project("", PURPLE_BRIGHT)

    # ---------- actions ----------

    async def action_new_agent(self) -> None:
        result: PickerResult | None = await self.push_screen_wait(AgentPicker())
        if not result:
            return
        accent_hex = PROJECT_BORDER_PALETTE.get(result.project_key, PURPLE_BRIGHT)
        pane = AgentPane(
            agent_name=result.agent_name,
            project_display=result.project_display,
            mode=result.objective,
            accent=result.accent,
            project_key=result.project_key,
        )
        await self._tabs.add_pane(pane, result.project_key, result.project_display)
        self._update_chip_from_current()
        self._refresh_status()
        self.notify(
            f"spawned {result.agent_name} on {result.project_display}",
            timeout=4,
        )

    def action_cycle_agent(self) -> None:
        self._tabs.cycle()
        self._update_chip_from_current()
        self._refresh_status()

    async def action_close_agent(self) -> None:
        cur = self._tabs.current_pane
        if not cur:
            self.notify("no active pane to close", severity="warning")
            return
        # terminate subprocess if any
        if cur.subprocess:
            await cur.subprocess.terminate()
        cur.remove()
        try:
            self._tabs.panes.remove(cur)
        except ValueError:
            pass
        self._tabs.current_idx = max(-1, min(self._tabs.current_idx, len(self._tabs.panes) - 1))
        self._update_chip_from_current()
        self._refresh_status()
        self.notify("agent closed", timeout=3)

    def action_clear_log(self) -> None:
        cur = self._tabs.current_pane
        if cur:
            cur.clear_log()

    def action_write_resume_point(self) -> None:
        # Best-effort: spawn the resume-point-write.ps1 in the background
        import subprocess
        ps1 = Path("D:/Sinister Sanctum/automations/resume-point-write.ps1")
        if not ps1.exists():
            self.notify("resume-point-write.ps1 missing", severity="warning")
            return
        cur = self._tabs.current_pane
        if not cur:
            self.notify("no active pane", severity="warning")
            return
        try:
            subprocess.Popen([
                "powershell.exe", "-NoProfile", "-WindowStyle", "Hidden",
                "-ExecutionPolicy", "Bypass", "-File", str(ps1),
                "-ProjectName", cur.project_display,
                "-AgentName", cur.agent_name,
                "-Mode", cur.mode,
            ], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.notify(f"resume-point written for {cur.project_display}", timeout=4)
        except Exception as e:
            self.notify(f"resume-point failed: {e}", severity="error")

    async def action_toggle_memory(self) -> None:
        if not self._booted:
            return
        if not self._memory_visible:
            self._memory = MemoryPanel()
            await self._workspace.mount(self._memory)
            cur = self._tabs.current_pane
            if cur:
                self._memory.set_project(cur.project_key, cur.project_display)
            self._memory_visible = True
            self.notify("memory panel open", timeout=2)
        else:
            self._memory.remove()
            self._memory_visible = False
            self.notify("memory panel closed", timeout=2)

    async def action_command_palette(self) -> None:
        cmd_id = await self.push_screen_wait(CommandPalette())
        if not cmd_id:
            return
        # Map palette ids to existing actions
        handlers = {
            "new_agent":      self.action_new_agent,
            "cycle_agent":    self.action_cycle_agent,
            "close_agent":    self.action_close_agent,
            "clear_log":      self.action_clear_log,
            "toggle_memory":  self.action_toggle_memory,
            "toggle_rkoj":    self.action_toggle_rkoj,
            "open_mind":      self.action_open_mind,
            "write_resume":   self.action_write_resume_point,
            "help":           self.action_help,
            "quit":           self.action_quit,
            "swarm":          self._action_swarm,
            "focus_all":      self._action_focus_all,
        }
        h = handlers.get(cmd_id)
        if h:
            result = h()
            if asyncio.iscoroutine(result):
                await result

    def action_help(self) -> None:
        self.notify(
            "Ctrl+W new · Ctrl+Tab cycle · Ctrl+Shift+W close · Ctrl+L clear · "
            "Ctrl+S resume-pt · Ctrl+M memory · Ctrl+P palette · F2 RKOJ · "
            "F3 Mind · Ctrl+Q quit",
            timeout=10,
        )

    def action_toggle_rkoj(self) -> None:
        webbrowser.open("http://127.0.0.1:5077/")
        self.notify("opened RKOJ at :5077", timeout=3)

    def action_open_mind(self) -> None:
        webbrowser.open("http://localhost:5079/")
        self.notify("opened Sinister Mind at :5079", timeout=3)

    async def _action_swarm(self) -> None:
        """Spawn 3 parallel agents on the current project (or open picker first)."""
        cur = self._tabs.current_pane
        if not cur:
            self.notify("no current project - open picker first", severity="warning")
            return
        accent_hex = PROJECT_BORDER_PALETTE.get(cur.project_key, PURPLE_BRIGHT)
        for i in range(3):
            pane = AgentPane(
                agent_name=f"{cur.agent_name}-swarm-{i+1}",
                project_display=cur.project_display,
                mode=cur.mode,
                accent=cur.accent,
                project_key=cur.project_key,
            )
            await self._tabs.add_pane(pane, cur.project_key, cur.project_display)
        self.notify(f"swarmed 3 agents on {cur.project_display}", timeout=4)
        self._refresh_status()

    def _action_focus_all(self) -> None:
        # TabbedContent active switch
        if self._tabs._tabbed:
            self._tabs._tabbed.active = "tab-all"


if __name__ == "__main__":
    ForgeApp().run()
