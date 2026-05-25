# Author: RKOJ-ELENO :: 2026-05-24
"""Sinister Overseer CLI entry point.

P0 SCAFFOLD -- argparse skeleton only. Real subcommands land in P1+.

Planned subcommands:
    overseer attach --project <key> [--adapter <name>]
    overseer detach --project <key>
    overseer list
    overseer status [--all]
    overseer dryrun --project <key> [--inject-symptom <name>]
    overseer apply --proposal <id>
    overseer lessons --project <key>  (P3+)
    overseer fleet-lessons             (P4+)
    overseer aggregator --dryrun       (P4+)
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser. Kept separate so tests can exercise it."""
    parser = argparse.ArgumentParser(
        prog="overseer",
        description="Sinister Overseer -- meta-agent that watches + fixes + learns across attached projects.",
    )
    sub = parser.add_subparsers(dest="command")

    p_attach = sub.add_parser("attach", help="Attach Overseer to a project")
    p_attach.add_argument("--project", required=True, help="Project key from projects.json")
    p_attach.add_argument("--adapter", help="Adapter class override (default: auto-detect from registry)")

    p_detach = sub.add_parser("detach", help="Detach Overseer from a project")
    p_detach.add_argument("--project", required=True, help="Project key")

    sub.add_parser("list", help="List attached projects + their status")

    p_status = sub.add_parser("status", help="Show Overseer status")
    p_status.add_argument("--all", action="store_true", help="Show all attachments")
    p_status.add_argument("--project", help="Status for a specific attachment")

    p_dryrun = sub.add_parser("dryrun", help="Simulate one watch cycle without applying")
    p_dryrun.add_argument("--project", required=True)
    p_dryrun.add_argument("--inject-symptom", help="(test-only) inject a synthetic symptom")

    p_apply = sub.add_parser("apply", help="Apply a queued proposal")
    p_apply.add_argument("--proposal", required=True, help="Proposal ID")

    sub.add_parser("version", help="Print version")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point used by tests + main_cli_entrypoint."""
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        from overseer import __version__
        print(f"sinister-overseer {__version__} (P0 scaffold)")
        return 0

    if args.command == "list":
        # P0: read config/attached-projects.json and dump status
        from overseer.config_io import list_attachments
        attachments = list_attachments()
        if not attachments:
            print("No attachments. Use `overseer attach --project <key>` to add one.")
            return 0
        print("Attached projects:")
        for a in attachments:
            print(f"  - {a['project_key']:<40s} status={a['status']:<10s} adapter={a.get('adapter','(auto)')}")
        return 0

    # P0: all other commands -- print not-yet-implemented
    print(f"[P0 scaffold] command '{args.command}' not yet implemented.")
    print(f"  See docs/07-evolution-roadmap.md for the phase plan.")
    print(f"  Args: {vars(args)}")
    return 0


def main_cli_entrypoint() -> None:
    """Console-script entrypoint declared in pyproject.toml."""
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
