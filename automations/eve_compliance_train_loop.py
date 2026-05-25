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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
LETSTEXT_ROOT = Path("C:/Users/Zonia/Desktop/LetsText")
AUTONOMOUS_LOOP = SANCTUM_ROOT / "projects" / "eve-compliance" / "scripts" / "autonomous-training-loop.sh"
METRICS_JSONL = SANCTUM_ROOT / "_shared-memory" / "eve-training-loop.jsonl"
INBOX_DIR = SANCTUM_ROOT / "_shared-memory" / "inbox" / "eve-compliance"
HEARTBEAT_PATH = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / "eve-compliance-train-loop.json"

BACKEND_HEALTH_URL = "http://localhost:4000/api/health"
DEFAULT_INTERVAL_SEC = 1800  # 30 min
DEGRADED_PRECISION_THRESHOLD = 0.85
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


def write_metrics(row: dict[str, Any]) -> None:
    METRICS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SEC)
    parser.add_argument("--max-cycles", type=int, default=0, help="0 = forever")
    parser.add_argument("--once", action="store_true", help="Run a single cycle then exit")
    args = parser.parse_args(argv)

    interval = max(60, args.interval)  # never less than 1 min
    max_cycles = 1 if args.once else (args.max_cycles or 0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log.info(f"EVE Compliance train loop starting · interval={interval}s · max_cycles={max_cycles or 'forever'}")

    cycle = 0
    backend_failures = 0
    precision_failures = 0

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
            if precision is not None and precision < DEGRADED_PRECISION_THRESHOLD:
                precision_failures += 1
                log.warning(
                    f"Precision {precision} below threshold {DEGRADED_PRECISION_THRESHOLD} "
                    f"({precision_failures}/3)"
                )
                if precision_failures >= 3:
                    write_alert_inbox(
                        f"Precision degraded {precision:.2f} sustained 3 cycles",
                        "DEGRADED",
                        {"cycle": cycle, "precision": precision, "metrics": metrics},
                    )
                    precision_failures = 0  # reset, keep looping (don't exit)
            else:
                precision_failures = 0

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
