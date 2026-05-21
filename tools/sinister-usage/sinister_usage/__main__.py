# Sinister Sanctum :: sinister-usage :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .api import check, check_all, list_endpoints
from .estimator import estimate_text_breakdown, estimate_tokens
from .sources import DEFAULT_CLAUDE_DIR, scan_claude_local, today_summary


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sinister-usage",
        description="Sinister Sanctum :: jcode-usage parity (env-check + endpoint registry + local-state scan + token estimator; v0.1.0 has no network calls)",
    )
    p.add_argument("--version", action="version", version=f"sinister-usage {__version__}")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("list", help="list known usage endpoints (no env lookup)")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("check", help="env-check one provider (no network)")
    sp.add_argument("provider")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("check-all", help="env-check every provider")
    sp.add_argument("--json", action="store_true")

    sub.add_parser("matrix", help="print the jcode-feature-matrix row for this tool")

    sp = sub.add_parser("local", help="scan ~/.claude/ local state (no network)")
    sp.add_argument("--claude-dir", default=None, help="override ~/.claude path")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("today", help="UTC-today rollup of local Claude Code state")
    sp.add_argument("--claude-dir", default=None)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("estimate", help="estimate token count of text (stdin / --text / --file)")
    sp.add_argument("--text", default=None, help="inline text (overrides stdin)")
    sp.add_argument("--file", default=None, help="read text from file")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("doctor", help="5-check self-test (schemas + dir reachability)")
    sp.add_argument("--no-state-ok", action="store_true",
                    help="pass even if ~/.claude doesn't exist (CI / fresh install)")
    sp.add_argument("--json", action="store_true")

    return p


def _print_endpoints(json_out: bool) -> int:
    rows = list_endpoints()
    if json_out:
        print(json.dumps(rows, indent=2))
        return 0
    w_slug = max(len(r["slug"]) for r in rows)
    w_disp = max(len(r["display"]) for r in rows)
    print(f"{'slug'.ljust(w_slug)}  {'provider'.ljust(w_disp)}  auth         endpoint")
    print("-" * (w_slug + w_disp + 40))
    for r in rows:
        ep = r["endpoint_url"] or f"(no public API — {r['docs_url'] or 'see provider console'})"
        print(f"{r['slug'].ljust(w_slug)}  {r['display'].ljust(w_disp)}  {r['auth_method'].ljust(12)}  {ep}")
    return 0


def _print_check_all(json_out: bool) -> int:
    rows = check_all()
    if json_out:
        print(json.dumps(rows, indent=2))
        return 0
    w_slug = max(len(r["slug"]) for r in rows)
    print(f"{'slug'.ljust(w_slug)}  endpoint  configured  notes")
    print("-" * (w_slug + 36))
    for r in rows:
        ep = "yes" if r["endpoint_known"] else "no"
        cfg = "—" if r["configured"] is None else ("yes" if r["configured"] else "no")
        notes = (r["notes"] or "")[:50]
        print(f"{r['slug'].ljust(w_slug)}  {ep.ljust(8)}  {cfg.ljust(10)}  {notes}")
    return 0


def main(argv=None) -> int:
    p = _parser()
    args = p.parse_args(argv)
    cmd = args.cmd

    if cmd is None:
        p.print_help()
        return 0

    if cmd == "list":
        return _print_endpoints(getattr(args, "json", False))
    if cmd == "check":
        r = check(args.provider)
        if getattr(args, "json", False):
            print(json.dumps(r, indent=2))
            return 0 if r.get("ok") else 2
        if not r.get("ok"):
            print(f"sinister-usage: {r.get('error', 'unknown')} ({args.provider})", file=sys.stderr)
            return 2
        print(f"[{r['slug']}] {r['display']}")
        print(f"  endpoint:    {r['endpoint_url'] or '(no public API)'}")
        print(f"  auth:        {r['auth_method']}")
        cfg = "—" if r["configured"] is None else ("yes" if r["configured"] else "no")
        print(f"  configured:  {cfg}")
        if r.get("notes"):
            print(f"  notes:       {r['notes']}")
        if r.get("docs_url"):
            print(f"  docs:        {r['docs_url']}")
        return 0
    if cmd == "check-all":
        return _print_check_all(getattr(args, "json", False))
    if cmd == "matrix":
        print("| jcode `usage` (token quota / billing) | "
              "`tools/sinister-usage/` | shipped v0.1.0 (env-check + local-scan + estimator) | sanctum | "
              "11-row endpoint registry + ~/.claude/ local-state scan + chars/4 token estimator. "
              "Cross-refs sinister-login for configured flag. NO network in v0.1.0. |")
        return 0
    if cmd == "local":
        return _cmd_local(args)
    if cmd == "today":
        return _cmd_today(args)
    if cmd == "estimate":
        return _cmd_estimate(args)
    if cmd == "doctor":
        return _cmd_doctor(args)

    p.print_help()
    return 1


def _cmd_local(args) -> int:
    out = scan_claude_local(args.claude_dir)
    if getattr(args, "json", False):
        print(json.dumps(out, indent=2, default=str))
        return 0
    print(f"sinister-usage local :: scanning {out['root']}")
    if not out["exists"]:
        print("  (no Claude Code state directory — fresh install?)")
        return 0
    print(f"  projects:           {out['projects_count']}")
    print(f"  sessions total:     {out['sessions_count']}")
    print(f"  sessions today:     {out['sessions_today']}")
    print(f"  bytes total:        {out['total_session_bytes']:,}")
    print(f"  bytes today:        {out['today_session_bytes']:,}")
    print(f"  settings present:   {out['settings_present']}")
    print(f"  history lines:      {out['history_lines']}")
    return 0


def _cmd_today(args) -> int:
    out = today_summary(args.claude_dir)
    if getattr(args, "json", False):
        print(json.dumps(out, indent=2, default=str))
        return 0
    print(f"sinister-usage today :: UTC {out['as_of_utc']}")
    print(f"  sessions today:     {out['sessions_today']}")
    print(f"  bytes today:        {out['bytes_today']:,}")
    print(f"  rough tokens today: {out['rough_tokens_today']:,}  (upper-bound; bytes/4)")
    print(f"  note: {out['notes']}")
    return 0


def _read_text_for_estimate(args) -> str:
    if args.text is not None:
        return args.text
    if args.file:
        return Path(args.file).read_text(encoding="utf-8", errors="replace")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def _cmd_estimate(args) -> int:
    text = _read_text_for_estimate(args)
    if args.verbose or args.json:
        bd = estimate_text_breakdown(text)
        if args.json:
            print(json.dumps(bd, indent=2, default=str))
            return 0
        print("sinister-usage estimate ::")
        for k, v in bd.items():
            if k == "schema_version":
                continue
            print(f"  {k.ljust(18)} {v}")
        return 0
    print(estimate_tokens(text))
    return 0


def _cmd_doctor(args) -> int:
    from .estimator import SCHEMA_VERSION as ES, estimate_tokens as _e
    from .sources import SCHEMA_VERSION as SS
    from .endpoints import SCHEMA_VERSION as ENS
    checks = [
        ("estimator schema", ES == "sinister.usage.estimator.v1", ES),
        ("sources schema", SS == "sinister.usage.sources.v1", SS),
        ("endpoints schema", ENS == "sinister.usage.endpoints.v1", ENS),
        ("estimator nonzero on 'hello world'", _e("hello world") > 0, "ok"),
        ("estimator zero on empty string", _e("") == 0, "ok"),
        ("endpoint registry has 11 rows", len(list_endpoints()) == 11, str(len(list_endpoints()))),
        ("Claude Code dir reachable",
         DEFAULT_CLAUDE_DIR.exists() or args.no_state_ok,
         str(DEFAULT_CLAUDE_DIR)),
    ]
    ok = all(c[1] for c in checks)
    if args.json:
        print(json.dumps({"ok": ok, "checks": [{"name": n, "ok": p, "detail": d} for n, p, d in checks]}, indent=2))
        return 0 if ok else 1
    print(f"sinister-usage v{__version__} doctor :: {'OK' if ok else 'FAIL'}")
    for n, p, d in checks:
        mark = "[OK]  " if p else "[FAIL]"
        print(f"  {mark} {n}  ({d})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
