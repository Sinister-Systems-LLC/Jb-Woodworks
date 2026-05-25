<!-- Author: RKOJ-ELENO :: 2026-05-25 -->

<!-- decay:
  category: proposal
  confidence: 0.85
  reinforcements: 0
  half_life_days: 90
-->
# Overseer-led swarm expansions (10 ranked proposals)

**Slug:** swarm-improvements-overseer-led-2026-05-25
**First discovered:** 2026-05-25 ~02:25Z by Sinister Sanctum (EVE) lane `sanctum-jcode-swarm-review`
**Status:** proposal (operator-approval pending; top-3 routed to queue)
**Tags:** proposal, overseer, swarm, expansion, jcode-parity, p1-candidates, 2026-05-25
**Sources:** `jcode-swarm-reverse-engineering-2026-05-25.md` (gap matrix), `overseer-unified-improvement-engine-2026-05-24.md`, `mesh-coordination-and-resource-lifecycle-2026-05-24.md`, `oauth-pivot-max-quota-pooling-2026-05-24.md`

---

## Scoring rubric

| Field | Meaning |
|---|---|
| Why ship | Operator value in one sentence |
| Cost-eq / day | Token burn from the Overseer's $5/day cap (Haiku-cheap / Sonnet-medium / Opus-rare) |
| Files touched | Approx Sinister files modified |
| Risk tier | TRIVIAL / LOW / MEDIUM / HIGH per `docs/03-watch-architecture.md` apply-gate table |
| Priority | P1 = next-iter ship; P2 = follow-up; P3 = stretch |

---

## P1 - top 3 (routed to OPERATOR-ACTION-QUEUE for approval)

### P1.1 - Overseer SubAgentBudgetMeter (per-sub-agent cost cap + auto-suspend)

**Why ship.** Today a single SWARM-MODE session can fan out to 5 sub-agents via Claude `Task` tool. None of them respect a per-sub-agent budget; they all bill against the shared OAuth pool. Operator has no visibility into "this swarm just ate $2 in 4 minutes". This is the highest-value low-risk add.

**Spec.**
- New sensor `SubAgentBudgetSensor` in `projects/sinister-overseer/src/overseer/sensors/`.
- Polls `_shared-memory/spawned-windows.jsonl` + `automations/claude-usage-meter.ps1 -Mode Json` every 60s.
- For each spawn whose `parent_session_id` matches a tracked coordinator, accumulates cost; at 80% of per-sub-agent cap ($0.50 default) emits `SubAgentBudgetWarn`; at 100% emits `SubAgentBudgetSuspend`.
- ApplyGate on Suspend = call `automations/agent-actions.ps1 -Action SaveAndClose -Slug <slug>` (LOW risk - already-shipped backend).
- Emits operator-inbox row at suspend with last-3-turns summary.

**Cost-eq / day.** Sensor is subprocess (0 LLM). Detector tier: cheap (Haiku) only on emit (~5-10 events / day). ~$0.02 / day per attached lane.

**Files touched.** 2 new files + 1 config row. Risk tier: LOW (auto-applies SaveAndClose only; that's reversible via resume-point). Priority: **P1**.

### P1.2 - Overseer NotificationInjector (soft-interrupt via inbox-tail watcher)

**Why ship.** jcode's killer feature: inter-agent messages interleave INTO a running turn without a new round-trip. Sinister today polls `inbox/<slug>/` on cold-start + every Nth heartbeat (3-8). HIGH-priority operator interrupts can sit unread for minutes mid-turn.

**Spec.**
- New module `projects/sinister-overseer/src/overseer/notification_injector.py`.
- Watches `_shared-memory/inbox/<slug>/` + `_shared-memory/fleet-updates.jsonl` for rows tagged `priority=high`.
- Maintains per-slug "pending-inject" buffer.
- Sinister side: add a 1-line shim to `start-sinister-session.ps1` Build-Phrase: *"Check `_shared-memory/inbox/<slug>/.inject-pending` after every tool result; if present, read top row, address, then delete."*
- Overseer writes `.inject-pending` marker file when a HIGH row lands; agent reads on next tool boundary (NO new turn required).

**Cost-eq / day.** Watcher is filesystem poll (0 LLM). Linter on agent compliance via cheap-tier classifier on weekly digest (~$0.01 / week).

**Files touched.** 1 new file + 1 line in start-sinister-session.ps1 Build-Phrase. Risk tier: LOW (read-only marker; no auto-modify of agent state). Priority: **P1**.

### P1.3 - SharedSwarmPlanStore (DAG with deps + checkpoints; coordinator-managed)

**Why ship.** jcode's `comm_assign_next` works because there is ONE shared plan DAG. Sinister has per-lane plans only; the master Sanctum agent can't say "give the next runnable task to whichever sibling is idle". This blocks every multi-lane refactor from being parallelizable.

**Spec.**
- New file format `_shared-memory/swarm-plans/<swarm-id>/plan.json` with shape:
  `{ "swarm_id": str, "owner_slug": str, "items": [{"id", "content", "status", "deps": [ids], "assigned_to": slug|null, "checkpoint_utc": iso|null }] }`.
- New script `automations/swarm-plan.ps1` with actions: `Create`, `List`, `Assign`, `AssignNext`, `Complete`, `Status`.
- Overseer adds `PlanProgressSensor` that watches plan files, emits `PlanStallEvent` when an item has been `running` >30 min with no checkpoint.
- Triage tier proposes reassign / replace / salvage.

**Cost-eq / day.** Sensor subprocess only. Triage cheap-tier on stall events (~2-5 / day). ~$0.05 / day.

**Files touched.** 1 new script + 1 new sensor + 1 new directory contract. Risk tier: LOW (additive; no existing file mutated). Priority: **P1**.

---

## P2 - next-tier ships

### P2.1 - LifecycleStatus enum + heartbeat schema bump

Adopt jcode's 13-state enum (`spawned/ready/running/running_stale/completed/done/failed/stopped/crashed/queued/blocked/pending/todo`). Add `lifecycle_status` field to heartbeat JSON; backfill `_shared-memory/heartbeats/*.json` writers (~6 scripts). Overseer adds `LifecycleAuditSensor` that flags `running` heartbeats older than 30 min as `running_stale`. Cost: $0.01/day. Risk: LOW (additive field). Files: 6 writers + 1 sensor + heartbeat schema doc.

### P2.2 - MeshAwaitMembers primitive

`automations/mesh-await-members.ps1 -Slugs <list> -TargetStatus completed,stopped -TimeoutSec 3600 -Mode all|any`. Polls heartbeats every 10s; returns exit code 0 on hit, 1 on timeout, 2 on bad args. Lets a coordinator agent block until N siblings finish before merging results. Cost: 0 (subprocess). Risk: TRIVIAL (read-only). Files: 1 new script + doc.

### P2.3 - StructuredCompletionReport enforcer

Adopt jcode's 4KB-cap structured-report contract. Add `_end-of-turn-template.md` snippet to Build-Phrase reminding agents to write `_shared-memory/completion-reports/<slug>/<utc>.json` with `{message, validation, follow_up}` keys when `loop=on` ends a meaningful unit. Overseer's `CompletionReportSensor` emits `ReportMissingEvent` when a meaningful-unit boundary fires with no report. Triage proposes the report retroactively for the operator. Cost: cheap-tier ~$0.02/day. Risk: LOW (template only). Files: 1 sensor + 1 line in Build-Phrase + 1 template doc.

### P2.4 - Sub-agent role specialization (researcher / coder / verifier)

Three named role profiles for the picker: when SWARM=on, child can spawn typed sub-agents with role-pinned prompt headers + restricted tool-allowlist. researcher = read-only (Grep/Read/WebFetch); coder = read+edit; verifier = read+exec test commands. Reduces blast radius per sub-agent. Cost: 0 (prompt-shape only). Risk: LOW. Files: 1 new module in start-sinister-session.ps1 + 3 role-prompt templates.

---

## P3 - stretch

### P3.1 - TopicChannel pub/sub with membership index

File-based channels in `_shared-memory/channels/<channel>/` with `members.json` index. Replaces ad-hoc `_shared-memory/cross-agent/*.md` topic-dirs. Cost: 0. Risk: LOW. Files: 1 new script + migration of 3 existing topic-dirs.

### P3.2 - EVE.exe swarm-graph widget

ASCII swarm-graph in EVE.exe Agents page sub-tab: shows coordinator -> sub-agents tree with status + last-tool. Uses `spawned-windows.jsonl` parent_session_id linkage. Cost: 0. Risk: LOW (read-only UI). Files: 1 sub-page in eve.py + AutoRebuild step.

### P3.3 - Coordinator model override (cheaper-model fan-out)

`AgentsConfig.swarm_model` equivalent: per-spawn picker question "for swarm sub-agents, use which model? [Opus / Sonnet / Haiku]". Coordinator stays Opus; fan-out workers downshift. Cost: SAVES $1-3/day on heavy swarm sessions. Risk: LOW (operator-chosen). Files: 1 picker question + 1 env var in Build-Phrase + per-account model-pin in claude-accounts.ps1.

### P3.4 - Auto-fanout heuristic on prompt complexity

When the initial prompt LOC > X OR cites N+ files OR has K+ deliverables, suggest "swarm=on (auto-detected)". Cost: cheap-tier classifier on prompt at spawn (~$0.005/spawn). Risk: TRIVIAL (suggestion only; operator still picks). Files: 1 classifier in Build-Phrase + 1 prompt-template.

---

## Top-3 ranked summary (for OPERATOR-ACTION-QUEUE)

| Rank | Proposal | Cost/day | Risk | Why now |
|---|---|---|---|---|
| 1 | P1.1 SubAgentBudgetMeter | $0.02 | LOW | Highest visible-value: caps the "swarm just spent $5 in 4 min" failure mode jcode prevents |
| 2 | P1.2 NotificationInjector | $0.01 | LOW | Closes biggest UX gap vs jcode: HIGH-pri operator interrupts during long swarm turns |
| 3 | P1.3 SharedSwarmPlanStore | $0.05 | LOW | Unlocks `comm_assign_next` style multi-lane parallel refactors; foundation for P2.2 await-members |

Total burn for all 3 ~ $0.08 / day; well under the per-attachment $5 cap and the Overseer-fleet daily budget.

## Pass criteria (per proposal)

Each P1 ships only when:
1. Spec doc written under `projects/sinister-overseer/docs/`.
2. Smoke test for the new sensor / script (PASS evidence in commit message).
3. Mesh-coord lock acquired before any shared-file edit.
4. Reversibility plan declared (per `docs/03-watch-architecture.md` apply-gate rules).
5. Lessons-store row written on outcome (win or loss).
6. End-of-turn separates `Shipped (verified)` from `Scaffolded (unverified)` per no-bullshit rule 3.

## Composes with

- `_shared-memory/knowledge/jcode-swarm-reverse-engineering-2026-05-25.md` (source gap matrix)
- `_shared-memory/knowledge/overseer-unified-improvement-engine-2026-05-24.md` (engine pipeline)
- `_shared-memory/knowledge/oauth-pivot-max-quota-pooling-2026-05-24.md` (cost-pool basis)
- `_shared-memory/knowledge/mesh-coordination-and-resource-lifecycle-2026-05-24.md` (lock primitive)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (ship-criteria)
