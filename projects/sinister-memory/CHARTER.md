# Sinister Memory — Charter

> Author: RKOJ-ELENO :: 2026-05-25
> Status: P0 scaffolded
> Operator brief: *"add to eve exe a project start for Sinister Memroy and complie all thigsn he needs there to get started"* (2026-05-25 ~07:30Z)

## What

A per-agent + per-project memory engine that unifies the fleet's four existing memory surfaces (brain markdown, PROGRESS logs, heartbeats, Ruflo MCP) behind one Python CLI + library + spawn-phrase injector.

## Why

The fleet currently has four memory layers, none of which talk to each other:

- **Brain** (`_shared-memory/knowledge/`) is grep-only — no ranking, no per-agent slicing.
- **PROGRESS** logs grow unbounded and the operator cannot ask "what did Overseer do yesterday?".
- **Heartbeats** are point-in-time JSON; useful for "is it alive" but not for "what did it think".
- **Ruflo MCP** is rich but agent-opaque (no per-agent scope on first call).

Result: every spawn re-discovers what the previous spawn already knew, wasting tokens and breaking continuity. The RELENTLESS loop doctrine (2026-05-25) explicitly demands cross-session continuity. Sinister Memory delivers it.

## How

1. **Indexer** (incremental, mtime-based) walks all four layers nightly + on-demand, writes rows into one SQLite FTS5 table at `_shared-memory/sinister-memory/index.db`.
2. **Recall** runs BM25 over FTS5, optionally augments with Ruflo `agentdb_hierarchical-recall` when the MCP is reachable, merges + ranks by combined score, returns `file:line + 3-line snippet` tuples.
3. **Auto-save** at iter-close (called by agents themselves or by `forever-improve.ps1` Tally) writes a per-agent markdown blurb to `_shared-memory/sinister-memory/per-agent/<slug>/iter-<N>.md` and triggers an incremental re-index for that slug.
4. **Spawn-inject** emits a markdown chunk of the last-5 memories for a given slug; `start-sinister-session.ps1` Build-Phrase calls it and embeds the chunk so the new spawn loads with full continuity.
5. **CLI** wraps all four operations; Python API mirrors them for in-process use.

## 5 P0 milestones (acceptance criteria below each)

### P0.1 — Package + CLI parse-clean
- `python -m sinister_memory.cli --help` exits 0
- `python -m sinister_memory.cli recall --help` exits 0
- All four subcommands (`recall` / `save` / `index` / `inject-spawn-phrase`) parse without errors

### P0.2 — Indexer real (FTS5 backed)
- `indexer.build(root, db_path)` creates a FTS5 virtual table `memories` with columns `(layer, slug, path, line, snippet, mtime UNINDEXED)`
- Walks the 4 layer roots (brain / PROGRESS / heartbeats / per-agent) and indexes every `.md` and `.json` file
- Incremental: rows with unchanged mtime are skipped
- Idempotent: rerun produces no duplicates

### P0.3 — Recall + ranking
- `recall.recall("loop relentless", limit=5)` returns ≤5 `Hit` namedtuples with `.path .line .snippet .score`
- BM25 ordering (FTS5 default ranking)
- `--agent <slug>` filters to that agent's PROGRESS + per-agent rows
- Empty index returns `[]` without erroring

### P0.4 — Auto-save + spawn-inject
- `auto_save.save_iter_close(slug, iter_num, summary)` writes `per-agent/<slug>/iter-<N>.md` with frontmatter (timestamp, slug, iter)
- `spawn_inject.inject_for_spawn(slug, limit=5)` returns a markdown chunk listing last-5 iter summaries for that slug
- Chunk is bash-safe (no backticks that could break PowerShell here-strings)

### P0.5 — Pytest 5/5 PASS
- `python -m pytest projects/sinister-memory/ -v` exits 0
- 5 tests cover: indexer build, recall query, auto_save iter-close, spawn_inject chunk, CLI smoke
- All tests use `tmp_path` fixture; zero contact with the real `_shared-memory/`

## Out of scope (P0)

- **Do NOT replicate Ruflo's vector store.** Use FTS5 keyword search; let Ruflo MCP do semantic when present. Custom embeddings are P3+.
- **Do NOT auto-edit `start-sinister-session.ps1`.** Spawn-inject is exposed; integration is documented in `docs/03-agent-integration.md` and shipped in a follow-up iter once operator approves.
- **Do NOT touch other projects/.** Sinister Memory is a library + CLI; other agents call it, it does not reach into them.
- **Do NOT replace forge-memory.** Both coexist; sinister-memory can later delegate to forge-memory as one of its sources.
- **Do NOT create a daemon.** Indexer runs on-demand or via a future schtask; no long-running process at P0.

## Phase plan (post-P0)

- **P1** — wire `auto_save` into `forever-improve.ps1` Tally so every agent's iter-close auto-persists
- **P2** — wire `inject-spawn-phrase` into `start-sinister-session.ps1` Build-Phrase
- **P3** — Ruflo MCP integration (hierarchical-recall fallback when FTS5 returns <3 hits)
- **P4** — operator-facing dashboard ("what did Overseer learn this week?")
- **P5** — cross-project lesson surfacing (auto-link related memories across agents)

## Compose with existing doctrine

- `loop-relentless-pursuit-doctrine-2026-05-25` — provides the cross-iter continuity the loop demands
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — auto-save lets agents back claims with same-turn memory evidence
- `forever-improve-review-doctrine-2026-05-24` — Tally action becomes the natural iter-close hook
- `sanctum-scope-discipline-2026-05-24` — Sinister Memory is fleet-wide infra (Sanctum-scope), not a per-project tool
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` — memory growth becomes structured + searchable
