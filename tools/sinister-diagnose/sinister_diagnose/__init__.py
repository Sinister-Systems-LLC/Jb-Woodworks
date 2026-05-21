# Sinister Sanctum :: sinister-diagnose :: package
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
sinister-diagnose — RKOJ/Sanctum health checker.

Like `npm doctor` or `brew doctor`. Each check is a pure function that returns
a CheckResult dict ({name, status, message, fix_hint}). The CLI composes them
into either a colored Rich report or a machine-readable JSON document.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .checks import (
    ALL_CHECKS,
    CheckResult,
    check_anthropic_sdk,
    check_backups,
    check_branch,
    check_claude_cli,
    check_disk_space,
    check_git_config,
    check_heartbeats,
    check_mcp_servers,
    check_pyinstaller,
    check_python_version,
    check_rkoj_exe,
    check_rust_toolchain,
    check_sanctum_root,
    check_vault_daemon,
    run_all,
)

__all__ = [
    "__version__",
    "ALL_CHECKS",
    "CheckResult",
    "check_anthropic_sdk",
    "check_backups",
    "check_branch",
    "check_claude_cli",
    "check_disk_space",
    "check_git_config",
    "check_heartbeats",
    "check_mcp_servers",
    "check_pyinstaller",
    "check_python_version",
    "check_rkoj_exe",
    "check_rust_toolchain",
    "check_sanctum_root",
    "check_vault_daemon",
    "run_all",
]
