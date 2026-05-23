r"""Quantum-random-bytes entry-point for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

`quantum_random(n_bytes, purpose=..., backend='sim-local')` — the Lane 1
starter. Generates `n_bytes` of entropy and writes a provenance sidecar.

Backends:

  - 'sim-local' (default): uses `os.urandom` with a provenance-only note
    indicating the V4.2 sim is not yet wired in. ZERO quantum-class
    randomness; the value-add is the audit trail. Operator can flip
    individual call sites to 'sim-pilotos' once the PilotOS sim is
    extracted from `Desktop\QPilotos-V4.2\python_simulator.tar.gz`.

  - 'sim-pilotos': calls into the local PilotOS python_simulator (not
    yet wired — operator must extract the SDK first; placeholder raises
    NotImplementedError until wired).

  - 'cloud-wukong-180': submits a 16-qubit measurement circuit to the
    Wukong-180 cloud QPU via pyqpanda3. Costs Wukong tier credits;
    opt-in per call. Not yet wired — placeholder raises
    NotImplementedError.

This module DOES NOT shell out to the cloud unless backend='cloud-wukong-180'
AND the cloud path is wired. The default backend is intentionally local +
classical with audit-only value so the first integration ships safely.
"""
from __future__ import annotations

import os
from typing import Literal

# Dual-mode import: relative when imported as `sinister_seraphim` package,
# flat when imported via tests/conftest.py (hyphen dir on sys.path).
try:
    from .audit import write_provenance
    from .license import LicenseError, get_license
except ImportError:
    from audit import write_provenance  # type: ignore
    from license import LicenseError, get_license  # type: ignore

Backend = Literal['sim-local', 'sim-pilotos', 'cloud-wukong-180']


def quantum_random(
    n_bytes: int,
    *,
    purpose: str,
    backend: Backend = 'sim-local',
) -> bytes:
    """Return `n_bytes` of entropy with a provenance sidecar written.

    Parameters
    ----------
    n_bytes : int
        Number of entropy bytes to generate. 1-4096.
    purpose : str
        Operator-readable purpose; logged in provenance.
    backend : str
        See module docstring.
    """
    if not isinstance(n_bytes, int) or n_bytes < 1 or n_bytes > 4096:
        raise ValueError(f'quantum_random: n_bytes must be 1..4096, got {n_bytes!r}')

    # License gate — backends that need it must call get_license() themselves;
    # for sim-local we still verify the license exists as a fail-fast
    # configuration check (operator dropped the license = system is set up).
    try:
        get_license()
    except LicenseError:
        # Sim-local can run without a license, but warn via the audit log.
        if backend != 'sim-local':
            raise

    if backend == 'sim-local':
        data = os.urandom(n_bytes)
        write_provenance(
            purpose=purpose,
            backend='sim-local',
            n_bytes=n_bytes,
            extra={
                'note': 'sim-local backend; entropy from os.urandom. '
                        'Audit trail only — flip to sim-pilotos once SDK wired.',
            },
        )
        return data

    if backend == 'sim-pilotos':
        raise NotImplementedError(
            'sim-pilotos backend not yet wired. Operator action: extract '
            r'C:\Users\Zonia\Desktop\QPilotos-V4.2\python_simulator.tar.gz '
            'and pip install the sim package; then implement '
            'qrng._call_pilotos_sim(n_bytes).'
        )

    if backend == 'cloud-wukong-180':
        # Operator hard-canonical 2026-05-23: "we only have 120 seconds on the
        # license key". The cloud path is BUDGET-GATED — even with pyqpanda3
        # installed, every cloud submission must call budget.check_budget()
        # FIRST with an estimated_seconds value, then budget.record_usage()
        # AFTER measuring the actual wall time. This NotImplementedError
        # stays until the budget gate is wired into the cloud call site.
        try:
            from .budget import remaining_seconds
        except ImportError:
            from budget import remaining_seconds  # type: ignore
        rem = remaining_seconds()
        raise NotImplementedError(
            f'cloud-wukong-180 backend BUDGET-GATED (operator hard-canonical: '
            f'120s total, {rem:.2f}s remaining). Wire path requires: '
            f'(1) budget.check_budget(estimated_seconds) pre-call, '
            f'(2) pyqpanda3 cloud submission, '
            f'(3) budget.record_usage(actual_seconds, purpose=...) post-call. '
            f'Use sim-local for testing; use sim-pilotos for real local quantum '
            f'sim (no budget cost) once operator extracts python_simulator.tar.gz.'
        )

    raise ValueError(f'quantum_random: unknown backend {backend!r}')


if __name__ == '__main__':
    data = quantum_random(16, purpose='qrng.py CLI smoke-test', backend='sim-local')
    print(f'[sinister-seraphim.qrng] generated {len(data)} bytes: {data.hex()}')
