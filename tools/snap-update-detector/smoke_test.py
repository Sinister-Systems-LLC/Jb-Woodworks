# Author: RKOJ-ELENO :: 2026-05-25
"""Phase 3 of the Snap auto-update pipeline.

Post-install smoke test: installs APK on a connected ADB device, verifies
Snap launches + stays alive + reports the installed versionName.

Does NOT drive UI signup flow (SnapFlow.kt on-device owns that). This
just confirms install + launch + alive. Failure here -> trigger Phase 5
rollback.py.

Shared exit-code contract: 0 ok, 1 usage error, 2 env error (adb missing),
3 device/smoke failure.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _emit(d: dict) -> None:
    sys.stdout.write(json.dumps(d, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _adb(serial: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["adb", "-s", serial, *args],
        capture_output=True, text=True, timeout=timeout
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 3 Snap APK smoke test (kernel-apk lane)")
    ap.add_argument("--apk-path", required=True)
    ap.add_argument("--device-serial", required=True)
    ap.add_argument("--timeout-sec", type=int, default=120)
    ap.add_argument("--first-render-wait-sec", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        cmds = [
            f"adb -s {args.device_serial} install -r -d {args.apk_path}",
            f"adb -s {args.device_serial} shell am start -n com.snapchat.android/.LandingPageActivity",
            f"adb -s {args.device_serial} shell pidof com.snapchat.android",
            f"adb -s {args.device_serial} shell dumpsys package com.snapchat.android",
        ]
        _emit({"ok": True, "phase": "smoke", "dry_run": True, "device_serial": args.device_serial, "apk_path": args.apk_path, "commands": cmds})
        return 0

    if not shutil.which("adb"):
        _emit({"ok": False, "phase": "smoke", "error": "adb not on PATH"})
        return 2

    apk = Path(args.apk_path)
    if not apk.is_file():
        _emit({"ok": False, "phase": "smoke", "error": f"apk not found: {apk}"})
        return 2

    errors: list[str] = []

    # 1) install
    r = _adb(args.device_serial, "install", "-r", "-d", str(apk), timeout=args.timeout_sec)
    if r.returncode != 0 or "Success" not in r.stdout:
        _emit({"ok": False, "phase": "smoke", "error": "install failed", "stdout": r.stdout[-500:], "stderr": r.stderr[-500:]})
        return 3

    # 2) launch
    r = _adb(args.device_serial, "shell", "am", "start", "-n", "com.snapchat.android/.LandingPageActivity", timeout=15)
    if r.returncode != 0:
        errors.append(f"am start rc={r.returncode}")

    # 3) wait for first render + alive
    deadline = time.monotonic() + args.first_render_wait_sec
    alive = False
    while time.monotonic() < deadline:
        r = _adb(args.device_serial, "shell", "pidof", "com.snapchat.android", timeout=5)
        if r.stdout.strip().isdigit():
            alive = True
            break
        time.sleep(2)

    if not alive:
        errors.append(f"snap not alive after {args.first_render_wait_sec}s")

    # 4) verify installed version
    r = _adb(args.device_serial, "shell", "dumpsys", "package", "com.snapchat.android", timeout=15)
    m = re.search(r"versionName=(\S+)", r.stdout)
    version_installed = m.group(1) if m else "unknown"

    ok = alive and not errors and version_installed != "unknown"
    _emit({
        "ok": ok, "phase": "smoke",
        "device_serial": args.device_serial,
        "apk_path": str(apk),
        "version_installed": version_installed,
        "snap_alive": alive,
        "errors": errors,
    })
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
