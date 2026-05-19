# install-md-sweep-task.ps1 - one-shot registrar for the md-trash-bin sweep task.
#
# Operator-side only. Run this ONCE, ELEVATED (right-click -> Run as administrator).
# It registers a Windows scheduled task named "SinisterMDSweep" that fires every
# 6 hours at a random minute offset chosen at install time. So a single install
# will fire at e.g. 04:17, 10:17, 16:17, 22:17 every day until you re-install
# or unregister.
#
# To unregister later:
#   Unregister-ScheduledTask -TaskName 'SinisterMDSweep' -Confirm:$false
#
# NOTE: This script is NOT run automatically by the sandbox or by the sweeper.
# It must be executed manually, elevated, by the operator.

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterMDSweep',
    [string]$SweeperPath = 'D:\Sinister Sanctum\automations\sweep-md-trash.ps1',
    [int]$RandomMinute = -1
)

$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'Install MD Sweep Task'

Write-Host ''
Write-Host '  ==============================================' -ForegroundColor Magenta
Write-Host '   INSTALL :: SinisterMDSweep scheduled task' -ForegroundColor White
Write-Host '  ==============================================' -ForegroundColor Magenta
Write-Host ''

# Elevation check.
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host '  [FAIL] Not elevated. Right-click this script and choose "Run as administrator".' -ForegroundColor Red
    Write-Host ''
    exit 2
}

if (-not (Test-Path $SweeperPath)) {
    Write-Host "  [FAIL] sweeper not found at: $SweeperPath" -ForegroundColor Red
    exit 3
}

# Pick a random minute offset (0-59) once at install time. Operator can override
# via -RandomMinute on re-install if they want to dodge a noisy slot.
if ($RandomMinute -lt 0 -or $RandomMinute -gt 59) {
    $RandomMinute = Get-Random -Minimum 0 -Maximum 60
}

# Fire times: 04:XX, 10:XX, 16:XX, 22:XX (every 6h from 04:XX).
# We register four daily triggers at those fixed times rather than a single
# RepetitionInterval, so the offset is stable across reboots.
$mm = $RandomMinute.ToString('00')
$triggerTimes = @("04:$mm", "10:$mm", "16:$mm", "22:$mm")

Write-Host "  [*] sweeper : $SweeperPath" -ForegroundColor DarkGray
Write-Host "  [*] task    : $TaskName"    -ForegroundColor DarkGray
Write-Host "  [*] fires   : $($triggerTimes -join ', ') every day" -ForegroundColor DarkGray
Write-Host ''

# If task already exists, unregister first.
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  [*] task '$TaskName' already exists - re-registering with new offset..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Build the action.
$psExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action = New-ScheduledTaskAction `
    -Execute $psExe `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$SweeperPath`" -Quiet"

# Build four daily triggers.
$triggers = @()
foreach ($t in $triggerTimes) {
    $triggers += New-ScheduledTaskTrigger -Daily -At $t
}

# Run as the current interactive user, so the sweeper can see desktop paths
# and write into D:\Sinister Sanctum\ with the same ACL as manual runs.
$principalCfg = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType S4U `
    -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description 'Sinister Sanctum :: sweep C:\Users\Zonia\Desktop\MD-Trash-Bin\*.md into D:\Sinister Sanctum\library\<topic>\.  Installed by install-md-sweep-task.ps1.' `
    -Action $action `
    -Trigger $triggers `
    -Principal $principalCfg `
    -Settings $settings | Out-Null

Write-Host "  [OK] task '$TaskName' registered." -ForegroundColor Green
Write-Host "       trigger minute offset: :$mm (random)" -ForegroundColor DarkGray
Write-Host ''
Write-Host '  To remove later:' -ForegroundColor DarkGray
Write-Host "    Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor DarkGray
Write-Host ''

exit 0
