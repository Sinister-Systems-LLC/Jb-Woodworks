"""FSEvents-based live tail (P3). RKOJ-ELENO :: 2026-05-24.

This module is a STUB until the farm is connected. The real implementation
runs ON THE FARM (spawned by bridge_daemon over SSH) and uses `fswatch -1`
on chat.db-wal to wake up + re-poll. On Windows this module exits 1 with a
clear message; on macOS without fswatch installed it surfaces a brew hint.

See plans/p3-bridge-daemon-acceptance.md §1 for the target shape.
"""
from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path


def precheck() -> dict:
    """Return readiness info without running the tail."""
    out = {
        "platform": platform.system(),
        "fswatch_path": shutil.which("fswatch"),
        "chatdb_default": str(Path.home() / "Library" / "Messages" / "chat.db"),
        "ready": False,
        "reason": "",
    }
    if out["platform"] != "Darwin":
        out["reason"] = "tail.py only runs on macOS — invoke from bridge_daemon over SSH to the farm"
        return out
    if not out["fswatch_path"]:
        out["reason"] = "fswatch not on PATH — install via `brew install fswatch`"
        return out
    if not Path(out["chatdb_default"]).exists():
        out["reason"] = f"chat.db not found at {out['chatdb_default']} — operator must sign into Messages first"
        return out
    out["ready"] = True
    return out


def main() -> int:
    info = precheck()
    if not info["ready"]:
        print(f"[tail] not ready: {info['reason']}", file=sys.stderr)
        print(f"[tail] info: {info}", file=sys.stderr)
        return 1
    # The real `while True: fswatch + emit_new` loop lands when the farm is connected.
    # Keeping it stubbed here so accidental invocation on Windows fails clean.
    print("[tail] precheck OK; live loop not yet implemented — see plans/p3-bridge-daemon-acceptance.md §1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
