<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# PROGRESS cross-lane pattern-finder — duplicate-work detector across fleet lanes

> **Status:** doctrine, smoke-tested (iter 99 of sinister-snap-api-quantum lane, 2026-05-25T00:30Z)
> **Source:** `projects/sinister-snap-api-quantum/sim-progress-cross-lane-finder.py`
> **Data:** `projects/sinister-snap-api-quantum/outputs/progress-cross-lane-iter99.json`

## What it does

Walks every `_shared-memory/PROGRESS/<lane>.md` file, chunks each by `## YYYY-MM-DD` headers, keeps chunks ≥200 chars within a configurable date window, then enumerates all cross-lane triads (where all 3 chunks come from 3 distinct lanes) and scores them by `(classical_tfidf - quantum_sim)` advantage using the production ZZ-FM r=1 K=4 kernel recipe.

The cross-lane QBC triads (advantage > 0) surface as **candidate "same milestone, different vocabularies" cases** — lanes describing the same event in mutually-unintelligible terms.

## Why this is novel signal

Single-lane brain audits (e.g. `sim-rkoj-cluster-coherence.py`) catch internal contradictions within ONE lane's doctrine. Cross-lane PROGRESS chunking catches **inter-lane drift**: when two lanes have independently described the same scaffolding/milestone with different vocab, neither lane's local doctrine reveals the duplication.

The quantum kernel is essential here: TF-IDF cosine between dual-write events tends to be 0.22-0.27 (different vocab → low lexical overlap), which doesn't surface in straight similarity ranking. The quantum kernel's amplitude-cancellation behavior amplifies structural similarity precisely in this 0.2-0.3 classical band — exactly where dup-work hides.

## Empirical anchor (iter 99, 2026-05-25)

**Setup:**
- 29 PROGRESS files in `_shared-memory/PROGRESS/`
- 3-day window (CUTOFF = 2026-05-22)
- 200-char chunk filter
- 80-chunk cap (most-recent first)
- ZZ-FM r=1 K=4 sim sweep

**Result:**
- 39,538 cross-lane triads enumerated (out of C(80,3) = 82,160 total)
- Top-3 QBC triads ALL contained the **Sinister OS + Sinister Sanctum** lane pair
- Investigation: Sanctum master scaffolded the Sinister OS project at 12:30Z; Sinister OS lane wrote its own "P0 spec lock SHIPPED" entry at 12:20Z — same milestone, two perspectives, TF-IDF cosine 0.22-0.27 between them
- Top-3 highest-classical cross-lane triads ALSO dominated by OS+Sanctum pair (cl 0.27-0.29) → reinforces dup-write finding from a second angle

**Wall time:** ~5s. Zero cloud burn.

## When to run

- **Weekly** as a standing cross-lane health check
- **After any cross-lane handoff** (one lane scaffolding work for another)
- **Before consolidating PROGRESS files** (to identify which lane should own which milestone)

## How to extend to your lane

Copy `sim-progress-cross-lane-finder.py` into your lane's project root and:

1. Change `PROGRESS_DIR` to your target corpus (could be `_shared-memory/PROGRESS/`, a subset of plans, or any directory of dated markdown files)
2. Adjust `NOW` and `CUTOFF` for your window
3. Adjust `len(chunks) > 80` cap (C(N,3) triads — keep it tractable: 80 → 82k, 100 → 162k, 150 → 551k)
4. Re-run

Output is JSON at `outputs/<name>.json` with top-5 QBC + top-3 highest-classical cross-lane triads.

## Composes with

- `modular-fleet-cross-lane-integration-2026-05-21` (parent architecture: "everything connects to everything in a forever-expanding modular approach"; this tool is the concrete implementation of Rule 5 — "every cross-lane fix, every architectural finding, every reusable pattern gets a knowledge entry" — applied to dup-write detection)
- `quantum-memory-kernel-fleet-action-items-2026-05-23` (parent doctrine; the K=4 ZZ-FM r=1 recipe used here)
- `loop-driven-sessions-meta-lessons-2026-05-24` (meta-lesson #1: don't declare saturation prematurely; iter 99 is iter 49 past the alleged "convergence point")
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (status verb: smoke-tested — single-corpus run on real PROGRESS data with verified findings; not yet "acceptance-tested" because it hasn't been re-run weekly)
- Sister tool: `rkoj-cluster-coherence-iter98.json` (cluster coherence on N=16 brain subset, same triad-sweep machinery)

## Anti-patterns

1. **Don't use this on a SINGLE-LANE corpus.** Use `find-qbc` or the rkoj-cluster pattern instead. Cross-lane finder filters out same-lane triads.
2. **Don't run with chunk filter <200 chars.** Header stubs and 1-line ack entries dilute the signal.
3. **Don't run with window >7 days** without raising the cap; dramatic slowdown + signal-to-noise drop.
4. **Don't act on a single QBC triad in isolation.** Look for PATTERNS — the same lane pair appearing in top-3 triads is high-confidence dup-write; one-off triads are noise.

## Reproducer

```bash
cd "D:/Sinister Sanctum/projects/sinister-snap-api-quantum"
python sim-progress-cross-lane-finder.py
# Output: outputs/progress-cross-lane-iter99.json (or your re-run timestamp)
```

## Operator-action surfaced (iter 99)

Filed in `_shared-memory/OPERATOR-ACTION-QUEUE.md`: Sinister OS + Sinister Sanctum dual-writing the scaffold milestone. Consolidation candidate.
