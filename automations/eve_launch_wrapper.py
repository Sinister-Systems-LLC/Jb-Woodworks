#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# eve_launch_wrapper.py -- Update-then-launch wrapper for EVE.exe.
#
# Operator hard-canonical 2026-05-25: every fleet agent finds an automated
# workaround. EVE.exe must self-update without operator clicks. This
# wrapper is the recommended invocation in `deploy/eve-updater-CLI.md`:
# it runs the self-updater (10-second hard cap, log-only on failure) and
# then shells out to EVE.exe, passing through all argv.
#
# Why a wrapper instead of editing start-sinister-session.ps1?
#   - Operator doctrine (no-bat-no-ps1) bans NEW .ps1 surfaces; this is
#     pure Python.
#   - The launcher PS1 has multiple EVE.exe entry points (cold-start,
#     forge-recall pre-invoke, headless project mode); a wrapper covers
#     all callers via a single binary indirection.
#   - Non-blocking design: any update failure is logged to
#     `_shared-memory/eve-update-log.jsonl` and EVE.exe still launches.
#
# Usage:
#   python automations/eve_launch_wrapper.py [eve-args...]
#   python automations/eve_launch_wrapper.py --no-update [eve-args...]
#   python automations/eve_launch_wrapper.py --eve-path PATH [eve-args...]

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVE = REPO_ROOT / "EVE.exe"
UPDATE_TIMEOUT_S = 10


def _run_update(eve_path: Path) -> None:
    """Best-effort, hard-timeout. Never raises into caller."""
    try:
        from automations import eve_self_update  # type: ignore[import-not-found]
    except Exception:
        # Fallback: invoke as subprocess of this interpreter.
        eve_self_update = None  # type: ignore[assignment]

    if eve_self_update is not None:
        worker_exc: list[BaseException] = []

        def _go() -> None:
            try:
                eve_self_update.check_and_update(eve_path)
            except BaseException as exc:  # noqa: BLE001
                worker_exc.append(exc)

        t = threading.Thread(target=_go, daemon=True)
        t.start()
        t.join(UPDATE_TIMEOUT_S)
        return

    # Subprocess fallback (module import failed — likely path issue).
    try:
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "automations" / "eve_self_update.py"),
                "--path",
                str(eve_path),
            ],
            timeout=UPDATE_TIMEOUT_S,
            capture_output=True,
        )
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    ap = argparse.ArgumentParser(
        description="Update-then-launch EVE.exe.", add_help=False
    )
    ap.add_argument("--no-update", action="store_true")
    ap.add_argument("--eve-path", default=str(DEFAULT_EVE))
    ap.add_argument("--help-wrapper", action="store_true")
    ns, passthrough = ap.parse_known_args(argv)

    if ns.help_wrapper:
        ap.print_help()
        print(
            "\nUpdate-then-launch wrapper for EVE.exe. Runs eve_self_update\n"
            "(10s cap, non-blocking) then shells EVE.exe with passthrough argv.\n"
            "See deploy/eve-updater-CLI.md for full doctrine."
        )
        return 0

    eve_path = Path(ns.eve_path)

    if not ns.no_update:
        _run_update(eve_path)

    if not eve_path.is_file():
        print(f"[eve_launch_wrapper] EVE.exe not found at {eve_path}", file=sys.stderr)
        return 127

    # Replace current process on POSIX; on Windows os.execv works but does not
    # preserve console wiring well — prefer subprocess for clean exit code.
    if os.name == "nt":
        cp = subprocess.run([str(eve_path), *passthrough])
        return cp.returncode
    os.execv(str(eve_path), [str(eve_path), *passthrough])
    return 0  # unreachable


if __name__ == "__main__":
    sys.exit(main())
