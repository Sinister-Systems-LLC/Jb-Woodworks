"""Sinister Jokester — top-level CLI.

Author: RKOJ-ELENO :: 2026-05-26

Usage:
  python jokester_cli.py intake <url> [--reviewer SLUG] [--force] [--verdict V] [--rationale "a|b|c"]
  python jokester_cli.py recall <query>
  python jokester_cli.py list [adopt|watch|reject]
  python jokester_cli.py stats
  python jokester_cli.py reindex
  python jokester_cli.py drain-queue <queue.jsonl>   # one URL per line
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from db import init_db as init_db_mod  # noqa: E402
from db import recall as recall_mod  # noqa: E402
from review import decide as decide_mod  # noqa: E402


def cmd_intake(args: argparse.Namespace) -> int:
    init_db_mod.init_db()
    bullets = args.rationale.split("|") if args.rationale else None
    out = decide_mod.decide(
        args.url,
        force=args.force,
        reviewed_by=args.reviewer,
        manual_verdict=args.verdict,
        manual_rationale=bullets,
    )
    print(json.dumps(out, indent=2, default=str))
    return 0 if out.get("intake_ok") or out.get("verdict") in {"ADOPT", "WATCH", "REJECT"} else 1


def cmd_recall(args: argparse.Namespace) -> int:
    out = recall_mod.search(args.query)
    print(json.dumps(out, indent=2, default=str))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    verdict = args.verdict.upper() if args.verdict else None
    out = recall_mod.list_by_verdict(verdict)
    print(json.dumps(out, indent=2, default=str))
    return 0


def cmd_stats(_: argparse.Namespace) -> int:
    print(json.dumps(recall_mod.stats(), indent=2))
    return 0


def cmd_reindex(_: argparse.Namespace) -> int:
    init_db_mod.init_db()
    path = recall_mod.rebuild_index_md()
    print(f"ok index={path}")
    return 0


def cmd_drain_queue(args: argparse.Namespace) -> int:
    init_db_mod.init_db()
    qpath = Path(args.queue)
    if not qpath.exists():
        print(f"queue not found: {qpath}", file=sys.stderr)
        return 2
    rc_overall = 0
    for raw in qpath.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # JSON line ({url, reviewer?}) OR bare URL
        if line.startswith("{"):
            try:
                row = json.loads(line)
                url = row["url"]
                reviewer = row.get("reviewer", "sinister-jokester")
            except (json.JSONDecodeError, KeyError):
                print(f"skip-malformed: {line[:80]}")
                continue
        else:
            url = line
            reviewer = "sinister-jokester"
        try:
            out = decide_mod.decide(url, reviewed_by=reviewer)
            print(f"ok {out['verdict']} {out['id']} -> {out['decision_md_path']}")
        except Exception as e:  # noqa: BLE001
            print(f"fail {url} :: {e!r}", file=sys.stderr)
            rc_overall = 1
    # Rebuild index after a drain.
    recall_mod.rebuild_index_md()
    return rc_overall


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="jokester_cli.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_intake = sub.add_parser("intake", help="Intake + verdict a single URL.")
    p_intake.add_argument("url")
    p_intake.add_argument("--reviewer", default="sinister-jokester")
    p_intake.add_argument("--force", action="store_true")
    p_intake.add_argument("--verdict", choices=["ADOPT", "WATCH", "REJECT"], default=None)
    p_intake.add_argument("--rationale", default=None, help="Pipe-separated rationale bullets (only with --verdict).")
    p_intake.set_defaults(func=cmd_intake)

    p_recall = sub.add_parser("recall", help="Free-text search across url/title/summary/tags.")
    p_recall.add_argument("query")
    p_recall.set_defaults(func=cmd_recall)

    p_list = sub.add_parser("list", help="List items, optionally filtered by verdict.")
    p_list.add_argument("verdict", nargs="?", choices=["adopt", "watch", "reject"], default=None)
    p_list.set_defaults(func=cmd_list)

    p_stats = sub.add_parser("stats", help="Counts by verdict + source type.")
    p_stats.set_defaults(func=cmd_stats)

    p_reindex = sub.add_parser("reindex", help="Rebuild vault/INDEX.md from DB state.")
    p_reindex.set_defaults(func=cmd_reindex)

    p_drain = sub.add_parser("drain-queue", help="Process a queue file (one URL or JSON row per line).")
    p_drain.add_argument("queue")
    p_drain.set_defaults(func=cmd_drain_queue)

    args = ap.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
