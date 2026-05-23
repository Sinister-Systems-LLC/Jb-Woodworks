<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sinister Snap API Quantum :: dual-lane test environment

> **Operator (2026-05-23):** *"ok lets test this for snap api emu and sinister emu bndle at same time. prepare the test ... add evreything to a folder called sinister snap api quantum. add evberything here in prepartion for the test so that we have a test env."*

## What this project is

The dedicated test environment that exercises **Sinister Seraphim** (the quantum-compute application layer at `D:\Sinister Sanctum\tools\sinister-seraphim\`) against **two sibling lanes simultaneously**:

1. **Snap API EMU** (`D:\Sinister Sanctum\projects\sinister-snap-emu\source\snap-api-prototype\`) — Tier-2 fire pipeline, `kiib.zck.e` → `kiib.zck.i` chain reversal, libscplugin signing, 24h survival doctrine
2. **Sinister Emulator Bundle** (`D:\Sinister Sanctum\projects\sinister-emulator-bundle\source\`) — shared emulator core, cvd-frida-hooks, RKA signing, signup looper

The test **never touches** the real fire pipeline (no live HTTP POST to Snap servers, no cvd-1 phone activity, no RKA daemon calls). It exercises the Seraphim integration layer end-to-end with audit-only stub fires.

## Why a separate project

- **Lane isolation**: this test env doesn't modify snap-emu or emulator-bundle source. It imports from them read-only; outputs land here.
- **Cloud-budget protection**: every test call is `backend='sim-local'` — zero cloud-Wukong-180 seconds burned. The 120s operator cap stays intact.
- **Reproducibility**: a fresh run regenerates `outputs/` deterministically (modulo intentional QRNG-seeded randomness, which has provenance attribution).

## Run it

Single command, no bat:

```
python "D:\Sinister Sanctum\projects\sinister-snap-api-quantum\run-test.py"
```

What it does (in ~5-10 seconds):

1. **Parallel cohort generation** — 100 device fingerprints for snap-emu lane + 100 for sinister-emulator lane, simultaneously via threads.
2. **`probe_zcke_modes` expansion** — 100 QRNG-sampled (mode, field-5) tuples for the Snap RE pipeline, replacing the 10 hard-coded variations.
3. **Audit-stub fire batch** — 25 stub fire-audit entries per lane covering all 4 Tier-2 fire kinds (psf12_real_argos_full / _realhex / _zcki / _attoken_full) + probe_zcke variants. Stub responses are deterministic so the test is reproducible.
4. **Signing-nonce batch** — 50 single-use nonces per lane covering libscplugin / libpipo / libbma / libkameleon signing oracles.
5. **Dashboard regen** — rewrites `_shared-memory/dashboards/seraphim.html` with the cumulative ledger.
6. **Summary** — prints per-lane counts + provenance sidecar count delta + dashboard path.

## Outputs

Everything written by the test lands at:

| Path | What |
|---|---|
| `outputs/test-run-<UTC>.json` | One JSON per test run with all counters, lane breakdowns, timing, sidecar paths |
| `outputs/dashboard-<UTC>.html` | Snapshot of the Seraphim dashboard at test end |
| `outputs/fingerprint-sample-<lane>-<UTC>.json` | Sample of the cohort fingerprints (first 5 per lane) |
| `_shared-memory/qrng-provenance/<UTC>.json` | Standard Seraphim provenance sidecars (fleet-shared, not test-private) |
| `_shared-memory/seraphim-snap-re-ledger.jsonl` | Append-only fire-audit ledger (fleet-shared) |

## Cold-start (per-agent)

See `CLAUDE.md` next to this file.

## What this project NEVER does

- Real HTTP POST to Snap, TikTok, Bumble, or any third-party service
- Touch cvd-1 phone / RKA daemon / frida / Snap install
- Spend cloud-Wukong-180 seconds (sim-local only)
- Modify snap-emu or emulator-bundle source (read-only access via sys.path)

## Project lane

- **Slug**: `sinister-snap-api-quantum`
- **Display**: `Sinister Snap API Quantum`
- **Branch convention**: `agent/sinister-snap-api-quantum/<topic>`
- **Heartbeat**: `_shared-memory/heartbeats/sinister-snap-api-quantum.json`
- **PROGRESS**: `_shared-memory/PROGRESS/Sinister Snap API Quantum.md`
- **Resume-points**: `_shared-memory/resume-points/Sinister Snap API Quantum/<UTC>.json`
- **Accent**: purple (default fleet)
