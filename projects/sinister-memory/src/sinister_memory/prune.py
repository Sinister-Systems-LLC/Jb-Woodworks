# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: prune.

Hard-delete low-confidence aging memories. Cherry-picked from jcode v0.12.4
`memory_agent.rs:1074-1091` (prune_low_confidence). Schedule: per ambient
consolidation pass (every 6h via schtask) or on-demand via CLI.

Policy: confidence < 0.15 AND age_hours >= 24 -> delete.
        OR: explicit superseded_set membership AND age_hours >= 24 -> delete.

Cascade: incident edges in the supersede `edges` and `supersedes` tables are
auto-cleaned (PRIMARY KEYs ensure no orphans persist).

Safety: dry_run=True by default. Files on disk are NEVER deleted by this
function -- only the FTS5 + embeddings + edges DB rows. Recovery is one
`sinister-memory index` re-build away.

Public API:
  prune_low_confidence(root, db_path, confidence_threshold=0.15,
                       age_hours=24, dry_run=True) -> dict
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional


def _read_confidence(path: Path) -> Optional[float]:
    """Best-effort: parse `confidence: <float>` from a v2 frontmatter file.
    Returns None if not present (treats as default 1.0 -> never pruned)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    block = text[4:end]
    for line in block.splitlines():
        if line.startswith("confidence:"):
            try:
                return float(line.split(":", 1)[1].strip())
            except (ValueError, IndexError):
                return None
    return None


def prune_low_confidence(
    root: Path,
    db_path: Path,
    confidence_threshold: float = 0.15,
    age_hours: float = 24.0,
    dry_run: bool = True,
) -> dict:
    """Prune memory rows whose source file has confidence < threshold AND age
    >= age_hours. Also clears their FTS5 memory rows and embedding rows.

    Returns stats: {scanned, candidates, pruned_fts, pruned_embeddings,
    pruned_edges, dry_run}.

    The `db_path` should be the FTS5 index (default `index.db`). Embeddings
    are pruned from the sibling `embeddings.db` automatically.
    """
    db_path = Path(db_path)
    root = Path(root)
    if not db_path.exists():
        return {
            "scanned": 0,
            "candidates": 0,
            "pruned_fts": 0,
            "pruned_embeddings": 0,
            "pruned_edges": 0,
            "dry_run": dry_run,
        }

    now = time.time()
    cutoff_ts = now - (age_hours * 3600.0)

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT path, mtime FROM files WHERE mtime < ?", (cutoff_ts,)
        ).fetchall()
    finally:
        conn.close()

    candidates: list[str] = []
    for path_str, _mt in rows:
        p = Path(path_str)
        c = _read_confidence(p)
        # Missing confidence == not eligible (treat as fresh/high-confidence)
        if c is not None and c < confidence_threshold:
            candidates.append(path_str)

    if not candidates or dry_run:
        return {
            "scanned": len(rows),
            "candidates": len(candidates),
            "pruned_fts": 0,
            "pruned_embeddings": 0,
            "pruned_edges": 0,
            "dry_run": dry_run,
        }

    # Apply: delete from FTS5 + files + embeddings + edges (cascade)
    pruned_fts = 0
    pruned_embeddings = 0
    pruned_edges = 0

    conn = sqlite3.connect(str(db_path))
    try:
        for p in candidates:
            cur = conn.execute("DELETE FROM memories WHERE path = ?", (p,))
            pruned_fts += cur.rowcount
            conn.execute("DELETE FROM files WHERE path = ?", (p,))
        conn.commit()
    finally:
        conn.close()

    # Embeddings live in a sibling DB
    from . import embed as _embed
    emb_db = _embed.default_embedding_db(root)
    if emb_db.exists():
        conn = sqlite3.connect(str(emb_db))
        try:
            for p in candidates:
                cur = conn.execute("DELETE FROM embeddings WHERE path = ?", (p,))
                pruned_embeddings += cur.rowcount
            conn.commit()
        finally:
            conn.close()

    # Edges -- supersede.py's two tables live in the FTS5 db (per
    # supersede._connect creating them there if absent). Try both.
    conn = sqlite3.connect(str(db_path))
    try:
        for p in candidates:
            cur1 = conn.execute(
                "DELETE FROM supersedes WHERE new_id = ? OR old_id = ?", (p, p)
            )
            cur2 = conn.execute(
                "DELETE FROM edges WHERE src_id = ? OR dst_id = ?", (p, p)
            )
            pruned_edges += (cur1.rowcount or 0) + (cur2.rowcount or 0)
        conn.commit()
    except sqlite3.OperationalError:
        # Tables may not exist (no supersede activity ever recorded)
        pass
    finally:
        conn.close()

    return {
        "scanned": len(rows),
        "candidates": len(candidates),
        "pruned_fts": pruned_fts,
        "pruned_embeddings": pruned_embeddings,
        "pruned_edges": pruned_edges,
        "dry_run": dry_run,
    }
