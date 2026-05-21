# Sinister Sanctum :: sanctum-backup :: package
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""Recurring Sinister Sanctum backup tool.

Programmatic surface:
    from sanctum_backup import run_backup, list_backups, verify_backup, prune_backups
    from sanctum_backup.state import backup_root, sanctum_root
"""

__version__ = "0.1.0"

from .engine import (
    DEFAULT_EXCLUDES,
    BackupResult,
    BackupSummary,
    build_robocopy_cmd,
    compute_dir_stats,
    run_backup,
    verify_backup,
    write_manifest,
)
from .state import (
    backup_root,
    sanctum_root,
    list_backups,
    prune_backups,
)

__all__ = [
    "__version__",
    "DEFAULT_EXCLUDES",
    "BackupResult",
    "BackupSummary",
    "build_robocopy_cmd",
    "compute_dir_stats",
    "run_backup",
    "verify_backup",
    "write_manifest",
    "backup_root",
    "sanctum_root",
    "list_backups",
    "prune_backups",
]
