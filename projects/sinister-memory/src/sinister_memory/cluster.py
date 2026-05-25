# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: cluster.

Jaccard-similarity clustering on snippet token sets. Used by the dedupe pass
to collapse near-duplicate iter-close memories (and other repeated rows) into
supersedes edges so recall doesn't surface the same fact 5x.

Pure-Python, no deps. Designed to run on at most a few thousand snippets — for
larger corpora the index.db should be sharded or a real embedding store used.

Public API:
  tokenize(text)                              -> set[str]
  jaccard(a, b)                               -> float in [0, 1]
  cluster_snippets(rows, threshold=0.7)       -> list[list[int]]   # row index groups
  dedupe(db_path, threshold=0.85, layers=...) -> dict  # stats {scanned, clustered, edges}
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Sequence

from . import supersede

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]{3,}")
_STOPWORDS = frozenset(
    {
        "the", "and", "for", "with", "from", "this", "that", "into", "have",
        "has", "are", "was", "were", "but", "not", "you", "your", "our", "all",
        "any", "per", "via", "use", "uses", "using", "used", "via", "ref",
    }
)


def tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens of length >=3, stopwords removed."""
    if not text:
        return set()
    return {t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def cluster_snippets(rows: Sequence[tuple], threshold: float = 0.7) -> list[list[int]]:
    """Greedy single-pass clustering.

    `rows` is a sequence of (snippet, ...) tuples; only [0] is read. Returns
    a list of clusters, each cluster is a list of row indices. Rows whose
    Jaccard >= threshold against any cluster representative join that cluster;
    otherwise they spawn a new cluster.
    """
    clusters: list[list[int]] = []
    reps: list[set[str]] = []
    for idx, row in enumerate(rows):
        text = row[0] if row else ""
        toks = tokenize(text)
        joined = False
        for c_idx, rep in enumerate(reps):
            if jaccard(toks, rep) >= threshold:
                clusters[c_idx].append(idx)
                # Merge tokens into representative (centroid drift)
                reps[c_idx] = rep | toks
                joined = True
                break
        if not joined:
            clusters.append([idx])
            reps.append(toks)
    return clusters


def _fetch_dedup_targets(
    conn: sqlite3.Connection,
    layers: Optional[Sequence[str]],
    limit: int,
) -> list[tuple[str, str, str, str]]:
    """Return (snippet, layer, slug, path) rows we'll consider for dedupe."""
    sql = "SELECT snippet, layer, slug, path FROM memories"
    params: list = []
    if layers:
        placeholders = ",".join("?" for _ in layers)
        sql += f" WHERE layer IN ({placeholders})"
        params.extend(layers)
    sql += " LIMIT ?"
    params.append(limit)
    return list(conn.execute(sql, params).fetchall())


def dedupe(
    db_path: Path,
    threshold: float = 0.85,
    layers: Optional[Sequence[str]] = ("progress", "per-agent"),
    limit: int = 5000,
    dry_run: bool = False,
) -> dict:
    """Scan the FTS5 index, cluster near-duplicate rows, mark all-but-newest as
    superseded by the newest in each cluster.

    Returns stats: {scanned, clusters, edges_added, dry_run}.
    Defaults to progress/per-agent layers (brain entries are curated -- don't
    auto-supersede them).
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return {"scanned": 0, "clusters": 0, "edges_added": 0, "dry_run": dry_run}

    conn = sqlite3.connect(str(db_path))
    try:
        rows = _fetch_dedup_targets(conn, layers, limit)
    finally:
        conn.close()

    if not rows:
        return {"scanned": 0, "clusters": 0, "edges_added": 0, "dry_run": dry_run}

    clusters = cluster_snippets(rows, threshold=threshold)

    # For each multi-row cluster, pick newest (highest mtime per files table) as canonical;
    # mark all others superseded by it.
    edges_added = 0
    if not dry_run:
        conn = sqlite3.connect(str(db_path))
        try:
            # mtime lookup per path
            mtimes = {r[0]: float(r[1]) for r in conn.execute("SELECT path, mtime FROM files")}
        finally:
            conn.close()

        for cluster in clusters:
            if len(cluster) < 2:
                continue
            paths = [rows[i][3] for i in cluster]
            uniq_paths = list(dict.fromkeys(paths))  # preserve order, dedupe
            if len(uniq_paths) < 2:
                continue
            uniq_paths.sort(key=lambda p: mtimes.get(p, 0.0), reverse=True)
            newest = uniq_paths[0]
            for older in uniq_paths[1:]:
                try:
                    supersede.mark_supersedes(
                        new_id=newest,
                        old_id=older,
                        reason=f"cluster-dedupe Jaccard>={threshold:.2f}",
                        db_path=db_path,
                    )
                    edges_added += 1
                except ValueError:
                    # cycle or invalid id - skip
                    pass

    return {
        "scanned": len(rows),
        "clusters": sum(1 for c in clusters if len(c) >= 2),
        "edges_added": edges_added,
        "dry_run": dry_run,
    }
