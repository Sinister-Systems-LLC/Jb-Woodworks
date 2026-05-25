# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: decay.

Time-decay scoring layer on top of BM25. Boosts recent memories so a fresh
PROGRESS row beats a 30-day-old brain entry of equal BM25 relevance.

Half-life model: weight = 0.5 ** (age_days / half_life_days)
Final score    : (1 + alpha * weight) * (-bm25)   [BM25 is negative; lower = better]

Pure-function module; no schema changes. Composes with recall.recall + indexer
mtime column.

Public API:
  decay_weight(age_days, half_life_days=30.0)  -> float in (0, 1]
  apply_decay(hits, now_ts, alpha=0.5, half_life_days=30.0) -> ranked list[Hit]
  recall_with_decay(query, db_path, **kwargs) -> list[Hit]   # convenience wrapper
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Sequence

from .recall import Hit, _sanitize_fts5


# Per-category half-lives (days). Cherry-picked from jcode v0.12.4
# MEMORY_ARCHITECTURE.md:419-423 (see brain entry jcode-memory-audit-and-cherry-picks-2026-05-25).
# Rationale: a Correction memory ("we DON'T use bat files") should outlive a
# transient Fact ("port 7421 is currently free"). Inferred guesses decay fastest
# so they get re-derived from fresh data.
HALF_LIVES: dict[str, float] = {
    "correction": 365.0,
    "preference": 90.0,
    "procedure": 60.0,
    "fact": 30.0,
    "entity": 30.0,
    "inferred": 7.0,
}
DEFAULT_HALF_LIFE_DAYS: float = 30.0


def half_life_for(category: Optional[str]) -> float:
    """Map a MemoryCategory string to its half-life. Unknown -> DEFAULT_HALF_LIFE_DAYS."""
    if not category:
        return DEFAULT_HALF_LIFE_DAYS
    return HALF_LIVES.get(category.strip().lower(), DEFAULT_HALF_LIFE_DAYS)


def decay_weight(age_days: float, half_life_days: float = DEFAULT_HALF_LIFE_DAYS) -> float:
    """Exponential half-life. age=0 -> 1.0; age=half_life -> 0.5; age=2*half_life -> 0.25."""
    if half_life_days <= 0:
        return 1.0
    age = max(0.0, float(age_days))
    return 0.5 ** (age / half_life_days)


def _mtime_for_path(conn: sqlite3.Connection, path: str) -> float:
    row = conn.execute("SELECT mtime FROM files WHERE path = ?", (path,)).fetchone()
    return float(row[0]) if row else 0.0


def apply_decay(
    hits: Sequence[Hit],
    now_ts: float,
    db_path: Path,
    alpha: float = 0.5,
    half_life_days: float = 30.0,
) -> list[Hit]:
    """Re-rank `hits` by combined BM25 + decay weight. Returns new list, best-first.

    BM25 score is negative (lower = more relevant). We invert to positive, multiply
    by (1 + alpha * decay_weight), then re-sort descending.
    """
    if not hits:
        return []
    db_path = Path(db_path)
    if not db_path.exists():
        return list(hits)
    conn = sqlite3.connect(str(db_path))
    try:
        scored: list[tuple[float, Hit]] = []
        for h in hits:
            mt = _mtime_for_path(conn, h.path)
            age_days = max(0.0, (now_ts - mt) / 86400.0) if mt else 365.0
            w = decay_weight(age_days, half_life_days)
            # BM25: lower is better. Convert to positive relevance, then boost.
            relevance = -h.score
            boosted = relevance * (1.0 + alpha * w)
            # Stuff the boosted score into the Hit's score field for downstream sorting
            scored.append((boosted, h._replace(score=-boosted)))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [t[1] for t in scored]
    finally:
        conn.close()


def recall_with_decay(
    query: str,
    db_path: Path,
    limit: int = 5,
    layers: Optional[Sequence[str]] = None,
    agent: Optional[str] = None,
    alpha: float = 0.5,
    half_life_days: Optional[float] = None,
    category: Optional[str] = None,
    now_ts: Optional[float] = None,
    pool_multiplier: int = 4,
    gap_filter: bool = False,
) -> list[Hit]:
    """Convenience wrapper: pulls `pool_multiplier * limit` BM25 hits, re-ranks
    with decay, returns top `limit`.

    If `category` is set and `half_life_days` is None, the per-category half-life
    table (HALF_LIVES) is used. Otherwise `half_life_days` (or DEFAULT_HALF_LIFE_DAYS)
    applies.

    `gap_filter=True` invokes the jcode-style gap filter to drop the noise tail
    when there's a >=25% relative score drop (cite recall.apply_gap_filter).

    `now_ts` is unix seconds; defaults to current time.
    """
    import time

    from .recall import apply_gap_filter, recall

    if now_ts is None:
        now_ts = time.time()
    if half_life_days is None:
        half_life_days = half_life_for(category)

    pool = max(limit, limit * max(1, pool_multiplier))
    raw = recall(query=query, db_path=db_path, limit=pool, layers=layers, agent=agent)
    ranked = apply_decay(raw, now_ts=now_ts, db_path=db_path, alpha=alpha, half_life_days=half_life_days)
    if gap_filter:
        ranked = apply_gap_filter(ranked)
    return ranked[:limit]


__all__ = [
    "decay_weight",
    "apply_decay",
    "recall_with_decay",
    "half_life_for",
    "HALF_LIVES",
    "DEFAULT_HALF_LIFE_DAYS",
]

# Keep the _sanitize_fts5 import alive so static analyzers don't strip recall import.
_ = _sanitize_fts5
