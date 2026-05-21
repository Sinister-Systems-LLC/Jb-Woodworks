# Sinister Forge :: spawn/base.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import asyncio
import os
import subprocess
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SpawnConfig:
    project_key: str
    project_root: Path
    agent_name: str
    accent_color: str
    mode: str
    phrase: str
    token_mode: str = "compact"
    speed: str = "turbo"
    extra_env: dict[str, str] = field(default_factory=dict)


class AgentSubprocess(ABC):
    def __init__(self, cfg: SpawnConfig) -> None:
        self.cfg = cfg
        self.process: asyncio.subprocess.Process | None = None
        self._exit_code: int | None = None

    @property
    @abstractmethod
    def binary_name(self) -> str: ...

    @abstractmethod
    def build_argv(self) -> list[str]: ...

    async def spawn(self) -> None:
        argv = self.build_argv()
        env = self._compose_env()
        try:
            self.process = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # stdin=DEVNULL so Claude CLI doesn't sit waiting for stdin
                # input after we pass the prompt positionally. Operator-reported
                # 2026-05-21: "Warning: no stdin data received in 3s, proceeding
                # without it" because Claude treats PIPE'd stdin as interactive
                # mode and blocks. We pass the opening prompt via build_argv()
                # positional, so no stdin input is needed.
                # When PH-interactive lands, switch this back to PIPE and have
                # send_line() feed lines from a pane input widget.
                stdin=asyncio.subprocess.DEVNULL,
                cwd=str(self.cfg.project_root),
                env=env,
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"{self.binary_name} not on PATH. Install + retry, or pick a different Agent Host."
            ) from e

    def _compose_env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["SINISTER_AGENT_NAME"] = self.cfg.agent_name
        env["SINISTER_ACCENT_COLOR"] = self.cfg.accent_color
        env["SINISTER_PROJECT_KEY"] = self.cfg.project_key
        env["SINISTER_MODE"] = self.cfg.mode
        env["SINISTER_TOKEN_MODE"] = self.cfg.token_mode
        env["SINISTER_SPEED"] = self.cfg.speed
        env.update(self.cfg.extra_env)
        return env

    async def tail_stdout(self) -> AsyncIterator[str]:
        if not self.process or not self.process.stdout:
            return
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            yield line.decode("utf-8", errors="replace").rstrip("\n")

    async def tail_stderr(self) -> AsyncIterator[str]:
        if not self.process or not self.process.stderr:
            return
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
            yield "[stderr] " + line.decode("utf-8", errors="replace").rstrip("\n")

    async def send_line(self, text: str) -> None:
        if self.process and self.process.stdin:
            self.process.stdin.write((text + "\n").encode("utf-8"))
            await self.process.stdin.drain()

    async def wait(self) -> int:
        if self.process:
            self._exit_code = await self.process.wait()
            return self._exit_code
        return -1

    async def terminate(self) -> None:
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self.process.kill()
                except Exception:
                    pass

    @property
    def status(self) -> str:
        if not self.process:
            return "not started"
        if self.process.returncode is None:
            return "running"
        return f"exited ({self.process.returncode})"
