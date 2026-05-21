# Sinister Sanctum :: sinister-diagnose :: entry-point
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Module-level entry-point.

Two callers:
  1. The `sinister-diagnose` console script (from pyproject.scripts).
  2. The `sinister diagnose ...` umbrella dispatcher, which resolves
     `sinister_diagnose.__main__:main(argv)` at runtime.

`main(argv)` is the contract: it accepts a list[str] or None and returns int.
"""
from __future__ import annotations

import sys
from typing import List

from .cli import dispatch


def main(argv: List[str] | None = None) -> int:
    """Umbrella-compatible entry-point. argv=None → use sys.argv[1:]."""
    return dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
