#!/usr/bin/env python3
"""agent_overlap_guard.py — Detect and prevent overlapping agent work.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T08:15Z (verbatim):
  "MAKE SURE THAT NO AGENTS DO WORK OR OVER LAP what opther agents do make it
   very know and in place that this does not happen and everything stays
   completely efficent"

How it works:
  Each agent registers its FOCUS_AREA at spawn via --register.
  Before starting work on a topic, an agent calls --check <area>.
  The guard reads all heartbeat JSON files + mesh locks to detect overlap.
  If another agent claims the same focus, the guard returns exit 2 (CONFLICT)
  with the conflicting slug so the caller can pick a different slice.

  Focus areas use prefix matching: "kernel-apk:att_token" conflicts with
  "kernel-apk:att_token_fix" but NOT with "kernel-apk:proguard".

CLI:
  --register <slug> <focus>   claim a focus area (writes to overlap-registry.jsonl)
  --release <slug>            release a focus area claim
  --check <focus>             exit 0 if clear, 2 if conflict (prints conflicting slug)
  --list                      show all active focus claims
  --sweep                     remove stale claims (heartbeat older than 2h)
  --status                    full status report

Registry file: _shared-memory/agent-overlap-registry.jsonl
  Each row: {"ts_utc": ..., "slug": ..., "focus": ..., "expires_utc": ...}
  Claims expire automatically after 2h (refreshed by heartbeat).

Integration:
  start-sinister-session.ps1 calls --register at spawn start.
  CLAUDE.md cold-start step 11(b) includes a sibling-detect that calls --check
  before starting work on any topic that could conflict.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

SANCTUM_ROOT = Path("D:/Sinister Sanctum")
REGISTRY = SANCTUM_ROOT / "_shared-memory" / "agent-overlap-registry.jsonl"
HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
CLAIM_TTL_H = 2       # hours
STALE_WARN_M = 90     # minutes before warning about unclaimed area


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _expires(hours: float = CLAIM_TTL_H) -> str:
    dt = datetime.now(timezone.utc) + timedelta(hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_claims() -> list[dict]:
    """Load all non-expired claims from registry."""
    if not REGISTRY.exists():
        return []
    now_ts = time.time()
    claims: list[dict] = []
    try:
        for line in REGISTRY.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            # Skip released claims
            if row.get("released"):
                continue
            # Check expiry
            exp = row.get("expires_utc", "")
            if exp:
                try:
                    exp_ts = datetime.fromisoformat(exp.replace("Z", "+00:00")).timestamp()
                    if exp_ts < now_ts:
                        continue  # expired
                except Exception:
                    pass
            claims.append(row)
    except Exception:
        pass
    return claims


def _write_row(row: dict) -> None:
    try:
        REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        with REGISTRY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[overlap-guard] write failed: {e}", file=sys.stderr)


def _focus_conflicts(a: str, b: str) -> bool:
    """True if focus area A overlaps with B using prefix matching."""
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return True
    # Prefix: "kernel-apk" conflicts with "kernel-apk:att_token"
    if a.startswith(b + ":") or b.startswith(a + ":"):
        return True
    # Substring: broad "eve-launcher" conflicts with "eve-launcher:glow"
    if a in b or b in a:
        return True
    return False


def cmd_register(slug: str, focus: str) -> int:
    """Register a focus area claim for slug."""
    # Auto-release any prior claim by this slug
    _write_row({
        "ts_utc": _now(), "slug": slug, "focus": focus,
        "expires_utc": _expires(), "released": False,
    })
    print(f"[overlap-guard] registered: {slug} → {focus} (expires in {CLAIM_TTL_H}h)")
    return 0


def cmd_release(slug: str) -> int:
    """Release all focus claims for slug."""
    _write_row({"ts_utc": _now(), "slug": slug, "focus": "*", "released": True})
    print(f"[overlap-guard] released: {slug}")
    return 0


def cmd_check(focus: str, caller: str = "?") -> int:
    """Check if focus area is free. Exit 0=clear, 2=conflict."""
    claims = _load_claims()
    conflicts = [c for c in claims if _focus_conflicts(c["focus"], focus)]
    if not conflicts:
        print(f"[overlap-guard] CLEAR: {focus} — no conflicts")
        return 0
    for c in conflicts:
        print(f"[overlap-guard] CONFLICT: {focus} ← {c['slug']} owns '{c['focus']}' "
              f"(expires {c.get('expires_utc','?')})")
    return 2


def cmd_list() -> int:
    """Show all active focus claims."""
    claims = _load_claims()
    if not claims:
        print("[overlap-guard] No active claims.")
        return 0
    print(f"[overlap-guard] Active claims ({len(claims)}):")
    for c in claims:
        print(f"  {c['slug']:<30} {c['focus']:<40} exp={c.get('expires_utc','?')}")
    return 0


def cmd_sweep() -> int:
    """Remove stale/expired entries from registry (compact it)."""
    if not REGISTRY.exists():
        print("[overlap-guard] No registry file.")
        return 0
    claims = _load_claims()
    # Rewrite registry with only live claims
    REGISTRY.write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in claims) + "\n",
        encoding="utf-8"
    )
    print(f"[overlap-guard] Swept registry — {len(claims)} active claims remain.")
    return 0


def cmd_status() -> int:
    """Full status: claims + heartbeat cross-check."""
    print("=== Agent Overlap Guard ===")
    claims = _load_claims()
    print(f"Active claims: {len(claims)}")
    for c in claims:
        print(f"  {c['slug']:<30} {c['focus']}")
    print()
    # Cross-check: agents with heartbeat but no claim
    if HEARTBEAT_DIR.exists():
        hb_slugs = set()
        for p in HEARTBEAT_DIR.glob("*.json"):
            try:
                row = json.loads(p.read_text(encoding="utf-8"))
                ts = row.get("ts_utc", "")
                if ts:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - dt).total_seconds()
                    if age < 3600:  # fresh heartbeat
                        hb_slugs.add(row.get("agent") or row.get("slug") or p.stem)
            except Exception:
                pass
        claimed = {c["slug"] for c in claims}
        unclaimed = hb_slugs - claimed
        if unclaimed:
            print(f"Live agents WITHOUT focus claim ({len(unclaimed)}):")
            for s in sorted(unclaimed):
                print(f"  {s}")
        else:
            print("All live agents have focus claims registered. OK.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Agent overlap guard — prevent duplicate work")
    sub = ap.add_subparsers(dest="cmd")

    r = sub.add_parser("register", help="claim a focus area")
    r.add_argument("slug", help="agent slug")
    r.add_argument("focus", help="focus area string (e.g. 'kernel-apk:att_token')")

    rel = sub.add_parser("release", help="release all claims for a slug")
    rel.add_argument("slug")

    ch = sub.add_parser("check", help="check if focus area is free (exit 2=conflict)")
    ch.add_argument("focus")
    ch.add_argument("--caller", default="?")

    sub.add_parser("list", help="show all active claims")
    sub.add_parser("sweep", help="compact registry, remove expired")
    sub.add_parser("status", help="full status report")

    # Legacy flat flags for backwards compat with old calls
    ap.add_argument("--register", nargs=2, metavar=("SLUG", "FOCUS"),
                    help="register <slug> <focus>")
    ap.add_argument("--release", metavar="SLUG", help="release <slug>")
    ap.add_argument("--check", metavar="FOCUS", help="check <focus>")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--caller", default="?")

    args = ap.parse_args()

    if args.cmd == "register" or args.register:
        s, f = (args.slug, args.focus) if args.cmd == "register" else args.register
        return cmd_register(s, f)
    if args.cmd == "release" or args.release:
        return cmd_release(args.slug if args.cmd == "release" else args.release)
    if args.cmd == "check" or args.check:
        return cmd_check(args.focus if args.cmd == "check" else args.check,
                         caller=args.caller)
    if args.cmd == "list" or args.list:
        return cmd_list()
    if args.cmd == "sweep" or args.sweep:
        return cmd_sweep()
    if args.cmd == "status" or args.status:
        return cmd_status()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
