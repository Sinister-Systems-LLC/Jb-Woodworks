# Sinister Sanctum :: sanctum-backup :: pytest conftest
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Inject the package path for in-place tests without requiring `pip install`."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))
