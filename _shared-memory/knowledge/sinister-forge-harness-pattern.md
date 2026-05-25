<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Forge harness pattern (wrap-don't-replace Claude/Codex)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Slug:** `sinister-forge-harness-pattern`
> **Status:** doctrine
> **Tags:** forge, harness, subprocess, claude-code, codex, jcode-mining, agpl-quarantine, contracts, multi-provider, ui-pattern, doctrine

## The pattern

Sinister Forge is a **TUI harness** that wraps `claude --dangerously-skip-permissions <phrase>` (or `codex -q <phrase>`, or any future provider) as a subprocess inside its own pane and presents the I/O nicely — boot art, scrollback buffer, project-name header, status pip, multi-pane layout, picker overlay, resume-point integration.

The harness does **NOT** reimplement the agent. The brain, the contracts, the MCP network, the Ruflo agentdb tools, the Vault MCP, the sinister-bus heartbeat — all of that lives inside the spawned subprocess unchanged. Forge is just the chrome around the existing fleet.

```
┌──────────────────────────────────────────────────────────────────┐
│ Sinister Forge (Python + Textual, AGPL-3.0)                      │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│ │ Pane: panel    │  │ Pane: forge    │  │ Pane: rkoj     │       │
│ │ ▼ claude exe  │  │ ▼ claude exe  │  │ ▼ codex exe   │          │
│ │   subprocess  │  │   subprocess  │  │   subprocess  │          │
│ │   (full brain │  │   (full brain │  │   (full brain │          │
│ │    + contracts│  │    + contracts│  │    + contracts│          │
│ │    + MCP)    │  │    + MCP)    │  │    + MCP)    │             │
│ └───────────────┘  └───────────────┘  └───────────────┘          │
│                      ▲                                            │
│                      │ Forge ONLY adds: UI, keybinds, picker,    │
│                      │ resume-point auto-load, RKOJ panel, boot │
│                      │ art, theme. NOT the agent itself.        │
└──────────────────────────────────────────────────────────────────┘
```

## Why wrap-not-replace

1. **Brain preservation** — 130+ knowledge entries + 6 session contracts + lane discipline only exist because every agent reads them on cold-start. Replacing the agent means re-implementing the loader. Wrapping leaves it untouched.
2. **AGPL-quarantine for jcode** — jcode is MIT, Sanctum is AGPL-3.0. Importing jcode source into Forge would force re-licensing OR vendor under MIT. Mining jcode's *patterns* (look-and-feel, multi-pane, scroll buffer, animated boot, multi-provider routing) without importing its code keeps the license boundary clean. Reference jcode at `D:\Research\jcode\` read-only; mirror behaviors in our Python+Textual stack.
3. **Provider neutrality** — same harness wraps Claude, Codex, Ollama, LM Studio, Together, Fireworks. The JSON-RPC-over-stdin/stdout contract is stable; the inner agent swaps. Without wrap-don't-replace, every provider switch would require rewriting agent internals.
4. **Operator velocity** — operator can read + modify the Forge source (Python) without a Rust toolchain. Forge ships in hours, not weeks. The agent it wraps already exists.

## What Forge owns

- **UI layer**: panes, scrollback buffer, picker overlay (Ctrl+W), boot art, theme, status bar.
- **Subprocess lifecycle**: spawn, tail stdout/stderr, status flips (running/idle/exited), kill.
- **Resume integration**: read `pre_warm_reads` from latest resume-point per project on pane open; write resume-point on pane close via `automations/resume-point-write.ps1`.
- **Cross-agent surface**: the REST/SSE bridge at `:5078` exposes the same lifecycle to the mobile Claw client + the planned RKOJ Forge tab.
- **Keybinds + picker**: same Q1-Q5 picker the launcher PS1 uses, lifted into a Textual modal.

## What Forge explicitly does NOT own

- The agent's prompt, memory, tool registry, MCP wiring — that's the spawned process's domain.
- The brain (`_shared-memory/knowledge/`) — read by the spawned agent, not by Forge.
- The session contracts (`automations/session-contracts.md`) — injected into the spawned agent's cold-start phrase, not interpreted by Forge.
- The auto-cleanup / auto-backup / context-pruner background daemons — they run via Windows scheduled tasks, orthogonal to Forge.

## Composes with

- `auto-mode-launcher-pattern` — `forge` mode in the launcher PS1's BuiltinPhrases is the spiritual successor; both lift the picker into a one-click flow.
- `multi-agent-branch-contention-isolation-pattern` — each Forge pane spawns its agent on its own `agent/<slug>/...` branch; harness enforces isolation per-pane. **Empirically reinforced 2026-05-21 11:20Z when a sibling agent's `git checkout` clobbered this very brain entry's first draft — recovery via re-write + immediate commit per the doctrine.**
- `forge-bridge-rest-sse-pattern` — the REST/SSE bridge is the same architecture extended out to mobile clients; same wrap-don't-replace logic.
- `rkoj-workstation-ui-layout` — RKOJ stays the workstation, Forge stays the agent harness; F2 toggle in Forge embeds RKOJ as a side panel (PH7) without merging the two products.

## Anti-patterns

- **Forge spawns its own LLM call** (forbidden) — defeats the brain + contract loading. Always spawn the existing `claude` / `codex` binary.
- **Forge edits files the agent owns** — pane UI never writes inside `projects/<slug>/source/`. The agent writes; Forge displays.
- **Forge maintains its own conversation history** — the agent already does, via Claude Code's own session log + the resume-point chain. Forge's scrollback is presentation-only; closing a pane and reopening it doesn't lose history because the agent's transcript persists on disk.
- **Forge becomes a meta-orchestrator** — it's UI. The orchestration (Ruflo MCP, sinister-bus, cross-agent inbox) is its own layer. Don't conflate.

## Where to land changes

- Pure UI tweaks (theme, art, keybinds, picker layout) → `projects/sinister-forge/source/forge/`.
- Subprocess contract changes (new --flag, env var passthrough) → `projects/sinister-forge/source/forge/spawn/claude.py` + `codex.py`.
- Bridge endpoints → `projects/sinister-forge/source/forge/bridge/server.py`.
- New providers → add a sibling `spawn/<provider>.py` + extend the picker's host enum.
- Pattern documentation → this brain entry + `forge-bridge-rest-sse-pattern`.

## Cross-references

- `projects/sinister-forge/PLAN.md` — phase plan PH0-PH15
- `_shared-memory/plans/sinister-forge-2026-05-21/plan.md` — forward R-row plan
- `_shared-memory/plans/sinister-forge-2026-05-21/jcode-memory-feature.md` — jcode mining notes (memory crate review)
- `_shared-memory/plans/sinister-forge-2026-05-21/sanctum-audit-findings.md` — TOP-5 tools audit (PH12-PH15 origins)
- `automations/agent-host-routing.md` — multi-provider routing contract pin Forge → claude-opus-4-7 default
- `D:\Research\jcode\` — read-only reference (mine patterns, never import source)
