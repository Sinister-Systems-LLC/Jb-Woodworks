# Sinister Sanctum :: sinister-login :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
from __future__ import annotations
import argparse
import json
import sys

from . import __version__
from .providers import PROVIDERS, get_provider, provider_status
from .api import status_all, resolve_active, doctor, print_env_for, add_to_envfile


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sinister-login",
        description="Sinister Sanctum :: jcode-login parity (11-provider auth wallet)",
    )
    p.add_argument("--version", action="version", version=f"sinister-login {__version__}")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("providers", help="list all 11 providers + config status")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("status", help="show every provider's configured/missing state")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("current", help="show the active provider (first configured per preference)")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("doctor", help="diagnose one provider (env + optional TCP probe)")
    sp.add_argument("provider")
    sp.add_argument("--probe", action="store_true",
                    help="attempt a TCP-only reachability check (no HTTP body, no auth)")
    sp.add_argument("--timeout", type=float, default=3.0)
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("env", help="print export commands for one provider")
    sp.add_argument("provider")

    sp = sub.add_parser("add", help="write a provider key into ~/.sinister/login.env (operator-only)")
    sp.add_argument("provider")
    sp.add_argument("--key", required=True)
    sp.add_argument("--envfile", default=None)
    sp.add_argument("--allow-plaintext", action="store_true",
                    help="REQUIRED: confirms you accept plaintext-on-disk")
    sp.add_argument("--json", action="store_true")

    sub.add_parser("matrix", help="print the jcode parity matrix row for this tool")

    return p


def _print_providers_table(json_out: bool) -> int:
    rows = status_all()
    if json_out:
        print(json.dumps(rows, indent=2))
        return 0
    w_slug = max(len(r["slug"]) for r in rows)
    w_disp = max(len(r["display"]) for r in rows)
    print(f"{'slug'.ljust(w_slug)}  {'provider'.ljust(w_disp)}  auth     configured  key-env")
    print("-" * (w_slug + w_disp + 36))
    for r in rows:
        cfg = "yes" if r["configured"] else "no"
        key = r["key_env_found"] or "—"
        print(f"{r['slug'].ljust(w_slug)}  {r['display'].ljust(w_disp)}  "
              f"{r['auth'].ljust(7)}  {cfg.ljust(10)}  {key}")
    return 0


def _print_current(json_out: bool) -> int:
    s = resolve_active()
    if json_out:
        print(json.dumps(s, indent=2))
        return 0 if s else 2
    if not s:
        print("sinister-login: no provider configured. Run `sinister login providers` to see the list.")
        return 2
    print(f"active: {s['slug']} ({s['display']})")
    print(f"  auth:       {s['auth']}")
    print(f"  endpoint:   {s['endpoint'] or '(none)'}")
    print(f"  key-env:    {s['key_env_found'] or '(local)'}")
    return 0


def _print_matrix_row() -> int:
    print("| jcode `login --provider` (11 providers) | "
          "`tools/sinister-login/` | shipped v0.1.0 | sanctum | "
          "11 providers, env-var first, opt-in TCP probe, refuses plaintext by default |")
    return 0


def main(argv=None) -> int:
    p = _parser()
    args = p.parse_args(argv)
    cmd = args.cmd

    if cmd is None:
        p.print_help()
        return 0

    if cmd in ("providers", "status"):
        return _print_providers_table(getattr(args, "json", False))
    if cmd == "current":
        return _print_current(getattr(args, "json", False))
    if cmd == "doctor":
        r = doctor(args.provider, probe=args.probe, timeout_s=args.timeout)
        if getattr(args, "json", False):
            print(json.dumps(r, indent=2))
        else:
            ok = "OK" if r.get("ok") else "FAIL"
            print(f"[{ok}] {r.get('slug')} ({r.get('display', '?')})")
            print(f"  configured: {r.get('configured')}")
            if r.get("probed"):
                print(f"  reachable:  {r.get('reachable')}")
            if r.get("missing_envs"):
                print(f"  missing:    {', '.join(r['missing_envs'])}")
            if r.get("error"):
                print(f"  error:      {r['error']}")
            if r.get("notes"):
                print(f"  notes:      {r['notes']}")
        return 0 if r.get("ok") else 2
    if cmd == "env":
        lines = print_env_for(args.provider)
        if not lines:
            print(f"sinister-login: unknown provider `{args.provider}`", file=sys.stderr)
            return 2
        for ln in lines:
            print(ln)
        return 0
    if cmd == "add":
        r = add_to_envfile(args.provider, args.key,
                           envfile_path=args.envfile,
                           allow_plaintext=args.allow_plaintext)
        out = json.dumps(r, indent=2) if getattr(args, "json", False) else (
            f"OK -> {r['path']} ({r['env_name']})" if r.get("ok") else f"REFUSED: {r.get('error')}"
        )
        print(out)
        return 0 if r.get("ok") else 2
    if cmd == "matrix":
        return _print_matrix_row()

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
