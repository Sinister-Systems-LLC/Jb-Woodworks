# Author: Sinister Kernel APK (Claude agent, 2026-05-21)
# sinister-recovery-watchdog/Install-Task.ps1
#
# Idempotently registers a scheduled task "SinisterRecoveryWatchdog" that runs
# watchdog.ps1 every 60s indefinitely. Safe to re-run; unregisters + re-registers
# cleanly.

#Requires -Version 5.1
#Requires -RunAsAdministrator

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterRecoveryWatchdog',
    [int]$IntervalSeconds = 60
)

$ErrorActionPreference = 'Stop'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchdogPath = Join-Path $scriptRoot 'watchdog.ps1'

if (-not (Test-Path $watchdogPath)) {
    Write-Error "watchdog.ps1 not found at $watchdogPath"
    exit 1
}

# Unregister existing
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Unregistering existing task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Build new
$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$watchdogPath`""

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2)
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Seconds $IntervalSeconds) -RepetitionDuration ([System.TimeSpan]::FromDays(3650))).Repetition

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew

# LogonType Interactive: task runs ONLY while operator's user is logged in.
# Trade-off: if operator logs out or locks/reboots the machine without auto-login,
# the watchdog pauses. Chosen over `S4U` / `Password` to avoid storing credentials.
# For a 24/7 watchdog, switch to `-LogonType ServiceAccount -UserId 'SYSTEM'`
# AFTER verifying adb-as-SYSTEM permissions to the USB devices (often broken on
# Windows 10 without a dedicated service account). Current design is correct for
# the operator-attended workstation use case.
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Polls connected phones for recovery-boot and runaway-error events; emits [ALERT] JSON to _shared-memory/inbox/kernel-apk/. Read-only on phones; append-only on host.'

Write-Host "Registered '$TaskName' - repeating every ${IntervalSeconds}s starting in 2 minutes."
Write-Host "First run output: $scriptRoot\watchdog.log"
Write-Host "Alerts will land in: D:\Sinister Sanctum\_shared-memory\inbox\kernel-apk\"
