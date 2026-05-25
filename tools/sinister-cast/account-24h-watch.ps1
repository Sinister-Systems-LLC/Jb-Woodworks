# Author: RKOJ-ELENO :: 2026-05-24
# Lane: kernel-apk (EVE on Sinister Kernel APK, purple accent)
# Tool: sinister-cast / account-24h-watch.ps1
# Purpose: 24-hour survival watch harness for a freshly created + harvested Snap
#          account. Polls panel every PollMinutes for account state; logs to
#          PROGRESS; alerts operator on flag/ban events; emits SURVIVED or
#          DIED_<reason> verdict at creation_ts + 24h.
#
# Composes with:
#   - Operator runbook Phase 4 (D:\Sinister Sanctum\_shared-memory\plans\kernel-apk-andrewt407-24h-survival-2026-05-24\runbook.md)
#   - snap-account-24h-survival-doctrine-2026-05-21 (the empirical doctrine this monitors)
#
# Pure PowerShell 5.1 compatible. No && / ternary / null-coalescing / em-dash.
# ASCII-only per sub-agent-ascii-only-prompt-template-doctrine-2026-05-24.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Handle,

    [Parameter(Mandatory = $true)]
    [string]$CreationTsUtc,

    [Parameter(Mandatory = $false)]
    [string]$PanelBase = "https://snap.sinijkr.com",

    [Parameter(Mandatory = $false)]
    [int]$PollMinutes = 30,

    [Parameter(Mandatory = $false)]
    [string]$LogPath = "",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Parse creation timestamp
try {
    $creationDt = [datetime]::ParseExact($CreationTsUtc, "yyyy-MM-ddTHH:mm:ssZ", $null).ToUniversalTime()
} catch {
    Write-Host "ERROR: -CreationTsUtc must be ISO-8601 UTC like 2026-05-24T20:30:00Z" -ForegroundColor Red
    exit 2
}
$deadlineDt = $creationDt.AddHours(24)

# Default log path
if ([string]::IsNullOrWhiteSpace($LogPath)) {
    $LogPath = "D:\Sinister Sanctum\_shared-memory\PROGRESS\account-24h-watch-$Handle.log"
}

$AccentColor = 'Magenta'
$OkColor     = 'Green'
$WarnColor   = 'Yellow'
$BadColor    = 'Red'
$DimColor    = 'DarkGray'

function Write-Log([string]$line) {
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $msg = "$stamp $line"
    Write-Host $msg -ForegroundColor $DimColor
    Add-Content -Path $LogPath -Value $msg -Encoding UTF8
}

function Poll-PanelAccount([string]$handle) {
    if ($DryRun) {
        return @{
            handle           = $handle
            status           = 'active'
            last_activity_ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            pi_verdict       = '3/3'
            friend_count     = 1
            flags            = @()
            dry_run          = $true
        }
    }
    $url = "$PanelBase/api/accounts?q=$handle"
    try {
        $resp = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 15
        return $resp
    } catch {
        return @{
            handle = $handle
            status = 'panel-unreachable'
            error  = $_.Exception.Message
        }
    }
}

function Eval-Verdict($snapshot, [datetime]$deadlineDt) {
    # Returns one of: ACTIVE / SURVIVED / DIED_<reason> / PANEL_UNREACHABLE
    $nowUtc = (Get-Date).ToUniversalTime()
    if ($snapshot.status -eq 'panel-unreachable') { return 'PANEL_UNREACHABLE' }
    if ($snapshot.status -eq 'banned')   { return "DIED_BANNED" }
    if ($snapshot.status -eq 'flagged')  { return "DIED_FLAGGED" }
    if ($snapshot.status -eq 'expired')  { return "DIED_EXPIRED" }
    if ($snapshot.pi_verdict -and $snapshot.pi_verdict -ne '3/3' -and $snapshot.pi_verdict -ne 'unknown') {
        return "DIED_PI_DEGRADED_$($snapshot.pi_verdict)"
    }
    if ($nowUtc -ge $deadlineDt) { return 'SURVIVED' }
    return 'ACTIVE'
}

# Header
Write-Host ""
Write-Host "============================================================" -ForegroundColor $AccentColor
Write-Host "  Sinister Cast -- Account 24h Survival Watch" -ForegroundColor $AccentColor
Write-Host "  Author: RKOJ-ELENO :: 2026-05-24" -ForegroundColor $AccentColor
Write-Host "============================================================" -ForegroundColor $AccentColor
Write-Host ""
Write-Host "  Handle:       $Handle"
Write-Host "  Creation UTC: $($creationDt.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
Write-Host "  Deadline UTC: $($deadlineDt.ToString('yyyy-MM-ddTHH:mm:ssZ'))"
Write-Host "  Panel base:   $PanelBase"
Write-Host "  Poll:         every $PollMinutes minutes"
Write-Host "  Log path:     $LogPath"
if ($DryRun) {
    Write-Host "  Mode:         DRY-RUN (single iter, synthetic snapshot)" -ForegroundColor $WarnColor
}
Write-Host ""

Write-Log "watch-armed handle=$Handle creation=$($creationDt.ToString('yyyy-MM-ddTHH:mm:ssZ')) deadline=$($deadlineDt.ToString('yyyy-MM-ddTHH:mm:ssZ')) poll_min=$PollMinutes panel=$PanelBase dry_run=$DryRun"

$pollIter = 0
while ($true) {
    $pollIter++
    $snapshot = Poll-PanelAccount -handle $Handle
    $verdict = Eval-Verdict $snapshot $deadlineDt

    $snapJson = ($snapshot | ConvertTo-Json -Compress)
    Write-Log "poll iter=$pollIter verdict=$verdict snapshot=$snapJson"

    Write-Host "[$pollIter] verdict=" -NoNewline
    $color = $OkColor
    if ($verdict -like 'DIED_*')         { $color = $BadColor }
    if ($verdict -eq 'PANEL_UNREACHABLE') { $color = $WarnColor }
    if ($verdict -eq 'SURVIVED')         { $color = $OkColor }
    Write-Host $verdict -ForegroundColor $color

    if ($verdict -eq 'SURVIVED' -or $verdict -like 'DIED_*') {
        Write-Host ""
        Write-Host "FINAL VERDICT: $verdict" -ForegroundColor $color
        Write-Log "FINAL verdict=$verdict iter=$pollIter"
        exit 0
    }

    if ($DryRun) {
        Write-Host ""
        Write-Host "DRY-RUN: single iter completed; not polling further." -ForegroundColor $WarnColor
        exit 0
    }

    Write-Host "  Sleeping $PollMinutes min until next poll..." -ForegroundColor $DimColor
    Start-Sleep -Seconds ($PollMinutes * 60)
}
