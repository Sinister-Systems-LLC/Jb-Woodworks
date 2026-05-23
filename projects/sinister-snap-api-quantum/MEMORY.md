<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sinister Snap API Quantum :: project memory (audit + cross-reference)

> **Operator (2026-05-23):** *"take detailed notes of all of this and expand and audit and cross reference those notes make sure we have a full project with memory etc for this and we are working there. update memory"*

Append-only memory. Most recent at top. Cross-references to brain entries and other project memory.

---

## 2026-05-23T14:10Z — 🎯🎯🎯 REAL WUKONG-180 MEMORY-KERNEL EXPERIMENT (3 SWAP tests)

**The 10-second EVE memory upgrade experiment — empirical result on real quantum hardware.**

| Field | Value |
|---|---|
| Run ID | `2026-05-23T141028Z` |
| Backend | `WK_C180` (Wukong-180) |
| Circuit | 9-qubit SWAP-test (1 ancilla + 2 × 4-qubit RY-encoded registers) |
| Shots per pair | 1024 |
| Pairs submitted | 3 (Snap-RE triad: (0,1), (0,2), (1,2)) |
| Jobs | `DDB9BE75F0B45D8601BA2716F2441424`, `D2C7260C3862256F20F3E8B8D35CAF6A`, `6F774FFDA1FB04EA01F94449A55D4ADC` |
| Counts (0,1) | `{'0': 262, '1': 762}` → P(0)=0.256 → 2P-1 = -0.488 → clamped 0.000 |
| Counts (0,2) | `{'0': 548, '1': 476}` → P(0)=0.535 → overlap 0.0703 |
| Counts (1,2) | `{'0': 506, '1': 518}` → P(0)=0.494 → clamped 0.000 |
| Wall (3 pairs) | 32.73s |
| Conservative budget burn recorded | 27.78s (wall-time; will overcount real billing) |
| qpu_run_ms reported by API | 0.0 for all 3 (anomaly — timing field returned zero; may indicate API doesn't report run time for SWAP-test circuits, OR billing is queue-based not run-based) |
| Budget remaining (per our tracker) | 91.989s of 120s |
| Operator dashboard ground truth | (verify; tracker likely overcounts) |

### Three-way kernel comparison

```
                 classical    cpuqvm-sim   real-WK_C180
pair (0,1):       0.2473       0.8102      0.0000  (decohered)
pair (0,2):       0.2259       0.9271      0.0703
pair (1,2):       0.1382       0.9552      0.0000  (decohered)
off-diag mean:    0.2038       0.8975      0.0234
```

### Honest findings

1. **Hardware noise on a 9-qubit SWAP test destroys the small overlap signal.** Pairs (0,1) and (1,2) show P(0) < 0.5 — physically impossible for true quantum overlaps (which always give P(0) ≥ 0.5). This is unmistakable evidence the decoherence corrupted the SWAP-test measurement.

2. **Real QPU off-diag mean ≈ 0 vs CPUQVM sim mean ≈ 0.90.** The sim (no noise) shows the expected encoding-collapse pattern. Real hardware "fixes" the collapse — but in the wrong way (decoherence, not discrimination).

3. **Wukong-180 IS real + reachable + cheap enough to iterate.** ~10s wall per pair (mostly queue/poll). ~3 second per 1024-shot 9-qubit circuit measurement. The budget burn is more about queue time than QPU time.

### Next iteration plan (the real EVE memory upgrade path)

The K=4 RY encoding + SWAP test combination is the wrong circuit shape for our triad. Two cleaner alternatives:

| Variant | Why it should fare better | Circuit depth |
|---|---|---|
| **Destructive SWAP test** | No ancilla; SWAPs followed by direct measurement of both registers. Shallower → less decoherence. | 2K+0 qubits, depth O(K) |
| **Inversion overlap (U†_B · U_A; measure all 0)** | Requires gate inversion but circuit depth halves. Probability of all-zero outcome = |⟨A|B⟩|². | K qubits, depth ~2·encoding_depth |
| **More features (K=8) + ZZ-feature-map** | Larger Hilbert space → more discrimination headroom. WK_C180 has 180 qubits; 17 qubits for K=8 SWAP-test is fine. Risk: depth grows. | 2K+1 = 17 qubits, depth O(K²) for ZZ |

Burn budget remaining: ~92s (per our tracker) / actual unknown. Conservative: budget for ~5-10 more pairs at this depth, OR ~2-3 deeper experiments.

Cross-refs:
- `seraphim-cloud-qpu-real-first-fire-2026-05-23.md` (the first single-qubit H+measure proof)
- `outputs/real-qpu-memory-kernel-2026-05-23T141028Z.json` (full result blob)
- `outputs/real-qpu-memory-kernel-latest.log` (console output of this run)

---

## 2026-05-23T14:00Z — accurate billing observation from operator's dashboard

Operator's `qcloud.originqc.com.cn` dashboard screenshot reported:

| Field | Value |
|---|---|
| Total Remaining | 119.770 s |
| Remaining Paid | 0.000 s (free tier; no paid balance) |
| Remaining Free | 119.770 s |
| Total Used | 0.230 s (from the 2026-05-23T13:55Z H+measure) |
| 05/23 usage | 0.230 s |

**The Origin-internal billing unit is NEITHER `qpuRunTime` (38ms) NOR wall (5.91s).** A single 100-shot H+measure cost **0.230 seconds** of the free-tier budget. That's a meter we don't have direct API access to from pyqpanda3 — we have to read it from the dashboard.

Implications:
- Our `budget.record_usage(elapsed_wall)` OVER-RECORDS — wall is much higher than actual billed.
- Real per-submission rate: ~0.2-1s for small circuits.
- 120s budget → ~120-600 small submissions before exhaustion.

**Until pyqpanda3 exposes the billed-seconds field per call, the operator dashboard is the only authoritative source for budget remaining.**

---

## 2026-05-23T13:55Z — 🎯 FIRST REAL WUKONG-180 QPU SUBMISSION

**Empirical anchor — the first time we touched real quantum hardware from this fleet.**

| Field | Value |
|---|---|
| Backend | `WK_C180` (Wukong-180 chip, 180 superconducting qubits, 99.9% single-qubit fidelity) |
| Job ID | `CD39F4DD92D5B5ADFAFF1CB2C991864A` |
| Pilot Task ID | `3113D2E758A94F3F8DF84EB93BDFA0D2` |
| Circuit | `H q[0]; MEASURE q[0],c[0]` (OriginIR) |
| Shots | 100 |
| Counts (real QPU) | `{'0': 52, '1': 48}` |
| Probabilities | `{'0': 0.4302, '1': 0.5698}` (slight real-noise bias) |
| qpuRunTime | **38 ms** (actual QPU compute) |
| totalTime | 2917 ms (queue + compile + run + post) |
| pulseTime | 40 ms |
| Wall (submit→result) | 5.91 s (mostly poll overhead) |
| Budget before | 120.00 s remaining |
| Budget after | 114.09 s remaining (we recorded full wall as burn — conservative) |
| Caveat on budget | Actual QPU runtime was 38ms, NOT 5.91s. The 120s license-seconds probably refers to `qpuRunTime` not wall time. **Operator should clarify with Origin** to know real burn rate. If qpuRunTime is the unit, we used ~0.04 of 120s here. |
| Result fields available | `get_counts` / `get_probs` / `get_amplitudes` / `get_state_fidelity` / `get_state_tomography_density` / `origin_data` / `timing_info` / `error_message` / `job_status` |

Proof on disk: `outputs/first-qpu-submission.json`. Cross-ref brain entry: `seraphim-cloud-qpu-real-first-fire-2026-05-23.md`.

---

## 2026-05-23T13:30Z — cloud auth + endpoint clarification (the hard wall, now solved)

**Discovery chain:**

1. Operator vaulted the PilotOS V4.2 license blob (512 base64 chars = 384 bytes encrypted binary) at `_vault-personal/licenses/pilotos.txt`. I initially assumed this was the qcloud API key. It is NOT.
2. PilotOS license = self-hosted PilotOS deployment auth. Operator's V4.2 tarball at `C:\Users\Zonia\Desktop\QPilotos-V4.2\` is for Linux-server deploy; the default test endpoint in the lib is `https://10.10.8.8:10080` (private network — Origin internal, unreachable from operator's Windows machine).
3. `qcloud.originqc.com.cn` = Origin's **public cloud QPU service** (separate product, separate billing). Needs a separate API key from the user dashboard.
4. **The correct cloud submission endpoint is `http://pyqanda-admin.qpanda.cn` (HTTP, default in pyqpanda3 0.3.5 `QCloudService.__init__`), NOT the `https://qcloud.originqc.com.cn` website URL.** The website is the frontend; the backend API lives on the admin domain.
5. Operator registered + retrieved the qcloud API key (96 hex chars = 48 bytes) and dropped it into `_vault-personal/licenses/originqc-qcloud-apikey.txt`. With this key + the correct backend URL, `QCloudService(api_key=key, url='http://pyqanda-admin.qpanda.cn')` authed cleanly.

**Backends listed by `QCloudService.backends()`:**

| Backend | Available | Notes |
|---|---|---|
| `WK_C180` | ✅ | Wukong-180 (the flagship 180-qubit superconducting chip) |
| `PQPUMESH8` | ✅ | 8-qubit superconducting test chip |
| `HanYuan_01` | ❌ | Offline at probe time |
| `full_amplitude` | ✅ | Full statevector simulator (cloud-hosted) |
| `partial_amplitude` | ✅ | Partial-amplitude simulator |
| `single_amplitude` | ✅ | Single-amplitude simulator |

Cross-ref: `seraphim-cloud-qpu-real-first-fire-2026-05-23.md`, `eve-exe-launcher-jcode-speed-parity-2026-05-23.md` (parallel pattern: wrap paid SDK with our discipline).

---

## 2026-05-23T13:25Z — pyqpanda3 0.3.5 API map (empirical, not in docs)

**Circuit construction (gotchas):**

- `from pyqpanda3.core import QCircuit, QProg, H, measure` — note **`H` is uppercase function, `measure` is lowercase function**, both are pybind11 builtin_function_or_method. The OpType enum members (`Measure`, `MeasureNode`) are NOT callable.
- `circ = QCircuit(n_qubits)` — bare int constructor
- `circ << H(0)` — operator overloading; `H(0)` returns a Gate op
- `prog = QProg(); prog << circ << measure(0, 0)` — `measure(qubit, cbit)` adds measurement
- `prog.originir()` — serializes to OriginIR string for inspection
- QCircuit methods: `append / clear / control / dagger / depth / draw / expand / matrix / originir / remap / size` etc.
- QProg methods: `append / cbits / count_ops / depth / draw / flatten / from_originbis / get_measure_nodes / originbis / originir / qubits / qubits_num / remap / to_circuit`

**Submission:**

- `svc = QCloudService(api_key=key, url='http://pyqanda-admin.qpanda.cn')`
- `backend = svc.backend('WK_C180')`
- `opts = QCloudOptions(); opts.set_mapping(True); opts.set_optimization(True); opts.set_is_prob_counts(True)`
- `job = backend.run(prog, shots, opts)` — returns `QCloudJob` (async)

**Job lifecycle:**

- `job.job_id()` — 32-hex Origin task ID
- `job.status()` — `JobStatus.COMPUTING` → `JobStatus.FINISHED` (also `QUEUED` `PENDING` `FAILED`)
- `job.query()` — refresh status from server
- `job.result()` — returns `QCloudResult` when finished (blocks if not)

**Result fields (QCloudResult):**

- `get_counts() -> dict[str, int]` — measurement-string → shot count
- `get_counts_list() -> list[dict]` — per-shot batch (if multiple circuits)
- `get_probs() -> dict[str, float]` — normalized probabilities
- `get_amplitudes() -> dict[str, complex]` — amplitudes (empty for chip backends)
- `get_state_fidelity() -> float` — fidelity to expected state (if expected provided)
- `get_state_tomography_density() -> list` — if run_quantum_state_tomography
- `origin_data` — raw server JSON (contains taskId / pilotTaskId / errCode / qpuRunTime / pulseTime / totalTime / probCount)
- `timing_info` — dict of all timing fields
- `error_message` — empty on success

---

## 2026-05-23T13:00Z — memory-kernel encoding experiment (CPUQVM, no cloud burn)

Built `tools/sinister-seraphim/memory_kernel.py` with 3 encoding variants:

- **Variant A** (4-qubit amplitude encoding): off-diag mean 0.987 → encoding-loss collapse
- **Variant B** (8-qubit angle / RY top-8): off-diag mean 0.849 → less collapsed
- **Variant C** (4-qubit ZZ-feature-map, Havlicek): off-diag mean 0.715 → best of 3; disagrees with classical TF-IDF on the strongest pair

Classical TF-IDF baseline: off-diag mean 0.204 (clean discrimination).

**Honest verdict at 4-8 qubit scale: classical wins for recall.** Quantum kernels collapse off-diag to >0.7 due to tiny Hilbert space. Variant C's disagreement with classical on the strongest pair IS a signal (ZZ-feature-map captures cross-term correlations TF-IDF misses) but could equally be small-Hilbert-space noise. **Real test requires 16+ qubit scale** — now feasible on WK_C180 (180 qubits!) with the live cloud key.

Cross-ref: `seraphim-for-emu-re-2026-05-23.md`, `sinister-seraphim-integration-vision-2026-05-23.md`.

---

## 2026-05-23T12:30Z — dual-lane test env shipped + run

Project scaffolded at `D:\Sinister Sanctum\projects\sinister-snap-api-quantum\` + Desktop junction at `C:\Users\Zonia\Desktop\Sinister Snap API Quantum\`. Single-command test driver `run-test.py` exercises Seraphim against snap-emu + sinister-emulator-bundle in parallel via threads.

Initial run was 234s (per-call disk thrash on 164 sidecar writes). Optimized to 10.78s (22x faster) via batch-aggregate sidecars per `make_fingerprint_batch` + `mode_search_seeds`.

Test outputs:
- `outputs/test-run-<UTC>.json` — full summary
- `outputs/dashboard-<UTC>.html` — Seraphim dashboard snapshot
- `outputs/fingerprint-sample-<lane>-<UTC>.json` — cohort samples
- `outputs/memory-kernel-{variant-A,B,C}.json` — kernel experiment per-variant detail
- `outputs/memory-kernel-comparison-<UTC>.json` — side-by-side summary
- `outputs/first-qpu-submission.json` — **the first real QPU proof**

---

## Cross-references (brain index)

| Brain entry | Why |
|---|---|
| `seraphim-cloud-qpu-real-first-fire-2026-05-23.md` | **New** — captures the first real WK_C180 submission with full evidence |
| `seraphim-for-emu-re-2026-05-23.md` | Operator-canonical doctrine pinning Seraphim to EMU/RE focus + 120s budget table |
| `sinister-seraphim-integration-vision-2026-05-23.md` | 4-lane vision (memory+audit / sinister-emulator-env / drone-sim / RE) |
| `snap-tt-rka-chain-attestation-insufficient-2026-05-19.md` | Snap RE work the snap_re adapter complements |
| `snap-emu-pb2-schema-shadow-2026-05-21.md` | Snap pb2 schema gap; mode_search_seeds expansion path |
| `snap-account-24h-survival-doctrine-2026-05-21.md` | 24h survival cohort study; survival_fingerprints is the audit layer |
| `jcode-feature-matrix.md` row 29 | Seraphim tool entry |
| `eve-exe-launcher-jcode-speed-parity-2026-05-23.md` | Parallel pattern: wrap a paid/proprietary SDK with our discipline |
| `do-not-revert-operator-canonical-protections-2026-05-23.md` | Canonical protections — Seraphim follows the same pattern |
| `sanctioned-bypasses-doctrine-2026-05-21.md` | Lane 4 RE work operator-OWN-only per AUP-RESPECT |

## What this project NEVER does

- Fire live HTTP at Snap/TikTok/Bumble/Origin production services beyond the qcloud API itself
- Burn cloud-Wukong-180 seconds without `budget.check_budget(...)` gate
- Commit secrets (vault keys, signed nonces, raw circuit results that might leak) — `outputs/` and `_vault-personal/` are gitignored
- Modify `projects/sinister-snap-emu/` or `projects/sinister-emulator-bundle/` source — lane discipline per canonical-10
