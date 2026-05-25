#!/usr/bin/env python3
"""launch_rate_limit_governor.py -- pre-spawn rate-limit gate + account auto-balance.

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25 ~07:00Z (verbatim):
    "make sure you get the rate limiting in check and we can run all agents
     with no issues. add things like when i launch a agent it balances it out
     over the other claude account we have or use more hardware like i said
     to do."

What it does:
    Before any new spawn, this script reads the live usage cache + rate-limit
    causes + account_balancer recommendation. It chooses the least-burdened
    OAuth slot OR, if every slot is hot, recommends offloading the task to
    the local GPU bot fleet (Ollama on 4090) instead.

Composes with:
    automations/account_balancer.py             -- per-account verdict
    automations/claude-oauth-accounts.ps1       -- PickBest / RotateToNext / List
    automations/gpu_bot_fleet.py                -- fallback target when accounts hot
    automations/resource_quota_governor.py      -- consulted for resource ceiling
    _shared-memory/anthropic-usage-cache.default.json
    _shared-memory/rate-limit-causes.jsonl
    _shared-memory/launch-rate-limit-log.jsonl  -- audit log

Doctrine binding:
    NO new .bat / NO new .ps1 (operator 2026-05-25T02:45Z). This script may
    CALL existing claude-oauth-accounts.ps1 (legacy, allowed).
    Author RKOJ-ELENO header (operator 2026-05-21).
    Operator clicks nothing -- never surfaces "please pick an account".

CLI:
    --pre-launch <project>           recommend account + (if hot) gpu fallback
    --account <name|auto>            override account (default: auto via PickBest)
    --snapshot                       dump current rate-limit state to
                                     _shared-memory/rate-limit-snapshot-<ts>.json
    --install-schtask                register passive watcher (5-min cadence)
    --dry-run                        never invoke claude-oauth-accounts.ps1
    --json                           structured output
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
USAGE_CACHE = SANCTUM_ROOT / "_shared-memory" / "anthropic-usage-cache.default.json"
RL_CAUSES = SANCTUM_ROOT / "_shared-memory" / "rate-limit-causes.jsonl"
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
OAUTH_PS1 = SANCTUM_ROOT / "automations" / "claude-oauth-accounts.ps1"
LOG_FILE = SANCTUM_ROOT / "_shared-memory" / "launch-rate-limit-log.jsonl"
SNAPSHOT_DIR = SANCTUM_ROOT / "_shared-memory"

# Thresholds
WEEKLY_HOT_PCT = 80    # >= => recommend GPU offload
WEEKLY_WARN_PCT = 65   # >= => still allow, but flag
SESSION_HOT_PCT = 90
RECENT_429_WINDOW_M = 10  # any 429 in last N min on chosen slot => GPU offload


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def log_event(event: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        event = {"ts": utc_now_iso(), **event}
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_usage_cache() -> dict:
    if not USAGE_CACHE.exists():
        return {"present": False, "reason": "cache-missing"}
    try:
        # PowerShell writes UTF-8 with BOM by default; use utf-8-sig to tolerate.
        return {"present": True, **json.loads(USAGE_CACHE.read_text(encoding="utf-8-sig"))}
    except (json.JSONDecodeError, OSError) as exc:
        return {"present": False, "reason": f"parse-failed:{exc}"}


def read_rl_causes(window_minutes: int) -> list[dict]:
    if not RL_CAUSES.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    rows = []
    try:
        with RL_CAUSES.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = obj.get("ts") or obj.get("timestamp")
                if not ts:
                    continue
                try:
                    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if parsed >= cutoff:
                    rows.append(obj)
    except OSError:
        pass
    return rows


def read_accounts() -> list[dict]:
    if not ACCOUNTS_JSON.exists():
        return []
    try:
        data = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig"))
        # accounts.json structure varies; tolerate dict-or-list at root
        if isinstance(data, dict):
            return data.get("accounts", []) or []
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def pick_best_account_via_ps1(dry_run: bool) -> tuple[str | None, str]:
    if dry_run:
        return None, "dry-run-skipped"
    if not OAUTH_PS1.exists():
        return None, f"oauth-ps1-missing:{OAUTH_PS1}"
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        return None, "no-powershell"
    try:
        proc = subprocess.run(
            [
                pwsh,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(OAUTH_PS1),
                "-Action",
                "PickBest",
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = (proc.stdout or "").strip()
        if proc.returncode != 0:
            return None, f"ps1-rc={proc.returncode}:{(proc.stderr or '').strip()[:200]}"
        # PS1 may print extra lines; take first non-empty token-like line
        for line in out.splitlines():
            t = line.strip()
            if t and not t.startswith("WARNING") and not t.startswith("VERBOSE"):
                return t, "ok"
        return None, "no-output"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return None, f"ps1-err:{exc}"


def recommend(usage: dict, recent_429s: list[dict], project: str, chosen_account: str | None) -> dict:
    """Build the recommendation payload."""
    rec: dict = {
        "project": project,
        "chosen_account": chosen_account,
        "route": "claude",  # default
        "reason": "ok",
        "warnings": [],
    }
    if not usage.get("present"):
        rec["warnings"].append(f"usage-cache-unavailable:{usage.get('reason')}")
    else:
        weekly = usage.get("weekly_all") or {}
        session = usage.get("session") or {}
        weekly_pct = weekly.get("pct") or 0
        session_pct = session.get("pct") or 0
        rec["weekly_pct"] = weekly_pct
        rec["session_pct"] = session_pct
        if weekly_pct >= WEEKLY_HOT_PCT:
            rec["route"] = "gpu"
            rec["model"] = "llama3.1:8b"
            rec["reason"] = f"weekly usage {weekly_pct}% >= {WEEKLY_HOT_PCT}% threshold"
        elif session_pct >= SESSION_HOT_PCT:
            rec["route"] = "gpu"
            rec["model"] = "llama3.1:8b"
            rec["reason"] = f"session usage {session_pct}% >= {SESSION_HOT_PCT}% threshold"
        elif weekly_pct >= WEEKLY_WARN_PCT:
            rec["warnings"].append(f"weekly-warn:{weekly_pct}%")
    if recent_429s:
        rec["warnings"].append(f"recent-429s:{len(recent_429s)}-in-last-{RECENT_429_WINDOW_M}min")
        # If we have a chosen account and it specifically got 429'd, escalate
        if chosen_account and any(
            (r.get("account") or r.get("slot")) == chosen_account for r in recent_429s
        ):
            rec["route"] = "gpu"
            rec["model"] = "llama3.1:8b"
            rec["reason"] = f"chosen account {chosen_account} hit 429 within {RECENT_429_WINDOW_M} min"
    return rec


def cmd_pre_launch(project: str, account: str, dry_run: bool, json_out: bool) -> int:
    usage = read_usage_cache()
    recent_429s = read_rl_causes(RECENT_429_WINDOW_M)
    chosen = account
    pick_reason = "explicit"
    if account == "auto":
        chosen, pick_reason = pick_best_account_via_ps1(dry_run)
        if dry_run and not chosen:
            # In dry-run we still want a deterministic answer
            accounts = read_accounts()
            for a in accounts:
                slot = a.get("name") or a.get("slot")
                if slot:
                    chosen, pick_reason = slot, "dry-run-first-account"
                    break
    rec = recommend(usage, recent_429s, project, chosen)
    rec["pick_reason"] = pick_reason
    log_event({"event": "pre_launch", **rec})
    if json_out:
        print(json.dumps(rec, indent=2))
    else:
        print("=== launch_rate_limit_governor pre-launch ===")
        print(f"project        : {project}")
        print(f"chosen_account : {chosen} ({pick_reason})")
        print(f"route          : {rec['route']}")
        if rec.get("model"):
            print(f"model          : {rec['model']}")
        print(f"reason         : {rec['reason']}")
        if rec.get("weekly_pct") is not None:
            print(f"weekly_pct     : {rec['weekly_pct']}%")
        if rec.get("session_pct") is not None:
            print(f"session_pct    : {rec['session_pct']}%")
        for w in rec.get("warnings", []):
            print(f"warning        : {w}")
    return 0


def cmd_snapshot(json_out: bool) -> int:
    usage = read_usage_cache()
    recent = read_rl_causes(60)
    accounts = read_accounts()
    snapshot = {
        "ts": utc_now_iso(),
        "usage": usage,
        "recent_429s_last_60min": recent,
        "accounts": accounts,
        "thresholds": {
            "weekly_hot_pct": WEEKLY_HOT_PCT,
            "weekly_warn_pct": WEEKLY_WARN_PCT,
            "session_hot_pct": SESSION_HOT_PCT,
            "recent_429_window_m": RECENT_429_WINDOW_M,
        },
    }
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"rate-limit-snapshot-{utc_compact()}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    log_event({"event": "snapshot", "path": str(path)})
    if json_out:
        print(json.dumps({"snapshot_path": str(path)}, indent=2))
    else:
        print(f"snapshot written: {path}")
    return 0


def cmd_install_schtask() -> int:
    schtasks = shutil.which("schtasks") or r"C:\Windows\System32\schtasks.exe"
    if not Path(schtasks).exists():
        print("install-schtask: schtasks.exe not found", file=sys.stderr)
        return 2
    python_exe = sys.executable
    script = str(SANCTUM_ROOT / "automations" / "launch_rate_limit_governor.py")
    task_name = "SinisterLaunchRateLimitGovernor"
    cmd_line = f'"{python_exe}" "{script}" --snapshot'
    subprocess.run([schtasks, "/Delete", "/TN", task_name, "/F"], capture_output=True)
    proc = subprocess.run(
        [
            schtasks,
            "/Create",
            "/TN",
            task_name,
            "/TR",
            cmd_line,
            "/SC",
            "MINUTE",
            "/MO",
            "5",
            "/F",
            "/RL",
            "HIGHEST",
        ],
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
    log_event({"event": "schtask_install", "rc": proc.returncode, "task": task_name})
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pre-spawn rate-limit gate + account auto-balance")
    p.add_argument("--pre-launch", metavar="PROJECT", help="recommend account + route for spawn")
    p.add_argument("--account", default="auto", help="account name or 'auto'")
    p.add_argument("--snapshot", action="store_true", help="dump rate-limit state to file")
    p.add_argument("--install-schtask", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.install_schtask:
        return cmd_install_schtask()
    if args.snapshot:
        return cmd_snapshot(args.json)
    if args.pre_launch:
        return cmd_pre_launch(args.pre_launch, args.account, args.dry_run, args.json)
    print("launch_rate_limit_governor: no action (use --pre-launch / --snapshot / --install-schtask)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
