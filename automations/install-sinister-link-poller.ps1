# install-sinister-link-poller.ps1 - register/unregister SinisterLinkPoll task
# Author: RKOJ-ELENO :: 2026-05-25
#
# Idempotent: if the task already exists, replaces it. -Uninstall removes it.
# Default cadence: every 60s when linked, hidden, no user prompt.
#
# Why every 60s? Operator brief: "Sinister LINK should poll cross-machine
# state infrequently (60s-5min cadences)". 60s is the floor; the poller itself
# exits early when unlinked so the steady-state cost is one process spawn /
# minute that returns in <50ms.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$TaskName    = 'SinisterLinkPoll',
    [int]$IntervalSec    = 60,
    [switch]$Uninstall,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$PollPs1 = Join-Path $SanctumRoot 'automations\sinister-link-poller.ps1'

if ($Uninstall) {
    if ($DryRun) {
        Write-Output "DRY-RUN: would unregister scheduled task '$TaskName'"
        exit 0
    }
    try {
        $existing = schtasks /Query /TN $TaskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            schtasks /Delete /TN $TaskName /F | Out-Null
            Write-Output "OK: unregistered $TaskName"
        } else {
            Write-Output "(no task named $TaskName found)"
        }
    } catch {
        Write-Error "uninstall failed: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

if (-not (Test-Path $PollPs1)) {
    Write-Error "poller script missing at $PollPs1"
    exit 2
}

# Compose the schtasks command. Run every $IntervalSec seconds for 24h then
# the task re-arms next day. -RI is in MINUTES, so for sub-minute polls we
# fall back to a 1-minute floor (Windows Task Scheduler doesn't support
# sub-minute repeating triggers via schtasks /Create).
$minutes = [Math]::Max(1, [int]([Math]::Ceiling($IntervalSec / 60.0)))

$tr = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PollPs1`" -SanctumRoot `"$SanctumRoot`""

if ($DryRun) {
    Write-Output "DRY-RUN: would register $TaskName"
    Write-Output ("  /TR $tr")
    Write-Output ("  /SC MINUTE /MO $minutes /RL HIGHEST /F")
    exit 0
}

try {
    # Remove existing first for clean replace
    schtasks /Query /TN $TaskName 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        schtasks /Delete /TN $TaskName /F | Out-Null
    }
    $createArgs = @(
        '/Create',
        '/TN', $TaskName,
        '/TR', $tr,
        '/SC', 'MINUTE',
        '/MO', $minutes.ToString(),
        '/RL', 'HIGHEST',
        '/F'
    )
    schtasks @createArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "schtasks /Create failed (exit $LASTEXITCODE)"
        exit 1
    }
    Write-Output "OK: registered $TaskName (every $minutes min; hidden powershell.exe)"
    Write-Output ("  uninstall: powershell -File automations\install-sinister-link-poller.ps1 -Uninstall")
    exit 0
} catch {
    Write-Error "install failed: $($_.Exception.Message)"
    exit 1
}
