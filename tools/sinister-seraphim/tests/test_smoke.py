"""Smoke tests for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Run via: `pytest tools/sinister-seraphim/tests/ -v`

The conftest.py adjacent puts tools/sinister-seraphim/ on sys.path so
the modules import flat (qrng, audit, fingerprint, license) without
requiring `pip install -e` first.
"""
from __future__ import annotations

import json

import pytest

import audit  # noqa: E402
import fingerprint  # noqa: E402
import qrng  # noqa: E402


def test_quantum_random_sim_local_returns_bytes():
    """qrng.quantum_random(N, backend='sim-local') returns N bytes."""
    data = qrng.quantum_random(16, purpose='pytest-smoke', backend='sim-local')
    assert isinstance(data, bytes)
    assert len(data) == 16


def test_quantum_random_rejects_out_of_range():
    """qrng.quantum_random raises ValueError for out-of-range n_bytes."""
    with pytest.raises(ValueError):
        qrng.quantum_random(0, purpose='pytest', backend='sim-local')
    with pytest.raises(ValueError):
        qrng.quantum_random(5000, purpose='pytest', backend='sim-local')


def test_quantum_random_pilotos_not_implemented():
    """sim-pilotos backend is documented placeholder until operator extracts SDK."""
    with pytest.raises(NotImplementedError):
        qrng.quantum_random(8, purpose='pytest', backend='sim-pilotos')


def test_quantum_random_cloud_not_implemented():
    """cloud-wukong-180 backend is documented placeholder (cost-gated)."""
    with pytest.raises(NotImplementedError):
        qrng.quantum_random(8, purpose='pytest', backend='cloud-wukong-180')


def test_write_provenance_creates_sidecar():
    """audit.write_provenance writes a JSON sidecar."""
    p = audit.write_provenance(
        purpose='pytest-smoke',
        backend='sim-local',
        n_bytes=16,
        extra={'test': True},
    )
    assert p.exists()
    rec = json.loads(p.read_text(encoding='utf-8'))
    assert rec['schema'] == 'sinister-seraphim.provenance.v1'
    assert rec['purpose'] == 'pytest-smoke'
    assert rec['backend'] == 'sim-local'
    assert rec['n_bytes'] == 16
    assert rec['extra'] == {'test': True}


def test_write_provenance_rejects_empty_purpose():
    """audit.write_provenance refuses empty purpose."""
    with pytest.raises(ValueError):
        audit.write_provenance(purpose='', backend='sim-local')
    with pytest.raises(ValueError):
        audit.write_provenance(purpose='   ', backend='sim-local')


def test_write_provenance_rejects_unknown_backend():
    """audit.write_provenance refuses unknown backend."""
    with pytest.raises(ValueError):
        audit.write_provenance(purpose='pytest', backend='not-a-backend')


def test_make_fingerprint_shape():
    """fingerprint.make_fingerprint returns the documented v1 shape."""
    fp = fingerprint.make_fingerprint(lane='kernel-apk', build_fingerprint_stub='pytest/v0')
    assert fp['schema'] == 'sinister-seraphim.fingerprint.v1'
    assert fp['lane'] == 'kernel-apk'
    assert len(fp['device_id']) == 32   # 16 bytes -> 32 hex chars
    assert len(fp['android_id']) == 16  # 8 bytes -> 16 hex chars
    assert len(fp['imei']) == 15        # 14 digits + 1 Luhn check
    assert fp['imei'].isdigit()
    assert fp['mac_address'].count(':') == 5
    assert fp['build_fingerprint'] == 'pytest/v0'
    # MAC should have locally-administered bit set
    first_octet = int(fp['mac_address'].split(':')[0], 16)
    assert (first_octet & 0x02) == 0x02


def test_luhn_check_digit():
    """fingerprint._luhn_check_digit matches a known test vector."""
    # Known IMEI: 35-209900-176148-1 (Luhn check = 1)
    assert fingerprint._luhn_check_digit('35209900176148') == '1'
    # Another known: 49-015420-323751-8
    assert fingerprint._luhn_check_digit('49015420323751') == '8'


def test_make_fingerprint_batch_returns_distinct():
    """fingerprint.make_fingerprint_batch returns n entries, each distinct."""
    batch = fingerprint.make_fingerprint_batch(5, lane='snap-emu')
    assert len(batch) == 5
    ids = {fp['device_id'] for fp in batch}
    assert len(ids) == 5  # QRNG collisions vanishingly unlikely


def test_make_fingerprint_batch_rejects_out_of_range():
    """fingerprint.make_fingerprint_batch refuses n < 1 or > 10_000."""
    with pytest.raises(ValueError):
        fingerprint.make_fingerprint_batch(0)
    with pytest.raises(ValueError):
        fingerprint.make_fingerprint_batch(10_001)
