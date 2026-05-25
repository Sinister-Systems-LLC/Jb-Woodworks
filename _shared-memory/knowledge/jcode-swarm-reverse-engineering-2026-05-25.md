<!-- Author: RKOJ-ELENO :: 2026-05-25 -->

<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 120
-->
# jcode swarm reverse-engineering + Sinister coverage matrix

**Slug:** jcode-swarm-reverse-engineering-2026-05-25
**First discovered:** 2026-05-25 ~02:20Z by Sinister Sanctum (EVE) lane `sanctum-jcode-swarm-review`
**Status:** audit (read-only), proposal source for `swarm-improvements-overseer-led-2026-05-25.md`
**Tags:** audit, jcode, swarm, sub-agents, coordinator, overseer, parity, expansion-source, 2026-05-25
**Composes with:** `jcode-swarm-token-parity-audit-2026-05-23.md`, `jcode-full-feature-audit-2026-05-24.md`, `parallel-agent-orchestration-pattern-2026-05-21.md`, `mesh-coordination-and-resource-lifecycle-2026-05-24.md`

---

## Phase 1 - jcode swarm reverse-engineering

Source: `C:\Users\Zonia\Desktop\jcode-0.12.4\` (v0.12.4, read-only).

### 1.1 Architecture - 3 roles, server-mediated

Per `docs/SWARM_ARCHITECTURE.md` (status: Proposed; matches what is in code):

- **Coordinator** - sole spawner / stopper of agents; owns plan v1; reviews plan updates; routes operator interaction.
- **Worktree Manager** - owns a single git worktree scope; coordinates agents inside; owns integration back to main.
- **Agent** - executes tasks; receives full plan + scoped instructions on spawn; can propose plan updates; cannot spawn or stop peers.

### 1.2 Wire protocol - 12 swarm verbs (jcode-protocol/src/wire.rs)

All swarm operations are first-class wire messages routed through a long-running daemon (not per-spawn .ps1 + .bat orchestration):

| Verb | Purpose |
|---|---|
| `comm_spawn` | coordinator-only; creates new agent session with optional working_dir + initial_message + spawn_mode |
| `comm_stop` | coordinator-only; force-flag for hard kill |
| `comm_assign_role` | flip Agent / Coordinator / WorktreeManager role |
| `comm_assign_task` | coordinator assigns specific plan task to specific session |
| `comm_assign_next` | coordinator says "give the next runnable unassigned task to <target>" (optionally spawn if needed) |
| `comm_task_control` | start / wake / resume / retry / reassign / replace / salvage actions |
| `comm_subscribe_channel` / `comm_unsubscribe_channel` | topic-channel pub/sub for group coordination |
| `comm_await_members` | block until a set of sessions reach target_status; timeout default 1 hour |
| `comm_report` | structured completion report (message + validation + follow_up) |
| `comm_summary` | short activity feed (tool calls + intent + brief results) |
| `comm_status` | lock-free metadata snapshot - readable even while agent is mid-tool |
| `comm_read_context` | heavy read of full conversation history (used sparingly) |
| `comm_plan_status` / `comm_resync_plan` | shared swarm-plan DAG status + on-demand resync |

### 1.3 Lifecycle states (jcode-swarm-core/src/lib.rs)

13 explicit states: `spawned`, `ready`, `running`, `running_stale`, `completed`, `done`, `failed`, `stopped`, `crashed`, `queued`, `blocked`, `pending`, `todo`. Serde-typed enum prevents stringly-typed drift. Each agent emits lifecycle notifications; coordinator decides respawn / rescope / shutdown / complete.

### 1.4 Spawn modes (jcode-config-types/src/lib.rs `SwarmSpawnMode`)

Three modes, configured via `AgentsConfig.swarm_spawn_mode`:

- `Visible` (default) - new terminal window per agent.
- `Headless` - in-process worker, no terminal.
- `Auto` - try visible, fall back to headless if no window can be opened.

Also: `AgentsConfig.swarm_model` lets the coordinator override which model spawned sub-agents use (cheaper model for fan-out workers).

### 1.5 Completion report contract (enforced by core)

`MAX_SWARM_COMPLETION_REPORT_CHARS = 4000`. `SWARM_COMPLETION_REPORT_MARKER = "SWARM COMPLETION REPORT REQUIRED"`. The function `append_swarm_completion_report_instructions()` injects a `<system-reminder>` into every spawn prompt instructing the worker to call `swarm.report` before finishing with: message + validation + follow-up. Idempotent (safe to call twice).

Forced contract per `docs/SWARM_ARCHITECTURE.md`:
- Spawned/assigned agents with a `report_back_to_session_id` MUST end each turn with a useful final assistant response.
- Server auto-forwards that final response to the coordinator as the completion report.
- Reports required for: spawn prompts, assigned plan tasks, start/wake/resume/retry runs.
- Reports NOT required for: idle no-prompt spawns, user-peers without owner, ordinary mid-work status broadcasts, intentional idle cleanup.

### 1.6 Communication topology

- DMs (1:1) + Swarm broadcast (1:N) + Topic channels (group, bidirectional indexed via `ChannelIndex`).
- Shared context keys (set/read/append) for soft state.
- All inter-agent messages delivered as **soft-interrupt notifications** injected at safe points within a running turn (no new-turn round-trip required).
- Completed / idle agents do NOT auto-resume on notification - explicit `assign_task` / `wake` / `respawn` required.

### 1.7 Conflict handling

**Optimistic / no locks.** Coordination via DM + channels, not via the coordinator. Touch-notifications are used for conflict detection; agents resolve directly via DM. Worktrees provide hard isolation only when justified (large refactor / risky change / divergent deps).

### 1.8 UI (TUI)

Two real-time widgets:
- **Swarm info widget** - graph of agents + worktree managers + coordinator + channels; nodes show status + intent; live edges for DM / channel / broadcast.
- **Plan info widget** - DAG of tasks with dependencies; nodes carry owner + scope + status + checkpoints + heartbeat-age + last-checkpoint-summary.

### Top-5 jcode swarm patterns (1-liner each)

1. **Coordinator-owned spawn monopoly + 13-state lifecycle enum** - one entity allowed to spawn/stop; serde-typed states.
2. **Server-mediated wire protocol with 12 swarm verbs** - long-running daemon vs per-spawn .ps1 orchestration.
3. **Soft-interrupt notification injection at safe points** - inter-agent comms interleave inside a turn without new round-trip.
4. **Mandatory completion-report contract enforced by core** - 4KB cap, idempotent system-reminder injector, structured (message + validation + follow-up).
5. **Live swarm + plan TUI widgets with DAG visualization** - operator can SEE the swarm graph + plan graph updating from events.

---

## Phase 2 - Sinister swarm coverage matrix

Source: `D:\Sinister Sanctum\` (current branch `agent/sinister-os-mobile/p0-spec-2026-05-24`, working tree).

### 2.1 What Sinister has today (verified by file read)

| Capability | Surface | Status |
|---|---|---|
| Spawn child Claude sessions | `start-sinister-session.ps1` (1600+ LOC) + `claude --dangerously-skip-permissions` | shipped (per-spawn .ps1 + .bat, NOT a daemon) |
| Per-spawn picker (project + modes) | `start-sinister-session.ps1` `Prompt-AgentModes` | shipped; asks swarm Y/N + loop Y/N + loop_condition |
| Sibling-detect pre-spawn | `automations/detect-similar-agents.ps1` | shipped; injected into cold-start phrase |
| Resource-lock primitive (mesh-coord) | `automations/mesh-coordinator.ps1` | shipped; file-based locks under `_shared-memory/mesh-locks/`; TTL + heartbeat + peer-aware via sinister-link-state |
| Cross-agent messaging | `_shared-memory/inbox/<slug>/*.json` rows + `sinister-bus` MCP `inbox_poll` | shipped |
| Fleet-update broadcast channel | `automations/fleet-update.ps1` + `_shared-memory/fleet-updates.jsonl` | shipped |
| Sub-agent dispatch within a Claude session | Claude `Task` tool (deferred via ToolSearch) | shipped (Anthropic-native; not Sinister-owned) |
| Heartbeat liveness tracking | `_shared-memory/heartbeats/<slug>.json` | shipped (60s tick fallback when MCP absent) |
| Spawn ledger / PID tracking | `_shared-memory/spawned-windows.jsonl` | shipped |
| Agents page action backend | `automations/agent-actions.ps1` (KillAll / ImmediateClose / SaveAndClose / Pause / Message) | shipped this iter |
| SWARM MODE prompt-side injection | `start-sinister-session.ps1` Build-Phrase line ~1333 | shipped; ONE sentence inviting fan-out via Agent tool or sinister-swarm CLI |
| Loop-mode continuous iteration | `start-sinister-session.ps1` modes.loop branch + loop_condition | shipped (operator-set 2026-05-24T19:55Z) |
| Overseer watch architecture | `projects/sinister-overseer/docs/03-watch-architecture.md` + `09-unified-improvement-engine.md` | shipped (Phase 0 + docs); per-attachment watch loop with cost-cap + tier-routed sensors |
| sinister-swarm CLI (standalone) | `tools/sinister-swarm/` v0.1.0 | shipped; `dm`, `broadcast`, `spawn`, `list`, `watch`, `mark-done`, `wait-for`, `hive-status` |

### 2.2 Coverage matrix (jcode pattern -> Sinister status)

| # | jcode capability | Sinister status | Gap severity |
|---|---|---|---|
| 1 | Coordinator-owned spawn monopoly | partial - operator IS the coordinator at picker time; spawned EVE sessions can also spawn via Task tool (no role enforcement) | LOW (intentional - operator preference) |
| 2 | 13-state lifecycle enum (serde-typed) | absent - states implied by heartbeat freshness + spawned-windows.jsonl `pid` presence | MEDIUM (no `running_stale` / `blocked` distinction) |
| 3 | Server-mediated wire protocol (12 verbs) | absent - file-based comms instead (mesh-locks dir + inbox dir + heartbeats dir + fleet-updates.jsonl) | HIGH (no real-time pub/sub; agents poll dirs) |
| 4 | `comm_spawn` (programmatic) | partial - `start-sinister-session.ps1` is operator-driven; spawning from inside a running session goes through Anthropic Task tool only | MEDIUM |
| 5 | `comm_assign_task` / `comm_assign_next` (plan DAG) | absent - no shared swarm-plan DAG; per-agent plans live in `_shared-memory/plans/<lane>-<topic>/plan.md` | HIGH |
| 6 | `comm_task_control` (start/wake/retry/reassign/replace/salvage) | absent - Pause / Message / KillAll exist in `agent-actions.ps1`; no retry / reassign / salvage primitive | MEDIUM |
| 7 | `comm_await_members` (block until N sessions hit target_status) | absent - sinister-swarm has `wait-for` for single-file marker; no fleet-await | MEDIUM |
| 8 | Topic channels with ChannelIndex pub/sub | partial - `_shared-memory/cross-agent/` topic-dir pattern (e.g. `tt-snap-channel.md`); no membership index, no real pub/sub | MEDIUM |
| 9 | Soft-interrupt notification injection | absent - inbox poll on cold-start + each turn; no in-turn safe-point interleave | HIGH (fleet-updates poll N=3..8 heartbeats, not realtime) |
| 10 | Mandatory completion-report contract (4KB cap, structured) | partial - end-of-turn discipline in `no-bullshit-tested-before-claimed-doctrine` rule 3; no schema, no automatic forward to coordinator | MEDIUM |
| 11 | `comm_status` lock-free snapshot during busy agent | partial - heartbeat JSON has focus + status; no in-turn tool-snapshot | LOW |
| 12 | `comm_summary` (recent tool feed) | absent - PROGRESS files are append-only narrative; no tool-call activity feed | LOW |
| 13 | `comm_read_context` (heavy full-context read) | partial - operator can `cat _shared-memory/resume-points/<slug>/<utc>.json`; not callable from inside another session | LOW |
| 14 | Plan DAG with dependencies + checkpoints | absent - plans are markdown; no DAG, no machine-readable deps | MEDIUM |
| 15 | TUI swarm-graph widget | partial - EVE.exe Agents page shows list; no graph view | LOW |
| 16 | TUI plan-graph widget | absent | LOW |
| 17 | Worktree-manager role + grouping | absent - we use per-agent branches (`agent/<slug>/<topic>`), not worktrees | LOW (different topology) |
| 18 | `SwarmSpawnMode` (Visible/Headless/Auto) | partial - we have visible mintty + `-DryRun` smoke; no Auto-fallback | LOW |
| 19 | Coordinator model override (`swarm_model`) | absent - all spawns share the operator's account/model | MEDIUM (token-cost lever missing) |
| 20 | Optimistic conflict detection via file-touch | absent - we use mesh-coord locks (pessimistic) | LOW (different philosophy; ours is safer) |
| 21 | Per-agent + per-attachment cost-cap enforcement | partial - `claude-usage-meter.ps1` per-attachment; no automatic suspend at 100% per-sub-agent | MEDIUM (Overseer doctrine has it; not enforced yet) |
| 22 | Forced final-assistant-response delivery to coordinator | absent - completion reports live in agent's own PROGRESS file; not pushed to spawner | MEDIUM |

**Verdict in one line:** Sinister has more BREADTH (per-project bot fleet, OAuth-pool, lessons store, contradiction engine, mesh peer-aware locks, Overseer doctrine), jcode has more DEPTH on the swarm-runtime primitives themselves (serde-typed states, structured comms, soft-interrupt notifications, mandatory completion reports, plan DAG).

### 2.3 Where Sinister beats jcode

- **Cross-machine swarm via Sinister LINK** (peer-aware mesh-locks + auto-push). jcode is single-host.
- **OAuth-pivoted Max-quota pooling** (`oauth-pivot-max-quota-pooling-2026-05-24`) - swarm fan-out doesn't multiply per-API-key spend if pool is loaded.
- **Mesh-coord with blast_radius (single/lane/fleet)** + TTL + heartbeat extends - safer than jcode's optimistic no-locks for multi-machine.
- **Overseer doctrine** - meta-agent with token-tier routing, lessons store, contradiction engine, cross-project aggregator. jcode has no equivalent.
- **Bot fleet (13 MCPs)** + token-efficiency analytics - displaces Opus calls with free local Ollama / Haiku for tail/scan/heartbeat work.
- **Per-spawn picker UX** (project + modes + loop_condition) - jcode does not gate spawn through operator question flow.

---

## Phase 3 - gap shortlist (full proposals in companion doc)

See `_shared-memory/knowledge/swarm-improvements-overseer-led-2026-05-25.md` for prioritized expansions. Six gap categories rolled up:

1. **No shared swarm-plan DAG** -> Overseer-led PlanStore + comm_assign_next equivalent.
2. **Spawn-side cost cap unenforced** -> Overseer per-sub-agent budget meter + auto-suspend.
3. **No soft-interrupt notification injection** -> Sinister inbox-tail watcher that injects high-pri rows at next tool boundary.
4. **No mandatory completion-report contract** -> end-of-turn structured-report enforcer in `start-sinister-session.ps1` Build-Phrase.
5. **No serde-typed lifecycle states** -> heartbeat JSON `lifecycle_status` field with same 13-state enum + linter.
6. **No fleet-await primitive** -> `mesh-await-members.ps1` that polls heartbeats for target_status with timeout.

---

## Phase 4 - audit metadata

- Mesh-coord lock acquired at start: `jcode-swarm-audit -Slug sanctum-jcode-swarm-review -TtlSeconds 1800`.
- Token cost of this audit: ~$0.15 cost-eq (Opus reading file source + reasoning). Well inside $0.50 budget.
- Files read: 12 (jcode swarm-core lib.rs + SWARM_ARCHITECTURE.md + wire.rs swarm section + config-types AgentsConfig/FeatureConfig + 6 Sinister files).
- Files written this turn: this doctrine + companion proposals doc + OPERATOR-ACTION-QUEUE row (no code edits).
- No edits to jcode source (read-only as required).
- No edits to Sinister automations (proposals only as required).

## Cross-references

- `_shared-memory/knowledge/jcode-swarm-token-parity-audit-2026-05-23.md` (earlier swarm audit; this updates and expands)
- `_shared-memory/knowledge/jcode-full-feature-audit-2026-05-24.md` (the 30-row feature matrix)
- `_shared-memory/knowledge/parallel-agent-orchestration-pattern-2026-05-21.md`
- `_shared-memory/knowledge/mesh-coordination-and-resource-lifecycle-2026-05-24.md`
- `_shared-memory/knowledge/overseer-unified-improvement-engine-2026-05-24.md`
- `projects/sinister-overseer/docs/03-watch-architecture.md`
- `projects/sinister-overseer/docs/09-unified-improvement-engine.md`
- `automations/start-sinister-session.ps1` (Build-Phrase + Prompt-AgentModes)
- `automations/detect-similar-agents.ps1`
- `automations/mesh-coordinator.ps1`
- `automations/agent-actions.ps1`
- `tools/sinister-swarm/` v0.1.0
