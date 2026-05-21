# Sinister Sanctum :: sinister-model :: CLI
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later

from __future__ import annotations
import argparse
import json
import sys

from .api import (
    list_models as _list,
    current as _curr,
    providers as _provs,
    propose_switch as _switch,
    set_sanctum_root,
)


def _parser():
    p = argparse.ArgumentParser(
        prog="sinister-model",
        description="Sinister Sanctum :: model list/current/switch (jcode model parity)",
    )
    p.add_argument("--sanctum-root", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sp = sub.add_parser("current")
    sp.add_argument("--task-class", required=True)
    sp = sub.add_parser("switch")
    sp.add_argument("--task-class", required=True)
    sp.add_argument("--primary", required=True)
    sp.add_argument("--rationale", default=None)
    sub.add_parser("providers")
    return p


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.sanctum_root:
        set_sanctum_root(args.sanctum_root)
    if args.cmd == "list":
        print(json.dumps(_list(), indent=2, default=str))
        return 0
    if args.cmd == "current":
        rec = _curr(args.task_class)
        print(json.dumps(rec, indent=2, default=str))
        return 0 if rec else 1
    if args.cmd == "switch":
        print(json.dumps(_switch(args.task_class, args.primary, rationale=args.rationale), indent=2, default=str))
        return 0
    if args.cmd == "providers":
        print(json.dumps(_provs(), indent=2, default=str))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
