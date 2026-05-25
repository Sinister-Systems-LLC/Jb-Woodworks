#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
# sinister_link_poller.py -- Python replacement for the 0-byte legacy
# sinister-link-poller.ps1. Runs on a 5-min schtask (registered by
# deploy/first_time_setup.py) to keep peer state fresh.
#
# Per operator hard-canonical 2026-05-25 (NO .bat / NO .ps1 / EXECUTE
# EVERYTHING): NEW automations are Python. Calling an existing .ps1 is
# fine, so this poller shells out to the unchanged sinister-link.ps1
# state machine (Sync + Health actions) without re-implementing the
# pairing protocol.
#
# Steps:
#   1. Resolve sanctum root + sinister-link.ps1 location.
#   2. If sinister-link-state.json says state=unpaired, log heartbeat
#      and exit 0 (no-op until operator pairs).
#   3. Run `sinister-link.ps1 -Action Sync` (git pull peer branch).
#   4. Run `sinister-link.ps1 -Action Health` (peer reachability check).
#   5. Append a row to _shared-memory/sinister-link-poll-log.jsonl with
#      both exit codes + stdout tail + duration.
#
# Exit codes: 0 ok / 1 link-error / 2 io-fail.
#
# Composes with:
#   _shared-memory/knowledge/sinister-link-doctrine-2026-05-25.md
#   _shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT") or r"D:\Sinister Sanctum")
LINK_PS1 = SANCTUM_ROOT / "automations" / "sinister-link.ps1"
STATE_PATH = SANCTUM_ROOT / "_shared-memory" / "sinister-link-state.json"
LOG_PATH = SANCTUM_ROOT / "_shared-memory" / "sinister-link-poll-log.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_log(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _read_state() -> dict | None:
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _run_link(action: str, timeout: int = 60) -> tuple[int, str]:
    if not LINK_PS1.exists():
        return 127, f"sinister-link.ps1 missing at {LINK_PS1}"
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(LINK_PS1),
        "-Action",
        action,
        "-SanctumRoot",
        str(SANCTUM_ROOT),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as exc:
        return 126, f"spawn-fail: {exc}"
    tail = (proc.stdout or proc.stderr or "")[-400:]
    return proc.returncode, tail


def main() -> int:
    started = time.time()
    state = _read_state()
    paired = bool(state and (state.get("state") == "paired"))
    if not paired:
        _append_log({
            "ts_utc": _utc_now(),
            "event": "skip-unpaired",
            "state": (state or {}).get("state", "absent"),
            "duration_ms": int((time.time() - started) * 1000),
        })
        return 0
    sync_rc, sync_tail = _run_link("Sync", timeout=90)
    health_rc, health_tail = _run_link("Health", timeout=30)
    overall = 0 if sync_rc == 0 and health_rc == 0 else 1
    _append_log({
        "ts_utc": _utc_now(),
        "event": "poll",
        "peer": (state or {}).get("peer_name", ""),
        "sync_exit": sync_rc,
        "sync_tail": sync_tail,
        "health_exit": health_rc,
        "health_tail": health_tail,
        "duration_ms": int((time.time() - started) * 1000),
    })
    return overall


if __name__ == "__main__":
    sys.exit(main())
