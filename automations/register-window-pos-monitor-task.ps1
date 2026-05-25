# Author: RKOJ-ELENO :: 2026-05-24
# register-window-pos-monitor-task.ps1
#
# Registers SinisterWindowPosMonitor scheduled task so per-project terminal
# positions get logged every 10 minutes (operator directive 2026-05-24T21:50Z:
# "We need to have the terminal windows or something log their position on
# the pc every 10 minutes or so because I want projects to auto open and
# return to where they were closed from. ... And I need fucking naming and
# coloring to works and have defaults per project selected. Just log that
# too when you log position.").
#
# Idempotent. Re-runnable. Operator must run as themselves (HighestAvailable;
# no admin required since trigger is at-logon for the current user).
#
# Verify after register: schtasks /Query /TN SinisterWindowPosMonitor

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$IntervalMinutes = 10,
    [string]$TaskName = 'SinisterWindowPosMonitor'
)

$ErrorActionPreference = 'Stop'

$monitorScript = Join-Path $SanctumRoot 'automations\window-position-monitor.ps1'
if (-not (Test-Path $monitorScript)) {
    Write-Host "[FAIL] monitor script not found: $monitorScript" -ForegroundColor Red
    exit 2
}

# Build action — every $IntervalMinutes the watcher does one sweep snapshot.
# We use -Action Snapshot (single pass + exit) rather than -Action Watch
# (long-running loop) so the task scheduler owns the cadence, not the script.
#
# schtasks /TR quoting trap: the entire command goes through cmd's parser. We
# need single OUTER quotes for /TR and ESCAPED-BACKSLASH-DOUBLEQUOTES inside
# for paths with spaces. Use \" (cmd escape) inside an outer '...'.
$psExe = 'powershell.exe'
$inner = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \`"$monitorScript\`" -Action Snapshot -SanctumRoot \`"$SanctumRoot\`""
$trArg = "$psExe $inner"

# Delete prior registration (idempotent)
try {
    schtasks /Delete /TN $TaskName /F 2>$null | Out-Null
} catch {}

# Register: schtasks /SC MINUTE /MO N — fires every N minutes starting now.
# (ONLOGON doesn't support /RI repeat-interval, so MINUTE is the right schedule
# for a 10-min poll. The task auto-resumes after reboot/login because Windows
# Task Scheduler persists the schedule across reboots.)
$rc = & schtasks /Create /TN $TaskName /TR $trArg /SC MINUTE /MO $IntervalMinutes /RL LIMITED /F 2>&1

# Verify
$verify = & schtasks /Query /TN $TaskName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] $TaskName registered (every $IntervalMinutes min)" -ForegroundColor Green
    Write-Host ''
    Write-Host $verify
    exit 0
} else {
    Write-Host "[FAIL] could not register task" -ForegroundColor Red
    Write-Host $verify
    exit 1
}
