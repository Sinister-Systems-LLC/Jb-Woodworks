"""eve_gpu_trainer_watchdog.py - watchdog companion for eve_gpu_trainer.py

Author: RKOJ-ELENO :: 2026-05-27

Mirrors the R10 train-loop dedup-hardening pattern (singleton pidfile + 6h
alert re-fire floor) shipped in automations/eve_compliance_train_loop.py.

Polls the GPU trainer pidfile + heartbeat. If trainer is dead OR heartbeat
is stale, drops an inbox row + auto-restarts via `python eve_gpu_trainer.py
start`. If three consecutive restart attempts fail to revive the trainer,
escalates to OPERATOR-ACTION-QUEUE.md instead of looping forever.

CLI:
   python automations/eve_gpu_trainer_watchdog.py            # daemon (60s poll)
   python automations/eve_gpu_trainer_watchdog.py --once     # single poll, exit
   python automations/eve_gpu_trainer_watchdog.py --self-test
   python automations/eve_gpu_trainer_watchdog.py --status   # print state JSON

Design notes:
   - SINGLETON pidfile at _shared-memory/eve-gpu-trainer-watchdog.pid (same
     pattern as R10 train-loop). Prevents two watchdogs racing each other.
   - STALE THRESHOLD: 5 min (heartbeat older than this -> trainer is hung).
   - RESTART COOLDOWN: 60s minimum between restart attempts to avoid
     thrashing if torch is broken / venv missing / etc.
   - ESCALATION FLOOR: 6h between OPERATOR-ACTION-QUEUE entries for the
     same failure class (matches R10 alert re-fire floor).
   - STATE FILE: _shared-memory/eve-gpu-trainer-watchdog-state.json tracks
     consecutive_failures, last_restart_ts, last_escalation_ts.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
SHARED_MEM = SANCTUM_ROOT / "_shared-memory"
INBOX_DIR = SHARED_MEM / "inbox" / "eve-compliance"
OPERATOR_QUEUE = SHARED_MEM / "OPERATOR-ACTION-QUEUE.md"

# Trainer-owned paths (read-only from our perspective).
TRAINER_PIDFILE = SHARED_MEM / "eve-gpu-trainer.pid"
TRAINER_HEARTBEAT = SHARED_MEM / "heartbeats" / "eve-gpu-trainer.json"
TRAINER_SCRIPT = SANCTUM_ROOT / "automations" / "eve_gpu_trainer.py"

# Watchdog-owned paths.
WATCHDOG_PIDFILE = SHARED_MEM / "eve-gpu-trainer-watchdog.pid"
WATCHDOG_STATE = SHARED_MEM / "eve-gpu-trainer-watchdog-state.json"
WATCHDOG_HEARTBEAT = SHARED_MEM / "heartbeats" / "eve-gpu-trainer-watchdog.json"

POLL_INTERVAL_SEC = 60
STALE_HEARTBEAT_SEC = 5 * 60
RESTART_COOLDOWN_SEC = 60
MAX_CONSECUTIVE_FAILURES = 3
ESCALATION_FLOOR_SEC = 6 * 3600


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


# -- pid-alive helper (copied verbatim from R10 train-loop / R12 trainer) --

def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not h:
                return False
            try:
                exit_code = ctypes.c_ulong()
                ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(exit_code))
                return bool(ok) and exit_code.value == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(h)
        except (OSError, AttributeError):
            return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return pid > 0


# -- watchdog singleton --

def acquire_watchdog_lock() -> tuple[bool, str]:
    WATCHDOG_PIDFILE.parent.mkdir(parents=True, exist_ok=True)
    if WATCHDOG_PIDFILE.exists():
        try:
            existing = int(WATCHDOG_PIDFILE.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing = 0
        if existing and existing != os.getpid() and _pid_alive(existing):
            return False, f"watchdog pid {existing} already running"
    WATCHDOG_PIDFILE.write_text(str(os.getpid()), encoding="utf-8")
    return True, f"acquired pid={os.getpid()}"


def release_watchdog_lock() -> None:
    try:
        if WATCHDOG_PIDFILE.exists():
            current = WATCHDOG_PIDFILE.read_text(encoding="utf-8").strip()
            if current == str(os.getpid()):
                WATCHDOG_PIDFILE.unlink()
    except OSError:
        pass


# -- trainer state inspection (read-only) --

def read_trainer_pid() -> int:
    if not TRAINER_PIDFILE.exists():
        return 0
    try:
        return int(TRAINER_PIDFILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


def read_trainer_heartbeat() -> dict[str, Any]:
    if not TRAINER_HEARTBEAT.exists():
        return {}
    try:
        return json.loads(TRAINER_HEARTBEAT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def heartbeat_age_seconds(hb: dict[str, Any], now: datetime | None = None) -> float | None:
    ts_str = hb.get("ts_utc") if hb else None
    if not ts_str:
        return None
    ts = parse_iso(ts_str)
    if ts is None:
        return None
    now = now or datetime.now(timezone.utc)
    return (now - ts).total_seconds()


# -- watchdog state file --

def read_state() -> dict[str, Any]:
    if not WATCHDOG_STATE.exists():
        return {
            "consecutive_failures": 0,
            "last_restart_ts_utc": "",
            "last_escalation_ts_utc": "",
            "restart_count_total": 0,
        }
    try:
        return json.loads(WATCHDOG_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "consecutive_failures": 0,
            "last_restart_ts_utc": "",
            "last_escalation_ts_utc": "",
            "restart_count_total": 0,
        }


def write_state(state: dict[str, Any]) -> None:
    WATCHDOG_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = WATCHDOG_STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp, WATCHDOG_STATE)


# -- watchdog heartbeat (we report aliveness too) --

def write_watchdog_heartbeat(state: dict[str, Any], trainer_state: str) -> None:
    WATCHDOG_HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": "eve-gpu-trainer-watchdog",
        "agent_display": "EVE GPU Trainer Watchdog",
        "ts_utc": utc_now_iso(),
        "pid": os.getpid(),
        "trainer_state": trainer_state,
        "consecutive_failures": state.get("consecutive_failures", 0),
        "last_restart_ts_utc": state.get("last_restart_ts_utc", ""),
        "restart_count_total": state.get("restart_count_total", 0),
    }
    tmp = WATCHDOG_HEARTBEAT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, WATCHDOG_HEARTBEAT)


# -- actions: restart + inbox + escalation --

def restart_trainer() -> tuple[bool, str]:
    """Spawn `python eve_gpu_trainer.py start` and return (ok, stdout/err)."""
    if not TRAINER_SCRIPT.exists():
        return False, f"trainer script missing: {TRAINER_SCRIPT}"
    try:
        proc = subprocess.run(
            [sys.executable, str(TRAINER_SCRIPT), "start"],
            capture_output=True, text=True, timeout=30,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()
    except subprocess.TimeoutExpired:
        return False, "restart subprocess timed out after 30s"
    except OSError as e:
        return False, f"restart subprocess OSError: {e}"


def write_inbox_restart_note(reason: str, restart_output: str, attempt: int) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{utc_now_compact()}-train-loop-watchdog-restart.md"
    path = INBOX_DIR / fname
    body = (
        f"# Train-loop watchdog restart\n\n"
        f"- ts_utc: {utc_now_iso()}\n"
        f"- attempt: {attempt}/{MAX_CONSECUTIVE_FAILURES}\n"
        f"- reason: {reason}\n"
        f"- action: ran `python eve_gpu_trainer.py start`\n\n"
        f"## Restart output\n\n```\n{restart_output or '(no output)'}\n```\n\n"
        f"Author: RKOJ-ELENO :: 2026-05-27\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def escalate_to_operator_queue(reason: str, state: dict[str, Any]) -> None:
    OPERATOR_QUEUE.parent.mkdir(parents=True, exist_ok=True)
    row = (
        f"\n## CRITICAL {utc_now_iso()} :: eve-gpu-trainer-watchdog\n\n"
        f"GPU trainer dead and watchdog failed to revive after "
        f"{state.get('consecutive_failures', 0)} consecutive restart attempts.\n\n"
        f"- reason: {reason}\n"
        f"- pidfile: `{TRAINER_PIDFILE}`\n"
        f"- heartbeat: `{TRAINER_HEARTBEAT}`\n"
        f"- trainer-script: `{TRAINER_SCRIPT}`\n"
        f"- watchdog-state: `{WATCHDOG_STATE}`\n"
        f"- restart-count-total: {state.get('restart_count_total', 0)}\n\n"
        f"**Suggested triage:** run `python {TRAINER_SCRIPT} status` and inspect "
        f"the most recent log in `projects/eve-compliance/training/logs/`. "
        f"Most likely causes: torch missing in the lane venv, GPU OOM at "
        f"resident-game load, or control.json malformed.\n\n"
        f"Author: RKOJ-ELENO :: 2026-05-27\n"
    )
    with open(OPERATOR_QUEUE, "a", encoding="utf-8") as f:
        f.write(row)


def should_escalate(state: dict[str, Any], now: datetime | None = None) -> bool:
    if state.get("consecutive_failures", 0) < MAX_CONSECUTIVE_FAILURES:
        return False
    last = parse_iso(state.get("last_escalation_ts_utc", ""))
    if last is None:
        return True
    now = now or datetime.now(timezone.utc)
    return (now - last).total_seconds() >= ESCALATION_FLOOR_SEC


def restart_cooldown_active(state: dict[str, Any], now: datetime | None = None) -> bool:
    last = parse_iso(state.get("last_restart_ts_utc", ""))
    if last is None:
        return False
    now = now or datetime.now(timezone.utc)
    return (now - last).total_seconds() < RESTART_COOLDOWN_SEC


# -- the core poll-and-act cycle --

def evaluate_trainer() -> tuple[str, str]:
    """Returns (status, reason) where status in HEALTHY|DEAD|STALE|UNKNOWN."""
    pid = read_trainer_pid()
    hb = read_trainer_heartbeat()
    if pid <= 0:
        return "DEAD", "no pidfile"
    if not _pid_alive(pid):
        return "DEAD", f"pid {pid} not alive"
    age = heartbeat_age_seconds(hb)
    if age is None:
        return "STALE", "heartbeat missing or unparseable"
    if age > STALE_HEARTBEAT_SEC:
        return "STALE", f"heartbeat {int(age)}s old (threshold {STALE_HEARTBEAT_SEC}s)"
    # Also treat trainer-reported ERROR state as dead — the run loop sets
    # state=ERROR when torch import fails, then exits. The process can be
    # gone even if the heartbeat ts is fresh (race window).
    if hb.get("state") == "ERROR":
        return "DEAD", f"trainer reported state=ERROR: {hb.get('error', '?')}"
    return "HEALTHY", f"pid {pid} alive, heartbeat {int(age or 0)}s old"


def poll_and_act(restart_fn: Callable[[], tuple[bool, str]] | None = None,
                 now: datetime | None = None) -> dict[str, Any]:
    """Single poll cycle. Returns a structured report."""
    restart_fn = restart_fn or restart_trainer
    now = now or datetime.now(timezone.utc)
    state = read_state()
    status, reason = evaluate_trainer()

    report: dict[str, Any] = {
        "ts_utc": utc_now_iso(),
        "trainer_status": status,
        "reason": reason,
        "action": "none",
        "consecutive_failures": state.get("consecutive_failures", 0),
    }

    if status == "HEALTHY":
        if state.get("consecutive_failures", 0) > 0:
            state["consecutive_failures"] = 0
            write_state(state)
        write_watchdog_heartbeat(state, status)
        return report

    # DEAD or STALE: attempt a restart unless we're in cooldown or have
    # already exhausted the failure budget (in which case we escalate).
    if should_escalate(state, now=now):
        escalate_to_operator_queue(reason, state)
        state["last_escalation_ts_utc"] = utc_now_iso()
        write_state(state)
        report["action"] = "escalated"
        write_watchdog_heartbeat(state, status)
        return report

    if restart_cooldown_active(state, now=now):
        report["action"] = "cooldown"
        write_watchdog_heartbeat(state, status)
        return report

    attempt = state.get("consecutive_failures", 0) + 1
    ok, output = restart_fn()
    note_path = write_inbox_restart_note(reason, output, attempt)
    state["last_restart_ts_utc"] = utc_now_iso()
    state["restart_count_total"] = state.get("restart_count_total", 0) + 1
    if ok:
        # Verify by re-polling once after a short settle window.
        time.sleep(2)
        post_status, post_reason = evaluate_trainer()
        if post_status == "HEALTHY":
            state["consecutive_failures"] = 0
            report["action"] = "restarted_ok"
        else:
            state["consecutive_failures"] = attempt
            report["action"] = f"restart_spawned_but_unhealthy ({post_status})"
            report["reason"] = post_reason
    else:
        state["consecutive_failures"] = attempt
        report["action"] = "restart_subprocess_failed"
        report["reason"] = output

    write_state(state)
    write_watchdog_heartbeat(state, status)
    report["consecutive_failures"] = state["consecutive_failures"]
    report["inbox_note"] = str(note_path)
    return report


# -- daemon loop --

def run_daemon() -> int:
    ok, msg = acquire_watchdog_lock()
    if not ok:
        print(f"watchdog singleton refused: {msg}")
        return 0
    try:
        print(f"[watchdog] started pid={os.getpid()} poll={POLL_INTERVAL_SEC}s")
        while True:
            try:
                report = poll_and_act()
                print(f"[watchdog] {report['ts_utc']} status={report['trainer_status']} "
                      f"action={report['action']} fail_streak={report['consecutive_failures']} "
                      f"reason={report['reason']}")
            except (OSError, RuntimeError) as e:
                print(f"[watchdog] poll error: {e}")
            time.sleep(POLL_INTERVAL_SEC)
    finally:
        release_watchdog_lock()


# -- self-test --

def cmd_self_test() -> int:
    """Inline assertions covering pidfile-check + stale-heartbeat detection +
    restart-trigger logic. No real trainer process is spawned."""
    import tempfile
    global TRAINER_PIDFILE, TRAINER_HEARTBEAT, WATCHDOG_PIDFILE
    global WATCHDOG_STATE, WATCHDOG_HEARTBEAT, INBOX_DIR, OPERATOR_QUEUE
    saved = (TRAINER_PIDFILE, TRAINER_HEARTBEAT, WATCHDOG_PIDFILE,
             WATCHDOG_STATE, WATCHDOG_HEARTBEAT, INBOX_DIR, OPERATOR_QUEUE)
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        TRAINER_PIDFILE = td_p / "trainer.pid"
        TRAINER_HEARTBEAT = td_p / "trainer-hb.json"
        WATCHDOG_PIDFILE = td_p / "watchdog.pid"
        WATCHDOG_STATE = td_p / "watchdog-state.json"
        WATCHDOG_HEARTBEAT = td_p / "watchdog-hb.json"
        INBOX_DIR = td_p / "inbox"
        OPERATOR_QUEUE = td_p / "OPERATOR-ACTION-QUEUE.md"

        def check(name: str, cond: bool, detail: str = "") -> None:
            tag = "PASS" if cond else "FAIL"
            print(f"  {tag}  {name}" + (f" :: {detail}" if detail and not cond else ""))
            if not cond:
                failures.append(name)

        # 1. evaluate_trainer with no pidfile -> DEAD
        status, reason = evaluate_trainer()
        check("no pidfile -> DEAD", status == "DEAD", reason)

        # 2. dead pid in pidfile -> DEAD
        TRAINER_PIDFILE.write_text("999999", encoding="utf-8")
        status, reason = evaluate_trainer()
        check("dead pid -> DEAD", status == "DEAD", reason)

        # 3. live pid but no heartbeat -> STALE
        TRAINER_PIDFILE.write_text(str(os.getpid()), encoding="utf-8")
        status, reason = evaluate_trainer()
        check("live pid + no heartbeat -> STALE", status == "STALE", reason)

        # 4. live pid + fresh heartbeat -> HEALTHY
        TRAINER_HEARTBEAT.write_text(json.dumps({
            "ts_utc": utc_now_iso(),
            "state": "TRAINING",
        }), encoding="utf-8")
        status, reason = evaluate_trainer()
        check("live pid + fresh hb -> HEALTHY", status == "HEALTHY", reason)

        # 5. live pid + stale heartbeat -> STALE
        old_ts = datetime.now(timezone.utc).replace(year=2020).strftime("%Y-%m-%dT%H:%M:%SZ")
        TRAINER_HEARTBEAT.write_text(json.dumps({"ts_utc": old_ts, "state": "TRAINING"}), encoding="utf-8")
        status, reason = evaluate_trainer()
        check("live pid + stale hb -> STALE", status == "STALE", reason)

        # 6. trainer-reported ERROR -> DEAD (even with fresh ts)
        TRAINER_HEARTBEAT.write_text(json.dumps({
            "ts_utc": utc_now_iso(),
            "state": "ERROR",
            "error": "torch ImportError",
        }), encoding="utf-8")
        status, reason = evaluate_trainer()
        check("ERROR state -> DEAD", status == "DEAD", reason)

        # 7. poll_and_act with mock restart_fn that succeeds -> healthy after
        restart_calls = {"n": 0}
        def mock_restart_ok() -> tuple[bool, str]:
            restart_calls["n"] += 1
            # Make trainer "healthy" on next eval.
            TRAINER_HEARTBEAT.write_text(json.dumps({
                "ts_utc": utc_now_iso(), "state": "TRAINING",
            }), encoding="utf-8")
            return True, "spawned pid 12345"
        write_state({"consecutive_failures": 0, "last_restart_ts_utc": "",
                     "last_escalation_ts_utc": "", "restart_count_total": 0})
        # Reset trainer to dead state.
        TRAINER_HEARTBEAT.write_text(json.dumps({
            "ts_utc": utc_now_iso(), "state": "ERROR", "error": "x",
        }), encoding="utf-8")
        report = poll_and_act(restart_fn=mock_restart_ok)
        check("restart succeeds -> action=restarted_ok",
              report["action"] == "restarted_ok", report.get("action", "?"))
        check("restart called exactly once", restart_calls["n"] == 1,
              f"called {restart_calls['n']}")
        check("inbox note written",
              report.get("inbox_note") is not None and Path(report["inbox_note"]).exists())

        # 8. poll_and_act with mock restart_fn that fails -> failure increments
        write_state({"consecutive_failures": 0, "last_restart_ts_utc": "",
                     "last_escalation_ts_utc": "", "restart_count_total": 0})
        TRAINER_HEARTBEAT.write_text(json.dumps({
            "ts_utc": utc_now_iso(), "state": "ERROR", "error": "x",
        }), encoding="utf-8")
        def mock_restart_fail() -> tuple[bool, str]:
            return False, "torch import failed"
        report = poll_and_act(restart_fn=mock_restart_fail)
        check("restart failure -> action=restart_subprocess_failed",
              report["action"] == "restart_subprocess_failed", report.get("action", "?"))
        check("failure streak -> 1", read_state().get("consecutive_failures") == 1)

        # 9. cooldown active suppresses restart on next call
        report2 = poll_and_act(restart_fn=mock_restart_fail)
        check("immediate re-poll -> cooldown",
              report2["action"] == "cooldown", report2.get("action", "?"))

        # 10. after MAX_CONSECUTIVE_FAILURES, escalation fires + state captured
        st = read_state()
        st["consecutive_failures"] = MAX_CONSECUTIVE_FAILURES
        st["last_restart_ts_utc"] = "2020-01-01T00:00:00Z"  # past cooldown
        st["last_escalation_ts_utc"] = ""
        write_state(st)
        report3 = poll_and_act(restart_fn=mock_restart_fail)
        check("max failures + no prior escalation -> escalated",
              report3["action"] == "escalated", report3.get("action", "?"))
        check("OPERATOR-ACTION-QUEUE row appended",
              OPERATOR_QUEUE.exists() and "eve-gpu-trainer-watchdog" in OPERATOR_QUEUE.read_text(encoding="utf-8"))

        # 11. escalation floor: second escalation within 6h suppressed
        report4 = poll_and_act(restart_fn=mock_restart_fail)
        check("repeat escalation within floor -> NOT escalated again",
              report4["action"] != "escalated", report4.get("action", "?"))

        # 12. watchdog singleton: fresh acquire then idempotent re-acquire
        ok, _ = acquire_watchdog_lock()
        check("watchdog singleton fresh acquire", ok)
        ok2, _ = acquire_watchdog_lock()
        check("watchdog singleton idempotent re-acquire", ok2)
        # Reclaim stale
        WATCHDOG_PIDFILE.write_text("999999", encoding="utf-8")
        ok3, _ = acquire_watchdog_lock()
        check("watchdog singleton reclaims stale", ok3)
        release_watchdog_lock()
        check("watchdog singleton release removes file", not WATCHDOG_PIDFILE.exists())

        # 13. should_escalate honors floor
        recent = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        check("should_escalate=False when floor active",
              not should_escalate({"consecutive_failures": 5, "last_escalation_ts_utc": recent}))
        check("should_escalate=True when no prior",
              should_escalate({"consecutive_failures": MAX_CONSECUTIVE_FAILURES,
                               "last_escalation_ts_utc": ""}))
        check("should_escalate=False below threshold",
              not should_escalate({"consecutive_failures": 1, "last_escalation_ts_utc": ""}))

    (TRAINER_PIDFILE, TRAINER_HEARTBEAT, WATCHDOG_PIDFILE,
     WATCHDOG_STATE, WATCHDOG_HEARTBEAT, INBOX_DIR, OPERATOR_QUEUE) = saved

    print()
    if failures:
        print(f"FAIL :: {len(failures)} failed")
        return 1
    print("PASS :: all watchdog self-test assertions green")
    return 0


def cmd_status() -> int:
    state = read_state()
    status, reason = evaluate_trainer()
    pid = read_trainer_pid()
    hb = read_trainer_heartbeat()
    payload = {
        "watchdog_pid": os.getpid(),
        "trainer_status": status,
        "trainer_reason": reason,
        "trainer_pid": pid,
        "trainer_state": hb.get("state", "?"),
        "trainer_step": hb.get("step", "-"),
        "trainer_epoch": hb.get("epoch", "-"),
        "trainer_loss": hb.get("loss", "-"),
        "trainer_last_hb": hb.get("ts_utc", "-"),
        "watchdog_state": state,
    }
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="eve_gpu_trainer_watchdog")
    parser.add_argument("--self-test", action="store_true",
                        help="Run inline assertions (no real trainer touched)")
    parser.add_argument("--once", action="store_true",
                        help="Single poll-and-act cycle, then exit (cron mode)")
    parser.add_argument("--status", action="store_true",
                        help="Print current trainer + watchdog state JSON")
    args = parser.parse_args(argv)

    if args.self_test:
        return cmd_self_test()
    if args.status:
        return cmd_status()
    if args.once:
        report = poll_and_act()
        print(json.dumps(report, indent=2))
        return 0 if report["trainer_status"] == "HEALTHY" else 1

    return run_daemon()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
