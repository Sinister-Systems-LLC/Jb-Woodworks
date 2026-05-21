# Sinister Term

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-term` :: branch `agent/sinister-term/<topic>` :: purple accent
> **License:** AGPL-3.0-or-later

## What this is

Sinister Term is our own Sinister-branded terminal — inspired by jehuang's `handterm` (Wayland-only Rust) but adapted for our Windows-10 reality + tightly coupled to Forge + Mind + RKOJ.

`handterm` itself can't be ported as-is — it's Wayland + Linux-only, uses Kitty graphics protocol that ConHost/Windows Terminal don't speak, and assumes Niri compositor. What we CAN take from it is the *philosophy*: hyper-optimised, Sinister-themed, agent-aware, with builtin command shortcuts for our 12-bot fleet + 10 projects.

## Operator directive (verbatim 2026-05-21)

> *"I want everything to be our own shit. like what he did here so we can have our own terminal"*

## Two-track plan

**Track A — Sinister Term v0 (Windows-native, ships fast).** Python + prompt_toolkit. Drop-in shell that:
- Wraps PowerShell/git-bash transparently
- Sinister theme (purple primary, Vault Boy ASCII at boot)
- Builtin slash-commands: `/forge` `/mind` `/launch <project>` `/bot <name>` `/skill <name>` `/agent <name>`
- Auto-completion fed by our `projects.json` + `bots/_INDEX.md` + `skills/_INDEX.md`
- History persisted per-session to `_shared-memory/sinister-term-history/<UTC>.jsonl`
- Cross-references Forge (`Ctrl+F` opens a Forge pane on the current dir's project)

**Track B — Sinister Term v1 (Rust, Windows-Terminal-native).** If v0 proves the design, port the hot path to Rust on top of `ratatui` (same UI toolkit jcode/handterm use). Defer until v0 has 30 days of operator use.

## Phases

| Phase | What | Status |
|---|---|---|
| **PH0** | Scaffold (this commit) | ✅ |
| **PH1** | Python+prompt_toolkit minimal shell w/ Sinister theme + Vault Boy boot | pending |
| **PH2** | Builtin slash-commands (/forge /mind /launch /bot /skill) | pending |
| **PH3** | Auto-completion from projects.json + bots/_INDEX.md + skills/_INDEX.md | pending |
| **PH4** | History persistence (JSONL per session) | pending |
| **PH5** | Forge integration (Ctrl+F spawns Forge pane on cwd project) | pending |
| **PH6** | Mind integration (`/mind` opens http://127.0.0.1:5079/) | pending |
| **PH7** | Rust port evaluation (only if operator says go after 30 days v0) | deferred |

## What we mine from handterm (per the audit)

- Single-binary distribution mindset (vs. install-a-toolchain)
- Per-keypress latency budget (<2ms input-to-screen)
- Status bar at bottom showing cwd / git branch / active agent / pending heartbeat
- Configurable keybinds via JSON (operator can rebind without recompile)

## What we WON'T copy

- Wayland-specific code paths (we're Windows)
- Kitty graphics protocol (Windows Terminal doesn't speak it)
- Niri compositor assumptions
- Tab-management UI (Windows Terminal already does tabs well)

## Cross-references

- `projects/sinister-forge/source/PLAN.md` — sibling (Forge handles agents; Term handles shell)
- `projects/sinister-mind/README.md` — sibling (Mind visualizes the brain)
- `_shared-memory/knowledge/research-import-pipeline.md` — how external repos get audited (this is where handterm went)
- `D:\Research\handterm\` (pending clone target — handterm itself stays read-only reference)
