#!/usr/bin/env python3
# Author: RKOJ-ELENO :: 2026-05-25
"""Rotate _shared-memory/PROGRESS/<lane>.md when it crosses a size threshold.

Why: Sinister Kernel APK is 380 KB, Sinister Sanctum is 488 KB, snap-api-quantum
is 200 KB. These all bloat the FTS5 index + slow down agent cold-start
recall + add noise to RRF rankings. Per `_shared-memory/plans/sinister-memory-
master-plan-2026-05-25/plan.md` R4: rotate.

Convention: PROGRESS files are append-newest-at-top markdown with `---`
horizontal-rule separators between iter entries. Keep the top `--keep-kb`
(default 80 KB) live -> recent activity stays instantly recallable. Archive
the rest to `_shared-memory/_archive/PROGRESS/<lane-slug>-<utc>.md`.

Split rules (priority):
  1. Cut at the first `\n---\n` boundary AFTER `keep_kb` bytes (preserves
     entry coherence).
  2. If no separator found in the next 16 KB, fallback to a paragraph
     boundary (`\n\n`).
  3. If still nothing, cut at byte boundary (rare; very-long single entry).

Idempotent: under threshold = no-op.
Atomic-rename safe writes (per `automate-everything-no-operator-admin-doctrine`).

Composes with R11 (`rotate_fleet_updates.py`) — same primitive shape, different
schema. Future iter: extract shared rotation helper into
`sinister_memory.rotate`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def rotate_progress_file(
    path: Path,
    keep_kb: int = 80,
    scan_window_kb: int = 16,
    min_archive_kb: int = 10,
    dry_run: bool = False,
) -> dict:
    """Rotate one PROGRESS file when it exceeds keep_kb. Returns stats dict.

    Iter-24 add: `min_archive_kb` (default 10) -- rotation only fires when the
    archived portion would be at least this size. Prevents pointless rotations
    of files barely over the threshold (e.g. 84KB file with keep_kb=80 -> only
    4KB to archive -> not worth the operation).
    """
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "action": "missing"}

    original_bytes = path.stat().st_size
    keep_bytes = keep_kb * 1024
    scan_bytes = scan_window_kb * 1024
    min_archive_bytes = min_archive_kb * 1024

    if original_bytes <= keep_bytes:
        return {
            "path": str(path),
            "action": "skip-under-threshold",
            "original_bytes": original_bytes,
            "threshold_bytes": keep_bytes,
        }

    # Iter-24: skip if archive would be too small to be worth rotating.
    if original_bytes - keep_bytes < min_archive_bytes:
        return {
            "path": str(path),
            "action": "skip-archive-too-small",
            "original_bytes": original_bytes,
            "threshold_bytes": keep_bytes,
            "min_archive_bytes": min_archive_bytes,
            "would_archive_bytes": original_bytes - keep_bytes,
        }

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"path": str(path), "action": "read-error", "error": str(exc)}

    # Find split point. Iter-23 fix: previous version would land cut near EOF
    # when the last `\n---\n` separator was past keep_bytes + scan_bytes window,
    # giving a no-op rotation (kept ratio = 1.0). Reject any cut that would
    # keep more than 1.25x keep_bytes live -- forces fallback to paragraph or
    # byte boundary so rotation actually shrinks the file.
    # Iter-24 enhancement: try `\n## ` H2 heading FIRST -- PROGRESS files use
    # `## YYYY-MM-DD iter-N --- title` as their iter-entry boundary, which is
    # far more common than `\n---\n` in real fleet data. The 6 oversized files
    # at iter-23 (Sinister Kernel APK / OS / Panel / Sanctum / snap-api-quantum
    # / snap-emu) all lacked `\n---\n` in the search window but have plenty
    # of `\n## ` headings.
    cut = -1
    search_window_end = keep_bytes + scan_bytes
    for needle in ("\n## ", "\n---\n", "\n\n"):
        cut = text.find(needle, keep_bytes, search_window_end)
        if cut != -1 and cut <= int(keep_bytes * 1.25):
            break
        cut = -1
    if cut == -1:
        cut = keep_bytes

    if cut <= 0 or cut >= len(text):
        return {
            "path": str(path),
            "action": "split-point-not-found",
            "original_bytes": original_bytes,
        }

    # Sanity check: rotation must actually reduce live text length meaningfully.
    # Iter-23 contradict-fix: compare cut to len(text), NOT original_bytes,
    # because on Windows text and disk byte counts diverge by ~10% due to
    # CRLF<->LF newline translation in Python's read_text/write_text.
    if cut > int(len(text) * 0.95):
        return {
            "path": str(path),
            "action": "rotation-would-be-noop",
            "original_bytes": original_bytes,
            "text_len": len(text),
            "split_at": cut,
            "note": "no separator found in keep_bytes-to-1.25x text-len window; degenerate split too close to EOF",
        }

    live_part = text[:cut]
    archive_part = text[cut:]

    # Prepend a rotation footer to the live part so readers know the
    # archive exists and how to find it.
    archive_slug = path.stem.replace(" ", "-")
    archive_dir = path.parent.parent / "_archive" / "PROGRESS"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    archive_path = archive_dir / f"{archive_slug}-{ts}.md"

    rotation_footer = (
        f"\n\n---\n\n"
        f"<!-- ROTATED {ts} :: older entries moved to "
        f"`_shared-memory/_archive/PROGRESS/{archive_path.name}` "
        f"by sinister-memory R4. Live size kept at <={keep_kb} KB; "
        f"archive preserves full history. -->\n"
    )

    if dry_run:
        return {
            "path": str(path),
            "action": "dry-run",
            "original_bytes": original_bytes,
            "live_bytes": len(live_part.encode("utf-8")),
            "archive_bytes": len(archive_part.encode("utf-8")),
            "split_at": cut,
            "would_archive_to": str(archive_path),
        }

    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(archive_part, encoding="utf-8")

    # Atomic-rename for live file
    fd, tmp = tempfile.mkstemp(prefix=path.stem + "-", suffix=path.suffix, dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(live_part)
            f.write(rotation_footer)
        os.replace(tmp, str(path))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    return {
        "path": str(path),
        "action": "rotated",
        "original_bytes": original_bytes,
        "new_bytes": path.stat().st_size,
        "archive_path": str(archive_path),
        "archive_bytes": archive_path.stat().st_size,
        "split_at": cut,
        "ratio_kept": f"{path.stat().st_size/original_bytes:.4f}",
    }


def rotate_all(progress_dir: Path, keep_kb: int = 80, dry_run: bool = False) -> list[dict]:
    """Rotate every *.md file in `progress_dir` that exceeds keep_kb."""
    progress_dir = Path(progress_dir)
    if not progress_dir.is_dir():
        return [{"action": "missing-dir", "path": str(progress_dir)}]

    results: list[dict] = []
    for entry in sorted(progress_dir.iterdir()):
        if entry.is_file() and entry.suffix.lower() == ".md":
            results.append(rotate_progress_file(entry, keep_kb=keep_kb, dry_run=dry_run))
    return results


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rotate PROGRESS markdown files larger than --keep-kb")
    p.add_argument("--progress-dir", default=r"D:\Sinister Sanctum\_shared-memory\PROGRESS")
    p.add_argument("--keep-kb", type=int, default=80, help="keep top N KB of newest entries live (default 80)")
    p.add_argument("--path", help="rotate ONLY this one file instead of scanning the dir")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if args.path:
        results = [rotate_progress_file(Path(args.path), keep_kb=args.keep_kb, dry_run=args.dry_run)]
    else:
        results = rotate_all(Path(args.progress_dir), keep_kb=args.keep_kb, dry_run=args.dry_run)

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
