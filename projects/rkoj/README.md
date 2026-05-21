> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ — Sinister Sanctum's unified jcode-form agent system

**Version:** v1.4.0 (2026-05-21) — see `CHANGELOG.md`.

**One-line:** RKOJ is the Sinister Sanctum unified agent system — jcode form-factor at the core, expanded with every skill, bot, vault tap, swarm coordinator, and BM25 memory layer the fleet has built. EVE persona runs the orchestration. One EXE, one prompt, one console.

This directory is the **umbrella project**. It does not duplicate source code — every component lives in its native lane on disk. RKOJ is the integration layer that names them, indexes them, builds them, and ships them as a single `RKOJ.exe`.

**Component count:** 26 entries in `MANIFEST.json` after v1.3.0 (forge sub-pieces incl. AgentsDashboard + workstation tab + niri-workspace + theme; 11 sinister-* tools; 5 relocated `sinister-*` projects via GG2 Phase 3).

## What "unified" means here

Per operator directive (2026-05-21, image 27 escalation):

> *"make sure this is all in one proejct in the siniser sanctum called RKOJ. and it has all that we have built for this, the workstation, termina;l, forge all it i is suppose to be one system using the jcode as a base and expanding off of it with all our skills, bots etc."*

RKOJ binds these surfaces into one product:

- **Forge TUI** — the multi-pane front door (sidebar + ADB + agent panes)
- **Terminal (sterm)** — the shell layer beneath Forge; also exposed as standalone CLI
- **Workstation** — the Console window manager (pywebview + FastAPI :5077)
- **Skills** — operator's portable behavior packs (50+ skills)
- **Bots** — 12 LLM-orchestration agents (sentinel, librarian, custodian, ...)
- **Sinister-* tools** — login, usage, swarm, model, vault, jcode-shim, ...
- **Build pipeline** — PyInstaller assembly into `RKOJ.exe`

## Components

| Slot | Source path | Kind |
|---|---|---|
| `forge` | `projects/sinister-forge/source/forge/` | Multi-pane TUI (sidebar, ADB tab, agent panes) |
| `term` | `projects/sinister-term/source/term/` | Terminal shell (sterm) — RKOJ.exe shell layer |
| `workstation` | `automations/window-manager/` | Console (pywebview + FastAPI :5077) |
| `skills` | `skills/` + `~/.sinister/skills/` | Operator skill registry |
| `bots` | `bots/` (junctions to `D:/Sinister/Sinister Skills/12_LLM_ORCHESTRATION/agents/`) | 12 LLM orchestration bots |
| `tools/sinister-cli` | `tools/sinister-cli/` | Umbrella CLI dispatcher |
| `tools/sinister-login` | `tools/sinister-login/` | Anthropic auth bridge |
| `tools/sinister-usage` | `tools/sinister-usage/` | API/token usage tracker |
| `tools/sinister-swarm` | `tools/sinister-swarm/` | Multi-agent coordinator |
| `tools/sinister-model` | `tools/sinister-model/` | Model picker / pin |
| `tools/sinister-vault` | `tools/sinister-vault/` | Vault MCP (1 TB collaborative store :5078) |
| `tools/sinister-jcode-shim` | `tools/sinister-jcode-shim/` | jcode CLI shim / sidecar |
| `tools/sinister-review` | `tools/sinister-review/` | Code review helper |
| `tools/sinister-chatbot` | `tools/sinister-chatbot/` | Chatbot front-end |
| `tools/sinister-crawler` | `tools/sinister-crawler/` | Web crawler |
| `tools/sinister-phone-viewer` | `tools/sinister-phone-viewer/` | scrcpy / ADB viewer |
| `build` | `automations/build/forge-exe/` | PyInstaller pipeline → `RKOJ.exe` |

## jcode parity matrix

RKOJ targets full jcode parity AND extends it. The form factor (single-EXE, slash commands, thinking deltas) is the floor; our skills/bots/vault/swarm are the ceiling.

| Capability | jcode | RKOJ | Notes |
|---|---|---|---|
| Single-EXE distribution | yes | yes | PyInstaller one-file |
| Slash-command vocabulary (60+) | yes | yes | `/help /clear /compact /context /save /unsave /rename /rewind /start /resume ...` |
| Thinking deltas (panel) | yes | yes | `anthropic_direct.py` extended-thinking |
| Parallel tool use | yes | yes | SDK tool-use loop with concurrency |
| Prompt caching | yes | yes | Cache-aware messages.create |
| Batch tools | yes | yes | Message batch API path |
| BM25 + TF-IDF memory | partial | yes | `forge_memory_bridge` |
| Ruflo MCP integration | no | yes | agentdb, hooks, swarm, hive-mind |
| Skill registry | no | yes | operator skills + plugin skills |
| Session save/restore | yes | yes | journal JSONL + `/save` `/resume` |
| Direct Anthropic SDK fallback | partial | yes | `anthropic_direct.py` |
| Multi-pane TUI (Forge) | no | yes | sidebar + ADB + N agent panes |
| Vault tap (:5078) | no | yes | sinister-vault MCP |
| Swarm coordinator | no | yes | sinister-swarm + Ruflo coordination |
| EVE persona | n/a | yes | operator-canonical identity |

## Quick-start

1. Build: `pwsh automations/build/forge-exe/build.ps1`
2. Run: `RKOJ.exe` → Forge TUI launches by default
3. Help: type `/help` inside the TUI
4. Shell fallback: `RKOJ.exe --shell` for the v0.x `>` prompt

## Where to look for what

- **Bug in a slash command?** → `projects/sinister-forge/source/forge/spawn/` + `projects/sinister-term/source/term/`
- **Memory recall wrong?** → `tools/sinister-vault/` + `forge_memory_bridge`
- **Skill not loading?** → `skills/_INDEX.md` and `~/.sinister/skills/`
- **Window won't dock?** → `automations/window-manager/`
- **EXE build broken?** → `automations/build/forge-exe/build.ps1`
- **Manifest of what's bundled** → `projects/rkoj/MANIFEST.json` (also `RKOJ.exe info`)
- **How the pieces connect** → `projects/rkoj/INTEGRATION.md`
- **What shipped when** → `projects/rkoj/CHANGELOG.md`

## Lane discipline

This umbrella project DOES NOT own the source of any component. Each component lane (sinister-forge, sinister-term, etc.) keeps its own branch, CLAUDE.md, and PROGRESS log. RKOJ documents the integration; the component lanes do the work.

Branch prefix for umbrella-only work: `agent/rkoj/<short-topic>`.
