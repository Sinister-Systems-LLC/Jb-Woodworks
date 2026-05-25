# Author: RKOJ-ELENO :: 2026-05-25
"""Thin wrapper so `python deploy/setup.py` matches the README's default entry-point.

Delegates to deploy/first_time_setup.py:main() — see that module for the full flow,
arguments (--dry-run, --no-elevate, --no-clone, --target, --no-launch), and the
operator-hard-canonical doctrine references (no operator clicks beyond OAuth).
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from first_time_setup import main  # noqa: E402  (path inserted above)


if __name__ == "__main__":
    sys.exit(main())
