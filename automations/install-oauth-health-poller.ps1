# install-oauth-health-poller.ps1 -- one-time Windows scheduled task installer
# Author: RKOJ-ELENO :: 2026-05-24
#
# Registers SinisterOAuthHealthPoll: every 5 minutes, runs oauth-health-poller.ps1.
# Idempotent: re-running updates the existing task in place.
# Removable: -Uninstall switch.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$IntervalMinutes = 5,
    [switch]$Uninstall,
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$TaskName = 'SinisterOAuthHealthPoll'
$Poller   = Join-Path $SanctumRoot 'automations\oauth-health-poller.ps1'

function Say { param([string]$M, [string]$C = 'White') if (-not $Quiet) { Write-Host $M -ForegroundColor $C } }

if ($Uninstall) {
    Say "[installer] uninstalling task '$TaskName'..." 'Yellow'
    & schtasks.exe /Delete /TN $TaskName /F 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Say "[installer] OK -- removed." 'Green'; exit 0 }
    Say "[installer] task was not present (exit $LASTEXITCODE)." 'DarkGray'
    exit 0
}

if (-not (Test-Path $Poller)) {
    Say "[installer] FAIL poller not found: $Poller" 'Red'
    exit 2
}

$args = "-NoProfile -ExecutionPolicy Bypass -File `"$Poller`" -Quiet"
$schtaskArgs = @(
    '/Create', '/F',
    '/SC', 'MINUTE',
    '/MO', "$IntervalMinutes",
    '/TN', $TaskName,
    '/TR', "powershell.exe $args",
    '/RL', 'LIMITED'
)
Say "[installer] registering task '$TaskName' (every $IntervalMinutes min)..." 'Cyan'
$out = & schtasks.exe @schtaskArgs 2>&1
if ($LASTEXITCODE -eq 0) {
    Say "[installer] OK -- task registered." 'Green'
    Say "  Verify with: schtasks /Query /TN $TaskName" 'DarkGray'
    Say "  Trigger now: schtasks /Run   /TN $TaskName" 'DarkGray'
    Say "  Uninstall:   powershell -File $($MyInvocation.MyCommand.Path) -Uninstall" 'DarkGray'
    exit 0
}
Say "[installer] FAIL schtasks exit=$LASTEXITCODE" 'Red'
Say ($out -join "`n") 'DarkGray'
exit 4
