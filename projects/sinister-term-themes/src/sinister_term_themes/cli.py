# Author: RKOJ-ELENO :: 2026-05-25
"""Ancestral Remotion CLI.

P0:
    python -m sinister_term_themes demo <project-key> [--frames N]
    python -m sinister_term_themes list
    python -m sinister_term_themes --version

P1+:
    python -m sinister_term_themes attach --source stdin   (sidecar tap)
    python -m sinister_term_themes attach --source pipe:<path>
"""

from __future__ import annotations

import argparse
import sys

from . import __version__, entities, engine


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sinister_term_themes",
        description="Ancestral Remotion :: living ASCII visualization layer.",
    )
    p.add_argument("--version", action="store_true", help="print version + exit")
    sub = p.add_subparsers(dest="command")

    demo = sub.add_parser("demo", help="render a frames demo of an entity")
    demo.add_argument("project_key", nargs="?", default="sanctum",
                      help="project key (default: sanctum)")
    demo.add_argument("--frames", type=int, default=30,
                      help="number of frames to render (default 30; CI: 5)")

    sub.add_parser("list", help="list registered entities")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.version:
        print(f"sinister-term-themes {__version__}")
        return 0

    if args.command == "list":
        keys = entities.list_keys()
        print("Registered entities:")
        for k in keys:
            try:
                defn = entities.load(k)
                print(f"  {k:30s}  name={defn['name']!r}  idle={defn['idle_palette']}  "
                      f"hot={defn['high_energy_palette']}")
            except Exception as e:
                print(f"  {k:30s}  [LOAD ERROR: {e}]")
        return 0

    if args.command == "demo":
        return engine.demo_render(
            project_key=args.project_key,
            frames=max(1, args.frames),
        )

    # No command -> help
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
