#!/usr/bin/env python3
"""multi_agent_status.py -- live multi-pane fleet dashboard + batch ops.

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25 ~06:30Z (Tony Stark brief):
    "think of how i can control, open, manage multiple claude agents at once
     in the most efficent manner..."

Reads:
    _shared-memory/heartbeats/<slug>.json     liveness + focus_intent
    _shared-memory/PROGRESS/<display>.md      latest log row
    _shared-memory/agent-modes/<slug>.json    swarm/loop/loop_relentless flags
    automations/session-templates/agent-prefs.json   per-agent display+accent

CLI:
    --once                       print one-shot table
    --watch [--interval 5]       refresh in place every N sec until Ctrl-C
    --batch <action> [...]       batch op across LIVE agents (heartbeat < 60m)
        --batch poke --message "..."
        --batch save-close
        --batch rotate-account
        --batch resume-all
    --dry-run                    print planned batch commands without invoking

Live status thresholds:
    RUNNING  heartbeat < 5 min
    STALL    5 <= age_min < 60
    CRASHED  age_min >= 60
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

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
HB_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
PROG_DIR = SANCTUM_ROOT / "_shared-memory" / "PROGRESS"
MODES_DIR = SANCTUM_ROOT / "_shared-memory" / "agent-modes"
PREFS_FILE = SANCTUM_ROOT / "automations" / "session-templates" / "agent-prefs.json"
POKE_PS1 = SANCTUM_ROOT / "automations" / "agent-poke.ps1"
ACTIONS_PS1 = SANCTUM_ROOT / "automations" / "agent-actions.ps1"
OAUTH_PS1 = SANCTUM_ROOT / "automations" / "claude-oauth-accounts.ps1"
LAUNCHER_PY = SANCTUM_ROOT / "automations" / "multi_agent_launcher.py"

# ANSI
RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
PURPLE = "\033[35m"
WHITE = "\033[97m"
CLEAR_HOME = "\033[2J\033[H"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def age_minutes(ts: str) -> float:
    if not ts:
        return 99999.0
    try:
        # Accept both "...Z" and "+00:00" forms; also "YYYY-MM-DDTHH:MMZ" (no seconds).
        ts_norm = ts.replace("Z", "+00:00")
        # If seconds missing, fromisoformat will throw on 3.10 but works 3.11+; tolerate.
        try:
            dt = datetime.fromisoformat(ts_norm)
        except ValueError:
            # Try inserting :00 seconds
            if len(ts_norm) >= 17 and ts_norm[16] == "+":
                ts_norm = ts_norm[:16] + ":00" + ts_norm[16:]
                dt = datetime.fromisoformat(ts_norm)
            else:
                raise
        return max(0.0, (utc_now() - dt).total_seconds() / 60.0)
    except Exception:
        return 99999.0


def status_for_age(age_min: float) -> tuple[str, str]:
    if age_min < 5:
        return ("RUNNING", GREEN)
    if age_min < 60:
        return ("STALL", YELLOW)
    return ("CRASHED", RED)


def format_age(age_min: float) -> str:
    if age_min >= 99999:
        return "??"
    if age_min < 1:
        return f"{int(age_min * 60)}s"
    if age_min < 60:
        return f"{int(age_min)}m"
    h = age_min / 60
    if h < 24:
        return f"{h:.1f}h"
    return f"{h / 24:.1f}d"


def read_modes(slug: str) -> dict:
    f = MODES_DIR / f"{slug}.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {}


def latest_progress_line(display: str) -> str:
    f = PROG_DIR / f"{display}.md"
    if not f.exists():
        return ""
    try:
        # PROGRESS is most-recent-at-top; first non-blank non-header line
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            return s[:80]
    except Exception:
        pass
    return ""


def collect_rows() -> list[dict]:
    rows: list[dict] = []
    if not HB_DIR.exists():
        return rows
    for hb in sorted(HB_DIR.glob("*.json")):
        try:
            d = json.loads(hb.read_text(encoding="utf-8-sig", errors="replace"))
        except Exception:
            continue
        slug = d.get("slug") or hb.stem
        display = d.get("agent_display") or d.get("agent") or slug
        ts = d.get("ts_utc", "")
        age = age_minutes(ts)
        state, color = status_for_age(age)
        modes = read_modes(slug)
        account = d.get("account") or os.environ.get("SINISTER_ACCOUNT", "?")
        rows.append({
            "slug": slug,
            "display": display,
            "account": account,
            "age_min": age,
            "state": state,
            "color": color,
            "loop_iter": d.get("loop_iter", "?"),
            "swarm": modes.get("swarm", False),
            "loop": modes.get("loop", False),
            "branch": d.get("branch", ""),
            "focus": (d.get("focus_intent") or "")[:60],
            "progress": latest_progress_line(display),
        })
    rows.sort(key=lambda r: r["age_min"])
    return rows


def render_once(rows: list[dict]) -> str:
    out: list[str] = []
    out.append(f"{PURPLE}{BOLD}--- Sinister Fleet Dashboard ---{RESET}  "
               f"{DIM}{utc_now().strftime('%Y-%m-%d %H:%M:%SZ')}{RESET}")
    out.append("")
    if not rows:
        out.append(f"{DIM}(no heartbeats in {HB_DIR}){RESET}")
        out.append("")
        return "\n".join(out)
    header = f"{'slug':<28} {'state':<8} {'age':>6} {'acct':<10} {'sw':<3}{'lp':<3} {'iter':>4}  focus"
    out.append(f"{WHITE}{header}{RESET}")
    out.append(DIM + "-" * len(header) + RESET)
    running = stall = crashed = 0
    for r in rows:
        if r["state"] == "RUNNING":
            running += 1
        elif r["state"] == "STALL":
            stall += 1
        else:
            crashed += 1
        sw = f"{GREEN}S{RESET}" if r["swarm"] else f"{DIM}-{RESET}"
        lp = f"{GREEN}L{RESET}" if r["loop"] else f"{DIM}-{RESET}"
        state_seg = f"{r['color']}{r['state']:<8}{RESET}"
        out.append(
            f"{WHITE}{r['slug'][:28]:<28}{RESET} {state_seg} "
            f"{format_age(r['age_min']):>6} "
            f"{CYAN}{str(r['account'])[:10]:<10}{RESET} "
            f"{sw}  {lp}  "
            f"{str(r['loop_iter']):>4}  "
            f"{DIM}{r['focus']}{RESET}"
        )
    out.append("")
    out.append(f"  {GREEN}RUNNING {running}{RESET}   "
               f"{YELLOW}STALL {stall}{RESET}   "
               f"{RED}CRASHED {crashed}{RESET}   "
               f"{DIM}total {len(rows)}{RESET}")
    out.append("")
    return "\n".join(out)


def watch_loop(interval: int) -> int:
    try:
        while True:
            rows = collect_rows()
            sys.stdout.write(CLEAR_HOME)
            sys.stdout.write(render_once(rows))
            sys.stdout.write(f"\n{DIM}refresh every {interval}s  --  Ctrl-C to exit{RESET}\n")
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{DIM}watch exit{RESET}")
        return 0


def live_slugs(rows: list[dict], max_age_min: int = 60) -> list[str]:
    return [r["slug"] for r in rows if r["age_min"] < max_age_min]


def run_batch(action: str, message: str, dry_run: bool) -> int:
    rows = collect_rows()
    targets = live_slugs(rows)
    if not targets:
        print(f"{YELLOW}(no live agents to batch on){RESET}")
        return 0
    print(f"batch={action} targets={len(targets)} dry_run={dry_run}")
    fails = 0
    for slug in targets:
        ok = True
        if action == "poke":
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(POKE_PS1), "-Action", "Poke", "-Slug", slug]
            if message:
                cmd += ["-Reason", message]
        elif action == "save-close":
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(ACTIONS_PS1), "-Action", "SaveAndClose", "-Slug", slug]
        elif action == "rotate-account":
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                   "-File", str(OAUTH_PS1), "-Action", "RotateToNext"]
        elif action == "resume-all":
            # Resume strategy: invoke multi_agent_launcher.py with solo-deep preset
            # for any CRASHED slug. Conservative single-shot only.
            cmd = [sys.executable, str(LAUNCHER_PY), "--swarm", "solo-deep"]
            if dry_run:
                cmd.append("--dry-run")
        else:
            print(f"{RED}unknown batch action: {action}{RESET}")
            return 2
        print(f"  -> {slug}: {' '.join(cmd[:5])}...")
        if dry_run:
            continue
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                ok = False
                print(f"     fail rc={r.returncode}  {r.stderr.strip()[:120]}")
        except Exception as e:
            ok = False
            print(f"     exception: {e!r}")
        if not ok:
            fails += 1
        # resume-all only runs once (the preset handles fan-out)
        if action == "resume-all":
            break
    print(f"batch done. failures={fails}/{len(targets)}")
    return 0 if fails == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=5)
    ap.add_argument("--batch", type=str, default=None,
                    choices=["poke", "save-close", "rotate-account", "resume-all"])
    ap.add_argument("--message", type=str, default="")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.batch:
        return run_batch(args.batch, args.message, args.dry_run)
    if args.watch:
        return watch_loop(args.interval)
    # default = --once
    rows = collect_rows()
    print(render_once(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
