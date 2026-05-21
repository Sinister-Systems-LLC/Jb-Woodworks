# memory-graph-render

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Lane:** Sanctum-side tool. Composes with `forge-memory-bridge`. Used by Forge PH7 RKOJ tab + Mind project graph view.
> **Status:** v0.1.0 — emits .mmd; renders to .png if a renderer is on PATH; degrades gracefully when none is.

## What it is

Render the **memory graph** (output of `forge-memory graph`) to a PNG. jcode's memory-visualization feature parity, AGPL-3.0 re-implement, multi-renderer fallback chain so it works on any operator's machine.

Render backends, in priority order:

1. **`mermaid-rs-renderer`** — Rust-native, fastest, lowest dep footprint. Operator-gated (cargo install). Source: `Desktop\Github Research\mermaid-rs-renderer-0.2.2\`.
2. **`mmdc`** — Node-based mermaid CLI (`npm install -g @mermaid-js/mermaid-cli`). Cross-platform, mature.
3. **Inline SVG** — write `.mmd` + `.html` wrapper that loads `mermaid@10` from CDN; operator opens in browser. Last-resort fallback when neither (1) nor (2) installed.

`.mmd` output is ALWAYS written even if no renderer is available — caller can paste into `https://mermaid.live` manually.

## Quickstart

```bash
cd "D:/Sinister Sanctum/tools/memory-graph-render"
pip install -e .

# CLI — render the full sanctum namespace
memory-graph-render --namespace sanctum --output "D:/Sinister Sanctum/inventions/memory-graphs/sanctum-$(date +%Y-%m-%dT%H%M%SZ).png"

# Query-filtered subgraph
memory-graph-render --namespace forge --query "memory PH16" --output - | head -20

# Just the .mmd source (no render attempt)
memory-graph-render --namespace sanctum --mmd-only --output ./sanctum.mmd

# Python
from memory_graph_render import render
result = render(namespace="sanctum", output="./out.png")
print(result)  # {"backend": "mmdc", "png": "./out.png", "mmd": "./out.mmd"}
```

## Output structure

```
inventions/memory-graphs/
├── <UTC>-<namespace>.mmd       # mermaid source
├── <UTC>-<namespace>.png       # rendered (if a backend was available)
└── <UTC>-<namespace>.html      # fallback HTML (CDN mermaid) when no renderer
```

## Composes with

- **`tools/forge-memory-bridge/`** — calls `forge_memory_bridge.graph()` to get the mermaid syntax
- **`mermaid-rs-renderer-0.2.2`** — Rust renderer; install via `winget install Rustlang.Rustup --silent` then `cargo install --path <renderer>`
- **`@mermaid-js/mermaid-cli`** (mmdc) — Node renderer; `npm install -g @mermaid-js/mermaid-cli`
- **`projects/sinister-forge/source/forge/panes/rkoj_panel.py`** (PH7) — embeds the PNG via RKOJ Forge tab
- **`projects/sinister-mind/source/`** — Mind's web view ingests the .mmd directly + renders client-side
- **`_shared-memory/knowledge/jcode-memory-graph-visualization-pattern.md`** — pattern doc

## Why graceful-degrade

Per `forever-expanding-modular-architecture-doctrine.md`: the operator should be able to use this tool on a fresh PC without installing Rust or Node. We always produce the `.mmd` source + HTML fallback — actual PNG rendering is a nice-to-have, never a hard requirement.
