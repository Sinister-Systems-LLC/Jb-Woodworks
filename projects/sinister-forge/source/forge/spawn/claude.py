# Sinister Forge :: spawn/claude.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
from forge.spawn.base import AgentSubprocess


class ClaudeSubprocess(AgentSubprocess):
    @property
    def binary_name(self) -> str:
        return "claude"

    def build_argv(self) -> list[str]:
        # `claude` default mode is INTERACTIVE (needs a TTY). With stdin=DEVNULL
        # the process hangs forever — operator-reported "Spawning claude..."
        # never resolving in image 20.
        # `-p / --print` switches to non-interactive streaming: claude prints
        # the response then exits. This is the jcode-style turn-per-line shape.
        return ["claude", "--dangerously-skip-permissions", "-p", self.cfg.phrase]
