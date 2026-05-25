# Sinister Memory

> Author: RKOJ-ELENO :: 2026-05-25
> Project root: `D:\Sinister Sanctum\projects\sinister-memory\`
> Agent slug: `sinister-memory`
> Display name: `Sinister Memory`
> Persona: EVE
> Accent: magenta (memory-class)
> Status: **P0 scaffold** — CLI parse-clean, 5/5 pytest PASS, indexer real (SQLite FTS5)

## Vision

**Every fleet agent has perfect recall across sessions.**

The Sinister Sanctum fleet already ships four loosely-coupled memory layers:

| Layer | Where | Format | Owner | Search? |
|---|---|---|---|---|
| **Brain** | `_shared-memory/knowledge/*.md` | markdown w/ decay-score frontmatter | curator agents | grep only |
| **PROGRESS** | `_shared-memory/PROGRESS/<DisplayName>.md` | append-only markdown | each agent | grep only |
| **Heartbeats** | `_shared-memory/heartbeats/<slug>.json` | JSON snapshot | each agent | json-walk only |
| **Forge / Ruflo** | `forge-memory` CLI + `mcp__ruflo__memory_*` | sqlite + neural | external | semantic |

Each is useful in isolation; together they are noisy. **Sinister Memory unifies them under one CLI + Python API + SQLite FTS5 index**, with optional Ruflo MCP fallback for semantic recall when keyword search misses.

## What `sinister-memory recall` gives you that `forge-memory recall` does not

1. **Walks the knowledge graph** — pulls in Ruflo causal edges + hierarchical recall when the MCP is reachable.
2. **Per-agent scoping** — `sinister-memory recall <topic> --agent sinister-overseer` filters to that agent's PROGRESS + per-agent memory only.
3. **Cross-session persistence** — at iter-close, each agent writes a summary to `per-agent/<slug>/iter-<N>.md`; on next spawn those memories are auto-injected into the spawn phrase.
4. **Ranked snippets** — BM25 over FTS5 returns file:line + 3-line excerpt, not just file hits.
5. **No vector DB rebuild** — leverages SQLite (stdlib) + Ruflo MCP (already running). Zero new heavy deps.

## CLI examples

```bash
# Recall everything the fleet knows about "loop relentless"
sinister-memory recall "loop relentless" --limit 5

# Per-agent scoped recall
sinister-memory recall "kernel apk crash" --agent sinister-kernel-apk

# Save a memory at iter-close
sinister-memory save iter-23 "shipped Sinister Memory P0 scaffold; 5/5 pytest PASS" --agent sinister-sanctum

# Rebuild the unified index (incremental, mtime-based)
sinister-memory index --layer all

# Emit the spawn-phrase chunk to embed into start-sinister-session.ps1
sinister-memory inject-spawn-phrase sinister-overseer
```

## 4-layer integration

```
   brain/*.md    PROGRESS/*.md   heartbeats/*.json   per-agent/<slug>/*
        \             |              |                      /
         \            |              |                     /
          ---->  indexer.py  ----> SQLite FTS5  <----  recall.py
                                       |
                                  inject-spawn-phrase
                                       |
                          start-sinister-session.ps1
                                       |
                                   spawn phrase
                                       |
                                   next agent
```

When Ruflo MCP is reachable, `recall.py` calls `mcp__ruflo__agentdb_hierarchical-recall` as a second-pass query and merges results by score. When unreachable, FTS5 is the sole oracle.

## Endgame

- Every EVE agent spawn picks up exactly where the last iter of THAT slug left off
- Operator can ask "what did Sinister Overseer learn last week about token efficiency?" and get a ranked answer
- Cross-project lessons surface automatically (e.g. "loop-relentless doctrine evolved from the kernel-apk lane, applied to sleight, refined by sanctum")
- forge-memory becomes a backend, not a top-level surface

## Project files

| Path | Purpose |
|---|---|
| `README.md` | This file |
| `CHARTER.md` | What / why / how / 5 P0 milestones / acceptance criteria |
| `pyproject.toml` | Minimal package definition |
| `src/sinister_memory/__init__.py` | Version + author |
| `src/sinister_memory/cli.py` | `recall` / `save` / `index` / `inject-spawn-phrase` |
| `src/sinister_memory/indexer.py` | Walks 4 layers; builds FTS5 index |
| `src/sinister_memory/recall.py` | BM25 search over the index |
| `src/sinister_memory/auto_save.py` | iter-close persistence |
| `src/sinister_memory/spawn_inject.py` | Last-N memory chunk for spawn phrase |
| `tests/test_basic.py` | 5 pytest tests; tmp_path isolated |
| `docs/01-architecture.md` | Diagram + FTS5 schema |
| `docs/02-cli-usage.md` | CLI examples |
| `docs/03-agent-integration.md` | How to call from a running agent |
