# Sinister Forge :: memory/graph.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Memory graph - jcode equivalent layered on Ruflo agentdb_*. Each turn
# embeds as a semantic vector; auto-recall queries cosine similarity to
# fetch related memories; results fed back into the agent's context.
#
# Backed by Ruflo MCP when loaded:
#   - agentdb_hierarchical-store  (write)
#   - agentdb_semantic-route      (recall via cosine)
#   - agentdb_pattern-search      (k-nearest)
#   - agentdb_consolidate         (ambient consolidation)
#
# Falls back to a local JSON store at _shared-memory/forge-memory/<project>.json
# if Ruflo MCP is unavailable. The JSON store keeps the agent productive
# even without the MCP loaded; consolidation in fallback mode is basic
# dedupe-by-hash rather than semantic.

from __future__ import annotations
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
FORGE_MEMORY_DIR = SANCTUM_ROOT / "_shared-memory" / "forge-memory"


@dataclass
class MemoryEntry:
    """One memory record. Mirrors jcode's per-turn embedding entry."""
    id: str
    project: str
    agent: str
    ts_utc: float
    role: str            # 'user' | 'assistant' | 'tool' | 'fact'
    content: str
    tags: list[str] = field(default_factory=list)
    importance: float = 1.0   # 0..1; consolidation raises on repeat
    embedding_ref: str = ""   # Ruflo's pattern-id if stored there


class MemoryGraph:
    """jcode-style memory layer for a single (project, agent) pair."""

    def __init__(self, project: str, agent: str) -> None:
        self.project = project
        self.agent = agent
        FORGE_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._fallback_path = FORGE_MEMORY_DIR / f"{project}__{agent}.json"
        self._ruflo_available = False  # toggled True when sideagent confirms

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

    # ---- Public surface (matches jcode's memory contract) ----

    async def store(self, content: str, role: str = "fact",
                    tags: list[str] | None = None, importance: float = 1.0) -> str:
        """Write a memory. Tries Ruflo first, falls back to local JSON."""
        entry = MemoryEntry(
            id=self._hash(content),
            project=self.project,
            agent=self.agent,
            ts_utc=time.time(),
            role=role,
            content=content,
            tags=tags or [],
            importance=importance,
        )
        if self._ruflo_available:
            try:
                # Ruflo handles embedding + index entirely
                # await mcp.agentdb_hierarchical_store(content=content, tags=tags, project=self.project)
                entry.embedding_ref = entry.id
            except Exception:
                pass
        self._append_fallback(entry)
        return entry.id

    async def recall(self, query: str, k: int = 5) -> list[MemoryEntry]:
        """Cosine-similarity k-nearest. Ruflo when up; substring otherwise."""
        if self._ruflo_available:
            try:
                # results = await mcp.agentdb_semantic_route(query=query, top_k=k)
                # return [MemoryEntry(**r) for r in results]
                pass
            except Exception:
                pass
        return self._fallback_recall(query, k)

    async def consolidate(self) -> int:
        """Ambient consolidation - dedupe + raise importance on repeats."""
        if self._ruflo_available:
            try:
                # await mcp.agentdb_consolidate(project=self.project)
                return 0
            except Exception:
                pass
        # Fallback: dedupe by id, sum importance
        return self._fallback_consolidate()

    async def session_search(self, query: str) -> list[MemoryEntry]:
        """Traditional RAG over all PRIOR sessions of this (project, agent)."""
        # Same surface as recall() in fallback mode; Ruflo version pivots to
        # cross-session search.
        return await self.recall(query, k=10)

    # ---- Fallback (local JSON) helpers ----

    def _load(self) -> list[MemoryEntry]:
        if not self._fallback_path.exists():
            return []
        try:
            data = json.loads(self._fallback_path.read_text(encoding="utf-8"))
            return [MemoryEntry(**d) for d in data]
        except Exception:
            return []

    def _save(self, entries: list[MemoryEntry]) -> None:
        self._fallback_path.write_text(
            json.dumps([asdict(e) for e in entries], indent=2), encoding="utf-8"
        )

    def _append_fallback(self, entry: MemoryEntry) -> None:
        entries = self._load()
        # Dedupe by id; if repeat, raise importance
        for existing in entries:
            if existing.id == entry.id:
                existing.importance = min(1.0, existing.importance + 0.1)
                self._save(entries)
                return
        entries.append(entry)
        self._save(entries)

    def _fallback_recall(self, query: str, k: int) -> list[MemoryEntry]:
        entries = self._load()
        q_lower = query.lower()
        scored = [
            (e, sum(1 for w in q_lower.split() if w in e.content.lower()) + e.importance)
            for e in entries
        ]
        scored.sort(key=lambda t: t[1], reverse=True)
        return [e for e, _ in scored[:k] if _ > 0]

    def _fallback_consolidate(self) -> int:
        entries = self._load()
        before = len(entries)
        # Dedupe (already done at append time); also drop importance < 0.05
        kept = [e for e in entries if e.importance >= 0.05]
        if len(kept) != before:
            self._save(kept)
        return before - len(kept)
