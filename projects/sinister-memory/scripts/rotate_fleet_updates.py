#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""Rotate _shared-memory/fleet-updates.jsonl when it crosses a size threshold.

Why: iter-4 fleet-update.ps1 broadcast hit System.OutOfMemoryException because
the script does .ToString() on the full file in PowerShell 5.1. The file had
grown to 1.33 GB (~486k rows of mostly-duplicate broadcasts from this
session's flurry of operator directives). PS5.1 max string is 2 GB but
practical OOM hits ~500MB on a 16GB workstation.

This script:
  1. Streams the file row-by-row (zero RAM bloat).
  2. Keeps the last `--keep` rows (default 1000).
  3. Dedupes by `id` field, keeping the newest occurrence.
  4. Writes to `_archive/fleet-updates-<utc>.jsonl` (the full history).
  5. Atomically replaces the live file with the dedup-tail.

Idempotent: if file is already <`--max-mb`, no-op.

Per `automate-everything-no-operator-admin-doctrine-2026-05-25`: no operator
admin needed; runs as plain user.

Schedule recommendation (operator-canonical no-bat-no-ps1): register schtask
via `schtasks.exe /create` calling `pythonw.exe` to run this every 6h
(headless per `headless-runners-doctrine-2026-05-25`).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


def rotate(path: Path, keep: int = 1000, max_mb: int = 100, dry_run: bool = False) -> dict:
    """Rotate `path` if it's larger than `max_mb` megabytes.

    Returns stats: {action, original_bytes, kept_rows, archive_path, new_bytes}.
    """
    path = Path(path)
    if not path.exists():
        return {"action": "missing", "original_bytes": 0, "kept_rows": 0}

    original_bytes = path.stat().st_size
    if original_bytes < max_mb * 1024 * 1024:
        return {
            "action": "skip-under-threshold",
            "original_bytes": original_bytes,
            "threshold_bytes": max_mb * 1024 * 1024,
        }

    # Stream: read whole file once into ring buffer of last `keep` parseable rows
    ring: OrderedDict[str, str] = OrderedDict()  # id -> raw line
    skipped_unparseable = 0
    seen = 0
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for raw in f:
            seen += 1
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped_unparseable += 1
                continue
            rid = str(obj.get("id") or obj.get("ts_utc") or seen)
            # Dedupe: move-to-end on re-occurrence so newest wins
            ring[rid] = line
            ring.move_to_end(rid, last=True)
            if len(ring) > keep:
                ring.popitem(last=False)

    if dry_run:
        return {
            "action": "dry-run",
            "original_bytes": original_bytes,
            "would_keep_rows": len(ring),
            "scanned_rows": seen,
            "skipped_unparseable": skipped_unparseable,
        }

    # Archive the original
    archive_dir = path.parent / "_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    archive_path = archive_dir / f"{path.stem}-{ts}-pre-rotate{path.suffix}"

    # Move via os.replace where possible; fall back to rename-then-write-tail
    # (atomic rename only works on same drive; archive is in same dir so OK)
    os.replace(str(path), str(archive_path))

    # Write the dedup-tail to a temp then atomic-rename
    fd, tmp = tempfile.mkstemp(prefix=path.stem + "-", suffix=path.suffix, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for line in ring.values():
                f.write(line + "\n")
        os.replace(tmp, str(path))
    except Exception:
        # If anything went wrong restore the archive back to live so we don't
        # leave the channel broken.
        if os.path.exists(tmp):
            os.unlink(tmp)
        if not path.exists() and archive_path.exists():
            os.replace(str(archive_path), str(path))
        raise

    new_bytes = path.stat().st_size if path.exists() else 0
    return {
        "action": "rotated",
        "original_bytes": original_bytes,
        "archive_path": str(archive_path),
        "kept_rows": len(ring),
        "scanned_rows": seen,
        "skipped_unparseable": skipped_unparseable,
        "new_bytes": new_bytes,
        "ratio": f"{new_bytes/original_bytes:.4f}",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rotate fleet-updates.jsonl when it crosses a size threshold")
    p.add_argument("--path", default=r"D:\Sinister Sanctum\_shared-memory\fleet-updates.jsonl")
    p.add_argument("--keep", type=int, default=1000, help="rows to keep in the live file (default 1000)")
    p.add_argument("--max-mb", type=int, default=100, help="rotate iff file exceeds this MB (default 100)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    stats = rotate(Path(args.path), keep=args.keep, max_mb=args.max_mb, dry_run=args.dry_run)
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
