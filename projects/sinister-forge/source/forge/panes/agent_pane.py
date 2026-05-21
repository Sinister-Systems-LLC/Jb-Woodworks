# Sinister Forge :: panes/agent_pane.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# AgentPane = pane-local UI for one spawned agent. Layout:
#   header (project + agent name + mode + status)
#   RichLog (forever-scroll stdout/stderr buffer)
#   Input (PH-interactive: pane-local `:` builtins + forward-to-subprocess)
#
# Builtins parsed inline (start with `:`):
#   :dm <slug> <message...>
#   :broadcast <message...>
#   :host claude|codex
#   :swarm <N>            -> spawn N parallel agents on this pane's project
#   :clear                -> clear RichLog
#   :help                 -> list inline commands
# Anything not starting with `:` is forwarded to the subprocess stdin via
# send_line() (works once base.py flips stdin back to PIPE for interactive
# mode; current spawn uses DEVNULL so non-:-prefixed input is buffered until
# the operator re-spawns under interactive mode).

from __future__ import annotations
import asyncio
import shlex
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, RichLog, Static

from forge.spawn.base import AgentSubprocess
from forge.theme import AGENT_ACCENTS

if TYPE_CHECKING:
    from forge.app import ForgeApp


class AgentPane(Vertical):
    def __init__(self, agent_name: str, project_display: str, mode: str,
                 accent: str = "purple", subprocess: AgentSubprocess | None = None,
                 project_key: str = "") -> None:
        super().__init__(classes="agent-pane")
        self.agent_name = agent_name
        self.project_display = project_display
        self.project_key = project_key or project_display.lower()
        self.mode = mode
        self.accent = accent
        self.subprocess = subprocess
        self._status = "ready"
        self._header: Static | None = None
        self._log: RichLog | None = None
        self._input: Input | None = None

    def compose(self) -> ComposeResult:
        accent_hex = AGENT_ACCENTS.get(self.accent, AGENT_ACCENTS["purple"])
        self._header = Static(self._header_text(), classes="agent-header", markup=True)
        yield self._header
        self._log = RichLog(highlight=True, markup=True, wrap=False, auto_scroll=True)
        self._log.write(f"[bold {accent_hex}]Sinister Forge[/] :: agent pane ready")
        self._log.write(f"[dim]Project: {self.project_display} ({self.mode})[/dim]")
        self._log.write(
            "[dim]inline :  :dm <slug> <msg> · :broadcast <msg> · :host claude|codex · "
            ":swarm <N> · :clear · :help[/dim]"
        )
        if self.subprocess:
            self._log.write(f"[dim]Spawning {self.subprocess.binary_name}...[/dim]")
        yield self._log
        self._input = Input(
            placeholder=": for inline command, otherwise forwards to agent",
            classes="agent-input",
        )
        yield self._input

    def _header_text(self) -> str:
        return (
            f"  [b]{self.project_display.upper()}[/b]  ::  "
            f"[b]{self.agent_name}[/b]  ::  {self.mode}  ::  "
            f"[dim]{self._status}[/dim]  "
        )

    def update_header(self) -> None:
        if self._header:
            self._header.update(self._header_text())

    def write_line(self, line: str) -> None:
        if self._log:
            self._log.write(line)

    def clear_log(self) -> None:
        if self._log:
            self._log.clear()

    # ----- PH-interactive inline command surface -----

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Operator pressed Enter in the pane input. Route by prefix."""
        if event.input is not self._input:
            return
        text = (event.value or "").strip()
        if self._input is not None:
            self._input.value = ""
        if not text:
            return
        if text.startswith("/"):
            # jcode-style slash commands (full registry in forge/commands.py)
            try:
                from forge.commands import dispatch as _slash_dispatch
                app = getattr(self, "app", None)
                out = _slash_dispatch(text, pane=self, app=app)
                if out:
                    self.write_line(out)
            except Exception as e:
                self.write_line(f"[red]slash dispatch crashed: {e}[/]")
            return
        if text.startswith(":"):
            await self._handle_builtin(text[1:].strip())
        else:
            await self._forward_to_subprocess(text)

    async def _handle_builtin(self, body: str) -> None:
        """Parse and dispatch a `:` builtin. body is the text after the colon."""
        try:
            tokens = shlex.split(body, posix=False)
        except ValueError:
            tokens = body.split()
        if not tokens:
            self.write_line("[yellow]empty :command[/]")
            return
        cmd = tokens[0].lower()
        args = tokens[1:]
        if cmd in ("help", "?"):
            self.write_line(
                "[bold]inline builtins[/]\n"
                "  :dm <slug> <message...>  - direct-message a sibling\n"
                "  :broadcast <message...>  - fan out to fleet\n"
                "  :host claude|codex       - switch this pane's host\n"
                "  :swarm <N>               - spawn N parallel agents on this project\n"
                "  :clear                   - clear this pane\n"
                "  :help                    - this message"
            )
            return
        if cmd == "clear":
            self.clear_log()
            return
        if cmd == "dm":
            if len(args) < 2:
                self.write_line("[yellow]usage: :dm <slug> <message...>[/]")
                return
            to_slug = args[0]
            message = " ".join(args[1:]).strip('"').strip("'")
            self._call_app_builtin_dm(to_slug, message)
            return
        if cmd == "broadcast":
            if not args:
                self.write_line("[yellow]usage: :broadcast <message...>[/]")
                return
            message = " ".join(args).strip('"').strip("'")
            self._call_app_builtin_broadcast(message)
            return
        if cmd == "host":
            if not args or args[0].lower() not in ("claude", "codex"):
                self.write_line("[yellow]usage: :host claude|codex[/]")
                return
            self._call_app_builtin_host(args[0].lower())
            return
        if cmd == "swarm":
            n = 3
            if args:
                try:
                    n = max(1, min(int(args[0]), 8))
                except ValueError:
                    self.write_line(f"[yellow]:swarm requires an int, got {args[0]!r}[/]")
                    return
            self._call_app_builtin_swarm(n)
            return
        self.write_line(f"[yellow]unknown :command `{cmd}` (try :help)[/]")

    async def _forward_to_subprocess(self, text: str) -> None:
        """Non-`:` input forwards to subprocess stdin via send_line()."""
        if not self.subprocess:
            self.write_line(
                "[dim]no subprocess attached (empty pane). Use Ctrl+W to spawn one.[/]"
            )
            return
        try:
            await self.subprocess.send_line(text)
            self.write_line(f"[dim]> {text}[/]")
        except Exception as e:
            # base.py currently spawns with stdin=DEVNULL so send_line is a no-op.
            # When PH-interactive flips it back to PIPE the stdin write will land.
            self.write_line(f"[yellow]send_line failed: {e} (stdin may be DEVNULL)[/]")

    # ----- thin app-callbacks (deferred lookup so AgentPane has no app import cycle) -----

    def _call_app_builtin_dm(self, to_slug: str, message: str) -> None:
        from forge.swarm import send_dm as _send_dm
        from_slug = self.agent_name.lower().replace(" ", "-") or "forge"
        try:
            path = _send_dm(
                from_slug=from_slug,
                to_slug=to_slug,
                subject=f"inline-dm-from-{from_slug}",
                body=message,
                project_hint=self.project_key,
            )
            self.write_line(f"[green]:dm → {to_slug} :: {path.name}[/]")
        except Exception as e:
            self.write_line(f"[red]:dm failed: {e}[/]")

    def _call_app_builtin_broadcast(self, message: str) -> None:
        from forge.swarm import broadcast as _broadcast
        from_slug = self.agent_name.lower().replace(" ", "-") or "forge"
        try:
            paths = _broadcast(
                from_slug=from_slug,
                subject=f"inline-broadcast-from-{from_slug}",
                body=message,
                project_hint=self.project_key,
            )
            self.write_line(f"[green]:broadcast → {len(paths)} siblings[/]")
        except Exception as e:
            self.write_line(f"[red]:broadcast failed: {e}[/]")

    def _call_app_builtin_host(self, target_host: str) -> None:
        # Delegate to the App-level action which already does termination +
        # respawn synthesis. Use `self.app` instead of an import to avoid a
        # cycle and to bind to the live app instance.
        try:
            self.app._action_host_switch(target_host)  # type: ignore[attr-defined]
        except AttributeError:
            self.write_line("[red]:host requires the parent app to be ForgeApp[/]")

    def _call_app_builtin_swarm(self, n: int) -> None:
        # Reuse the existing _action_swarm which spawns 3 by default; for now
        # we just call it once. A future PH could parameterize _action_swarm
        # to honor n.
        try:
            self.app._action_swarm()  # type: ignore[attr-defined]
            self.write_line(f"[green]:swarm (default 3) on {self.project_display}[/]")
        except AttributeError:
            self.write_line("[red]:swarm requires the parent app to be ForgeApp[/]")

    async def run_subprocess(self) -> None:
        if not self.subprocess:
            return
        try:
            await self.subprocess.spawn()
            self._status = "running"
            self.update_header()
        except FileNotFoundError as e:
            self._status = "no binary"
            self.update_header()
            self.write_line(f"[red]{e}[/]")
            return

        async def _tail(stream_iter):
            async for line in stream_iter:
                self.write_line(line)

        await asyncio.gather(
            _tail(self.subprocess.tail_stdout()),
            _tail(self.subprocess.tail_stderr()),
        )
        exit_code = await self.subprocess.wait()
        self._status = f"exited ({exit_code})"
        self.update_header()
        self.write_line(f"[dim]Process exited with code {exit_code}.[/dim]")
