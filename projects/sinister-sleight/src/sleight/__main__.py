# Author: RKOJ-ELENO :: 2026-05-24
"""Sinister Sleight CLI entry point.

P0 SCAFFOLD — prints status only. Real CLI lands in P1.

Planned (P1+) subcommands:
    sleight data fetch --universe sp500 --years 5
    sleight backtest --strategy momentum --start 2024-01-01 --end 2025-01-01
    sleight paper-trade --strategy ensemble --portfolio sample
    sleight train --strategy m1-direction
    sleight kill-switch
    sleight risk status
"""

import sys


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    print("Sinister Sleight (P0 scaffold)")
    print("==============================")
    print("Status: not yet implemented (P0 is structure + docs only).")
    print("See docs/06-roadmap.md for phase plan.")
    print("First CLI feature lands in P1 (data layer).")
    print(f"Args received: {argv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
