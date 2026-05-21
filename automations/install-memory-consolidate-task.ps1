# Sinister Sanctum :: register the nightly memory-consolidate scheduled task
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
# Run: as operator, in an elevated PowerShell.
# Idempotent — re-running updates the existing task without duplicating.

param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Time = '03:30',                       # local time
    [string]$TaskName = 'SinisterMemoryConsolidate'
)

$ErrorActionPreference = 'Stop'

$consolidateScript = Join-Path $SanctumRoot 'automations\memory-consolidate.ps1'
if (-not (Test-Path $consolidateScript)) {
    Write-Host "[install] script not found: $consolidateScript" -ForegroundColor Red
    exit 1
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "[install] removing existing task: $TaskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$consolidateScript`" -SanctumRoot `"$SanctumRoot`" -Quiet"

$trigger = New-ScheduledTaskTrigger -Daily -At $Time

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

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
    -Description 'Sinister Sanctum :: nightly memory consolidation (jcode parity). RKOJ-ELENO 2026-05-21.' | Out-Null

Write-Host "[install] task '$TaskName' registered for daily $Time local." -ForegroundColor Green
Write-Host "[install] check it: Get-ScheduledTask -TaskName $TaskName | Format-List" -ForegroundColor DarkGray
Write-Host "[install] run now: Start-ScheduledTask -TaskName $TaskName" -ForegroundColor DarkGray
