# Sinister Forge :: spawn/__init__.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import shutil
from forge.spawn.base import AgentSubprocess, SpawnConfig
from forge.spawn.claude import ClaudeSubprocess
from forge.spawn.codex import CodexSubprocess


def make_subprocess(host: str, cfg: SpawnConfig) -> AgentSubprocess:
    host = (host or "claude").lower()
    if host == "codex" and (shutil.which("codex") or shutil.which("codex.cmd")):
        return CodexSubprocess(cfg)
    return ClaudeSubprocess(cfg)


__all__ = ["make_subprocess", "AgentSubprocess", "SpawnConfig", "ClaudeSubprocess", "CodexSubprocess"]
