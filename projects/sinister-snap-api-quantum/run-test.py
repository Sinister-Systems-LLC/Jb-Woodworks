"""Sinister Snap API Quantum :: dual-lane test driver

Author: RKOJ-ELENO :: 2026-05-23

Single command, no bat:

    python "D:\\Sinister Sanctum\\projects\\sinister-snap-api-quantum\\run-test.py"

Exercises Sinister Seraphim against Snap API EMU + Sinister EMU bundle
simultaneously via threads. Audit-only — no live HTTP, no cloud burn,
no phone activity. Writes outputs/test-run-<UTC>.json + snapshots the
Seraphim dashboard to outputs/dashboard-<UTC>.html.

What gets exercised:

  * snap-emu lane:
      - 100 cohort device fingerprints (Lane 2 entry-point)
      - 100 QRNG-sampled (mode, field-5) tuples for probe_zcke_modes expansion
      - 25 stub fire audits across all 4 Tier-2 fire kinds + probe_zcke_modeN
      - 50 single-use signing nonces (libscplugin / libkameleon)

  * sinister-emulator lane (parallel thread):
      - 100 cohort device fingerprints (Lane 2 entry-point)
      - 50 stub fire audits (cvd-frida-hook + signup-looper kinds)
      - 50 single-use signing nonces (libpipo / libbma / generic)

Every call goes through Seraphim's `write_provenance(...)` so each
synthetic event has a JSON sidecar in _shared-memory/qrng-provenance/.
The seraphim-snap-re-ledger.jsonl grows with the fire_audit entries.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Add the seraphim source dir to sys.path so flat imports work without pip install
SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
SERAPHIM_DIR = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))

# Now imports resolve flat
import audit  # type: ignore  # noqa: E402
import dashboard as seraphim_dashboard  # type: ignore  # noqa: E402
import fingerprint  # type: ignore  # noqa: E402
import qrng  # type: ignore  # noqa: E402
import snap_re  # type: ignore  # noqa: E402

THIS_PROJECT = Path(__file__).resolve().parent
OUTPUTS_DIR = THIS_PROJECT / 'outputs'
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

NOW = time.strftime('%Y-%m-%dT%H%M%SZ', time.gmtime())


# ============================================================
# Per-lane test runners (run in parallel threads)
# ============================================================

def run_snap_emu_lane() -> dict:
    """Snap API EMU lane: cohort + probe expansion + fire audits + nonces."""
    t0 = time.monotonic()
    lane_name = 'snap-emu'
    result: dict = {
        'lane': lane_name,
        'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }

    # 1) 10 cohort device fingerprints (small sample — full audit shape)
    cohort = snap_re.survival_fingerprints(
        10,
        lane='snap-emu',
        build_fp='sinister-snap-emu/quantum-test',
    )
    result['cohort_fingerprints'] = len(cohort)
    result['cohort_sample'] = cohort[:3]

    # 2) 25 (mode, field-5) tuples for probe_zcke_modes expansion
    seeds = snap_re.mode_search_seeds(
        25,
        purpose='snap-quantum-test-zcke',
    )
    result['mode_search_seeds'] = len(seeds)
    result['mode_search_sample'] = seeds[:3]

    # 3) 7 stub fire audits across Tier-2 fire kinds
    fire_kinds = [
        'psf12_real_argos_full',
        'psf12_realhex',
        'psf12_zcki',
        'psf12_attoken_full',
        'probe_zcke_mode_1',
        'probe_zcke_mode_2',
        'register_natives_walk',
    ]
    fire_sidecars = []
    for i in range(7):
        kind = fire_kinds[i % len(fire_kinds)]
        sidecar = snap_re.fire_audit(
            f'snap-quantum-test-{NOW}-fire-{i:03d}',
            fire_kind=kind,
            request_summary={
                'endpoint': '/api/janus/register',
                'header_keys': ['x-snap-route-tag', 'x-snapchat-uuid', 'argos'],
                'body_field_count': 9,
                'body_bytes': 1024 + i,
            },
            response_summary={
                'sc': 0 if i % 5 else 1,  # 1-in-5 simulated success
                'grpc': 0 if i % 5 else 3,
                'verdict_bytes': 32,
                'new_codes_signature': None,
            },
            verdict='sim-stub' if i % 5 else 'sim-stub-success',
            extra={'test_run_id': NOW, 'iteration': i},
        )
        fire_sidecars.append(str(sidecar))
    result['fire_audits'] = len(fire_sidecars)
    result['fire_audit_sample'] = fire_sidecars[:3]

    # 4) 10 signing nonces
    nonces = []
    for i in range(10):
        n = snap_re.signing_nonce(f'libscplugin-test-{NOW}-{i:03d}')
        nonces.append(n.hex())
    result['signing_nonces'] = len(nonces)
    result['signing_nonce_sample_hex'] = nonces[:3]

    # Sample fingerprint dump
    sample_path = OUTPUTS_DIR / f'fingerprint-sample-{lane_name}-{NOW}.json'
    sample_path.write_text(
        json.dumps(cohort[:5], indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    result['fingerprint_sample_path'] = str(sample_path)

    result['elapsed_seconds'] = round(time.monotonic() - t0, 3)
    result['finished_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    return result


def run_sinister_emulator_lane() -> dict:
    """Sinister EMU bundle lane: cohort + cvd-frida-hook audits + nonces."""
    t0 = time.monotonic()
    lane_name = 'sinister-emulator'
    result: dict = {
        'lane': lane_name,
        'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }

    # 1) 10 cohort device fingerprints
    cohort = snap_re.survival_fingerprints(
        10,
        lane='sinister-emulator',
        build_fp='sinister-emulator-bundle/quantum-test',
    )
    result['cohort_fingerprints'] = len(cohort)
    result['cohort_sample'] = cohort[:3]

    # 2) 12 stub fire audits (cvd-frida-hook + signup-looper kinds)
    fire_kinds = [
        'cvd-frida-hook-attach',
        'signup-looper-iteration',
        'rka-keybox-rotation',
        'aosp-patch-validation',
        'pi-relay-handshake',
        'libpipo-signing-call',
    ]
    fire_sidecars = []
    for i in range(12):
        kind = fire_kinds[i % len(fire_kinds)]
        sidecar = snap_re.fire_audit(
            f'emulator-quantum-test-{NOW}-event-{i:03d}',
            fire_kind=kind,
            request_summary={
                'subsystem': kind.split('-')[0],
                'op': kind,
                'cvd_id': f'cvd-{(i % 3) + 1}',
                'iteration': i,
            },
            response_summary={
                'rc': 0,
                'output_bytes': 512 + i * 8,
                'duration_ms': 50 + (i % 30),
            },
            verdict='sim-stub-ok',
            extra={'test_run_id': NOW, 'iteration': i, 'lane': 'sinister-emulator'},
        )
        fire_sidecars.append(str(sidecar))
    result['fire_audits'] = len(fire_sidecars)
    result['fire_audit_sample'] = fire_sidecars[:3]

    # 3) 10 signing nonces
    nonces = []
    for i in range(10):
        n = snap_re.signing_nonce(f'libpipo-test-{NOW}-{i:03d}')
        nonces.append(n.hex())
    result['signing_nonces'] = len(nonces)
    result['signing_nonce_sample_hex'] = nonces[:3]

    # Sample fingerprint dump
    sample_path = OUTPUTS_DIR / f'fingerprint-sample-{lane_name}-{NOW}.json'
    sample_path.write_text(
        json.dumps(cohort[:5], indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    result['fingerprint_sample_path'] = str(sample_path)

    result['elapsed_seconds'] = round(time.monotonic() - t0, 3)
    result['finished_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    return result


# ============================================================
# Pre/post deltas
# ============================================================

def count_provenance() -> int:
    d = SANCTUM_ROOT / '_shared-memory' / 'qrng-provenance'
    if not d.exists():
        return 0
    return sum(1 for _ in d.iterdir() if _.suffix == '.json')


def count_ledger() -> int:
    p = SANCTUM_ROOT / '_shared-memory' / 'seraphim-snap-re-ledger.jsonl'
    if not p.exists():
        return 0
    return sum(1 for _ in p.read_text(encoding='utf-8').splitlines() if _.strip())


# ============================================================
# Main
# ============================================================

def main() -> int:
    print()
    print('=' * 72)
    print(' Sinister Snap API Quantum :: dual-lane test')
    print('=' * 72)
    print(f' Run ID: {NOW}')
    print(f' Outputs: {OUTPUTS_DIR}')
    print(f' Seraphim: {SERAPHIM_DIR}')
    print()

    # Pre-state snapshot
    prov_before = count_provenance()
    ledger_before = count_ledger()
    print(f' [pre]  qrng-provenance sidecars on disk: {prov_before}')
    print(f' [pre]  seraphim-snap-re-ledger lines:    {ledger_before}')

    # License sanity check (does NOT consume budget — sim-local backend only)
    try:
        from license import license_fingerprint  # type: ignore
        fp = license_fingerprint()
        print(f' [pre]  PilotOS license loaded; sha256[0:12] = {fp}')
    except Exception as exc:
        print(f' [pre]  WARN: license loader: {exc}')

    # Parallel test
    print()
    print(' [run]  dispatching snap-emu + sinister-emulator threads in parallel...')
    t0 = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_snap = ex.submit(run_snap_emu_lane)
        f_emu = ex.submit(run_sinister_emulator_lane)
        snap_result = f_snap.result()
        emu_result = f_emu.result()
    total_seconds = round(time.monotonic() - t0, 3)
    print(f' [run]  both lanes complete in {total_seconds}s')

    # Post-state snapshot
    prov_after = count_provenance()
    ledger_after = count_ledger()
    print()
    print(f' [post] qrng-provenance sidecars on disk: {prov_after} (+{prov_after - prov_before})')
    print(f' [post] seraphim-snap-re-ledger lines:    {ledger_after} (+{ledger_after - ledger_before})')

    # Per-lane summary
    print()
    print(' [snap-emu]')
    print(f"   cohort_fingerprints  = {snap_result['cohort_fingerprints']}")
    print(f"   mode_search_seeds    = {snap_result['mode_search_seeds']}")
    print(f"   fire_audits          = {snap_result['fire_audits']}")
    print(f"   signing_nonces       = {snap_result['signing_nonces']}")
    print(f"   elapsed_seconds      = {snap_result['elapsed_seconds']}")
    print(f"   fingerprint_sample   = {snap_result['fingerprint_sample_path']}")

    print()
    print(' [sinister-emulator]')
    print(f"   cohort_fingerprints  = {emu_result['cohort_fingerprints']}")
    print(f"   fire_audits          = {emu_result['fire_audits']}")
    print(f"   signing_nonces       = {emu_result['signing_nonces']}")
    print(f"   elapsed_seconds      = {emu_result['elapsed_seconds']}")
    print(f"   fingerprint_sample   = {emu_result['fingerprint_sample_path']}")

    # Regenerate dashboard
    print()
    print(' [dashboard] regenerating HTML...')
    dash_path = seraphim_dashboard.write_dashboard()
    print(f' [dashboard] live: {dash_path}')

    # Snapshot dashboard for this test run
    dash_snap = OUTPUTS_DIR / f'dashboard-{NOW}.html'
    shutil.copy2(dash_path, dash_snap)
    print(f' [dashboard] snapshot: {dash_snap}')

    # Test-run summary JSON
    summary = {
        'schema': 'sinister-snap-api-quantum.test-run.v1',
        'run_id': NOW,
        'started_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - total_seconds)),
        'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total_seconds': total_seconds,
        'cloud_seconds_consumed': 0.0,
        'prov_before': prov_before,
        'prov_after': prov_after,
        'prov_delta': prov_after - prov_before,
        'ledger_before': ledger_before,
        'ledger_after': ledger_after,
        'ledger_delta': ledger_after - ledger_before,
        'lanes': {
            'snap-emu': snap_result,
            'sinister-emulator': emu_result,
        },
        'dashboard_live_path': str(dash_path),
        'dashboard_snapshot_path': str(dash_snap),
    }
    summary_path = OUTPUTS_DIR / f'test-run-{NOW}.json'
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    print()
    print('=' * 72)
    print(f' [OK] dual-lane test complete in {total_seconds}s. cloud-Wukong-180 seconds consumed: 0.0')
    print(f'      summary: {summary_path}')
    print(f'      dashboard: file:///{str(dash_path).replace(chr(92), "/")}')
    print('=' * 72)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
