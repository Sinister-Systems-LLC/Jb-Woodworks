#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
#
# eve_oauth_reconcile.py -- post-OAuth-wizard reconciler for the EVE.exe Accounts
# tab Login flow.
#
# WHAT THIS FIXES (W3 of plan-v2.md eve-exe-complete-everything-2026-05-26):
#
# Operator 2026-05-25T01:25Z verbatim: "(64) login didn't work fix".
#
# Root cause traced through eve-bulk-oauth-login.log:
#
#   * Every recent live run (03:03Z .. 12:12Z 2026-05-25) logged
#     `wizard end processed=0` -- i.e. CapturedSlots.Count stayed at 0.
#   * Even when OAuth DID complete in mintty and the per-slot creds file
#     landed at ~/.claude/credentials.<slot>.json, the slot row in
#     claude-accounts.json never got `linked: true` because the wizard's
#     _RegisterOAuthSlot helper only writes auth_mode/oauth_email/
#     credentials_file/enabled. The `linked` field (required gate inside
#     _Is-AccountAvailable in claude-accounts.ps1) was silently left absent
#     OR stuck at false, so spawn rotation skipped the freshly logged-in
#     account.
#   * Side effect: a successful sandbox login round was indistinguishable
#     from a failed one in the eve.py UI -- the Accounts page just showed
#     "(no slots processed)" or the slot still as [ON UNLINKED].
#
# THIS SCRIPT (no-bat-no-ps1 doctrine, 2026-05-25):
#   1. Walks every ~/.claude/credentials.*.json on disk.
#   2. For each, applies the same linked-check the .ps1 fleet uses
#      (file readable + claudeAiOauth.accessToken OR api_key OR accessToken
#      present + length >= 16 + not FAKE/PLACEHOLDER/TODO/XXX).
#   3. Patches _shared-memory/claude-accounts.json:
#         - existing slot row -> sets linked = True/False, keeps everything
#           else, re-anchors credentials_file if it pointed at the wrong path
#         - NEW per-slot credentials file (no row yet) -> inserts a minimal
#           slot row so the wizard's bash success path is honored even when
#           the .ps1's _RegisterOAuthSlot bailed (e.g. file race, JSON parse
#           hiccup, or the wizard was killed mid-write).
#   4. Sweeps existing rows whose credentials_file is missing/empty/FAKE and
#      sets linked = False so the rotator skips them.
#   5. Returns a dict + exit code 0 on success, 1 on JSON write failure.
#
# CLI:
#   python automations/eve_oauth_reconcile.py
#       --quiet     suppress per-row output (still prints summary line)
#       --json      machine-readable summary on stdout (one JSON line)
#       --dry-run   compute the new state but do NOT write the file
#
# eve.py invokes this after the wizard returns so the post-Login state is
# correct regardless of which path the wizard took (success / window-closed /
# timeout / wizard-bailed-before-RegisterOAuthSlot).
#
# This file is the canonical "did the login actually take" check. The .ps1
# wizard is left as-is per no-bat-no-ps1 (don't grow .ps1, supplement with
# Python instead).
"""eve_oauth_reconcile.py -- see module docstring."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "_lib"))
from _json_safe import atomic_write_json

VERSION = "1.0.0"
SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")
ACCOUNTS_JSON = SANCTUM_ROOT / "_shared-memory" / "claude-accounts.json"
HOME = Path(os.environ.get("USERPROFILE") or Path.home())
CLAUDE_DIR = HOME / ".claude"

# Placeholder token rejects (mirror Test-AccountLinked in claude-accounts.ps1).
_PLACEHOLDER_RE = re.compile(r"^(FAKE|PLACEHOLDER|TODO|XXX)", re.IGNORECASE)

# credentials.<slot>.json regex; the leaf must yield the slot name.
_PER_SLOT_RE = re.compile(r"^credentials\.([a-z0-9][a-z0-9_-]{0,30})\.json$",
                          re.IGNORECASE)


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_token(creds_path: Path) -> str | None:
    """Mirror Test-AccountLinked from claude-accounts.ps1:
    accept either api_key, claudeAiOauth.accessToken, or top-level accessToken.
    Returns the token string OR None if file unreadable / no token field /
    obvious placeholder / too-short.
    """
    if not creds_path.is_file():
        return None
    try:
        raw = creds_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not raw or not raw.strip():
        return None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    token = None
    if obj.get("api_key"):
        token = str(obj["api_key"])
    else:
        oa = obj.get("claudeAiOauth")
        if isinstance(oa, dict) and oa.get("accessToken"):
            token = str(oa["accessToken"])
        elif obj.get("accessToken"):
            token = str(obj["accessToken"])
    if not token:
        return None
    if len(token) < 16:
        return None
    if token == "FAKE" or _PLACEHOLDER_RE.match(token):
        return None
    return token


def _decode_oauth_email(token: str) -> str | None:
    """Best-effort JWT email decode -- mirrors _DecodeOAuthEmail in .ps1.
    Returns None when token is not a parsable JWT or has no email claim.
    Pure Python (no PyJWT dep).
    """
    parts = token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    # base64url -> base64 + padding
    pad = (-len(payload)) % 4
    if pad:
        payload += "=" * pad
    payload = payload.replace("-", "+").replace("_", "/")
    try:
        import base64
        raw = base64.b64decode(payload)
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        email = data.get("email")
        if isinstance(email, str) and "@" in email:
            return email
    return None


def _scan_per_slot_creds() -> dict[str, Path]:
    """Return {slot_name: creds_path} for every ~/.claude/credentials.*.json."""
    out: dict[str, Path] = {}
    if not CLAUDE_DIR.is_dir():
        return out
    for child in CLAUDE_DIR.iterdir():
        if not child.is_file():
            continue
        m = _PER_SLOT_RE.match(child.name)
        if not m:
            continue
        slot = m.group(1).lower()
        out[slot] = child
    return out


def _empty_slot_row(slot: str, creds_path: Path, email: str | None) -> dict:
    """Schema-v2-compatible minimal row.

    Mirrors _RegisterOAuthSlot in eve-bulk-oauth-login.ps1 but adds the
    `linked` field (which the .ps1 forgot -- that is the W3 bug fix).
    """
    label = f"{email} ({slot})" if email else slot
    return {
        "name": slot,
        "label": label,
        "display_name": email or slot,
        "enabled": True,
        "linked": True,  # the actual fix
        "auth_mode": "oauth",
        "oauth_email": email,
        "credentials_file": str(creds_path),
        "env_key": "ANTHROPIC_API_KEY",
        "current_sessions": 0,
        "max_sessions_concurrent": 5,
        "plan_tier": "max",
        "successful_spawns_today": 0,
        "rate_limited_until_utc": None,
        "last_429_at_utc": None,
        "last_spawn_at_utc": None,
        "quota_resets_at_utc": None,
        "weekly_reset_at_utc": None,
        "fleet_share": 0.0,
    }


def reconcile(*, dry_run: bool = False,
              quiet: bool = False) -> dict:
    """The W3 fix entry-point.

    Returns a summary dict:
        {
          "newly_linked": [slot,...],
          "newly_unlinked": [slot,...],
          "inserted_slots": [slot,...],
          "untouched": [slot,...],
          "wrote_file": bool,
          "accounts_count_before": int,
          "accounts_count_after": int,
        }
    """
    summary: dict = {
        "newly_linked": [],
        "newly_unlinked": [],
        "inserted_slots": [],
        "untouched": [],
        "wrote_file": False,
        "accounts_count_before": 0,
        "accounts_count_after": 0,
    }

    if not ACCOUNTS_JSON.is_file():
        if not quiet:
            print(f"[reconcile] ERR: claude-accounts.json missing at {ACCOUNTS_JSON}",
                  file=sys.stderr)
        return summary

    try:
        # claude-accounts.json may be UTF-8 with BOM (PowerShell ConvertTo-Json
        # writes one by default on Windows PowerShell 5.1). utf-8-sig strips it.
        raw = ACCOUNTS_JSON.read_text(encoding="utf-8-sig")
        cfg = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        if not quiet:
            print(f"[reconcile] ERR: could not read claude-accounts.json: {e}",
                  file=sys.stderr)
        return summary

    if not isinstance(cfg, dict) or "accounts" not in cfg or \
            not isinstance(cfg["accounts"], list):
        if not quiet:
            print("[reconcile] ERR: claude-accounts.json has no .accounts list",
                  file=sys.stderr)
        return summary

    summary["accounts_count_before"] = len(cfg["accounts"])

    # Index existing rows by name + by credentials_file basename.
    # A per-slot creds file is "claimed" if ANY row points its
    # credentials_file at it (regardless of that row's name). This prevents
    # the reconciler from inserting a duplicate row for e.g.
    # credentials.slot3.json when row "operator-b" already maps to it.
    by_name: dict[str, dict] = {}
    claimed_files: set[str] = set()
    for row in cfg["accounts"]:
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("name"), str):
            by_name[row["name"].lower()] = row
        cp = row.get("credentials_file")
        if isinstance(cp, str) and cp:
            # Normalize Windows path comparison: lowercase + forward-slash.
            claimed_files.add(cp.lower().replace("\\", "/"))

    on_disk = _scan_per_slot_creds()  # {slot: path}

    changed = False

    # (1) Update existing rows.
    for name, row in by_name.items():
        cp = row.get("credentials_file")
        token = None
        if cp:
            token = _extract_token(Path(cp))
        # Also consider the per-slot file we'd derive from `name`, in case
        # credentials_file points to a stale/wrong path (operator renamed slot,
        # wizard wrote credentials.<slot>.json but row.credentials_file still
        # points at the old slot3.json etc.).
        if not token and name in on_disk:
            disk_token = _extract_token(on_disk[name])
            if disk_token:
                token = disk_token
                row["credentials_file"] = str(on_disk[name])
                changed = True
        is_linked = token is not None
        was_linked = bool(row.get("linked")) if "linked" in row else None
        if "linked" not in row:
            row["linked"] = is_linked
            changed = True
            if is_linked:
                summary["newly_linked"].append(name)
            else:
                summary["newly_unlinked"].append(name)
        elif was_linked != is_linked:
            row["linked"] = is_linked
            changed = True
            if is_linked:
                summary["newly_linked"].append(name)
            else:
                summary["newly_unlinked"].append(name)
        else:
            summary["untouched"].append(name)
        # Decode email and patch the row if we have a token and the row's
        # oauth_email field is empty (helps the wizard's _RegisterOAuthSlot
        # post-write where JWT decode failed once).
        if token and not row.get("oauth_email"):
            email = _decode_oauth_email(token)
            if email:
                row["oauth_email"] = email
                # Don't clobber a custom label/display_name -- only fill in
                # if currently empty / mirroring the slot name.
                if not row.get("label") or row["label"] == name:
                    row["label"] = f"{email} ({name})"
                if not row.get("display_name") or row["display_name"] == name:
                    row["display_name"] = email
                changed = True

    # (2) Insert rows for per-slot credentials files we found on disk
    # that have no row yet (the "wizard wrote creds but JSON registration
    # failed" path). Skip files already claimed by an existing row's
    # credentials_file pointer even if the row's name differs from the
    # filename (e.g. operator-b -> credentials.slot3.json).
    for slot, path in on_disk.items():
        if slot in by_name:
            continue
        normpath = str(path).lower().replace("\\", "/")
        if normpath in claimed_files:
            continue
        token = _extract_token(path)
        if not token:
            # File exists but it's empty/placeholder -- don't insert.
            continue
        email = _decode_oauth_email(token)
        row = _empty_slot_row(slot, path, email)
        cfg["accounts"].append(row)
        summary["inserted_slots"].append(slot)
        changed = True

    summary["accounts_count_after"] = len(cfg["accounts"])

    if changed and not dry_run:
        try:
            atomic_write_json(ACCOUNTS_JSON, cfg, indent=4)
            summary["wrote_file"] = True
        except OSError as e:
            if not quiet:
                print(f"[reconcile] ERR: write failed: {e}", file=sys.stderr)
            return summary

    if not quiet:
        if summary["newly_linked"]:
            print(f"[reconcile] linked=true now for: "
                  f"{', '.join(summary['newly_linked'])}")
        if summary["newly_unlinked"]:
            print(f"[reconcile] linked=false now for: "
                  f"{', '.join(summary['newly_unlinked'])}")
        if summary["inserted_slots"]:
            print(f"[reconcile] inserted new slot rows: "
                  f"{', '.join(summary['inserted_slots'])}")
        if not (summary["newly_linked"] or summary["newly_unlinked"]
                or summary["inserted_slots"]):
            print("[reconcile] no changes (all slots already correct)")
        print(f"[reconcile] accounts: "
              f"{summary['accounts_count_before']} -> "
              f"{summary['accounts_count_after']}"
              f" {'(WROTE)' if summary['wrote_file'] else '(no write)'}"
              f"{' [dry-run]' if dry_run else ''}")

    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="EVE.exe OAuth post-wizard reconciler "
                    "(linked-field auto-compute)"
    )
    parser.add_argument("--quiet", action="store_true",
                        help="suppress per-row output")
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable summary line")
    parser.add_argument("--dry-run", action="store_true",
                        help="compute new state but do not write")
    args = parser.parse_args(argv)

    summary = reconcile(dry_run=args.dry_run, quiet=args.quiet or args.json)
    if args.json:
        print(json.dumps(summary, separators=(",", ":")))
    # exit 0 if we successfully computed; never raise on no-op.
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
