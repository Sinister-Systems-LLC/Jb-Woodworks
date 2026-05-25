# Author: RKOJ-ELENO :: 2026-05-25
"""Phase 5 of the Snap auto-update pipeline.

Reverts a device to a prior cached Snap APK version. Captures pre-rollback
version via dumpsys so callers have full provenance.

Triggered when Phase 3 smoke_test.py reports ok=false AND
--rollback-on-failure was set on the upstream auto-update job.

Shared exit-code contract: 0 ok, 1 usage error, 2 env error (adb missing or
no cached APK), 3 install failure.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

CACHE_DEFAULT = Path.home() / ".sinister" / "snap-apk-cache"


def _emit(d: dict) -> None:
    sys.stdout.write(json.dumps(d, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def _adb(serial: str, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["adb", "-s", serial, *args],
        capture_output=True, text=True, timeout=timeout
    )


def _read_version(serial: str) -> str:
    r = _adb(serial, "shell", "dumpsys", "package", "com.snapchat.android", timeout=15)
    m = re.search(r"versionName=(\S+)", r.stdout)
    return m.group(1) if m else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 5 Snap APK rollback (kernel-apk lane)")
    ap.add_argument("--device-serial", required=True)
    ap.add_argument("--to-version", required=True)
    ap.add_argument("--cache-dir", default=str(CACHE_DEFAULT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cache_path = Path(args.cache_dir) / f"snap-{args.to_version}.apk"

    if args.dry_run:
        cmds = [
            f"adb -s {args.device_serial} shell dumpsys package com.snapchat.android",
            f"adb -s {args.device_serial} install -r -d {cache_path}",
        ]
        _emit({"ok": True, "phase": "rollback", "dry_run": True, "device_serial": args.device_serial, "to_version": args.to_version, "cache_path": str(cache_path), "commands": cmds})
        return 0

    if not shutil.which("adb"):
        _emit({"ok": False, "phase": "rollback", "error": "adb not on PATH"})
        return 2

    if not cache_path.is_file():
        _emit({"ok": False, "phase": "rollback", "error": f"no cached APK at {cache_path}; run acquire.py --version {args.to_version} first"})
        return 2

    from_version = _read_version(args.device_serial)

    r = _adb(args.device_serial, "install", "-r", "-d", str(cache_path), timeout=120)
    if r.returncode != 0 or "Success" not in r.stdout:
        _emit({"ok": False, "phase": "rollback", "error": "install failed", "from_version": from_version, "to_version": args.to_version, "stdout": r.stdout[-500:], "stderr": r.stderr[-500:]})
        return 3

    installed = _read_version(args.device_serial)
    verified = installed == args.to_version

    _emit({
        "ok": verified, "phase": "rollback",
        "device_serial": args.device_serial,
        "from_version": from_version,
        "to_version": args.to_version,
        "installed_version": installed,
        "verified": verified,
    })
    return 0 if verified else 3


if __name__ == "__main__":
    sys.exit(main())
