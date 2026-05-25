<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 08 :: Contradiction Engine

> Sibling docs: `01-architecture.md`, `03-watch-architecture.md`, `05-fails-to-learn.md`, `09-unified-improvement-engine.md`.
> Module: `src/overseer/contradiction.py` (P0 stubs; P2 live).
> Brain doctrine: `_shared-memory/knowledge/contradiction-engine-doctrine-2026-05-24.md`.

## Why this exists

Operator hard-canonical 2026-05-24 ~21:25Z verbatim:

> "i need to expand system i talked about where we contracdict ourself and keep growing and expanding projects"

Reinforced 2026-05-24 ~23:55Z (post token-analytics ship) verbatim:

> "in the overseer add all things for improving like the contradiction system and like the analyzer you used here ... complie it all into one thing and expand it"

The Overseer's job is to surface weak spots and propose fixes. A fix proposed in a single forward pass is by definition incomplete -- the agent that wrote it had no opposing view in the room. The Contradiction Engine puts the opposing view in the room before the fix lands. Every fix must survive its own counter-argument OR get held / rolled back.

This composes with `no-bullshit-tested-before-claimed-doctrine-2026-05-23` rule 8 (quality-degradation limits expansion). The Contradiction Engine is the rule-8 enforcer at fix granularity: if a fix's counter-argument score is high, the fix is held BEFORE we accumulate downstream technical debt from a wrong fix.

## The three counter-argument questions

For every `FixProposal` the Overseer wants to apply, the Contradiction Engine asks a cheap-tier (Haiku-4.5) model THREE questions:

1. **What is the strongest argument THIS FIX IS WRONG?** (forces the model to argue against the fix on the fix's own terms)
2. **What edge case does this fix miss?** (forces enumeration of states the proposer didn't consider)
3. **What would a hostile reviewer say?** (forces an adversarial frame)

The model returns a JSON object with a 0-10 `score` and an `arguments` list. Score semantics:

| Score band | Meaning | Default action |
|---|---|---|
| 0-3 | No credible counter | `apply` (proceed to gate) |
| 4-6 | Plausible counter; worth a second look | `hold` -- re-reason at medium tier (Sonnet) |
| 7-10 | Strong counter; fix is likely wrong | `rollback` -- discard + push to lessons store |

The threshold for rollback is governed by `should_rollback(score, threshold=6)`. Threshold is per-lane tunable via `config/improvement-recipe.json` (default 6 fleet-wide).

## When the engine fires

| Trigger | Cadence | Function entry-point |
|---|---|---|
| Every proposed fix, BEFORE the apply gate | per-fix (synchronous in the watch loop) | `run_full_contradiction_check(fix, all_lanes, threshold)` |
| Quarterly adversarial sweep over PAST applied fixes | every 90 days (configurable) | `adversarial_cycle(past_fixes)` |
| Operator-triggered adversarial-now | on demand via CLI | `overseer adversarial-now` (P2) |
| Forever-improve DEGRADED score in a lane >= 3 times | event-driven (via `ForeverImproveSensor`) | `adversarial_cycle(past_fixes_for_lane)` |
| Cross-project invariant check | per-fix (synchronous) | `cross_project_invariant_check(fix, all_lanes)` |

## The adversarial cycle

The standing watch loop catches what's wrong with the CURRENT system as it changes. The adversarial cycle catches what has been silently eroded over time. Quarterly (or on demand) the Overseer iterates every fix it has ever successfully applied and asks the medium-tier model:

> "Given the current state of the target lane, has this fix been eroded or contradicted by subsequent changes? Does any new evidence make this fix wrong in hindsight?"

Any fix flagged becomes a `Regression` row with a suggested action (`rollback` / `re-reason` / `add-test` / `escalate`). Regressions are surfaced to the operator inbox AND written into the lessons store so future similar fixes consult them.

## Cross-project invariant collisions

When the Overseer is attached to N lanes, a fix proposed for lane A may silently violate an invariant of lane B. Example: a fix that disables `ANTHROPIC_API_KEY` export across the spawn pipeline must NOT contradict `oauth-pivot-max-quota-pooling-2026-05-24` (the api-key legacy path is preserved by design). `cross_project_invariant_check` aggregates invariants from every attached lane's adapter and pattern-matches the fix's diff summary + evidence against each invariant. Any collision yields a `Conflict` row and forces verdict `escalate` (always operator-gated, never auto-applied).

## Composition rules

| Composes with | How |
|---|---|
| `no-bullshit-tested-before-claimed-doctrine-2026-05-23` rule 8 | rollbacks ARE the rule-8 enforcement at fix granularity |
| `forever-improve-review-doctrine-2026-05-24` | contradiction scores piped into improvement-log.jsonl |
| `mesh-coordination-and-resource-lifecycle-2026-05-24` | adversarial-cycle takes a mesh-coord lock on each fix it re-examines |
| `sanctum-scope-discipline-2026-05-24` | cross-project conflicts always route to operator; never silently auto-resolved |
| `docs/02-token-efficiency.md` | counter-argument is cheap-tier; adversarial-cycle is medium-tier; re-propose-after-rollback is high-tier; cost cap enforced |
| `docs/05-fails-to-learn.md` | every rollback is a lesson row, written before the next fix is proposed |

## Pass criterion

1. `python -m py_compile src/overseer/contradiction.py` parse-clean.
2. `python tests/test_sensors.py` passes the `test_contradiction_stubs` case (score=0, verdict=`apply` on empty input; `should_rollback(7)==True` / `should_rollback(5)==False` / `should_rollback(6)==False`).
3. `run_full_contradiction_check` precedence-resolves correctly: conflicts > rollback > hold > apply.
4. Every rollback writes a lesson row to `lessons.db` (P2; P0 has the call-site marked TODO).
5. Cost cap honored: contradiction-engine consumes <= 5 percent of per-attachment daily cost-eq.

## P0 -> P2 implementation milestones

| Phase | Deliverable | Done when |
|---|---|---|
| P0 (this iter) | Stubs + dataclasses + verdict precedence + smoke tests | All four pass criteria items 1-3 verified this turn |
| P1 | Wire to OAuth-pooled cheap-tier client | `score_counter_argument` returns live 0-10 from Haiku |
| P2 | adversarial_cycle live + lessons store write-back | Quarterly cron registered + lessons rows visible in `lessons.db` |
| P3 | Cross-project invariant DSL + adapter-declared invariants | Each adapter ships an `INVARIANTS = [...]` list; cross-check matches by pattern |

## Anti-patterns (named for the record)

1. **Skipping the engine for "obvious" fixes.** The watch loop never bypasses the engine; the cost is bounded by design.
2. **Letting score 5 silently auto-apply.** Score 4-6 means `hold` + re-reason; never auto-apply.
3. **Rolling back without writing a lesson.** Every rollback is a lesson row; otherwise we re-propose the same bad fix.
4. **Treating cross-project conflicts as warnings.** They are `escalate`; operator-gated, full stop.
5. **Running adversarial-cycle on every iter.** It's quarterly by design; running it every iter burns the cost cap with no signal gain.
