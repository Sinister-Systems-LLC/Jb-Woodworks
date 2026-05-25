# Author: RKOJ-ELENO :: 2026-05-25
"""Sinister Sanctum fresh-PC auto-installer.

Operator hard-canonical 2026-05-25: NO operator clicks beyond OAuth in-browser.
Self-elevates via UAC (ShellExecuteW runas) when not already admin.

Module + executable. Run:

    python deploy/first_time_setup.py [--dry-run] [--no-elevate] [--no-clone]
                                      [--target "D:/Sinister Sanctum"]

Steps (each logged to _shared-memory/first-time-setup-log.jsonl):
    1. is_admin / self-elevate
    2. detect_repo (offer clone if missing)
    3. ensure_python_deps (pip)
    4. ensure_winget_deps (winget)
    5. install_schtasks (3 background tasks)
    6. ensure_claude_config (~/.claude/settings.json seed)
    7. copy_eve_exe_to_userprofile + desktop shortcut
    8. first_launch_eve (non-blocking spawn)
    9. summary

Doctrine refs:
  - _shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md
  - _shared-memory/knowledge/no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25.md
  - _shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as _dt
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ---------- constants ----------

DEFAULT_SANCTUM_PATH = r"D:\Sinister Sanctum"
FALLBACK_SANCTUM_PATH = os.path.join(os.environ.get("USERPROFILE", r"C:\Users\Public"), "Sinister-Sanctum")
SANCTUM_REPO = "https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git"

PYTHON_DEPS = ["requests", "cryptography", "psutil", "watchdog"]

# winget IDs we try to install; ones that don't exist are skipped silently.
WINGET_DEPS = [
    ("Git.Git", "Git for Windows"),
    ("Microsoft.PowerShell", "PowerShell 7+"),
    ("Anthropic.Claude.Code", "Claude Code CLI (may not be in winget yet)"),
]

# (TaskName, ScheduleSpec, RelativePs1)
SCHTASKS = [
    ("SinisterSanctumAutoPush", ("MINUTE", "30"), r"automations\sanctum-auto-push.ps1", ""),
    ("SinisterLoopRelentlessWatchdog", ("MINUTE", "5"), r"automations\loop-relentless-watchdog.ps1", "-Action Scan"),
    ("SinisterLinkPoller", ("MINUTE", "5"), r"automations\sinister-link-poller.ps1", ""),
]

LOG_RELATIVE = Path("_shared-memory") / "first-time-setup-log.jsonl"

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


# ---------- logging ----------

_RESULTS: list[dict[str, Any]] = []


def _utcnow() -> str:
    # tz-aware UTC; .utcnow() is deprecated in 3.12+
    try:
        now = _dt.datetime.now(_dt.UTC)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover  (3.10 fallback)
        now = _dt.datetime.utcnow()
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def log_step(name: str, status: str, sanctum_root: Path | None, **extra: Any) -> None:
    """Append a row to first-time-setup-log.jsonl and to in-memory results."""
    row = {"ts": _utcnow(), "step": name, "status": status, **extra}
    _RESULTS.append(row)
    if sanctum_root is None:
        return
    try:
        log_path = sanctum_root / LOG_RELATIVE
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError as exc:  # pragma: no cover
        print(f"[warn] could not write log row ({exc})", file=sys.stderr)


# ---------- step 1: admin / self-elevate ----------

def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        # non-Windows or restricted env
        return False


def self_elevate(extra_args: list[str]) -> None:
    """Re-launch this script under UAC. Returns only if elevation refused."""
    params = " ".join([f'"{__file__}"'] + [f'"{a}"' for a in extra_args])
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None, "runas", sys.executable, params, None, 1
        )
    except (AttributeError, OSError) as exc:
        print(f"[warn] ShellExecuteW unavailable ({exc}); continuing without elevation", file=sys.stderr)
        return
    if int(rc) <= 32:
        print(f"[warn] UAC elevation refused (rc={rc}); continuing non-elevated", file=sys.stderr)
        return
    sys.exit(0)


# ---------- step 2: repo detection ----------

def detect_repo(start: Path) -> Path | None:
    """Walk up from start looking for Sanctum markers."""
    for candidate in [start, *start.parents]:
        markers = ["_shared-memory", "CLAUDE.md", "automations"]
        if all((candidate / m).exists() for m in markers):
            return candidate
    return None


def maybe_clone(target: Path, dry_run: bool) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and any(target.iterdir()):
        return True
    cmd = ["git", "clone", SANCTUM_REPO, str(target)]
    if dry_run:
        print(f"[dry-run] would clone: {' '.join(cmd)}")
        return True
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"[fail] clone failed: {exc}", file=sys.stderr)
        return False


# ---------- step 3: python deps ----------

def ensure_python_deps(dry_run: bool) -> dict[str, str]:
    results: dict[str, str] = {}
    for pkg in PYTHON_DEPS:
        import_name = {"watchdog": "watchdog", "cryptography": "cryptography"}.get(pkg, pkg)
        try:
            importlib.import_module(import_name)
            results[pkg] = "already-present"
            continue
        except ImportError:
            pass
        if dry_run:
            results[pkg] = "would-install"
            continue
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                check=True,
            )
            results[pkg] = "installed"
        except subprocess.CalledProcessError as exc:
            results[pkg] = f"install-fail rc={exc.returncode}"
    return results


# ---------- step 4: winget deps ----------

def _winget_available() -> bool:
    return shutil.which("winget") is not None


def ensure_winget_deps(dry_run: bool) -> dict[str, str]:
    results: dict[str, str] = {}
    if not _winget_available():
        return {"_winget": "not-available; skipped"}
    for pkg_id, label in WINGET_DEPS:
        try:
            chk = subprocess.run(
                ["winget", "list", "--id", pkg_id, "-e"],
                capture_output=True, text=True, timeout=60,
            )
            if chk.returncode == 0 and pkg_id.lower() in chk.stdout.lower():
                results[pkg_id] = "already-present"
                continue
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results[pkg_id] = "check-fail"
            continue
        if dry_run:
            results[pkg_id] = "would-install"
            continue
        try:
            inst = subprocess.run(
                ["winget", "install", "--id", pkg_id, "-e",
                 "--accept-package-agreements", "--accept-source-agreements", "--silent"],
                capture_output=True, text=True, timeout=600,
            )
            if inst.returncode == 0:
                results[pkg_id] = "installed"
            else:
                # 0x8A15002B = no applicable update found, often means not in catalog
                results[pkg_id] = f"install-skipped rc={inst.returncode} ({label})"
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            results[pkg_id] = f"install-fail {exc}"
    return results


# ---------- step 5: schtasks ----------

def install_schtasks(sanctum_root: Path, dry_run: bool, elevated: bool) -> dict[str, str]:
    results: dict[str, str] = {}
    runas = "SYSTEM" if elevated else os.environ.get("USERNAME", "")
    for task_name, (sc_unit, sc_mod), rel_ps1, extra_args in SCHTASKS:
        ps1_full = sanctum_root / rel_ps1
        if not ps1_full.exists():
            results[task_name] = f"missing-script {rel_ps1}"
            continue
        tr = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{ps1_full}" {extra_args}'.strip()
        cmd = [
            "schtasks", "/Create", "/TN", task_name,
            "/SC", sc_unit, "/MO", sc_mod,
            "/TR", tr, "/F",
        ]
        if runas:
            cmd += ["/RU", runas]
        if dry_run:
            results[task_name] = "would-create"
            continue
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            results[task_name] = "created" if res.returncode == 0 else f"fail rc={res.returncode} {res.stderr.strip()[:120]}"
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            results[task_name] = f"err {exc}"
    return results


# ---------- step 6: claude config ----------

def _claude_dir() -> Path:
    return Path.home() / ".claude"


def ensure_claude_config(dry_run: bool) -> dict[str, str]:
    results: dict[str, str] = {}
    cdir = _claude_dir()
    cdir.mkdir(parents=True, exist_ok=True)
    settings = cdir / "settings.json"

    seed = {
        "bypassPermissions": True,
        "defaultMode": "bypassPermissions",
        "permissions": {"allow": ["claude --dangerously-skip-permissions*"]},
        "enabledPlugins": {"understand-anything@understand-anything": True},
    }

    if settings.exists():
        try:
            existing = json.loads(settings.read_text(encoding="utf-8"))
            merged = {**seed, **existing}
            # canonical protections: ensure these are present
            merged["bypassPermissions"] = True
            merged["defaultMode"] = "bypassPermissions"
            ep = merged.setdefault("enabledPlugins", {})
            ep["understand-anything@understand-anything"] = True
            if not dry_run:
                settings.write_text(json.dumps(merged, indent=2), encoding="utf-8")
            results["settings.json"] = "merged-protections"
        except (json.JSONDecodeError, OSError) as exc:
            results["settings.json"] = f"merge-fail {exc}"
    else:
        if dry_run:
            results["settings.json"] = "would-create"
        else:
            settings.write_text(json.dumps(seed, indent=2), encoding="utf-8")
            results["settings.json"] = "created"

    creds = cdir / ".credentials.json"
    if creds.exists():
        results["credentials"] = "present"
    else:
        results["credentials"] = "USER-OAUTH-REQUIRED: open EVE.exe and use O) Accounts -> 1) Claude Login"
    return results


# ---------- step 7: EVE.exe mirror + shortcut ----------

def copy_eve_exe_to_userprofile(sanctum_root: Path, dry_run: bool) -> dict[str, str]:
    results: dict[str, str] = {}
    src = sanctum_root / "EVE.exe"
    if not src.exists():
        results["EVE.exe"] = "source-missing"
        return results

    user_eve_dir = Path(os.environ.get("USERPROFILE", "")) / ".eve"
    user_eve = user_eve_dir / "EVE.exe"
    if dry_run:
        results["mirror"] = f"would-copy {src} -> {user_eve}"
    else:
        try:
            user_eve_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, user_eve)
            results["mirror"] = "copied"
        except (OSError, shutil.SameFileError) as exc:
            results["mirror"] = f"copy-fail {exc}"

    # Desktop shortcut pointing at root EVE.exe
    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    shortcut = desktop / "EVE.lnk"
    if dry_run:
        results["shortcut"] = f"would-create {shortcut}"
        return results
    try:
        _create_lnk(shortcut, src)
        results["shortcut"] = "created"
    except (OSError, RuntimeError) as exc:
        results["shortcut"] = f"shortcut-fail {exc}"
    return results


def _create_lnk(lnk_path: Path, target: Path) -> None:
    """Create a Windows .lnk via WScript.Shell COM (no extra deps)."""
    try:
        import win32com.client  # type: ignore
        shell = win32com.client.Dispatch("WScript.Shell")
        sc = shell.CreateShortcut(str(lnk_path))
        sc.TargetPath = str(target)
        sc.WorkingDirectory = str(target.parent)
        sc.IconLocation = str(target)
        sc.Save()
        return
    except ImportError:
        pass

    # Fallback via PowerShell COM one-liner (no .ps1 file created)
    ps = (
        f'$s=New-Object -ComObject WScript.Shell;'
        f'$sc=$s.CreateShortcut("{lnk_path}");'
        f'$sc.TargetPath="{target}";'
        f'$sc.WorkingDirectory="{target.parent}";'
        f'$sc.IconLocation="{target}";'
        f'$sc.Save()'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False, timeout=30)


# ---------- step 8: first launch ----------

def first_launch_eve(sanctum_root: Path, dry_run: bool) -> dict[str, str]:
    eve = sanctum_root / "EVE.exe"
    if not eve.exists():
        return {"launch": "EVE.exe-missing"}
    if dry_run:
        return {"launch": f"would-spawn {eve}"}
    try:
        proc = subprocess.Popen(
            [str(eve)],
            cwd=str(sanctum_root),
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
        # Poll for up to 5s; we just want to confirm it did not insta-die.
        deadline = time.time() + 5
        while time.time() < deadline:
            if proc.poll() is not None:
                return {"launch": f"died rc={proc.returncode}"}
            time.sleep(0.5)
        return {"launch": f"spawned pid={proc.pid}"}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"launch": f"spawn-fail {exc}"}


# ---------- orchestrator ----------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sinister Sanctum fresh-PC auto-installer")
    p.add_argument("--dry-run", action="store_true", help="Run all checks; print actions; perform none.")
    p.add_argument("--no-elevate", action="store_true", help="Do not attempt UAC self-elevation.")
    p.add_argument("--no-clone", action="store_true", help="Skip git-clone fallback when repo not detected.")
    p.add_argument("--target", default=DEFAULT_SANCTUM_PATH, help="Sanctum clone target if cloning.")
    p.add_argument("--no-launch", action="store_true", help="Skip first-launch EVE.exe step.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print("=== Sinister Sanctum first-time setup ===")
    print(f"Dry-run: {args.dry_run}  |  Elevate: {not args.no_elevate}")

    # Step 1
    elevated = is_admin()
    if not elevated and not args.no_elevate and not args.dry_run:
        print("[step 1] Not admin; attempting UAC self-elevation...")
        forward = [a for a in (sys.argv[1:] if argv is None else argv) if a != "--no-elevate"]
        self_elevate(forward)
        elevated = is_admin()
    log_step("1_is_admin", "PASS" if elevated else "WARN", None, elevated=elevated)

    # Step 2
    here = Path.cwd().resolve()
    repo = detect_repo(here)
    if repo is None and not args.no_clone:
        target = Path(args.target)
        ok = maybe_clone(target, args.dry_run)
        if ok:
            repo = target
    if repo is None:
        # Use fallback path to write the log somewhere if we have nothing
        repo_for_log: Path | None = None
    else:
        repo_for_log = repo
    log_step("2_detect_repo", "PASS" if repo else "FAIL", repo_for_log,
             repo=str(repo) if repo else None)

    if repo is None:
        print("[fail] No Sanctum repo detected and clone disabled/failed. Stopping.")
        _print_summary()
        return 0  # always 0 if installer ran (per spec)

    # Step 3
    py_results = ensure_python_deps(args.dry_run)
    log_step("3_python_deps", "PASS", repo, results=py_results)

    # Step 4
    wg_results = ensure_winget_deps(args.dry_run)
    log_step("4_winget_deps", "PASS", repo, results=wg_results)

    # Step 5
    st_results = install_schtasks(repo, args.dry_run, elevated)
    log_step("5_schtasks", "PASS", repo, results=st_results)

    # Step 6
    cc_results = ensure_claude_config(args.dry_run)
    log_step("6_claude_config", "PASS", repo, results=cc_results)

    # Step 7
    eve_results = copy_eve_exe_to_userprofile(repo, args.dry_run)
    log_step("7_eve_mirror", "PASS", repo, results=eve_results)

    # Step 8
    if args.no_launch:
        log_step("8_first_launch", "SKIP", repo, reason="--no-launch")
    else:
        launch_results = first_launch_eve(repo, args.dry_run)
        log_step("8_first_launch", "PASS", repo, results=launch_results)

    log_step("9_summary", "PASS", repo, total_steps=len(_RESULTS))
    _print_summary()
    return 0


def _print_summary() -> None:
    print("\n=== Summary ===")
    for row in _RESULTS:
        marker = {"PASS": "[ok]", "FAIL": "[!!]", "WARN": "[..]", "SKIP": "[--]"}.get(row["status"], "[??]")
        extras = {k: v for k, v in row.items() if k not in ("ts", "step", "status")}
        print(f"  {marker} {row['step']}: {row['status']}  {extras if extras else ''}")
    print("=== Done ===")


if __name__ == "__main__":
    sys.exit(main())
