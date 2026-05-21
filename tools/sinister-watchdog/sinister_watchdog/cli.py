"""sinister-watchdog :: CLI surface.

Author: RKOJ-ELENO :: 2026-05-21
License: AGPL-3.0-or-later

Commands:
  status        Print a one-shot snapshot — heartbeats, stale agents, mcp count.
  start         Run the watchdog loop in the foreground.
  start --bg    Spawn the loop detached (no console window on Windows).
  stop          Kill the daemon via pid file.
  tail [N]      Print the last N lines of `_shared-memory/watchdog.log` (default 40).
  probe         Probe MCP servers once and print results.
  tick          Run one full loop iteration (debug).
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from .core import (
    SanctumPaths,
    Watchdog,
    load_registry,
    probe_mcp_servers,
    scan_heartbeats,
    snapshot_status,
)


def _cmd_status(args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    snap = snapshot_status(paths)
    if args.json:
        print(json.dumps(snap, indent=2))
        return 0

    print(f"sinister-watchdog :: status @ {snap['ts_utc']}")
    print(f"  sanctum_root        : {snap['sanctum_root']}")
    print(f"  daemon_running      : {snap['running']}   (pid file: {snap['pid_file']})")
    print(f"  agents (total/stale): {snap['agent_total']} / {snap['stale_count']}")
    print(f"  mcp servers config  : {len(snap['mcp_servers_configured'])} ({', '.join(snap['mcp_servers_configured']) or '—'})")
    print(f"  log                 : {snap['log_path']}")
    print()
    print("  HEARTBEATS")
    if not snap["heartbeats"]:
        print("    (none)")
    else:
        for row in snap["heartbeats"]:
            tag = "STALE" if row["stale"] else "ok   "
            print(f"    [{tag}] {row['slug']:<28} {row['age_minutes']:>6.1f} min")
    return 0


def _cmd_start(args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    if args.bg:
        # Relaunch self with --foreground in a detached process (no window).
        py = sys.executable
        cmd = [py, "-m", "sinister_watchdog", "start", "--foreground"]
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED|NEW_GROUP|NO_WINDOW
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
            start_new_session=(os.name != "nt"),
        )
        # Wait briefly for the pid file to appear so we can confirm liftoff.
        for _ in range(30):
            if paths.pid_file.exists():
                break
            time.sleep(0.1)
        print(f"watchdog spawned detached (parent-pid={proc.pid}); see {paths.watchdog_log}")
        return 0

    if paths.pid_file.exists():
        existing = paths.pid_file.read_text(encoding="utf-8").strip()
        print(f"watchdog already appears to be running (pid={existing}); use `stop` first")
        return 1

    Watchdog(
        paths=paths,
        poll_interval=float(args.interval),
        stale_minutes=float(args.stale_minutes),
        enable_mcp_probe=not args.no_mcp,
        enable_docker=not args.no_docker,
    ).run()
    return 0


def _cmd_stop(_args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    if not paths.pid_file.exists():
        print("not running (no pid file)")
        return 0
    try:
        pid = int(paths.pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        print("pid file unreadable")
        return 1
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        print(f"kill failed: {exc}")
        return 1
    try:
        paths.pid_file.unlink()
    except OSError:
        pass
    print(f"watchdog stopped (pid={pid})")
    return 0


def _cmd_tail(args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    if not paths.watchdog_log.exists():
        print("(no log yet)")
        return 0
    n = max(1, int(args.lines))
    try:
        lines = paths.watchdog_log.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        print(f"read failed: {exc}")
        return 1
    for line in lines[-n:]:
        print(line)
    return 0


def _cmd_probe(args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    results = probe_mcp_servers(paths, timeout=float(args.timeout))
    if args.json:
        print(json.dumps(results, indent=2))
        return 0
    print(f"sinister-watchdog :: probed {len(results)} mcp servers")
    for r in results:
        tag = "ok " if r["ok"] else "FAIL"
        print(f"  [{tag}] {r['name']:<22} {r.get('reason') or 'responsive'}")
    return 0


def _cmd_tick(_args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    wd = Watchdog(paths=paths)
    wd._tick(0)
    snap = snapshot_status(paths)
    print(json.dumps(snap, indent=2))
    return 0


def _cmd_registry(args: argparse.Namespace) -> int:
    paths = SanctumPaths.detect()
    reg = load_registry(paths)
    print(json.dumps(reg, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sinister-watchdog", description="Auto-online keeper for Sanctum agents + MCP servers.")
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_status = sub.add_parser("status", help="One-shot status snapshot")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=_cmd_status)

    p_start = sub.add_parser("start", help="Start the watchdog loop")
    p_start.add_argument("--bg", action="store_true", help="Spawn detached (no console window)")
    p_start.add_argument("--foreground", action="store_true", help="(internal) run in foreground")
    p_start.add_argument("--interval", type=float, default=60.0, help="Poll interval seconds (default 60)")
    p_start.add_argument("--stale-minutes", type=float, default=5.0, help="Agent stale threshold (default 5)")
    p_start.add_argument("--no-mcp", action="store_true", help="Disable MCP probes")
    p_start.add_argument("--no-docker", action="store_true", help="Disable docker checks")
    p_start.set_defaults(func=_cmd_start)

    p_stop = sub.add_parser("stop", help="Stop the watchdog daemon")
    p_stop.set_defaults(func=_cmd_stop)

    p_tail = sub.add_parser("tail", help="Tail watchdog.log")
    p_tail.add_argument("lines", nargs="?", default=40, type=int)
    p_tail.set_defaults(func=_cmd_tail)

    p_probe = sub.add_parser("probe", help="Probe MCP servers once")
    p_probe.add_argument("--timeout", type=float, default=8.0)
    p_probe.add_argument("--json", action="store_true")
    p_probe.set_defaults(func=_cmd_probe)

    p_tick = sub.add_parser("tick", help="Run one loop iteration (debug)")
    p_tick.set_defaults(func=_cmd_tick)

    p_reg = sub.add_parser("registry", help="Print the loaded registry.json")
    p_reg.set_defaults(func=_cmd_registry)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
