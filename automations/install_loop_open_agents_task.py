#!/usr/bin/env python3
"""install_loop_open_agents_task.py — register SinisterLoopOpenAgents schtask.

Author: RKOJ-ELENO :: 2026-05-25

Operator (verbatim 2026-05-25 ~18:09Z): "i need looper to work on the open
agents". iter-20 + iter-24 shipped the looper. This iter REGISTERS it as
a Windows scheduled task that fires every 15 minutes, even when no Claude
session is running -- so the live fleet keeps getting scored + checkpointed
all on its own.

Per no-bat-no-ps1 doctrine: this installer is Python; it calls schtasks.exe
inline to register the task (windowless via pythonw.exe + the cmd flow is
hidden by schtasks itself when run from Task Scheduler).

USAGE:
  python automations/install_loop_open_agents_task.py            # install
  python automations/install_loop_open_agents_task.py --uninstall
  python automations/install_loop_open_agents_task.py --status
  python automations/install_loop_open_agents_task.py --dry-run  # show cmd

Cadence: every 15 minutes (matches the heartbeat-fresh window of 30 min so
each tick sees fresh agents). Configurable via --minutes N.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SANCTUM = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
TASK_NAME = "SinisterLoopOpenAgents"
LOOP_PY = SANCTUM / "automations" / "loop_open_agents.py"
PYTHONW = r"C:\Users\Zonia\AppData\Local\Programs\Python\Python312\pythonw.exe"

_NO_WIN = 0x08000000 if os.name == "nt" else 0


def _run_schtasks(*args: str, dry_run: bool = False) -> tuple[int, str]:
    cmd = ["schtasks.exe", *args]
    if dry_run:
        return 0, f"[dry-run] {' '.join(cmd)}"
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                       creationflags=_NO_WIN)
    return r.returncode, (r.stdout + r.stderr).strip()


def status() -> dict:
    rc, out = _run_schtasks("/Query", "/TN", TASK_NAME, "/FO", "csv")
    return {"installed": rc == 0, "output": out}


def install(minutes: int = 15, dry_run: bool = False) -> dict:
    if not LOOP_PY.exists():
        return {"ok": False, "error": f"missing: {LOOP_PY}"}
    if not Path(PYTHONW).exists():
        return {"ok": False, "error": f"missing: {PYTHONW}"}
    # Delete existing first (idempotent).
    _run_schtasks("/Delete", "/TN", TASK_NAME, "/F", dry_run=dry_run)
    # Build the command. Use pythonw (windowless) to avoid cmd flash per
    # iter-20 popup-fix doctrine. --no-checkpoint=false (default) so each
    # tick saves agent state.
    tr_cmd = f'"{PYTHONW}" "{LOOP_PY}"'
    rc, out = _run_schtasks(
        "/Create", "/TN", TASK_NAME,
        "/TR", tr_cmd,
        "/SC", "MINUTE",
        "/MO", str(minutes),
        "/RL", "LIMITED",
        "/F",
        dry_run=dry_run,
    )
    return {"ok": rc == 0, "interval_min": minutes, "tr": tr_cmd, "output": out}


def uninstall(dry_run: bool = False) -> dict:
    rc, out = _run_schtasks("/Delete", "/TN", TASK_NAME, "/F", dry_run=dry_run)
    return {"ok": rc == 0, "output": out}


def run_now() -> dict:
    rc, out = _run_schtasks("/Run", "/TN", TASK_NAME)
    return {"ok": rc == 0, "output": out}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--uninstall", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--run-now", action="store_true")
    p.add_argument("--minutes", type=int, default=15)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    import json
    if args.status:
        r = status()
    elif args.uninstall:
        r = uninstall(dry_run=args.dry_run)
    elif args.run_now:
        r = run_now()
    else:
        r = install(minutes=args.minutes, dry_run=args.dry_run)
    print(json.dumps(r, indent=2, default=str))
    return 0 if r.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
