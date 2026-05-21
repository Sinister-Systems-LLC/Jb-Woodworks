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
    from textual import work
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
from forge.panes.swarm_modal import SwarmModal, SwarmModalResult
from forge.swarm import send_dm as _send_dm, broadcast as _broadcast
from forge.projects import get_project
from forge.spawn.base import SpawnConfig
from forge.spawn.claude import ClaudeSubprocess
from forge.spawn.codex import CodexSubprocess


def _compose_phrase(*, project_key: str, agent_name: str, objective: str,
                    token_mode: str, speed: str, focus: str) -> str:
    """Build the opening phrase the Claude/Codex CLI gets as its first message."""
    contracts = "Read automations/session-contracts.md (6 binding contracts)."
    focus_block = f"\n\nFocus: {focus}" if focus else ""
    return (
        f"You are {agent_name}, the Sinister {project_key} lane agent via Forge. "
        f"Mode={objective}, TokenMode={token_mode}, Speed={speed}. {contracts}"
        f"{focus_block}\n\nStart the loop."
    )


def _build_subprocess(result: PickerResult) -> "AgentSubprocess | None":
    """Construct a ClaudeSubprocess or CodexSubprocess from picker output. Returns
    None if no valid project root exists (operator picked a project without a
    source tree on disk yet; pane mounts empty and the operator sees the message)."""
    proj = get_project(result.project_key)
    if not proj or not proj.root:
        return None
    project_root = Path(proj.root)
    if not project_root.exists():
        return None
    phrase = _compose_phrase(
        project_key=result.project_key,
        agent_name=result.agent_name,
        objective=result.objective,
        token_mode=result.token_mode,
        speed=result.speed,
        focus=result.focus,
    )
    cfg = SpawnConfig(
        project_key=result.project_key,
        project_root=project_root,
        agent_name=result.agent_name,
        accent_color=result.accent,
        mode=result.objective,
        phrase=phrase,
        token_mode=result.token_mode,
        speed=result.speed,
    )
    host = (result.host or "claude").lower()
    if host == "codex":
        return CodexSubprocess(cfg)
    return ClaudeSubprocess(cfg)


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
        # PH18 niri navigation
        Binding("ctrl+right", "scroll_right", "Col→", show=False),
        Binding("ctrl+left", "scroll_left", "Col←", show=False),
        Binding("ctrl+shift+right", "swap_right", "Move→", show=False),
        Binding("ctrl+shift+left", "swap_left", "Move←", show=False),
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

    @work(exit_on_error=False)
    async def action_new_agent(self) -> None:
        # Textual 8.x: push_screen_wait requires a worker context. Without @work
        # the call raises NoActiveWorker and Ctrl+W crashes the app.
        # exit_on_error=False so a bug in the post-submit flow notifies instead
        # of killing the whole app (operator-reported submit-auto-close before
        # adding project_display to PickerResult).
        result: PickerResult | None = await self.push_screen_wait(AgentPicker())
        if not result:
            return
        accent_hex = PROJECT_BORDER_PALETTE.get(result.project_key, PURPLE_BRIGHT)
        subprocess = _build_subprocess(result)
        pane = AgentPane(
            agent_name=result.agent_name,
            project_display=result.project_display,
            mode=result.objective,
            accent=result.accent,
            subprocess=subprocess,
            project_key=result.project_key,
        )
        await self._tabs.add_pane(pane, result.project_key, result.project_display)
        self._update_chip_from_current()
        self._refresh_status()
        if subprocess:
            # Run the actual Claude/Codex CLI in the background; pane.run_subprocess
            # tails stdout/stderr into the pane log. Don't await — fire-and-forget so
            # the action handler returns and the modal closes cleanly.
            self.run_worker(pane.run_subprocess(), exclusive=False, name=f"sub-{result.agent_name}")
            self.notify(
                f"spawned {result.agent_name} ({subprocess.binary_name}) on {result.project_display}",
                timeout=4,
            )
        else:
            self.notify(
                f"{result.project_display} has no source tree on disk - empty pane",
                severity="warning",
                timeout=5,
            )

    def action_cycle_agent(self) -> None:
        self._tabs.cycle()
        self._update_chip_from_current()
        self._refresh_status()

    def action_scroll_right(self) -> None:
        self._tabs.cycle(1)
        self._update_chip_from_current()
        self._refresh_status()

    def action_scroll_left(self) -> None:
        self._tabs.cycle(-1)
        self._update_chip_from_current()
        self._refresh_status()

    def action_swap_right(self) -> None:
        self._tabs.swap_focused(1)
        self._update_chip_from_current()

    def action_swap_left(self) -> None:
        self._tabs.swap_focused(-1)
        self._update_chip_from_current()

    async def action_close_agent(self) -> None:
        cur = self._tabs.current_pane
        if not cur:
            self.notify("no active pane to close", severity="warning")
            return
        # terminate subprocess if any
        if cur.subprocess:
            await cur.subprocess.terminate()
        # remove the focused column via ScrollableColumns (handles DOM + bookkeeping)
        if self._tabs._columns is not None:
            self._tabs._columns.remove_focused()
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

    @work(exit_on_error=False)
    async def action_command_palette(self) -> None:
        # Textual 8.x: push_screen_wait requires a worker context.
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
            "dm":             self._action_dm,
            "broadcast":      self._action_broadcast,
            "host_claude":    lambda: self._action_host_switch("claude"),
            "host_codex":     lambda: self._action_host_switch("codex"),
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

    @work(exit_on_error=False)
    async def _action_dm(self) -> None:
        """PH16 [DM]: pop a modal, send to inbox/<slug>/."""
        result: SwarmModalResult | None = await self.push_screen_wait(SwarmModal(kind="dm"))
        if not result:
            return
        from_slug = self._current_agent_slug()
        try:
            path = _send_dm(
                from_slug=from_slug,
                to_slug=result.to_slug,
                subject=result.subject,
                body=result.body,
                project_hint=self._current_project_key() or "",
            )
            self.notify(f"DM → {result.to_slug} :: {path.name}", timeout=4)
        except Exception as e:
            self.notify(f"DM failed: {e}", severity="error", timeout=6)

    @work(exit_on_error=False)
    async def _action_broadcast(self) -> None:
        """PH16 [BROADCAST]: fan-out to every known sibling slug except sender."""
        result: SwarmModalResult | None = await self.push_screen_wait(SwarmModal(kind="broadcast"))
        if not result:
            return
        from_slug = self._current_agent_slug()
        try:
            paths = _broadcast(
                from_slug=from_slug,
                subject=result.subject,
                body=result.body,
                project_hint=self._current_project_key() or "",
            )
            self.notify(f"broadcast → {len(paths)} siblings", timeout=4)
        except Exception as e:
            self.notify(f"broadcast failed: {e}", severity="error", timeout=6)

    def _current_agent_slug(self) -> str:
        """Return the slug for the focused pane (or 'forge' if none)."""
        cur = self._tabs.current_pane
        if cur and getattr(cur, "agent_name", None):
            return cur.agent_name.lower().replace(" ", "-")
        return "forge"

    def _current_project_key(self) -> str | None:
        cur = self._tabs.current_pane
        return getattr(cur, "project_key", None) if cur else None

    @work(exit_on_error=False)
    async def _action_host_switch(self, target_host: str) -> None:
        """PH10 :host switch — terminate current subprocess, respawn with the
        other host on the same project + same agent name.

        Matches jcode multi-provider parity. The pane stays mounted; only its
        underlying subprocess changes. RichLog buffer is preserved (operator
        can scroll back to see the prior host's output).
        """
        cur = self._tabs.current_pane
        if not cur:
            self.notify("no active pane to switch", severity="warning", timeout=4)
            return
        target_host = target_host.lower()
        if target_host not in ("claude", "codex"):
            self.notify(f"invalid host: {target_host}", severity="error")
            return

        # Terminate the existing subprocess (if any). pane.subprocess may be
        # None when the pane was mounted empty (project root missing on disk).
        if cur.subprocess is not None:
            try:
                await cur.subprocess.terminate()
            except Exception as e:
                cur.write_line(f"[yellow]warning: terminate failed: {e}[/]")

        # Synthesize a PickerResult-equivalent and re-build a subprocess.
        synthetic = PickerResult(
            project_key=cur.project_key,
            project_display=cur.project_display,
            objective=cur.mode,
            token_mode="compact",
            speed="turbo",
            host=target_host,
            agent_name=cur.agent_name,
            accent=cur.accent,
            focus="",
        )
        new_sub = _build_subprocess(synthetic)
        if new_sub is None:
            cur.write_line(
                f"[red]:host {target_host} aborted — no source tree for "
                f"{cur.project_display}[/]"
            )
            self.notify(f":host {target_host} aborted - no source tree", severity="warning")
            return

        cur.subprocess = new_sub
        cur.write_line(
            f"[bold]:host {target_host}[/] — respawning with {new_sub.binary_name}"
        )
        self.run_worker(cur.run_subprocess(), exclusive=False,
                        name=f"sub-{cur.agent_name}-{target_host}")
        self.notify(f"switched {cur.agent_name} → {target_host}", timeout=4)


if __name__ == "__main__":
    ForgeApp().run()
