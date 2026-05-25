"""hgly CLI. Author: RKOJ-ELENO :: 2026-05-25.

Phase 2 subcommands:
  hgly --version        — print version.
  hgly run <file.shp>   — parse + execute via the tree-walking interpreter.
Real codegen subcommands (compile, sim) land Phase 3+ once Rust crates exist;
this Python CLI shells out to them then.
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .parser import parse_file, ParseError
from .interpreter import Interpreter, HglyPanic


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hgly",
        description="Sinister Hieroglyphics command-line interface.",
    )
    p.add_argument("--version", action="version", version=f"hgly {__version__}")
    sub = p.add_subparsers(dest="cmd")
    run = sub.add_parser("run", help="parse + execute a .shp source file")
    run.add_argument("file", help="path to .shp source")
    run.add_argument("args", nargs="*", help="positional args passed as argv")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "run":
        try:
            prog = parse_file(args.file)
        except (ParseError, FileNotFoundError, OSError) as e:
            sys.stderr.write(f"parse error: {e}\n")
            return 2
        try:
            return Interpreter().run(prog, args.args)
        except HglyPanic as e:
            sys.stderr.write(f"panic: {e.msg}\n")
            return 134
    return 0


if __name__ == "__main__":
    sys.exit(main())
