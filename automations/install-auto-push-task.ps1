# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# Registers the SinisterSanctumAutoPush scheduled task. Idempotent — re-running
# replaces the existing task. Unblocked per the 2026-05-19 Expanded Authority
# directive (Register-ScheduledTask is now direct-execute legal).

[CmdletBinding()]
param(
    [string]$TaskName     = 'SinisterSanctumAutoPush',
    [string]$ScriptPath   = 'D:\Sinister Sanctum\automations\sanctum-auto-push.ps1',
    [int]$IntervalMinutes = 30
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Script not found at $ScriptPath"
    exit 1
}

# Remove existing task if present (idempotent)
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task $TaskName"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Trigger: start 5 min from now (gives system time to settle after install),
# then repeat every $IntervalMinutes minutes indefinitely.
$startAt = (Get-Date).AddMinutes(5)
$trigger = New-ScheduledTaskTrigger -Once -At $startAt `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 25) `
    -RestartCount 0

# Run as the interactive user only when logged on (keeps SSH key + credential
# helper available without prompting). LogonType Interactive avoids the
# "store password" prompt entirely.
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
    -Description 'Sanctum auto-push daemon: every 30 min, diff working tree + push to origin/main when there is activity. Built by Sinister Sanctum master agent 2026-05-19.' | Out-Null

Write-Host ""
Write-Host "Registered $TaskName."
Write-Host "  Script:   $ScriptPath"
Write-Host "  Interval: every $IntervalMinutes minutes"
Write-Host "  First run: $($startAt.ToString('yyyy-MM-dd HH:mm:ss')) local"
Write-Host ""
Write-Host "Useful follow-ups:"
Write-Host "  Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
Write-Host "  Start-ScheduledTask -TaskName $TaskName     # run immediately"
Write-Host "  Disable-ScheduledTask -TaskName $TaskName   # pause"
Write-Host "  Enable-ScheduledTask -TaskName $TaskName    # resume"
