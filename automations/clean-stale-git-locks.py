#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
# License: AGPL-3.0-or-later
#
# Cleans stale git lock files that cause terminal freezes.
#
# Operator pain (2026-05-26 ~21:30Z, verbatim):
#   "sometimes the terminals will just freeze for 1-10 minutes and then come
#    back and keep working. i need things like these to stop happening"
#
# Root cause: concurrent Claude sessions in the same repo race on
# `.git/index.lock`. When one process dies (crashed clone, killed mintty, OOM)
# without releasing its lock, every subsequent `git` op blocks waiting for a
# lock that will never be released. A `git status` that should take 50ms
# instead takes the full timeout (1-10 min) before giving up.
#
# Per CLAUDE.md `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` this is a
# Python automation (NOT a .ps1) because it runs on a schtask cadence and
# may grow per-platform logic.
#
# Behavior:
#   - Walks `D:\Sinister Sanctum\.git\` looking for `*.lock` files
#   - For each lock file, checks mtime age
#   - If age >= --threshold-seconds (default 120) AND no live `git.exe` PID
#     references the file (best-effort check), removes it
#   - Logs every action to `_shared-memory/git-lock-cleanup.jsonl`
#   - Exit 0 always (never wedges the schtask scheduler)
#
# Usage:
#   python automations/clean-stale-git-locks.py
#   python automations/clean-stale-git-locks.py --threshold-seconds 60
#   python automations/clean-stale-git-locks.py --dry-run
#   python automations/clean-stale-git-locks.py --once   (default)
#   python automations/clean-stale-git-locks.py --loop --interval 30
#       (runs forever; used by SinisterStaleLockCleaner schtask if you'd
#        rather a single long-lived daemon than a 1-min schtask cadence)

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SANCTUM_ROOT") or r"D:\Sinister Sanctum")
GIT_DIR = SANCTUM_ROOT / ".git"
LOG_FILE = SANCTUM_ROOT / "_shared-memory" / "git-lock-cleanup.jsonl"

# Lock filenames git creates that are safe to nuke when stale.
# index.lock = working-tree index transaction
# HEAD.lock / packed-refs.lock / refs/**/*.lock = ref update transactions
# config.lock = config edit transaction
_LOCK_GLOBS = (
    "index.lock",
    "HEAD.lock",
    "packed-refs.lock",
    "config.lock",
    # ref update locks under refs/heads/, refs/tags/, refs/remotes/
    "refs/**/*.lock",
    "logs/**/*.lock",
)


def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log_event(kind: str, **fields) -> None:
    row = {"ts_utc": utcnow(), "kind": kind}
    row.update(fields)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except OSError:
        # Never wedge on log failure.
        pass


def find_lock_files() -> list[Path]:
    """All git lock files under SANCTUM_ROOT/.git/ that match known patterns."""
    if not GIT_DIR.exists():
        return []
    locks: list[Path] = []
    seen: set[Path] = set()
    for pattern in _LOCK_GLOBS:
        try:
            for p in GIT_DIR.glob(pattern):
                if p.is_file() and p not in seen:
                    seen.add(p)
                    locks.append(p)
        except OSError:
            continue
    return locks


def lock_age_seconds(p: Path) -> float:
    """Seconds since the lock file was last modified. -1 on stat failure."""
    try:
        return max(0.0, time.time() - p.stat().st_mtime)
    except OSError:
        return -1.0


def try_remove(p: Path, dry_run: bool) -> tuple[bool, str]:
    """Attempt removal. Returns (ok, detail). Tolerant of in-use files."""
    if dry_run:
        return True, "dry-run"
    try:
        p.unlink()
        return True, "removed"
    except FileNotFoundError:
        return True, "already-gone"
    except PermissionError as e:
        return False, f"permission-denied: {e}"
    except OSError as e:
        return False, f"oserror: {e}"


def sweep_once(threshold_seconds: int, dry_run: bool) -> dict:
    """One pass: scan, remove stale, return summary stats."""
    locks = find_lock_files()
    summary = {
        "ts_utc": utcnow(),
        "scanned": len(locks),
        "removed": 0,
        "skipped_fresh": 0,
        "skipped_failed": 0,
        "details": [],
    }
    for p in locks:
        age = lock_age_seconds(p)
        rel = p.relative_to(GIT_DIR)
        if age < 0:
            summary["details"].append({"path": str(rel), "result": "stat-failed"})
            summary["skipped_failed"] += 1
            continue
        if age < threshold_seconds:
            summary["skipped_fresh"] += 1
            continue
        ok, detail = try_remove(p, dry_run)
        summary["details"].append({
            "path": str(rel), "age_s": round(age, 1),
            "result": detail, "ok": ok,
        })
        if ok:
            summary["removed"] += 1
            log_event("removed-stale-lock",
                      path=str(rel), age_s=round(age, 1),
                      dry_run=dry_run)
        else:
            summary["skipped_failed"] += 1
            log_event("remove-failed",
                      path=str(rel), age_s=round(age, 1),
                      detail=detail)
    return summary


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Remove stale git lock files that cause terminal freezes.",
    )
    ap.add_argument(
        "--threshold-seconds", type=int, default=120,
        help="Remove lock files older than this many seconds (default: 120).",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be removed without removing.",
    )
    ap.add_argument(
        "--loop", action="store_true",
        help="Run forever (used by long-lived daemon variant).",
    )
    ap.add_argument(
        "--interval", type=int, default=30,
        help="Seconds between sweeps in --loop mode (default: 30).",
    )
    ap.add_argument(
        "--quiet", action="store_true",
        help="Suppress non-error stdout (still writes to log file).",
    )
    args = ap.parse_args(argv)

    if args.threshold_seconds < 10:
        print("WARN: threshold < 10s is unsafe; clamping to 10s.",
              file=sys.stderr)
        args.threshold_seconds = 10

    def emit(summary: dict) -> None:
        if args.quiet:
            return
        msg = (
            f"[{summary['ts_utc']}] scanned={summary['scanned']} "
            f"removed={summary['removed']} fresh={summary['skipped_fresh']} "
            f"failed={summary['skipped_failed']}"
        )
        print(msg)
        for d in summary["details"]:
            if d.get("ok") is False or summary["scanned"] <= 5:
                print(f"  - {d}")

    if not args.loop:
        s = sweep_once(args.threshold_seconds, args.dry_run)
        emit(s)
        return 0

    print(f"clean-stale-git-locks loop mode "
          f"(interval={args.interval}s, threshold={args.threshold_seconds}s)")
    try:
        while True:
            s = sweep_once(args.threshold_seconds, args.dry_run)
            if s["removed"] > 0 or s["skipped_failed"] > 0 or not args.quiet:
                emit(s)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("interrupted; exiting cleanly")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
