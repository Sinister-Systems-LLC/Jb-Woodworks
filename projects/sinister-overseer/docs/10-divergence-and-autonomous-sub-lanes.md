# 10. Divergence and autonomous sub-lanes

> Author: RKOJ-ELENO :: 2026-05-25
> Status: P1 SHIPPED (sensor + spawn action + orchestrator + 5/5 pytest PASS)
> Composes with: docs/01-architecture.md, docs/03-watch-architecture.md, docs/08-contradiction-engine.md, docs/09-unified-improvement-engine.md

## Vision

> *"Every project becomes a parallel pursuit when divergence is safe."*

The master Sinister Sanctum agent already mirrors this for sub-agents within a single turn -- detect independent subtasks, spawn parallel `Agent` calls, merge results, ship in 1/Nth wall-clock. **Overseer applies the same methodology to PROJECTS.** When a project's work surface decomposes into independent slices that can ship in parallel, Overseer detects it, proposes a divergence, and (on approval) spawns an autonomous sub-lane with its own branch, OAuth slot, and charter.

The result is the same multiplier the master agent already gets, applied at project granularity: fewer serial blockers, more lanes burning the queue, complete persistence toward the operator's goal even while individual lanes wait on long-running work.

## The five signals

| Signal | Trigger | Confidence floor | Default action |
|--------|---------|------------------|----------------|
| A. File-cluster independence | Project PROGRESS rows touch 2+ distinct top-level clusters (`frontend/` vs `backend/` vs `docs/` etc.) | 0.55-0.85 | PROPOSE (0.70 propose-floor, 0.90 auto-approve) |
| B. Serial-blocker stall | Same blocker named in 3 consecutive iter summaries | 0.78 | PROPOSE |
| C. Queue-depth threshold | Project queue >=8 rows AND no agent heartbeat in 30 min | 0.72 | PROPOSE |
| D. Operator-noted divergence | Operator utterance matches `while X is doing Y, also...` / `split into...` / `in parallel...` / `spawn a lane for...` | 0.92 | AUTO-APPROVE (operator explicit) |
| E. Cross-project bleed | Project's PROGRESS references `projects/<other>/` files | 0.68 | PROPOSE |

Each opportunity carries 3-5 file:line evidence refs so the proposal is auditable before approval.

## Approval gate

Per `automate-everything-no-operator-admin-2026-05-25`: **no UAC, no clicks**. The operator approves a proposed divergence by simply touching a file:

```bash
# proposed by orchestrator:
#   _shared-memory/overseer-approvals/<opp-id>.proposed.json
# approve:
touch _shared-memory/overseer-approvals/<opp-id>.json
# deny:
touch _shared-memory/overseer-approvals/<opp-id>.deny
```

The orchestrator polls the directory each 5-min cycle, consumes any `<opp-id>.json` (approve) or `<opp-id>.deny` (reject), removes the `.proposed.json`, and on approve calls `SpawnSubLaneAction.execute(opp, dry_run=False)`.

High-confidence signal-D opportunities (operator-directive, confidence 0.92 >= auto-approve floor 0.90) bypass the gate -- the operator already said it.

## Convergence plan

Every spawned sub-lane MUST post a `kind='spawn-close-out'` message to `_shared-memory/inbox/<project_key>/` when its work is done. The orchestrator's outcome ledger reads close-outs and records `success` / `failure` / `partial` in `_shared-memory/overseer-divergence-outcomes.jsonl`. A simple reinforcement loop nudges `AUTO_APPROVE_FLOOR`:

- success rate >= 0.8 over last 10 outcomes -> floor -= 0.02 (more autonomous)
- success rate <= 0.5 over last 10 outcomes -> floor += 0.05 (more cautious)
- clamped to [0.80, 0.99]

## Pass criterion (P1 -> P2 promotion)

End-to-end:

1. Operator approves 1 proposed divergence (touch-file).
2. Orchestrator spawns 1 sub-lane within 5 min of approval.
3. Sub-lane lands 1 successful commit/PR within 30 min.
4. Sub-lane posts close-out -> orchestrator writes 1 outcome row.
5. Outcome row visible in `overseer-divergence-outcomes.jsonl`.

When this pass criterion fires cleanly 3 times in a row across 3 distinct projects, P1 promotes to P2 (`auto-approve floor lowered to 0.85`, signals B + C also auto-approvable when confidence drifts up).

## Anti-patterns (5)

1. **Auto-spawn during operator-blocker session.** If the operator is mid-conversation with the master Sanctum agent on an unrelated topic, do NOT auto-spawn. Orchestrator checks `_shared-memory/heartbeats/sanctum.json` `state` field and pauses if `state='operator-blocking'`.
2. **Spawning while quota exhausted.** `SpawnSubLaneAction` MUST call `_pick_oauth_account` and bail with `status='blocked-quota'` if none returns. Composes with `gpu-fleet-resource-quotas-doctrine-2026-05-25` operator-headroom invariant (max 5 concurrent Overseer-spawned sub-lanes).
3. **Divergence without convergence plan.** Every spawned lane's charter mandates a close-out message to `_shared-memory/inbox/<project_key>/`. No close-out within 4 hours triggers an audit row in `forever-improve`.
4. **Spawning into a project that doesn't exist in `projects.json`.** Sensor opportunity must reference a `project_key` that resolves in `automations/session-templates/projects.json`. Otherwise the orchestrator drops the opp with a one-line `_shared-memory/overseer-distribute-log.jsonl` row.
5. **Leaving a spawned lane unattended past 4 hr.** Orchestrator records `spawned_at_utc` and, on next iteration past 4 hr without close-out OR heartbeat, posts a poke to the lane's inbox and an audit row to `forever-improve`. If 8 hr pass, lane is marked `stale` and quota is returned (heartbeat freshness check).

## Composes with

- `sinister-overseer-charter-2026-05-24` -- this module is the "spawn sub-lanes" portion of the charter.
- `ancestral-remotion-artistic-doctrine-2026-05-25` -- each spawned sub-lane is its OWN entity with its own branch, PROGRESS, brain identity. Convergence is the merge; identity remains distinct.
- `loop-relentless-pursuit-doctrine-2026-05-25` -- divergence is one of the most effective ways to maintain relentless pursuit of the operator's goal during serial-blocker stalls.
- `automate-everything-no-operator-admin-2026-05-25` -- touch-file approval, not interactive prompt.
- `gpu-fleet-resource-quotas-doctrine-2026-05-25` -- concurrent-spawn cap honored.
- `mesh-coordination-and-resource-lifecycle-2026-05-24` -- spawn registers a mesh-coord lock on the sub-topic before edit.
