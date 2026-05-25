#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25 Sub-Q
#
# finalize_oauth_paste_relay.py -- last-mile rescue for sandboxed Claude logins
# whose bash consumer died before the OAuth paste-back code was exchanged.
#
# Context (operator hard-canonical 2026-05-25T03:15Z paste-back wizard from
# iter-21 Sub-G): each "M)anage account -> L)ogin" spawns a mintty sandbox
# with .claude/.oauth-paste-relay.txt as the rendezvous file. The sandbox
# bash polls that file for up to 600s and then runs `claude $LOGIN_CMD` with
# the code on stdin. If the mintty window was closed early OR the operator
# walked away >10 min, the bash dies and the relay file sits there unused.
#
# This script:
#   1. Reads the relay file (--sandbox dir).
#   2. Invokes `claude $LOGIN_CMD` directly (auth login or login) with the
#      code piped to stdin -- same exchange the sandbox bash would have done.
#   3. On success: copies sandbox .credentials.json to per-slot file
#      (~/.claude/credentials.<slot>.json -- NOT touching the operator's
#      main .credentials.json) + appends/updates the slot row in
#      _shared-memory/claude-accounts.json.
#   4. On failure: surfaces the exact failure reason. Caller is expected
#      to file the recovery doc and re-spawn EVE -> M -> Login.
#
# Usage:
#   python automations/finalize_oauth_paste_relay.py \
#       --sandbox C:/Users/Zonia/AppData/Local/Temp/sinister-claude-login-knott-gmail-a1770bfb \
#       --slot knott-gmail [--dry-run] [--label "knott@gmail.com"]
#
# Exit codes:
#   0 = success (creds written, slot upserted)
#   1 = relay file missing/empty (operator never pasted the code)
#   2 = exchange failed (likely code expired or network -- recovery doc fires)
#   3 = missing args / bad sandbox path
#   4 = `claude` CLI not on PATH (Sub-G login wizard pre-flight should catch
#       this; if we hit it here something is very wrong)
"""finalize_oauth_paste_relay.py -- see module docstring (Sub-Q 2026-05-25)."""
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

VERSION = "1.0.0"
SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
HOME = Path(os.environ.get("USERPROFILE") or Path.home())


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_login_cmd() -> list[str] | None:
    """Pick `claude auth login` vs legacy `claude login`. Sub-G's login.sh
    has the same probe -- we mirror it so behavior is identical."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return None
    try:
        r = subprocess.run([claude_bin, "auth", "--help"],
                           capture_output=True, timeout=10)
        if r.returncode == 0:
            return [claude_bin, "auth", "login"]
    except (subprocess.TimeoutExpired, OSError):
        pass
    return [claude_bin, "login"]


def _read_relay(sandbox: Path) -> str | None:
    relay = sandbox / ".claude" / ".oauth-paste-relay.txt"
    if not relay.is_file():
        return None
    try:
        first = relay.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return None
    return first.strip() or None


def _exchange_code(code: str, sandbox: Path, *, dry_run: bool) -> tuple[int, str]:
    """Pipe the code to `claude $LOGIN_CMD` with HOME pointing at the sandbox
    so the resulting .credentials.json lands in the sandbox (NOT the
    operator's real ~/.claude/). Returns (exit_code, stderr_or_status)."""
    login_cmd = _resolve_login_cmd()
    if login_cmd is None:
        return (127, "claude CLI not on PATH")
    if dry_run:
        return (0, f"DRY: would pipe code to {' '.join(login_cmd)} with HOME={sandbox}")
    env = os.environ.copy()
    env["HOME"] = str(sandbox)
    env["USERPROFILE"] = str(sandbox)
    env["CLAUDE_CONFIG_DIR"] = str(sandbox / ".claude")
    (sandbox / ".claude").mkdir(parents=True, exist_ok=True)
    # CLI expects code + blank line so its read loop terminates.
    stdin_payload = f"{code}\n\n"
    try:
        r = subprocess.run(
            login_cmd, input=stdin_payload, text=True,
            env=env, capture_output=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return (124, f"exchange subprocess failed: {exc}")
    msg = (r.stderr or "").strip() or (r.stdout or "").strip()[:300]
    return (r.returncode, msg)


def _copy_creds(sandbox: Path, slot: str, *, dry_run: bool) -> Path | None:
    """Copy sandbox .credentials.json to per-slot file. NEVER touches the
    operator's main ~/.claude/.credentials.json (Sub-Q hard rule)."""
    src = sandbox / ".claude" / ".credentials.json"
    if not src.is_file():
        return None
    dst_dir = HOME / ".claude"
    dst = dst_dir / f"credentials.{slot}.json"
    if dry_run:
        print(f"[finalize] DRY: would copy {src} -> {dst}")
        return dst
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"[finalize] wrote {dst}")
    return dst


def _upsert_account_row(slot: str, label: str, creds_path: Path,
                        *, dry_run: bool) -> bool:
    """Add or update the slot row in claude-accounts.json."""
    if not ACCOUNTS_JSON.is_file():
        print(f"[finalize] WARN: {ACCOUNTS_JSON} missing -- skipping slot upsert")
        return False
    try:
        data = json.loads(ACCOUNTS_JSON.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[finalize] WARN: could not parse accounts file: {exc}")
        return False
    accts = data.get("accounts", []) or []
    found = None
    for a in accts:
        if a.get("name") == slot:
            found = a
            break
    row = {
        "name": slot,
        "label": label or slot,
        "env_key": "ANTHROPIC_API_KEY",
        "credentials_file": str(creds_path),
        "plan_tier": "max",
        "max_sessions_concurrent": 5,
        "current_sessions": 0,
        "rate_limited_until_utc": None,
        "last_429_at_utc": None,
        "successful_spawns_today": 0,
        "fleet_share": 0.5,
        "last_spawn_at_utc": None,
        "enabled": True,
        "linked": True,
        "auth_mode": "oauth",
        "display_name": label or slot,
        "oauth_email": label if "@" in (label or "") else None,
        "quota_resets_at_utc": None,
        "weekly_reset_at_utc": None,
        "added_by": "finalize_oauth_paste_relay",
        "added_at_utc": utc_iso(),
    }
    if found:
        found.update(row)
        action = "updated"
    else:
        accts.append(row)
        data["accounts"] = accts
        action = "added"
    if dry_run:
        print(f"[finalize] DRY: would {action} slot '{slot}' in {ACCOUNTS_JSON.name}")
        return True
    # Atomic write (write to .tmp + rename).
    tmp = ACCOUNTS_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=4), encoding="utf-8")
    tmp.replace(ACCOUNTS_JSON)
    print(f"[finalize] {action} slot '{slot}' in {ACCOUNTS_JSON.name}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Finalize an orphaned OAuth paste-back.")
    ap.add_argument("--sandbox", required=True,
                    help="Sandbox dir (contains .claude/.oauth-paste-relay.txt)")
    ap.add_argument("--slot", required=True,
                    help="Slot name for ~/.claude/credentials.<slot>.json")
    ap.add_argument("--label", default="",
                    help="Human-friendly label (usually the email)")
    ap.add_argument("--dry-run", action="store_true")
    ns = ap.parse_args(argv or sys.argv[1:])

    sandbox = Path(ns.sandbox)
    if not sandbox.is_dir():
        print(f"[finalize] sandbox not found: {sandbox}", file=sys.stderr)
        return 3

    code = _read_relay(sandbox)
    if not code:
        print(f"[finalize] relay missing/empty under {sandbox}/.claude/", file=sys.stderr)
        return 1
    print(f"[finalize] picked up code (len={len(code)}) from relay")

    rc, msg = _exchange_code(code, sandbox, dry_run=ns.dry_run)
    if rc != 0:
        print(f"[finalize] exchange FAILED rc={rc}: {msg}", file=sys.stderr)
        print("[finalize] see deploy/KNOTT-GMAIL-LOGIN-RECOVERY.md for next steps", file=sys.stderr)
        return 2 if rc != 127 else 4

    if ns.dry_run:
        # In dry-run we don't have real creds; report success of the plan.
        print(f"[finalize] DRY OK -- would now copy creds + upsert slot")
        return 0

    creds_path = _copy_creds(sandbox, ns.slot, dry_run=ns.dry_run)
    if creds_path is None:
        print("[finalize] exchange returned 0 but no sandbox creds appeared", file=sys.stderr)
        return 2
    label = ns.label or ns.slot
    _upsert_account_row(ns.slot, label, creds_path, dry_run=ns.dry_run)
    print(f"[finalize] OK -- slot '{ns.slot}' linked at {creds_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
