# Sinister Sanctum :: sanctum-backup :: state + path resolution
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Backup-root path resolver + on-disk catalog helpers.

Environment variables (read at call time, not import):
    SANCTUM_BACKUP_ROOT   - destination root for backup snapshots
                            (default: D:/sinister-sanctum-backups/)
    SANCTUM_ROOT          - source path (Sanctum workstation root)
                            (default: D:/Sinister Sanctum/)
"""
from __future__ import annotations

import datetime
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BACKUP_ROOT = Path("D:/sinister-sanctum-backups")
DEFAULT_SANCTUM_ROOT = Path("D:/Sinister Sanctum")
DATE_FMT = "%Y-%m-%d"
MANIFEST_NAME = "_BACKUP-MANIFEST.md"


def backup_root() -> Path:
    """Return the on-disk root that holds dated snapshot directories."""
    return Path(os.environ.get("SANCTUM_BACKUP_ROOT") or DEFAULT_BACKUP_ROOT)


def sanctum_root() -> Path:
    """Return the source Sinister Sanctum workstation root."""
    return Path(os.environ.get("SANCTUM_ROOT") or DEFAULT_SANCTUM_ROOT)


def snapshot_dir(date: datetime.date | str, *, root: Path | None = None) -> Path:
    """Path for a snapshot keyed by date (YYYY-MM-DD)."""
    if isinstance(date, datetime.date):
        date = date.strftime(DATE_FMT)
    root = root if root is not None else backup_root()
    return root / date


@dataclass
class BackupRecord:
    date: str
    path: Path
    size_bytes: int
    file_count: int
    has_manifest: bool

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
            "has_manifest": self.has_manifest,
        }


def list_backups(root: Path | None = None) -> list[BackupRecord]:
    """Enumerate backup snapshot directories under `root`, newest first."""
    root = root if root is not None else backup_root()
    if not root.exists() or not root.is_dir():
        return []
    out: list[BackupRecord] = []
    for child in sorted(root.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        try:
            datetime.datetime.strptime(child.name, DATE_FMT)
        except ValueError:
            continue
        size, count = _quick_stats(child)
        out.append(
            BackupRecord(
                date=child.name,
                path=child,
                size_bytes=size,
                file_count=count,
                has_manifest=(child / MANIFEST_NAME).exists(),
            )
        )
    return out


def _quick_stats(path: Path) -> tuple[int, int]:
    """Return (size_bytes, file_count) for a directory; tolerant of errors."""
    size = 0
    count = 0
    try:
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    size += p.stat().st_size
                    count += 1
            except OSError:
                continue
    except OSError:
        pass
    return size, count


def prune_backups(
    *,
    keep: int = 7,
    root: Path | None = None,
    dry_run: bool = False,
) -> list[BackupRecord]:
    """Delete oldest snapshots beyond `keep`. Returns the removed records.

    Snapshots are ordered newest-first by date filename; the first `keep`
    survive; the rest are removed (or just reported if `dry_run`).
    """
    records = list_backups(root)
    if len(records) <= keep:
        return []
    victims = records[keep:]
    if dry_run:
        return victims
    for rec in victims:
        try:
            shutil.rmtree(rec.path, ignore_errors=True)
        except OSError:
            continue
    return victims


def humanize_bytes(n: int) -> str:
    """Compact human-readable byte count (no third-party deps)."""
    if n < 0:
        return f"-{humanize_bytes(-n)}"
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024
        i += 1
    return f"{f:.1f} {units[i]}" if i else f"{int(f)} {units[i]}"
