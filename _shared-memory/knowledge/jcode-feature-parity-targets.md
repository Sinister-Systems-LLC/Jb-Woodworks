<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 180
-->
# jcode → Sinister feature parity targets (mining roadmap)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Slug:** `jcode-feature-parity-targets`
> **Status:** roadmap
> **Tags:** jcode, mining, forge, swarm, multi-provider, sinister-cli, login-flows, parity, branding, rebrand, roadmap, sinister-forge

## Operator directives this turn (2026-05-21)

- *(image 11:43Z to Sanctum)* "make sure we do what jcode does and use tools like this in our own way and branding like i said" — re: `https://github.com/niri-wm/niri` scrollable-tiling Wayland WM.
- *(image 11:48Z)* "i want all jcode features in our system like this" — re: jcode swarm (multi-agent collaboration with server-mediated file-edit notifications + DM/broadcast + spawned sub-swarms).
- *(image 11:50Z)* "our commands will be sinister then the command" — re: jcode login flows (`jcode login --provider X` for 11 providers).

## Feature parity matrix

| jcode feature | Sinister analogue (today) | Gap | Lane owner | Target |
|---|---|---|---|---|
| **Auto-recall memory** | `_shared-memory/knowledge/_INDEX.md` hand-curated + `tools/forge-memory-bridge` (Sanctum-shipped Ruflo wrapper) | Auto-recall mid-turn via `agentdb_pattern-search` not yet wired into Forge | Sanctum (bridge) + Forge (in-pane invocation) | PH16 Forge |
| **Memory write** | `sinister-bus.heartbeat` + brain entry append-only protocol + `tools/forge-memory-bridge.write` | Need operator-facing `sinister memory write "<fact>"` CLI | Sanctum | brain command |
| **Memory consolidation** | `automations/memory-consolidate.ps1` (Sanctum-shipped) | Nightly cron not yet installed | Sanctum | scheduled task |
| **Memory graph viz** | `tools/memory-graph-render/` (Sanctum) + `forge/mermaid_render.py` (Forge wrapper) | Need fleet brain-graph viewable in RKOJ Forge tab (R7 ASK pending) | RKOJ + Forge | PH7 + R7 |
| **Multi-provider routing** | `automations/agent-host-routing.md` (12 task-class rows + 9 project-lane rows) | Only Claude + Codex spawn paths exist; 9 other providers planned | Sanctum (routing) + Forge (per-pane host picker) | PH10 + R10 expansion |
| **`X login --provider Y` flows** | None — secrets live in `_vault/` and operator-set env vars per provider | 11 provider flows missing: claude / openai / gemini / copilot / azure / alibaba-coding-plan / fireworks / minimax / lmstudio / ollama / openai-compatible | Sanctum (CLI) | PH17 |
| **`sinister <command>` top-level CLI** | Per-tool entry points only (`forge`, `sinister-forge`, `sinister-forge-bridge`, `python -m mind`, `python -m term`) | No top-level `sinister` dispatcher routing to subcommands | Sanctum | PH17 |
| **Swarm spawn** | `forge.bridge.registry` subprocess.Popen pool + `_shared-memory/inbox/` async messaging | Missing in-band file-edit notification pump + `:swarm spawn` Forge builtin | Forge | PH16 |
| **Agent DM / broadcast** | `inbox/<slug>/<UTC>-*.json` + `cross-agent/*.md` | Works but operator needs to type JSON. Forge builtin `:dm <slug>` + `:broadcast` is the UX win | Forge | PH16 |
| **Agent spawns sub-swarm** | `Start-Process` from any agent's bash + `forge.bridge.POST /api/forge/agents` | Works headlessly; lacks operator visibility of swarm tree | Forge | PH16 |
| **Conflict auto-resolution on file race** | `multi-agent-branch-contention-isolation-pattern` doctrine (manual recovery) | jcode auto-resolves at server level. Adopting requires file-change watchdog + 3-way merge attempt | Forge OR Sanctum | TBD |
| **Scrollable-tile multi-pane** *(niri pattern)* | `TabbedMultiPane` (Textual TabbedContent) — hides non-current panes | niri-style horizontal scroll keeps all panes visible | Forge | PH18 candidate |
| **Animated boot art** | `forge.art.BOOT_FRAMES` (Vault Boy ASCII) + `BootScreen` widget | Already shipped (PH5) | Forge | ✅ done |
| **jcode-look TUI** | Textual + Cascadia Code + purple theme | Already shipped (PH1-PH9 + PH11 liquid-glass polish) | Forge | ✅ done |
| **Status bar with live counts** | `ChromeBar` + `StatusFooter` widgets | Already shipped (PH9 — and just unbreaked from the _render shadowing bug) | Forge | ✅ done |
| **Command palette (fuzzy)** | `forge.panes.command_palette.CommandPalette` (Ctrl+P) | Already shipped (PH11) | Forge | ✅ done |

## Branding rule (binding for all new CLI surfaces)

**All new operator-facing CLI commands**: `sinister <verb>` not `<tool> <verb>`.

Examples per the operator directive:
- ✅ `sinister forge`
- ✅ `sinister login --provider claude`
- ✅ `sinister swarm spawn sinister-panel resume`
- ✅ `sinister memory write "lipsum"`
- ❌ `forge spawn` (current pattern) → rebrand to `sinister forge spawn`
- ❌ `jcode login --provider claude` (jcode's pattern; we don't ship jcode commands)

Existing entry points like `python -m forge` STAY for the dev loop (faster than full CLI re-init); the `sinister` dispatcher is the operator-facing surface.

## Lane split (who builds what)

| Capability | Lane | Reasoning |
|---|---|---|
| `tools/sinister-cli/` dispatcher | **Sanctum** | Top-level fleet infra, not Forge-internal |
| `sinister login --provider X` flows | **Sanctum** | Talks to `_vault/`; security-sensitive |
| `sinister forge` subcommand → `python -m forge` | **Sanctum** dispatcher + **Forge** target | Forge keeps the entry point; Sanctum routes to it |
| `sinister swarm spawn` subcommand | **Sanctum** (dispatcher) + **Forge** (impl via bridge) | Bridge already has spawn semantics |
| File-edit notification pump (jcode swarm parity) | **Forge** | Sits inside `forge.bridge.registry` |
| In-pane builtins (`:dm`, `:broadcast`, `:swarm`) | **Forge** | Pane-local UX |
| niri scrollable-tile multi-pane | **Forge** | Pure UI |
| Memory auto-recall in-turn | **Forge** consumer of **Sanctum** `tools/forge-memory-bridge` | Sanctum owns store, Forge owns trigger |

## Anti-patterns

- **Don't import jcode source.** Sinister Forge is AGPL-3.0; jcode is MIT. Mining patterns is allowed; importing source forces re-license OR vendor under MIT and we lose AGPL guarantees. Reference jcode at `D:\Research\jcode\` read-only.
- **Don't double-implement the `sinister` dispatcher inside Forge.** Forge stays a SUBCOMMAND target. If Sanctum hasn't shipped the dispatcher yet, Forge keeps its current entry points and waits.
- **Don't strip the lane discipline for "feature parity speed."** Multi-agent contention is REAL (this very session hit it 4+ times). The brain doctrines are the contract; jcode's auto-resolution is a future enhancement on top, not a replacement.
- **Don't rebrand the `sinister-bus` MCP or other already-established surfaces** unless explicitly asked. The rebrand is for new CLI commands, not retroactive renaming of stable APIs.

## Composes with

- `sinister-forge-harness-pattern` — wrap-don't-replace; mining jcode patterns FITS the doctrine.
- `forever-expanding-modular-architecture-doctrine` — composition over silos; Sanctum dispatcher + Forge subcommands is the pattern.
- `forge-bridge-rest-sse-pattern` — the bridge is the swarm collaboration substrate.
- `multi-agent-branch-contention-isolation-pattern` — jcode auto-resolution maps onto our explicit branch isolation; both are valid, ours is more durable for parallel Claude Code sessions.
- `textual-render-shadowing-pitfall` — discovered while landing the picker fix this turn; relevant because the swarm/CLI work will add more widgets that need the same hygiene.

## Cross-references

- jcode repo (operator's reference): mining from `D:\Research\jcode\` only.
- niri-wm repo (operator's reference for tiling pattern): `https://github.com/niri-wm/niri`
- `projects/sinister-forge/PLAN.md` — gets PH16/PH17/PH18 addenda
- `automations/agent-host-routing.md` — gets 11-provider extension
- `_shared-memory/cross-agent/2026-05-21T1200Z-forge-to-sanctum-jcode-swarm-and-sinister-cli-absorption.md` — paired delegation message
