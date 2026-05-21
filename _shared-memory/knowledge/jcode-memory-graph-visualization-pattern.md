# jcode-Memory-Graph-Visualization Pattern (memory-graph-render)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Implements:** jcode-feature-matrix row 12 (memory-graph visualization). AGPL-3.0-or-later re-implement of jcode's memory-visualization feature.

## The pipeline (3 stages, decoupled per modular-doctrine)

```
┌────────────────────────────┐   ┌─────────────────────────────┐   ┌────────────────────────────┐
│ Stage 1 :: SOURCE          │   │ Stage 2 :: TRANSFORM        │   │ Stage 3 :: RENDER          │
│                            │   │                             │   │                            │
│ forge-memory (disk)        │ → │ forge_memory_bridge.graph() │ → │ memory-graph-render        │
│ OR                         │   │ emits mermaid-flowchart     │   │ - mermaid-rs-renderer (Rs) │
│ Ruflo agentdb_*  (MCP)     │   │ syntax with:                │   │ - mmdc (Node) fallback     │
│                            │   │  - one node per record      │   │ - HTML+CDN last-resort     │
│                            │   │  - edges for shared tags    │   │ - .mmd ALWAYS written      │
└────────────────────────────┘   └─────────────────────────────┘   └────────────────────────────┘
                                                                              │
                                                                              v
                                                  ┌─────────────────────────────────────────────┐
                                                  │ Sinks                                       │
                                                  │  - inventions/memory-graphs/<UTC>-<ns>.png  │
                                                  │  - Forge PH7 RKOJ tab (embed)               │
                                                  │  - Sinister Mind web view (ingest .mmd)     │
                                                  │  - Operator's browser (open the .html)      │
                                                  └─────────────────────────────────────────────┘
```

## Why three stages

Each stage is independently replaceable. Per `forever-expanding-modular-architecture-doctrine.md`:

- **Stage 1 (source)** could be forge-memory disk, Ruflo agentdb MCP, or any future memory store — as long as it emits records with `namespace`, `key`, `tags`.
- **Stage 2 (transform)** could be the current mermaid-emitter, a Graphviz DOT emitter, a JSON-graph for D3, or a Cytoscape-compatible format — same input, different syntactic output.
- **Stage 3 (render)** could be mermaid-rs-renderer (Rust, fastest), mmdc (Node, mature), or the CDN HTML fallback (zero install) — same .mmd input.

## Stage 2 :: mermaid emission rules

From `tools/forge-memory-bridge/forge_memory_bridge/api.py::graph()`:

| Element | Mermaid expression | Why |
|---|---|---|
| Each record | `<safe_id>["<ns>:<key>"]` (rectangle node, ns-prefixed label) | Operator-readable; grep-able |
| Records sharing ≥1 tag | `<id_a> -- "<tag_csv>" --- <id_b>` (undirected edge with tag label) | Tags ARE the relations in this knowledge model |
| Empty result | `flowchart LR\n    empty[No memories matched]` | Renderer doesn't crash on empty input |

Limitations of mermaid (don't fight the format):
- No node colors per-namespace yet (could add via `classDef` blocks; deferred)
- Large graphs (>200 nodes) get cluttered — pre-filter via `query=` to keep digestible
- Multi-hop relations need to be derived; mermaid is flat

## Stage 3 :: renderer detection order

`memory-graph-render` checks PATH for renderers in this order, returns the first hit:

1. `mermaid-rs-renderer` (Rust binary)
2. `mmdc` (Node CLI)
3. `html-fallback` (always succeeds — writes `.html` w/ mermaid@10 CDN)

The `.mmd` source is ALWAYS written regardless of which backend ran. Operator can paste into `https://mermaid.live` if rendering fails.

## Output naming convention

```
inventions/memory-graphs/<UTC>-<namespace>.<ext>
```

Where:
- `<UTC>` = `YYYY-MM-DDTHHMMSSZ` (filesystem-safe; sortable)
- `<namespace>` = forge-memory namespace OR "all" if cross-ns
- `<ext>` = `mmd` (always) + `html` (always) + `png` (when a PNG renderer was available)

## Composes with

- **`tools/forge-memory-bridge/`** — Stage 1+2 (source + transform)
- **`tools/memory-graph-render/`** — Stage 3 (render)
- **`mermaid-rs-renderer-0.2.2`** (`Desktop\Github Research\`) — preferred renderer; operator-gated (cargo install)
- **`@mermaid-js/mermaid-cli`** (mmdc) — fallback renderer; npm install
- **`projects/sinister-forge/source/forge/panes/rkoj_panel.py`** (PH7) — Forge tab embeds the PNG via web view
- **`projects/sinister-mind/source/`** — Mind ingests `.mmd` directly + renders client-side D3 for the interactive view
- **`automations/memory-consolidate.ps1`** — nightly cron; after consolidation, optionally regenerates the graph for visibility-of-recent-state
- **`_shared-memory/knowledge/jcode-feature-matrix.md`** rows 8, 9, 10, 11, 12 — the broader jcode-memory pipeline
- **`_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`** — the meta-doctrine that made this 3-stage split a design rule, not just a convenience

## When to revisit

- A renderer goes EOL → drop from detection chain
- A new node-relationship type emerges (currently only tag-overlap) → add edge-emission rule in Stage 2
- Operator wants interactive graphs (zoom, click-to-recall) → move Stage 3 to a web view backed by Mind project
- Graph size explodes → introduce namespace-level clustering + pre-filter UI

## Status

🚧 **In-flight 2026-05-21:**
- `tools/forge-memory-bridge/` shipped (Stage 1 + Stage 2)
- `tools/memory-graph-render/` shipped (Stage 3 — html-fallback works without install; mmdc/mermaid-rs-renderer recognized when present)
- mermaid-rs-renderer install still operator-gated (cargo)
- Forge PH7 RKOJ embed pending (Forge sibling owns)
- Mind ingest pending (Mind sibling owns)
