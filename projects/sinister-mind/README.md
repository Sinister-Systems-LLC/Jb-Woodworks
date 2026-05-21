# Sinister Mind

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-mind` :: branch `agent/sinister-mind/<topic>` :: purple accent
> **License:** AGPL-3.0-or-later

## What this is

Sinister Mind is **the visual nervous system of the Sinister fleet** — a Sinister-branded, jcode-powered mind-graph that visualizes everything the brain knows about every project. Think Obsidian's mind-graph, but:

- **Powered by Ruflo `agentdb_*` semantic search** instead of plain wikilinks, so cluster-by-meaning + cosine-similarity edges instead of literal `[[link]]` matches.
- **Per-project sidebar + filter** so the operator can collapse the universe to just `snap-emulator-api` or `sinister-forge` or `Kernel APK`.
- **Complex-query search** (regex + tag + connected-component + shortest-path-between-two-concepts).
- **Sinister visual theme**: dark void background, purple primary, neural-architecture cluster aesthetic (per the reference image — colorful blobs + thin label leaders + project-grouped layout).
- **Live**: brain entries / cross-agent messages / plans / heartbeats all stream in. No nightly re-index.
- **jcode memory-graph integration**: the same semantic vectors that drive Forge's auto-recall power Mind's node-similarity edges. One source of truth.

## Operator directive (verbatim 2026-05-21)

> *"in the graph we make i need it to look like this in theme with a side bar to tell me where things are complex searching etc. and i can see the by project breakdown in here and essentially be a more p[oowerful obsidan mind graph using jcode and all other skills. create this project and call it Sinister Mind"*

## Architecture

```
                ┌──────────────────────────────────────┐
                │ Desktop\Sinister Mind.bat            │
                └───────────────┬──────────────────────┘
                                │
                                ▼
                ┌──────────────────────────────────────┐
                │ python -m mind                       │
                │  - Flask server on http://127.0.0.1:5079/
                │  - Auto-opens default browser to /
                └─────┬─────────────────────────┬──────┘
                      │                         │
                      ▼                         ▼
       ┌──────────────────────┐    ┌────────────────────────────┐
       │ Backend (mind/)      │    │ Frontend (static/ + D3.js) │
       │ - reads brain        │    │ - SVG force-directed graph │
       │   _INDEX.md          │    │ - Sinister theme (dark +   │
       │ - reads PROGRESS/    │    │   purple primary)          │
       │ - reads plans/       │    │ - sidebar:                 │
       │ - reads cross-agent/ │    │   * project filter         │
       │ - Ruflo agentdb_*    │    │   * complex search         │
       │   (when MCP loaded)  │    │   * tag chips              │
       │ - JSON /api/* endps  │    │   * shortest-path between  │
       └──────────────────────┘    │     two concepts           │
                                   └────────────────────────────┘
```

## Tech stack

- **Backend**: Flask + watchdog (file-watcher for live reload)
- **Frontend**: vanilla HTML + D3.js v7 (force-directed graph, no React/Node build step)
- **Data**: reads existing Sanctum brain files; no migration needed
- **Memory**: optional Ruflo agentdb integration for semantic-similarity edges (works fine without it — falls back to tag overlap)

## What gets rendered as nodes

| Node type | Source | Color (Sinister palette) |
|---|---|---|
| **Brain entry** | `_shared-memory/knowledge/*.md` | `#A06EFF` (purple-bright) |
| **Project** | `automations/session-templates/projects.json` | `#6EE8FF` (cyan) |
| **Plan artifact** | `_shared-memory/plans/<proj>-*/` | `#6EFFA0` (green) |
| **PROGRESS entry** | `_shared-memory/PROGRESS/<agent>.md` headings | `#FFD66E` (yellow) |
| **Cross-agent message** | `_shared-memory/cross-agent/*.md` | `#FF6EE8` (magenta) |
| **Resume-point** | `_shared-memory/resume-points/<proj>/*.json` | `#FF6E6E` (red) |
| **Agent (active)** | `_shared-memory/heartbeats/*.json` (fresh <15min) | `#6EFFA0` halo |

## Edge types

- **Brain → Brain** by `## Related topics` cross-link OR cosine similarity > 0.7 (Ruflo)
- **Brain → Project** by tag overlap
- **Project → Plan / PROGRESS / Resume-point** by project key in path
- **Cross-agent → Project** by `to:` field
- **Agent → Project** by heartbeat slug ↔ project mapping

## Phases

| Phase | What | Status |
|---|---|---|
| **PH0** | Scaffold (this commit) | ✅ |
| **PH1** | Flask app + 1 endpoint (`/api/graph`) that reads `_INDEX.md` + projects.json + returns node-and-edge JSON | ✅ |
| **PH2** | D3.js force-directed graph in `static/index.html` with Sinister theme | ✅ |
| **PH3** | Sidebar: project filter dropdown + text search input | ✅ |
| **PH4** | Tag chips (click to filter graph to that tag's connected component) | pending |
| **PH5** | Shortest-path-between-two-concepts (operator picks node A + node B, graph highlights path) | pending |
| **PH6** | Ruflo agentdb integration for semantic edges (falls back to tag overlap if MCP not loaded) | pending |
| **PH7** | Live reload (watchdog file-watcher on `_shared-memory/`) | pending |
| **PH8** | RKOJ Workstation embed (Mind iframe in RKOJ's Plans tab) | pending |
| **PH9** | Forge integration — Forge `agent_pane` shows a mini-mind in the bottom of each pane for that project's neighborhood | pending |
| **PH10** | Export to PNG / SVG / standalone HTML (operator wants to share it) | pending |

## Cross-references

- `projects/sinister-mind/source/PLAN.md` — full phase plan
- `projects/sinister-forge/source/PLAN.md` — sibling project (Forge wraps the harness, Mind visualizes the brain)
- `automations/session-contracts.md` — 6 contracts (Mind agents honor them too)
- `_shared-memory/plans/sinister-mind-2026-05-21/` — design notes + decisions
- `Desktop\Sinister Mind.bat` — one-click entry
