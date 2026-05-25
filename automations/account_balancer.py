#!/usr/bin/env python3
"""account_balancer.py -- overseer rate-limit feedback loop for OAuth account fleet.

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25 ~06:30Z (Image 1 reinforcement):
    "make sure you place in good round robin jerry rigging so that we can use
     the 4 different accounts flking under the radar to gain more power. i
     ened you to hvae the over seer track the rate limit rate and slowly
     adjust things as you find out more info about the rate limits."

What it does:
    Periodically reads usage cache + rate-limit causes + accounts.json and emits
    a per-account recommendation (ROTATE/THROTTLE/SAFE/EXHAUST). In --auto-mark-
    limited mode, it invokes claude-oauth-accounts.ps1 MarkLimited for any account
    crossing thresholds. Schedules itself via schtasks (--install-schtask).

Thresholds (conservative, adjustable):
    SESSION_HOT_PCT     = 95   # >= flips to EXHAUST
    SESSION_WARN_PCT    = 80   # >= flips to THROTTLE
    WEEKLY_HOT_PCT      = 85   # >= flips to ROTATE
    WEEKLY_WARN_PCT     = 70   # >= flips to THROTTLE
    RECENT_429_WINDOW_M = 5    # any 429 in last N min => ROTATE

CLI:
    --scan                  read state, print verdict per account (no mutation)
    --auto-mark-limited     run --scan then call MarkLimited for HOT accounts
    --recommend             print one-table recommendation (for dashboards / EVE.exe)
    --install-schtask       register SinisterAccountBalancer schtask (10-min cadence)
    --dry-run               never invoke PS1 (paired with --auto-mark-limited)

Outputs:
    stdout                                        recommendation table
    _shared-memory/account-balancer-log.jsonl     audit log (one row per scan)

Composes with:
    automations/claude-oauth-accounts.ps1     MarkLimited / RotateToNext
    automations/multi_agent_launcher.py       reads recommendation indirectly
    _shared-memory/anthropic-usage-cache.default.json   usage source
    _shared-memory/rate-limit-causes.jsonl    429 history source
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
USAGE_CACHE = SANCTUM_ROOT / "_shared-memory" / "anthropic-usage-cache.default.json"
RL_CAUSES = SANCTUM_ROOT / "_shared-memory" / "rate-limit-causes.jsonl"
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
OAUTH_PS1 = SANCTUM_ROOT / "automations" / "claude-oauth-accounts.ps1"
LOG_FILE = SANCTUM_ROOT / "_shared-memory" / "account-balancer-log.jsonl"

SESSION_HOT_PCT = 95
SESSION_WARN_PCT = 80
WEEKLY_HOT_PCT = 85
WEEKLY_WARN_PCT = 70
RECENT_429_WINDOW_M = 5


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_read_json(p: Path) -> dict | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return None


def read_recent_429s(window_min: int) -> dict[str, int]:
    """Return {account_name: count_in_window}."""
    out: dict[str, int] = {}
    if not RL_CAUSES.exists():
        return out
    cutoff = utc_now() - timedelta(minutes=window_min)
    try:
        for line in RL_CAUSES.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            ts = row.get("ts_utc", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if dt < cutoff:
                continue
            name = row.get("account_name", "?")
            out[name] = out.get(name, 0) + 1
    except Exception:
        pass
    return out


def classify(usage_session_pct: float, usage_weekly_pct: float, recent_429s: int) -> tuple[str, str]:
    """Return (verdict, one-line reason)."""
    if recent_429s > 0:
        return ("ROTATE", f"recent 429 x{recent_429s} (<{RECENT_429_WINDOW_M}m)")
    if usage_session_pct >= SESSION_HOT_PCT:
        return ("EXHAUST", f"session {usage_session_pct:.0f}% >= {SESSION_HOT_PCT}%")
    if usage_weekly_pct >= WEEKLY_HOT_PCT:
        return ("ROTATE", f"weekly {usage_weekly_pct:.0f}% >= {WEEKLY_HOT_PCT}%")
    if usage_session_pct >= SESSION_WARN_PCT or usage_weekly_pct >= WEEKLY_WARN_PCT:
        return ("THROTTLE", f"session {usage_session_pct:.0f}% / weekly {usage_weekly_pct:.0f}%")
    return ("SAFE", f"session {usage_session_pct:.0f}% / weekly {usage_weekly_pct:.0f}%")


def time_to_reset(reset_utc: str | None) -> str:
    if not reset_utc:
        return "?"
    try:
        dt = datetime.fromisoformat(reset_utc.replace("Z", "+00:00"))
        delta = dt - utc_now()
        if delta.total_seconds() <= 0:
            return "now"
        total_m = int(delta.total_seconds() // 60)
        h, m = divmod(total_m, 60)
        return f"{h}h{m:02d}m" if h else f"{m}m"
    except Exception:
        return "?"


def collect_recommendations() -> list[dict]:
    """Build a row per account with verdict + signals."""
    accounts_doc = safe_read_json(ACCOUNTS_JSON) or {}
    usage = safe_read_json(USAGE_CACHE) or {}
    recent_429s = read_recent_429s(RECENT_429_WINDOW_M)

    session = usage.get("session", {}) or {}
    weekly = usage.get("weekly_all", {}) or {}
    cache_slot = usage.get("slot", "default")

    rows: list[dict] = []
    for a in accounts_doc.get("accounts", []):
        name = a.get("name", "?")
        # Usage cache only covers the slot it was probed against; if name matches
        # we use it, otherwise fall back to per-account fields.
        sess_pct = float(session.get("pct", 0) or 0) if name == cache_slot else 0.0
        wk_pct = float(weekly.get("pct", 0) or 0) if name == cache_slot else 0.0
        rl_until = a.get("rate_limited_until_utc")
        rl_active = False
        if rl_until:
            try:
                rl_active = datetime.fromisoformat(rl_until.replace("Z", "+00:00")) > utc_now()
            except Exception:
                rl_active = False
        recent = recent_429s.get(name, 0)
        if rl_active:
            verdict = "EXHAUST"
            reason = f"limited until {rl_until}"
        else:
            verdict, reason = classify(sess_pct, wk_pct, recent)
        rows.append({
            "name": name,
            "enabled": bool(a.get("enabled", False)),
            "linked": bool(a.get("linked", False)),
            "session_pct": sess_pct,
            "weekly_pct": wk_pct,
            "recent_429s": recent,
            "ttr_session": time_to_reset(session.get("reset_utc") if name == cache_slot else None),
            "ttr_weekly": time_to_reset(weekly.get("reset_utc") if name == cache_slot else None),
            "rate_limited_until_utc": rl_until,
            "verdict": verdict,
            "reason": reason,
            "spawns_today": int(a.get("successful_spawns_today", 0) or 0),
        })
    return rows


def render_table(rows: list[dict]) -> str:
    if not rows:
        return "(no accounts found in claude-accounts.json)"
    lines: list[str] = []
    header = f"{'account':<12} {'state':<10} {'sess%':>6} {'wk%':>5} {'429/5m':>7} {'reset':>7} {'verdict':<10} reason"
    lines.append(header)
    lines.append("-" * len(header))
    for r in rows:
        state = "off"
        if r["enabled"] and r["linked"]:
            state = "ON"
        elif r["enabled"]:
            state = "UNLINKED"
        lines.append(
            f"{r['name']:<12} {state:<10} "
            f"{r['session_pct']:>5.0f}% {r['weekly_pct']:>4.0f}% "
            f"{r['recent_429s']:>7d} "
            f"{r['ttr_session']:>7} "
            f"{r['verdict']:<10} {r['reason']}"
        )
    return "\n".join(lines)


def append_log(rows: list[dict], action: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts_utc": utc_iso(), "action": action, "rows": rows}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def auto_mark_limited(rows: list[dict], dry_run: bool) -> int:
    if not OAUTH_PS1.exists():
        print(f"WARN: oauth ps1 missing at {OAUTH_PS1}; skipping mark-limited")
        return 0
    marked = 0
    for r in rows:
        if r["verdict"] in ("ROTATE", "EXHAUST") and not r.get("rate_limited_until_utc"):
            until = (utc_now() + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            cmd = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(OAUTH_PS1), "-Action", "MarkLimited",
                "-Name", r["name"], "-Until", until,
            ]
            print(f"  -> MarkLimited {r['name']} until {until}  ({r['reason']})")
            if not dry_run:
                try:
                    subprocess.run(cmd, check=False, capture_output=True)
                except Exception as e:
                    print(f"     fail: {e!r}")
                    continue
            marked += 1
    return marked


def install_schtask() -> int:
    """Register SinisterAccountBalancer schtask -- 10-min cadence."""
    py_exe = sys.executable
    script = str(Path(__file__).resolve())
    tr = f"\"{py_exe}\" \"{script}\" --auto-mark-limited"
    cmd = [
        "schtasks", "/Create", "/F",
        "/SC", "MINUTE", "/MO", "10",
        "/TN", "SinisterAccountBalancer",
        "/TR", tr,
    ]
    print(f"  Registering schtask: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode != 0:
            print(f"  stderr: {r.stderr.strip()}")
            return r.returncode
        print("  OK schtask installed (10-min cadence)")
        return 0
    except FileNotFoundError:
        print("  ERROR: schtasks.exe not available on this platform")
        return 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--auto-mark-limited", action="store_true")
    ap.add_argument("--recommend", action="store_true")
    ap.add_argument("--install-schtask", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.install_schtask:
        return install_schtask()

    if not (args.scan or args.auto_mark_limited or args.recommend):
        ap.print_help()
        return 0

    rows = collect_recommendations()
    table = render_table(rows)
    print(table)

    if args.auto_mark_limited:
        marked = auto_mark_limited(rows, dry_run=args.dry_run)
        print(f"\nmarked-limited: {marked} account(s){' [dry-run]' if args.dry_run else ''}")
        append_log(rows, "auto-mark-limited")
    elif args.scan:
        append_log(rows, "scan")
    elif args.recommend:
        # recommend is read-only; no log row
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
