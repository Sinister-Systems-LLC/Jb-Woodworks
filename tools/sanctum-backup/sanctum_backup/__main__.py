# Sinister Sanctum :: sanctum-backup :: python -m sanctum_backup
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Entry-point for `python -m sanctum_backup` and the sinister-cli umbrella.

The umbrella dispatcher (`tools/sinister-cli/sinister_cli/__main__.py`) resolves
`sinister sanctum-backup ...` to this module's `main(argv) -> int` callable.
"""
from __future__ import annotations
import sys

from .cli import main as _cli_main


def main(argv: list[str] | None = None) -> int:
    """Standalone-callable entry point.

    Click's command object accepts a single argv list via `main(args=...)`
    and translates SystemExit into the integer return code.
    """
    if argv is None:
        argv = sys.argv[1:]
    try:
        # standalone_mode=False so we control exit code; returns the value
        # of the invoked command (or raises click.exceptions.Exit).
        _cli_main.main(args=list(argv), standalone_mode=False)
        return 0
    except SystemExit as e:
        return int(e.code or 0)
    except Exception as e:  # pragma: no cover - defensive
        print(f"sanctum-backup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
