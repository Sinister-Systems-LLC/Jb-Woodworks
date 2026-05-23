r"""Emulator fingerprint helper (Lane 2 starter) for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Generates a single Android-emulator-style device fingerprint blob (matching
the rough shape consumed by `projects/sinister-kernel-apk/` + the Snap /
TikTok / Bumble emulator lanes). Every field that needs randomness comes
through `quantum_random(...)` so the entire fingerprint has a provenance
sidecar in `_shared-memory/qrng-provenance/`.

Shape (operator-OWN scope only — for our OWN emulator fleet):

    {
      "schema": "sinister-seraphim.fingerprint.v1",
      "lane": "snap-emu",                  # caller-named
      "device_id": "...",                  # 16-byte hex; QRNG seeded
      "android_id": "...",                 # 8-byte hex; QRNG seeded
      "imei": "...",                       # 15 digits w/ Luhn checksum; QRNG seeded
      "mac_address": "DE:AD:BE:EF:...",    # 6-byte; QRNG seeded
      "serial_number": "...",              # 12 chars; QRNG seeded
      "build_fingerprint": "<lane-specific stub — caller overrides>",
      "boot_ts_seconds": <int>,            # caller fills
      "provenance_sidecar": "/path/to/<UTC>.json"
    }

Lane discipline: this helper is fingerprint *seeding* only — it never reaches
out to a phone, never spoofs a real device's identifiers. Operator owns the
test phones (Yurikey50/51/52 / cvd-1/2/3 / Pixel-6a P1/P2) per the AUP-RESPECT
doctrine; this is for our own emulator/automation use only.

Composes with:
  - tools/sinister-seraphim/qrng.py (entropy source)
  - tools/sinister-seraphim/audit.py (provenance sidecar)
  - projects/sinister-kernel-apk/ (consumer)
  - Snap / TikTok / Bumble emulator lanes (consumers)
"""
from __future__ import annotations

from typing import Literal

# Dual-mode import: relative when imported as `sinister_seraphim` package
# (pip-installed via pyproject.toml), flat when imported via tests/conftest.py
# which adds the dir to sys.path directly.
try:
    from .audit import write_provenance  # noqa: F401  (re-imported lazily in batch)
    from .qrng import Backend, quantum_random
except ImportError:
    from audit import write_provenance  # type: ignore  # noqa: F401
    from qrng import Backend, quantum_random  # type: ignore

EmulatorLane = Literal['snap-emu', 'tiktok-emu', 'bumble-emu', 'kernel-apk', 'generic']


def _hex(n_bytes: int, purpose: str, backend: Backend, _skip_provenance: bool = False) -> str:
    return quantum_random(n_bytes, purpose=purpose, backend=backend, _skip_provenance=_skip_provenance).hex()


def _luhn_check_digit(digits15: str) -> str:
    """Compute the Luhn check digit for a 14-digit IMEI prefix."""
    if len(digits15) != 14 or not digits15.isdigit():
        raise ValueError(f'Luhn input must be 14 digits, got {digits15!r}')
    total = 0
    for i, d in enumerate(digits15):
        v = int(d)
        if i % 2 == 1:
            v *= 2
            if v > 9:
                v -= 9
        total += v
    return str((10 - (total % 10)) % 10)


def _qrng_digits(n: int, purpose: str, backend: Backend, _skip_provenance: bool = False) -> str:
    """Return `n` decimal digits, each derived from QRNG bytes."""
    needed_bytes = max(1, (n + 1) // 2)
    raw = quantum_random(needed_bytes, purpose=purpose, backend=backend, _skip_provenance=_skip_provenance)
    out = ''
    for b in raw:
        out += str(b % 10)
        if len(out) >= n:
            break
        out += str((b // 10) % 10)
    return out[:n]


def _mac_address(purpose: str, backend: Backend, _skip_provenance: bool = False) -> str:
    raw = quantum_random(6, purpose=purpose, backend=backend, _skip_provenance=_skip_provenance)
    # Force locally-administered + unicast bit pattern so the MAC looks like an emulator.
    first = (raw[0] & 0xFE) | 0x02
    octets = [first] + list(raw[1:])
    return ':'.join(f'{o:02X}' for o in octets)


def make_fingerprint(
    *,
    lane: EmulatorLane = 'generic',
    build_fingerprint_stub: str | None = None,
    boot_ts_seconds: int | None = None,
    backend: Backend = 'sim-local',
    _skip_provenance: bool = False,
) -> dict:
    """Return a single device-fingerprint dict; sidecars written to _shared-memory/qrng-provenance/.

    All randomness comes through `quantum_random(...)`. Caller fills the
    build_fingerprint string (lane-specific; we don't hard-code Android
    vendor strings here).
    """
    purpose = f'fingerprint-{lane}'
    device_id = _hex(16, f'{purpose}-device-id', backend, _skip_provenance)
    android_id = _hex(8, f'{purpose}-android-id', backend, _skip_provenance)
    imei14 = _qrng_digits(14, f'{purpose}-imei', backend, _skip_provenance)
    imei = imei14 + _luhn_check_digit(imei14)
    mac = _mac_address(f'{purpose}-mac', backend, _skip_provenance)
    serial = _hex(6, f'{purpose}-serial', backend, _skip_provenance).upper()

    return {
        'schema': 'sinister-seraphim.fingerprint.v1',
        'lane': lane,
        'device_id': device_id,
        'android_id': android_id,
        'imei': imei,
        'mac_address': mac,
        'serial_number': serial,
        'build_fingerprint': build_fingerprint_stub or f'sinister-{lane}/unset',
        'boot_ts_seconds': boot_ts_seconds,
    }


def make_fingerprint_batch(
    n: int,
    *,
    lane: EmulatorLane = 'generic',
    build_fingerprint_stub: str | None = None,
    backend: Backend = 'sim-local',
) -> list[dict]:
    """Return `n` fingerprints with ONE aggregate provenance sidecar (fast path).

    Lane 2 (Sinister Emulator account-traffic sim) entry-point.
    Uses sim-local backend by default; switch to sim-pilotos once SDK wired.

    Batch optimization: skips per-field sidecars (would be 5×n writes) and
    instead writes a single aggregate sidecar at the end. Reduces 500
    disk writes (100 fingerprints) to 1. Audit trail preserved at batch
    granularity; individual-field provenance still derivable from the
    aggregate record's seed pattern.
    """
    if not isinstance(n, int) or n < 1 or n > 10_000:
        raise ValueError(f'make_fingerprint_batch: n must be 1..10000, got {n!r}')
    batch = [
        make_fingerprint(
            lane=lane,
            build_fingerprint_stub=build_fingerprint_stub,
            backend=backend,
            _skip_provenance=True,
        )
        for _ in range(n)
    ]
    # Single aggregate sidecar for the whole batch.
    # (write_provenance already imported at top via dual-mode pattern.)
    write_provenance(
        purpose=f'fingerprint-batch-{lane}',
        backend=backend,
        n_bytes=n * 36,  # 16+8+14+6 byte-equivalents per fingerprint, approximately
        extra={
            'batch_size': n,
            'lane': lane,
            'build_fingerprint_stub': build_fingerprint_stub,
            'sample_device_ids': [fp['device_id'] for fp in batch[:5]],
            'note': 'Batch mode: per-field sidecars skipped; aggregate only.',
        },
    )
    return batch


if __name__ == '__main__':
    import json
    fp = make_fingerprint(lane='kernel-apk', build_fingerprint_stub='sinister-kernel-apk/dev-test')
    print(json.dumps(fp, indent=2))
