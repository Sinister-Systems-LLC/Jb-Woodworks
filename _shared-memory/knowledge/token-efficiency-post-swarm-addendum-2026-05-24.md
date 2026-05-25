<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Token-efficiency :: post-swarm operational addendum (2026-05-24T18:25Z)

> **Parent:** `jcode-swarm-token-parity-audit-2026-05-23` (the canonical token-efficiency reference; this is an operational re-measurement after the 2026-05-24 5x-parallel ships).
> **Trigger:** operator (16:08:32Z verbatim): *"make sure we remain uber token efficent wihtout loosing any power"* — paired with 16:05:32Z about Docker auto-open + GitHub push. Also closes plan §3.E from `test-modes-completion-plan-2026-05-24/plan.md`.
> **Status:** addendum (not a new doctrine; supersedes §3 of the parent audit for spawn-flow specifically).

## What changed in the spawn flow since the parent audit

Six 2026-05-24 ships touched the per-spawn token surface:

| Change | Impact on cold-start phrase | Net tokens (estimate) |
|---|---|---|
| `Get-ResumeContextInject` (prior, ~iter 6 of /loop) | adds `focus_intent`, `last_5_files`, `pre_warm_reads` inline | +60 to +180 |
| `Get-MemoryRecallInject` (sub-area A, this swarm 18:00Z) | adds `MEMORY_RECALL=[k] v(80c) \| ...` | +120 to +260 (top-3 hits × 80c + overhead) |
| `Prompt-AgentModes` in headless path (sub-area D-ext, this swarm 18:05Z) | adds `SWARM MODE on:` / `LOOP MODE on:` lines IF operator picks those modes | +80 to +160 (conditional) |
| `Build-Phrase` bot-fleet-quickref pointer (prior) | adds `Before reaching for Opus on routine work...` reminder | +50 |
| Resume context "UNREAD_OPERATOR_UTTERANCES=N" notice (prior) | adds 1 short clause | +12 |
| Slug + project metadata (always-on) | unchanged | baseline ~280 |

**Per-spawn phrase total now:** ~700-1000 tokens (was ~280 pre-2026-05-24). **Net delta: +420 to +720 tokens per spawn.**

## Cost framing

| Spawns per day (operator + agents) | Phrase-only token cost @ Sonnet 4.6 ($3/MTok input) | Cost added per day |
|---|---|---|
| 10 | 7-10K tokens | $0.02-$0.03 |
| 50 | 35-50K tokens | $0.10-$0.15 |
| 200 | 140-200K tokens | $0.42-$0.60 |

**Worst case for the operator's "uber token efficient" target:** spawn-phrase cost stays under $0.60/day even at 200 spawns. That's well inside operator's burn budget. **No catastrophic regression.** But the +420-720 token delta is real and there are concrete cuts available.

## Concrete cuts not yet made (ROI-ordered)

### Cut 1 — De-duplicate `Build-Phrase` "before reaching for Opus" reminder when already in resume-inject

**Symptom:** the `bot-fleet-quick-reference.md` pointer is appended UNCONDITIONALLY at the end of `Build-Phrase` (line ~967 in `automations/start-sinister-session.ps1`). For resume spawns it composes with the resume-context's own "you have prior knowledge" implication.

**Fix:** check if `$resumeInject` was non-empty; if so, skip the bot-fleet appendage (it's only useful for FRESH spawns / general mode).

**Saves:** ~50 tokens per resume spawn × N spawns/day = noticeable.

**Estimate:** 5-minute edit. Sub-area for a future iter.

### Cut 2 — Compress `MEMORY_RECALL` tag list under 80 chars

**Symptom:** `Get-MemoryRecallInject` currently concatenates up to 8 unique tags (line `query = (@($tagSet) | Select-Object -First 8) -join ' '`). For a hot lane with diverse utterance tags the query string can be 100-150 chars before any hits. Tag itself takes phrase budget without adding signal (forge-memory recall is TF-IDF; 4-5 tags is near optimal).

**Fix:** drop `First 8` → `First 5`. Cap query string at 80 chars max.

**Saves:** ~50-80 tokens per spawn × N = decent.

**Estimate:** 2-minute edit. Same file as sub-area A; ideally batched with Cut 1.

### Cut 3 — Drop verbose `MEMORY_RECALL` header when hits are empty

**Symptom:** when forge-memory returns 0 hits (lane has no relevant memories yet), `Get-MemoryRecallInject` returns `''` (correct). But when it returns hits with low recall_score (< 0.1), the noise dominates signal. Current code shows all top-3 hits regardless of score.

**Fix:** filter `_recall_score >= 0.1` (current verified hits have score=0 because the test memories are sparse; real production memories will have meaningful scores). When 0 hits clear threshold, suppress the entire `MEMORY_RECALL` block instead of injecting noise.

**Saves:** ~150-200 tokens per spawn when memory lookup yields only weak hits. **Highest-value cut** because it preserves signal-to-noise.

**Estimate:** 5-minute edit. Same file as Cuts 1-2.

### Cut 4 — Move bot-fleet quickref pointer into a once-per-cold-start system reminder (not the phrase)

**Symptom:** every spawn phrase re-states the bot-fleet pointer. The CHILD Claude sees it once in turn-0 and either follows it or doesn't; re-stating in turn-1 / turn-2 spawns gives diminishing returns.

**Fix:** make the bot-fleet pointer a once-per-COLD-START injection (first spawn of the day or first spawn in this CLI session), not every spawn. Track via `_shared-memory/script-runs/last-bot-fleet-pointer-injection.txt`.

**Saves:** ~50 tokens × (N spawns - 1) spawns per day = 250-9000 tokens/day.

**Estimate:** 15-minute edit + test. Medium ROI; defer until cuts 1-3 land.

### Cut 5 — Profile and tune the `Get-ResumeContextInject` field selection

**Symptom:** `Get-ResumeContextInject` includes `focus_intent` + `prior_iter_shipped` + `open_next` + `pre_warm_reads`. The `pre_warm_reads` field is intermediate (paths) and the child Claude reads them via `Read` tool anyway. Token-wise it pre-pays for cache hits.

**Recommendation:** measure cache hit rate (operator-observable via Claude Code metrics) on `pre_warm_reads` paths. If <60% hit, the upfront cost outweighs the cache benefit and we can drop the field.

**Estimate:** 30-min measurement + decision. Lowest-ROI cut; gather data first.

## Already-good behaviors (don't regress)

- **`Get-MemoryRecallInject` has 5s wall-clock timeout** — prevents pathological forge-memory latency from blocking spawn.
- **All injects gated by env-var killswitches** — `SINISTER_SKIP_MEMORY_RECALL` / `SINISTER_SKIP_MODES_PROMPT` / `SINISTER_SKIP_TRUST_BLOCK`. Task Scheduler / cron can bypass cleanly.
- **`Build-Phrase` is bounded** by tail-truncation rules — no infinite-length phrase even if utterances JSONL grows.
- **Spawn .sh heredoc is fixed-size** — no per-spawn growth.

## Operator-visible "power" preserved

Operator's anti-constraint: *"without losing any power"*. Checks:

| Power vector | Preserved? | Evidence |
|---|---|---|
| Memory recall in context | YES | Cuts 2-3 tighten the budget but DON'T remove the feature; killswitch still allows full opt-out |
| Per-spawn swarm/loop ask | YES | D-ext fix is orthogonal to token cuts |
| Resume from prior session | YES | `Get-ResumeContextInject` is the durable channel; Cut 5 is measurement-gated |
| Multi-account burn-first | YES | Operates outside phrase; no token interaction |

**Net:** Cuts 1-3 are pure wins (lower tokens, identical power). Cut 4 trades a small frequency penalty for sustained savings. Cut 5 is research-mode only.

## Recommendation order for next 3 lane-turns

1. **Iter A (15 min):** batch Cuts 1+2+3 into one edit to `start-sinister-session.ps1` (`Build-Phrase` + `Get-MemoryRecallInject`). Smoke-test phrase length before vs after.
2. **Iter B (20 min):** Cut 4 (once-per-cold-start bot-fleet pointer). Independent file; can run in parallel with A.
3. **Iter C (30 min):** Cut 5 measurement pass — instrument `Build-Phrase` to log the per-spawn phrase length, then dashboard 7 days of data.

## Composes with

- `jcode-swarm-token-parity-audit-2026-05-23` — parent doctrine; §3 supersession noted
- `bot-fleet-quick-reference.md` — the 13-bot catalog this addendum recommends keeping but not re-stating per-spawn
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — every estimate above is a hypothesis, NOT a smoke-tested claim; the post-cut numbers must be verified
- `_shared-memory/plans/test-modes-completion-plan-2026-05-24/plan.md` — closes §3.E
- `forever-improve-review-doctrine-2026-05-24` — this addendum IS the forever-improve REVIEW pass for the spawn-flow ships

## Halt-check

This is the second new doctrine added today (the consolidated-status doc was the first). Brain rows ~163 → 164 with this. **Threshold is 150 soft.** Next iter MUST be consolidation (merge / archive small fragments) or non-doctrine work (code edits + verification only). No more new doctrine until cuts 1-3 land + measurements.
