"""Pytest config for sinister-seraphim.

Author: RKOJ-ELENO :: 2026-05-23

The tools/sinister-seraphim/ dir is hyphen-named, which breaks Python's
package import via the __init__.py-relative-import path. Until the
operator runs `pip install -e tools/sinister-seraphim/` (which maps the
hyphen dir to the underscore `sinister_seraphim` package per pyproject),
tests import the modules flat.

This conftest puts the seraphim dir at sys.path[0] so `import qrng`,
`import audit`, `import fingerprint`, `import license` all resolve.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERAPHIM_DIR = HERE.parent

if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))
