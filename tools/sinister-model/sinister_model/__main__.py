# Sinister Sanctum :: sinister-model :: python -m sinister_model entry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Thin wrapper that exposes `main(argv) -> int` for the sinister-cli
umbrella dispatcher (per the 5-file sinister-CLI subcommand pattern).

`python -m sinister_model ...` and `sinister model ...` both land here.
"""
from __future__ import annotations
import sys

from .cli import main


if __name__ == "__main__":
    sys.exit(main())
