#!/usr/bin/env python3
"""sinister_memory_guard.py — Bun crash guard + auto-restart for Sinister Memory.

Author: RKOJ-ELENO :: 2026-05-25

Operator: Image #5 showed Bun v1.3.13 segfault (panic thread 29180 address 0x8)
in the Sinister Memory terminal. Bun's own crash report confirms "this is a bug
in Bun, not your code." This guard wraps the Bun server and auto-restarts on
any non-zero exit, with exponential backoff (2s -> 4s -> 8s, cap 30s).

Usage:
  python automations/sinister_memory_guard.py [--cmd "bun run ..."] [--cwd PATH]
  python automations/sinister_memory_guard.py --install-schtask
  python automations/sinister_memory_guard.py --status

The guard logs every crash + restart to _shared-memory/sinister-memory-crash-log.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
MEMORY_ROOT = SANCTUM_ROOT / "projects" / "sinister-memory"
CRASH_LOG = SANCTUM_ROOT / "_shared-memory" / "sinister-memory-crash-log.jsonl"
DEFAULT_CMD = ["bun", "run", "src/sinister_memory/server.ts"]
MAX_BACKOFF = 30
TASK_NAME = "SinisterMemoryGuard"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(row: dict) -> None:
    try:
        CRASH_LOG.parent.mkdir(parents=True, exist_ok=True)
        with CRASH_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def _find_entry_point(cwd: Path) -> list[str]:
    """Auto-detect the Bun entry point for sinister-memory."""
    candidates = [
        cwd / "src" / "sinister_memory" / "server.ts",
        cwd / "src" / "server.ts",
        cwd / "index.ts",
        cwd / "src" / "index.ts",
    ]
    for c in candidates:
        if c.exists():
            return ["bun", "run", str(c)]
    # Fallback: bun run start via package.json
    if (cwd / "package.json").exists():
        return ["bun", "run", "start"]
    return DEFAULT_CMD


def run_guard(cmd: list[str], cwd: Path, max_restarts: int = 0) -> None:
    """Run cmd in cwd, restarting on crash with exponential backoff."""
    backoff = 2.0
    restarts = 0
    print(f"[sinister-memory-guard] starting: {' '.join(cmd)}")
    print(f"[sinister-memory-guard] cwd: {cwd}")
    _log({"ts": _now(), "event": "guard_start", "cmd": cmd, "cwd": str(cwd)})

    while True:
        t_start = time.time()
        try:
            proc = subprocess.run(cmd, cwd=str(cwd))
            rc = proc.returncode
        except FileNotFoundError as e:
            rc = -127
            print(f"[sinister-memory-guard] command not found: {e}", file=sys.stderr)
        except KeyboardInterrupt:
            print("[sinister-memory-guard] operator Ctrl-C — exiting guard.")
            _log({"ts": _now(), "event": "guard_stop", "reason": "ctrl_c"})
            return

        elapsed = time.time() - t_start
        restarts += 1
        crash_type = "segfault" if rc in (-11, 3221225477) else f"exit_{rc}"
        print(f"[sinister-memory-guard] process exited rc={rc} ({crash_type}) "
              f"after {elapsed:.1f}s — restart #{restarts} in {backoff:.0f}s")
        _log({
            "ts": _now(), "event": "crash", "rc": rc, "crash_type": crash_type,
            "elapsed_s": round(elapsed, 1), "restart_n": restarts,
        })

        if max_restarts > 0 and restarts >= max_restarts:
            print(f"[sinister-memory-guard] max_restarts={max_restarts} reached — giving up.")
            _log({"ts": _now(), "event": "guard_stop", "reason": "max_restarts"})
            return

        # Fast crash (< 5s) → double backoff; long-lived crash → reset
        if elapsed < 5:
            backoff = min(backoff * 2, MAX_BACKOFF)
        else:
            backoff = 2.0

        time.sleep(backoff)
        print(f"[sinister-memory-guard] restarting...")
        _log({"ts": _now(), "event": "restart", "restart_n": restarts})


def install_schtask(cwd: Path, cmd: list[str]) -> int:
    """Install SinisterMemoryGuard as a user schtask (starts on logon)."""
    import shutil as _sh
    _pw = _sh.which("pythonw") or str(Path(sys.executable).parent / "pythonw.exe")
    python_exe = _pw if Path(_pw).exists() else sys.executable
    this_script = Path(__file__).resolve()
    cmd_str = " ".join(f'"{c}"' if " " in c else c for c in cmd)
    action_args = f'"{this_script}" --cwd "{cwd}" --cmd {cmd_str}'

    import subprocess as sp
    try:
        from win32com.shell import shell  # type: ignore
        pass
    except ImportError:
        pass

    result = sp.run([
        "powershell", "-NoProfile", "-Command",
        f"""
$action = New-ScheduledTaskAction -Execute '{python_exe}' -Argument '{this_script} --cwd "{cwd}"'
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Output 'OK'
"""
    ], capture_output=True, text=True)
    if "OK" in result.stdout:
        print(f"[sinister-memory-guard] {TASK_NAME} schtask installed.")
        _log({"ts": _now(), "event": "schtask_installed", "task": TASK_NAME})
        return 0
    print(f"[sinister-memory-guard] schtask install failed: {result.stderr.strip()}", file=sys.stderr)
    return 5


def cmd_status() -> int:
    print("=== Sinister Memory Guard status ===")
    print(f"Log: {CRASH_LOG}")
    if not CRASH_LOG.exists():
        print("(no log yet — guard has not run)")
        return 0
    lines = CRASH_LOG.read_text(encoding="utf-8").splitlines()[-10:]
    for line in lines:
        try:
            row = json.loads(line)
            print(f"  {row.get('ts','?')}  {row.get('event','?')}  "
                  f"rc={row.get('rc','-')}  restart#{row.get('restart_n','-')}")
        except Exception:
            print(f"  {line[:120]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Bun crash guard + auto-restart for Sinister Memory")
    ap.add_argument("--cwd", default=str(MEMORY_ROOT), help="working directory for Bun")
    ap.add_argument("--cmd", nargs="*", help="command to run (default: auto-detect)")
    ap.add_argument("--max-restarts", type=int, default=0, help="0=infinite")
    ap.add_argument("--install-schtask", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    cwd = Path(args.cwd)
    cmd = args.cmd if args.cmd else _find_entry_point(cwd)

    if args.status:
        return cmd_status()

    if args.install_schtask:
        return install_schtask(cwd, cmd)

    run_guard(cmd, cwd, max_restarts=args.max_restarts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
