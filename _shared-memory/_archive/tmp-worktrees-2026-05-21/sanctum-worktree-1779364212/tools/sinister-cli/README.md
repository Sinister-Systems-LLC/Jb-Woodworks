# sinister-cli

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Operator directive (verbatim 2026-05-21):** *"our commands will be sinister then the command"* (+ screenshot of jcode's `jcode login --provider <X>` pattern)
> **Status:** v0.1.0 — umbrella dispatcher; subcommands resolve at runtime to installed sibling tools

## What it is

The single top-level `sinister` CLI that dispatches to per-tool entry-points. Mirrors jcode's `jcode <subcommand>` UX (`jcode login --provider claude`, `jcode swarm spawn`, etc.) — but Sinister-branded.

## Subcommand map

| Command | Backend tool | Purpose |
|---|---|---|
| `sinister memory <write/recall/list/graph/consolidate/delete/info>` | `tools/forge-memory-bridge/` | Disk-first cross-session memory (jcode-memory parity) |
| `sinister swarm <dm/broadcast/spawn/list/watch/mark-done/wait-for/hive-status/whoami>` | `tools/sinister-swarm/` | Multi-agent coordination (jcode-swarm parity) |
| `sinister graph <render>` | `tools/memory-graph-render/` | Memory-graph → mermaid → PNG (jcode-memory-visualization parity) |
| `sinister login --provider <claude/openai/codex/gemini/copilot/azure/ollama/lmstudio/openai-compatible/...>` | `tools/sinister-login/` (stub v0.1.0) | Provider OAuth / API-key management (jcode-login parity) |
| `sinister freeze <subcommand>` | `projects/sinister-freeze/source/` (future) | Joe @ Ferrari of Winter Park lane |
| `sinister term <subcommand>` | `projects/sinister-term/source/term/` | Sinister Term shell |
| `sinister forge <subcommand>` | `projects/sinister-forge/source/forge/` | Sinister Forge TUI |
| `sinister help [subcommand]` | n/a | Print help |
| `sinister version` | n/a | Print version of every Sinister tool installed |

## Quickstart

```bash
cd "D:/Sinister Sanctum/tools/sinister-cli"
pip install -e .

# Use:
sinister memory write --namespace sanctum --key cold-start "Read SESSION-START in order"
sinister memory recall "how do I cold-start?"
sinister swarm dm forge "found a bug"
sinister swarm broadcast "fleet pause in 5 min"
sinister swarm spawn --project sinister-freeze --mode resume --headless
sinister swarm list --stale-minutes 15
sinister swarm watch --path automations/start-sinister-session.ps1
sinister graph render --namespace sanctum --output ./sanctum.png
sinister login --provider claude
sinister version
```

## How dispatch works

1. `sinister <subcmd> <rest...>` parses `<subcmd>`
2. Looks up in `SUBCOMMAND_MAP` — finds the target package + entry function
3. Tries to import the backend module (graceful-degrade if not installed)
4. If imported, calls its `main()` with `<rest...>` as argv
5. If NOT installed: prints `"pip install <pkg>"` hint and exits 2

## Composes with

- `tools/forge-memory-bridge/` — `sinister memory ...`
- `tools/sinister-swarm/` — `sinister swarm ...`
- `tools/memory-graph-render/` — `sinister graph ...`
- `tools/sinister-login/` — `sinister login --provider ...` (v0.2.0)
- Per-project source trees — `sinister freeze/term/forge/...` (future)
- `_shared-memory/knowledge/sinister-cli-naming-convention.md` — doctrine that drove this design

## Why an umbrella

- Discoverability: operator types `sinister` and sees every subcommand
- jcode-pattern parity: matches the `jcode <cmd>` UX the operator picked
- Plugin-friendly: dropping a new tool with a `sinister-*` entry-point auto-shows up (v0.2.0 plugin-scan)
- Single command to memorize; subcommands handle the depth

## Anti-patterns this avoids

- ❌ Five different `forge-memory`, `memory-graph-render`, `sinister-swarm` CLIs operator has to remember
- ❌ Hard imports requiring every backend to be installed for any subcommand to work
- ❌ Hidden subcommands not listed in help
