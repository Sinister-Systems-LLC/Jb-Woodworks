# Sinister Forge :: forward plan (post-9af3407)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Cut at commit:** `9af3407` (Forge branch tip on origin)
> **Operator ask:** *"review everything we need to do. check on the sinister term and sinister sanctum agent and see what you can do without fucking them up. create a plan to complete it all and get to work"*

## Now (this commit)

| ID | Title | Status | Notes |
|---|---|---|---|
| P0-A | Boot crash (`_render` shadowing in 4 widgets) | ✅ shipped | `34af6a8` + `cebf6cf` |
| P0-B | Ctrl+W picker crash (`push_screen_wait` needs `@work`) | ✅ shipped | `79f3ddd` + `aa04a4a` |
| P0-C | Submit auto-closes app (`PickerResult.project_display` missing + worker `exit_on_error=True`) | ✅ shipped | `9af3407` (this commit) |

All three P0s Pilot-verified end-to-end: `boot + Ctrl+W + Submit -> pane mounted, app alive`.

## Master-actionable next (no operator gate required, no sibling-blocked)

| ID | Title | Effort | Lane | Why now |
|---|---|---|---|---|
| F1 | Pilot regression suite under `projects/sinister-forge/source/tests/` covering boot + picker submit + cycle + close + palette | ~30 min | Forge | Lock in fixes; future Textual bumps won't regress silently again |
| F2 | Wire AgentPane `subprocess=` arg from picker submit so the panes actually spawn `claude --dangerously-skip-permissions <phrase>` per the picked host/mode | ~45 min | Forge | Today the pane mounts EMPTY (no subprocess started). PH3/PH4 says spawn, current submit only renders a placeholder log. |
| F3 | Brain entry: `textual-quiet-failure-mode-trilogy` extending `textual-render-shadowing-pitfall` with P0-B (`@work` requirement) + P0-C (`exit_on_error=False`). One unified detection/fix doctrine. | ~15 min | Forge | All three bugs share root cause "Textual swallows exception → app dies/freezes silently in wrapper bat"; consolidating compounds the lesson |
| F4 | Reply to Sinister Term inbox ASK 11:42Z (interactive-test message) — just an ACK; their agent was probing the inbox roundtrip | ~5 min | Forge | Lane hygiene |
| F5 | Resume-point write (post-F1/F2/F3) | ~2 min | Forge | CONTRACT 7 close |

## Sibling-coupled (read their state, drop ASKs, do NOT touch their source)

| Sibling | Status | What I'm doing | What I'm NOT doing |
|---|---|---|---|
| Sinister Sanctum | Heartbeat 06:48Z (~90 min stale); last PROGRESS 11:30Z noted active builds on `tools/forge-memory-bridge/` + `tools/memory-graph-render/` + 5 brain entries shipped 11:30Z | Read-only. My `forge/mermaid_render.py` already routes-through their `tools/memory-graph-render/` per the HELLO-ACK I dropped (`inbox/sanctum/2026-05-21T1145Z-hello-ack-from-forge.json`). | Will NOT edit `tools/` (their lane). Will NOT touch `projects/sinister-freeze/` (Joe lane, Sanctum-scaffolded). |
| Sinister Term | Heartbeat 07:42Z (fresh, ~20 min). Operates in its own worktree at `D:/Sinister-Term-WT/`. Already pushed commits on its branch via my Term-branch detour | ACK their 11:42Z interactive-test ASK in their inbox. | Will NOT edit `projects/sinister-term/source/` (their lane). Will NOT push to `agent/sinister-term/*` (classifier-blocked correctly). |
| RKOJ Workstation | Heartbeat 07:09Z (~50 min). Active. My R7 Forge-tab spec sitting in `inbox/rkoj/2026-05-21T1108Z-forge-dashboard-spec.json` | Wait for their ack at `cross-agent/<UTC>-rkoj-to-sinister-forge-ack.md`. Non-blocking. | Will NOT edit RKOJ source. |

## Operator-gated (one-liner each, not blocking me)

| ID | Title | Operator action |
|---|---|---|
| O1 | Install `mmdr` binary so R8 wrapper actually renders | `scoop install mmdr` OR `cargo install mermaid-rs-renderer` |
| O2 | Authorize cargo build for PH14 live agentgrep benchmark | `cargo build --release` inside `D:\Research\agentgrep\` OR add Bash allow-rule |
| O3 | Create GitHub repo R12 | `gh repo create Sinister-Systems-LLC/Sinister-Forge --private` |
| O4 | Answer PLAN.md Q1-Q5 (or accept defaults already in effect) | Reply in inbox or just say "defaults are fine" |

## Sanctum-delegated (waiting on their lane)

| ID | Title | Blocker |
|---|---|---|
| D1 | `tools/sinister-cli/` top-level dispatcher (per operator 11:50Z image — `sinister <command>` rebrand) | Sanctum picks up; Forge consumes via `sinister forge` subcommand once it lands. Tracked in `cross-agent/2026-05-21T1200Z-forge-to-sanctum-jcode-swarm-and-sinister-cli-absorption.md`. |
| D2 | 11-provider OAuth/token wallet | Same lane; Forge picker Q4 extends once available |

## Week+ horizon (after the immediate sweep)

- **PH16 jcode-swarm parity**: `watchdog` observer in `forge.bridge.registry` + `:swarm`/`:dm`/`:broadcast` pane builtins. Sized ~half day.
- **PH18 niri scrollable multi-pane**: replace `TabbedMultiPane` with `ScrollableColumns`. Sized ~half day. Operator-visible payoff is large; ordering matters.
- **PH12 Skill_Seekers integration**: clone + wrap; gated on operator-approved external clone+build (same AUP wall as PH14).
- **PH13 claude-hooks integration**: clone + wrap; same gate.

## What I am explicitly NOT touching this turn (lane discipline)

- `tools/` anywhere (Sanctum's domain)
- `projects/sinister-term/source/` (Term agent's domain; they have their own worktree)
- `projects/sinister-freeze/source/` (will be a dedicated Freeze agent's domain once handoff)
- `projects/sinister-panel/source/` (Panel agent's domain)
- `_shared-memory/PROGRESS/Sinister Term.md`, `Sinister Sanctum.md`, etc. (sibling-owned)
- `automations/start-sinister-session.ps1` (cross-lane hot file)
- `~/.claude/.mcp.json` (operator-owned)
- LICENSE (operator-owned)
- Force-pushes to any branch
- Cherry-picks across to sibling branches (already triggered classifier; respecting that)

## Cross-references

- `projects/sinister-forge/source/PLAN.md` — full phase plan PH0-PH18
- `_shared-memory/plans/sinister-forge-2026-05-21/plan.md` — original R-row forward plan
- `_shared-memory/plans/sinister-forge-2026-05-21/agentgrep-eval.md` — PH14 static verdict + 3 unlock paths
- `_shared-memory/knowledge/sinister-forge-harness-pattern.md` — wrap-don't-replace doctrine
- `_shared-memory/knowledge/textual-render-shadowing-pitfall.md` — P0 doctrine (to be extended by F3)
- `_shared-memory/knowledge/jcode-feature-parity-targets.md` — niri + swarm + sinister-CLI directives absorbed
- `_shared-memory/cross-agent/2026-05-21T1200Z-forge-to-sanctum-jcode-swarm-and-sinister-cli-absorption.md` — Sanctum delegation
