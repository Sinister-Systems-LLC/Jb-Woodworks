# install-loop-watchdog-task.ps1 — register/unregister SinisterLoopRelentlessWatchdog
# Author: RKOJ-ELENO :: 2026-05-25
#
# Idempotent: if the task already exists, replaces it. -Uninstall removes it.
# Default cadence: every 5 minutes, hidden powershell.exe, runs Scan action.
#
# Why 5 min? Stall-detection thresholds use 3 consecutive ticks (~15 min same
# focus/iter) as the trigger; faster than that is noise, slower lets agents
# rot for half an hour before being poked. 5-min cadence + 3-tick threshold =
# ~15 min worst-case time-to-poke, which matches the LOOP-MODE doctrine's
# "ScheduleWakeup cap 270s" rule (no agent should naturally pause >4.5 min).
#
# Composes with: loop-relentless-watchdog.ps1 (the script this task runs),
# CLAUDE.md operator-canonical 2026-05-25T02:18Z.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$TaskName    = 'SinisterLoopRelentlessWatchdog',
    [int]$IntervalMinutes = 5,
    [switch]$Uninstall,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$WatchdogPs1 = Join-Path $SanctumRoot 'automations\loop-relentless-watchdog.ps1'

if ($Uninstall) {
    if ($DryRun) {
        Write-Output "DRY-RUN: would unregister scheduled task '$TaskName'"
        exit 0
    }
    try {
        schtasks /Query /TN $TaskName 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            schtasks /Delete /TN $TaskName /F | Out-Null
            Write-Output "OK: unregistered $TaskName"
        } else {
            Write-Output "(no task named $TaskName found)"
        }
    } catch {
        Write-Error "uninstall failed: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

if (-not (Test-Path $WatchdogPs1)) {
    Write-Error "watchdog script missing at $WatchdogPs1"
    exit 2
}

$minutes = [Math]::Max(1, [int]$IntervalMinutes)
$tr = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$WatchdogPs1`" -Action Scan -SanctumRoot `"$SanctumRoot`""

if ($DryRun) {
    Write-Output "DRY-RUN: would register $TaskName"
    Write-Output ("  /TR " + $tr)
    Write-Output ("  /SC MINUTE /MO $minutes /RL HIGHEST /F")
    Write-Output ""
    Write-Output "(no changes made)"
    exit 0
}

try {
    schtasks /Query /TN $TaskName 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        schtasks /Delete /TN $TaskName /F | Out-Null
    }
    $createArgs = @(
        '/Create',
        '/TN', $TaskName,
        '/TR', $tr,
        '/SC', 'MINUTE',
        '/MO', $minutes.ToString(),
        '/RL', 'HIGHEST',
        '/F'
    )
    schtasks @createArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "schtasks /Create failed (exit $LASTEXITCODE)"
        exit 1
    }
    Write-Output "OK: registered $TaskName (every $minutes min; hidden powershell.exe)"
    Write-Output ("  uninstall: powershell -File automations\install-loop-watchdog-task.ps1 -Uninstall")
    exit 0
} catch {
    Write-Error "install failed: $($_.Exception.Message)"
    exit 1
}
