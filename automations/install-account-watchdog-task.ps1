# RKOJ-ELENO :: 2026-05-23
# install-account-watchdog-task.ps1
#
# Registers the `SinisterAccountWatchdog` scheduled task that runs every 5 min
# to clear expired rate-limit markers + auto-resume the fleet when accounts
# become available again. Phase 3 of the multi-account rotation system.
#
# Operator must run ONCE (with admin rights for system-scope task; user-scope
# also works if -RunAsSystem is omitted). Idempotent: re-running just refreshes
# the registration.
#
# Usage (PowerShell from admin or normal shell):
#   powershell -NoProfile -ExecutionPolicy Bypass -File `
#     "D:\Sinister Sanctum\automations\install-account-watchdog-task.ps1"
#
# Verify:
#   Get-ScheduledTask -TaskName SinisterAccountWatchdog
#   Get-ScheduledTaskInfo -TaskName SinisterAccountWatchdog

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterAccountWatchdog',
    [string]$SanctumRoot = $null,
    [int]$IntervalMinutes = 5
)

$ErrorActionPreference = 'Stop'

if (-not $SanctumRoot) {
    $SanctumRoot = Split-Path -Parent $PSScriptRoot
    if (-not $SanctumRoot -or -not (Test-Path $SanctumRoot)) {
        $SanctumRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
    }
}

$WatchdogScript = Join-Path $SanctumRoot 'automations\claude-account-watchdog.ps1'
if (-not (Test-Path $WatchdogScript)) {
    Write-Error "watchdog script not found at $WatchdogScript - install aborted"
    exit 1
}

Write-Host "[install-account-watchdog-task]"
Write-Host "  task name : $TaskName"
Write-Host "  watchdog  : $WatchdogScript"
Write-Host "  interval  : every $IntervalMinutes min"
Write-Host ''

# Build action: PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File <watchdog>
$action = New-ScheduledTaskAction `
    -Execute 'PowerShell.exe' `
    -Argument ("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WatchdogScript`"")

# Trigger: every 5 minutes, starting at task creation, indefinite duration
$startBoundary = (Get-Date).AddMinutes(1)
$trigger = New-ScheduledTaskTrigger -Once -At $startBoundary `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))  # ~10 years (effectively forever)

# Settings: hidden, allow on battery, don't stop if user logs off
$settings = New-ScheduledTaskSettingsSet `
    -Hidden `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 4) `
    -RestartCount 0

# Principal: current interactive user, lowest privilege (no admin needed for watchdog)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Register (or refresh) the task
try {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Write-Host "  > task '$TaskName' already exists - unregistering for refresh" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    }
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description 'Sinister Sanctum multi-account rotation watchdog. Clears expired rate-limits + auto-resumes fleet. RKOJ-ELENO :: 2026-05-23.' `
        -ErrorAction Stop | Out-Null

    Write-Host "  [OK] task '$TaskName' registered" -ForegroundColor Green
    Write-Host ''
    Write-Host '  next steps:' -ForegroundColor Cyan
    Write-Host '    Get-ScheduledTaskInfo -TaskName SinisterAccountWatchdog'
    Write-Host '    Start-ScheduledTask    -TaskName SinisterAccountWatchdog   # run once now'
    Write-Host '    Get-Content "D:\Sinister Sanctum\_shared-memory\account-watchdog.log" -Tail 20'
} catch {
    Write-Error "task registration failed: $($_.Exception.Message)"
    exit 2
}
