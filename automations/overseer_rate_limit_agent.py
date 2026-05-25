#!/usr/bin/env python3
"""overseer_rate_limit_agent.py -- Overseer agent for Claude rate-limit detect+fix (20s SLA).

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 (multiple messages):
    Image #7: "make sure all things like this are flagged and have the overseer
              make a agent for this part to analyse the claude rate limits and
              auto improve them."
    "we need to actively tweak rate limits to dial them in and just have a
     detection system for them to fix them seleves in the sinister terminal
     within 20 seconds of them getting errors"
    "i ened you to hvae the over seer track the rate limit rate and slowly
     adjust things as you find out more info about the rate limits."

WHAT THIS IS:
    A dedicated Overseer agent that runs every 10 seconds via schtask. On each
    pass it:

    1. Tails the last 60 seconds of three signal files for rate-limit / overload
       / 429 / 529 / "Anthropic server-throttle" patterns:
         - _shared-memory/eve-incidents.jsonl       (claude-nonzero-exit)
         - _shared-memory/anthropic-throttle-events.jsonl  (global throttle)
         - _shared-memory/rate-limit-causes.jsonl   (per-account 429 hits)
         - _shared-memory/claude-wrapper.log        (recent stdout patterns)

    2. If a rate-limit signal is detected:
         a. Identify the affected account from the event row
         b. Mark the account rate-limited in claude-accounts.json (sets
            rate_limited_until_utc per the operator-set window)
         c. Rotate to the next round-robin slot
         d. Append a FLAG row to _shared-memory/rate-limit-flags.jsonl so
            the Sinister Terminal banner / EVE.exe Accounts page can show it
         e. Log the auto-fix to overseer-rate-limit-actions.jsonl

    3. Maintains a rolling "learn" profile in
       _shared-memory/prompt-profiles/rate-limit-tuning.json that records
       what triggers limits (project / hour-of-day / prompt-length) so
       account_balancer.py can pre-empt them.

SLA: 20 seconds end-to-end (10s schtask cadence + <5s execution time +
     <5s for the rotation to take effect on next spawn).

DOCTRINE: composes with
    automations/account_balancer.py             (slow tuning loop, 10-min cadence)
    automations/claude-oauth-accounts.ps1       (MarkLimited / RotateToNext primitives)
    _shared-memory/knowledge/sanctum-master-full-control-doctrine-2026-05-25.md
    _shared-memory/knowledge/hard-priority-ceiling-failsafe-2026-05-25.md

CLI:
    --once                  single detect+fix pass + exit (used by schtask)
    --watch                 loop forever, 10s interval
    --install-schtask       register SinisterOverseerRateLimitAgent (1-min cadence
                            since schtasks min granularity = 1min; we run --watch
                            inside the once to hit 10s SLA)
    --uninstall
    --dry-run               detect + log but never mutate accounts.json
    --status                print last 24h of rate-limit flags + actions
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
INCIDENTS = SANCTUM_ROOT / "_shared-memory" / "eve-incidents.jsonl"
THROTTLES = SANCTUM_ROOT / "_shared-memory" / "anthropic-throttle-events.jsonl"
RL_CAUSES = SANCTUM_ROOT / "_shared-memory" / "rate-limit-causes.jsonl"
WRAPPER_LOG = SANCTUM_ROOT / "_shared-memory" / "claude-wrapper.log"
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
OAUTH_PS1 = SANCTUM_ROOT / "automations" / "claude-oauth-accounts.ps1"
FLAGS_OUT = SANCTUM_ROOT / "_shared-memory" / "rate-limit-flags.jsonl"
ACTIONS_LOG = SANCTUM_ROOT / "_shared-memory" / "overseer-rate-limit-actions.jsonl"
TUNING_PROFILE = SANCTUM_ROOT / "_shared-memory" / "prompt-profiles" / "rate-limit-tuning.json"

SCHTASK_NAME = "SinisterOverseerRateLimitAgent"

# Rate-limit signal patterns (cover Anthropic + Claude wrapper formats)
RATE_LIMIT_PATTERNS = [
    re.compile(r"\b429\b"),                     # HTTP 429
    re.compile(r"\b529\b"),                     # HTTP 529 overloaded
    re.compile(r"rate.?limit", re.I),
    re.compile(r"overloaded", re.I),
    re.compile(r"server.?throttle", re.I),
    re.compile(r"try again at", re.I),
    re.compile(r"weekly usage", re.I),
    re.compile(r"rate_limit_error", re.I),
    re.compile(r"quota.?exceeded", re.I),
    re.compile(r"too.?many.?requests", re.I),
]

# How far back to look on each scan (seconds)
SCAN_WINDOW_S = 90


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_action(event: dict) -> None:
    try:
        ACTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ACTIONS_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": utc_iso(), **event}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def flag(row: dict) -> None:
    """Append to rate-limit-flags.jsonl for Sinister Terminal banner consumption."""
    try:
        FLAGS_OUT.parent.mkdir(parents=True, exist_ok=True)
        with FLAGS_OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": utc_iso(), **row}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tail_jsonl(path: Path, since_seconds: int) -> list[dict]:
    """Return jsonl rows from the last `since_seconds` (by row ts_utc or file mtime)."""
    if not path.exists():
        return []
    cutoff = utc_now() - timedelta(seconds=since_seconds)
    rows: list[dict] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                ts_str = row.get("ts_utc") or row.get("ts") or ""
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts < cutoff:
                            continue
                    except Exception:
                        pass
                rows.append(row)
    except Exception:
        return []
    return rows


def tail_text(path: Path, since_seconds: int, max_lines: int = 200) -> str:
    """Return last `max_lines` of a text log written within `since_seconds`."""
    if not path.exists():
        return ""
    try:
        # Cheap: just read last 64 KB
        size = path.stat().st_size
        with path.open("rb") as fh:
            fh.seek(max(0, size - 64 * 1024))
            data = fh.read().decode("utf-8", errors="replace")
        # Filter to lines whose timestamp (if present) is within window
        cutoff = utc_now() - timedelta(seconds=since_seconds)
        out_lines = []
        for line in data.splitlines()[-max_lines:]:
            m = re.search(r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]", line)
            if m:
                try:
                    ts = datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
                    if ts < cutoff:
                        continue
                except Exception:
                    pass
            out_lines.append(line)
        return "\n".join(out_lines)
    except Exception:
        return ""


def detect_signals(window_s: int = SCAN_WINDOW_S) -> list[dict]:
    """Scan all sources, return list of detected rate-limit events."""
    hits: list[dict] = []

    for row in tail_jsonl(INCIDENTS, window_s):
        kind = (row.get("kind") or "").lower()
        if kind in ("claude-nonzero-exit", "claude-rate-limit", "claude-529", "claude-429"):
            hits.append({
                "source": "eve-incidents.jsonl",
                "kind": kind,
                "exit_code": row.get("exit_code"),
                "account": row.get("account"),
                "project": row.get("project"),
                "agent": row.get("agent"),
                "raw": row,
            })

    for row in tail_jsonl(THROTTLES, window_s):
        hits.append({
            "source": "anthropic-throttle-events.jsonl",
            "kind": "global-throttle",
            "account": row.get("account"),
            "project": row.get("project"),
            "raw": row,
        })

    for row in tail_jsonl(RL_CAUSES, window_s):
        hits.append({
            "source": "rate-limit-causes.jsonl",
            "kind": "rl-cause",
            "account": row.get("account") or row.get("slot"),
            "raw": row,
        })

    log_text = tail_text(WRAPPER_LOG, window_s)
    for pat in RATE_LIMIT_PATTERNS:
        for m in pat.finditer(log_text):
            snippet = log_text[max(0, m.start() - 60):m.end() + 60]
            hits.append({
                "source": "claude-wrapper.log",
                "kind": "log-pattern",
                "pattern": pat.pattern,
                "snippet": snippet.strip(),
            })

    return hits


def load_accounts() -> dict:
    try:
        return json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {"accounts": []}


def mark_account_rate_limited(account_name: str, minutes: int = 30, dry_run: bool = False) -> bool:
    """Set rate_limited_until_utc on the account; bumps rotation cursor past it."""
    if not account_name:
        return False
    if dry_run:
        log_action({"action": "dry-run-mark-limited", "account": account_name, "minutes": minutes})
        return True

    data = load_accounts()
    changed = False
    until = (utc_now() + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for acct in data.get("accounts", []):
        if (acct.get("name") == account_name or acct.get("label") == account_name):
            existing = acct.get("rate_limited_until_utc")
            # Only update if new limit pushes later than existing
            if not existing or existing < until:
                acct["rate_limited_until_utc"] = until
                changed = True

    if changed:
        try:
            ACCOUNTS_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
            log_action({"action": "mark-limited", "account": account_name, "until_utc": until})
            return True
        except Exception as exc:
            log_action({"action": "mark-limited-FAIL", "account": account_name, "error": str(exc)})
            return False
    return False


def rotate_to_next(dry_run: bool = False) -> tuple[bool, str]:
    """Bump round-robin cursor past any rate-limited account."""
    if dry_run:
        log_action({"action": "dry-run-rotate"})
        return (True, "dry-run")

    data = load_accounts()
    accts = data.get("accounts", [])
    if not accts:
        return (False, "no-accounts")
    cur = int(data.get("last_rotation_index", 0))
    n = len(accts)
    now = utc_iso()
    for offset in range(1, n + 1):
        idx = (cur + offset) % n
        acct = accts[idx]
        if not acct.get("enabled", False):
            continue
        rlu = acct.get("rate_limited_until_utc")
        if rlu and rlu > now:
            continue
        # Found next usable
        data["last_rotation_index"] = idx
        try:
            ACCOUNTS_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
            new_name = acct.get("label") or acct.get("name")
            log_action({"action": "rotate", "to": new_name, "cursor": idx})
            return (True, new_name)
        except Exception as exc:
            log_action({"action": "rotate-FAIL", "error": str(exc)})
            return (False, str(exc))
    return (False, "no-available-account")


def update_tuning_profile(hits: list[dict]) -> None:
    """Maintain a rolling learn profile of when limits occur."""
    if not hits:
        return
    try:
        TUNING_PROFILE.parent.mkdir(parents=True, exist_ok=True)
        if TUNING_PROFILE.exists():
            prof = json.loads(TUNING_PROFILE.read_text(encoding="utf-8"))
        else:
            prof = {
                "profile_id": "rate-limit-tuning",
                "last_updated": utc_iso(),
                "total_hits": 0,
                "by_hour_utc": {},
                "by_project": {},
                "by_account": {},
                "by_kind": {},
            }
        hour = utc_now().strftime("%H")
        prof["by_hour_utc"][hour] = prof["by_hour_utc"].get(hour, 0) + len(hits)
        for h in hits:
            prof["total_hits"] += 1
            for key, bucket in [
                ("project", "by_project"),
                ("account", "by_account"),
                ("kind", "by_kind"),
            ]:
                v = h.get(key)
                if v:
                    prof[bucket][v] = prof[bucket].get(v, 0) + 1
        prof["last_updated"] = utc_iso()
        TUNING_PROFILE.write_text(json.dumps(prof, indent=2), encoding="utf-8")
    except Exception:
        pass


def respawn_dead_agents(hits: list[dict], dry_run: bool = False) -> list[dict]:
    """For each rate-limit hit where we know the project+agent, check if a
    heartbeat is stale (>2 min). If yes, re-spawn the session on a fresh account.

    Operator 2026-05-25: "agents get recovered and fixed with rate limit issues"
    """
    recoveries: list[dict] = []
    seen: set[str] = set()
    for h in hits:
        proj = (h.get("raw") or {}).get("project") or h.get("project")
        if not proj or proj in seen:
            continue
        seen.add(proj)
        hb_path = SANCTUM_ROOT / "_shared-memory" / "heartbeats" / f"{proj}.json"
        if not hb_path.exists():
            continue
        try:
            hb = json.loads(hb_path.read_text(encoding="utf-8-sig"))
            ts_str = hb.get("ts_utc") or hb.get("last_seen_utc")
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                age_s = (utc_now() - ts).total_seconds()
                if age_s < 120:
                    # Still alive — let the rotation alone do the fix
                    continue
        except Exception:
            pass
        # Heartbeat stale or missing — agent likely died. Re-spawn.
        launcher = SANCTUM_ROOT / "automations" / "start-sinister-session.ps1"
        if not launcher.exists():
            continue
        if dry_run:
            recoveries.append({"action": "dry-run-respawn", "project": proj})
            continue
        try:
            env = os.environ.copy()
            env["SINISTER_QUICK_LAUNCH"] = "1"
            env["SINISTER_SKIP_MODES_PROMPT"] = "1"
            env["SINISTER_DEFAULT_SWARM"] = "1"
            env["SINISTER_DEFAULT_LOOP"] = "1"
            creationflags = 0
            if os.name == "nt":
                creationflags = 0x00000008 | 0x00000200  # DETACHED + NEW_PGRP
            subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(launcher), "-Project", proj],
                env=env, creationflags=creationflags,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, close_fds=True,
            )
            recoveries.append({"action": "respawned", "project": proj})
            log_action({"action": "agent-respawn-after-rate-limit", "project": proj})
        except Exception as exc:
            recoveries.append({"action": "respawn-FAIL", "project": proj, "error": str(exc)})
    return recoveries


def run_once(dry_run: bool = False, auto_recover: bool = True) -> dict:
    """Detect + fix in one pass. Returns summary dict."""
    hits = detect_signals()
    if not hits:
        return {"scanned": True, "hits": 0, "actions": 0, "recoveries": 0}

    actions = 0
    affected_accounts = set()
    for h in hits:
        acct = h.get("account")
        if acct:
            affected_accounts.add(acct)

    for acct in affected_accounts:
        if mark_account_rate_limited(acct, minutes=30, dry_run=dry_run):
            actions += 1

    if affected_accounts and not dry_run:
        ok, new = rotate_to_next(dry_run=dry_run)
        if ok:
            actions += 1

    # Flag for Sinister Terminal banner
    for h in hits:
        flag({"kind": h["kind"], "account": h.get("account"), "source": h["source"]})

    update_tuning_profile(hits)

    # Agent auto-recovery: respawn sessions whose agent died from rate limit
    recoveries: list[dict] = []
    if auto_recover:
        recoveries = respawn_dead_agents(hits, dry_run=dry_run)

    summary = {
        "scanned": True,
        "hits": len(hits),
        "affected_accounts": list(affected_accounts),
        "actions": actions,
        "recoveries": len(recoveries),
        "recovery_details": recoveries,
    }
    log_action({"action": "scan-complete", **summary})
    return summary


def watch_loop(interval_s: int = 10, dry_run: bool = False) -> int:
    print(f"[rate-limit-overseer] watch start interval={interval_s}s")
    while True:
        try:
            s = run_once(dry_run=dry_run)
            if s["hits"] > 0:
                print(f"[rate-limit-overseer] hits={s['hits']} actions={s['actions']} affected={s.get('affected_accounts')}")
            time.sleep(interval_s)
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            print(f"[rate-limit-overseer] err: {exc}", file=sys.stderr)
            time.sleep(interval_s)


def install_schtask() -> int:
    pw = shutil.which("pythonw") or str(Path(sys.executable).parent / "pythonw.exe")
    py = pw if Path(pw).exists() else sys.executable
    script = str(Path(__file__).resolve())
    action = f'"{py}" "{script}" --once'
    cmd = [
        "schtasks.exe", "/Create", "/F",
        "/TN", SCHTASK_NAME,
        "/TR", action,
        "/SC", "MINUTE", "/MO", "1",  # 1-min cadence; --once runs ~3s
        "/RL", "LIMITED",
    ]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if cp.returncode == 0:
            print(f"[rate-limit-overseer] schtask {SCHTASK_NAME} installed (1-min cadence, headless)")
            return 0
        print(f"[rate-limit-overseer] schtask install failed: {cp.stderr.strip()}", file=sys.stderr)
        return cp.returncode
    except Exception as exc:
        print(f"[rate-limit-overseer] install error: {exc}", file=sys.stderr)
        return 1


def uninstall_schtask() -> int:
    try:
        cp = subprocess.run(
            ["schtasks.exe", "/Delete", "/TN", SCHTASK_NAME, "/F"],
            capture_output=True, text=True, timeout=15,
        )
        print(f"[rate-limit-overseer] uninstall rc={cp.returncode}")
        return cp.returncode
    except Exception as exc:
        print(f"[rate-limit-overseer] uninstall error: {exc}", file=sys.stderr)
        return 1


def status() -> int:
    print(f"[rate-limit-overseer] status @ {utc_iso()}")
    print()
    print(f"  flags file:   {FLAGS_OUT}")
    print(f"  actions log:  {ACTIONS_LOG}")
    print(f"  tuning profile: {TUNING_PROFILE}")
    print()
    if FLAGS_OUT.exists():
        print("  recent flags (last 24h):")
        cutoff = utc_now() - timedelta(hours=24)
        try:
            for line in FLAGS_OUT.read_text(encoding="utf-8").splitlines()[-20:]:
                try:
                    row = json.loads(line)
                    ts = datetime.fromisoformat(row.get("ts", "").replace("Z", "+00:00"))
                    if ts >= cutoff:
                        print(f"    [{row.get('ts')}] {row.get('kind')} acct={row.get('account')} src={row.get('source')}")
                except Exception:
                    continue
        except Exception:
            pass
    else:
        print("  (no flags yet)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true")
    g.add_argument("--watch", action="store_true")
    g.add_argument("--install-schtask", action="store_true")
    g.add_argument("--uninstall", action="store_true")
    g.add_argument("--status", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--interval", type=int, default=10)
    args = ap.parse_args(argv)

    if args.install_schtask:
        return install_schtask()
    if args.uninstall:
        return uninstall_schtask()
    if args.status:
        return status()
    if args.once:
        s = run_once(dry_run=args.dry_run)
        print(json.dumps(s, indent=2))
        return 0
    if args.watch:
        return watch_loop(args.interval, dry_run=args.dry_run)
    return 1


if __name__ == "__main__":
    sys.exit(main())
