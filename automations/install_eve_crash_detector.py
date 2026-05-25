#!/usr/bin/env python3
"""Install / uninstall SinisterEveCrashWatchdog schtask.

Author: RKOJ-ELENO :: 2026-05-25

Schtask: SinisterEveCrashWatchdog, runs every 5 minutes:
  python "D:\\Sinister Sanctum\\automations\\eve_crash_detector.py" --scan --auto-kill
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

TASK_NAME = "SinisterEveCrashWatchdog"
SANCTUM_ROOT = Path("D:/Sinister Sanctum")
DETECTOR = SANCTUM_ROOT / "automations" / "eve_crash_detector.py"


def _python_exe() -> str:
    return shutil.which("python") or shutil.which("python3") or sys.executable


def build_install_cmd() -> list[str]:
    py = _python_exe()
    action = f'"{py}" "{DETECTOR}" --scan --auto-kill'
    return [
        "schtasks.exe", "/Create", "/F",
        "/TN", TASK_NAME,
        "/TR", action,
        "/SC", "MINUTE", "/MO", "5",
        "/RL", "LIMITED",
    ]


def build_uninstall_cmd() -> list[str]:
    return ["schtasks.exe", "/Delete", "/TN", TASK_NAME, "/F"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not DETECTOR.exists() and not args.uninstall:
        print(f"[install] detector script not found: {DETECTOR}", file=sys.stderr)
        return 2

    cmd = build_uninstall_cmd() if args.uninstall else build_install_cmd()
    print("[install] schtasks command:")
    print("  " + " ".join(f'"{a}"' if " " in a else a for a in cmd))

    if args.dry_run:
        print("[install] --dry-run: not executing")
        return 0

    cp = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(cp.stdout or "")
    sys.stderr.write(cp.stderr or "")
    print(f"[install] exit={cp.returncode}")
    return cp.returncode


if __name__ == "__main__":
    sys.exit(main())
