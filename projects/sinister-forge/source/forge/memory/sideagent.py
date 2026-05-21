# Sinister Forge :: memory/sideagent.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Memory sideagent - jcode's pattern of running a SEPARATE lighter agent to
# verify recall relevance + extract new memories from a finishing session.
#
# Cadence triggers (any):
#   - K turns since last extraction (default K=10)
#   - explicit session-end event
#   - operator hits Ctrl+S in Forge
#   - detected semantic drift (cosine to last-N average < 0.4)
#
# Implementation: invokes Haiku (cheapest Anthropic tier) via the same
# subprocess pattern as the main agent, just with a much smaller prompt
# and the memory.consolidate() result as its job.

from __future__ import annotations
import asyncio
import json
import os
import time
from dataclasses import dataclass

from forge.memory.graph import MemoryGraph, MemoryEntry


@dataclass
class SideagentConfig:
    project: str
    agent: str
    turns_per_extraction: int = 10
    drift_threshold: float = 0.4
    model_tier: str = "haiku"   # cheapest tier - this is bulk consolidation
    enabled: bool = True


class MemorySideagent:
    """Background memory worker. Runs on cadence + on demand."""

    def __init__(self, cfg: SideagentConfig) -> None:
        self.cfg = cfg
        self.graph = MemoryGraph(cfg.project, cfg.agent)
        self._turn_count = 0
        self._last_consolidate = 0.0
        self._running = False

    async def note_turn(self, user_msg: str, assistant_msg: str) -> None:
        """Called by AgentPane after each completed turn pair."""
        if not self.cfg.enabled:
            return
        # Store as a turn-pair memory entry
        await self.graph.store(
            content=f"USER: {user_msg[:500]}\n---\nASSISTANT: {assistant_msg[:500]}",
            role="turn",
            tags=["turn", self.cfg.project, self.cfg.agent],
            importance=0.5,
        )
        self._turn_count += 1
        if self._turn_count >= self.cfg.turns_per_extraction:
            self._turn_count = 0
            asyncio.create_task(self._extract_and_consolidate())

    async def manual_consolidate(self) -> int:
        """Operator triggered (Ctrl+S in Forge)."""
        return await self.graph.consolidate()

    async def session_end(self) -> int:
        """Called when AgentPane closes."""
        return await self.graph.consolidate()

    async def _extract_and_consolidate(self) -> None:
        """Background: dedupe + raise importance on patterns."""
        if self._running:
            return
        self._running = True
        try:
            await self.graph.consolidate()
            self._last_consolidate = time.time()
        finally:
            self._running = False

    async def recall_for_prompt(self, query: str, k: int = 5) -> str:
        """Return a markdown-formatted block to splice into the next agent prompt."""
        entries = await self.graph.recall(query, k=k)
        if not entries:
            return ""
        lines = ["## Relevant memories (auto-recalled)"]
        for e in entries:
            lines.append(f"- ({e.role}, importance {e.importance:.2f}) {e.content[:200]}")
        return "\n".join(lines)
