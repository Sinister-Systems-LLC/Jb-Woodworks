# Sinister Sanctum :: sinister-provider :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import argparse
import json
import sys

from .api import list_providers as _ll, current as _curr, add_provider as _add, remove_provider as _rm


def _parser():
    p = argparse.ArgumentParser(
        prog="sinister-provider",
        description="Sinister Sanctum :: provider list/current/add (jcode provider parity)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("current")
    sp = sub.add_parser("add")
    sp.add_argument("--provider", required=True)
    sp.add_argument("--key", default=None)
    sp.add_argument("--endpoint", default=None)
    sp.add_argument("--base-url", default=None)
    sp.add_argument("--use-env", action="store_true")
    sp.add_argument("--env", default=None)
    sp = sub.add_parser("remove")
    sp.add_argument("--provider", required=True)
    return p


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.cmd == "list":
        print(json.dumps(_ll(), indent=2, default=str))
        return 0
    if args.cmd == "current":
        print(json.dumps(_curr(), indent=2, default=str))
        return 0
    if args.cmd == "add":
        print(json.dumps(_add(args.provider, key=args.key, endpoint=args.endpoint,
                              base_url=args.base_url, use_env=args.use_env, env_var=args.env),
                         indent=2, default=str))
        return 0
    if args.cmd == "remove":
        print(json.dumps(_rm(args.provider), indent=2, default=str))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
