<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# Overseer autonomous divergence doctrine (2026-05-25)

> Author: RKOJ-ELENO :: 2026-05-25
> Status: SHIPPED (P1; orchestrator scan-only smoke green)
> Lane: sinister-overseer (delegates to project-owner lanes on spawn)

## Operator verbatim (2026-05-25 ~07:30Z)

> *"i want you to take this same methodology and use it in the sinsiter overseer and how it functions to realeasiuze whwen areas of projects can diverge on their own path to allow fo maximum efficenecy and complete persistence towards the goal."*

## What this doctrine binds

Every Overseer process and any future fleet code that proposes spawning a NEW autonomous sub-lane MUST:

1. Use the `DivergenceSensor` at `projects/sinister-overseer/src/overseer/sensors/divergence.py` (or a successor that emits the same `DivergenceOpportunity` dataclass).
2. Pass the opportunity through `SpawnSubLaneAction.execute(opp, dry_run=...)` (or successor) so the OAuth-pick / quota check / heartbeat verify / spawn-log row are all enforced.
3. Honor the touch-file approval gate (NOT an interactive prompt).
4. On lane completion, append outcome row to `_shared-memory/overseer-divergence-outcomes.jsonl`.

## Methodology mirrored from the master Sanctum agent

The master Sanctum agent's "swarm pattern":

1. Has a primary goal (operator directive).
2. Detects when subtasks are INDEPENDENT (no shared mutable state, no ordering dependency).
3. Spawns parallel sub-agents via the `Agent` tool with isolated prompts.
4. Each sub-agent commits to the same branch; master orchestrates merge + push.
5. Result: 5x throughput vs serial execution.

**Overseer applies this at the PROJECT level instead of the turn level.** Where master Sanctum identifies sub-tasks within a single response, Overseer identifies project-areas that can fork into their own concurrent lane. Same independence test (no shared mutable file, no blocking serial dependency); same isolated-prompt charter; same merge-or-converge convention (close-out message to project inbox).

## The five signals

(Full table + thresholds: `projects/sinister-overseer/docs/10-divergence-and-autonomous-sub-lanes.md`.)

| Signal | Default confidence | Default route |
|--------|--------------------|---------------|
| A. File-cluster independence | 0.55-0.85 | PROPOSE |
| B. Serial-blocker stall | 0.78 | PROPOSE |
| C. Queue-depth threshold | 0.72 | PROPOSE |
| D. Operator-noted divergence | 0.92 | AUTO-APPROVE (>= 0.90 floor) |
| E. Cross-project bleed | 0.68 | PROPOSE (just clears propose floor) |

## Approval gate (no clicks, no UAC)

`_shared-memory/overseer-approvals/<opp-id>.proposed.json` lands when a propose-floor-qualifying opportunity is detected. Operator just touches `<opp-id>.json` to approve or `<opp-id>.deny` to reject; orchestrator polls every 5 min and acts. This composes with `automate-everything-no-operator-admin-2026-05-25` (operator is END USER, not sysadmin).

## Five anti-patterns (also in docs/10)

1. Auto-spawn during operator-blocker session.
2. Spawning while OAuth quota exhausted (`SpawnSubLaneAction` returns `status='blocked-quota'`).
3. Divergence without a convergence plan (close-out message mandatory).
4. Spawning into a project that doesn't exist in `projects.json`.
5. Leaving a spawned lane unattended past 4 hr (poke at 4 hr, mark stale at 8 hr, return quota).

## Pass criterion

1 operator-approved divergence -> 1 spawned lane -> 1 successful PR/commit within 30 min -> 1 documented learning row in `_shared-memory/overseer-divergence-outcomes.jsonl`.

3 consecutive pass-criterion-clean runs across 3 distinct projects promote P1 -> P2 (auto-approve floor lowered from 0.90 -> 0.85; signals B + C eligible for auto-approve when their confidence rises).

## Composes with

- `sinister-overseer-charter-2026-05-24` -- divergence is a named module in the charter's apply path.
- `ancestral-remotion-artistic-doctrine-2026-05-25` -- spawned sub-lanes are their own entities (own branch, identity, PROGRESS file); convergence preserves identity.
- `loop-relentless-pursuit-doctrine-2026-05-25` -- divergence is a primary tool to maintain relentless pursuit during serial-blocker stalls (signal B).
- `automate-everything-no-operator-admin-2026-05-25` -- touch-file approval not interactive prompt.
- `gpu-fleet-resource-quotas-doctrine-2026-05-25` -- concurrent-spawn cap (5) is enforced in `SpawnSubLaneAction._count_live_spawns`.
- `single-repo-push-policy-2026-05-25` -- spawned sub-lanes inherit the parent project's push policy (default Sinister-Sanctum; LetsText/Showmasters/JB-Woodworks carve-outs preserved).
- `mesh-coordination-and-resource-lifecycle-2026-05-24` -- sub-lane charter mandates mesh-coord Check/Register/Release before risky edits.

## Pointers

- Sensor: `D:/Sinister Sanctum/projects/sinister-overseer/src/overseer/sensors/divergence.py`
- Action: `D:/Sinister Sanctum/projects/sinister-overseer/src/overseer/actions/spawn_sub_lane.py`
- Orchestrator: `D:/Sinister Sanctum/projects/sinister-overseer/src/overseer/orchestrator.py`
- Tests: `D:/Sinister Sanctum/projects/sinister-overseer/tests/test_divergence.py` (5/5 PASS)
- Project doc: `D:/Sinister Sanctum/projects/sinister-overseer/docs/10-divergence-and-autonomous-sub-lanes.md`
