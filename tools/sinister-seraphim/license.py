"""PilotOS license loader for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

Reads the paid V4.2 license from `_vault-personal/licenses/pilotos.txt`
(gitignored — never reaches GitHub). Every other module in this package
calls `get_license()` before touching pyqpanda3 / cloud submission.

The license is a long opaque base64-ish string. We do NOT parse it;
we forward it to pyqpanda3 / cloud SDK as opaque bytes.
"""
from __future__ import annotations

import os
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
VAULT_LICENSE = SANCTUM_ROOT / '_vault-personal' / 'licenses' / 'pilotos.txt'


class LicenseError(RuntimeError):
    """Raised when the PilotOS license cannot be loaded."""


def get_license() -> str:
    """Return the raw license string, or raise LicenseError.

    Strips comment lines (`## ...`) and whitespace so the result is the
    bare license token. Never logs the value.
    """
    if not VAULT_LICENSE.exists():
        raise LicenseError(
            f'PilotOS license missing at {VAULT_LICENSE}. '
            'Drop the operator-provided license into that path; the dir is '
            'gitignored so it stays local. See tools/sinister-seraphim/README.md.'
        )
    raw = VAULT_LICENSE.read_text(encoding='utf-8')
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith('##')]
    if not lines:
        raise LicenseError(
            f'PilotOS license file at {VAULT_LICENSE} contained no non-comment lines.'
        )
    return ''.join(lines)


def license_fingerprint() -> str:
    """Return a short hex fingerprint of the license for logging.

    Safe to log (one-way hash) — proves which license is loaded without
    leaking the value.
    """
    import hashlib
    return hashlib.sha256(get_license().encode('utf-8')).hexdigest()[:12]


if __name__ == '__main__':
    try:
        fp = license_fingerprint()
        print(f'[sinister-seraphim] license loaded; sha256[0:12] = {fp}')
    except LicenseError as exc:
        print(f'[sinister-seraphim] {exc}')
        raise SystemExit(2)
