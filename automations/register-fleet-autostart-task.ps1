# register-fleet-autostart-task.ps1 -- OPERATOR-RUN once from ELEVATED PowerShell
# Author: RKOJ-ELENO :: 2026-05-24
#
# Why elevated: AtLogOn triggers + system-level scheduled tasks require admin.
# This script is the proper-scheduled-task path. A user-level fallback (Startup
# folder .bat) was installed automatically by fleet-autostart-bootstrap (so the
# fleet bringup happens at logon either way) but using this script gives the
# operator visibility/control via Task Scheduler GUI.
#
# Usage (right-click PowerShell -> Run as Administrator):
#   powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\register-fleet-autostart-task.ps1"

[CmdletBinding()]
param(
    [switch]$Unregister,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$TaskName = 'SinisterFleetAutostart'

# Elevation check
$id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$pr = New-Object System.Security.Principal.WindowsPrincipal($id)
if (-not $pr.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERR: This script must be run as Administrator." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as Administrator, then re-run this script."
    exit 1
}

if ($Unregister) {
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Unregistered: $TaskName"
    } catch {
        Write-Host "Not found (already unregistered): $TaskName"
    }
    exit 0
}

$ps1 = Join-Path $SanctumRoot 'automations\fleet-autostart.ps1'
if (-not (Test-Path $ps1)) {
    Write-Host "ERR: missing $ps1" -ForegroundColor Red; exit 1
}

$T = New-ScheduledTaskTrigger -AtLogOn -RandomDelay (New-TimeSpan -Seconds 30)
$A = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $ps1 + '" -Mode Full -Quiet')
$S = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -MultipleInstances IgnoreNew

try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue } catch {}

Register-ScheduledTask -TaskName $TaskName -Trigger $T -Action $A -Settings $S `
    -Description 'Sinister fleet bringup on user logon (waits for Docker, warms 13-bot fleet, sweeps, announces)' `
    -RunLevel Highest | Out-Null

$task = Get-ScheduledTask -TaskName $TaskName
Write-Host ""
Write-Host "OK: $TaskName registered" -ForegroundColor Green
Write-Host ("  State: " + $task.State)
Write-Host ("  Path:  " + $ps1)
Write-Host ""
Write-Host "Test now (without logon): Start-ScheduledTask -TaskName $TaskName"
exit 0
