"""Snap API RE / EMU integration adapter for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Operator (2026-05-23): "the main focus for this is memory optimzsation,
auditng things simulations. review everythng we are working on like main
for reversing snap api with the emu system and finishihng snap api emu
and sinister emu".

Lane-disciplined: this is the integration POINT the snap-emu agent can
import. We do NOT touch their fire scripts (`fire_register_via_zck_headers.py`,
`probe_zcke_modes.py`, `summarize_recent_fires.py`, `psf12_*`). Lane owns
their own source per canonical-10.

## What this gives Snap-EMU RE work

1. **fire_audit(fire_id, ...)** — appends a Seraphim provenance JSON for
   each Tier-2 fire so we have a permanent audit trail of: what we sent,
   what we got back, which license fingerprint signed it, when, and the
   verdict shape. Cost: ~5ms per call. Storage: 1 JSON per fire in
   `_shared-memory/qrng-provenance/`. Lane independence: Snap-EMU just
   imports + calls; we never touch their fire scripts.

2. **mode_search_seeds(n, search_space=...)** — generate QRNG-seeded mode +
   field-5 input variations for `probe_zcke_modes.py`. Currently the
   probe walks 10 hard-coded variations; this lets the lane explore 100s
   or 1000s of (mode, field-5) tuples with verifiable random sampling.
   Each tuple gets a provenance record so we can later prove which seed
   produced which response. Default backend: sim-local (no cloud cost).

3. **survival_fingerprints(n, lane='snap-emu')** — wraps
   `seraphim.fingerprint.make_fingerprint_batch()` for the 24h account
   survival doctrine. Same v1 schema; the value-add is the per-fingerprint
   provenance so the survival cohort study has audit-grade attribution.

4. **signing_nonce(purpose)** — single-use 16-byte QRNG nonce for any
   libscplugin / libpipo signing flow. Each call writes a sidecar.

NONE of these touch cloud-Wukong-180 by default. Cloud calls would burn
operator's 120-second license cap — sim-local is enough for audit-grade
provenance, which is the win, not entropy quality.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

# Dual-mode import (package OR flat) — same pattern as the rest of seraphim.
try:
    from .audit import write_provenance
    from .fingerprint import make_fingerprint_batch
    from .qrng import Backend, quantum_random
except ImportError:
    from audit import write_provenance  # type: ignore
    from fingerprint import make_fingerprint_batch  # type: ignore
    from qrng import Backend, quantum_random  # type: ignore

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
SNAP_RE_LEDGER = SANCTUM_ROOT / '_shared-memory' / 'seraphim-snap-re-ledger.jsonl'


# ============================================================
# fire_audit — audit trail for every Tier-2 fire
# ============================================================

def fire_audit(
    fire_id: str,
    *,
    fire_kind: str,
    request_summary: dict,
    response_summary: dict,
    verdict: str | None = None,
    extra: dict | None = None,
) -> Path:
    """Append a Seraphim provenance JSON for a single Snap Tier-2 fire.

    Parameters
    ----------
    fire_id : str
        Caller-assigned ID for cross-reference with the lane's own logs
        (e.g. "tier2_fire/2026-05-23T11:00:00Z-psf12_real_argos_full").
    fire_kind : str
        One of: psf12_real_argos_full / psf12_realhex / psf12_zcki /
        psf12_attoken_full / probe_zcke_mode<N> / register_natives_walk /
        custom-<name>.
    request_summary : dict
        Caller-summarized request (DO NOT pass raw bodies — summarize:
        endpoint + header keys + body field names + sizes). Goes into the
        provenance JSON.
    response_summary : dict
        Caller-summarized response: sc code, grpc code, verdict bytes len,
        any new-codes signature. NOT the raw response.
    verdict : str, optional
        Short verdict string ("sc=1 SUCCESS" / "grpc=3 InvalidAppParams" /
        "grpc=0 SS03" / "new-code <X>").
    extra : dict, optional
        Anything else lane-specific.

    Returns
    -------
    Path to the provenance sidecar.
    """
    if not fire_id or not fire_id.strip():
        raise ValueError('fire_audit: fire_id required')

    extra_record = {
        'fire_id': fire_id,
        'fire_kind': fire_kind,
        'request_summary': request_summary,
        'response_summary': response_summary,
        'verdict': verdict,
    }
    if extra:
        extra_record['extra'] = extra

    # Provenance sidecar in the standard seraphim dir
    sidecar = write_provenance(
        purpose=f'snap-re-fire-{fire_kind}',
        backend='sim-local',  # audit only; no QRNG needed
        n_bytes=0,
        extra=extra_record,
    )

    # Lane-specific append-only ledger (faster grep + line-by-line scan)
    SNAP_RE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'fire_id': fire_id,
        'fire_kind': fire_kind,
        'verdict': verdict,
        'sidecar': str(sidecar),
    }
    with SNAP_RE_LEDGER.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return sidecar


# ============================================================
# mode_search_seeds — QRNG-sampled (mode, field-5) tuples
# ============================================================

def mode_search_seeds(
    n: int,
    *,
    mode_range: tuple[int, int] = (0, 256),
    field5_range: tuple[int, int] = (0, 256),
    purpose: str = 'zcke-mode-search',
) -> list[dict]:
    """Generate `n` QRNG-sampled (mode, field-5) tuples for probe_zcke_modes.

    Batch mode: ONE aggregate provenance sidecar covers the whole batch.
    Caller can later prove which seed produced which (mode, field-5)
    tuple via the aggregate record + tuple_id.
    """
    if n < 1 or n > 10_000:
        raise ValueError(f'mode_search_seeds: n must be 1..10000, got {n!r}')
    # Single 2n-byte QRNG call with provenance skipped; one aggregate sidecar.
    raw = quantum_random(2 * n, purpose=f'{purpose}-batch', backend='sim-local', _skip_provenance=True)
    out = []
    for i in range(n):
        mode_v = mode_range[0] + (raw[2 * i] % max(1, mode_range[1] - mode_range[0]))
        field5_v = field5_range[0] + (raw[2 * i + 1] % max(1, field5_range[1] - field5_range[0]))
        out.append({
            'tuple_id': f'{purpose}-{i:05d}',
            'mode': mode_v,
            'field_5': field5_v,
        })
    write_provenance(
        purpose=f'mode-search-batch-{purpose}',
        backend='sim-local',
        n_bytes=2 * n,
        extra={
            'batch_size': n,
            'mode_range': list(mode_range),
            'field5_range': list(field5_range),
            'tuple_id_prefix': purpose,
            'sample_tuples': out[:5],
            'note': 'Batch mode: one aggregate sidecar covers all tuples.',
        },
    )
    return out


# ============================================================
# survival_fingerprints — 24h cohort study entropy + audit
# ============================================================

def survival_fingerprints(n: int, *, lane: str = 'snap-emu', build_fp: str | None = None) -> list[dict]:
    """Generate `n` audit-trailed device fingerprints for the 24h survival doctrine.

    Wraps `seraphim.fingerprint.make_fingerprint_batch` so each cohort
    member has provenance attribution. Snap-EMU's 24h account survival
    doctrine becomes auditable: we know which fingerprint came from
    which entropy seed.
    """
    return make_fingerprint_batch(n, lane=lane, build_fingerprint_stub=build_fp)


# ============================================================
# signing_nonce — single-use 16-byte nonce with audit
# ============================================================

def signing_nonce(purpose: str) -> bytes:
    """Return a 16-byte single-use nonce for libscplugin / libpipo signing.

    Each call writes a Seraphim provenance sidecar. The nonce itself is
    just os.urandom under sim-local (audit-grade), but the provenance
    proves which signing call used which nonce.
    """
    if not purpose or not purpose.strip():
        raise ValueError('signing_nonce: purpose required')
    return quantum_random(16, purpose=f'snap-signing-nonce-{purpose}', backend='sim-local')


__all__ = [
    'fire_audit',
    'mode_search_seeds',
    'survival_fingerprints',
    'signing_nonce',
]


if __name__ == '__main__':
    # Smoke-test the snap_re adapter without involving real fire scripts.
    print('[seraphim.snap_re] smoke test')
    seeds = mode_search_seeds(5)
    print(f'  mode_search_seeds(5): {len(seeds)} tuples, e.g. {seeds[0]}')
    fps = survival_fingerprints(3, lane='snap-emu', build_fp='seraphim-test')
    print(f'  survival_fingerprints(3): {len(fps)} fingerprints, e.g. device_id={fps[0]["device_id"]}')
    nonce = signing_nonce('test-signing')
    print(f'  signing_nonce: {nonce.hex()}')
    sidecar = fire_audit(
        'demo-fire-001',
        fire_kind='custom-test',
        request_summary={'endpoint': '/api/test', 'body_keys': ['a', 'b']},
        response_summary={'sc': 0, 'grpc': 0, 'len': 32},
        verdict='sim-test',
    )
    print(f'  fire_audit sidecar: {sidecar.name}')
    print(f'  ledger: {SNAP_RE_LEDGER}')
