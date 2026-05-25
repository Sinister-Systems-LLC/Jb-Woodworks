#!/usr/bin/env python3
"""EVE.exe crash / hang detector + auto-rescue.

Author: RKOJ-ELENO :: 2026-05-25

Operator (verbatim 2026-05-25 ~06:14Z):
  "C:\\Users\\Zonia\\Desktop\\Kill-Stuck-EVE.bat I need you to detect eve
   crashes and run this especially if they crash before you compile an exe."

Five signals:
  A. Zombie process     - alive PID, 0% CPU x2 samples, status stopped/zombie OR
                          alive >5min with no recent file I/O.
  B. No main window     - EVE.exe alive >15s with zero visible top-level window.
  C. mintty exit 126    - recent eve-incidents.jsonl rows with "exit 126" pattern.
  D. Orphan conhost     - conhost.exe with dead parent PID.
  E. Stale lock file    - lock older than 30min, no matching live EVE.exe.

Actions:
  --scan                 detect-only (exit 0 healthy, 1 crash detected)
  --scan --auto-kill     detect AND run Kill-Stuck-EVE.bat + log
  --pre-compile          ALWAYS kill running EVE.exe before rebuild (exit 0/2)
  --pre-compile --dry-run print kill targets without killing
  --status               print last 5 detection events + current EVE.exe procs

Safety: ONLY triggers Kill-Stuck-EVE.bat (title-targeted, image-name EVE.exe).
Does NOT broad-kill claude.exe / mintty / operator's sessions.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

try:
    import psutil
except ImportError:
    print("[eve-crash-detector] FATAL: psutil missing. pip install psutil", file=sys.stderr)
    sys.exit(3)


SANCTUM_ROOT = Path("D:/Sinister Sanctum")
KILL_BAT = Path(r"C:\Users\Zonia\Desktop\Kill-Stuck-EVE.bat")
CRASH_LOG = SANCTUM_ROOT / "_shared-memory" / "eve-crash-log.jsonl"
INCIDENTS = SANCTUM_ROOT / "_shared-memory" / "eve-incidents.jsonl"
LOCK_CANDIDATES = [
    Path.home() / ".eve" / "eve.lock",
    SANCTUM_ROOT / "_shared-memory" / ".eve-running.lock",
]
EVE_IMAGE_NAMES = {"eve.exe"}
ALIVE_GRACE_S = 15        # signal B grace
ALIVE_LONG_S = 300        # signal A "alive too long"
LOCK_STALE_S = 30 * 60    # signal E

# Auto-restart: paths tried in order
EVE_EXE_CANDIDATES = [
    SANCTUM_ROOT / "EVE.exe",
    SANCTUM_ROOT / "automations" / "eve-launcher" / "dist" / "EVE.exe",
]
# Cooldown: don't restart more than once every N seconds (prevents boot-loop)
RESTART_COOLDOWN_S = 180      # 3 min between restarts (was 90s -- too aggressive)
MAX_RESTARTS_PER_HOUR = 3     # stop restart loop after 3 failures in 1h
_RESTART_STATE = SANCTUM_ROOT / "_shared-memory" / ".eve-last-restart.json"
INCIDENT_LOOKBACK_S = 5 * 60


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_jsonl(path: Path, row: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[eve-crash-detector] log append failed: {e}", file=sys.stderr)


# ---------- window enum ----------

def _visible_window_pids() -> set[int]:
    """Return set of PIDs that own at least one visible top-level window."""
    user32 = ctypes.windll.user32
    EnumWindows = user32.EnumWindows
    IsWindowVisible = user32.IsWindowVisible
    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    pids: set[int] = set()

    def _cb(hwnd, _lparam):
        try:
            if IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value:
                    pids.add(int(pid.value))
        except Exception:
            pass
        return True

    EnumWindows(WNDENUMPROC(_cb), 0)
    return pids


# ---------- signal helpers ----------

def _eve_procs() -> list[psutil.Process]:
    out: list[psutil.Process] = []
    for p in psutil.process_iter(["pid", "name", "create_time", "status"]):
        try:
            if (p.info["name"] or "").lower() in EVE_IMAGE_NAMES:
                out.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return out


def signal_a_zombie() -> tuple[bool, dict]:
    hits = []
    for p in _eve_procs():
        try:
            status = p.status()
            cpu1 = p.cpu_percent(interval=1.0)
            cpu2 = p.cpu_percent(interval=1.0)
            age = time.time() - p.create_time()
            zombie = status in ("stopped", "zombie")
            idle_old = (cpu1 == 0.0 and cpu2 == 0.0 and age > ALIVE_LONG_S)
            if zombie or idle_old:
                hits.append({"pid": p.pid, "status": status, "cpu": [cpu1, cpu2], "age_s": int(age)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return (bool(hits), {"signal": "A_zombie", "hits": hits})


def signal_b_no_window() -> tuple[bool, dict]:
    vis = _visible_window_pids()
    hits = []
    for p in _eve_procs():
        try:
            age = time.time() - p.create_time()
            if age > ALIVE_GRACE_S and p.pid not in vis:
                hits.append({"pid": p.pid, "age_s": int(age)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return (bool(hits), {"signal": "B_no_window", "hits": hits})


def signal_c_mintty_126() -> tuple[bool, dict]:
    if not INCIDENTS.exists():
        return (False, {"signal": "C_mintty_126", "hits": []})
    cutoff = time.time() - INCIDENT_LOOKBACK_S
    hits = []
    try:
        with INCIDENTS.open("r", encoding="utf-8", errors="replace") as f:
            tail = f.readlines()[-50:]
        for line in tail:
            line_l = line.lower()
            if "exit 126" in line_l or "exit code 126" in line_l or ("mintty" in line_l and "126" in line_l):
                try:
                    row = json.loads(line)
                    ts = row.get("ts") or row.get("timestamp") or ""
                    if ts:
                        try:
                            t = datetime.strptime(ts.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z").timestamp()
                            if t < cutoff:
                                continue
                        except Exception:
                            pass
                    hits.append({"line": line.strip()[:200]})
                except Exception:
                    hits.append({"line": line.strip()[:200]})
    except Exception as e:
        return (False, {"signal": "C_mintty_126", "error": str(e)})
    return (bool(hits), {"signal": "C_mintty_126", "hits": hits[:5]})


def signal_d_orphan_conhost() -> tuple[bool, dict]:
    hits = []
    alive_pids = {p.pid for p in psutil.process_iter(["pid"])}
    for p in psutil.process_iter(["pid", "name", "ppid"]):
        try:
            if (p.info["name"] or "").lower() == "conhost.exe":
                ppid = p.info.get("ppid")
                if ppid and ppid not in alive_pids:
                    hits.append({"pid": p.pid, "dead_ppid": ppid})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return (bool(hits), {"signal": "D_orphan_conhost", "hits": hits[:5]})


def signal_e_stale_lock() -> tuple[bool, dict]:
    eve_pids = {p.pid for p in _eve_procs()}
    hits = []
    for lock in LOCK_CANDIDATES:
        if not lock.exists():
            continue
        try:
            age = time.time() - lock.stat().st_mtime
            content = lock.read_text(encoding="utf-8", errors="replace").strip()
            lock_pid = None
            for tok in content.replace("\n", " ").split():
                if tok.isdigit():
                    lock_pid = int(tok)
                    break
            if age > LOCK_STALE_S and (lock_pid is None or lock_pid not in eve_pids):
                hits.append({"lock": str(lock), "age_s": int(age), "lock_pid": lock_pid})
        except Exception:
            continue
    return (bool(hits), {"signal": "E_stale_lock", "hits": hits})


SIGNALS = [signal_a_zombie, signal_b_no_window, signal_c_mintty_126, signal_d_orphan_conhost, signal_e_stale_lock]


def run_all_signals() -> tuple[bool, list[dict]]:
    results = []
    crash = False
    for fn in SIGNALS:
        try:
            triggered, detail = fn()
        except Exception as e:
            triggered, detail = False, {"signal": fn.__name__, "error": str(e)}
        detail["triggered"] = triggered
        results.append(detail)
        if triggered:
            crash = True
    return crash, results


# ---------- actions ----------

def run_kill_bat(reason: str, signals: list[dict]) -> int:
    if not KILL_BAT.exists():
        print(f"[eve-crash-detector] Kill-Stuck-EVE.bat NOT FOUND at {KILL_BAT}", file=sys.stderr)
        return 4
    try:
        cp = subprocess.run([str(KILL_BAT)], shell=False, timeout=30,
                            capture_output=True, text=True)
        rc = cp.returncode
    except subprocess.TimeoutExpired:
        rc = -1
    _append_jsonl(CRASH_LOG, {
        "ts": _now_iso(),
        "event": "auto_kill",
        "reason": reason,
        "bat_rc": rc,
        "signals": [s for s in signals if s.get("triggered")],
    })
    return rc


def _eve_exe_path() -> Path | None:
    """Return first existing EVE.exe candidate."""
    for p in EVE_EXE_CANDIDATES:
        if p.exists():
            return p
    return None


def _restart_cooldown_ok() -> bool:
    """Return True if enough time has passed since last restart AND under hourly cap."""
    try:
        if not _RESTART_STATE.exists():
            return True
        state = json.loads(_RESTART_STATE.read_text(encoding="utf-8"))
        last_ts = state.get("ts", 0)
        if (time.time() - last_ts) < RESTART_COOLDOWN_S:
            return False
        # Count restarts in the last hour to prevent restart loops
        restarts_1h = [t for t in state.get("history", []) if (time.time() - t) < 3600]
        if len(restarts_1h) >= MAX_RESTARTS_PER_HOUR:
            print(f"[eve-crash-detector] auto-restart: hourly cap {MAX_RESTARTS_PER_HOUR} hit -- suppressed.")
            return False
        return True
    except Exception:
        return True


def auto_restart_eve(reason: str) -> bool:
    """Kill EVE.exe then relaunch it detached. Returns True if relaunch fired.

    RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical:
    'auto detect when it sticks and make sure auto update works as it keeps
     fucking crashing and causing agents to stall'.

    Steps:
    1. psutil.terminate() all eve.exe procs (graceful first)
    2. wait 2s, force-kill any survivors
    3. run Kill-Stuck-EVE.bat (cleans title-matched windows + orphan python)
    4. wait 1.5s
    5. Popen EVE.exe detached so watchdog schtask exits cleanly
    6. write cooldown stamp
    """
    if not _restart_cooldown_ok():
        print("[eve-crash-detector] auto-restart: cooldown active, skipping.")
        return False

    eve_exe = _eve_exe_path()
    print(f"[eve-crash-detector] auto-restart triggered: {reason}")
    print(f"[eve-crash-detector] EVE.exe path: {eve_exe}")

    # Step 1-2: terminate EVE procs
    procs = _eve_procs()
    for p in procs:
        try:
            p.terminate()
            print(f"  terminated PID {p.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if procs:
        psutil.wait_procs(procs, timeout=3)
    # Force-kill survivors
    still = _eve_procs()
    for p in still:
        try:
            p.kill()
            print(f"  force-killed PID {p.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Step 3: run Kill-Stuck-EVE.bat (cleans orphan python + titled windows)
    if KILL_BAT.exists():
        try:
            subprocess.run([str(KILL_BAT)], shell=False, timeout=20,
                           capture_output=True)
        except Exception:
            pass

    time.sleep(1.5)

    # Step 4: write cooldown stamp + history BEFORE launch so re-entrant schtask fires see it
    try:
        prev = {}
        if _RESTART_STATE.exists():
            try:
                prev = json.loads(_RESTART_STATE.read_text(encoding="utf-8"))
            except Exception:
                pass
        history = [t for t in prev.get("history", []) if (time.time() - t) < 3600]
        history.append(time.time())
        _RESTART_STATE.write_text(
            json.dumps({"ts": time.time(), "reason": reason, "history": history}),
            encoding="utf-8",
        )
    except Exception:
        pass

    # Step 5: relaunch
    if eve_exe is None:
        print("[eve-crash-detector] auto-restart: EVE.exe NOT FOUND — skipping relaunch.")
        _append_jsonl(CRASH_LOG, {"ts": _now_iso(), "event": "auto_restart_no_exe",
                                   "reason": reason})
        return False

    try:
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP so the watchdog schtask
        # can exit without killing the newly launched EVE window.
        DETACHED = 0x00000008
        NEW_GROUP = 0x00000200
        subprocess.Popen(
            [str(eve_exe)],
            creationflags=DETACHED | NEW_GROUP,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[eve-crash-detector] auto-restart: launched {eve_exe}")
        _append_jsonl(CRASH_LOG, {
            "ts": _now_iso(), "event": "auto_restart", "reason": reason,
            "exe": str(eve_exe),
        })
        return True
    except Exception as exc:
        print(f"[eve-crash-detector] auto-restart: launch FAILED: {exc}", file=sys.stderr)
        _append_jsonl(CRASH_LOG, {"ts": _now_iso(), "event": "auto_restart_failed",
                                   "reason": reason, "error": str(exc)})
        return False


def install_watchdog_schtask() -> int:
    """Install SinisterEVEWatchdog schtask: scan+auto-kill+auto-restart every 60s.

    RKOJ-ELENO :: 2026-05-25 :: operator 'auto detect when it sticks'.
    Idempotent: Delete+recreate so the XML always matches current python path.
    """
    python_exe = sys.executable
    this_script = Path(__file__).resolve()
    cmd = (f'"{python_exe}" "{this_script}" --scan --auto-kill --auto-restart')
    task_name = "SinisterEVEWatchdog"
    # Delete old if present (idempotent)
    subprocess.run(["schtasks", "/Delete", "/TN", task_name, "/F"],
                   capture_output=True)
    # Create: run every 1 minute indefinitely
    result = subprocess.run([
        "schtasks", "/Create",
        "/TN", task_name,
        "/TR", cmd,
        "/SC", "MINUTE", "/MO", "1",
        "/RL", "HIGHEST",
        "/F",
    ], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[eve-crash-detector] {task_name} schtask installed (every 1 min).")
        _append_jsonl(CRASH_LOG, {"ts": _now_iso(), "event": "watchdog_installed",
                                   "task": task_name})
        return 0
    else:
        print(f"[eve-crash-detector] schtask create FAILED: {result.stderr.strip()}", file=sys.stderr)
        return 5


def pre_compile_clear(dry_run: bool = False) -> int:
    """Always-kill EVE.exe before rebuild. Returns 0 cleared, 2 still alive."""
    procs = _eve_procs()
    if not procs:
        print("[eve-crash-detector] pre-compile: no EVE.exe running, clear to build.")
        return 0
    print(f"[eve-crash-detector] pre-compile: {len(procs)} EVE.exe alive -> killing")
    for p in procs:
        print(f"  PID {p.pid} (age {int(time.time() - p.create_time())}s)")
    if dry_run:
        print("[eve-crash-detector] --dry-run: would invoke Kill-Stuck-EVE.bat")
        return 0
    # Graceful first
    for p in procs:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    gone = psutil.wait_procs(procs, timeout=5)[1]
    if gone:
        run_kill_bat(reason="pre_compile_force", signals=[])
        time.sleep(1)
    still = _eve_procs()
    if still:
        print(f"[eve-crash-detector] pre-compile: STILL ALIVE after kill: {[p.pid for p in still]}", file=sys.stderr)
        _append_jsonl(CRASH_LOG, {"ts": _now_iso(), "event": "pre_compile_failed", "alive_pids": [p.pid for p in still]})
        return 2
    _append_jsonl(CRASH_LOG, {"ts": _now_iso(), "event": "pre_compile_cleared"})
    return 0


def cmd_status() -> int:
    print("=== EVE crash detector status ===")
    print(f"Kill bat:  {KILL_BAT} ({'OK' if KILL_BAT.exists() else 'MISSING'})")
    print(f"Log:       {CRASH_LOG}")
    procs = _eve_procs()
    print(f"\nCurrent EVE.exe processes ({len(procs)}):")
    for p in procs:
        try:
            print(f"  PID {p.pid}  age={int(time.time() - p.create_time())}s  status={p.status()}")
        except Exception:
            print(f"  PID {p.pid}  (info unavailable)")
    print("\nLast 5 detection events:")
    if not CRASH_LOG.exists():
        print("  (no log yet)")
    else:
        try:
            with CRASH_LOG.open("r", encoding="utf-8") as f:
                tail = f.readlines()[-5:]
            for line in tail:
                try:
                    row = json.loads(line)
                    print(f"  {row.get('ts','?')}  {row.get('event','?')}  rc={row.get('bat_rc','-')}")
                except Exception:
                    print(f"  {line.strip()[:180]}")
        except Exception as e:
            print(f"  (read failed: {e})")
    return 0


# ---------- CLI ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="EVE.exe crash / hang detector + auto-rescue")
    ap.add_argument("--scan", action="store_true", help="run detection; exit 1 if crash detected")
    ap.add_argument("--auto-kill", action="store_true", help="with --scan: run Kill-Stuck-EVE.bat on detection")
    ap.add_argument("--auto-restart", action="store_true",
                    help="with --scan --auto-kill: also relaunch EVE.exe after killing (cooldown 90s)")
    ap.add_argument("--pre-compile", action="store_true", help="kill any running EVE.exe before rebuild")
    ap.add_argument("--dry-run", action="store_true", help="with --pre-compile: don't actually kill")
    ap.add_argument("--status", action="store_true", help="print log tail + current EVE procs")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout (with --scan)")
    ap.add_argument("--install-watchdog", action="store_true",
                    help="install SinisterEVEWatchdog schtask (scan+kill+restart every 60s)")
    args = ap.parse_args()

    if args.install_watchdog:
        return install_watchdog_schtask()

    if args.status:
        return cmd_status()

    if args.pre_compile:
        return pre_compile_clear(dry_run=args.dry_run)

    if args.scan:
        crashed, signals = run_all_signals()
        triggered = [s["signal"] for s in signals if s.get("triggered")]
        if args.json:
            print(json.dumps({"crashed": crashed, "triggered": triggered, "signals": signals}, indent=2))
        else:
            print(f"[eve-crash-detector] scan: crashed={crashed} triggered={triggered}")
            for s in signals:
                if s.get("triggered"):
                    print(f"  -> {s['signal']}: {s.get('hits', s.get('error', ''))}")
        if crashed and args.auto_kill:
            if args.auto_restart:
                # auto_restart does kill + relaunch atomically
                auto_restart_eve(reason="scan_auto_restart")
            else:
                rc = run_kill_bat(reason="scan_auto_kill", signals=signals)
                print(f"[eve-crash-detector] Kill-Stuck-EVE.bat exit={rc}")
        elif crashed:
            _append_jsonl(CRASH_LOG, {"ts": _now_iso(), "event": "scan_detected",
                                       "signals": [s for s in signals if s.get("triggered")]})
        return 1 if crashed else 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
