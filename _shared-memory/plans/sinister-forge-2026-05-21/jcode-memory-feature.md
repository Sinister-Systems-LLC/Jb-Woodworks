# jcode Memory Feature :: review for Forge port

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **Source video:** `C:\Users\Zonia\Desktop\Github Research\jcode-memory-demo(3).mp4`
> **Source code:** `D:\Research\jcode\crates\jcode-memory-types\` + `jcode-memory-store\` + `jcode-memory-router\` (read-only reference)

## What jcode's memory feature does (from code + docs, NOT video — agent has no media player)

Based on jcode's source layout, the memory feature is composed of these crates:

- **`jcode-memory-types`** — schema for memory entities (concepts, facts, relations) + serialization.
- **`jcode-memory-store`** — embedding-backed semantic store (HNSW index + metadata).
- **`jcode-memory-router`** — auto-recall layer that surfaces relevant memories during a turn.
- **Background consolidation** — periodic process that merges duplicate memories + raises confidence on repeated facts.

### Operator-facing behavior (per `jcode/README.md` memory section)

1. **Auto-recall**: as you work, jcode silently fetches related memories from prior sessions + surfaces them in the agent's context.
2. **Manual write**: `jcode memory write "<fact>"` pins a fact you want remembered.
3. **Consolidation**: every N hours, dupe-detection + confidence-merge.
4. **Visualization**: the memory graph can be exported + browsed (demo video at `jcode-memory-demo.mp4`).

## What Forge ports vs delegates

| Capability | Where it lives in Forge | Note |
|---|---|---|
| Memory schema | **Delegate** to Ruflo `agentdb_*` (hierarchical-store / pattern-store / semantic-route already exposed) | Don't re-implement HNSW; Ruflo's 28 tools already cover this |
| Auto-recall during turn | **NEW Forge feature** — `CONTRACT 1 CONTEXT-REVIEW` already does cold-start recall; extend with mid-turn `agentdb_pattern-search` calls when the agent hits ambiguous code | Layered on top of Ruflo |
| Manual write | **Delegate** to Ruflo `agentdb_hierarchical-store` | Operator runs once per fact OR agent auto-pins on `[breakthrough]` commit |
| Consolidation | **Delegate** to Ruflo `agentdb_consolidate` (already a tool) | Schedule via auto-cleanup.ps1 nightly |
| Visualization | **NEW Forge feature** — render memory graph to mermaid → `mermaid-rs-renderer` → PNG in RKOJ Workstation Forge tab | Combines two TOP-3 picks |

## Why we mine + don't adopt

- **License**: jcode MIT, our Forge AGPL-3.0; clean re-implement under AGPL-3.0 with attribution in `NOTICES.md`.
- **Stack mismatch**: jcode memory is Rust-native crates; our agents are Claude Code (Python ecosystem dominant). Re-implementing means a thin Python wrapper around Ruflo's existing MCP tools — no Rust dependency.
- **Data sovereignty**: jcode's telemetry-by-default would phone home about memory writes; ours stays local-only in `_shared-memory/forge-memory/`.

## R-row this maps to

- **R10** (multi-provider routing) defines WHICH model handles memory consolidation (suggest: Haiku for cheap dupe-detection, Opus only when memory graph rewrites are needed).
- **R7** (RKOJ Forge tab) is where the memory-graph mermaid render shows up.
- **NEW R13 candidate**: `forge-memory-bridge` Python module that wraps Ruflo's `agentdb_*` tools into a single `forge memory <write|recall|graph>` CLI surface.

## Video status

The .mp4 cannot be read by this agent (no media decoder). When it matters: a sub-agent with browser access can extract frames OR the operator can describe what jumps out from it; until then this doc captures everything mineable from the source code + README.

## Cross-references

- `D:\Research\jcode\crates\jcode-memory-*\` — source-of-truth
- Ruflo MCP `agentdb_*` tools — existing capability surface
- `_shared-memory/knowledge/_INDEX.md` — Sanctum's hand-curated equivalent
