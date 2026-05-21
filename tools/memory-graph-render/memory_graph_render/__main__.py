# Sinister Sanctum :: memory-graph-render :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations

import argparse
import json
import sys

from .render import render, detect_backend


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="memory-graph-render",
        description="Sinister Sanctum :: render forge-memory subgraph to PNG (with .mmd + HTML fallback).",
    )
    p.add_argument("--namespace", "-n", default=None, help="forge-memory namespace to graph")
    p.add_argument("--query", "-q", default=None, help="query filter (uses forge-memory recall)")
    p.add_argument("--output", "-o", default=None, help="output path (.png); use - for stdout (mmd src only)")
    p.add_argument("--mmd-only", action="store_true", help="skip PNG render; only write .mmd + .html")
    p.add_argument("--title", default=None)
    p.add_argument("--detect", action="store_true", help="print the detected render backend and exit")
    p.add_argument("--mmd", default=None, help="render this mermaid source instead of forge-memory")

    args = p.parse_args(argv)

    if args.detect:
        print(detect_backend())
        return 0

    mermaid_src = None
    if args.mmd:
        mermaid_src = open(args.mmd, encoding="utf-8").read() if args.mmd != "-" else sys.stdin.read()

    res = render(
        mermaid_src=mermaid_src,
        namespace=args.namespace,
        query=args.query,
        output=args.output,
        mmd_only=args.mmd_only,
        title=args.title,
    )
    print(json.dumps(res, indent=2, default=str))
    return 0 if not res.get("error") or res.get("backend") == "mmd-only" else 0


if __name__ == "__main__":
    sys.exit(main())
