# sinister-cli

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Operator directive 2026-05-21 (verbatim):** *"our commands will be sinister then the command"* (with jcode `jcode login --provider claude` screenshot)
> **Status:** v0.1.0 — umbrella dispatcher; subcommands resolve at runtime to installed sibling tools (graceful-degrade if missing)

## What it is

Single top-level `sinister` CLI mirroring jcode's `jcode <subcommand>` pattern. Dispatches to per-tool entry-points. Plugin-friendly via the `SUBCOMMAND_MAP` registry.

## Subcommand map

| Command | Backend tool | Purpose |
|---|---|---|
| `sinister memory <op>` | `tools/forge-memory-bridge/` | Disk-first cross-session memory (jcode-memory parity) |
| `sinister swarm <op>` | `tools/sinister-swarm/` | Multi-agent coordination (jcode-swarm parity) |
| `sinister graph <op>` | `tools/memory-graph-render/` | Memory-graph → mermaid → PNG |
| `sinister login --provider <X>` | `tools/sinister-login/` (planned v0.2.0) | Provider OAuth / API-key (claude/openai/codex/gemini/copilot/azure/ollama/lmstudio/openai-compatible/alibaba-coding-plan/fireworks/minimax) |
| `sinister freeze <op>` | `projects/sinister-freeze/source/` (future) | Joe @ Ferrari of Winter Park lane |
| `sinister term <op>` | `projects/sinister-term/source/term/` | Sinister Term shell (Term agent's PH-CLI integration) |
| `sinister forge <op>` | `projects/sinister-forge/source/forge/` | Sinister Forge TUI (Forge agent's PH17 integration) |
| `sinister help [subcmd]` | umbrella | Print help |
| `sinister version` | umbrella | Print version of every Sinister tool installed |

## Quickstart

```
cd "D:/Sinister Sanctum/tools/sinister-cli"
pip install -e .

sinister memory write --namespace sanctum --key cold-start "Read SESSION-START in order"
sinister memory recall "how do I cold-start?"
sinister swarm dm forge "found a bug"
sinister swarm broadcast "fleet pause in 5 min"
sinister swarm spawn --project sinister-freeze --mode resume --headless
sinister swarm list --stale-minutes 15
sinister graph render --namespace sanctum --output ./sanctum.png
sinister help
sinister version
```

## Dispatch flow

1. `sinister <subcmd> <rest...>` parses `<subcmd>`
2. Lookup in `SUBCOMMAND_MAP` → resolves target package + `main(argv)` callable
3. Import the backend module; if missing, prints install hint + exits 2
4. Call its `main(rest_argv)`; relay its exit code

## Composes with

- `tools/forge-memory-bridge/` — `sinister memory ...`
- `tools/sinister-swarm/` — `sinister swarm ...`
- `tools/memory-graph-render/` — `sinister graph ...`
- `tools/sinister-login/` — `sinister login ...` (planned v0.2.0)
- Forge PH17 — Forge's TUI consumes `sinister forge <op>` per their PROGRESS 12:00Z
- Term PH-CLI — Term renames their `sterm` to `sinister term` per their TODO Image #7
- `_shared-memory/knowledge/sinister-cli-naming-convention.md` — doctrine (planned)
- `_shared-memory/knowledge/jcode-feature-matrix.md` row 29 — implementation reference

## Why umbrella + per-tool dual-CLI

- Each tool keeps its standalone CLI (`forge-memory`, `sinister-swarm`, `memory-graph-render`) for power-users + scripting
- Umbrella `sinister` is the canonical operator-facing surface
- Help text for `sinister <sub> --help` is delegated to the backend, so it stays in sync

## Anti-patterns this avoids

- Five different binaries the operator must remember
- Hard imports requiring every backend installed for ANY subcommand
- Hidden subcommands not listed in `sinister help`
- Inconsistent flag patterns across subcommands
