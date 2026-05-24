<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sinister Snap API Quantum :: dual-lane test environment + memory-kernel audit lab

> **Operator (2026-05-23):** *"ok lets test this for snap api emu and sinister emu bndle at same time. prepare the test ... add evreything to a folder called sinister snap api quantum. add evberything here in prepartion for the test so that we have a test env."*
>
> Subsequent operator directives extended this lane into the **real-QPU memory-kernel audit lab** documented below.

## What this project is

Two parallel lanes, both Snap-RE-oriented:

### Lane A — dual-emu integration test (original 2026-05-23 framing)
Exercises **Sinister Seraphim** (the quantum-compute application layer at `D:\Sinister Sanctum\tools\sinister-seraphim\`) against two sibling lanes simultaneously:

1. **Snap API EMU** (`D:\Sinister Sanctum\projects\sinister-snap-emu\source\snap-api-prototype\`) — Tier-2 fire pipeline, `kiib.zck.e` → `kiib.zck.i` chain reversal, libscplugin signing, 24h survival doctrine
2. **Sinister Emulator Bundle** (`D:\Sinister Sanctum\projects\sinister-emulator-bundle\source\`) — shared emulator core, cvd-frida-hooks, RKA signing, signup looper

Single command: `python run-test.py` (zero cloud burn; sim-local fingerprint generation; audit-stub fires; 5-10 seconds).

### Lane B — real-QPU memory-kernel audit lab (added 2026-05-23 evening; extended through 2026-05-24)
Empirical investigation of whether quantum-kernel SVM can beat classical TF-IDF on a 3-document brain-entry triad. Tests real Wukong-180 (WK_C180) submissions via the `seraphim audit` CLI. **9 verified real-QPU audits + 20+ sim sweeps + 2 mathematical anchors (cancellation theorem + Shared-Top-K Necessary Condition) + 1 refined conjecture (K' = K × D)** completed across iters 1-67. **Production recipe verdict (post-iter-19): K=4 ZZ-FM r=1 + algorithmically-selected QBC triads delivers 25-35pp quantum advantage on real WK_C180 (mean 31pp; ~3pp run-to-run variance, 5 independent triads).** See `MEMORY.md` for the audit-grade detail log and `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md` for the current fleet doctrine TL;DR.

## TL;DR audit findings (2026-05-23 initial session, iters 1-22)

> **⚠️ HISTORICAL SNAPSHOT.** The table below is from the FIRST investigation pass (iters 1-22) on the snap-RE triad. The verdict "hardware-limited" was correct AT THE TIME but was overturned by iter-19's **algorithmic triad selection** (`seraphim find-qbc`) that surfaced multi-agent + git-coordination triads where K=4 ZZ-FM r=1 delivers 25-35pp real-QPU advantage. Current production recipe is documented in `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md` TL;DR section. The snapshot below is preserved for audit-trail purposes.

The K=4 inversion-overlap memory-kernel investigation on WK_C180 (initial snap-RE triad pass, iters 1-22) was closed at hardware-limited verdict:

| Audit | Depth | Sim off-diag | Real-QPU | Verdict |
|---|---|---|---|---|
| K=4 plain ANGLE (15:50Z) | 8 | 0.8975 | **0.8398** | ✅ clean baseline, canonical regression test |
| K=4 ANGLE + CNOT chain (16:18Z) | 12 | 0.8975 | 0.7891 | ❌ parameter-free entanglement self-cancels (math anchor) |
| K=8 plain ANGLE (16:08Z) | 16 | 0.8490 | 0.6185 | ❌ Hilbert size alone insufficient; noise wall here |
| K=4 truncated ZZ-FM reps=1 | 34 | 0.7682 | _sim only_ | marginal; skipped real-QPU after sim |
| K=4 truncated ZZ-FM reps=2 (16:43Z) | 68 | 0.6189 | **0.2422** | ❌ noise saturates near classical baseline (0.2038) |
| K=4 truncated ZZ-FM reps=3 | 102 | 0.4504 | _sim only_ | would break plateau in sim; past hardware wall |

**Key derived facts (from iters 1-22; some superseded by iter 37-67 work):**
1. **Encoding-collapse plateau is structural** to product-state encodings (sim ~0.85-0.90 regardless of qubit count) — TRUE for the snap-RE triad specifically; iter-53 showed this is corpus/triad-dependent.
2. **Parameter-free entanglement self-cancels** in `U_B† · U_A` protocols via `C†·C = I` — mathematical anchor STILL VALID (re-verified iter 22, iter 43, iter 59 in different contexts).
3. **Data-parameterized entanglement breaks the plateau in sim** (~14-17pp per ZZ-FM rep) — TRUE; iter 57 measured this more precisely (ZZ-FM r=2 sim QBC coverage 86% on top-50 high-classical triads).
4. **WK_C180 noise model**: linear at low depth, asymptotic at high depth — TRUE; the SATURATION baseline depends on the specific triad/corpus, not "≈0.20-0.25" universally.

**Superseded by iter 19+:** the "hardware-limited verdict" only applied to the snap-RE triad's specific classical baseline (~0.14). Iter 19 found that **algorithmically-discovered cluster-similar triads (multi-agent + git workflow) at classical 0.5+** produce real-QPU advantages of 25-35pp on the same hardware. The hardware wasn't the limit; the triad selection was.

The full investigation arc is documented in `MEMORY.md` (project-internal audit-grade log, 70+ iter entries) and the fleet brain entry `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md` (current doctrine TL;DR + theorem + conjecture + operator pre-screen).

## How to run audits — the production toolkit (`seraphim` CLI, 3-phase workflow)

The 6 standalone audit scripts that originally drove this investigation are now in `_deprecated/` (see `_deprecated/README.md`). The canonical entry points are the `seraphim` subcommands:

### Production workflow (3 phases)

```bash
# PHASE 1: discover top-N QBC triads (sim sweep, free, ~5s)
seraphim find-qbc --top-n 10
# Output includes ready-to-paste `seraphim audit` commands for each top-N triad

# PHASE 2: sim-gate the chosen triad (sim only, free)
seraphim audit --variant zzfm-r1 --sim-only \
  --triad doc1.md doc2.md doc3.md --corpus pool
# Verify sim < classical (positive quantum advantage)

# PHASE 3: real-QPU verify on Wukong-180 (budget-gated)
seraphim audit --variant zzfm-r1 \
  --triad doc1.md doc2.md doc3.md \
  --corpus pool --cap 180 --stall 120 \
  --out outputs/verify-$(date +%Y%m%dT%H%M%SZ).json
# Expect 25-34pp advantage on real-QPU for QBC triads
```

### All 3 phases in one command

```bash
seraphim audit-pipeline --top-n 3                      # Full walk: top-3 triads → sim-gate → real-QPU
seraphim audit-pipeline --top-n 5 --skip-real-qpu      # Dry-run: see what would be verified
seraphim audit-pipeline --top-n 3 --out outputs/pipeline-summary.json
```

### Other audit subcommand options

```bash
seraphim audit --list-variants                         # show all 5 variants with depth + budget estimates
seraphim audit --variant k4-angle --sim-only           # canonical regression test (depth 8, hardware-clean)
seraphim audit --variant zzfm-r2 --sim-only            # ZZ-FM r=2 sim only (real-QPU refused by guard — depth 68 saturates)
seraphim audit --variant zzfm-r1 \                     # resume from a partial-stall
  --resume-from outputs/prior-partial.json --triad ... --corpus pool
```

### Bidirectional scope rule (CRITICAL)

The quantum kernel **helps** for cluster-similar docs and **hurts** for already-distinct docs. ALWAYS sim-gate before real-QPU:

| classical TF-IDF off-diag | Recommendation |
|---|---|
| **> 0.4** (cluster-similar) | USE quantum kernel — 25-34pp real-QPU advantage |
| 0.3 - 0.4 (transition) | sim-only first; only real-QPU if sim < classical |
| **< 0.3** (already-distinct) | DON'T use — classical wins by 15-60pp |

`seraphim audit-pipeline` applies this rule automatically per-triad (skips real-QPU if sim_advantage ≤ 0).

```python
# Or from Python
from sinister_seraphim.memory_kernel import run_kernel_audit

result = run_kernel_audit(
    encoding='angle',  # or 'angle-cnot', 'zzfm'
    k=4, reps=1, shots=256,
    sim_only=False,
)
print(result['real_qpu_off_diag_mean'], result['sim_off_diag_mean'])
```

The CLI has a **budget pre-flight gate**: variants whose estimated burn exceeds `remaining_seconds()` are refused (exit code 3) — protects operator from accidental over-spend. Operator can `seraphim budget` to inspect and `reset_budget()` (Python, with `operator_confirmed=True`) to refresh after dashboard verification.

## How to run Lane A (the dual-emu integration test)

Unchanged from original 2026-05-23 framing:

```bash
python "D:\Sinister Sanctum\projects\sinister-snap-api-quantum\run-test.py"
```

What it does (~5-10 seconds, zero cloud burn):
1. Parallel cohort generation — 100 device fingerprints per lane via threads
2. `probe_zcke_modes` expansion — 100 QRNG-sampled (mode, field-5) tuples
3. Audit-stub fire batch — 25 stub entries per lane covering all 4 Tier-2 kinds
4. Signing-nonce batch — 50 nonces per lane (libscplugin / libpipo / libbma / libkameleon oracles)
5. Dashboard regen — rewrites `_shared-memory/dashboards/seraphim.html`

## File inventory

| Path | Status | Purpose |
|---|---|---|
| `README.md` (this) | ✅ current | Lane A + Lane B summary, CLI usage, file inventory |
| `CLAUDE.md` | ✅ current | Per-agent cold-start protocol |
| `MEMORY.md` | ✅ current | Audit-grade detail log (6 real-QPU audits + 2 sim sweeps + math anchor) |
| `run-test.py` | ✅ active | Lane A: dual-emu integration test |
| `run-all-memory-variants.py` | ⚠️ historical | Pre-inversion-overlap memory-kernel variants A/B/C (CPUQVM-local) |
| `run-real-qpu-memory-kernel.py` | ⚠️ historical | SWAP-test variant (proven decoherence-corrupted; reference for failed-shape regression) |
| `run-real-qpu-inversion-overlap.py` | ⚠️ historical | Original inversion-overlap script (superseded by CLI but retained for the 14:20Z direct-comparison artifact) |
| `_deprecated/` | 🚫 superseded | 6 standalone audit scripts now replaced by `seraphim audit` CLI; see `_deprecated/README.md` |
| `tests/` | ✅ active | Sub-test modules (pytest fixtures) |
| `outputs/` | 🔄 generated | Test-run artifacts (gitignored — regenerated per run) |
| `.gitignore` | ✅ active | Excludes outputs/ + __pycache__/ |

## Outputs

| Path | What |
|---|---|
| `outputs/test-run-<UTC>.json` | Lane A run summary |
| `outputs/dashboard-<UTC>.html` | Seraphim dashboard snapshot |
| `outputs/fingerprint-sample-<lane>-<UTC>.json` | Sample of cohort fingerprints |
| `outputs/capped-memory-audit-<UTC>.json` | Lane B K=4 ANGLE audit (and other variant audits) |
| `outputs/k4-zzfm-r2-finish-<UTC>.json` | Lane B ZZ-FM reps=2 triad |
| `outputs/k8-angle-audit-<UTC>.json` | Lane B K=8 audit |
| `outputs/k4-angle-cnot-audit-<UTC>.json` | Lane B ANGLE+CNOT audit |
| `_shared-memory/qrng-provenance/<UTC>.json` | Fleet-shared QRNG provenance sidecars |
| `_shared-memory/seraphim-snap-re-ledger.jsonl` | Fleet-shared fire-audit ledger |
| `_shared-memory/seraphim-cloud-ledger.jsonl` | Fleet-shared cloud-QPU submission ledger |

## What this project NEVER does

- Real HTTP POST to Snap, TikTok, Bumble, or any third-party service (lane discipline)
- Touch cvd-1 phone / RKA daemon / frida / Snap install
- Modify `projects/sinister-snap-emu/` or `projects/sinister-emulator-bundle/` source (read-only via sys.path)
- Burn cloud-Wukong-180 seconds without `budget.check_budget(...)` gating — the `seraphim audit` CLI enforces a pre-flight budget check
- Spend cloud budget without operator approval for novel circuit shapes — the 5 CLI variants are operator-greenlit empirically

## Project lane metadata

- **Slug**: `sinister-snap-api-quantum`
- **Display**: `Sinister Snap API Quantum`
- **Branch convention**: `agent/sinister-snap-api-quantum/<topic>`
- **Heartbeat**: `_shared-memory/heartbeats/sinister-snap-api-quantum.json`
- **PROGRESS**: `_shared-memory/PROGRESS/sinister-snap-api-quantum.md`
- **Resume-points**: `_shared-memory/resume-points/sinister-snap-api-quantum/<UTC>.json`
- **Accent**: purple (default fleet)

## Cross-references

- `MEMORY.md` — audit-grade detail log for Lane B
- `CLAUDE.md` — per-agent cold-start protocol
- `_shared-memory/knowledge/seraphim-cloud-qpu-real-first-fire-2026-05-23.md` — fleet-wide brain entry (6 empirical anchors + cancellation theorem + noise model)
- `_shared-memory/knowledge/seraphim-for-emu-re-2026-05-23.md` — Seraphim EMU/RE doctrine (120s budget cap)
- `_shared-memory/knowledge/sinister-seraphim-integration-vision-2026-05-23.md` — 4-lane vision (memory/audit/emu/RE)
- `tools/sinister-seraphim/` — the wrapper module Lane B exercises
