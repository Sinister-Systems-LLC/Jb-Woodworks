<!-- Author: RKOJ-ELENO :: 2026-05-25 -->

<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# Quantum Fleet Discipline (Sanctum-scope)

**Created:** 2026-05-25T01:35Z
**Authority:** Operator hard-canonical 2026-05-25T01:25Z verbatim *"kee[p wporking on quantum and memory as the main project scort"*.

Sanctum-scope consolidation of quantum-applicability across the fleet. NOT lane-specific execution (that stays in `sinister-snap-api-quantum`); this doctrine binds the FLEET DISCIPLINE around when, how, and why quantum gets used.

---

## 1. Three categories of quantum work in the fleet

| Category | Owner Lane | Sanctum role |
|---|---|---|
| **Active QPU experiments** | `sinister-snap-api-quantum` | Route operator decisions + surface budget state + cross-lane absorption |
| **Quantum-enhanced features** in projects | per-project lane | Honor `sinister-os-quantum-applicability-2026-05-24` 3-hooks; classical-beats-quantum pre-screen always |
| **Quantum memory / vector backends** | sanctum + sinister-snap-api-quantum | Tier 3 of `memory-backbone-3-tier-hybrid` — Ruflo agentdb HNSW + RaBitQ as optional accelerator |

Sanctum does NOT submit QPU jobs directly. Sanctum DOES surface lane findings into fleet-wide doctrine + maintain cross-lane brain entries (this doctrine + the 6 quantum-related entries it composes with).

## 2. Classical-beats-quantum pre-screen (BINDING for every quantum hook)

Before ANY quantum submission (real-QPU OR CPUQVM), the lane must demonstrate:

1. **Classical baseline measured** — log the metric (accuracy / time / cost) on the classical solver first
2. **Quantum hypothesis stated** — explicit prediction of why quantum would beat classical
3. **Smoke-test in CPUQVM first** — if it doesn't discriminate in simulator, it WON'T on hardware
4. **Budget-gate on operator nod** — every real-QPU submission requires operator dashboard verification

This rule exists because iter-26 state showed `discrimination collapsed (K=4 Hilbert-space plateau)` — hardware path validated but encoding strategy wasn't yet beating classical. Don't burn budget on un-pre-screened encodings.

## 3. Current verified findings (2026-05-23 last real-QPU run)

- **ANGLE inversion overlap survived real WK_C180 hardware** at K=4 depth ~8 — 3/3 pairs P(0000) ∈ [0.77, 0.90] (physically valid)
- **ZZ-FM at depth ~88 past the decoherence wall** — overlaps ~0.11 (close to uniform-noise floor 0.0625); ZZ-FM all-pairs CNOT ladder hitting heavy mapping/optimization on server
- **Discrimination still collapsed at K=4** — classical TF-IDF discrimination 0.20 vs quantum 0.85 off-diag → quantum NOT yet beating classical on this task
- **Origin budget tracker over-counts** by ~5-10× vs server billing — operator dashboard at `qcloud.originqc.com.cn` is ground truth

## 4. Three open variants ready (gated on operator dashboard go)

| Variant | Rationale | Pre-screen status |
|---|---|---|
| Sparser ZZ-FM (nearest-neighbor only) | Avoid the decoherence wall by reducing CNOT depth | CPUQVM smoke pending |
| K=8 ANGLE | Larger Hilbert space, test if discrimination recovers | CPUQVM smoke pending |
| ANGLE + linear-entangling | Intermediate depth between K=4 ANGLE + ZZ-FM | CPUQVM smoke pending |

Lane should pre-screen all 3 in CPUQVM during the gating window so when operator unblocks, the highest-value variant goes first.

## 5. Quantum memory backend (Tier 3 of memory-backbone)

Ruflo agentdb HNSW + RaBitQ 1-bit quantization (32x compression) IS quantum-adjacent — RaBitQ paper cites quantum amplitude estimation as inspiration.

Per `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` Tier 3:
- Brain markdown stays canonical (Tier 1)
- JCODE-style decay frontmatter is canonical metric (Tier 2; iter 19 hit 100%)
- Ruflo agentdb is OPTIONAL accelerator (Tier 3; 4-8wk activation; gated on operator green-light)

When activated: 1.66 GB brain corpus → ~50 MB HNSW index (32x compression); semantic recall in <10ms.

## 6. Composes with

- `sinister-os-quantum-applicability-2026-05-24` (3-hook gate doctrine for any project considering quantum)
- `fleet-quantum-qbc-patterns-2026-05-24` (QBC pattern catalog)
- `seraphim-cloud-qpu-real-first-fire-2026-05-23` (verified real-QPU operational baseline)
- `seraphim-for-emu-re-2026-05-23` (emulator-side quantum integration vision)
- `quantum-memory-kernel-fleet-action-items-2026-05-23` (cross-lane absorption tracker)
- `sinister-seraphim-integration-vision-2026-05-23` (longer-arc integration vision)
- `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` (Tier 3 quantum-adjacent backend)
- `sanctum-scope-discipline-2026-05-24` (this doctrine = fleet-shape; lane-execution stays in sinister-snap-api-quantum)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rules 1+2: precise verbs / test before claiming)

## 7. Anti-patterns

1. Sanctum lane submitting QPU jobs directly (scope-discipline violation; route to sinister-snap-api-quantum)
2. Skipping classical baseline before quantum experiment (no apples-to-apples comparison)
3. Burning QPU budget without operator dashboard verification (tracker over-counts; could exhaust budget unnecessarily)
4. Treating Ruflo agentdb activation as immediate (4-8wk effort; gated on operator)
5. Cross-pollinating per-project quantum decisions without the 3-hook pre-screen from sinister-os-quantum-applicability doctrine

## 8. Verification

```powershell
# Quantum lane brain-decay state
powershell -File automations/brain-decay-score.ps1 -Action Score -TopDecayed 10 -As Json | ConvertFrom-Json | Where-Object { $_.Slug -match 'quantum|seraphim|qbc' } | Format-Table

# OPERATOR-ACTION-QUEUE rows tagged quantum
Get-Content _shared-memory/OPERATOR-ACTION-QUEUE.md | Select-String -Pattern 'quantum|qpu' -Context 1,3
```
