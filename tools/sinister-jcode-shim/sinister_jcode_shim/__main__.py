# Sinister Sanctum :: sinister-jcode-shim :: module entry
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Module entrypoint so `python -m sinister_jcode_shim ...` works in addition
to the installed `sinister-jcode-shim` console script.
"""
from __future__ import annotations

import sys

from .cli import cli


def main(argv: list[str] | None = None) -> int:
    """Console-script entrypoint. Returns exit code (or raises SystemExit)."""
    try:
        cli.main(args=argv, standalone_mode=False)
        return 0
    except SystemExit as e:
        return int(e.code or 0)


if __name__ == "__main__":
    sys.exit(main())
