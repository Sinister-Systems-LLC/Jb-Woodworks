"""hgly CLI stub. Author: RKOJ-ELENO :: 2026-05-25.

Phase 0: only --version is implemented. Real subcommands (parse/compile/run/sim)
land in Phase 2+ once the Rust crates exist; this Python CLI will then shell
out to them. Keeps a stable entry point from day 0.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hgly",
        description="Sinister Hieroglyphics command-line interface (Phase 0 stub).",
    )
    p.add_argument("--version", action="version", version=f"hgly {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # No subcommands yet; argparse handles --version itself.
    _ = args
    return 0


if __name__ == "__main__":
    sys.exit(main())
