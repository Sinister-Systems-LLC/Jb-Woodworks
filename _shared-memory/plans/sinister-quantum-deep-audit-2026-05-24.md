<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sinister Quantum — Deep Audit + Buildable Systems Proposal

> **Status:** plan, in-flight, awaiting operator pick on Section 2 systems
> **Origin:** parallel Sinister Quantum session prompt 2026-05-24 — *"deep audit what we can do with the new sinister quantum data and start building out systems with it that will help us"*
> **Scope:** `projects/sinister-snap-api-quantum/` lane through iter ~92, plus the seraphim wrapper at `tools/sinister-seraphim/`. Read-only audit. No source touched.

---

## Section 1 — Inventory (what data exists, audit-grade)

### 1.1 Real-QPU runs (paid Wukong-180 fires)

| File | Triad | Result |
|---|---|---|
| `outputs/zzfm-r1-rank1-realqpu.json` | multi-agent-branch / git-coord / verify-head | classical 0.5363 → sim 0.2746 → real 0.1953 (**34pp advantage**) |
| `outputs/zzfm-r1-rank2-realqpu.json` | multi-agent / git-index / verify-head | **32pp** |
| `outputs/zzfm-r1-rank3-realqpu.json` | multi-agent / git-coord / git-index | **31pp** |
| `outputs/zzfm-r1-rank4-realqpu.json` | branch-checkout / multi-agent / git-index | **25pp** |
| `outputs/audit-pipeline-end-to-end.json` | (rank-2 re-fire) | **35pp** (run-to-run variance ~3pp) |
| `outputs/k4-angle-on-zzfm-rank1-triad.json` | rank-1 with K=4 ANGLE (not ZZ-FM) | only **3.4pp** (encoding matters 10×) |
| `outputs/real-qpu-memory-kernel-2026-05-23T141028Z.json` | snap-RE canonical (already-distinct) | classical wins by 60pp (anti-QBC) |
| `outputs/real-qpu-inversion-overlap-2026-05-23T141959Z.json` | inversion-overlap reference | (baseline) |
| `outputs/k4-angle-cnot-audit-2026-05-23T161705Z.json` | cancellation-theorem proof | ANGLE-CNOT == K=4 ANGLE bit-for-bit |

**Total: 9 real-QPU audits + 5 verified-positive runs (mean 31pp advantage, range 25-35pp).**

### 1.2 Sim sweeps (zero-cost, large N)

| File | Shape |
|---|---|
| `outputs/quantum-beats-classical-search.json` | 317,750-triad sim sweep; 16 K=4 QBC (0.005%) + 451 ZZ-FM-r1 QBC (0.142%) |
| `outputs/zzfm-r1-qbc-search.json` | ZZ-FM r=1 enumeration |
| `outputs/zzfm-r2-qbc-search.json` | ZZ-FM r=2 enumeration (86% QBC on top-50) |
| `outputs/top50-qbc.json` | canonical top-50 QBC triads |
| `outputs/encoding-preference-sweep.json` | K=8 vs ZZ-FM r=1 complementarity (157 triads) |
| `outputs/sim-reps-ceiling-sweep.json` | r=1..6 sweep (ceiling 36-50pp triad-dependent) |
| `outputs/conjecture-classical-vs-headroom.json` | 12-triad classical↔ceiling Pearson r=+0.9537 |
| `outputs/triad-similarity-sweep.json` | similarity-vs-advantage characterization |
| `outputs/scope-test-zzfm-r1-sim.json` | bidirectional scope rule data |

**Total: 20+ sim sweeps producing parameter spaces in JSON.**

### 1.3 Empirically PROVEN findings (numerical evidence)

1. **Cancellation theorem** (iter 16/22/43): ANGLE-CNOT == K=4 ANGLE bit-for-bit. Parameter-free entangling layers cancel in U_B† · U_A.
2. **Production recipe** (iter 5-22): ZZ-FM r=1 + K=4 + 5-verified Wukong-180 runs → 25-35pp advantage.
3. **Bidirectional scope rule** (iter 10/23): classical > 0.4 → quantum helps; classical < 0.3 → quantum HURTS by 17-60pp.
4. **Encoding choice matters 10×** (iter 13): same triad K=4 ANGLE → 3.4pp; ZZ-FM r=1 → 34.1pp.
5. **Encoding complementarity** (iter 44/45): K=8 ANGLE wins 58.6% / ZZ-FM r=1 wins 41.4%; Pearson(classical, Δ) = -0.42.
6. **Universal-QBC nesting** (iter 52): K=4 QBC ⊂ K=8 QBC ⊂ ZZ-FM QBC (strict subset, corpus=pool only).
7. **Per-encoding 50% thresholds** (iter 53): K=4 ANGLE 0.55, K=8 ANGLE 0.45, ZZ-FM r=1 0.50.
8. **Classical↔ceiling correlation** (iter 40): Pearson r=+0.9537 (single best predictor).
9. **Shared-Top-K Necessary Condition** (iter 58-60): K∈{4..8} ANGLE, 500 classifications, **zero false positives**. Disjoint top-K → never QBC.
10. **K=4 combined predictor** (iter 65-66): shared=0 OR same-top-1 → anti-QBC. **44% rule-out on 149-full corpus, zero FP**.
11. **Origin queue stall pattern** (iter 4-22): 5 stalls on `multi-agent-git-coordination` triad; triad-specific not encoding-specific.
12. **Corpus-context sensitivity** (iter 84): same triad, different TF-IDF vocabulary → different K=4 verdict. Doctrine must specify corpus.

### 1.4 Conjectures OPEN (not yet proven)

1. **K' = K × D conjecture** (iter 63, **only 2 data points**): for ZZ-FM at reps=r, predictor window K' = K × (1+r). Needs ≥5 more data points.
2. **Higher classical → more headroom** (iter 39, 3 triads): seen in 3-triad sweep, not tested broadly.
3. **Error-mitigation pathways** (ZNE / Pauli twirling / readout cal): conjectured to unlock ZZ-FM r=2's 86% sim ceiling on real-QPU. **No empirical fire**.
4. **ANGLE K=6/7 theorem boundary** (iter 61): rule is intrinsic to ANGLE; conjectured to never extend to ZZ-FM. Not formally bounded.

### 1.5 Brain entries (5 quantum-related)

- `quantum-memory-kernel-fleet-action-items-2026-05-23.md` (doctrine TL;DR, refreshed iter 68)
- `seraphim-cloud-qpu-real-first-fire-2026-05-23.md` (empirical anchor log)
- `seraphim-for-emu-re-2026-05-23.md` (120s budget doctrine)
- `sinister-seraphim-integration-vision-2026-05-23.md` (4-lane vision)
- `loop-driven-sessions-meta-lessons-2026-05-24.md` (meta-doctrine from iter 90)

### 1.6 Cost ledger (operator-visible)

- Total Wukong-180 seconds burned: ~60s of 120s budget (5 verified-positive fires + 5 stalls + theorem-proof fires).
- Estimated dollar spend: ~$2-3 (Origin Quantum pricing; lower bound).
- Remaining budget: ~60s (50% headroom for follow-up empirical work).

---

## Section 2 — Buildable systems (operator-pickable)

The 5 verified-positive real-QPU runs + 12 empirical findings unlock real value. Below: 8 concrete systems, ordered by ROI/effort.

### S1 — Quantum-Discriminated Brain-Recall Service (QDB-R)

**What it does:** an MCP server (or HTTP endpoint) that takes a query string + top-K and returns brain-entry candidates re-ranked by ZZ-FM r=1 quantum-kernel discrimination, used as a tiebreaker AFTER classical TF-IDF. Sim-only (zero cloud burn).

**Consumes:** the brain corpus (`_shared-memory/knowledge/`), the iter-48 corrected `brain-recall` semantics (default alpha=1.0; quantum as separate signal not blended), the find-qbc enumeration cache.

**Produces:** for any agent calling `brain.recall(query, top_k)`, a re-ranked top-K where the bottom-of-top-K is verified quantum-distinguishable. The "tiebreaker for surface-similar docs" use case from iter 4's honest verdict.

**Effort:** M (1 week). Wrap `tools/sinister-seraphim/cli.py brain-recall` into an MCP server. Add cache layer for `find-qbc` results (refresh on corpus delta > 1%).

**POC (2 hours):** wire `seraphim brain-recall --top-k 5` into a simple HTTP endpoint at `tools/sinister-seraphim/server.py`; test against 3 ambiguous queries (multi-agent / git-coord / verify-head themes); compare to pure TF-IDF; document the tiebreaker behavior.

---

### S2 — Pre-Screen Triad Filter (PSTF)

**What it does:** a fast Python helper any lane can import to apply the iter-65/66 K=4 combined predictor (shared top-4 = 0 OR top-1 all identical → skip) BEFORE running expensive quantum or sim work. 44% of triads ruled out at zero cost.

**Consumes:** triad doc paths + corpus mode.

**Produces:** boolean `is_likely_qbc(triad, corpus='full') -> bool` with confidence interval (currently 44% rule-out, zero FP).

**Effort:** S (1 day). Extract the predictor from `memory_kernel.py` into a standalone `tools/sinister-seraphim/prescreen.py` with explicit API + 3 unit tests covering shared-top-4, same-top-1, and combined-rule cases.

**POC (1 hour):** write the function + test on the 31 universal-QBC triads (must return True for all known QBC; must return False for the 44% rule-out set per iter 66 measurement).

---

### S3 — Quantum Doctrine Drift Detector (QDDD)

**What it does:** weekly cron-style audit that runs `seraphim audit --variant zzfm-r1 --sim-only` on a canonical reference triad (the rank-1 multi-agent/git-coord/verify-head set). Alerts if sim_off_diag_mean drifts > 3pp from the iter-19 baseline (0.2746). Detects TF-IDF vocabulary drift caused by brain-corpus changes.

**Consumes:** the rank-1 canonical triad, the iter-49 corpus-pool stability baseline.

**Produces:** a heartbeat entry at `_shared-memory/heartbeats/quantum-drift.json` + an OPERATOR-ACTION-QUEUE row when drift > 3pp.

**Effort:** S (1 day). Single script + Windows Scheduled Task. Outputs `_shared-memory/PROGRESS/quantum-drift.md` append-only log.

**POC (1 hour):** write `automations/quantum-drift-check.ps1`; manually run today, capture baseline; verify drift detection by intentionally perturbing the corpus (add a high-overlap-vocab doc) and confirming alert fires.

---

### S4 — Discrimination-as-a-Service Tiebreaker MCP (DaaS-MCP)

**What it does:** MCP server exposing 4 tools — `qbc_check_triad(docs)`, `find_qbc(top_n, variant)`, `audit_pair(doc_a, doc_b, variant)`, `prescreen_triad(docs)`. Lets any lane query the quantum kernel via MCP without spawning subprocesses. All sim-only by default.

**Consumes:** the seraphim CLI surface as transport layer.

**Produces:** machine-readable JSON responses for any Claude session that has `sinister-seraphim` MCP loaded.

**Effort:** M (3-5 days). Build on the existing seraphim Python; expose via FastMCP. Register in `~/.claude/.mcp.json` (operator-gated — request per the lane-discipline rules).

**POC (2 hours):** scaffold FastMCP server with one tool (`qbc_check_triad`) + smoke test from a separate Claude session. Don't wire MCP config yet — that's the operator-handoff step.

---

### S5 — Triad Library + Pre-Computed Catalog (TLPC)

**What it does:** ships a JSON catalog at `_shared-memory/quantum-catalog/triads-2026-05-24.json` containing the top-50 QBC triads under each of K=4 ANGLE / K=8 ANGLE / ZZ-FM r=1 / ZZ-FM r=2, with classical + sim + (where known) real-QPU values + Shared-Top-K predictor flags + recommended use-case. Refreshed weekly by `QDDD` (S3).

**Consumes:** existing `outputs/top50-qbc.json` + `outputs/encoding-preference-sweep.json` + `outputs/quantum-beats-classical-search.json`.

**Produces:** a canonical lookup table any lane can grep for "give me 3 known-QBC docs that include lane X" without re-running find-qbc.

**Effort:** S (1 day). Merge the existing JSON outputs into a normalized catalog with schema. Add an index by lane (which lane each doc lives in) + by classical bin.

**POC (1.5 hours):** write a build script that produces the catalog; verify the 5 verified-positive triads land in K=4/ZZ-FM r=1 bins; spot-check 3 K=8 triads in the catalog match `find-qbc --variant k8-angle`.

---

### S6 — Snap-API-EMU Cross-Lane Discriminator (SAECD)

**What it does:** integrates the quantum-kernel pre-screen into the dual-emu test harness (`run-test.py`). Before each test run, emit a one-line quantum diagnostic: "doctrine-set for this run has classical 0.X / shared-top-4 Y / quantum-recommendation: USE/SKIP/TIEBREAK". Surfaces the quantum signal alongside the existing audit + fingerprint signals.

**Consumes:** the test harness's lane-doc set + the iter-65/66 pre-screen.

**Produces:** an extra column in the dashboard (`_shared-memory/dashboards/seraphim.html`) showing quantum-discrimination verdict per test run.

**Effort:** S-M (2-3 days). One new column in dashboard + invocation hook in `run-test.py`. Read-only consumer of the quantum-catalog from S5.

**POC (2 hours):** add a `--quantum-diagnostic` flag to `run-test.py` (does NOT modify lane behavior — just prints diagnostic); run twice and confirm the diagnostic appears in dashboard.

---

### S7 — K'=K×D Conjecture Empirical Closer (KKD-EC)

**What it does:** scripted experiment that tests the iter-63 conjecture with ≥5 more data points (currently only 2). Sweeps ZZ-FM r=1..r=4 across 5 K values × 3 corpora = 60 sim runs. Either confirms the K'=K×D relation or falsifies it. Closes one of the 4 open conjectures.

**Consumes:** the existing sim sweep machinery + the conjecture spec from `quantum-memory-kernel-fleet-action-items-2026-05-23.md`.

**Produces:** a new brain entry `_shared-memory/knowledge/kkd-conjecture-closer-2026-05-25.md` with either proven status + 4 more decimal places of measurement, or falsifying counter-example.

**Effort:** S (1 day, mostly compute). 60 sim runs at ~5s each = 5 min CPU + 1h analysis.

**POC (1.5 hours):** write the sweep script as `projects/sinister-snap-api-quantum/sim-kkd-conjecture-closer.py` (with the lane's existing run-test.py pattern); run on 2 K values × 3 reps = 6 runs as smoke test; verify pattern holds.

---

### S8 — Quantum-Aware Auto-Doctrine Promoter (QADP)

**What it does:** a fleet-wide doctrine auditor that, when a new brain entry lands, runs find-qbc with the new entry in the corpus, identifies the top-3 entries it most strongly discriminates against (via QBC triads), and AUTO-POSTS a `composes-with:` link suggestion to the new entry. Surfaces "this new doctrine is quantum-distinct from X/Y/Z" as a one-time advisory.

**Consumes:** the brain corpus + find-qbc + the entry's own `Tags` field.

**Produces:** a daily report at `_shared-memory/quantum-promotions/<date>.md` with 0-5 suggestions per day (low-noise).

**Effort:** M (4-5 days). Needs corpus-delta detector + find-qbc batch mode + report writer. Heaviest item on this list.

**POC (2 hours):** prototype the "given new entry, find top-3 discriminable siblings" function in Python; test on the 3 most recently added entries; verify suggestions are non-obvious + actionable.

---

### Pick guidance (operator)

- **Quick wins (S1+S2):** combine for a fully-usable quantum-kernel tiebreaker layer in <1.5 weeks.
- **Catalog-first (S5):** unblocks S6 + S8 by giving everything a stable lookup table.
- **Empirical closer (S7):** clears 1 of 4 open conjectures with 1 day of work — closes the "no fairy tale bullshit" gap.
- **MCP exposure (S4):** highest leverage long-term; biggest operator-gate (MCP config).
- **Drift detection (S3):** lowest risk, weekly recurring value.

---

## Section 3 — Memory propagation (cross-lane)

### 3.1 Brain entries that should cross-link to quantum findings

| Brain entry | Suggested addition |
|---|---|
| `multi-agent-branch-contention-isolation-pattern.md` | "Composes with: `quantum-memory-kernel-fleet-action-items-2026-05-23.md` — this entry is in the rank-1 universal-QBC triad; doctrine is quantum-discriminable across encodings (34pp advantage on Wukong-180)." |
| `multi-agent-git-coordination-2026-05-23.md` | "Composes with quantum kernel: in rank-1 universal-QBC triad. **Caveat:** triggers Origin Wukong-180 queue stalls — for real-QPU work use `multi-agent-git-index-contention-storm` variant instead." |
| `multi-agent-git-index-contention-storm-2026-05-23.md` | "Quantum-stable: appears in 5 universal-QBC triads; consistently lands on Wukong-180 without stalls. Recommended over the git-coord variant for real-QPU audits." |
| `verify-head-before-commit-multi-agent.md` | "Member of 4 of 5 verified Wukong-180 real-QPU triads. Quantum-distinguishable from sibling coordination doctrines (32-35pp advantage)." |
| `branch-checkout-silently-undoes-doctrine-2026-05-23.md` | "In rank-4 verified real-QPU triad (25pp advantage). Quantum-pattern extends beyond pure multi-agent prefix." |
| `apk-leak-surface-audit-2026-05-23.md` | "Quantum-anti-pattern: do NOT use as triad-mate with other APK docs — quantum kernel plateau-collapses on within-lane high-similarity sets (iter 23 cross-lane false-lead correction)." |
| `seraphim-for-emu-re-2026-05-23.md` | "Budget cap 120s; this session has spent ~60s; remaining headroom 50%. See `quantum-memory-kernel-fleet-action-items-2026-05-23.md` for the 5-run audit ledger." |
| `forge-memory-usage-2026-05-23.md` | "Quantum-discriminable from sibling forge doctrines. When updating, run `seraphim audit --variant zzfm-r1 --sim-only --triad <this> <sibling1> <sibling2>` to detect drift." |
| `panel-command-center-18-wave-sweep-2026-05-21.md` | "In rank-1 algorithmic-QBC triad. Quantum-distinct from sibling coordination doctrines." |
| `sinister-freeze-project-doctrine.md` | "Appears in 4 of top-10 algorithmic-QBC triads. Recommended adopter for `seraphim qrng` provenance + audit." |

**New brain row for `_INDEX.md`:**

```
| sinister-quantum-deep-audit-2026-05-24 | Sinister Quantum deep audit + buildable systems proposal | plan, awaiting-operator-pick | quantum-systems, mcp-proposal, qdb-r, pstf, qddd, daas-mcp, tlpc, saecd, kkd-ec, qadp, operator-pick, 8-systems, 5-verified-real-qpu, 4-open-conjectures | 2026-05-24 | 2026-05-24 |
```

### 3.2 PROGRESS files referencing quantum work (cross-link recommended)

- `_shared-memory/PROGRESS/Sinister Sanctum.md` — add row pointing to this audit + the 8 system proposals (master lane has S1+S5+S8 dependencies).
- `_shared-memory/PROGRESS/snap-emulator-api.md` — already references quantum work; add the `SAECD` (S6) integration item.
- `_shared-memory/PROGRESS/rkoj.md` — quantum mentions; add note that QRNG-seeded fingerprints (covered in iter 1 brain entry) is available via `seraphim qrng`.
- `_shared-memory/PROGRESS/Sinister Forge.md` — should add quantum-kernel doctrine-drift entry (S3 dependency).
- `_shared-memory/PROGRESS/Sinister Panel.md` — same (panel-command-center is in rank-1 triad).
- `_shared-memory/PROGRESS/Sinister Kernel APK.md` — should reflect the iter-23 correction (cross-lane triads HURT; within-lane apk-leak-surface triads also plateau-collapse).
- `_shared-memory/PROGRESS/sinister-freeze.md` — adopter candidate for QRNG provenance.

### 3.3 Agents to notify (per `PARALLEL-AGENT-COORDINATION.md`)

- **Sinister Sanctum** (master): owns S1+S5+S8; receives this audit doc directly.
- **Sinister Forge:** S3 customer (drift detection on `forge-memory-usage`).
- **Sinister Panel:** S3 customer (wave-sweep doctrine in rank-1 triad).
- **Sinister Snap-API (snap-emulator-api):** S6 owner (dual-emu test harness integration).
- **Sinister Kernel APK:** iter-23 correction broadcast — within-lane APK triads plateau-collapse on quantum kernel; do NOT adopt cross-lane snap+tt+apk pattern; use `find-qbc` enumeration with classical>0.4 filter instead.
- **Sinister Freeze:** S5 catalog consumer + QRNG-provenance candidate.
- **Sinister Snap API Quantum:** owns S7 + S5 (the closer + catalog live here).

---

## Section 4 — Operator action items

### 4.1 Pick which systems to build

Operator picks 1-N from S1-S8. Master can scaffold the picked ones in the next session.

### 4.2 Pre-existing operator-gates that compose

- **MCP config edit** (required for S4 + future S1 MCP upgrade): operator-owned per lane discipline. Document the entry before adding.
- **Real-QPU budget**: 60s remaining of 120s. S7 (KKD closer) is sim-only — does NOT consume budget. Future real-QPU error-mitigation work would.
- **Scheduled task registration** (S3): operator clicks `automations/install-quantum-drift-task.ps1` once installed.

### 4.3 Honest blockers / risks

- **K'=K×D conjecture has only 2 data points** — calling it "proven" would violate the no-bullshit doctrine. S7 closes this.
- **Origin queue non-stationarity** — 5 stalls observed on the multi-agent-git-coord triad. S5 catalog must document which triads are stall-prone; consumers must respect.
- **Corpus-context sensitivity** (iter 84) — any system using `run_kernel_audit` directly MUST pass `corpus=pool` explicitly. Document this in S2's API.
- **Combined predictor is K=4-specific** (iter 66) — S2's `is_likely_qbc(K=4)` has 44% rule-out; at K=8 only 2%. Document the K-axis.

---

## Cross-references

- Lane doctrine: `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md`
- Empirical anchor log: `_shared-memory/knowledge/seraphim-cloud-qpu-real-first-fire-2026-05-23.md`
- Loop-driven meta-lessons (parent doctrine): `_shared-memory/knowledge/loop-driven-sessions-meta-lessons-2026-05-24.md`
- Lane PROGRESS: `_shared-memory/PROGRESS/sinister-snap-api-quantum.md`
- Lane project root: `projects/sinister-snap-api-quantum/`
- Lane MEMORY.md (audit-grade detail): `projects/sinister-snap-api-quantum/MEMORY.md`

## Tags

quantum-deep-audit, sinister-snap-api-quantum, buildable-systems, operator-pick, qdb-r, pstf, qddd, daas-mcp, tlpc, saecd, kkd-ec, qadp, memory-propagation, cross-lane, 2026-05-24, plan, RKOJ-ELENO
