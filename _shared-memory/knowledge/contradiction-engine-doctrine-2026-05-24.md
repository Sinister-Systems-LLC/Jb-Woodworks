<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 365
-->
# Contradiction Engine doctrine (universal "contradict yourself" pattern)

> Operator hard-canonical 2026-05-24 ~21:25Z verbatim: *"i need to expand system i talked about where we contracdict ourself and keep growing and expanding projects"*.
> Reinforced 2026-05-24 ~23:55Z verbatim: *"in the overseer add all things for improving like the contradiction system and like the analyzer you used here ... complie it all into one thing and expand it"*.

## What it binds

Every Sinister Overseer-class agent (P0 today = `sinister-overseer`; future-tier agents that audit + propose fixes inherit) MUST run a proposed fix through the Contradiction Engine BEFORE applying it. The engine is the rule-8 enforcer at fix granularity, complementing `no-bullshit-tested-before-claimed-doctrine-2026-05-23` rule 8 (quality-degradation limits) at the higher granularity of "should we expand THIS iter at all".

## The three counter-argument questions

For every `FixProposal`, ask a cheap-tier (Haiku) model THREE questions:

1. What's the strongest argument THIS FIX IS WRONG?
2. What edge case does this fix miss?
3. What would a hostile reviewer say?

Score 0-10 (higher = more likely WRONG). Verdict:
- 0-3 -> `apply`
- 4-6 -> `hold` (re-reason at medium-tier Sonnet)
- 7-10 -> `rollback` (discard + write lesson)

Default rollback threshold = 6 (only `> 6` rolls back). Lane-tunable via `projects/sinister-overseer/config/improvement-recipe.json` field `contradiction_threshold`.

## The adversarial cycle

Quarterly (every 90 days) OR on operator-explicit-go OR when forever-improve reports DEGRADED >= 3 times on a lane: the Overseer iterates every PAST applied fix and asks medium-tier "has this fix been eroded by subsequent changes? Does new evidence make it wrong in hindsight?" Flagged fixes become `Regression` rows with suggested action `rollback` / `re-reason` / `add-test` / `escalate`. Regressions land in lessons store + operator inbox.

## Cross-project invariant collisions

A fix proposed for lane A may silently violate an invariant of lane B (example: a fix that disables `ANTHROPIC_API_KEY` export contradicts `oauth-pivot-max-quota-pooling-2026-05-24` -- the api-key legacy path is preserved by design). The engine aggregates invariants from every CURRENTLY-ATTACHED lane's adapter and pattern-matches the fix's diff summary + evidence. Any collision forces verdict `escalate` -- always operator-gated, never auto-applied.

## Verdict precedence (most severe wins)

1. `cross_project_conflicts` non-empty -> `escalate`
2. counter-arg score > threshold -> `rollback`
3. counter-arg score in 4..threshold -> `hold` (re-reason at medium)
4. otherwise -> `apply`

## Implementation status

- Code: `projects/sinister-overseer/src/overseer/contradiction.py` (P0 stubs + dataclasses + verdict precedence + module-level smoke).
- Tests: `projects/sinister-overseer/tests/test_sensors.py` `test_contradiction_stubs` -- PASS this turn (score=0 / verdict=`apply` on empty input; threshold edge `should_rollback(6)==False` / `should_rollback(7)==True`).
- Doc: `projects/sinister-overseer/docs/08-contradiction-engine.md`.
- Live wiring (Haiku calls + lessons-store writes + cross-project DSL): P1 + P2 + P3 milestones in `docs/08-contradiction-engine.md` table.

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 8 enforcement at fix granularity)
- `forever-improve-review-doctrine-2026-05-24` (contradiction scores append to `improvement-log.jsonl`)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (adversarial-cycle takes mesh-coord lock on each fix it re-examines)
- `sanctum-scope-discipline-2026-05-24` (cross-project conflicts never silently auto-resolved)
- `overseer-token-efficiency-doctrine-2026-05-24` (cost cap: cheap-tier counter-arg + medium-tier hold + high-tier rare re-propose)
- `fails-to-learn-doctrine-2026-05-24` (every rollback is a lesson row before the next propose)
- `overseer-unified-improvement-engine-2026-05-24` (sibling -- the compilation doc that names the engine's place in the pipeline)

## Anti-patterns

1. Skipping the engine for "obvious" fixes (cost is bounded; engine ALWAYS fires).
2. Letting score 5 silently auto-apply (4-6 = `hold`, never `apply`).
3. Rolling back without writing a lesson row (same bad fix recurs).
4. Treating cross-project conflicts as warnings (`escalate` is full-stop operator-gated).
5. Running adversarial-cycle every iter (quarterly by design; burns cost cap with no signal gain).

## Pass criterion

1. `python -m py_compile projects/sinister-overseer/src/overseer/contradiction.py` parse-clean.
2. `python projects/sinister-overseer/tests/test_sensors.py` reports all tests PASS.
3. Verdict precedence holds in `run_full_contradiction_check`: conflicts > rollback > hold > apply.
4. Every rollback writes a lesson row (P2 wiring; P0 TODO marked at call-site).
5. Engine cost <= 5 percent of per-attachment daily cap.

## Decay metadata

Category: `doctrine` (operator-stated).
Confidence: 1.0.
Half-life: 365 days (operator-canonical doctrine -- stable until operator changes).
Reinforcements: 2 (initial 21:25Z + reinforcement 23:55Z same UTC day).
