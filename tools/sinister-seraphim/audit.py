"""Provenance audit sidecar writer for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Every quantum call (QRNG, simulation, circuit submission) writes a JSON
sidecar to `_shared-memory/qrng-provenance/<UTC>.json` proving:

  - When (UTC timestamp)
  - What circuit (OriginIR or pyqpanda3 representation)
  - Where (local sim vs cloud Wukong-180)
  - How many shots / bytes generated
  - Caller purpose ("kernel-apk-fingerprint-spoof", "test-suite", etc.)
  - License fingerprint (NOT the raw license — sha256[0:12] for traceability)

This IS the operator-requested "audit / super-local-agent" value-add: a
verifiable chain showing every randomness / quantum-result we used in
the fleet has provenance.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
PROVENANCE_DIR = SANCTUM_ROOT / '_shared-memory' / 'qrng-provenance'


def write_provenance(
    *,
    purpose: str,
    backend: str,
    n_bytes: int | None = None,
    n_shots: int | None = None,
    circuit_repr: str | None = None,
    extra: dict | None = None,
) -> Path:
    """Write a provenance sidecar and return its path.

    Parameters
    ----------
    purpose : str
        Operator-readable string ("kernel-apk-fingerprint-spoof",
        "letstext-signing-nonce", "brain-recall-experiment", etc.).
        Required — empty purpose rejected.
    backend : {'sim-local', 'sim-pilotos', 'cloud-wukong-180'}
        Where the quantum work ran.
    n_bytes : int, optional
        Bytes of entropy generated (QRNG calls).
    n_shots : int, optional
        Measurement shots (circuit-submission calls).
    circuit_repr : str, optional
        OriginIR / pyqpanda3 textual circuit representation.
    extra : dict, optional
        Caller-specific metadata. Must be JSON-serializable.
    """
    if not purpose or not purpose.strip():
        raise ValueError('write_provenance: purpose is required')
    if backend not in ('sim-local', 'sim-pilotos', 'cloud-wukong-180'):
        raise ValueError(f'write_provenance: unknown backend {backend!r}')

    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)

    now_utc = time.strftime('%Y-%m-%dT%H%M%SZ', time.gmtime())
    record_id = uuid.uuid4().hex[:12]
    filename = f'{now_utc}-{record_id}.json'
    path = PROVENANCE_DIR / filename

    record: dict = {
        'schema': 'sinister-seraphim.provenance.v1',
        'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'record_id': record_id,
        'purpose': purpose.strip(),
        'backend': backend,
    }
    if n_bytes is not None:
        record['n_bytes'] = n_bytes
    if n_shots is not None:
        record['n_shots'] = n_shots
    if circuit_repr is not None:
        record['circuit_repr'] = circuit_repr
    if extra:
        record['extra'] = extra

    # License fingerprint for traceability (optional — skip if loader missing).
    # Dual-import (package vs flat) — tolerant of either layout.
    record['license_fp_sha256_12'] = None
    try:
        try:
            from .license import license_fingerprint
        except ImportError:
            from license import license_fingerprint  # type: ignore
        record['license_fp_sha256_12'] = license_fingerprint()
    except Exception:
        pass

    path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    return path


if __name__ == '__main__':
    p = write_provenance(
        purpose='self-test',
        backend='sim-local',
        n_bytes=0,
        extra={'note': 'audit.py CLI smoke-test'},
    )
    print(f'[sinister-seraphim.audit] wrote {p}')
