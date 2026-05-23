"""sinister-seraphim :: Sinister fleet's quantum-compute application layer.

Author: RKOJ-ELENO :: 2026-05-23

Public API:

  - `quantum_random(n_bytes, purpose, backend)` — QRNG entry-point
  - `write_provenance(...)` — audit sidecar writer
  - `get_license()` / `license_fingerprint()` — license loader

See README.md for the four use-lanes:
  Lane 1: Memory + audit (super-local agent)
  Lane 2: Sinister Emulator environment (account-traffic sim)
  Lane 3: Drone systems training env
  Lane 4: Reverse engineering — Sinister API discovery
"""
# Dual-mode imports — work both as proper package (pip-installed)
# AND when pytest auto-discovers this __init__.py via the hyphen dir.
try:
    from .audit import write_provenance
    from .license import LicenseError, get_license, license_fingerprint
    from .qrng import quantum_random
except ImportError:
    import sys as _sys
    from pathlib import Path as _Path
    _here = _Path(__file__).resolve().parent
    if str(_here) not in _sys.path:
        _sys.path.insert(0, str(_here))
    from audit import write_provenance  # type: ignore
    from license import LicenseError, get_license, license_fingerprint  # type: ignore
    from qrng import quantum_random  # type: ignore

__all__ = [
    'LicenseError',
    'get_license',
    'license_fingerprint',
    'quantum_random',
    'write_provenance',
]

__version__ = '0.1.0'
