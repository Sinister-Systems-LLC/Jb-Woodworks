# Author: RKOJ-ELENO :: 2026-05-21
# Purpose: install SinisterSanctumDailyBackup scheduled task (24h cadence)
# Operator 2026-05-21: "backup sanctum every 24 hours".
#
# Run AS ADMINISTRATOR (UAC elevation required for schtasks /Create).
#
# Usage:
#   pwsh "D:\Sinister Sanctum\automations\install-sanctum-daily-task.ps1"
#   pwsh "D:\Sinister Sanctum\automations\install-sanctum-daily-task.ps1" -Time "03:00"
#   pwsh "D:\Sinister Sanctum\automations\install-sanctum-daily-task.ps1" -Uninstall
#
# Verify after install:
#   schtasks /Query /TN SinisterSanctumDailyBackup

[CmdletBinding()]
param(
    [string]$TaskName = "SinisterSanctumDailyBackup",
    [string]$Time     = "03:00",
    [string]$BatPath  = "D:\Sinister Sanctum\Backup-Sanctum.bat",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

function Test-Elevated {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object System.Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Elevated)) {
    Write-Host "[install-sanctum-daily-task] ERROR: must run as Administrator (UAC elevation required)." -ForegroundColor Red
    Write-Host "Re-run from an elevated PowerShell:"
    Write-Host "  pwsh `"$($MyInvocation.MyCommand.Path)`""
    exit 1
}

if ($Uninstall) {
    Write-Host "[install-sanctum-daily-task] Removing $TaskName ..."
    schtasks /Delete /TN $TaskName /F | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[install-sanctum-daily-task] Removed." -ForegroundColor Green
    } else {
        Write-Host "[install-sanctum-daily-task] schtasks /Delete returned $LASTEXITCODE (already absent?)." -ForegroundColor Yellow
    }
    exit 0
}

if (-not (Test-Path $BatPath)) {
    Write-Host "[install-sanctum-daily-task] ERROR: $BatPath not found. Aborting." -ForegroundColor Red
    exit 2
}

# Remove existing task with same name first (idempotent install)
$existing = schtasks /Query /TN $TaskName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[install-sanctum-daily-task] Removing existing $TaskName ..."
    schtasks /Delete /TN $TaskName /F | Out-Null
}

Write-Host "[install-sanctum-daily-task] Registering $TaskName ..."
Write-Host "  Time:      $Time daily"
Write-Host "  Action:    $BatPath"
Write-Host "  RunLevel:  HIGHEST"

# Use cmd.exe /c so the .bat runs with full env + stdout to nul
$action = "cmd.exe /c `"`"$BatPath`"`""

schtasks /Create `
    /TN $TaskName `
    /TR $action `
    /SC DAILY `
    /ST $Time `
    /RL HIGHEST `
    /F

if ($LASTEXITCODE -ne 0) {
    Write-Host "[install-sanctum-daily-task] ERROR: schtasks /Create returned $LASTEXITCODE" -ForegroundColor Red
    exit 3
}

Write-Host ""
Write-Host "[install-sanctum-daily-task] Registered. Verifying ..." -ForegroundColor Green
schtasks /Query /TN $TaskName /FO LIST | Select-String -Pattern "TaskName|Next Run|Status|Schedule"

Write-Host ""
Write-Host "[install-sanctum-daily-task] First run will populate D:\Backups\sanctum-daily\<today>\ at $Time."
Write-Host "[install-sanctum-daily-task] To uninstall: pwsh `"$($MyInvocation.MyCommand.Path)`" -Uninstall"
