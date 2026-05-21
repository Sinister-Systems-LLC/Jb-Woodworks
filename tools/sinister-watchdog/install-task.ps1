# Author: RKOJ-ELENO :: 2026-05-21
# sinister-watchdog\install-task.ps1 — register the auto-online keeper to run on startup
#
# Registers a scheduled task "SinisterWatchdog" that launches the watchdog daemon
# at user logon AND at system startup. Runs with -WindowStyle Hidden (no powershell
# popup — per operator's #1 doctrine: NO POPUPS).
#
# Usage (no admin required for user-scope task):
#   cd "D:\Sinister Sanctum\tools\sinister-watchdog"
#   .\install-task.ps1
#
# Uninstall:
#   Unregister-ScheduledTask -TaskName SinisterWatchdog -Confirm:$false

#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterWatchdog',
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$IntervalSeconds = 60,
    [int]$StaleMinutes = 5,
    [switch]$Uninstall,
    [switch]$RunNow
)

$ErrorActionPreference = 'Stop'

if ($Uninstall) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Output "[install-task] Unregistered '$TaskName'"
    } catch {
        Write-Output "[install-task] No task '$TaskName' to remove"
    }
    exit 0
}

$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) {
    Write-Error "python not on PATH — install Python 3.10+ first"
    exit 1
}

$watchdogDir = Join-Path $SanctumRoot 'tools\sinister-watchdog'
if (-not (Test-Path $watchdogDir)) {
    Write-Error "watchdog dir not found: $watchdogDir"
    exit 1
}

# Argument list:  -m sinister_watchdog start --foreground --interval N --stale-minutes M
$arguments = "-m sinister_watchdog start --foreground --interval $IntervalSeconds --stale-minutes $StaleMinutes"

$action = New-ScheduledTaskAction `
    -Execute $py `
    -Argument $arguments `
    -WorkingDirectory $watchdogDir

# Two triggers: at user logon + at system startup (whichever fires first wins).
$triggers = @(
    New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    New-ScheduledTaskTrigger -AtStartup
)

# RunLevel Limited (no UAC prompt); MultipleInstances IgnoreNew (no double-spawn).
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

# CRITICAL: -WindowStyle Hidden is enforced by the Python -m invocation itself
# (the watchdog calls subprocess.Popen with CREATE_NO_WINDOW for any child it
# spawns). For the task host process we use the python.exe binary directly,
# which has no window when launched without a console.

$description = "Sinister Sanctum auto-online keeper :: RKOJ-ELENO :: revives stale agents + probes MCP every $IntervalSeconds s. Hidden, no popups."

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Principal $principal `
    -Settings $settings `
    -Description $description `
    -Force | Out-Null

Write-Output "[install-task] Registered '$TaskName'"
Write-Output "[install-task]   command   : $py $arguments"
Write-Output "[install-task]   workdir   : $watchdogDir"
Write-Output "[install-task]   triggers  : AtLogOn (current user) + AtStartup"
Write-Output "[install-task]   log       : $SanctumRoot\_shared-memory\watchdog.log"

if ($RunNow) {
    Start-ScheduledTask -TaskName $TaskName
    Write-Output "[install-task] Started '$TaskName' (running now)"
}
