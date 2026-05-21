# Forever-Expanding Modular Architecture :: Sinister fleet doctrine

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Operator directive (verbatim 2026-05-21T11:15Z):** *"ok take note we have sinister sanctum, sinister term, rkoj workstation, sinister panel and apk agents all running. make sure to keep in mind everything is going to connect to everything im a forver expanding modular approach."*

## What "forever-expanding modular" means in concrete code

Every capability shipped from any agent must satisfy these properties:

| Property | Why | How to satisfy |
|---|---|---|
| **Disk-first surface** | An agent that doesn't have your MCP tools loaded must still consume your output | Land your output as JSON / Markdown / PNG / SQLite on disk under `_shared-memory/` or `tools/<your-tool>/data/` |
| **MCP fast-path optional** | When MCP is loaded, integrations should be snappier — but never *required* | Provide both: `tool foo --json` shells out cleanly; `mcp__yourtool__foo` returns the same shape |
| **Schema versioned** | When you change the shape, older agents shouldn't crash | Top-level field `schema_version: "<dotted-prefix>.v<N>"` + a `_meta` block describing breaking changes |
| **Append-only when possible** | Two agents writing the same file race; appending lets both win | PROGRESS-style append-most-recent-on-top; or one-file-per-event with a sortable filename (`<UTC>-<slug>.json`) |
| **Slug-namespaced** | Two agents named the same thing in different lanes need to coexist | Use the agent slug (`sanctum`, `forge`, `panel`, `apk`, `rkoj`, `sinister-term`) as the first path segment under any shared directory |
| **No hard imports between agent source trees** | Forge's `projects/sinister-forge/source/` should never `import` from `projects/sinister-panel/source/`; that creates lifecycle coupling | Cross-tree comms go through `_shared-memory/inbox/` + `cross-agent/` + `tools/<bridge>/` — never source-level imports |
| **Discoverable by drop-in** | Operator should be able to add a new agent/tool/skill without editing a registry file | Index files (`tools/_INDEX.md`, `skills/_INDEX.md`, `bots/README.md`) auto-regenerate via glob, OR each consumer scans the dir at startup |
| **Local-first; no telemetry** | Per canonical-21 data sovereignty | Every tool defaults to writing under `_shared-memory/` or `D:\sinister-vault\` — never phones home |

## The 5+1 active fleet (2026-05-21T11:15Z snapshot)

```
                       ┌─────────────────────────┐
                       │   operator: RKOJ-ELENO  │
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            v           v           v           v           v
       ┌────────┐  ┌────────┐  ┌─────────┐ ┌────────┐ ┌──────────┐
       │sanctum │  │ forge? │  │sinister-│ │  rkoj  │ │  panel   │
       │ master │  │  TUI   │  │  term   │ │workstn │ │ Hetzner  │
       └───┬────┘  └───┬────┘  └────┬────┘ └───┬────┘ └─────┬────┘
           │           │            │           │            │
           └─────┬─────┴────────────┴───────────┴────────────┘
                 │                       │
                 v                       v              ┌─────────┐
       ┌─────────────────────┐  ┌─────────────────┐    │   apk   │
       │  _shared-memory/    │  │   tools/        │    │ keybox  │
       │  ├ inbox/<slug>/    │  │   ├ forge-memory│    └────┬────┘
       │  ├ cross-agent/     │  │   │  -bridge/   │         │
       │  ├ heartbeats/      │  │   ├ memory-     │         │
       │  ├ knowledge/       │  │   │  graph-     │         │
       │  ├ resume-points/   │  │   │  render/    │         │
       │  └ forge-memory/    │  │   ├ sinister-   │         │
       │                     │  │   │  vault/     │         │
       │                     │  │   └ ...         │         │
       └─────────────────────┘  └─────────────────┘         │
                 ^                       ^                   │
                 │                       │                   │
                 └───────────────────────┴───────────────────┘
                              "everything ingests, everything publishes"
```

The "?" on Forge is because operator's 11:15Z fleet enumeration omitted Forge — could be live, could have rolled into Sanctum/Term/RKOJ work. Treat as possibly-active; do not edit `projects/sinister-forge/source/` until confirmed dormant.

## Anti-patterns this doctrine forbids

- ❌ Importing `from sinister_panel.foo import bar` inside a Forge module
- ❌ Hardcoding an agent's MCP tool name (e.g. `mcp__myagent__do_thing`) without a disk-fallback path
- ❌ Mutating a shared file without checking schema_version
- ❌ Writing into `_shared-memory/inbox/<other-slug>/` for "convenience" — that's their inbox; you publish, they consume
- ❌ Asking the operator "should I add agent X to my registry?" — agents discover by glob, no registry edit needed
- ❌ Phoning home / cloud-publishing without explicit operator + data-sovereignty review

## Patterns this doctrine encourages

- ✅ Drop a new `.md` in `_shared-memory/knowledge/` — `_INDEX.md` regenerates next sweep
- ✅ Drop a `.py` skill in `_shared-memory/skills/` — every Forge pane picks it up on next reload
- ✅ Write `<UTC>-<event>.json` in `_shared-memory/inbox/<slug>/` — that agent ingests on next inbox-poll
- ✅ `tools/<your-tool>/` gets a `pyproject.toml` + `__main__.py` + a one-line README — every other tool can `pip install -e ../<your-tool>`
- ✅ Cross-agent semantic memory via Ruflo `agentdb_*` MCP **OR** disk JSON at `_shared-memory/forge-memory/` — same data, two surfaces

## Composes with

- `_shared-memory/knowledge/jcode-feature-matrix.md` (this session) — concrete capability matrix; this doctrine is the meta-pattern
- `automations/session-contracts.md` — CONTRACT 5 (CROSS-AGENT COMMUNICATION) is the runtime expression of this doctrine
- `automations/agent-host-routing.md` — multi-provider routing is one expression of "everything connects to everything"
- `_shared-memory/knowledge/sibling-active-launch-coordination-pattern.md` (this session) — coordination doctrine when N siblings spin simultaneously

## When to revisit this doctrine

- Operator overrides with a "concrete dependency is OK here" — specific exemption goes in this doc's exceptions section (none yet)
- A monolithic-coupling becomes the *only* way to meet a performance or correctness bar — document the trade in `_shared-memory/case-studies/`
- Two agents repeatedly race on the same file — add a lock-pattern brain entry rather than weakening modularity
