# Author: RKOJ-ELENO :: 2026-05-23
# License: AGPL-3.0-or-later

"""CLI entry: `python -m sinister_browser <subcommand>` or `sinister-browser`."""

from __future__ import annotations

import argparse
import json
import sys

from sinister_browser import __version__
from sinister_browser.probe import probe


def _cmd_probe(args: argparse.Namespace) -> int:
    result = probe(host=args.host, port=args.port, timeout=args.timeout)
    if args.json:
        print(json.dumps({
            "exit_code": result.exit_code,
            "summary": result.summary,
            "host": result.host,
            "port": result.port,
            "tcp_ok": result.tcp_ok,
            "handshake_ok": result.handshake_ok,
            "server_header": result.server_header,
            "accept_header_match": result.accept_header_match,
            "error": result.error,
        }, indent=2))
    else:
        status_label = {0: "ALIVE", 2: "NOT-INSTALLED", 3: "UNREACHABLE"}.get(
            result.exit_code, "?"
        )
        print(f"sinister-browser :: {result.host}:{result.port} :: {status_label}")
        print(f"  {result.summary}")
        if result.server_header:
            print(f"  server header: {result.server_header}")
    return result.exit_code


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"sinister-browser {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sinister-browser",
        description="Sinister wrapper around firefox-agent-bridge (Layer A probe).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_probe = sub.add_parser("probe", help="Probe the upstream bridge WebSocket")
    p_probe.add_argument("--host", default="127.0.0.1")
    p_probe.add_argument("--port", type=int, default=8766)
    p_probe.add_argument("--timeout", type=float, default=3.0)
    p_probe.add_argument("--json", action="store_true", help="Emit JSON")
    p_probe.set_defaults(func=_cmd_probe)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=_cmd_version)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(run())
