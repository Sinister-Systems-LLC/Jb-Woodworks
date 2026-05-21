# Sinister Sanctum :: sinister-diagnose :: checks
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
"""
Each check is a pure function that returns a CheckResult.

CheckResult shape:
    {
        "name":      "<short label, shown left-aligned in the report>",
        "status":    "ok" | "warn" | "fail" | "info",
        "message":   "<one-line summary printed next to the status>",
        "fix_hint":  "<optional remediation hint; printed indented>",
    }

Side-effect rules:
- NEVER raise. Catch and convert to status='fail' + message.
- NEVER mutate environment, files, network state. Read-only probes only.
- subprocess calls use timeout=5 and capture_output to avoid hanging.
- Honor SANCTUM_ROOT / SANCTUM_BACKUPS env vars for testability; fall back to
  the operator-canonical D:\\Sinister Sanctum and D:\\Backups when unset.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

# A CheckResult is just a TypedDict-shaped plain dict for trivial JSON dump.
CheckResult = Dict[str, Any]

_STATUS_OK = "ok"
_STATUS_WARN = "warn"
_STATUS_FAIL = "fail"
_STATUS_INFO = "info"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _ok(name: str, message: str, fix_hint: str = "") -> CheckResult:
    return {"name": name, "status": _STATUS_OK, "message": message, "fix_hint": fix_hint}


def _warn(name: str, message: str, fix_hint: str = "") -> CheckResult:
    return {"name": name, "status": _STATUS_WARN, "message": message, "fix_hint": fix_hint}


def _fail(name: str, message: str, fix_hint: str = "") -> CheckResult:
    return {"name": name, "status": _STATUS_FAIL, "message": message, "fix_hint": fix_hint}


def _info(name: str, message: str, fix_hint: str = "") -> CheckResult:
    return {"name": name, "status": _STATUS_INFO, "message": message, "fix_hint": fix_hint}


def _sanctum_root() -> Path:
    """Operator-canonical Sanctum root (env-overridable for tests)."""
    return Path(os.environ.get("SANCTUM_ROOT", r"D:\Sinister Sanctum"))


def _backups_root() -> Path:
    """Operator-canonical backups root (env-overridable for tests)."""
    return Path(os.environ.get("SANCTUM_BACKUPS", r"D:\Backups"))


def _run_cmd(args: List[str], timeout: float = 5.0) -> subprocess.CompletedProcess | None:
    """Run a subprocess safely. Returns None on FileNotFound / OSError."""
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None


# ---------------------------------------------------------------------------
# the 14 checks
# ---------------------------------------------------------------------------

def check_python_version() -> CheckResult:
    """Python interpreter must be >= 3.11."""
    v = sys.version_info
    label = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= (3, 11):
        return _ok("Python version", label)
    return _fail(
        "Python version",
        f"{label} is below the 3.11 minimum",
        "install Python 3.11+ from python.org and re-run",
    )


def check_pyinstaller() -> CheckResult:
    """PyInstaller must be importable so we can rebuild RKOJ.exe."""
    try:
        import PyInstaller  # type: ignore
        ver = getattr(PyInstaller, "__version__", "?")
        return _ok("PyInstaller", str(ver))
    except ImportError:
        return _fail(
            "PyInstaller",
            "not installed",
            "pip install pyinstaller",
        )


def check_anthropic_sdk() -> CheckResult:
    """anthropic SDK importable + ANTHROPIC_API_KEY present."""
    try:
        import anthropic  # type: ignore
        ver = getattr(anthropic, "__version__", "?")
    except ImportError:
        return _fail(
            "Anthropic SDK",
            "not installed",
            "pip install anthropic",
        )
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return _warn(
            "Anthropic SDK",
            f"installed {ver} but ANTHROPIC_API_KEY not set",
            "set the env var (see docs/ENV-VARIABLES.md)",
        )
    return _ok("Anthropic SDK", f"installed {ver}, key set ({len(key)} chars)")


def check_claude_cli() -> CheckResult:
    """`claude` CLI on PATH or under ~/.local/bin/."""
    p = shutil.which("claude") or shutil.which("claude.exe")
    if p:
        return _ok("Claude CLI", f"found at {p}")
    local = Path.home() / ".local" / "bin" / "claude"
    local_exe = Path.home() / ".local" / "bin" / "claude.exe"
    if local.exists() or local_exe.exists():
        hit = local if local.exists() else local_exe
        return _ok("Claude CLI", f"found at {hit}")
    return _fail(
        "Claude CLI",
        "not on PATH and not in ~/.local/bin/",
        "install via npm i -g @anthropic-ai/claude-code (or see anthropic docs)",
    )


def check_rust_toolchain() -> CheckResult:
    """rustc / cargo on PATH; warn (not fail) if missing — Rust is optional."""
    cp = _run_cmd(["rustc", "--version"])
    if cp is None or cp.returncode != 0:
        return _warn(
            "Rust toolchain",
            "not found",
            "install rustup-init.exe from rustup.rs (optional, only required for sinister-vault / native crates)",
        )
    out = (cp.stdout or "").strip().splitlines()[0] if cp.stdout else "rustc"
    return _ok("Rust toolchain", out)


def check_sanctum_root() -> CheckResult:
    """D:\\Sinister Sanctum\\ exists and has CLAUDE.md."""
    root = _sanctum_root()
    if not root.exists():
        return _fail(
            "Sanctum root",
            f"{root} does not exist",
            "the Sanctum lane is missing; restore from D:\\Backups\\ or git clone",
        )
    claude_md = root / "CLAUDE.md"
    if not claude_md.exists():
        return _fail(
            "Sanctum root",
            f"{root} exists but no CLAUDE.md",
            "CLAUDE.md is the operator-canonical entry-point; check for accidental delete",
        )
    return _ok("Sanctum root", f"{root} OK")


def check_backups() -> CheckResult:
    """D:\\Backups\\ exists, has MANIFEST.md, and at least one dated dir < 7 days old."""
    root = _backups_root()
    if not root.exists():
        return _fail(
            "Backups",
            f"{root} does not exist",
            "register the SinisterSanctumAutoPush / sanctum-backup scheduled task",
        )
    manifest = root / "MANIFEST.md"
    if not manifest.exists():
        return _warn(
            "Backups",
            f"{root} exists but no MANIFEST.md",
            "sanctum-backup should be regenerating MANIFEST.md on each run",
        )
    # Look for recent dated dirs (any dir mtime within 7 days).
    now = time.time()
    seven_days = 7 * 86400
    recent = []
    try:
        for child in root.iterdir():
            if child.is_dir():
                age = now - child.stat().st_mtime
                if age < seven_days:
                    recent.append(child.name)
    except OSError as e:
        return _fail("Backups", f"could not list {root}: {e}")
    if not recent:
        return _warn(
            "Backups",
            f"{root} has MANIFEST.md but no backup dir is < 7 days old",
            "run `sinister sanctum-backup run` or check the scheduled task",
        )
    return _ok("Backups", f"{len(recent)} recent backup dir(s); latest: {sorted(recent)[-1]}")


def check_vault_daemon() -> CheckResult:
    """Probe TCP localhost:5078 — info only (vault is opt-in)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.4)
    try:
        rv = sock.connect_ex(("127.0.0.1", 5078))
    except OSError:
        rv = 1
    finally:
        sock.close()
    if rv == 0:
        return _info("Vault daemon", "listening on :5078")
    return _info(
        "Vault daemon",
        "not listening on :5078",
        "start D:\\sinister-vault\\daemon if you want the vault MCP (optional)",
    )


def check_mcp_servers() -> CheckResult:
    """~/.claude/.mcp.json exists and parses as JSON."""
    mcp = Path.home() / ".claude" / ".mcp.json"
    if not mcp.exists():
        return _warn(
            "MCP servers",
            f"{mcp} does not exist",
            "operator-owned; see tools/sinister-vault/INSTALL-MCP.md for the canonical layout",
        )
    try:
        data = json.loads(mcp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return _fail(
            "MCP servers",
            f"{mcp} exists but is invalid JSON: {e}",
            "operator must repair .mcp.json by hand — one bad edit kills every active session",
        )
    n = len(data.get("mcpServers", {})) if isinstance(data, dict) else 0
    return _ok("MCP servers", f"{mcp} OK, {n} server(s) registered")


def check_git_config() -> CheckResult:
    """git user.name + user.email both set."""
    cp_name = _run_cmd(["git", "config", "--get", "user.name"])
    cp_email = _run_cmd(["git", "config", "--get", "user.email"])
    if cp_name is None or cp_email is None:
        return _fail(
            "Git config",
            "git binary not found",
            "install git from git-scm.com and re-run",
        )
    name = (cp_name.stdout or "").strip()
    email = (cp_email.stdout or "").strip()
    if not name and not email:
        return _fail(
            "Git config",
            "user.name and user.email both unset",
            "git config --global user.name 'RKOJ-ELENO' && git config --global user.email 'andrew.viperrr@gmail.com'",
        )
    if not name:
        return _warn("Git config", f"user.name unset (email: {email})",
                     "git config --global user.name 'RKOJ-ELENO'")
    if not email:
        return _warn("Git config", f"user.email unset (name: {name})",
                     "git config --global user.email 'andrew.viperrr@gmail.com'")
    return _ok("Git config", f"{name} <{email}>")


def check_disk_space() -> CheckResult:
    """D:\\ has >= 50 GB free."""
    drive = os.environ.get("SANCTUM_DRIVE", "D:\\")
    try:
        usage = shutil.disk_usage(drive)
    except (OSError, FileNotFoundError) as e:
        return _fail("Disk space", f"could not stat {drive}: {e}")
    free_gb = usage.free / (1024 ** 3)
    total_gb = usage.total / (1024 ** 3)
    msg = f"{free_gb:.1f} GB free of {total_gb:.1f} GB on {drive}"
    if free_gb < 10:
        return _fail("Disk space", msg, "free up space; sanctum-backup needs headroom")
    if free_gb < 50:
        return _warn("Disk space", msg, "consider freeing space; below 50 GB threshold")
    return _ok("Disk space", msg)


def check_rkoj_exe() -> CheckResult:
    """Desktop has RKOJ.exe, mtime within 7 days."""
    candidates = [
        Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop" / "RKOJ.exe",
        Path.home() / "Desktop" / "RKOJ.exe",
    ]
    rkoj = next((p for p in candidates if p.exists()), None)
    if rkoj is None:
        return _warn(
            "RKOJ.exe",
            "not found on Desktop",
            "build via automations/build/forge-exe/build.ps1 (or grab from D:\\Backups\\)",
        )
    age = time.time() - rkoj.stat().st_mtime
    age_days = age / 86400
    if age_days > 7:
        return _warn(
            "RKOJ.exe",
            f"{rkoj} is {age_days:.1f} days old",
            "rebuild via automations/build/forge-exe/build.ps1",
        )
    return _ok("RKOJ.exe", f"{rkoj} ({age_days:.1f}d old)")


def check_branch() -> CheckResult:
    """Current git branch must start with agent/sinister-sanctum/cli-dispatcher-."""
    cp = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=3.0)
    if cp is None or cp.returncode != 0:
        return _warn(
            "Git branch",
            "not inside a git working tree (or git missing)",
            "cd into the Sanctum repo before running diagnose",
        )
    branch = (cp.stdout or "").strip()
    expected_prefix = "agent/sinister-sanctum/cli-dispatcher-"
    if branch.startswith(expected_prefix):
        return _ok("Git branch", branch)
    return _warn(
        "Git branch",
        f"on `{branch}` (expected prefix `{expected_prefix}`)",
        "switch to the dispatcher branch, or update the diagnose expectation if intentional",
    )


def check_heartbeats() -> CheckResult:
    """All _shared-memory/heartbeats/*.json must be < 24h old."""
    hb_dir = _sanctum_root() / "_shared-memory" / "heartbeats"
    if not hb_dir.exists():
        return _warn(
            "Heartbeats",
            f"{hb_dir} does not exist",
            "no fleet agents have heartbeated yet (or Sanctum lane misconfigured)",
        )
    try:
        files = sorted(hb_dir.glob("*.json"))
    except OSError as e:
        return _fail("Heartbeats", f"could not enumerate {hb_dir}: {e}")
    if not files:
        return _warn("Heartbeats", f"{hb_dir} is empty")
    now = time.time()
    stale = []
    fresh = 0
    for f in files:
        try:
            age = now - f.stat().st_mtime
        except OSError:
            continue
        if age > 24 * 3600:
            stale.append(f.stem)
        else:
            fresh += 1
    if stale:
        return _warn(
            "Heartbeats",
            f"{fresh} fresh, {len(stale)} stale (>24h): {', '.join(stale)}",
            "agents must call sinister-bus.heartbeat every turn (canonical Rule 9)",
        )
    return _ok("Heartbeats", f"{fresh} agent(s) heartbeating within 24h")


# ---------------------------------------------------------------------------
# registry + runner
# ---------------------------------------------------------------------------

# Stable ordering for both `run` output and `<check>` slug lookups.
ALL_CHECKS: Dict[str, Callable[[], CheckResult]] = {
    "python": check_python_version,
    "pyinstaller": check_pyinstaller,
    "anthropic": check_anthropic_sdk,
    "claude-cli": check_claude_cli,
    "rust": check_rust_toolchain,
    "sanctum-root": check_sanctum_root,
    "backups": check_backups,
    "vault": check_vault_daemon,
    "mcp": check_mcp_servers,
    "git-config": check_git_config,
    "disk": check_disk_space,
    "rkoj-exe": check_rkoj_exe,
    "branch": check_branch,
    "heartbeats": check_heartbeats,
}


def run_all() -> List[CheckResult]:
    """Run every check in ALL_CHECKS order and return the result list.

    Any exception inside a check is caught and converted to a fail result
    so the overall run always returns one row per check.
    """
    results: List[CheckResult] = []
    for slug, fn in ALL_CHECKS.items():
        try:
            results.append(fn())
        except Exception as e:  # pragma: no cover - defensive only
            results.append(_fail(slug, f"check raised: {e!r}",
                                 "this is a bug in sinister-diagnose; please report"))
    return results


def overall_status(results: List[CheckResult]) -> str:
    """Reduce a list of check results to one overall status string."""
    if any(r["status"] == _STATUS_FAIL for r in results):
        return _STATUS_FAIL
    if any(r["status"] == _STATUS_WARN for r in results):
        return _STATUS_WARN
    return _STATUS_OK


def now_utc_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
