# Sinister Term :: tests/conftest.py
# Author: RKOJ-ELENO :: 2026-05-25
# License: AGPL-3.0-or-later
#
# Shared pytest fixtures + path insertion so `from term import ...` resolves
# even when pytest is invoked from any cwd.

from __future__ import annotations

import sys
from pathlib import Path

# Ensure projects/sinister-term/source/ is on sys.path so `term` imports work
# regardless of where pytest is invoked from.
_SOURCE_ROOT = Path(__file__).resolve().parent.parent
if str(_SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SOURCE_ROOT))
