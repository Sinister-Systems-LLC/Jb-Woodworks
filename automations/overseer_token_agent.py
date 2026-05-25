#!/usr/bin/env python3
"""overseer_token_agent.py -- Overseer sub-agent #2: token monitor + waste-free utilization.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (verbatim):
    "tie the over screen rate limit watcher into the same thing for token
     watcher. so the overseer project will have two sub agents. one for token
     monitor and incrasing of system also features where we can like make
     sure all tokeenbs are used and nothing is wasterd. like it can have
     background tasks that are noit as important or just chilling and lets
     say we have 10 percent left on a plan and 20 minutes left. the agent
     will make sure to use all tokens to have all power and control that we
     need in areas like this same for rate limiting monitor do all this now."

THE TWO OVERSEER SUB-AGENTS:
    1. automations/overseer_rate_limit_agent.py   -- detect+fix rate limits (20s SLA)
    2. automations/overseer_token_agent.py        -- THIS FILE -- max token use, no waste

DECISION RULES (every 60s pass):
    - if remaining_min < 25 AND available_pct > 8:
        SPARE-CAPACITY-WINDOW -> fire 2 background tasks (use it or lose it)
    - if available_pct > 50 AND live_agents == 0:
        IDLE-FILL -> fire 1 chill task (no waste)
    - else: NORMAL -> no fire

Background tasks pulled from _shared-memory/background-tasks.jsonl FIFO
(priority-sorted). Defaults seeded if queue empty: sanctum_custodian audit /
overseer_rate_limit_agent --once / prompt_profiler --scan / project_manager
categorize. Add custom via --queue-add.

DOCTRINE: _shared-memory/knowledge/overseer-monitors-doctrine-2026-05-25.md
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
USAGE_CACHE = SANCTUM_ROOT / "_shared-memory" / "anthropic-usage-cache.default.json"
QUEUE = SANCTUM_ROOT / "_shared-memory" / "background-tasks.jsonl"
FIRED_LOG = SANCTUM_ROOT / "_shared-memory" / "token-agent-fired.jsonl"
HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"

SCHTASK_NAME = "SinisterOverseerTokenAgent"

END_OF_WINDOW_MIN = 25
END_OF_WINDOW_AVAIL = 8
IDLE_AVAIL_PCT = 50
SPARE_FIRE_PER_PASS = 2
IDLE_FIRE_PER_PASS = 1


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_fired(event: dict) -> None:
    try:
        FIRED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with FIRED_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": utc_iso(), **event}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_usage() -> dict | None:
    if not USAGE_CACHE.exists():
        return None
    try:
        return json.loads(USAGE_CACHE.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return None


def remaining_minutes(reset_utc_str: str) -> float:
    try:
        dt = datetime.fromisoformat(reset_utc_str.replace("Z", "+00:00"))
        return max(0, (dt - utc_now()).total_seconds() / 60)
    except Exception:
        return 0


def live_agent_count(window_s: int = 300) -> int:
    if not HEARTBEAT_DIR.exists():
        return 0
    n = 0
    now = time.time()
    try:
        for p in HEARTBEAT_DIR.iterdir():
            if p.suffix.lower() not in (".json", ".beat"):
                continue
            try:
                if (now - p.stat().st_mtime) < window_s:
                    n += 1
            except OSError:
                continue
    except OSError:
        return 0
    return n


def seed_defaults() -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    if QUEUE.exists() and QUEUE.stat().st_size > 0:
        return
    defaults = [
        {"kind": "chill", "priority": 5, "description": "brain consolidation audit",
         "project": "sanctum",
         "cmd": ["python", str(SANCTUM_ROOT / "automations" / "sanctum_custodian.py"), "audit", "--quiet"]},
        {"kind": "chill", "priority": 4, "description": "active rate-limit probe",
         "project": "sanctum",
         "cmd": ["python", str(SANCTUM_ROOT / "automations" / "overseer_rate_limit_agent.py"), "--once"]},
        {"kind": "chill", "priority": 3, "description": "re-scan operator profile",
         "project": "sinister-overseer",
         "cmd": ["python", str(SANCTUM_ROOT / "projects" / "sinister-overseer" / "src" / "overseer" / "prompt_profiler.py"), "--scan", "--profile", "operator"]},
        {"kind": "chill", "priority": 2, "description": "auto-categorize picker",
         "project": "sanctum",
         "cmd": ["python", str(SANCTUM_ROOT / "automations" / "project_manager.py"), "categorize"]},
    ]
    with QUEUE.open("a", encoding="utf-8") as fh:
        for t in defaults:
            fh.write(json.dumps({"ts_added": utc_iso(), **t}, ensure_ascii=False) + "\n")


def read_queue() -> list[dict]:
    if not QUEUE.exists():
        return []
    rows: list[dict] = []
    try:
        for line in QUEUE.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        return []
    return rows


def rewrite_queue(rows: list[dict]) -> None:
    try:
        if rows:
            QUEUE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        else:
            QUEUE.write_text("", encoding="utf-8")
    except Exception:
        pass


def fire_task(task: dict, dry_run: bool = False) -> dict:
    cmd = task.get("cmd")
    if not cmd or not isinstance(cmd, list):
        return {"ok": False, "error": "bad-cmd"}
    if dry_run:
        log_fired({"action": "dry-run-fire", "task": task})
        return {"ok": True, "dry_run": True}
    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x00000008
        subprocess.Popen(
            cmd, creationflags=creationflags,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, close_fds=True,
        )
        log_fired({"action": "fired", "task": task})
        return {"ok": True}
    except Exception as exc:
        log_fired({"action": "fire-FAIL", "task": task, "error": str(exc)})
        return {"ok": False, "error": str(exc)}


def decide(usage: dict, live_agents: int) -> dict:
    session = usage.get("session", {}) if usage else {}
    pct = int(session.get("pct") or 0)
    available_pct = max(0, 100 - pct)
    reset = session.get("reset_utc") or ""
    rem_min = remaining_minutes(reset) if reset else 999

    if rem_min < END_OF_WINDOW_MIN and available_pct > END_OF_WINDOW_AVAIL:
        return {"mode": "spare-capacity-window", "fire_count": SPARE_FIRE_PER_PASS,
                "reason": f"{rem_min:.1f}min left + {available_pct}% available -- use it or lose it",
                "available_pct": available_pct, "remaining_min": rem_min}
    if available_pct > IDLE_AVAIL_PCT and live_agents == 0:
        return {"mode": "idle-fill", "fire_count": IDLE_FIRE_PER_PASS,
                "reason": f"{available_pct}% available, 0 live agents -- fill background work",
                "available_pct": available_pct, "remaining_min": rem_min}
    return {"mode": "normal", "fire_count": 0,
            "reason": f"{available_pct}% available, {live_agents} live, {rem_min:.1f}min left -- no fire",
            "available_pct": available_pct, "remaining_min": rem_min}


def run_once(dry_run: bool = False) -> dict:
    usage = read_usage()
    if not usage:
        return {"ok": False, "error": "no-usage-cache", "ts": utc_iso()}
    seed_defaults()
    live = live_agent_count()
    decision = decide(usage, live)
    if decision["fire_count"] == 0:
        log_fired({"action": "scan", **decision, "live_agents": live})
        return {"ok": True, "decision": decision, "live_agents": live, "fired": 0}
    queue = read_queue()
    queue.sort(key=lambda r: r.get("priority", 0), reverse=True)
    fired = 0
    remaining: list[dict] = []
    for task in queue:
        if fired < decision["fire_count"]:
            r = fire_task(task, dry_run=dry_run)
            if r.get("ok"):
                fired += 1
                continue
        remaining.append(task)
    if not dry_run:
        rewrite_queue(remaining)
    return {"ok": True, "decision": decision, "live_agents": live,
            "fired": fired, "queue_remaining": len(remaining)}


def queue_add(cmd: list[str], kind: str = "chill", project: str = "sanctum",
              priority: int = 3, description: str = "") -> dict:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    task = {"ts_added": utc_iso(), "kind": kind, "cmd": cmd,
            "project": project, "priority": priority, "description": description}
    with QUEUE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(task, ensure_ascii=False) + "\n")
    return {"ok": True, "enqueued": task}


def install_schtask() -> int:
    pw = shutil.which("pythonw") or str(Path(sys.executable).parent / "pythonw.exe")
    py = pw if Path(pw).exists() else sys.executable
    script = str(Path(__file__).resolve())
    action = f'"{py}" "{script}" --once'
    cmd = ["schtasks.exe", "/Create", "/F", "/TN", SCHTASK_NAME,
           "/TR", action, "/SC", "MINUTE", "/MO", "1", "/RL", "LIMITED"]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if cp.returncode == 0:
            print(f"[token-agent] schtask {SCHTASK_NAME} installed (1-min cadence, headless)")
            return 0
        print(f"[token-agent] schtask install failed: {cp.stderr.strip()}", file=sys.stderr)
        return cp.returncode
    except Exception as exc:
        print(f"[token-agent] install error: {exc}", file=sys.stderr)
        return 1


def uninstall_schtask() -> int:
    try:
        cp = subprocess.run(["schtasks.exe", "/Delete", "/TN", SCHTASK_NAME, "/F"],
                            capture_output=True, text=True, timeout=15)
        print(f"[token-agent] uninstall rc={cp.returncode}")
        return cp.returncode
    except Exception as exc:
        print(f"[token-agent] uninstall error: {exc}", file=sys.stderr)
        return 1


def status() -> int:
    usage = read_usage()
    if not usage:
        print("[token-agent] no usage cache yet")
        return 0
    live = live_agent_count()
    decision = decide(usage, live)
    print(f"[token-agent] status @ {utc_iso()}")
    print(f"  session.pct:      {usage.get('session', {}).get('pct')}%")
    print(f"  session.reset:    {usage.get('session', {}).get('reset_utc')}")
    print(f"  available_pct:    {decision['available_pct']}%")
    print(f"  remaining_min:    {decision['remaining_min']:.1f}")
    print(f"  live_agents:      {live}")
    print(f"  mode:             {decision['mode']}")
    print(f"  reason:           {decision['reason']}")
    print(f"  queue length:     {len(read_queue())}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true")
    g.add_argument("--watch", action="store_true")
    g.add_argument("--install-schtask", action="store_true")
    g.add_argument("--uninstall", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--queue-add", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--kind", default="chill")
    ap.add_argument("--project", default="sanctum")
    ap.add_argument("--priority", type=int, default=3)
    ap.add_argument("--description", default="")
    args = ap.parse_args(argv)

    if args.install_schtask:
        return install_schtask()
    if args.uninstall:
        return uninstall_schtask()
    if args.status:
        return status()
    if args.queue_add:
        r = queue_add(list(args.queue_add), args.kind, args.project, args.priority, args.description)
        print(json.dumps(r, indent=2))
        return 0
    if args.once:
        r = run_once(dry_run=args.dry_run)
        print(json.dumps(r, indent=2))
        return 0
    if args.watch:
        while True:
            try:
                r = run_once(dry_run=args.dry_run)
                if r.get("fired", 0) > 0:
                    print(f"[token-agent] fired={r['fired']} mode={r['decision']['mode']}")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
