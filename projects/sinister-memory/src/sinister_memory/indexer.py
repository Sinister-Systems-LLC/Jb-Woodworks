# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Memory :: indexer.

Walks the 4 fleet memory layers and writes a SQLite FTS5 index. Idempotent +
incremental (mtime-based — files unchanged since last index are skipped).

Layers:
  L1 = brain       :: <root>/_shared-memory/knowledge/*.md
  L2 = progress    :: <root>/_shared-memory/PROGRESS/*.md
  L3 = heartbeat   :: <root>/_shared-memory/heartbeats/*.json
  L4 = per-agent   :: <root>/_shared-memory/sinister-memory/per-agent/<slug>/*.md

Schema:
  files (path PK, layer, slug, mtime)         -- mtime cache for incremental
  memories(layer, slug, path, line, snippet, mtime UNINDEXED) USING fts5

Snippet granularity: one row per logical chunk
  - markdown: one row per non-empty line (line number = 1-based)
  - json:     one row per top-level key (line = best-effort 1 if hard to compute)

Public API:
  build(root, db_path)   -> stats dict {indexed, skipped, removed}
  reset(db_path)         -> wipes both tables (for tests)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

LAYERS = ("brain", "progress", "heartbeat", "per-agent")


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE IF NOT EXISTS files (
               path TEXT PRIMARY KEY,
               layer TEXT NOT NULL,
               slug TEXT,
               mtime REAL NOT NULL
           )"""
    )
    conn.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS memories USING fts5(
               layer, slug, path, line, snippet, mtime UNINDEXED
           )"""
    )
    return conn


def reset(db_path: Path) -> None:
    """Wipe both tables. For tests; do NOT call against production index."""
    if not db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("DROP TABLE IF EXISTS files")
        conn.execute("DROP TABLE IF EXISTS memories")
        conn.commit()
    finally:
        conn.close()


def _slug_from_progress(path: Path) -> str:
    """`_shared-memory/PROGRESS/Sinister Overseer.md` -> `sinister-overseer`."""
    stem = path.stem
    return stem.lower().replace(" ", "-")


def _slug_from_heartbeat(path: Path) -> str:
    return path.stem.lower()


def _slug_from_per_agent(path: Path) -> str:
    # per-agent/<slug>/iter-<N>.md  -> parent dir name
    return path.parent.name.lower()


def _iter_markdown_chunks(path: Path) -> Iterable[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped and not stripped.startswith("<!--"):
            yield idx, stripped[:500]


def _iter_json_chunks(path: Path) -> Iterable[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError):
        return
    if isinstance(data, dict):
        for k, v in data.items():
            snippet = f"{k}: {json.dumps(v, default=str)[:400]}"
            yield 1, snippet
    elif isinstance(data, list):
        for i, item in enumerate(data):
            snippet = f"[{i}]: {json.dumps(item, default=str)[:400]}"
            yield i + 1, snippet


def _discover_files(root: Path) -> list[tuple[str, str, Path]]:
    """Return list of (layer, slug, path) tuples for every memory file under root."""
    out: list[tuple[str, str, Path]] = []
    sm = root / "_shared-memory"
    if not sm.exists():
        return out

    brain_dir = sm / "knowledge"
    if brain_dir.is_dir():
        for p in brain_dir.glob("*.md"):
            out.append(("brain", "", p))

    progress_dir = sm / "PROGRESS"
    if progress_dir.is_dir():
        for p in progress_dir.glob("*.md"):
            out.append(("progress", _slug_from_progress(p), p))

    heartbeat_dir = sm / "heartbeats"
    if heartbeat_dir.is_dir():
        for p in heartbeat_dir.glob("*.json"):
            out.append(("heartbeat", _slug_from_heartbeat(p), p))

    per_agent_dir = sm / "sinister-memory" / "per-agent"
    if per_agent_dir.is_dir():
        for slug_dir in per_agent_dir.iterdir():
            if slug_dir.is_dir():
                for p in slug_dir.glob("*.md"):
                    out.append(("per-agent", _slug_from_per_agent(p), p))

    return out


def build(root: Path, db_path: Path) -> dict:
    """Build / refresh the index. Returns counts dict.

    Incremental: files whose mtime equals the cached mtime are skipped.
    Removed: rows whose path is gone from disk are pruned.
    """
    root = Path(root)
    db_path = Path(db_path)

    conn = _connect(db_path)
    cur = conn.cursor()
    indexed = skipped = removed = 0

    try:
        # Build map of currently-known file mtimes
        cached: dict[str, float] = {
            row[0]: row[1] for row in cur.execute("SELECT path, mtime FROM files")
        }

        seen: set[str] = set()
        for layer, slug, path in _discover_files(root):
            path_str = str(path)
            seen.add(path_str)
            try:
                mt = path.stat().st_mtime
            except OSError:
                continue

            if cached.get(path_str) == mt:
                skipped += 1
                continue

            # Stale or new — wipe + re-insert all rows for this path
            cur.execute("DELETE FROM memories WHERE path = ?", (path_str,))
            chunks = (
                _iter_markdown_chunks(path)
                if path.suffix == ".md"
                else _iter_json_chunks(path)
            )
            for line_no, snippet in chunks:
                cur.execute(
                    "INSERT INTO memories(layer, slug, path, line, snippet, mtime) "
                    "VALUES(?, ?, ?, ?, ?, ?)",
                    (layer, slug, path_str, str(line_no), snippet, mt),
                )

            cur.execute(
                "INSERT OR REPLACE INTO files(path, layer, slug, mtime) VALUES(?,?,?,?)",
                (path_str, layer, slug, mt),
            )
            indexed += 1

        # Prune gone files
        for stale_path in set(cached) - seen:
            cur.execute("DELETE FROM memories WHERE path = ?", (stale_path,))
            cur.execute("DELETE FROM files WHERE path = ?", (stale_path,))
            removed += 1

        conn.commit()
    finally:
        conn.close()

    return {"indexed": indexed, "skipped": skipped, "removed": removed}


def default_db_path(root: Path) -> Path:
    return Path(root) / "_shared-memory" / "sinister-memory" / "index.db"
