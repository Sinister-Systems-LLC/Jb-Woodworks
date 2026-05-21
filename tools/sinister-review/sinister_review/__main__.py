# Sinister Sanctum :: sinister-review :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import argparse
import json
import subprocess
import sys

from .api import (
    review_diff as _rd,
    review_transcript as _rt,
    review_commit as _rc,
    judge as _judge,
    recent_reviews as _recent,
    set_reviews_root,
)


def _parser():
    p = argparse.ArgumentParser(
        prog="sinister-review",
        description="Sinister Sanctum :: autoreview / autojudge (jcode parity).",
    )
    p.add_argument("--reviews-root", default=None)
    p.add_argument("--model", default="opus-4-7")
    p.add_argument("--focus", default=None)
    p.add_argument("--commit", default=None, help="git sha to review")
    p.add_argument("--transcript", default=None, help="path to transcript .jsonl")
    p.add_argument("--diff", default=None, help="diff file (or - for stdin)")
    p.add_argument("--recent", type=int, default=None, help="review last N commits")
    p.add_argument("--judge", default=None, help="binary judgment question")
    p.add_argument("--context", default=None, help="optional context file for --judge")
    p.add_argument("--list", action="store_true", help="list prior reviews")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--namespace", default=None, help="filter --list by from-slug")
    p.add_argument("--show", default=None, help="print a review JSON by path")
    return p


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.reviews_root:
        set_reviews_root(args.reviews_root)

    if args.list:
        out = _recent(limit=args.limit, namespace=args.namespace)
        for r in out:
            stub = " (stub)" if r.get("stub") else ""
            print(f"  {r['ts_utc']} {r['from']:<14} {r['kind']:<10} {r.get('rating','?'):<14} {r.get('headline','')[:80]}{stub}")
        return 0

    if args.show:
        from pathlib import Path
        p = Path(args.show)
        if not p.exists():
            print(f"not found: {p}", file=sys.stderr)
            return 2
        print(p.read_text(encoding="utf-8"))
        return 0

    if args.judge:
        ctx = None
        if args.context:
            from pathlib import Path
            ctx = Path(args.context).read_text(encoding="utf-8", errors="replace")
        rec = _judge(args.judge, context=ctx, model=args.model)
        print(json.dumps(rec, indent=2, default=str))
        return 0

    if args.commit:
        rec = _rc(args.commit, model=args.model, focus=args.focus)
        print(json.dumps(rec, indent=2, default=str))
        return 0

    if args.transcript:
        rec = _rt(args.transcript, model=args.model, focus=args.focus)
        print(json.dumps(rec, indent=2, default=str))
        return 0

    if args.diff:
        if args.diff == "-":
            content = sys.stdin.read()
        else:
            from pathlib import Path
            content = Path(args.diff).read_text(encoding="utf-8", errors="replace")
        rec = _rd(content, model=args.model, focus=args.focus)
        print(json.dumps(rec, indent=2, default=str))
        return 0

    if args.recent:
        try:
            res = subprocess.run(
                ["git", "log", f"-{args.recent}", "--format=%H"],
                capture_output=True, text=True, timeout=10,
            )
            shas = [s for s in res.stdout.strip().split("\n") if s]
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            print(f"git log failed: {e}", file=sys.stderr)
            return 2
        results = []
        for sha in shas:
            results.append(_rc(sha, model=args.model, focus=args.focus))
        print(json.dumps(results, indent=2, default=str))
        return 0

    _parser().print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
