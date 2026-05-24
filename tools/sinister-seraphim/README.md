<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# tools/sinister-seraphim :: Sinister fleet's quantum-compute application layer

> **Operator (2026-05-23):**
> 1. *"yes i know we can use this for our shit. get to work on it"*
> 2. *"i want the focus on the pilotos to be on memory. auditing things thigns like that. like a super local agent"*
> 3. *"using it to create our sinister emulator in the enviroment we ened for it ... a super local agent like with jcode ... memory simulations ... 1000s of accounts ... reverse engineering to help with our sinister api"*

## What this tool is

The Sinister fleet's wrapper around **Origin Quantum PilotOS V4.2** (locally installed at `C:\Users\Zonia\Desktop\QPilotos-V4.2\`) + the `python_simulator` measurement-control sim + `pyqpanda3` SDK. Single source of truth for every quantum primitive any fleet lane consumes (memory, audit, env-sim, RE).

License: paid V4.2 (operator), vaulted at `_vault-personal/licenses/pilotos.txt` (gitignored). Loader reads it from there at startup; refuses to start if missing.

## Why we need a wrapper (not pyqpanda3 directly)

1. **License-loader gate**: every entry-point reads the license from the vault, blocks if absent. Keeps the secret-handling in one place.
2. **Local-sim default**: cloud Wukong-180 submissions cost RMB + round-trip from PRC infra. Default every call to local sim; opt in to cloud per-call.
3. **Audit trail**: every quantum call writes a `_shared-memory/qrng-provenance/<UTC>.json` sidecar with circuit + seed + sim/cloud + measurement results — this IS the value-add for the "audit" framing.
4. **Sinister-purple branding**: outputs through our existing logging + heartbeat conventions.
5. **Fleet routing**: bots (forge / kernel-apk / panel / emulator) call a single Python API rather than each shelling out to pyqpanda3.

## Four use lanes (per operator's wider framing)

### Lane 1: Memory + audit (super-local agent)

- **QRNG-seeded fingerprints**: every emulator phone (Kernel-APK / Snap-EMU / TikTok-EMU / Bumble-EMU) seeds its device-fingerprint blob from quantum entropy. Sidecar JSON proves provenance — defensible if an external auditor questions our randomness source.
- **QRNG audit trail**: every secret we generate (signing nonces, session IDs, BB84 keys for internal comms) goes through `quantum_random(n_bytes)` which logs the circuit + measurement.
- **Quantum-kernel brain recall**: experimental — does a quantum-kernel SVM over `_shared-memory/knowledge/` embeddings beat TF-IDF + Ruflo HNSW for our 80-entry brain? Probably no at this size, but small experiment to confirm.
- **Memory simulation**: simulate counter-factual brain states ("what if we'd archived entry X 3 weeks earlier?") — quantum amplitudes are a natural fit for branching superposition over edit-history.

### Lane 2: Sinister Emulator environment (account-traffic sim)

- **Quantum-RNG-driven fingerprint generation** at 1000s of accounts/second (local sim).
- **Combinatorial fingerprint search**: QAOA over the device-attribute tuple-space to find detection-evading combinations the classical search misses. Real benefit only if the search space is large enough; needs measurement.
- **Behavioral-pattern sampling**: VQE / quantum-circuit-Born-machine generates "look-natural" sequences of taps/scrolls/dwell-times that classical pseudo-RNGs cluster on. Operator's account-orchestration lane benefits if classical generators are getting flagged.

### Lane 3: Drone systems training env

- Quantum simulation of physical environments (gravity / wind / sensor noise) for RL training of drone-pilot models.
- Quantum-walk navigation primitives — exploratory.

### Lane 4: Reverse engineering — Sinister API discovery

- Quantum-Grover search over a known plaintext space (e.g., suspected token-encoding patterns).
- Quantum-circuit primitive for hash-collision finding on weak proprietary hashes (educational; do NOT use against third-party services per AUP-RESPECT).

## Status (updated 2026-05-23 evening)

| Component | Status |
|---|---|
| README.md (this) | ✅ shipped 2026-05-23, updated 2026-05-23 evening |
| `license.py` (loader from vault) | ✅ shipped — PilotOS license fingerprint via sha256[0:12] |
| `qrng.py` (entropy daemon — Lane 1 starter) | ✅ shipped — sim-local default, cloud-Wukong-180 opt-in |
| `audit.py` (provenance sidecar writer) | ✅ shipped — `_shared-memory/qrng-provenance/<UTC>.json` |
| `budget.py` (cloud-Wukong-180 120s cap enforcer) | ✅ shipped — ledger at `_shared-memory/seraphim-cloud-ledger.jsonl`; 9 entries as of 2026-05-23 evening |
| `cloud_submit.py` (real-QPU submission path) | ✅ shipped — refactored 2026-05-23 evening: working URL/backend constants + 3 builders + generic `submit_circuit` + high-level `submit_kernel_pair(thetas_a, thetas_b, encoding=...)` |
| `memory_kernel.py` (quantum-kernel SVM experiment + audit runner) | ✅ shipped — `run_kernel_experiment` (sim variants A/B/C) + `run_kernel_audit` (inversion-overlap sim+real triad) |
| `fingerprint.py` (Lane 2 device-fingerprint generation) | ✅ shipped — `make_fingerprint`, `make_fingerprint_batch` |
| `snap_re.py` (Snap-EMU integration adapter) | ✅ shipped — `fire_audit`, `mode_search_seeds`, `survival_fingerprints`, `signing_nonce` |
| `dashboard.py` (static HTML dashboard) | ✅ shipped — `seraphim dashboard --out PATH` |
| `summarize.py` (provenance + ledger aggregation) | ✅ shipped — `seraphim summarize --since W` |
| `cli.py` (`seraphim <cmd>` entry point) | ✅ shipped — 11 subcommands incl. `audit`, `find-qbc`, `audit-pipeline` (2026-05-23 evening) |
| Cloud Wukong-180 path (opt-in per-call) | ✅ **ACTIVE workhorse** — 9 real submissions on 2026-05-23 covering K=4/K=8 plain ANGLE, ANGLE+CNOT, ZZ-FM r=2 (see `_shared-memory/knowledge/seraphim-cloud-qpu-real-first-fire-2026-05-23.md`) |
| FastAPI surface (`server.py` on :5079) | 📋 deferred (no consumer demand yet) |
| First consumer: kernel-apk fingerprint seeding | 📋 cross-lane (handoff offered) |
| First consumer: Sinister Emulator account-sim | 📋 cross-lane (handoff offered) |
| Brain entry: `seraphim-cloud-qpu-real-first-fire-2026-05-23.md` | ✅ shipped + heavily updated with 6 empirical-anchor sections |
| Pytest regression tests (`tests/test_smoke.py`) | ✅ shipped — 15 tests covering qrng/audit/fingerprint + iter 47/48/59/65 memory-kernel doctrine. Run: `cd tools/sinister-seraphim && pytest tests/ -v` (~5s) |

## How to use

### CLI

```bash
seraphim qrng -n 32 --purpose "fingerprint-seed"      # 32 bytes QRNG with provenance sidecar
seraphim fingerprint --lane snap-emu                   # one device-fingerprint blob
seraphim fingerprint-batch -n 1000 --lane snap-emu     # 1000 fingerprints (Lane 2)
seraphim license-check                                 # verify license + print sha256[0:12]
seraphim budget                                        # show cloud-Wukong-180 budget status (120s cap)
seraphim dashboard                                     # regenerate the dashboard HTML

# Memory-kernel quantum-advantage toolkit (PRODUCTION RECIPE — quintuple-verified 2026-05-23 evening / iter 19)
# Three-phase workflow, each phase callable separately OR all-in-one via audit-pipeline:

seraphim find-qbc --top-n 10                           # PHASE 1: discover quantum-beats-classical triads
                                                       # (sim sweep across 300k+ triads in ~5s, zero cloud burn)
seraphim find-qbc --top-n 10 --rank-by ceiling         # PHASE 1.b: re-rank by sim ceiling (sweeps r=2..6
                                                       #  for top-N; ~5s extra). Reveals error-mitigation
                                                       #  targets (see iters 39-41 doctrine).
seraphim find-qbc --top-n 10 --rank-by headroom        # PHASE 1.c: rank by (ceiling - r=1) = biggest
                                                       #  payoff if real-QPU ever exits depth-34 noise wall.

seraphim audit --variant zzfm-r1 --sim-only \         # PHASE 2: sim-gate the chosen triad
  --triad doc1.md doc2.md doc3.md --corpus pool       # (confirm sim < classical before real-QPU)

seraphim audit --variant zzfm-r1 \                     # PHASE 3: real-QPU verify on Wukong-180
  --triad doc1.md doc2.md doc3.md --corpus pool       # (25-35pp quantum advantage expected for QBC triads; mean 31pp across 5 verified runs)

seraphim audit-pipeline --top-n 3                      # ALL 3 PHASES in one command (the "easy mode")
seraphim audit-pipeline --top-n 5 --skip-real-qpu      # dry-run mode: see which triads would be verified

# Audit recovery + variants:
seraphim audit --variant k4-angle --sim-only           # zero-burn sim baseline (canonical regression test)
seraphim audit --variant zzfm-r1 --resume-from outputs/prior.json --triad ... --corpus pool
                                                       # resume from a partial-stall: reuses landed pairs
seraphim audit --variant zzfm-r2 --sim-only            # ZZ-FM r=2 sim only (real-QPU refused by guard)
seraphim audit --list-variants                         # show all 5 variants + their depth/burn estimates

seraphim brain-recall "your query string" --top-k 5    # iter 47 SHIPPED, iter 48 FIXED: TF-IDF + quantum-kernel hybrid recall
                                                       # DEFAULT alpha=1.0 (pure TF-IDF) per iter-48 stress-test.
                                                       # alpha<1.0 DEGRADES pair-wise recall (K=8 ANGLE collapses to
                                                       # noise-docs at sparse-query input). Override only after empirical
                                                       # validation. Doctrine: iter-44 K=8 ANGLE "wider net" applies to
                                                       # TRIAD (3-doc) discrimination, NOT pair-wise (query vs doc).

seraphim summarize --since 24h                         # provenance + ledger aggregation
```

### Production recipe (the headline)

**Quintuple-verified 25-35pp quantum-kernel-beats-classical-TF-IDF advantage** (mean 31pp; run-to-run variance ~3pp) on real WK_C180 with:
- Encoding: `--variant zzfm-r1` (K=4 ZZ-FM nearest-neighbor reps=1, depth ~34)
- Triad: discovered via `seraphim find-qbc` (cluster-similar docs where classical TF-IDF off-diag > 0.4)
- Corpus: `--corpus pool` (~129-doc topical-balanced TF-IDF vocabulary; grows with brain corpus but capped at 4-per-topic-prefix)

**Bidirectional scope rule** (critical):
- classical > 0.4 → quantum helps (use the recipe)
- classical < 0.3 → classical wins (quantum hurts by 15-60pp; **don't** use)
- 0.3-0.4 → run sim-gate first

**Sim-ceiling characterization** (added iter 40, 2026-05-24): a 12-triad reps-sweep established **`classical ↔ sim ceiling` Pearson r=+0.9537** (very strong). Classical TF-IDF baseline is the single best predictor of theoretical quantum-kernel advantage. Higher classical → higher ceiling, almost monotonically. Production recipe r=1 captures 48-82% of the ceiling depending on triad — the 18-52% gap is what error-mitigation work (ZNE / twirling / readout cal) could theoretically unlock at r=2..r=5 on a quieter QPU. Today's Wukong-180 noise saturates real-QPU at r=2+, so r=1 is optimal for production today.

Use `--rank-by ceiling` to surface high-ceiling triads (highest theoretical ZZ-FM advantage). Use `--rank-by headroom` to surface triads with biggest `ceiling - r=1` gap (= error-mitigation payoff targets). Use `--rank-by classical` to re-sort the top-N by classical baseline.

**Shared-Top-K Necessary Condition + K=4 combined pre-screen** (iter 58/59/60 theorem + iter 65/66 sharpening): For K-ANGLE encoding at K∈{4..8}, a triad is NEVER QBC if the top-K TF-IDF features have zero intersection across all 3 docs (500 zero-FP classifications across 2 corpora). For K=4 ANGLE specifically, the predictor extends: skip a triad if (a) shared top-4 = 0 OR (b) all 3 docs share the same #1 feature. Combined predictor rules out **44% of candidate triads on the 149-doc full corpus** before running the encoding — zero false positives. Mechanism: K=4 only uses top-4 features; disjoint sets → orthogonal feature subspaces → no quantum discrimination; same #1 → qubit 0 stuck (25% of capacity lost).

Quick Python pre-screen (saves ~half of pointless K=4 audit runs):
```python
import numpy as np
def k4_angle_worth_running(triad_tfidfs):
    top4 = [set(np.argsort(np.abs(v))[-4:].tolist()) for v in triad_tfidfs]
    if len(top4[0] & top4[1] & top4[2]) == 0:
        return False  # guaranteed K=4 anti-QBC
    top1 = [int(np.argmax(np.abs(v))) for v in triad_tfidfs]
    if top1[0] == top1[1] == top1[2]:
        return False  # all 3 same #1 → guaranteed K=4 anti-QBC
    return True  # might be QBC; run audit to verify
```

For K=5/K=6 ANGLE: the combined predictor stays safe (28% / 12% rule-out on the 129-doc pool). For K≥7 ANGLE or any ZZ-FM reps: use only the shared-top-K=0 condition (safe but weak filter). ZZ-FM r=1+ has no useful pre-screen — use `find-qbc` enumeration.

Full doctrine: `_shared-memory/knowledge/quantum-memory-kernel-fleet-action-items-2026-05-23.md`.

### Python API (Lane 1 — entropy/audit)

```python
from sinister_seraphim.qrng import quantum_random
from sinister_seraphim.audit import write_provenance

# 32 bytes of entropy with provenance sidecar
seed_bytes = quantum_random(32, purpose="kernel-apk-fingerprint-spoof")
# -> writes _shared-memory/qrng-provenance/<UTC>.json with circuit + measurement
```

### Python API (Lane 2 — emulator fingerprints)

```python
from sinister_seraphim.fingerprint import make_fingerprint_batch

fingerprints = make_fingerprint_batch(
    n=1000,
    lane="snap-emu",
    backend="sim-local",  # cloud-Wukong-180 also available but burns budget
)
```

### Python API (Lane 1+B — memory-kernel audits)

```python
from sinister_seraphim.memory_kernel import run_kernel_audit

# Sim-only check (zero cloud burn)
result = run_kernel_audit(encoding='angle', k=4, sim_only=True)
print(result['sim_off_diag_mean'])  # 0.8975 for canonical Snap-RE triad

# Full audit with real-QPU triad
result = run_kernel_audit(encoding='zzfm', k=4, reps=2, shots=256, sim_only=False)
print(result['real_qpu_off_diag_mean'], result['sim_off_diag_mean'])
```

### Python API (Lane 1+B — direct cloud submission)

```python
from sinister_seraphim.cloud_submit import confirm_auth, submit_kernel_pair
import numpy as np

# Cheap auth probe
r = confirm_auth()
assert r['ok'], r.get('detail')
print(r['backends'])  # {'WK_C180': True, 'PQPUMESH8': True, ...}

# One inversion-overlap pair (budget-gated)
thetas_a = np.array([0.5, 1.0, 1.5, 2.0])
thetas_b = np.array([0.4, 1.1, 1.6, 1.9])
pair = submit_kernel_pair(thetas_a, thetas_b, encoding='angle', k=4, shots=256)
print(pair['overlap'], pair['job_id'], pair['wall_seconds'])
```

## Lane discipline

- **Wrap, don't reimplement**: pyqpanda3 stays as the upstream; we wrap it with license-loader + audit + routing.
- **Local-sim default**: never call cloud unless `use_cloud=True` is explicit per-call.
- **Single source of truth**: every quantum call routes through this tool. No fleet lane shells out to pyqpanda3 directly.
- **License never leaves vault**: the `license.py` reads from `_vault-personal/licenses/pilotos.txt` (gitignored). Never log the key. Never embed in headers.

## Composes with

- `_vault-personal/licenses/pilotos.txt` (operator-private license)
- `C:\Users\Zonia\Desktop\QPilotos-V4.2\python_simulator.tar.gz` (local sim SDK)
- `tools/sinister-seraphim/audit.py` (sidecar JSON writer)
- Brain entry: `_shared-memory/knowledge/pilotos-integration-vision-2026-05-23.md` (next commit)
- Desktop audit: `C:\Users\Zonia\Desktop\AUDIT-pilotos-2026-05-23.md` (operator-private, full 3-pass audit)
- Existing fleet: `tools/sinister-watchdog/`, `tools/sinister-vault/`, `tools/nano-banana/` — same wrapper pattern.

## python_simulator.tar.gz audit (operator-requested 2026-05-23)

Inspected without extracting. Contents at `C:\Users\Zonia\Desktop\QPilotos-V4.2\python_simulator.tar.gz` (48 files, pure CPython 3.10):

- **Core**: `task_manager.py`, `result_generator.py`, `chip_config_loader.py`, `config.py`, `main.py`
- **Network**: `zmq_pub_server.py` + `zmq_router_server.py` — ZMQ-based pub/sub + router endpoints. This is a *measurement-control protocol simulator*, not a one-shot CLI. It runs as a background service that accepts circuit submissions and emits results, exactly the way Origin's real measurement-control hardware does.
- **Protocol adapters**: `superconducting.py`, `ion_trap.py`, `neutral_atom.py` — three quantum chip families simulated.
- **Chip configs**: `ChipArchConfig_PQPUMESH8.json` (8-qubit super), `ChipArchConfig_72.json` (72-qubit — Wukong family), `ChipArchConfig_IonTrap.json`, `ChipArchConfig_HanYuan_01.json`. Four virtual QPUs available locally.
- **Bilingual**: `README_CN.md` + `README.md` + `README_转换说明.md`.

**Verdict**: high value-add. This unblocks the `sim-pilotos` backend without any cloud round-trip. Concrete plan:

1. Operator extracts the tarball to `tools/sinister-seraphim/_vendor/python_simulator/` (gitignored as a vendor dir; sim is operator-licensed not ours to vendor publicly).
2. `qrng.py:_call_pilotos_sim()` gains a real implementation that issues a ZMQ request to the local router server for an N-shot measurement on `ChipArchConfig_PQPUMESH8` (8-qubit is enough for ≤32 bytes of entropy per call; chain calls for more).
3. Per-chip routing — Lane 2 (Sinister Emulator account-traffic sim) can pick `ChipArchConfig_72` for higher-bandwidth fingerprint batches.
4. The ZMQ surface composes cleanly with our existing 13-bot MCP network — `sinister-seraphim` becomes a 14th bot served by `sinister-bus` if operator wants.

**One operator gate**: extracting the tarball requires running `tar -xzf python_simulator.tar.gz -C tools/sinister-seraphim/_vendor/`. The dir lives in `.gitignore` (build/ pattern catches `_vendor/` too — verify before committing the first real `sim-pilotos` wiring).

## What this tool does NOT do (yet)

- Doesn't deploy PilotOS itself (operator owns the install at `Desktop\QPilotos-V4.2\` — that's a Linux-server-targeted deployment per the upstream manual).
- Doesn't call Wukong-180 cloud automatically (cost gate; opt-in only).
- Doesn't replace `forge-memory-bridge` or `Ruflo agentdb_*` for brain recall — quantum-kernel SVM is an experimental sidecar, not a replacement.
- Doesn't ship the user-manual PDFs to GitHub (operator-private; stays at `Desktop\QPilotos-V4.2\`).
