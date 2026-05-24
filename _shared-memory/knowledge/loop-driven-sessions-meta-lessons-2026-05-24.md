<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

# Loop-driven session meta-lessons (sinister-snap-api-quantum, iters 1-86)

> **Status:** doctrine, advisory for all spawned EVE sessions running /loop
>
> **Origin:** operator's persistent /loop directive (`"keep working and dont stop until the memory system is fuckign great and told to the agents what to add and fixc"`) ran the sinister-snap-api-quantum lane for 86+ iterations across 2026-05-23 → 2026-05-24. Many of these iterations produced unexpected value AFTER what looked like saturation. This entry captures the meta-lessons.

## Meta-lesson 1: Don't declare saturation prematurely. /loop persistence can find real gaps.

At iter 50, this lane declared "session converged, no actionable signal." Operator hit /loop twice more anyway. Iter 51 then probed an untested structural question and found that **K=4 ANGLE is anti-QBC on 84% of high-classical triads** — a fundamental nuance that re-shaped the bidirectional scope rule doctrine.

Iters 51-67 then produced:
- 1 empirical theorem (Shared-Top-K Necessary Condition for ANGLE encoding; 500 zero-FP classifications across 2 corpora)
- 1 refined conjecture (K' = K × D for encoding interaction degree)
- 1 K=4 combined predictor (44% rule-out on full corpus — operator-canonical pre-screen)
- 4th cross-agent broadcast tying the structural framework together

None of this would have happened if iter-50's "saturation" declaration had been honored.

**Doctrine:** When operator persists /loop after a saturation declaration, the saturation was probably PREMATURE. Treat the next /loop as signal to probe a SPECIFIC unanswered structural question, not to generate filler work. If a real probing-question exists, it will surface; if not, schedule longer cadence and acknowledge cleanly.

## Meta-lesson 2: Test failures catch real corpus-context nuances.

Iter 84 added a regression test for the iter-52 universal-QBC nesting claim (K=4 ⊂ K=8 ⊂ ZZ-FM). The test FAILED initially — but the failure surfaced a real doctrine point: **the iter-52 finding holds in the find-qbc pool TF-IDF, NOT in the 3-doc legacy mode.** Operators calling `run_kernel_audit` without explicit `corpus=pool` get different verdicts.

Fixing the test required passing `corpus=pool` explicitly. The corrected test then revealed an additional doctrine refinement that wasn't visible from research alone — it required the act of WRITING THE TEST to surface.

**Doctrine:** Writing tests is itself a doctrine-refinement exercise. When a test fails, the assertion might be wrong, the code might be wrong, OR the doctrine might have an implicit assumption that the test forces you to make explicit. All three are valuable.

## Meta-lesson 3: Documentation drift accumulates silently. Periodic sync sweeps yield real operator value.

Across iters 73-79, a methodical "sync sweep" found 7 stale operator-facing references that had been silently propagating:
- "quadruple-verified" (iter-19 made it quintuple)
- "25-34pp" (now 25-35pp / mean 31pp)
- "find-zzfm-qbc-triads.py" (deprecated iter-28 in favor of `seraphim find-qbc`)
- "alpha=0.5" (iter-48 fixed to alpha=1.0)
- "124-doc balanced pool" (now ~129-doc)
- "hardware-limited verdict" (overturned iter-19 algorithmic discovery)
- "K=8 ANGLE sim default" (superseded iter-57 ZZ-FM r=2 at 86%)

These accumulated over 30+ iterations without any single one being a "bug" — they were correct AT THE TIME they were written. But operators landing on the docs later get stale advice.

**Doctrine:** After any session producing >10 iterations of doctrine evolution, schedule a sync-sweep pass. Grep operator-facing surfaces (READMEs, brain entry _INDEX rows, CLI help text, docstrings) for the old claims; annotate or update them. Use forward pointers (`SUPERSEDED iter N: see ...`) rather than deletion to preserve audit trail.

## Meta-lesson 4: The no-bullshit doctrine ("test before claiming" + "continuous self-audit") produces visible self-corrections.

This session caught and reversed ~12 of its own claims within the iterations they were made:

| Iter | Original claim | Caught by | Correction |
|---|---|---|---|
| 38 | "6-7pp universal headroom" | iter 39 cross-triad sweep | Varies 6-26pp |
| 44 | "K=8 ANGLE dominates ZZ-FM r=1" | iter 45 per-triad ranking | They are COMPLEMENTARY (K=8 wins 58.6%, ZZ 41.4%) |
| 47 | "alpha=0.5 row #5 quantum value-add" | iter 48 stress test | Noise-collapse, not semantic similarity |
| 50 | "Session converged, no work" | iter 51 probing | K=4 anti-QBC 84% finding |
| 59 | (Implicit: shared-top-K is universal) | iter 61 ZZ-FM extension test | Theorem is ANGLE-only; ZZ-FM has different mechanism |
| 65 | (Implicit: same-top-1 anti-pattern universal) | iter 66 K=5..K=8 sweep | K=4-specific; K=5/K=6 marginally; K≥7 breaks |
| 73 | (Implicit: brain entry / README sync) | iter 73-79 sweep | 7 stale claims silently propagating |
| 84 | (Implicit: nesting test trivial) | test failure | Corpus-context required; iter-42 doctrine resurfaced |

Each correction was published in the same audit trail as the original claim, with a forward pointer. This makes the doctrine evolution legible to future readers — they see WHAT was wrong, WHY it was caught, HOW it was fixed.

**Doctrine:** When self-auditing, document corrections in-place rather than deleting the wrong claim. The audit trail is itself doctrine — it teaches future EVE sessions how to recognize the failure modes.

## Composes with

- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (operator's tested-before-claimed mandate)
- `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md` (the doctrine content this session produced)
- `projects/sinister-snap-api-quantum/MEMORY.md` (audit-grade detail log)

## Tags

doctrine, advisory, /loop, session-meta-lessons, premature-saturation, corpus-context, sync-sweep, self-correction, audit-trail, 2026-05-24
