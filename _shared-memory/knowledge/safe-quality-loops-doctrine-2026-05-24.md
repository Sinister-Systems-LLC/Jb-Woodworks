<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Safe quality loops doctrine

**Status:** hard-canonical 2026-05-24 (sanctum lane, end-of-/loop iter for spawn-flow stack).
**Operator verbatim 2026-05-24 (~20:08Z):** *"think of the best loops tho that will keep agents working and doing quality needed work. not starting to destory things."*

**Composes with** `quality-monotonic-loop.ps1` (regression+plateau detector — already shipped) + `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 8: 10 quality-degradation signals → STOP expanding, consolidate) + LOOP MODE block in `CLAUDE.md` (continuous-iteration, ≤270s ScheduleWakeup cap).

## What this is
The agent-side counterpart to the launcher's `Build-Phrase` LOOP MODE injection. The launcher tells the child *to* loop; this doctrine tells it *how to loop without destroying things*. Apply to every `loop=on` spawn.

## Loop-condition lifecycle (operator-set stop criterion)
Operator example (2026-05-24, Kernel APK screenshot): *"/loop do not stop testing, auditing, fixing, expanding things until you have created a snapchat account with our methods and apk that was harvested to panel with no issues or flags and added andrewt407 SUCCESSFULLY and that after all that lasted 24 hours"*.

1. **Capture** — launcher prompts `Loop stop condition?` after `Keep loop on?`. Free text. Plumbed via `SINISTER_LOOP_CONDITION` env + Build-Phrase LOOP STOP CONDITION block.
2. **Expand** — child agent's PLAN step turns the brief (could be 3 words) into a fully-specified multi-sentence acceptance criterion: success signals, acceptance evidence, measurable thresholds, what counts as "done" vs "partial". Operator confirms or revises in next utterance.
3. **Check each iter** — every iteration re-reads the expanded criterion; report 1-line progress against it.
4. **Stop cleanly** — when satisfied, STOP and surface verification evidence (the test outputs / measurements that prove it). Empty loop condition → fall back to "queue-empty-or-blocker" default.

## 12 guardrails for the best loops
Each is a precondition for the NEXT iteration. Violation → pause loop, surface to operator, do not auto-resume.

1. **Read-or-measure precondition.** Never act on stale memory. Each iter re-reads the file you are editing OR re-measures the state you are changing. (Fixes the "agent thinks state is X, state is now Y, loop overwrites" failure mode.)
2. **Reversibility wall.** Destructive operations (rm -rf, force-push, drop table, kill process, delete branch) require operator confirmation. Loop NEVER auto-confirms a destructive op. (Composes with canonical-11 reversibility doctrine.)
3. **Quality monotonic.** Quality score must trend ↑ or stay flat. 2-iter regression → `quality-monotonic-loop.ps1` auto-stops. Compose with no-bullshit rule 8 quality-degradation signals (brain rows / PROGRESS size / queue depth / etc.).
4. **Scope freeze.** Loop scope is fixed by the loop-condition at start. Loop NEVER expands its own scope mid-flight without operator approval — the EXPANDED-plan moment is at spawn time, not iter 7.
5. **Cost ceilings.** Per-loop token budget, image-gen ≤ 6 (per Sinister Generator doctrine), API ceilings. Hit ceiling → pause, surface burn-rate row to `OPERATOR-ACTION-QUEUE.md`.
6. **Idempotency check.** Each iter's action either is naturally idempotent OR has a clear "already done" detection before it acts. (Stops the "loop re-creates the file/account/PR each iter" failure mode.)
7. **Diff-before-write.** When editing files, the loop runs a Read first to verify it is not stomping concurrent work. (Sister-agent coordination — see #9.)
8. **Heartbeat liveness.** Loop writes heartbeat per iter. If 3 consecutive heartbeats show the SAME `focus_intent` with no progress → trigger contradict (write counter-arg row, switch approach, or surface block to operator).
9. **Sister-agent coordination.** Re-run `detect-similar-agents.ps1` each iter. If a sister agent starts working on overlapping files/topics → drop a coord note in `_shared-memory/cross-agent/`, carve away to a non-overlapping slice. (Composes with SPAWN-DETECT-SIMILAR doctrine.)
10. **Operator interrupt priority.** Poll operator-utterances tail each iter. New `status=new` utterance addressed to this lane → pause current iter, address utterance, then resume (or accept its mode-flip).
11. **Compaction watchdog.** If session is approaching context limit (90 % threshold), finish current iter, write resume-point, exit cleanly. Do NOT get caught in cold-compact mid-action.
12. **Loop-condition re-check.** Every iter re-reads the loop_condition; if NOW satisfied → STOP and surface verification evidence (do not "just one more iter" past the line — that's how loops turn destructive).

## EXPANDED-plan style (composes with the launcher's PLAN step)
Operator verbatim 2026-05-24 (~19:50Z): *"i want each agent to when its launched to of course have the cresume point but it needs to review past plans and current and create a new expanded plan based on everything it needs to do and expanded on it. like how our contradicting system should work"*.

- READ past plans in `_shared-memory/plans/<lane>-*/plan.md` (archived + open).
- WRITE a new plan that combines: (a) resume-point `open_for_next_iter`, (b) deferred / still-open items from prior plans, (c) operator-utterance rows tagged for this lane, AND (d) at least ONE expansion item that goes BEYOND any earlier plan (contradiction-system style — challenge prior assumptions; surface deeper improvements not previously listed).
- If your new plan disagrees with a prior one, log a counter-arg row in `_shared-memory/counter-arguments.jsonl` so the contradict trail stays intact.

## GOOD loop vs BAD loop quick examples

| Pattern | Why GOOD | Why BAD |
|---|---|---|
| `loop_condition=create snap acct + push to panel + 24h alive after add` | Concrete success signals: file exists, http 200, time-elapsed measurement. Each iter measurable. | (no example — this is a good loop) |
| `loop_condition=make it better forever` | (no example — this is a bad loop) | Zero stop criterion. No measurable signal. Triggers quality-degradation rule 8 by iter 3. |
| `loop_condition=fix bug X, smoke-test, write regression test` | Bounded, measurable, has reversibility. | (no example) |
| `loop_condition=clean up the codebase` | (no example) | Unbounded scope = every iter expands further into refactoring = destroys working code by iter 5. |

## Measurable pass criterion for this doctrine
- Any spawn with `loop_condition` set surfaces the expanded criterion in its first response.
- Quality score trend across loop iters never regresses for 2 iters in a row without a stop or contradict.
- No loop produces a destructive op without operator confirmation. (Track in `_shared-memory/improvement-log.jsonl`.)

Updated: 2026-05-24
