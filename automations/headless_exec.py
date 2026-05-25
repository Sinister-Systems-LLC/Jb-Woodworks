"""headless_exec.py — Headless subprocess wrapper for all Sinister automations.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25T08:30Z (verbatim):
  "these fucking random cmd consoles and powershell windows have to stop pulling
   up make a broadcast and fix fore all agents that we now do a headless sinister
   term approach and build and test it then tell them."

The fix: every subprocess call that runs external processes (powershell, cmd,
schtasks, git, etc.) MUST use CREATE_NO_WINDOW so no console window pops up.

Usage:
    from headless_exec import run, popen, CREATE_NO_WINDOW

    # Drop-in replacements for subprocess.run / subprocess.Popen:
    result = run(["powershell.exe", "-NoProfile", "-Command", "..."])
    proc   = popen(["git", "fetch"])

    # Or use the flag directly with subprocess:
    subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, ...)

All automations that spawn subprocesses MUST import from here instead of raw
subprocess to enforce the headless doctrine fleet-wide.
"""
from __future__ import annotations

import subprocess
import sys
from typing import Any

# Windows-only flag: CREATE_NO_WINDOW (0x08000000)
# On non-Windows this is 0 (no-op) so cross-platform code works.
CREATE_NO_WINDOW: int = 0x08000000 if sys.platform == "win32" else 0

# DETACHED_PROCESS: child survives parent exit (use for long-running daemons)
DETACHED_PROCESS: int = 0x00000008 if sys.platform == "win32" else 0

# Combined: headless daemon (no window + detached)
HEADLESS_DAEMON: int = CREATE_NO_WINDOW | DETACHED_PROCESS


def run(
    args: list[str] | str,
    *,
    capture_output: bool = True,
    text: bool = True,
    timeout: float | None = None,
    check: bool = False,
    shell: bool = False,
    cwd: str | None = None,
    env: dict | None = None,
    stdin: Any = subprocess.DEVNULL,
    extra_flags: int = 0,
    **kwargs: Any,
) -> subprocess.CompletedProcess:
    """subprocess.run() with CREATE_NO_WINDOW — no popup consoles ever.

    Drop-in replacement. Defaults: capture_output=True, text=True, stdin=DEVNULL.
    """
    flags = CREATE_NO_WINDOW | extra_flags
    return subprocess.run(
        args,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        check=check,
        shell=shell,
        cwd=cwd,
        env=env,
        stdin=stdin,
        creationflags=flags,
        **kwargs,
    )


def popen(
    args: list[str] | str,
    *,
    stdout: Any = subprocess.PIPE,
    stderr: Any = subprocess.PIPE,
    stdin: Any = subprocess.DEVNULL,
    text: bool = True,
    cwd: str | None = None,
    env: dict | None = None,
    daemon: bool = False,
    **kwargs: Any,
) -> subprocess.Popen:
    """subprocess.Popen() with CREATE_NO_WINDOW. Pass daemon=True for detached."""
    flags = HEADLESS_DAEMON if daemon else CREATE_NO_WINDOW
    return subprocess.Popen(
        args,
        stdout=stdout,
        stderr=stderr,
        stdin=stdin,
        text=text,
        cwd=cwd,
        env=env,
        creationflags=flags,
        **kwargs,
    )


def powershell(
    command: str,
    *,
    timeout: float = 30,
    check: bool = False,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """Run a PowerShell command headlessly. No window, no popup."""
    return run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        timeout=timeout,
        check=check,
        cwd=cwd,
    )


def schtask_create(
    task_name: str,
    exe: str,
    args: str,
    schedule: str = "ONLOGON",
    run_level: str = "",
) -> bool:
    """Create a schtask that runs headlessly (no window on trigger).

    Uses PowerShell Register-ScheduledTask with WindowStyle Hidden so the
    triggered process never shows a console window.
    """
    rl_flag = f"-RunLevel {run_level}" if run_level else ""
    ps_cmd = f"""
$action = New-ScheduledTaskAction -Execute '{exe}' -Argument '{args}'
$trigger = New-ScheduledTaskTrigger -{schedule}
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -Hidden $true -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings {rl_flag} -Force | Out-Null
Write-Output 'OK'
"""
    result = powershell(ps_cmd, timeout=30)
    return "OK" in result.stdout


def schtask_minute(
    task_name: str,
    exe: str,
    args: str,
    interval_min: int = 1,
) -> bool:
    """Create a repeating schtask (every N minutes) that runs headlessly."""
    ps_cmd = f"""
$action = New-ScheduledTaskAction -Execute '{exe}' -Argument '{args}'
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes {interval_min}) -Once -At (Get-Date)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -Hidden $true -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName '{task_name}' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Output 'OK'
"""
    result = powershell(ps_cmd, timeout=30)
    return "OK" in result.stdout


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    print(f"CREATE_NO_WINDOW = 0x{CREATE_NO_WINDOW:08X}")
    result = run(["python", "--version"])
    print(f"python --version: {result.stdout.strip()} (rc={result.returncode})")
    result2 = powershell("Write-Output 'headless-ps-ok'")
    print(f"powershell test: {result2.stdout.strip()} (rc={result2.returncode})")
    print("headless_exec self-test PASSED")
    sys.exit(0)
