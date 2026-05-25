# register-brain-broadcast-task.ps1 - register SinisterBrainBroadcast schtask
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T23:58Z:
#   "make sure all agents have the memory updates as we grow on it daily and it auto updates."
#
# Registers a 10-minute schtask that ticks brain-broadcast.ps1 -Action Broadcast.
# Idempotent — if the task already exists, we leave it alone (skip re-registration)
# unless -Force is passed. Composes with the existing register-fleet-autostart-task /
# install-auto-push-task convention (same Action+Trigger+Settings+Principal shape).

[CmdletBinding()]
param(
    [string]$TaskName     = 'SinisterBrainBroadcast',
    [string]$ScriptPath   = 'D:\Sinister Sanctum\automations\brain-broadcast.ps1',
    [int]$IntervalMinutes = 10,
    [int]$WindowHours     = 24,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found at $ScriptPath"
    exit 1
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing -and -not $Force) {
    Write-Host "Task $TaskName already registered (state: $($existing.State)). Use -Force to re-register."
    Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo | Format-List TaskName,LastRunTime,NextRunTime,LastTaskResult
    exit 0
}
if ($existing -and $Force) {
    Write-Host "Removing existing task $TaskName (-Force)"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$argString = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Action Broadcast -WindowHours $WindowHours"
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argString

# Start 2 min from now so an immediate first-tick can verify the wiring.
$startAt = (Get-Date).AddMinutes(2)
$trigger = New-ScheduledTaskTrigger -Once -At $startAt `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 8) `
    -RestartCount 0

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Sinister Brain Broadcast daemon: every 10 min, scan _shared-memory/knowledge/ for new or updated doctrines and push fleet-update rows so all live agents pick up brain changes on their next poll. Author: RKOJ-ELENO 2026-05-24.' | Out-Null

Write-Host ""
Write-Host "Registered $TaskName."
Write-Host "  Script:   $ScriptPath"
Write-Host "  Interval: every $IntervalMinutes minutes"
Write-Host "  First run: $($startAt.ToString('yyyy-MM-dd HH:mm:ss')) local"
Write-Host ""
Write-Host "Verify with:"
Write-Host "  Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
Write-Host "  Start-ScheduledTask -TaskName $TaskName     # fire immediately"
