# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: install SinisterDoctorTask (daily 03:30 fleet health check)
#
# Registers a Windows Scheduled Task that runs sinister-doctor.ps1 every day
# at 03:30 local. Writes the HTML report to _shared-memory/sinister-doctor-
# <UTC>.html so operator can review daily fleet status.
#
# Idempotent: re-run to update the task; uses schtasks /Create /F (force overwrite).
# Reversible: schtasks /Delete /TN SinisterDoctorTask /F
#
# Smoke: .\install-sinister-doctor-task.ps1 -DryRun
# Install: .\install-sinister-doctor-task.ps1
# Uninstall: schtasks /Delete /TN SinisterDoctorTask /F

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Time = '03:30',
    [switch]$DryRun
)

$taskName = 'SinisterDoctorTask'
$script = Join-Path $SanctumRoot 'automations\sinister-doctor.ps1'

if (-not (Test-Path $script)) {
    Write-Error "sinister-doctor.ps1 not found at $script"
    exit 2
}

# Build the action command: hidden powershell + -Html mode
$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$script`" -Html"

Write-Host "[install-sinister-doctor-task]"
Write-Host "  task name : $taskName"
Write-Host "  trigger   : daily at $Time"
Write-Host "  action    : $action"
Write-Host "  script    : $script"

if ($DryRun) {
    Write-Host "  [DRY RUN] would run schtasks /Create /F /TN $taskName /SC DAILY /ST $Time /RL HIGHEST /TR '<action>'"
    exit 0
}

# Check if task already exists
$existing = & schtasks /Query /TN $taskName 2>$null
if ($existing -and $LASTEXITCODE -eq 0) {
    Write-Host "  [INFO] task already exists; will overwrite with /F"
}

# Register/overwrite
$cmd = @(
    '/Create', '/F',
    '/TN', $taskName,
    '/SC', 'DAILY',
    '/ST', $Time,
    '/TR', $action
)
$out = & schtasks @cmd 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] SinisterDoctorTask registered" -ForegroundColor Green
    Write-Host "  Verify: schtasks /Query /TN $taskName"
    Write-Host "  Run now: schtasks /Run /TN $taskName"
    Write-Host "  Uninstall: schtasks /Delete /TN $taskName /F"
} else {
    Write-Host "  [FAIL] schtasks returned $LASTEXITCODE" -ForegroundColor Red
    Write-Host "  Output: $out" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Common cause: admin rights needed for /RL HIGHEST. Try without -RL or run from elevated shell." -ForegroundColor Yellow
    exit 2
}
exit 0
