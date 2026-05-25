# Quantum-Fleet 100× Master Plan — 2026-05-25

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: sinister-snap-api-quantum (incubation) → sanctum-lane (rollout)
> Operator (verbatim 2026-05-25 ~01:28Z): *"create a master plan to take all the knowledge we have gained and create a plan of how you are going to 100x our memory power, token efficiency and overall just sheer power with only increase things and breaking nothing. do what you need to do"*

## TL;DR — the compounded 100× thesis

100× is a compound, not a single-axis claim. Three multiplicative axes:

| Axis | Current state | Target state | Lift |
|---|---|---|---|
| **Memory power** | 195 brain `.md` entries accessed via grep / cold-Read; ~600 KB context cost per full lookup | Semantic-query top-5 recall via forge-memory + Ruflo agentdb embeddings; ~6 KB per lookup | **~40×** |
| **Token efficiency** | Opus default for every routine task; brain re-read each spawn; r=1 sweep underreports QBC | Bot-fleet-first routing + r\*-calibrated sweeps (+67% measurement) + condensed-log + QBC-curated cold-start | **~5-10×** |
| **Sheer power** | Single Opus account at quota; sequential sim runs; idle waits between operator clicks | N-OAuth pool + parallel sub-agent fan-out + always-on background workers (QKMS daemon + drift auditor) | **~5-10×** |

Compounded raw: 40 × 5 × 5 = 1000×. Amdahl + coordination overhead dampens to **realistic 100×** end-to-end on the operator-observable axis ("how fast and how well we move").

**Hard guardrail:** every swimlane is purely additive. No existing tool, doctrine, or call-site is removed or changed in a way that breaks current consumers. We ship NEW layers on top of EXISTING surfaces.

---

## What we learned (iters 98-113 + 2026-05-23 → 2026-05-25 doctrine wave)

1. **QBC is real signal.** Per-lane sweeps at K=4 ZZ-FM surface doctrine clusters classical TF-IDF misses (11 lanes swept; consistent semantic-family detection across 1,313,400-triad searches).
2. **r=3 unlocks 67% more measured QBC.** iter-113 finding. The "K=4 encoding-collapse plateau" was a depth-bound, not a Hilbert-space-bound. Every prior r=1 sweep underreported the brain.
3. **K=8 ANGLE is 2.4× faster than K=4 ZZ-FM.** Counter-intuitive — larger Hilbert space, cheaper compute (Kron-product state-build vs full-unitary build).
4. **Cross-encoding agreement = free robustness filter.** Triads in K=4 ZZ-FM ∩ K=8 ANGLE top-N are real clusters; encoding-singletons are artifacts.
5. **Brain self-coherence is healthy** after the 2026-05-25 doctrine surge (10 new entries absorbed cleanly; legacy backbone intact).
6. **Cross-corpus reconciliation finds duplicates.** 11 lane × brain reconciles + 12 lane × lane audits surfaced 15 standing-queue operator-action rows.
7. **The brain is GREP-only right now.** forge-memory store has 2 entries (vs 195 brain docs). Ruflo agentdb is wired (MCP visible) but unused for brain corpus.
8. **Doctrine surge is accelerating.** 10 new brain entries in 2026-05-25 alone; jcode-audit + push-policy + sinister-link + leo-auto-setup + headless-windows + condensed-log + quantum-fleet-discipline + r=3-finding + master-plan-this-file = doctrine generation faster than per-spawn cold-read can keep up.
9. **Token discipline already exists** but is unevenly applied (no-bullshit, condensed-log, no-visible-windows, sanctum-scope, sibling-detect, mesh-coord). Master plan = composition of existing doctrines, not new doctrines.
10. **Multi-OAuth pool + auto-429 + best-slot picker shipped (iter 30 fleet update).** Capacity multiplier already in place at the Sanctum lane; per-lane consumption pattern not yet tuned.

---

## Seven swimlanes (lowest-risk highest-leverage first)

### Swimlane 1 — forge-memory brain backfill (SHIPPING THIS TURN)

**Status:** 🟢 shipping iter-114 of sinister-snap-api-quantum
**Cost:** ~5s wall (Python batch via forge_memory_bridge API)
**Risk:** zero (additive; forge-memory namespace `brain`; upsert idempotent; no edits to existing namespaces)
**Lift:** ~40× memory-power
**Implementation:** `automations/seed-forge-memory-from-brain.py` walks `_shared-memory/knowledge/*.md` (skipping README/_INDEX/_TEMPLATE), writes one record per file under namespace `brain` with key = filename-without-ext, value = full file content, tags = filename-segment tokens. Idempotent re-runs upsert + bump confidence.

**Verification gate:**
- `forge-memory recall 'quantum doctrine' --limit 5` returns the 5 most-relevant brain entries in <500ms
- Tag-based recall works: `forge-memory recall '2026-05-25' --limit 5` returns the latest doctrine wave
- Diff against pre-backfill: namespace `sinister-term` (2 entries) untouched

### Swimlane 2 — r*-calibrated sweep wrapper

**Status:** 🟡 demonstrated empirically (iter-113); needs library wrapper
**Cost:** ~1 hour design, ~10s sim per use
**Risk:** zero (new wrapper function; existing `find_qbc_triads` untouched)
**Lift:** +67% measurement accuracy on every future per-lane sweep
**Implementation:** Add `find_qbc_triads_rstar(...)` to `tools/sinister-seraphim/memory_kernel.py` that defaults `ceiling_reps=[2,3]` and reports r\* + ceiling_pp + headroom_pp per triad. `sim-generic-corpus-qbc.py` adds `--rstar` flag that flips to the new wrapper. Existing scripts keep working unchanged.

### Swimlane 3 — Brain × code drift auditor (concept #10)

**Status:** 🟡 designed in `outputs/python-simulator-concepts-expansion.md`
**Cost:** ~60s sim per full audit; ~5s for incremental
**Risk:** zero (read-only)
**Lift:** doctrine-compliance auditor (the highest-value novel signal the QBC tool unlocks)
**Implementation:** Embed `.ps1` + `.py` + `.ts` files into the same TF-IDF + top-K + ZZ-FM/ANGLE kernel space as brain docs. Run cross-corpus QBC sweep. High-QBC pairs of (doctrine doc × implementation file) where the file IS NOT cited in the doctrine = drift signal. Surface via fleet-update channel + operator-action-queue.

### Swimlane 4 — QKMS daemon (Quantum Kernel Memory Service)

**Status:** 🔴 design only — needs operator green-light for scheduled-task install
**Cost:** ~30s wall per full re-sweep; runs on schedule (recommend every 6 hr)
**Risk:** low (read-only daemon; no writes outside its own output dir)
**Lift:** brain self-coherence + cross-lane drift detected automatically on every brain change
**Implementation:** Background scheduled task (composes with `no-visible-powershell-windows-doctrine` → `Start-Process -WindowStyle Hidden`). Re-runs iter-110 brain self-sweep + iter-113 r\*-calibrated top-20 + iter-112 cross-encoding robustness filter. Diff vs prior run; if max-advantage shifts by >5pp or new top-10 cluster appears, push a `high`-priority fleet-update row.

### Swimlane 5 — Bot-fleet-first task routing (token efficiency)

**Status:** 🟡 docs exist (`_shared-memory/knowledge/bot-fleet-quick-reference.md`); not enforced
**Cost:** ~2 hours doctrine + routing table
**Risk:** zero (additive routing; falls back to Opus on miss)
**Lift:** ~5-10× token-efficiency on routine tasks (file search / classify / scrape / digest / heartbeat / inbox triage)
**Implementation:** Codify a "Task → Bot" routing table as a brain entry. Add to cold-start step 11+1 (after fleet-update poll + sibling-detect + mesh-coord): consult the routing table before reaching for Opus. Per-lane heartbeat reports `bot_calls vs opus_calls` ratio. Quality-monotonic threshold: when ratio drops below 50% on routine work, fire forever-improve audit.

### Swimlane 6 — Parallel-sim sub-agent fan-out

**Status:** 🟡 swarm-mode is `on` doctrine but never used for sim runs
**Cost:** ~3-4× tokens per fan-out (vs 1 sequential)
**Risk:** low (context-budget guard; per-iter wall drops)
**Lift:** ~5× throughput on multi-variant probes (e.g. iters 114-117 of the concepts-expansion plan can fire in parallel instead of sequentially)
**Implementation:** When the next iter has N independent sim variants AND total sequential wall > 60s, spawn N sub-agents (Agent tool, subagent_type general-purpose) each running ONE variant. Aggregate via shared output directory; main lane reads the N JSON files. The Ruflo `hive-mind_consensus` MCP could also drive this.

### Swimlane 7 — QBC-curated cold-start (memory × token compound)

**Status:** 🔴 design only — depends on swimlane 1 + swimlane 4
**Cost:** ~3s per spawn (one Ruflo memory_search call) — negligible
**Risk:** zero (additive — cold-start phrase already does sibling-detect + forge-memory recall by tag; this adds top-5 brain entries by lane semantic similarity)
**Lift:** per-spawn context goes from ~200 brain files potentially read → 5 brain files pre-curated. Compounds with swimlane 1 (forge-memory backfill makes the query possible) and swimlane 5 (bot-fleet routing handles the query).
**Implementation:** Extend `automations/start-sinister-session.ps1` `Build-Phrase` RESUME branch with `MEMORY_RECALL_TOPIC=<lane-key>` → calls `forge-memory recall '<lane-key>' --limit 5` (or equivalent Python invocation) → injects top-5 brain-entry filenames + 1-line topics into the cold-start phrase. Reuses the existing MEMORY_RECALL injection mechanism (tags-based today; topic-based after swimlane 1 lands).

---

## Sequencing — ship lowest-risk first; re-evaluate after each lane

| Iter | Swimlane | What ships | Verification | When |
|---|---|---|---|---|
| **iter-114** | 1 (forge-memory backfill) | `seed-forge-memory-from-brain.py` + first backfill run + recall smoke | `forge-memory recall '<topic>'` returns 5 brain entries; count = 195+ post-backfill | THIS TURN |
| iter-115 | 2 (r\*-calibrated wrapper) | `find_qbc_triads_rstar()` + `--rstar` CLI flag | regression: existing scripts unchanged; new flag runs r∈{1,2,3} by default | next /loop turn |
| iter-116 | 3 (drift auditor) | `sim-brain-vs-code-drift.py` + first audit report | top-10 drift pairs surfaced; zero false-positive on canonical-citation pairs | next /loop turn |
| iter-117 | 5 (bot-routing doctrine) | brain entry + routing table + cold-start step | per-lane heartbeat reports bot/opus ratio | operator-greenlight (touches cold-start) |
| iter-118 | 7 (QBC-curated cold-start) | `start-sinister-session.ps1` MEMORY_RECALL_TOPIC extension | new cold-start phrase includes top-5 lane-curated brain entries | depends on iter-114 + iter-117 |
| iter-119 | 6 (parallel sim fan-out) | demonstrate via iter-115/116 ran-in-parallel mode | wall drops ~4× on multi-variant probe | demonstrated empirically when iter-115/116 ship |
| iter-120 | 4 (QKMS daemon) | scheduled task + diff-detection + fleet-update emission | operator-greenlight per `no-visible-powershell-windows-doctrine` headless install | requires operator-greenlight |

**Estimated total sim cost:** ~3 min wall across all 7 swimlanes. Zero cloud burn. Zero existing-tool changes.

---

## What this composes with (not replaces)

| Existing | How this plan extends it |
|---|---|
| `memory-backbone-3-tier-hybrid` doctrine | Swimlane 1 activates Tier 1 (forge-memory) at full coverage; Tier 2 (brain markdown) unchanged; Tier 3 (Ruflo agentdb) prepared via embedding-ready disk store |
| `quantum-fleet-discipline-doctrine-2026-05-25` | Swimlane 2 + 3 + 4 are concrete quantum-tool deployments; pre-screen (classical-beats-quantum) still binds; Sanctum still scope-disciplined |
| `jcode-full-audit-2026-05-25` 12-item backlog | Swimlane 5 + 7 directly close jcode-parity gaps in status surfacing + token telemetry |
| `bot-fleet-quick-reference.md` | Swimlane 5 codifies the doctrine of WHEN to consult the doc, not just THAT it exists |
| `no-visible-powershell-windows-doctrine-2026-05-25` | Swimlane 4 scheduled task uses `sinister-headless.ps1` wrapper; no new visible windows |
| `mesh-coordinator.ps1` + `sinister-link-doctrine` | Swimlane 4 + 6 register locks before edits; swimlane 7 reads peer locks if cross-machine spawn |
| `no-bullshit-tested-before-claimed-doctrine-2026-05-23` | Every swimlane has its verification gate spelled out; precise verbs at each ship |
| `forever-improve-review-doctrine-2026-05-24` | Swimlane 5 + 6 ratio reporting wires straight into the improvement log |

## Anti-patterns avoided

- **Don't replace forge-memory or Ruflo with a custom store.** Use what's there.
- **Don't pre-compute embeddings during swimlane 1.** Just store the markdown. Embeddings come in Tier 3 (Ruflo) via swimlane 7 + future iter.
- **Don't push everything through Ruflo MCP this iter.** forge-memory is the disk-first tier — start there, layer Ruflo on top.
- **Don't fork the QBC sweep scripts.** Add wrappers + flags; old call sites keep working.
- **Don't fan out to 7 parallel sub-agents in iter-114.** Sequence the swimlanes; demonstrate compounding only after each layer is verified.

## Open for operator decisions

1. **Greenlight swimlane 4 QKMS daemon scheduled-task install** when iter-115/116 land. Requires Task Scheduler write (Sanctum has standing authority via canonical doctrine; surfacing for visibility).
2. **Approve operator-action-queue rows** that surface from swimlane 3 (brain × code drift) — these may include doctrine-rewrite candidates.
3. **Pick a `loop_condition` if you want this lane to keep running** until all 7 swimlanes ship — current default is "queue-empty-or-blocker"; explicit "ship all 7 swimlanes verified" would override.

---

## Footer — the iteration cadence

Per LOOP MODE doctrine: ship swimlane #1 this turn (concrete, fast, zero risk); end-of-turn surfaces #2-7 as queued; next /loop turn auto-fires iter-115. No long ScheduleWakeup delays. Each swimlane verifies in-turn before the next is touched.
