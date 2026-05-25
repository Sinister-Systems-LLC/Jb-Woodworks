# 01 — Architecture

> Author: RKOJ-ELENO :: 2026-05-25

## 4-layer integration diagram

```
+-----------------------------------------------------------+
|                        SOURCES (read-only)                |
+-----------------------------------------------------------+
|  brain          PROGRESS         heartbeats    per-agent  |
|  *.md           *.md             *.json        iter-*.md  |
+--------+-------------+----------------+------------+------+
         |             |                |            |
         v             v                v            v
+-----------------------------------------------------------+
|                       indexer.build()                     |
|  - mtime-cached files table                               |
|  - per-line / per-key chunks                              |
|  - idempotent + incremental                               |
+-----------------------------+-----------------------------+
                              |
                              v
                +----------------------------+
                |   SQLite FTS5: memories    |
                |   (layer, slug, path,      |
                |    line, snippet, mtime)   |
                +-----+----------------+-----+
                      |                |
                      v                v
            +------------------+  +------------------+
            |  recall.recall   |  | spawn_inject.    |
            |  (BM25)          |  | inject_for_spawn |
            +--------+---------+  +--------+---------+
                     |                     |
                     v                     v
              CLI / Python API    PS1 Build-Phrase chunk
                                         |
                                         v
                                  next agent spawn
```

## SQLite FTS5 schema

Two tables in `_shared-memory/sinister-memory/index.db`:

### `files` (regular table — mtime cache)

| col   | type | role                                       |
|-------|------|--------------------------------------------|
| path  | TEXT | absolute path, PRIMARY KEY                 |
| layer | TEXT | one of brain / progress / heartbeat / per-agent |
| slug  | TEXT | per-agent scope (empty for brain)          |
| mtime | REAL | last os.stat mtime — incremental key       |

### `memories` (FTS5 virtual table — the searchable index)

| col     | type        | role                                  |
|---------|-------------|---------------------------------------|
| layer   | indexed     | layer filter (`WHERE layer = ?`)      |
| slug    | indexed     | agent filter                          |
| path    | indexed     | absolute file path                    |
| line    | indexed     | line number (or `1` for json)         |
| snippet | indexed     | up-to-500-char chunk text             |
| mtime   | UNINDEXED   | display-only; ranked by BM25, not mtime |

BM25 is FTS5's built-in default ranking (Okapi BM25 with k1=1.2, b=0.75). We
expose the raw score in `Hit.score` so callers can post-rank if they want.

## Ruflo MCP role

Ruflo (the existing fleet MCP server) provides semantic recall via
`mcp__ruflo__agentdb_hierarchical-recall` and causal-graph edges via
`mcp__ruflo__agentdb_causal-edge`. P0 keeps Ruflo out of the hot path because
the MCP tool family is only callable from the Claude harness, not from a
stand-alone Python process. `recall.try_ruflo_augment()` is a no-op stub today;
P3 wires the real call via a Ruflo client library.

The boundary: **FTS5 owns keyword recall (cheap, deterministic, offline-safe);
Ruflo owns semantic recall (rich, expensive, requires the MCP).**

## Decay-score interplay

The fleet's brain entries already carry decay-score frontmatter (`_INDEX.md`
ranks them). The indexer does NOT re-rank by decay — it indexes the raw text.
At recall time, callers can post-filter by reading the brain index. P2+ will
add a `--prefer-fresh` flag that joins against `_INDEX.md` mtimes.

## Why SQLite FTS5 over alternatives

| Option                  | Verdict                                              |
|-------------------------|------------------------------------------------------|
| **SQLite FTS5** (chosen)| stdlib in Python 3.12, BM25 built-in, zero new deps  |
| `sqlite-vss`            | requires C ext install — Windows pain; semantic only |
| Whoosh                  | pure-Python but unmaintained since 2016              |
| `ripgrep` shell-out     | no ranking, no per-layer schema                      |
| Custom embeddings + faiss | weeks of work; duplicates Ruflo MCP capability     |

Verified at scaffold time: `python -c "import sqlite3; conn=sqlite3.connect(':memory:'); conn.execute('CREATE VIRTUAL TABLE t USING fts5(x)')"` exit 0 on the fleet's Python 3.12.10.
