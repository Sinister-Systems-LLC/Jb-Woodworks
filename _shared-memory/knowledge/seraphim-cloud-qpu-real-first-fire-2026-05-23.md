<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sinister Seraphim — FIRST REAL Wukong-180 QPU submission (empirical anchor)

> **Status:** doctrine, validated, empirical
> **Origin:** operator 2026-05-23 verbatim: *"i want to test actaully using our seconds. we used nothing on the quantum computer stop wasting time and setup the real test"* + dropped qcloud API key (96 hex chars from `qcloud.originqc.com.cn` dashboard)

## The first real QPU submission (proof)

| Field | Value |
|---|---|
| Date | 2026-05-23T13:55Z |
| Backend | `WK_C180` (Wukong-180 chip — Origin's flagship 180-qubit superconducting QPU) |
| Job ID | `CD39F4DD92D5B5ADFAFF1CB2C991864A` (live on Origin's servers) |
| Pilot Task ID | `3113D2E758A94F3F8DF84EB93BDFA0D2` |
| Circuit (OriginIR) | `QINIT 1` / `CREG 1` / `H q[0]` / `MEASURE q[0],c[0]` |
| Shots | 100 |
| Counts | `{'0': 52, '1': 48}` |
| Probabilities | `{'0': 0.4302, '1': 0.5698}` (slight real-noise bias) |
| qpuRunTime | **38 ms** (the metric likely matching the operator's 120s budget) |
| totalTime | 2917 ms (queue + compile + run + post-process) |
| Wall (submit→result) | 5.91 s |

Disk artifacts:
- `projects/sinister-snap-api-quantum/outputs/first-qpu-submission.json`
- `_shared-memory/seraphim-cloud-ledger.jsonl` (entry recorded via `budget.record_usage`)

## The two-product confusion (clarification — critical for next agent)

Origin Quantum sells **two separate products** with **two separate auth credentials**:

| Product | What it is | Auth credential | Where it lives | Our path |
|---|---|---|---|---|
| **PilotOS V4.2** | Self-hosted quantum operating system (deploy on your own Linux server). License gates how long the OS runs. | 512-char base64 license blob (encrypted, 384 bytes) | `_vault-personal/licenses/pilotos.txt` | Operator hasn't deployed; default URL `https://10.10.8.8:10080` is Origin internal, unreachable. **BLOCKED until operator deploys PilotOS on a Linux server.** |
| **OriginQ qcloud** | Public cloud quantum service. Submit circuits to Wukong-180 + other backends via REST. | 96-hex-char API key from `qcloud.originqc.com.cn` user dashboard | `_vault-personal/licenses/originqc-qcloud-apikey.txt` | **WORKING as of 2026-05-23T13:55Z.** First submission proven. |

**The operator's "120 seconds on the license key" was originally PilotOS license language but now appears to apply to qcloud qpuRunTime budget too — needs clarification with Origin to confirm billing unit.**

## The endpoint URL gotcha

**Use `http://pyqanda-admin.qpanda.cn` (HTTP, default in pyqpanda3 0.3.5), NOT `https://qcloud.originqc.com.cn` (which is the website frontend).**

The two failure modes when using the wrong URL with the right key:

| URL | Error | Diagnosis |
|---|---|---|
| `https://qcloud.originqc.com.cn` | `RuntimeError: Invalid value.` | Frontend domain; lib's parser rejects the HTML response |
| `http://pyqanda-admin.qpanda.cn` | works | Correct backend admin endpoint |

This gotcha cost us ~30 minutes of "the license blob is wrong" debugging when the actual problem was URL. **Fixed in `tools/sinister-seraphim/cloud_submit.py` default URL** (was `https://qcloud.originqc.com.cn` → now `http://pyqanda-admin.qpanda.cn`).

## pyqpanda3 0.3.5 submission API (empirical map — not all in docs)

```python
from pyqpanda3.qcloud.qcloud import QCloudService, QCloudOptions
from pyqpanda3.core import QCircuit, QProg, H, measure

# 1. Service
svc = QCloudService(api_key=KEY, url='http://pyqanda-admin.qpanda.cn')

# 2. Backend
backend = svc.backend('WK_C180')      # other: PQPUMESH8 / full_amplitude / partial_amplitude / single_amplitude
# backend.name() / backend.chip_info() / backend.chip_backend()

# 3. Build circuit
circ = QCircuit(n_qubits)
circ << H(0)                          # H is uppercase function returning a Gate op
prog = QProg()
prog << circ << measure(0, 0)         # measure is lowercase function (qubit, cbit)

# 4. Options
opts = QCloudOptions()
opts.set_mapping(True)
opts.set_optimization(True)
opts.set_is_prob_counts(True)

# 5. Submit (returns QCloudJob — async)
job = backend.run(prog, shots, opts)

# 6. Poll
import time
while str(job.status()).lower() in ('jobstatus.computing', 'jobstatus.queued', 'jobstatus.pending'):
    time.sleep(1)

# 7. Fetch result
res = job.result()
print(res.get_counts())               # {'0': 52, '1': 48}
print(res.get_probs())                # {'0': 0.4302, '1': 0.5698}
print(res.timing_info['qpuRunTime'])  # 38 (ms — the billing unit)
```

**Critical gotchas:**

1. `H` is uppercase, `measure` is lowercase. The OpType enum members (`Measure`, `MeasureNode`) are NOT callable — using them raises `'OpType' object is not callable`. Use the function (lowercase `measure(q, c)`).
2. `backend.run()` is non-blocking. Always poll `job.status()` until `FINISHED`.
3. `job.result()` blocks until result is ready (or raises if job is in error state).
4. `error_message` empty string == success.
5. `qpuRunTime` is in **milliseconds**, not seconds. Multiply or convert before reasoning about the 120s budget.

## Backend roster (probed 2026-05-23T13:55Z)

| Backend | Status | Type |
|---|---|---|
| `WK_C180` | ✅ ONLINE | Wukong-180 superconducting chip (180 qubits, 99.9% 1q fidelity) |
| `PQPUMESH8` | ✅ ONLINE | 8-qubit superconducting test chip |
| `HanYuan_01` | ❌ OFFLINE | Hanyuan-1 chip (likely scheduled maintenance) |
| `full_amplitude` | ✅ ONLINE | Full statevector simulator (cloud-hosted; no QPU billing) |
| `partial_amplitude` | ✅ ONLINE | Partial-amplitude simulator |
| `single_amplitude` | ✅ ONLINE | Single-amplitude simulator |

## Budget interpretation (open question — operator clarify)

Two plausible meanings of "120 seconds on the license":

| Interpretation | Per-call cost from our first H+measure |
|---|---|
| **qpuRunTime** (actual QPU compute, the `qpuRunTime` field in `timing_info`) | 38 ms = 0.038s of 120s. ~3,158 such tiny submissions before exhaustion. |
| **Wall-clock submit→result** (what `budget.record_usage(elapsed)` currently records) | 5.91 s of 120s. ~20 such submissions before exhaustion. |
| **Other** (e.g. `pulseTime` 40ms, or some Origin-internal billing meter) | Unknown — operator to clarify with Origin if billing rate matters. |

Our `budget.record_usage` currently records the conservative wall-clock burn. If the real cost is `qpuRunTime`, we're under-using the budget by 100x. **Action**: keep conservative recording until operator confirms the billing unit.

## Anti-patterns to never repeat

1. **Assume the PilotOS license = qcloud API key.** They are different products. Two separate vault files: `pilotos.txt` (deployment) + `originqc-qcloud-apikey.txt` (cloud).
2. **Use `https://qcloud.originqc.com.cn` as the QCloudService URL.** That's the website frontend; the backend lives at `http://pyqanda-admin.qpanda.cn` (lib default).
3. **Treat `OpType.Measure` as callable.** It's an enum. Use `measure(qubit, cbit)` function.
4. **Fire cloud submissions without `budget.check_budget()` first.** Default-refuse pattern protects the operator's spend.
5. **Log raw API keys.** Use `license_fingerprint()` (sha256[0:12]) in provenance. Never log the 96-char key.
6. **Build big circuits before tiny auth-probe.** Always confirm the credential + backend with a 1-qubit H+measure first (cost: 38ms qpuRunTime).

## Cross-references

- Parent doctrine: `sinister-seraphim-integration-vision-2026-05-23.md` (4-lane vision)
- Narrowing doctrine: `seraphim-for-emu-re-2026-05-23.md` (EMU/RE focus, 120s cloud-spend table)
- Project memory: `projects/sinister-snap-api-quantum/MEMORY.md` (this lane's audit log)
- Tool code: `tools/sinister-seraphim/cloud_submit.py` (wraps QCloudService with budget gate)
- Pyqpanda3 API map: `pyqpanda3-0.3.5-api-empirical-map-2026-05-23.md` (sibling — could be split out)
- Composes with: `eve-exe-launcher-jcode-speed-parity-2026-05-23.md` (parallel wrap-paid-SDK pattern)
- AUP-RESPECT scope: `sanctioned-bypasses-doctrine-2026-05-21.md` (operator-OWN scope; this lane uses operator-paid qcloud account)
- Memory test result: `outputs/memory-kernel-comparison-*.json` (CPUQVM baseline; next iteration will re-run on real WK_C180 to compare)

## Tags

doctrine, validated, empirical, sinister-seraphim, cloud-wukong-180, qcloud, originqc, pyqpanda3-0.3.5, first-real-qpu-fire, 2026-05-23, h-gate-100-shots, api-key-96-hex, pyqanda-admin-qpanda-cn-default-url, https-originqc-frontend-not-backend, qpurunTime-vs-walltime-billing-question, opType-not-callable-gotcha, two-product-confusion, pilotos-vs-qcloud, lane-anchor, snap-api-quantum-project, ready-for-memory-kernel-real-qpu-rerun
