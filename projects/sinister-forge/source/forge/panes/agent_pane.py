# Sinister Forge :: panes/agent_pane.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import asyncio

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import RichLog, Static

from forge.spawn.base import AgentSubprocess
from forge.theme import AGENT_ACCENTS


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

    def compose(self) -> ComposeResult:
        accent_hex = AGENT_ACCENTS.get(self.accent, AGENT_ACCENTS["purple"])
        self._header = Static(self._header_text(), classes="agent-header", markup=True)
        yield self._header
        self._log = RichLog(highlight=True, markup=True, wrap=False, auto_scroll=True)
        self._log.write(f"[bold {accent_hex}]Sinister Forge[/] :: agent pane ready")
        self._log.write(f"[dim]Project: {self.project_display} ({self.mode})[/dim]")
        if self.subprocess:
            self._log.write(f"[dim]Spawning {self.subprocess.binary_name}...[/dim]")
        yield self._log

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
