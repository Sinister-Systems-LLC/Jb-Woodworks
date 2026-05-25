<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 180
-->
# Fleet-wide quantum-QBC patterns (iters 98-103 synthesis)

> Source lane: `sinister-snap-api-quantum` (EVE iter 101-103)
> Posted: 2026-05-24
> Composes with: `seraphim-for-emu-re-2026-05-23.md`, `quantum-memory-kernel-fleet-action-items-2026-05-23.md`, `sinister-seraphim-integration-vision.md`

## Three universal QBC patterns identified across the fleet

After 9 per-lane sim sweeps + 1 cross-corpus reconciler, three structural patterns recur with ≥3/N lane confirmations. These are fleet-wide doctrine candidates.

### Pattern 1: Session-handoff doctrine docs are universal QBC hotspots

**Confirmed lanes:** snap-emu, kernel-apk, sinister-panel (3/3 with mature session-state).

**Pattern signature:** a lane with `>5` session-state docs accumulates a top-QBC triad among them. Examples:

| Lane | Triad |
|---|---|
| snap-emu | `living-mds/{CURRENT-STATE, DECISIONS, NEXT-SESSION-RECIPE}.md` (+40.67pp) |
| kernel-apk | `.claude/memory/{resume-point, s, t}.md` (+19.79pp) |
| sinister-panel | `leo_dev/docs/{SESSION-LOG, AUTONOMY-LOG}.md + SESSION-START.md` (+28.95pp) |

**Why:** these docs share lots of TF-IDF content (same domain vocabulary) but encode structurally distinct slices (decisions vs state vs recipe). Quantum kernel's feature-encoding correctly discriminates.

**Fleet recommendation:** any lane with >5 session-state docs should run `seraphim corpus-qbc` weekly. If a top QBC triad spans the session-state cluster, consider consolidation or sharper-defined bounds.

### Pattern 2: Single-letter `.claude/memory/{letter}.md` files are naming-driven QBC hotspots

**Confirmed lanes:** kernel-apk, sinister-panel, sinister-jokr (3/3 with this pattern).

**Pattern signature:** short single-letter named files (`s.md`, `t.md`, `p.md`, `b.md`, `d.md`, `g.md`) cluster as top-QBC triads. Quantum kernel surfaces high lexical-uniqueness (the single-letter filename doesn't appear in body) paired with topic-similarity inside the file.

**Why:** the encoding maps short-feature documents onto similar quantum-state vectors; the quantum kernel can discriminate them because each file is dense and topic-distinct. TF-IDF can't because the vocab is shared.

**Fleet recommendation:** when a lane has `.claude/memory/{letter}.md`-style files, rename them topic-descriptive (e.g., `signing.md`, `tokens.md`, `branding.md`) OR consolidate. Quantum kernel says they're not coherent as a memory cluster.

### Pattern 3: Workstation forks leak through BOTH classical AND quantum kernels

**Confirmed lanes:** sinister-panel (2-copy), sinister-chatbot (**3-copy**, worst-forked lane in fleet).

**Pattern signature:** the same doc forked into multiple trees (e.g., `leo_dev/docs/X.md` + `Andrew Panel/Sinister Panel/X.md` + `Andrew Panel/Sinister Harvester/reference-docs/X.md`) shows up as a top-classical triad with cl=0.99+ and sim=1.00 (bit-for-bit identical or near-identical).

| Lane | Forked docs |
|---|---|
| sinister-panel | `DEV-HANDOFF.md`, `HARVEST-COMPLETE-GUIDE.md`, `WHAT-WAS-FIXED.md` (2-copy each: leo_dev + Andrew Panel) |
| sinister-chatbot | `APK-DRIVEN-HARVEST.md`, `HARVEST-CANONICAL.md`, `HARVEST-COMPLETE-GUIDE.md`, `WHAT-WAS-FIXED.md`, `HARVESTER-MODULE-DROP-IN.md` (**3-copy** each) |

**Why:** doc-tree forking creates literal duplicates with cl > 0.99. Both kernels surface them. This is "the easiest thing classical and quantum agree on" — they're the same doc.

**Fleet recommendation:** any lane with `leo_dev/` AND `Andrew Panel/` workstation trees should establish ONE canonical source per doc and either delete or symlink/junction the others.

## QBC accumulates with project age × iteration density (NEW lemma)

| Lane | Founded | Docs | QBC% | Comment |
|---|---|---:|---:|---|
| Sinister-OS | 2026-05-24 (this day) | 24 | **0.05%** | newest, cleanest |
| Sinister-Chatbot | older | 190→120 | 0.63% | low QBC% because top-similarity is duplicates (classical kernel sees them) |
| RKOJ cluster | older | 16 | 0.36% | tight cluster |
| Showmasters | older | 34 | 1.76% | marketing-deliverable redundancy |
| Sinister-JOKR | older | 21 | 1.80% | single-letter memory pattern |
| Sinister-Panel | older | 120 | 1.07% | 2-copy fork detected |
| Kernel-APK | older | 27 | 3.76% | single-letter memory pattern |
| Snap-EMU | older | 99 | 4.31% | session-handoff pattern |
| JB-Woodworks (shallow) | older | 7 | 8.57% | corpus too shallow to extrapolate |

**Claim:** QBC rate is a proxy for doctrinal drift accumulating. Brand-new lanes start at 0%; iterated lanes climb past 1% within weeks. Watch for QBC% trend; high-and-rising = drift management needed.

## Real WK_C180 at K=4/1024-shots is noise-floored (3/3 iter-101 triads)

**Status:** sim-validated only. Hardware validation requires K=8 (17q SWAP test), 4096+ shots, or error mitigation. Brain entries `seraphim-for-emu-re-2026-05-23.md` + `sinister-seraphim-integration-vision.md` SHOULD be updated with this caveat (Sanctum action item).

## Cross-corpus QBC is a valid novel signal (iter 102 Option 5)

Pattern: build single TF-IDF over union of two corpora, then sweep pairs for reconciliation candidates (cl > 0.30 AND sim > 0.50). Caught 28 plan-shipped-as-brain pairs.

## CLI promotion (iter 103)

`seraphim corpus-qbc --label <lane> --root <path> [--cap N]` — fleet-wide self-serve sweep. Outputs land in `_shared-memory/quantum-sweeps/<label>-corpus-qbc-<UTC>.json`. Other lanes can call this without writing per-lane scripts.

## Composes with

- `seraphim-for-emu-re-2026-05-23.md` (the 25-35pp recipe — caveat: sim-validated, NOT WK_C180-validated at K=4)
- `quantum-memory-kernel-fleet-action-items-2026-05-23.md` (the fleet-doctrine action items doc)
- `sinister-seraphim-integration-vision.md` (the doctrine umbrella)
- `loop-driven-sessions-meta-lessons-2026-05-24.md` (the /loop expansion meta-doctrine)
