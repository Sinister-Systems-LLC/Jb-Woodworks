# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: supersede.

Memory-graph edges: "memory B supersedes memory A". Lets agents mark older
iter-close memories as stale once a newer one fully replaces them. Cherry-pick
from `memory-audit-jcode-rufus-obsidian-understand-2026-05-24` (Obsidian-style
backlinks).

Schema (lives in the same index.db as the FTS5 memories):
  supersedes(
    new_id TEXT NOT NULL,    -- path or stable id of the replacement
    old_id TEXT NOT NULL,    -- path or stable id of the superseded entry
    reason TEXT,             -- why the replacement happened
    ts_utc TEXT NOT NULL,    -- ISO-8601
    PRIMARY KEY(new_id, old_id)
  )

Public API:
  mark_supersedes(new_id, old_id, reason, db_path) -> None
  chain_for(memory_id, db_path) -> list[dict]   # newest-to-oldest chain
  latest_of(memory_id, db_path) -> str          # walks forward to terminal node
  superseded_set(db_path) -> set[str]           # all ids that have been replaced
  unmark(new_id, old_id, db_path) -> bool       # remove an edge
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence


# EdgeKind taxonomy cherry-picked from jcode v0.12.4 memory_graph.rs:116-125.
# Brain entry: jcode-memory-audit-and-cherry-picks-2026-05-25.
EDGE_KINDS = frozenset({"Supersedes", "Contradicts", "RelatesTo", "HasTag", "InCluster"})


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE IF NOT EXISTS supersedes (
               new_id TEXT NOT NULL,
               old_id TEXT NOT NULL,
               reason TEXT,
               ts_utc TEXT NOT NULL,
               PRIMARY KEY(new_id, old_id)
           )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS edges (
               src_id TEXT NOT NULL,
               dst_id TEXT NOT NULL,
               kind TEXT NOT NULL,
               weight REAL,
               reason TEXT,
               ts_utc TEXT NOT NULL,
               PRIMARY KEY(src_id, dst_id, kind)
           )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS edges_dst_kind ON edges(dst_id, kind)")
    conn.execute("CREATE INDEX IF NOT EXISTS edges_src_kind ON edges(src_id, kind)")
    return conn


def mark_supersedes(new_id: str, old_id: str, reason: str, db_path: Path) -> None:
    """Record new_id supersedes old_id. Cycles are rejected (would create infinite chain_for)."""
    new_id = (new_id or "").strip()
    old_id = (old_id or "").strip()
    if not new_id or not old_id:
        raise ValueError("new_id and old_id must be non-empty")
    if new_id == old_id:
        raise ValueError("a memory cannot supersede itself")

    conn = _connect(db_path)
    try:
        # Cycle check: if old_id (transitively) already supersedes new_id, reject.
        if new_id in _walk_forward(conn, old_id):
            raise ValueError(f"cycle: {old_id} already supersedes {new_id}")
        conn.execute(
            "INSERT OR REPLACE INTO supersedes(new_id, old_id, reason, ts_utc) VALUES(?, ?, ?, ?)",
            (new_id, old_id, reason or "", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        )
        conn.commit()
    finally:
        conn.close()


def unmark(new_id: str, old_id: str, db_path: Path) -> bool:
    """Remove a single edge. Returns True if a row was deleted."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "DELETE FROM supersedes WHERE new_id = ? AND old_id = ?",
            (new_id, old_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def _walk_forward(conn: sqlite3.Connection, start: str, max_depth: int = 64) -> list[str]:
    """Return ids reachable forward from `start` (start -> things it supersedes -> ...)."""
    seen: list[str] = []
    visited: set[str] = set()
    frontier = [start]
    depth = 0
    while frontier and depth < max_depth:
        current = frontier.pop()
        if current in visited:
            continue
        visited.add(current)
        seen.append(current)
        rows = conn.execute(
            "SELECT old_id FROM supersedes WHERE new_id = ?", (current,)
        ).fetchall()
        frontier.extend(r[0] for r in rows if r[0] not in visited)
        depth += 1
    return seen


def chain_for(memory_id: str, db_path: Path) -> list[dict]:
    """Return the full supersedes chain that touches memory_id, newest-first.

    Walks BACKWARD: find anything that supersedes memory_id, then anything that
    supersedes that, etc. Returns rows shaped {new_id, old_id, reason, ts_utc}.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    conn = _connect(db_path)
    try:
        out: list[dict] = []
        visited: set[str] = set()
        frontier = [memory_id]
        depth = 0
        while frontier and depth < 64:
            current = frontier.pop()
            if current in visited:
                continue
            visited.add(current)
            rows = conn.execute(
                "SELECT new_id, old_id, reason, ts_utc FROM supersedes WHERE old_id = ?",
                (current,),
            ).fetchall()
            for r in rows:
                out.append({"new_id": r[0], "old_id": r[1], "reason": r[2], "ts_utc": r[3]})
                if r[0] not in visited:
                    frontier.append(r[0])
            depth += 1
        # Sort newest-first
        out.sort(key=lambda d: d.get("ts_utc", ""), reverse=True)
        return out
    finally:
        conn.close()


def latest_of(memory_id: str, db_path: Path) -> str:
    """Walk backward (old -> new) until no further replacement exists. Returns the terminal id."""
    db_path = Path(db_path)
    if not db_path.exists():
        return memory_id
    conn = _connect(db_path)
    try:
        current = memory_id
        seen: set[str] = set()
        for _ in range(64):
            if current in seen:
                break
            seen.add(current)
            row = conn.execute(
                "SELECT new_id FROM supersedes WHERE old_id = ? ORDER BY ts_utc DESC LIMIT 1",
                (current,),
            ).fetchone()
            if not row:
                return current
            current = row[0]
        return current
    finally:
        conn.close()


def superseded_set(db_path: Path) -> set[str]:
    """All old_ids that have at least one supersedes edge pointing at them."""
    db_path = Path(db_path)
    if not db_path.exists():
        return set()
    conn = _connect(db_path)
    try:
        rows = conn.execute("SELECT DISTINCT old_id FROM supersedes").fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def mark_edge(
    src_id: str,
    dst_id: str,
    kind: str,
    db_path: Path,
    weight: Optional[float] = None,
    reason: str = "",
) -> None:
    """Generic typed-edge writer (cherry-picked from jcode memory_graph.rs:116-125).

    Kind must be one of EDGE_KINDS. Weight is optional (used by RelatesTo).
    For Supersedes, also writes to the legacy `supersedes` table for back-compat
    with chain_for / latest_of / superseded_set.
    """
    src_id = (src_id or "").strip()
    dst_id = (dst_id or "").strip()
    if not src_id or not dst_id:
        raise ValueError("src_id and dst_id must be non-empty")
    if kind not in EDGE_KINDS:
        raise ValueError(f"unknown edge kind {kind!r}; must be one of {sorted(EDGE_KINDS)}")
    if src_id == dst_id and kind in {"Supersedes", "Contradicts"}:
        raise ValueError(f"{kind}: a memory cannot {kind.lower()} itself")

    conn = _connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute(
            "INSERT OR REPLACE INTO edges(src_id, dst_id, kind, weight, reason, ts_utc) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (src_id, dst_id, kind, weight, reason or "", now),
        )
        if kind == "Supersedes":
            # Also write the legacy row so existing chain_for/latest_of keep working.
            # Conventions match: src_id = new, dst_id = old.
            if dst_id in _walk_forward(conn, src_id):
                raise ValueError(f"cycle: {src_id} already reachable from {dst_id}")
            conn.execute(
                "INSERT OR REPLACE INTO supersedes(new_id, old_id, reason, ts_utc) VALUES(?, ?, ?, ?)",
                (src_id, dst_id, reason or "", now),
            )
        conn.commit()
    finally:
        conn.close()


def edges_of(
    memory_id: str,
    db_path: Path,
    kind: Optional[str] = None,
    direction: str = "both",
) -> list[dict]:
    """Return edges touching memory_id.

    Args:
      kind     : optional EdgeKind filter
      direction: "out" (src=memory_id), "in" (dst=memory_id), or "both"
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    if direction not in {"out", "in", "both"}:
        raise ValueError("direction must be one of: out, in, both")

    conn = _connect(db_path)
    try:
        clauses: list[str] = []
        params: list = []
        if direction in {"out", "both"}:
            clauses.append("src_id = ?")
            params.append(memory_id)
        if direction in {"in", "both"}:
            clauses.append("dst_id = ?")
            params.append(memory_id)
        sql = (
            "SELECT src_id, dst_id, kind, weight, reason, ts_utc FROM edges "
            f"WHERE ({' OR '.join(clauses)})"
        )
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        sql += " ORDER BY ts_utc DESC"
        rows = conn.execute(sql, params).fetchall()
        return [
            {
                "src_id": r[0],
                "dst_id": r[1],
                "kind": r[2],
                "weight": r[3],
                "reason": r[4],
                "ts_utc": r[5],
            }
            for r in rows
        ]
    finally:
        conn.close()


def cascade_retrieve(
    memory_id: str,
    db_path: Path,
    depth: int = 2,
    kinds: Optional[Sequence[str]] = None,
) -> list[str]:
    """BFS through the edges graph starting from memory_id, returning related ids
    up to `depth` hops away. Cherry-picked from jcode src/memory.rs:1743-1750.

    `kinds` restricts which edge types to traverse (default: all).
    Returns ids in BFS order, excluding memory_id itself.
    """
    db_path = Path(db_path)
    if not db_path.exists() or depth <= 0:
        return []

    kind_set = set(kinds) if kinds else None
    conn = _connect(db_path)
    try:
        visited: set[str] = {memory_id}
        result: list[str] = []
        frontier: list[tuple[str, int]] = [(memory_id, 0)]
        while frontier:
            current, hop = frontier.pop(0)
            if hop >= depth:
                continue
            rows = conn.execute(
                "SELECT src_id, dst_id, kind FROM edges WHERE src_id = ? OR dst_id = ?",
                (current, current),
            ).fetchall()
            for src, dst, kind in rows:
                if kind_set and kind not in kind_set:
                    continue
                neighbor = dst if src == current else src
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                result.append(neighbor)
                frontier.append((neighbor, hop + 1))
        return result
    finally:
        conn.close()
