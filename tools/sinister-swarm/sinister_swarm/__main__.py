# Sinister Sanctum :: sinister-swarm :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import argparse, json, sys
from .api import (
    dm as _dm, broadcast as _bc, spawn_agent as _spawn,
    list_active as _la, watch_file as _wf, mark_done as _md,
    wait_for as _wfor, mcp_hive_status as _hs,
    set_sanctum_root, detect_my_slug,
)


def _parser():
    p = argparse.ArgumentParser(prog="sinister-swarm",
        description="Sinister Sanctum :: jcode-swarm parity (DM/broadcast/spawn/watch/status)")
    p.add_argument("--sanctum-root", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("dm")
    sp.add_argument("to_slug")
    sp.add_argument("message", nargs="?")
    sp.add_argument("--tag", default="[MSG]")
    sp.add_argument("--subject", default=None)
    sp.add_argument("--from-slug", default=None)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("broadcast")
    sp.add_argument("message", nargs="?")
    sp.add_argument("--tag", default="[BROADCAST]")
    sp.add_argument("--subject", default=None)
    sp.add_argument("--exclude", default="")
    sp.add_argument("--no-mcp", action="store_true")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("spawn")
    sp.add_argument("--project", required=True)
    sp.add_argument("--mode", default="resume")
    sp.add_argument("--agent-name", default=None)
    sp.add_argument("--accent", default="purple")
    sp.add_argument("--no-headless", action="store_true")
    sp.add_argument("--focus", default=None)
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("list")
    sp.add_argument("--stale-minutes", type=int, default=15)

    sp = sub.add_parser("watch")
    sp.add_argument("--path", required=True)
    sp.add_argument("--poll-seconds", type=float, default=2.0)
    sp.add_argument("--blocking", action="store_true")
    sp.add_argument("--once", action="store_true")

    sp = sub.add_parser("mark-done")
    sp.add_argument("task")
    sp.add_argument("--result", default=None)
    sp.add_argument("--from-slug", default=None)

    sp = sub.add_parser("wait-for")
    sp.add_argument("slug")
    sp.add_argument("task")
    sp.add_argument("--timeout", type=float, default=300)
    sp.add_argument("--poll-seconds", type=float, default=2.0)

    sub.add_parser("hive-status")
    sub.add_parser("whoami")
    return p


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.sanctum_root:
        set_sanctum_root(args.sanctum_root)
    c = args.cmd
    if c == "dm":
        if args.message is None:
            args.message = sys.stdin.read().strip()
        msg = json.loads(args.message) if args.json else args.message
        print(json.dumps(_dm(args.to_slug, msg, tag=args.tag, subject=args.subject, from_slug=args.from_slug), indent=2, default=str))
        return 0
    if c == "broadcast":
        if args.message is None:
            args.message = sys.stdin.read().strip()
        msg = json.loads(args.message) if args.json else args.message
        ex = [s for s in args.exclude.split(",") if s.strip()]
        drops = _bc(msg, tag=args.tag, subject=args.subject, exclude=ex, use_mcp=not args.no_mcp)
        print(json.dumps({"recipients": len(drops), "drops": drops}, indent=2, default=str))
        return 0
    if c == "spawn":
        r = _spawn(args.project, mode=args.mode, agent_name=args.agent_name, accent=args.accent,
                   headless=not args.no_headless, focus=args.focus, dry_run=args.dry_run)
        print(json.dumps(r, indent=2, default=str))
        return 0 if r.get("ok") else 1
    if c == "list":
        print(json.dumps(_la(stale_minutes=args.stale_minutes), indent=2, default=str))
        return 0
    if c == "watch":
        if args.once:
            h = _wf(args.path, poll_seconds=args.poll_seconds, blocking=False)
            print(json.dumps({"path": str(h.path), "watched": True}, indent=2))
            return 0
        if args.blocking:
            _wf(args.path, on_change=lambda e: print(json.dumps(e, indent=2, default=str)),
                poll_seconds=args.poll_seconds, blocking=True)
            return 0
        h = _wf(args.path, poll_seconds=args.poll_seconds, blocking=False)
        print(json.dumps({"baseline_recorded": True, "path": str(h.path)}, indent=2))
        return 0
    if c == "mark-done":
        print(json.dumps(_md(args.task, result=args.result, from_slug=args.from_slug), indent=2, default=str))
        return 0
    if c == "wait-for":
        r = _wfor(args.slug, args.task, timeout_s=args.timeout, poll_seconds=args.poll_seconds)
        if r is None:
            print(json.dumps({"ok": False, "timeout": True}, indent=2))
            return 2
        print(json.dumps(r, indent=2, default=str))
        return 0
    if c == "hive-status":
        print(json.dumps(_hs(), indent=2, default=str))
        return 0
    if c == "whoami":
        print(detect_my_slug())
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
