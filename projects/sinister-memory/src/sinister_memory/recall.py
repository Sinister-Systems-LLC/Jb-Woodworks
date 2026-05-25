# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: recall.

BM25 search over the FTS5 index built by indexer.py. Optionally augments with
Ruflo MCP hierarchical-recall when the MCP is reachable in-process; gracefully
falls back to FTS5-only otherwise.

Public API:
  recall(query, db_path, limit=5, layers=None, agent=None) -> list[Hit]

Hit is a NamedTuple: (layer, slug, path, line, snippet, score).

Empty index, missing db, malformed query (FTS5 chokes on unbalanced quotes) all
return [] rather than raising — caller code is expected to treat 'no hits' as
'no information', not 'error'.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import NamedTuple, Optional, Sequence


class Hit(NamedTuple):
    layer: str
    slug: str
    path: str
    line: str
    snippet: str
    score: float


def _sanitize_fts5(query: str) -> str:
    """Strip characters that break FTS5 parser. Tokens are space-joined back.

    FTS5 reserves: ( ) " * : - . AND OR NOT NEAR
    We strip / quote them defensively so callers can pass arbitrary user text.
    """
    if not query or not query.strip():
        return ""
    bad = set('()"*:^')
    cleaned = "".join(c if c not in bad else " " for c in query)
    tokens = [t for t in cleaned.split() if t and t.upper() not in {"AND", "OR", "NOT", "NEAR"}]
    if not tokens:
        return ""
    # Quote each token individually so it's treated as a literal phrase
    return " ".join(f'"{t}"' for t in tokens)


def recall(
    query: str,
    db_path: Path,
    limit: int = 5,
    layers: Optional[Sequence[str]] = None,
    agent: Optional[str] = None,
) -> list[Hit]:
    """Run BM25 over the FTS5 index. Returns up to `limit` Hits, ranked best-first.

    Args:
      query  : user-supplied text (sanitized for FTS5)
      db_path: path to index.db (must exist; missing -> [])
      limit  : max hits
      layers : optional whitelist of layers ("brain"/"progress"/"heartbeat"/"per-agent")
      agent  : optional slug filter; matches `progress` + `per-agent` rows for that slug
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    sanitized = _sanitize_fts5(query)
    if not sanitized:
        return []

    sql = (
        "SELECT layer, slug, path, line, snippet, bm25(memories) AS score "
        "FROM memories WHERE memories MATCH ?"
    )
    params: list = [sanitized]

    if layers:
        placeholders = ",".join("?" for _ in layers)
        sql += f" AND layer IN ({placeholders})"
        params.extend(layers)

    if agent:
        sql += " AND (slug = ? OR layer = 'brain')"
        params.append(agent)

    sql += " ORDER BY score LIMIT ?"
    params.append(limit)

    conn = sqlite3.connect(str(db_path))
    try:
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []
    finally:
        conn.close()

    return [Hit(*row) for row in rows]


def try_ruflo_augment(query: str, fts_hits: list[Hit], limit: int = 5) -> list[Hit]:
    """Best-effort: if Ruflo MCP is reachable in this process, merge in
    hierarchical-recall hits. P0 stub — returns fts_hits unchanged.

    This stub exists so callers can rely on the API surface; P3 wires the real
    MCP call (`mcp__ruflo__agentdb_hierarchical-recall`) via a feature-detected
    import of the ruflo client. Today, the MCP tool family is only callable from
    the Claude harness, not from a stand-alone Python process, so P0 ships
    FTS5-only.
    """
    return fts_hits


def apply_gap_filter(hits: Sequence[Hit], drop_ratio: float = 0.25, min_kept: int = 1) -> list[Hit]:
    """Drop the noise tail when there's a large relative score drop between
    consecutive hits. Cherry-picked from jcode v0.12.4 src/memory.rs:724-746.

    Args:
      hits      : hits already sorted best-first. Hit.score stores -relevance so
                  smaller absolute score == better; positive relevance == -score.
      drop_ratio: when the relative drop between consecutive relevances exceeds
                  this fraction of the top relevance, truncate.
      min_kept  : never drop below this many results.

    Returns the truncated list (preserves input order).
    """
    if len(hits) <= min_kept:
        return list(hits)
    relevances = [-h.score for h in hits]
    top = relevances[0] if relevances else 0.0
    if top <= 0:
        return list(hits)
    cutoff = len(hits)
    for i in range(1, len(hits)):
        gap = relevances[i - 1] - relevances[i]
        if gap > drop_ratio * top:
            cutoff = i
            break
    return list(hits[: max(cutoff, min_kept)])


def format_hits_markdown(hits: list[Hit]) -> str:
    """Render hits as a markdown list for CLI output or spawn-phrase embedding."""
    if not hits:
        return "_(no memories matched)_"
    lines: list[str] = []
    for h in hits:
        path_rel = h.path
        loc = f"{path_rel}:{h.line}"
        lines.append(f"- **[{h.layer}]** `{h.slug or '--'}` `{loc}` -- {h.snippet}")
    return "\n".join(lines)
