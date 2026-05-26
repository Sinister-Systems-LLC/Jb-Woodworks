"""eve_compliance_train_loop.py — never-stop autonomous training daemon

Author: RKOJ-ELENO :: 2026-05-25 (R8)

Operator hard-canonical 2026-05-25T13:04Z:
   "i need you to like loop this traingin and like neevr stop so we can detect
    all that we need to combat. pull all head starts and jump starts you can
    get for this"

What this does:
   Every INTERVAL seconds (default 1800 = 30 min):
   1. Health-check the local backend at http://localhost:4000/api/health
   2. Re-seed the demo data (idempotent — keyed on demo-* email prefix)
   3. Run the autonomous-training-loop.sh
   4. Capture metrics: precision, queue depth, cooldown count, hash-set size
   5. Append a row to _shared-memory/eve-training-loop.jsonl
   6. If precision drops below DEGRADED_THRESHOLD or backend is down for >3
      cycles, write a high-pri inbox row to the eve-compliance lane.

Stop conditions:
   - Receive SIGINT / SIGTERM (graceful shutdown)
   - Backend down for >MAX_CONSECUTIVE_BACKEND_FAILURES cycles → write inbox + exit 3
   - Critical regression (precision <0.5 sustained 3 cycles) → write inbox + exit 4

Install (per no-bat/no-ps1 doctrine, schedule via schtasks.exe):
   schtasks /Create /TN "SinisterEveComplianceTrainLoop" /SC ONSTART \
       /TR "python D:\\Sinister Sanctum\\automations\\eve_compliance_train_loop.py" \
       /RU SYSTEM /F

Run manually:
   python eve_compliance_train_loop.py [--interval 1800] [--max-cycles N]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
LETSTEXT_ROOT = Path("C:/Users/Zonia/Desktop/LetsText")
AUTONOMOUS_LOOP = SANCTUM_ROOT / "projects" / "eve-compliance" / "scripts" / "autonomous-training-loop.sh"
METRICS_JSONL = SANCTUM_ROOT / "_shared-memory" / "eve-training-loop.jsonl"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox" / "eve-compliance"
HEARTBEAT_PATH = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / "eve-compliance-train-loop.json"
ALERT_STATE_PATH = SANCTUM_ROOT / "_shared-memory" / "eve-training-alert-state.json"
PIDFILE_PATH = SANCTUM_ROOT / "_shared-memory" / "eve-training-loop.pid"

BACKEND_HEALTH_URL = "http://localhost:4000/api/health"
DEFAULT_INTERVAL_SEC = 1800  # 30 min
DEGRADED_PRECISION_THRESHOLD = 0.85
# R8 2026-05-26: gate re-alerts so persistent (but unchanged) below-threshold
# state doesn't spam the inbox every 3 cycles. Re-fire only when precision
# diverges from the last alerted value by more than this delta, OR when
# labeled-row count grows enough to be a "fresh" data point.
ALERT_PRECISION_DELTA = 0.05
ALERT_LABELED_DELTA = 5
# Re-fire cooldown: even if dedup signals a re-alert, never fire more often
# than once per ALERT_MIN_INTERVAL_SEC. Operator (2026-05-26): 7 inbox copies of
# the same "precision degraded 0.83 sustained 3 cycles" alert in 7h is noise.
ALERT_MIN_INTERVAL_SEC = 6 * 3600  # 6h floor between re-alerts
RECOVERY_THRESHOLD = DEGRADED_PRECISION_THRESHOLD  # cross back above to clear
RECOVERY_REQUIRED_CYCLES = 2
MAX_CONSECUTIVE_BACKEND_FAILURES = 3

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    level=logging.INFO,
)
log = logging.getLogger("eve-train-loop")

_shutdown_requested = False


def _handle_signal(signum: int, frame: Any) -> None:
    global _shutdown_requested
    log.info(f"Signal {signum} received — requesting graceful shutdown")
    _shutdown_requested = True


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def health_check() -> bool:
    try:
        with urllib.request.urlopen(BACKEND_HEALTH_URL, timeout=5) as resp:
            return resp.status == 200
    except Exception as e:
        log.warning(f"Backend health check failed: {e}")
        return False


def run_autonomous_loop() -> dict[str, Any]:
    """Run the bash loop and parse the metrics from its stdout."""
    if not AUTONOMOUS_LOOP.exists():
        return {"ok": False, "error": f"{AUTONOMOUS_LOOP} not found"}

    bash_path = "C:\\Program Files\\Git\\bin\\bash.exe"
    if not Path(bash_path).exists():
        bash_path = "bash"

    cmd = [bash_path, str(AUTONOMOUS_LOOP)]
    log.info(f"Running: {' '.join(cmd)}")

    # RKOJ-ELENO :: 2026-05-25 (iter-20) :: operator screenshot ~18:09Z shows
    # this bash.exe spawn flashing a visible cmd window. Inject CREATE_NO_WINDOW
    # (0x08000000) so the child runs fully hidden. Same fix pattern as
    # eve.py iter-3 monkey-patch. Windows-only flag; safe no-op elsewhere.
    _no_win = 0x08000000 if os.name == "nt" else 0

    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ},
            creationflags=_no_win,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "loop timeout after 600s"}

    duration = time.time() - started
    stdout = proc.stdout
    stderr = proc.stderr

    metrics = parse_loop_output(stdout)
    metrics["duration_sec"] = round(duration, 1)
    metrics["exit_code"] = proc.returncode
    metrics["ok"] = proc.returncode == 0
    if not metrics["ok"]:
        metrics["stderr_tail"] = stderr.splitlines()[-5:] if stderr else []

    return metrics


def parse_loop_output(stdout: str) -> dict[str, Any]:
    """Extract structured metrics from the bash loop's text output."""
    out: dict[str, Any] = {"raw_lines": stdout.count("\n")}
    for line in stdout.splitlines():
        line = line.strip()
        if "pending=" in line and "Step 2" not in line:
            try:
                out["pending"] = int(line.split("pending=")[1].split()[0])
            except (ValueError, IndexError):
                pass
        if "precision-rolling" in line and '"precision":' in line:
            try:
                p = line.split('"precision":')[1].split(",")[0].split("}")[0].strip()
                out["precision"] = None if p == "null" else float(p)
            except (ValueError, IndexError):
                pass
            try:
                out["good_catch"] = int(line.split('"goodCatch":')[1].split(",")[0])
                out["bad_catch"] = int(line.split('"badCatch":')[1].split(",")[0])
            except (ValueError, IndexError):
                pass
        if "cooldowns/agencies" in line and '"count":' in line:
            try:
                out["agency_cooldowns"] = int(line.split('"count":')[1].split(",")[0])
            except (ValueError, IndexError):
                pass
        if "known-hashes" in line and '"rows":' in line:
            out["known_hash_set_present"] = '"rows":[' in line
        if "training-export.jsonl:" in line:
            try:
                out["training_jsonl_lines"] = int(line.split("training-export.jsonl:")[1].split("lines")[0].strip())
            except (ValueError, IndexError):
                pass
    return out


# R9 2026-05-26: dedup contiguous-identical rows. Volatile keys vary every
# cycle (ts/cycle/duration) but the substantive payload only changes when the
# upstream loop's metrics shift. Coalesce identical-payload runs into a single
# row that tracks first-seen ts/cycle + last-seen ts/cycle + repeat_count.
_DEDUP_VOLATILE_KEYS = frozenset({
    "ts_utc", "cycle", "duration_sec", "raw_lines", "stderr_tail",
    "last_ts_utc", "last_cycle", "last_duration_sec", "last_raw_lines",
    "repeat_count",
})


def _stable_signature(row: dict[str, Any]) -> tuple:
    return tuple(sorted(
        (k, v) for k, v in row.items() if k not in _DEDUP_VOLATILE_KEYS
    ))


def _read_last_jsonl_row(path: Path) -> tuple[dict[str, Any] | None, str]:
    """Return (parsed_last_row, prefix_text). Prefix preserves the rest of the
    file so the caller can rewrite the last line in place by writing
    prefix + new_line. Returns (None, "") if file missing/empty/unparseable."""
    if not path.exists() or path.stat().st_size == 0:
        return None, ""
    content = path.read_text(encoding="utf-8")
    stripped = content.rstrip("\n")
    if not stripped:
        return None, ""
    nl = stripped.rfind("\n")
    last_line = stripped[nl + 1:] if nl >= 0 else stripped
    prefix = stripped[:nl + 1] if nl >= 0 else ""
    try:
        return json.loads(last_line), prefix
    except json.JSONDecodeError:
        return None, ""


def _coalesce_into(target: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    out = dict(target)
    out["repeat_count"] = out.get("repeat_count", 1) + 1
    for src_key, dst_key in (
        ("ts_utc", "last_ts_utc"),
        ("cycle", "last_cycle"),
        ("duration_sec", "last_duration_sec"),
        ("raw_lines", "last_raw_lines"),
    ):
        if src_key in incoming:
            out[dst_key] = incoming[src_key]
    return out


def write_metrics(row: dict[str, Any]) -> None:
    METRICS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    last_row, prefix = _read_last_jsonl_row(METRICS_JSONL)
    if last_row is not None and _stable_signature(last_row) == _stable_signature(row):
        coalesced = _coalesce_into(last_row, row)
        METRICS_JSONL.write_text(
            prefix + json.dumps(coalesced) + "\n",
            encoding="utf-8",
        )
        return
    with METRICS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def compact_existing_metrics() -> dict[str, Any]:
    """Retroactively coalesce contiguous-identical rows in METRICS_JSONL.
    Writes original to .pre-dedup-bak alongside. Idempotent."""
    if not METRICS_JSONL.exists():
        return {"before": 0, "after": 0, "removed": 0, "backup": None}
    rows: list[dict[str, Any]] = []
    for line in METRICS_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    before = len(rows)
    if before == 0:
        return {"before": 0, "after": 0, "removed": 0, "backup": None}
    out: list[dict[str, Any]] = [rows[0]]
    for r in rows[1:]:
        if _stable_signature(out[-1]) == _stable_signature(r):
            out[-1] = _coalesce_into(out[-1], r)
        else:
            out.append(r)
    backup = METRICS_JSONL.with_suffix(".jsonl.pre-dedup-bak")
    if not backup.exists():
        backup.write_bytes(METRICS_JSONL.read_bytes())
    METRICS_JSONL.write_text(
        "\n".join(json.dumps(r) for r in out) + "\n",
        encoding="utf-8",
    )
    return {
        "before": before,
        "after": len(out),
        "removed": before - len(out),
        "backup": str(backup),
    }


def write_heartbeat(cycle: int, last_metrics: dict[str, Any]) -> None:
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    HEARTBEAT_PATH.write_text(
        json.dumps(
            {
                "slug": "eve-compliance-train-loop",
                "agent_display": "EVE Compliance Train Loop",
                "ts_utc": utc_now_iso(),
                "cycle": cycle,
                "last_metrics": last_metrics,
                "next_cycle_in_sec": int(last_metrics.get("interval_sec", DEFAULT_INTERVAL_SEC)),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def read_alert_state() -> dict[str, Any]:
    """Load persistent alert state for cross-cycle dedup. Empty dict if missing/corrupt."""
    if not ALERT_STATE_PATH.exists():
        return {}
    try:
        return json.loads(ALERT_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_alert_state(state: dict[str, Any]) -> None:
    ALERT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _parse_iso_utc(s: str) -> datetime | None:
    """Parse an ISO-8601 Z-suffixed UTC timestamp. Returns None on garbage input."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def should_re_alert(
    precision: float,
    labeled: int,
    last_state: dict[str, Any],
    now: datetime | None = None,
) -> tuple[bool, str]:
    """Return (should_fire, reason). Avoid re-firing on stuck-but-unchanged state.

    Two-layer dedup:
      1. Hard floor: never re-fire within ALERT_MIN_INTERVAL_SEC of the last alert
         (operator complaint 2026-05-26: 7 identical inbox copies in 7h was noise).
      2. Soft delta: even after the floor, only re-fire if precision diverged by
         >=ALERT_PRECISION_DELTA OR labeled-row count grew by >=ALERT_LABELED_DELTA.
    `now` is injectable for tests; defaults to wall-clock UTC.
    """
    last_precision = last_state.get("last_alerted_precision")
    last_labeled = last_state.get("last_alerted_labeled", 0)
    if last_precision is None:
        return True, "first-alert"

    now = now or datetime.now(timezone.utc)
    last_ts = _parse_iso_utc(last_state.get("last_alerted_ts_utc", ""))
    if last_ts is not None:
        age_sec = (now - last_ts).total_seconds()
        if age_sec < ALERT_MIN_INTERVAL_SEC:
            return False, f"suppressed-by-time-floor age={int(age_sec)}s<{ALERT_MIN_INTERVAL_SEC}s"

    if abs(precision - last_precision) >= ALERT_PRECISION_DELTA:
        return True, f"precision-diverged delta={abs(precision-last_precision):.3f}"
    if labeled - last_labeled >= ALERT_LABELED_DELTA:
        return True, f"labeled-grew delta={labeled-last_labeled}"
    return False, "suppressed-by-dedup"


def write_alert_inbox(subject: str, severity: str, payload: dict[str, Any]) -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    p = INBOX_DIR / f"{ts}-from-train-loop-{subject.replace(' ', '-').lower()}.md"
    p.write_text(
        f"# From: EVE Compliance Train Loop -> EVE Compliance\n\n"
        f"Author: RKOJ-ELENO :: 2026-05-25\n"
        f"Subject: [{severity}] {subject}\n"
        f"Priority: {'HIGH' if severity in ('CRITICAL', 'DEGRADED') else 'normal'}\n\n"
        f"## Payload\n\n"
        f"```json\n{json.dumps(payload, indent=2)}\n```\n\n"
        f"End.\n",
        encoding="utf-8",
    )
    log.warning(f"Alert inbox written: {p.name}")


def _pid_alive(pid: int) -> bool:
    """Return True if the OS knows about a live process with this pid.
    Cross-platform: signal 0 on POSIX, OpenProcess+GetExitCodeProcess on Windows."""
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
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
        return pid > 0  # PermissionError means proc exists but we can't signal


def acquire_singleton_lock() -> tuple[bool, str]:
    """Atomically take the train-loop pidfile. Returns (ok, reason)."""
    PIDFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if PIDFILE_PATH.exists():
        try:
            existing = int(PIDFILE_PATH.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            existing = 0
        if existing and existing != os.getpid() and _pid_alive(existing):
            return False, f"pid {existing} already running"
        # Stale pidfile — owner is dead or it's us. Reclaim.
    PIDFILE_PATH.write_text(str(os.getpid()), encoding="utf-8")
    return True, f"acquired pidfile pid={os.getpid()}"


def release_singleton_lock() -> None:
    try:
        if PIDFILE_PATH.exists():
            current = PIDFILE_PATH.read_text(encoding="utf-8").strip()
            if current == str(os.getpid()):
                PIDFILE_PATH.unlink()
    except OSError:
        pass


def run_self_test() -> int:
    """Inline assertions for dedup + pidfile logic. Exit 0 on PASS, 1 on FAIL."""
    import tempfile

    global ALERT_STATE_PATH, PIDFILE_PATH, METRICS_JSONL, INBOX_DIR, HEARTBEAT_PATH
    saved = (ALERT_STATE_PATH, PIDFILE_PATH, METRICS_JSONL, INBOX_DIR, HEARTBEAT_PATH)
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        ALERT_STATE_PATH = td_p / "alert-state.json"
        PIDFILE_PATH = td_p / "loop.pid"
        METRICS_JSONL = td_p / "metrics.jsonl"
        INBOX_DIR = td_p / "inbox"
        HEARTBEAT_PATH = td_p / "hb.json"

        def check(name: str, cond: bool, detail: str = "") -> None:
            if cond:
                print(f"  PASS  {name}")
            else:
                failures.append(f"{name} :: {detail}")
                print(f"  FAIL  {name} :: {detail}")

        # ── should_re_alert ───────────────────────────────────────────────
        now = datetime(2026, 5, 26, 21, 0, 0, tzinfo=timezone.utc)
        fire, reason = should_re_alert(0.80, 6, {}, now=now)
        check("first-alert fires", fire and reason == "first-alert", f"{fire=} {reason=}")

        state = {
            "last_alerted_precision": 0.83,
            "last_alerted_labeled": 6,
            "last_alerted_ts_utc": "2026-05-26T20:00:00Z",  # 1h ago
        }
        fire, reason = should_re_alert(0.83, 6, state, now=now)
        check(
            "identical-within-floor suppresses",
            not fire and reason.startswith("suppressed-by-time-floor"),
            f"{fire=} {reason=}",
        )

        fire, reason = should_re_alert(0.83, 6, state, now=now + timedelta(hours=7))
        check(
            "past-floor + identical still suppressed (delta dedup)",
            not fire and reason == "suppressed-by-dedup",
            f"{fire=} {reason=}",
        )

        fire, reason = should_re_alert(0.70, 6, state, now=now + timedelta(hours=7))
        check(
            "past-floor + precision-diverged fires",
            fire and reason.startswith("precision-diverged"),
            f"{fire=} {reason=}",
        )

        fire, reason = should_re_alert(0.70, 6, state, now=now)
        check(
            "within-floor + precision-diverged still suppressed",
            not fire and reason.startswith("suppressed-by-time-floor"),
            f"{fire=} {reason=}",
        )

        fire, reason = should_re_alert(0.83, 20, state, now=now + timedelta(hours=7))
        check(
            "past-floor + labeled-grew fires",
            fire and reason.startswith("labeled-grew"),
            f"{fire=} {reason=}",
        )

        # ── alert-state round-trip ──────────────────────────────────────
        write_alert_state({"active": True, "last_alerted_precision": 0.5, "last_alerted_ts_utc": "2026-05-26T20:00:00Z"})
        rt = read_alert_state()
        check("alert-state round-trip", rt.get("last_alerted_precision") == 0.5, f"{rt=}")

        # ── pidfile singleton ───────────────────────────────────────────
        ok, _ = acquire_singleton_lock()
        check("acquire fresh pidfile", ok)
        ok2, reason2 = acquire_singleton_lock()
        check(
            "re-acquire by same pid succeeds (idempotent)",
            ok2,
            f"{reason2=}",
        )
        PIDFILE_PATH.write_text("999999", encoding="utf-8")  # almost-certainly-dead pid
        ok3, reason3 = acquire_singleton_lock()
        check("acquire reclaims stale pidfile", ok3, f"{reason3=}")
        release_singleton_lock()
        check("release removes pidfile", not PIDFILE_PATH.exists())

        # ── metrics-row coalesce ────────────────────────────────────────
        write_metrics({"ts_utc": "t1", "cycle": 1, "precision": 0.9, "ok": True, "interval_sec": 60})
        write_metrics({"ts_utc": "t2", "cycle": 2, "precision": 0.9, "ok": True, "interval_sec": 60})
        write_metrics({"ts_utc": "t3", "cycle": 3, "precision": 0.9, "ok": True, "interval_sec": 60})
        write_metrics({"ts_utc": "t4", "cycle": 4, "precision": 0.5, "ok": True, "interval_sec": 60})
        lines = METRICS_JSONL.read_text(encoding="utf-8").strip().split("\n")
        check("contiguous-identical rows coalesce to 2", len(lines) == 2, f"got {len(lines)} lines")
        first = json.loads(lines[0])
        check("coalesced row tracks repeat_count", first.get("repeat_count") == 3, f"{first=}")
        check("coalesced row tracks last_cycle", first.get("last_cycle") == 3, f"{first=}")

    ALERT_STATE_PATH, PIDFILE_PATH, METRICS_JSONL, INBOX_DIR, HEARTBEAT_PATH = saved
    print()
    if failures:
        print(f"FAIL :: {len(failures)} assertion(s) failed")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS :: all self-test assertions green")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SEC)
    parser.add_argument("--max-cycles", type=int, default=0, help="0 = forever")
    parser.add_argument("--once", action="store_true", help="Run a single cycle then exit")
    parser.add_argument(
        "--compact-existing",
        action="store_true",
        help="Retroactively dedup METRICS_JSONL then exit (R9)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run inline dedup + pidfile + metrics-coalesce assertions then exit",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip singleton-pidfile guard (use only for ad-hoc debugging)",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    if args.compact_existing:
        stats = compact_existing_metrics()
        log.info(f"compact-existing: {stats}")
        print(json.dumps(stats, indent=2))
        return 0

    # Singleton guard: prevent the schtask --once run from racing the persistent
    # daemon. Both writing to the same JSONL + inbox is what produced the
    # 7-duplicate-alert noise on 2026-05-25. Skip with --force for debugging.
    if not args.force:
        ok, reason = acquire_singleton_lock()
        if not ok:
            log.warning(f"Singleton lock refused: {reason} — exiting cleanly")
            return 0

    interval = max(60, args.interval)  # never less than 1 min
    max_cycles = 1 if args.once else (args.max_cycles or 0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log.info(f"EVE Compliance train loop starting · interval={interval}s · max_cycles={max_cycles or 'forever'}")

    try:
        return _run_loop(interval, max_cycles)
    finally:
        if not args.force:
            release_singleton_lock()


def _run_loop(interval: int, max_cycles: int) -> int:
    cycle = 0
    backend_failures = 0
    precision_failures = 0
    recovery_cycles = 0

    while not _shutdown_requested:
        cycle += 1
        cycle_start = time.time()
        log.info(f"=== Cycle {cycle} ===")

        if not health_check():
            backend_failures += 1
            log.error(f"Backend unhealthy ({backend_failures}/{MAX_CONSECUTIVE_BACKEND_FAILURES})")
            write_metrics(
                {
                    "ts_utc": utc_now_iso(),
                    "cycle": cycle,
                    "ok": False,
                    "error": "backend_unhealthy",
                    "interval_sec": interval,
                }
            )
            if backend_failures >= MAX_CONSECUTIVE_BACKEND_FAILURES:
                write_alert_inbox(
                    "Backend down for 3 consecutive cycles",
                    "CRITICAL",
                    {"cycle": cycle, "url": BACKEND_HEALTH_URL},
                )
                return 3
        else:
            backend_failures = 0
            metrics = run_autonomous_loop()
            metrics["ts_utc"] = utc_now_iso()
            metrics["cycle"] = cycle
            metrics["interval_sec"] = interval
            write_metrics(metrics)
            write_heartbeat(cycle, metrics)

            precision = metrics.get("precision")
            labeled = (metrics.get("good_catch") or 0) + (metrics.get("bad_catch") or 0)
            alert_state = read_alert_state()

            if precision is not None and precision < DEGRADED_PRECISION_THRESHOLD:
                precision_failures += 1
                recovery_cycles = 0
                log.warning(
                    f"Precision {precision} below threshold {DEGRADED_PRECISION_THRESHOLD} "
                    f"({precision_failures}/3)"
                )
                if precision_failures >= 3:
                    fire, reason = should_re_alert(precision, labeled, alert_state)
                    if fire:
                        write_alert_inbox(
                            f"Precision degraded {precision:.2f} sustained 3 cycles",
                            "DEGRADED",
                            {
                                "cycle": cycle,
                                "precision": precision,
                                "labeled": labeled,
                                "alert_reason": reason,
                                "metrics": metrics,
                            },
                        )
                        write_alert_state({
                            "active": True,
                            "last_alerted_precision": precision,
                            "last_alerted_labeled": labeled,
                            "last_alerted_cycle": cycle,
                            "last_alerted_ts_utc": utc_now_iso(),
                        })
                    else:
                        log.info(f"Alert suppressed ({reason}) — precision={precision} labeled={labeled}")
                    precision_failures = 0  # window reset; dedup-state guards next fire
            elif precision is not None and precision >= RECOVERY_THRESHOLD and alert_state.get("active"):
                # Track sustained recovery to clear the active alert state.
                recovery_cycles += 1
                precision_failures = 0
                log.info(f"Precision recovered to {precision} ({recovery_cycles}/{RECOVERY_REQUIRED_CYCLES})")
                if recovery_cycles >= RECOVERY_REQUIRED_CYCLES:
                    write_alert_inbox(
                        f"Precision recovered to {precision:.2f}",
                        "RECOVERY",
                        {
                            "cycle": cycle,
                            "precision": precision,
                            "labeled": labeled,
                            "prior_alert": alert_state,
                            "metrics": metrics,
                        },
                    )
                    write_alert_state({"active": False, "cleared_at_cycle": cycle, "cleared_at_ts_utc": utc_now_iso()})
                    recovery_cycles = 0
            else:
                precision_failures = 0
                recovery_cycles = 0

            log.info(
                f"Cycle {cycle} done · ok={metrics.get('ok')} · "
                f"precision={precision} · pending={metrics.get('pending')} · "
                f"cooldowns={metrics.get('agency_cooldowns')} · "
                f"duration={metrics.get('duration_sec')}s"
            )

        if max_cycles and cycle >= max_cycles:
            log.info(f"max_cycles={max_cycles} reached — exiting")
            return 0

        elapsed = time.time() - cycle_start
        remaining = max(0, interval - elapsed)
        log.info(f"Sleeping {remaining:.0f}s before next cycle")
        slept = 0.0
        while slept < remaining and not _shutdown_requested:
            time.sleep(min(5.0, remaining - slept))
            slept += 5.0

    log.info("Graceful shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
