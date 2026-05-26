#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-26
"""
schtask_stagger.py -- spread Sinister* schtask start times across offsets to
prevent the I/O cluster-fire that causes 1-10min "Simmering" freezes.

ROOT CAUSE (per SUB-D diagnostic 2026-05-26):

  17 Sinister* schtasks all fire within the same 5-min window. When SinisterEVE-
  Watchdog + SinisterOAuthHealthPoll + SinisterAccountWatchdog co-fire, the
  resulting concurrent git/forge-memory/heartbeat-fsync hammers D:\\ -> claude.exe
  fsync() on transcript blocks -> "Simmering" stalls until disk queue drains.

  Operator screenshot 2026-05-26 21:30:03Z correlated exactly with one of these
  cluster-fires (all 3 named tasks "Running" at the time of the freeze).

FIX:

  Within each cadence bucket (e.g. all tasks firing every 5 minutes), spread the
  start times evenly. Example: 4 tasks at 5-min cadence -> offset 0:00 / 1:15 /
  2:30 / 3:45 instead of all at 0:00. Disk queue gets time to drain between.

USAGE:

  python automations/schtask_stagger.py --list           # show current schedule
  python automations/schtask_stagger.py --dry-run        # show proposed offsets
  python automations/schtask_stagger.py --apply          # apply via schtasks /Change

SAFETY:

  - --dry-run is DEFAULT.
  - Only modifies tasks whose name starts with "Sinister".
  - Only mutates /ST (start time), never /TR or /SC.
  - Captures pre-state snapshot to _shared-memory/_archive/schtask-snapshots/<utc>.txt
    BEFORE any change.

Doctrine refs:
  - perf-freeze-root-cause-2026-05-24.md
  - fleet-freeze-and-zombie-windows-diagnosis-2026-05-25.md
  - no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md (Python over .ps1)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
SNAPSHOT_DIR = SANCTUM_ROOT / "_shared-memory" / "_archive" / "schtask-snapshots"


def _utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _query_all() -> list[dict]:
    """Run schtasks /Query /FO CSV /V and return list of dicts for Sinister* tasks."""
    try:
        proc = subprocess.run(
            ["schtasks.exe", "/Query", "/FO", "CSV", "/V"],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as exc:
        print(f"[schtask-stagger] FAIL schtasks query: {exc}", file=sys.stderr)
        return []
    if proc.returncode != 0:
        print(f"[schtask-stagger] FAIL schtasks exit={proc.returncode}", file=sys.stderr)
        return []

    lines = proc.stdout.splitlines()
    if not lines:
        return []
    # Header line uses quoted CSV.
    header = [h.strip('"') for h in lines[0].split('","')]
    header[0] = header[0].lstrip('"')
    header[-1] = header[-1].rstrip('"')
    out = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = [c.strip('"') for c in line.split('","')]
        cells[0] = cells[0].lstrip('"')
        cells[-1] = cells[-1].rstrip('"')
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        name = row.get("TaskName", "")
        if "\\Sinister" in name or name.lstrip("\\").startswith("Sinister"):
            out.append(row)
    return out


def _bucket_by_repeat(tasks: list[dict]) -> dict[str, list[dict]]:
    """Group tasks by their `Repeat: Every:` value so we offset within a cadence."""
    buckets: dict[str, list[dict]] = {}
    for t in tasks:
        rep = t.get("Repeat: Every:", "Disabled") or "Disabled"
        buckets.setdefault(rep, []).append(t)
    return buckets


def _propose_offsets(bucket: list[dict], cadence_label: str) -> list[tuple[str, str]]:
    """Compute (task_name, new_HH:MM:SS) for each task in a cadence bucket."""
    n = len(bucket)
    if n <= 1:
        return []
    # Parse cadence label like "0 Hour(s), 5 Minute(s)" -> 5 min.
    m = re.search(r"(\d+)\s*Hour", cadence_label)
    h = int(m.group(1)) if m else 0
    m = re.search(r"(\d+)\s*Minute", cadence_label)
    mi = int(m.group(1)) if m else 0
    total_minutes = h * 60 + mi
    if total_minutes <= 0:
        return []
    # Spread N tasks evenly across the cadence window.
    step_seconds = (total_minutes * 60) // n
    proposals = []
    for i, t in enumerate(bucket):
        offset_s = i * step_seconds
        # Use a base time of 00:00:00 + offset, modulo 24h.
        hh = (offset_s // 3600) % 24
        mm = (offset_s // 60) % 60
        ss = offset_s % 60
        proposals.append((t["TaskName"], f"{hh:02d}:{mm:02d}:{ss:02d}"))
    return proposals


def _save_snapshot(tasks: list[dict]) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    p = SNAPSHOT_DIR / f"sinister-schtasks-{_utc_stamp()}.txt"
    lines = []
    for t in tasks:
        lines.append(f"{t.get('TaskName','')}\tStart={t.get('Start Time','')}\tRepeat={t.get('Repeat: Every:','')}\tStatus={t.get('Status','')}")
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _apply_offset(task_name: str, new_start: str) -> int:
    try:
        proc = subprocess.run(
            ["schtasks.exe", "/Change", "/TN", task_name, "/ST", new_start],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            print(f"[schtask-stagger] FAIL change {task_name}: {proc.stderr.strip()}", file=sys.stderr)
        return proc.returncode
    except Exception as exc:
        print(f"[schtask-stagger] FAIL exception on {task_name}: {exc}", file=sys.stderr)
        return 1


def cmd_list(_args: argparse.Namespace) -> int:
    tasks = _query_all()
    print(f"[schtask-stagger] found {len(tasks)} Sinister* tasks")
    for t in tasks:
        print(f"  {t.get('TaskName',''):60s}  start={t.get('Start Time','?')}  repeat={t.get('Repeat: Every:','?')}")
    return 0


def cmd_dry_run(_args: argparse.Namespace) -> int:
    tasks = _query_all()
    print(f"[schtask-stagger] found {len(tasks)} Sinister* tasks")
    buckets = _bucket_by_repeat(tasks)
    total_changes = 0
    for cadence, bucket in sorted(buckets.items()):
        proposals = _propose_offsets(bucket, cadence)
        if not proposals:
            continue
        print(f"\n[bucket cadence='{cadence}'  ({len(bucket)} tasks)]")
        for name, new_st in proposals:
            print(f"  WOULD-SET  {name:60s}  ST={new_st}")
            total_changes += 1
    print(f"\n[schtask-stagger] total changes proposed: {total_changes}")
    print("  --apply to commit.")
    return 0


def cmd_apply(_args: argparse.Namespace) -> int:
    tasks = _query_all()
    if not tasks:
        return 2
    snap = _save_snapshot(tasks)
    print(f"[schtask-stagger] snapshot -> {snap}")
    buckets = _bucket_by_repeat(tasks)
    applied = 0
    failed = 0
    for cadence, bucket in sorted(buckets.items()):
        for name, new_st in _propose_offsets(bucket, cadence):
            rc = _apply_offset(name, new_st)
            if rc == 0:
                applied += 1
                print(f"  OK    {name}  ST={new_st}")
            else:
                failed += 1
    print(f"\n[schtask-stagger] applied {applied}, failed {failed}")
    return 0 if failed == 0 else 4


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Stagger Sinister* schtask start times to prevent IO cluster-fire")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="list current Sinister* tasks")
    g.add_argument("--dry-run", action="store_true", help="show proposed offsets")
    g.add_argument("--apply", action="store_true", help="apply via schtasks /Change /ST")
    args = p.parse_args(argv)

    if args.list:
        return cmd_list(args)
    if args.dry_run:
        return cmd_dry_run(args)
    if args.apply:
        return cmd_apply(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
