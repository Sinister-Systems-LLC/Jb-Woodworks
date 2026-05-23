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

## Status

| Component | Status |
|---|---|
| README.md (this) | ✅ shipped 2026-05-23 |
| `license.py` (loader from vault) | 📋 next |
| `qrng.py` (entropy daemon — Lane 1 starter) | 📋 next |
| `audit.py` (provenance sidecar writer) | 📋 next |
| FastAPI surface (`server.py` on :5079) | 📋 |
| First consumer: kernel-apk fingerprint seeding | 📋 cross-lane |
| First consumer: Sinister Emulator account-sim | 📋 cross-lane |
| Brain entry: `pilotos-integration-vision-2026-05-23.md` | 📋 next |
| Cloud Wukong-180 path (opt-in per-call) | ⏸ deferred (cost gate) |

## How to use (post-skeleton ship — coming next commit)

```python
from sinister_quantum import quantum_random, audit_trail

# Lane 1 starter: 32 bytes of quantum entropy with full provenance
seed_bytes = quantum_random(32, purpose="kernel-apk-fingerprint-spoof")
# -> writes _shared-memory/qrng-provenance/<UTC>.json with circuit + measurement
```

```python
from sinister_quantum import emulator_fingerprint_batch

# Lane 2 starter: 1000 fingerprints with QRNG-seeded entropy
fingerprints = emulator_fingerprint_batch(
    n=1000,
    lane="snap-emu",
    use_cloud=False,  # local sim default
)
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
