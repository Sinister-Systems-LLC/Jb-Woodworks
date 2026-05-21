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
        return ["claude", "--dangerously-skip-permissions", self.cfg.phrase]
