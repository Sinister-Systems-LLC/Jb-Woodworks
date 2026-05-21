# Sinister Forge :: spawn/codex.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
from forge.spawn.base import AgentSubprocess


class CodexSubprocess(AgentSubprocess):
    @property
    def binary_name(self) -> str:
        return "codex"

    def build_argv(self) -> list[str]:
        return ["codex", "-q", self.cfg.phrase]
