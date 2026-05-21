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
from forge.theme import THEME_CSS, PURPLE_BRIGHT, PROJECT_BORDER_PALETTE
from forge.panes.chrome import ChromeBar, ProjectChip, StatusFooter
from forge.panes.memory_panel import MemoryPanel
from forge.panes.command_palette import CommandPalette
from forge.panes.tabs import TabbedMultiPane
from forge.panes.niri_workspace import NiriWorkspaceGrid
from forge.panes.agent_pane import AgentPane
from forge.panes.picker import AgentPicker, PickerResult
from forge.panes.swarm_modal import SwarmModal, SwarmModalResult
from forge.panes.sidebar import Sidebar
from forge.panes.adb_panel import AdbPanel
from forge.panes.workstation_panel import WorkstationPanel
from forge.panes.toolbar import Toolbar
from forge.panes.statusbar import Statusbar
from forge.swarm import send_dm as _send_dm, broadcast as _broadcast
from forge.projects import get_project
from forge.spawn.base import SpawnConfig
from forge.spawn.claude import ClaudeSubprocess
from forge.spawn.codex import CodexSubprocess


def _compose_phrase(*, project_key: str, agent_name: str, objective: str,
                    token_mode: str, speed: str, focus: str) -> str:
    """Build the opening phrase the Claude/Codex CLI gets as its first message.

    Uses ABSOLUTE path to the Sanctum contracts file so it works regardless of
    which project root the subprocess is spawned in. If contracts file missing
    on disk, omit the reference entirely so the agent doesn't crash trying to
    read a non-existent path.
    """
    import os as _os
    sanctum_root = _os.environ.get("SANCTUM_ROOT") or r"D:\Sinister Sanctum"
    contracts_path = Path(sanctum_root) / "automations" / "session-contracts.md"
    contracts = (f"Read {contracts_path} (6 binding contracts)."
                 if contracts_path.exists() else "")
    focus_block = f"\n\nFocus: {focus}" if focus else ""
    bits = [
        f"You are {agent_name}, the Sinister {project_key} lane agent via Forge.",
        f"Mode={objective}, TokenMode={token_mode}, Speed={speed}.",
    ]
    if contracts:
        bits.append(contracts)
    return " ".join(bits) + f"{focus_block}\n\nStart the loop."


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

    # Operator directive 2026-05-21: Sinister Panel chrome globally — every
    # screen mounts inheriting THEME_CSS (purple gradient + rounded borders
    # + glyph icons). See forge/theme.py for the canonical CSS string.
    CSS = THEME_CSS
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
        # Sinister Panel sidebar state — tracks which right-side view is mounted.
        # "agents" = TabbedMultiPane (default), "adb" = AdbPanel,
        # "workstation" = WorkstationPanel (RKOJ launcher stub).
        self._sidebar_active = "agents"
        self._adb_panel: AdbPanel | None = None
        self._workstation_panel: WorkstationPanel | None = None

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
        """Remove boot screen, mount the real workspace.

        Layout (left-to-right):
          [Sidebar]  [TabbedMultiPane or AdbPanel]  [optional MemoryPanel]
        The Sidebar posts Sidebar.TabSelected when the operator clicks a tab;
        on_sidebar_tab_selected swaps the right-side content between
        TabbedMultiPane (agents) and AdbPanel (adb).
        """
        self._boot.remove()
        # jcode chrome parity: top Toolbar + bottom Statusbar bracket the workspace.
        # Both widgets use dock: top / dock: bottom so they sit outside the Horizontal
        # workspace and never compete for vertical space with the sidebar / tabs.
        self._toolbar = Toolbar()
        await self.mount(self._toolbar, after=self._chip)
        self._statusbar = Statusbar()
        await self.mount(self._statusbar)
        # Workspace = horizontal split: sidebar + main content + optional memory panel
        self._workspace = Horizontal(id="workspace")
        await self.mount(self._workspace, after=self._toolbar)
        # Left rail (Sinister Panel-style)
        self._sidebar = Sidebar(active=self._sidebar_active)
        await self._workspace.mount(self._sidebar)
        # Right-side content: default to the niri-style workspace grid (v1.1.0
        # of niri-scrollable-column-pattern). Each workspace = a Vertical column
        # holding 1..N AgentPanes. Horizontal scroll with snap, Ctrl+1..9 jump,
        # Ctrl+T new ws, Ctrl+Left/Right move focus, Ctrl+Shift+Left/Right move
        # pane between ws. Operator directive 2026-05-21 — niri-wm port.
        # TabbedMultiPane still imported for fallback / legacy reference.
        self._tabs = NiriWorkspaceGrid()
        await self._workspace.mount(self._tabs)
        # Default project chip shows "no project"
        self._chip.set_project("", PURPLE_BRIGHT)
        self._booted = True
        self._refresh_status()

        # Welcome notification
        self.notify(
            "Ctrl+W to spawn · Ctrl+P palette · Ctrl+M memory · F1 help",
            timeout=4,
        )

        # Auto-spawn from RKOJ.exe picker env vars (the picker stashes the
        # operator's picks in SINISTER_PROJECT etc. so Forge boots into the
        # right lane without the operator hitting Ctrl+W again).
        await self._auto_spawn_from_env()

    async def _auto_spawn_from_env(self) -> None:
        """If the operator picked a project via RKOJ.exe picker, spawn it now.

        Optional SINISTER_TOOLS=swarm,memory,... triggers extras:
          - swarm → spawn 3 additional siblings on the same project
          - login → drop a /login providers cheat-sheet into the first pane

        Fallback (operator screenshot 27 of v1.2.0 — "no project selected"):
        if no SINISTER_PROJECT env var was set by the picker AND the operator
        has not opted out via RKOJ_NO_AUTOSPAWN=1, default-spawn an EVE agent
        on the `sanctum` project in resume mode after a 200ms settle. This
        populates ws 1 immediately so the console is never empty on cold boot.
        """
        import os
        proj_key = os.environ.get("SINISTER_PROJECT", "").strip()
        if not proj_key:
            # No env-driven pick. Fall back to default-spawn unless opted out.
            if os.environ.get("RKOJ_NO_AUTOSPAWN", "").strip() == "1":
                return
            default_result = PickerResult(
                project_key="sanctum",
                project_display="Sinister Sanctum",
                objective="resume",
                token_mode="compact",
                speed="turbo",
                host="claude",
                agent_name="EVE on Sinister Sanctum",
                accent="purple",
                focus="",
            )
            self.set_timer(
                0.2,
                lambda r=default_result: self.run_worker(
                    self._spawn_from_result(r),
                    exclusive=False,
                    name="default-autospawn",
                ),
            )
            return
        proj_display = os.environ.get("SINISTER_PROJECT_DISPLAY", proj_key).strip() or proj_key
        mode = os.environ.get("SINISTER_MODE", "resume").strip() or "resume"
        tools = {t.strip() for t in os.environ.get("SINISTER_TOOLS", "").split(",") if t.strip()}
        # Synthesize a PickerResult and drive the same spawn path as Ctrl+W.
        agent_name = f"EVE on {proj_display}"
        accent = "purple"
        result = PickerResult(
            project_key=proj_key,
            project_display=proj_display,
            objective=mode,
            token_mode="compact",
            speed="turbo",
            host="claude",
            agent_name=agent_name,
            accent=accent,
            focus="",
        )
        await self._spawn_from_result(result)
        # Swarm-pre-spawn: 2 sibling agents (total 3).
        if "swarm" in tools:
            for n in (2, 3):
                sib = PickerResult(
                    project_key=proj_key, project_display=proj_display,
                    objective=mode, token_mode="compact", speed="turbo",
                    host="claude", agent_name=f"EVE-{n} on {proj_display}",
                    accent=accent, focus="",
                )
                await self._spawn_from_result(sib)
        self.notify(f"booted into {proj_display} ({mode})  ·  /help for commands", timeout=5)

    async def _spawn_from_result(self, result: PickerResult) -> None:
        """The spawn body shared by action_new_agent + auto-spawn."""
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
            self.run_worker(pane.run_subprocess(), exclusive=False, name=f"sub-{result.agent_name}")

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

    # ---------- sidebar (Sinister Panel) ----------

    async def on_sidebar_tab_selected(self, event: "Sidebar.TabSelected") -> None:
        """Swap the right-side content based on which sidebar tab was clicked.

        agents      → NiriWorkspaceGrid (existing agent UI; subprocesses kept alive)
        adb         → AdbPanel (live `adb devices -l` grid)
        workstation → WorkstationPanel (RKOJ launcher stub)

        State is preserved across switches via display toggling (Textual's
        .remove() is destructive); each panel is mounted lazily on first use.
        """
        if not self._booted:
            return
        new_tab = event.tab
        if new_tab == self._sidebar_active:
            return
        self._sidebar_active = new_tab

        # Hide every right-side panel; we'll re-show the active one below.
        self._tabs.display = False
        if self._adb_panel is not None:
            self._adb_panel.display = False
        if self._workstation_panel is not None:
            self._workstation_panel.display = False

        if new_tab == "adb":
            if self._adb_panel is None:
                self._adb_panel = AdbPanel()
                await self._workspace.mount(self._adb_panel, after=self._sidebar)
            else:
                self._adb_panel.display = True
            self.notify("ADB devices view", timeout=2)
        elif new_tab == "workstation":
            if self._workstation_panel is None:
                self._workstation_panel = WorkstationPanel()
                await self._workspace.mount(self._workstation_panel, after=self._sidebar)
            else:
                self._workstation_panel.display = True
            self.notify("RKOJ workstation view", timeout=2)
        else:  # "agents"
            self._tabs.display = True
            self.notify("agents view", timeout=2)

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
        # Legacy: when TabbedMultiPane was the host, switch to the "All" tab.
        # Under NiriWorkspaceGrid the equivalent is "jump to workspace 1".
        if getattr(self._tabs, "_tabbed", None):
            self._tabs._tabbed.active = "tab-all"
        elif hasattr(self._tabs, "jump_to"):
            self._tabs.jump_to(1)

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
