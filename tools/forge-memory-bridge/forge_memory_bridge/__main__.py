# Sinister Sanctum :: forge-memory-bridge :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api import (
    write as _write,
    recall as _recall,
    list as _list,
    graph as _graph,
    consolidate as _consolidate,
    delete as _delete,
    set_root,
    get_root,
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="forge-memory",
        description="Sinister Sanctum :: forge-memory-bridge CLI (disk-first memory store).",
    )
    p.add_argument(
        "--root",
        default=None,
        help="Override store root (default: SINISTER_FORGE_MEMORY_ROOT env or _shared-memory/forge-memory/)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # write
    sp = sub.add_parser("write", help="Store a memory record")
    sp.add_argument("--namespace", "-n", default="default")
    sp.add_argument("--key", "-k", required=True)
    sp.add_argument("--tags", "-t", default="", help="Comma-separated tags")
    sp.add_argument("--no-upsert", action="store_true", help="Fail if key already exists")
    sp.add_argument("--json", action="store_true", help="Parse <value> as JSON")
    sp.add_argument("value", nargs="?", default=None, help="String or JSON value (omit to read stdin)")

    # recall
    sp = sub.add_parser("recall", help="Find relevant memories by query")
    sp.add_argument("--namespace", "-n", default=None)
    sp.add_argument("--limit", "-l", type=int, default=10)
    sp.add_argument("--use-mcp", action="store_true", help="Try Ruflo MCP fast-path (stub in v0.1.0)")
    sp.add_argument("query", help="Free-text query")

    # list
    sp = sub.add_parser("list", help="List records, optionally filtered by namespace/tags")
    sp.add_argument("--namespace", "-n", default=None)
    sp.add_argument("--tags", "-t", default="", help="Comma-separated tags (AND-match)")

    # graph
    sp = sub.add_parser("graph", help="Emit mermaid-flowchart syntax for the matching subgraph")
    sp.add_argument("--namespace", "-n", default=None)
    sp.add_argument("--query", "-q", default=None)
    sp.add_argument("--output", "-o", default="-", help="Output path, or - for stdout")

    # consolidate
    sp = sub.add_parser("consolidate", help="Dedupe near-duplicate memories + raise confidence")
    sp.add_argument("--namespace", "-n", default=None)
    sp.add_argument("--dry-run", action="store_true")

    # delete
    sp = sub.add_parser("delete", help="Delete a memory record")
    sp.add_argument("--namespace", "-n", required=True)
    sp.add_argument("--key", "-k", required=True)

    # info
    sub.add_parser("info", help="Print store root + version")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.root:
        set_root(args.root)

    if args.cmd == "write":
        if args.value is None:
            args.value = sys.stdin.read().strip()
        if not args.value:
            print("[forge-memory] write: empty value", file=sys.stderr)
            return 2
        value = json.loads(args.value) if args.json else args.value
        tags = [t for t in args.tags.split(",") if t.strip()]
        rec = _write(args.namespace, args.key, value, tags=tags, upsert=not args.no_upsert)
        print(json.dumps(rec, indent=2, default=str))
        return 0

    if args.cmd == "recall":
        hits = _recall(args.query, namespace=args.namespace, limit=args.limit, use_mcp=args.use_mcp)
        print(json.dumps(hits, indent=2, default=str))
        return 0

    if args.cmd == "list":
        tags = [t for t in args.tags.split(",") if t.strip()]
        recs = _list(namespace=args.namespace, tags=tags)
        print(json.dumps(recs, indent=2, default=str))
        return 0

    if args.cmd == "graph":
        mmd = _graph(namespace=args.namespace, query=args.query)
        if args.output == "-":
            print(mmd)
        else:
            Path(args.output).write_text(mmd, encoding="utf-8")
            print(f"[forge-memory] wrote {len(mmd)} chars -> {args.output}")
        return 0

    if args.cmd == "consolidate":
        summary = _consolidate(namespace=args.namespace, dry_run=args.dry_run)
        print(json.dumps(summary, indent=2, default=str))
        return 0

    if args.cmd == "delete":
        ok = _delete(args.namespace, args.key)
        print("deleted" if ok else "not found")
        return 0 if ok else 1

    if args.cmd == "info":
        from . import __version__
        print(json.dumps({
            "version": __version__,
            "root": str(get_root()),
            "author": "RKOJ-ELENO :: 2026-05-21",
            "license": "AGPL-3.0-or-later",
        }, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
