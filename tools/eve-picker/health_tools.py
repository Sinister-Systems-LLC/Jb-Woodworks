"""Health Tools sub-menu :: server-throttle vs plan-quota status surface.

Author: RKOJ-ELENO :: 2026-05-24

Wired into eve.py via the `H` picker shortcut. Reads:
  - _shared-memory/anthropic-throttle-events.jsonl   (global server-throttle, new)
  - _shared-memory/claude-accounts.log                (plan-quota / Mark-AccountRateLimited)

Distinguishes:
  - PLAN-QUOTA = per-account 429 (account rotation HELPS)
  - SERVER-THROTTLE = Anthropic global limiter (account rotation does NOT help;
    fix is fleet-burst dampening via SINISTER_FLEET_BURST_LIMIT env var).

Operator-facing surface — one-screen output, stdlib-only.
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ANSI accents shared with eve.py (local copy to avoid import cycle).
PURPLE = "\033[38;5;141m"
DARKP = "\033[38;5;91m"
BRIGHTP = "\033[38;5;177m"
WHITE = "\033[97m"
SOFT = "\033[38;5;245m"
DIM = "\033[38;5;240m"
OK = "\033[38;5;46m"
WARN = "\033[38;5;220m"
FAIL = "\033[38;5;196m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _sanctum_root() -> Path | None:
    """Resolve Sanctum root from env or conventional locations."""
    root_env = os.environ.get("SINISTER_SANCTUM_ROOT") or os.environ.get("SANCTUM_ROOT")
    candidates: list[Path] = []
    if root_env:
        candidates.append(Path(root_env))
    candidates += [
        Path(r"D:\Sinister Sanctum"),
        Path(r"C:\Sinister Sanctum"),
    ]
    for root in candidates:
        if (root / "_shared-memory").exists():
            return root
    return None


def _today_utc_prefix() -> str:
    """Return YYYY-MM-DD in UTC — used to filter today's events."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _parse_churned_seconds(excerpt: str) -> int | None:
    """Best-effort parse: 'Churned for 1m 5s' -> 65; 'Churned for 45s' -> 45."""
    if not excerpt:
        return None
    m = re.search(r"Churned for\s+(?:(\d+)m\s*)?(\d+)s", excerpt)
    if not m:
        return None
    minutes = int(m.group(1)) if m.group(1) else 0
    seconds = int(m.group(2))
    return minutes * 60 + seconds


def _read_throttle_events(root: Path) -> list[dict[str, Any]]:
    """Read anthropic-throttle-events.jsonl (server-throttle, new file)."""
    p = root / "_shared-memory" / "anthropic-throttle-events.jsonl"
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def _read_plan_quota_events(root: Path) -> list[dict[str, Any]]:
    """Parse claude-accounts.log for Mark-AccountRateLimited events."""
    p = root / "_shared-memory" / "claude-accounts.log"
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    try:
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                # log format example: "[2026-05-24T08:08:12Z] [INFO] Mark-AccountRateLimited: 'leo' limited until ..."
                if "Mark-AccountRateLimited" not in line:
                    continue
                tm = re.match(r"\[([0-9T:\-Z]+)\]", line)
                if not tm:
                    continue
                ts = tm.group(1)
                acct_m = re.search(r"'([^']+)'", line)
                acct = acct_m.group(1) if acct_m else "?"
                out.append({"ts_utc": ts, "account": acct, "raw": line.strip()})
    except OSError:
        pass
    return out


def _today_count(events: list[dict[str, Any]], today_prefix: str) -> int:
    """Count events whose ts_utc starts with today's date."""
    return sum(1 for e in events if str(e.get("ts_utc", "")).startswith(today_prefix))


def _avg_churned(events: list[dict[str, Any]]) -> float | None:
    """Average 'Churned for Xs' across throttle events. None if not parseable."""
    secs: list[int] = []
    for e in events:
        s = _parse_churned_seconds(e.get("excerpt", ""))
        if s is not None:
            secs.append(s)
    if not secs:
        return None
    return sum(secs) / len(secs)


def _hourly_rate(events: list[dict[str, Any]]) -> float:
    """Events per hour over the last 24h (rolling). 0 if none."""
    if not events:
        return 0.0
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - 24 * 3600
    count = 0
    for e in events:
        ts = e.get("ts_utc", "")
        try:
            t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if t.timestamp() >= cutoff:
                count += 1
        except (ValueError, TypeError):
            continue
    return count / 24.0


def _header(title: str) -> None:
    print()
    print(f"  {DARKP}{'=' * 68}{RESET}")
    print(f"  {WHITE}{BOLD} {title} {RESET}")
    print(f"  {DARKP}{'=' * 68}{RESET}")


def health_status() -> int:
    """One-screen Anthropic throttle health surface.

    Output:
      - # plan-quota events today
      - # server-throttle events today
      - avg "Churned for Xs" wait per server-throttle event
      - SINISTER_FLEET_BURST_LIMIT current value
      - Recommendation if server-throttle hourly rate > 1
    """
    _header("EVE :: Health (Anthropic throttle status)")

    root = _sanctum_root()
    if root is None:
        print(f"  {FAIL}[FAIL]{RESET} Sanctum root not found.")
        return 1

    today = _today_utc_prefix()
    server_throttle = _read_throttle_events(root)
    plan_quota = _read_plan_quota_events(root)

    st_today = _today_count(server_throttle, today)
    pq_today = _today_count(plan_quota, today)
    st_total = len(server_throttle)
    pq_total = len(plan_quota)
    avg = _avg_churned(server_throttle)
    rate = _hourly_rate(server_throttle)

    burst = os.environ.get("SINISTER_FLEET_BURST_LIMIT", "").strip()
    burst_disp = f"{BRIGHTP}{burst}{RESET}" if burst else f"{DIM}(unset — no limit){RESET}"

    print()
    print(f"  {SOFT}date (UTC):{RESET}              {today}")
    print()
    print(f"  {WHITE}{BOLD}Plan-quota events{RESET}  {DIM}(per-account 429; rotation helps){RESET}")
    print(f"    today:                  {OK if pq_today == 0 else WARN}{pq_today}{RESET}")
    print(f"    all-time:               {SOFT}{pq_total}{RESET}")
    print()
    print(f"  {WHITE}{BOLD}Server-throttle events{RESET}  {DIM}(Anthropic GLOBAL; rotation does NOT help){RESET}")
    print(f"    today:                  {OK if st_today == 0 else WARN}{st_today}{RESET}")
    print(f"    all-time:               {SOFT}{st_total}{RESET}")
    if avg is not None:
        print(f"    avg 'Churned for':      {SOFT}{avg:.1f}s{RESET}  {DIM}(per event){RESET}")
    else:
        print(f"    avg 'Churned for':      {DIM}n/a (no parseable wait times){RESET}")
    print(f"    rolling 24h rate:       {SOFT}{rate:.2f}/hr{RESET}")
    print()
    print(f"  {WHITE}{BOLD}Fleet-burst dampener{RESET}")
    print(f"    SINISTER_FLEET_BURST_LIMIT = {burst_disp}")
    print()

    # Recommendation logic.
    print(f"  {DARKP}{'-' * 68}{RESET}")
    if rate > 1.0:
        if not burst:
            print(f"  {WARN}[recommend]{RESET} server-throttle rate {rate:.2f}/hr > 1.0 — "
                  f"set {BRIGHTP}SINISTER_FLEET_BURST_LIMIT=2{RESET} in env to cap concurrent")
            print(f"               spawns and dampen the burst-rate that triggers the limiter.")
        else:
            print(f"  {WARN}[recommend]{RESET} still throttled with limit={burst} — try lowering to "
                  f"{BRIGHTP}SINISTER_FLEET_BURST_LIMIT={max(1, int(burst) - 1) if burst.isdigit() else 1}{RESET}.")
    elif st_today == 0 and pq_today == 0:
        print(f"  {OK}[healthy]{RESET}  no throttle events today.")
    else:
        print(f"  {DIM}[ok]{RESET}       rate within tolerances — no dampener needed.")
    print(f"  {DARKP}{'-' * 68}{RESET}")
    print()
    print(f"  {SOFT}log files:{RESET}")
    print(f"    {DIM}server-throttle:{RESET}  _shared-memory/anthropic-throttle-events.jsonl")
    print(f"    {DIM}plan-quota:{RESET}       _shared-memory/claude-accounts.log")
    print(f"  {SOFT}doctrine:{RESET}  _shared-memory/knowledge/anthropic-server-throttle-vs-plan-quota-2026-05-24.md")
    print()
    return 0


def menu_loop() -> int:
    """Health menu entry point. Single-screen + wait for Enter to return."""
    health_status()
    try:
        input(f"  {DIM}> press Enter to return to picker:{RESET} ")
    except (EOFError, KeyboardInterrupt):
        pass
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(menu_loop())
