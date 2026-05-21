# forge-memory-bridge

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Lane:** Sanctum-side tool. Every agent in the fleet (Sanctum, Forge, Term, Panel, RKOJ, APK) imports it.
> **Status:** v0.1.0 — disk-first store + keyword recall + mermaid graph export. MCP fast-path is stubbed.

## What it is

Single Python API + CLI for **persistent cross-session, cross-agent memory** in the Sinister fleet. jcode's `jcode-memory-*` crates re-implemented under AGPL-3.0 on top of Sanctum's existing infrastructure.

**Disk-first**: every memory is a JSON file at `D:\Sinister Sanctum\_shared-memory\forge-memory\<namespace>\<key>.json`. Any agent — even one that has no MCP loaded — can read it with `Get-Content`, `cat`, or this Python API.

**MCP fast-path optional**: when the calling agent has Ruflo MCP loaded, `recall(query, use_mcp=True)` shells to `mcp__ruflo__memory_search` for HNSW semantic recall. Without MCP, falls back to TF-IDF keyword recall over the disk store.

## Quickstart

```bash
cd "D:/Sinister Sanctum/tools/forge-memory-bridge"
pip install -e .

# CLI
forge-memory write --namespace sanctum --key cold-start-protocol --tags doctrine,binding "Read SESSION-START in order before any work"
forge-memory recall "how do I cold-start?"
forge-memory graph --namespace sanctum --output - | tee /tmp/sanctum.mmd
forge-memory consolidate --dry-run

# Python
from forge_memory_bridge import write, recall, graph, consolidate, list as ls
write("sanctum", "cold-start-protocol", "Read SESSION-START in order...", tags=["doctrine", "binding"])
hits = recall("how do I cold-start?")
mermaid_src = graph(namespace="sanctum")
```

## Public API (`forge_memory_bridge`)

| Function | Signature | Returns |
|---|---|---|
| `write` | `write(namespace: str, key: str, value: str \| dict, tags: list[str] = [], upsert: bool = True) -> dict` | the stored record |
| `recall` | `recall(query: str, namespace: str \| None = None, limit: int = 10, use_mcp: bool = False) -> list[dict]` | top-k matches with score |
| `list` | `list(namespace: str \| None = None, tags: list[str] = []) -> list[dict]` | matching records (no scoring) |
| `graph` | `graph(namespace: str \| None = None, query: str \| None = None) -> str` | mermaid syntax for matching subgraph |
| `consolidate` | `consolidate(namespace: str \| None = None, dry_run: bool = False) -> dict` | summary of dedupes + confidence raises |
| `delete` | `delete(namespace: str, key: str) -> bool` | True if deleted |

## On-disk layout

```
_shared-memory/forge-memory/
├── _index.json                       # global metadata for fast scans
├── <namespace>/                      # one dir per logical bucket (sanctum, forge, panel, ...)
│   ├── _meta.json                    # namespace-level metadata (creation date, schema_version)
│   └── <key>.json                    # one record per memory entry
└── _consolidation-log.jsonl          # append-only log of every consolidate run
```

Each record schema:
```json
{
  "schema_version": "sinister.forge-memory.v1",
  "namespace": "sanctum",
  "key": "cold-start-protocol",
  "value": "<string or object>",
  "tags": ["doctrine", "binding"],
  "ts_utc_first": "2026-05-21T11:30:00Z",
  "ts_utc_last": "2026-05-21T11:30:00Z",
  "writes": 1,
  "confidence": 1.0,
  "content_hash": "<sha256>",
  "_author": "RKOJ-ELENO :: 2026-05-21"
}
```

## CLI

```bash
forge-memory write [--namespace NS] --key K [--tags T,T] [--upsert] <value>
forge-memory recall [--namespace NS] [--limit N] [--use-mcp] <query>
forge-memory list [--namespace NS] [--tags T,T]
forge-memory graph [--namespace NS] [--query Q] [--output FILE|-]
forge-memory consolidate [--namespace NS] [--dry-run]
forge-memory delete --namespace NS --key K
```

## Composes with

- **Ruflo MCP** `agentdb_hierarchical-store` / `agentdb_pattern-search` / `agentdb_consolidate` — semantic fast-path (optional)
- **`tools/memory-graph-render/`** — renders the mermaid syntax from `graph()` to PNG
- **`automations/memory-consolidate.ps1`** — nightly cron calling `forge-memory consolidate`
- **`projects/sinister-forge/source/forge/memory/`** — Forge's PH16 memory subsystem; imports this bridge
- **`projects/sinister-term/source/term/`** — Term's `/jcode-memory-recall` builtin (planned); imports this bridge
- **`projects/sinister-mind/source/`** — Mind's graph view; ingests `graph()` output
- **`_shared-memory/knowledge/jcode-feature-matrix.md`** rows 8, 9, 10, 11, 12 — this bridge implements them

## Why disk-first (re: forever-expanding-modular-architecture-doctrine)

- Any agent — even one without Ruflo MCP loaded — can read/write.
- PowerShell, bash, Python, Node — all can `cat <namespace>/<key>.json`.
- No process needs to be running. Memory survives restart, crash, fleet shutdown.
- Two agents writing the same key race on the file — `upsert=True` does last-writer-wins with `writes` counter incrementing (additive, not destructive); `upsert=False` errors on collision.

## Non-goals

- HNSW index re-implementation (Ruflo does it; semantic fast-path delegates)
- Real-time bidirectional sync across hosts (use Sanctum Vault for that)
- Replacement for Vault — vault is for secrets / large blobs; forge-memory is for short-lived semantic memory entries
