# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# verify-auto-push.ps1 -- probe the SinisterSanctumAutoPush scheduled task state.
#
# Standing rule #14 (canonical-14 in _shared-memory/DIRECTIVES.md): Sanctum
# auto-pushes to GitHub every 30 minutes via the SinisterSanctumAutoPush task.
# Prior PROGRESS entries claimed the task was "registered + shipped" but the
# 2026-05-19 11:17 runtime audit ("HR-B") found it MISSING from the scheduler.
# This script gives the operator (and master agent) a fast read on the actual
# registration + run state, plus a suggested reinstall command if absent.
#
# Read-only: never registers, starts, stops, or modifies anything.
#
# Exit codes:
#   0 -- task exists and last-run was successful
#   1 -- task exists but last-run failed OR is stale (>2h)
#   2 -- task does NOT exist (registration was lost or never landed)
#   3 -- script failed to query (permission / WMI error)

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterSanctumAutoPush',
    [string]$LogPath  = 'D:\Sinister Sanctum\_shared-memory\auto-push.log'
)

$ErrorActionPreference = 'Continue'
$Purple = 'Magenta'

function Write-Section { param([string]$T) Write-Host ''; Write-Host ('== ' + $T + ' ==') -ForegroundColor $Purple }
function Write-OK     { param([string]$M) Write-Host ('[ OK ] ' + $M) -ForegroundColor Green }
function Write-Warn   { param([string]$M) Write-Host ('[WARN] ' + $M) -ForegroundColor Yellow }
function Write-Fail   { param([string]$M) Write-Host ('[FAIL] ' + $M) -ForegroundColor Red }
function Write-Info   { param([string]$M) Write-Host ('[INFO] ' + $M) -ForegroundColor White }

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host '##  Sanctum auto-push daemon -- verify-auto-push.ps1            ##' -ForegroundColor $Purple
Write-Host '##  read-only probe of SinisterSanctumAutoPush scheduled task  ##' -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple

# ----------------------------------------------------- task registration ---
Write-Section ('Step 1: scheduled-task lookup (' + $TaskName + ')')

$task = $null
try {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Write-OK ('found: ' + $task.TaskName + ' (' + $task.State + ')')
} catch {
    Write-Fail ('NOT registered: Get-ScheduledTask returned no such task')
    Write-Host ''
    Write-Info 'Suggested fix (operator must click; lane discipline forbids master registering tasks):'
    Write-Host '  & "D:\Sinister Sanctum\automations\install-auto-push-task.ps1"' -ForegroundColor White
    Write-Host '  # or, if that script does not exist:'
    Write-Host '  schtasks /Create /TN SinisterSanctumAutoPush /SC MINUTE /MO 30 ^' -ForegroundColor White
    Write-Host '         /TR "powershell -ExecutionPolicy Bypass -File ""D:\Sinister Sanctum\automations\sanctum-auto-push.ps1""" ^' -ForegroundColor White
    Write-Host '         /F' -ForegroundColor White
    Write-Host ''
    Write-Info 'See also _shared-memory/knowledge/sanctum-auto-push.md for the canonical install procedure.'
    exit 2
}

# ------------------------------------------------------- task last-run info ---
Write-Section 'Step 2: last-run / next-run telemetry'

try {
    $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
    $lastRun = $info.LastRunTime
    $nextRun = $info.NextRunTime
    $lastResult = $info.LastTaskResult

    Write-Info ('LastRunTime    : ' + $lastRun)
    Write-Info ('NextRunTime    : ' + $nextRun)
    Write-Info ('LastTaskResult : ' + $lastResult + (if ($lastResult -eq 0) { ' (success)' } else { ' (failure)' }))
    Write-Info ('NumberOfMissedRuns: ' + $info.NumberOfMissedRuns)

    $stale = $false
    if ($lastRun -and ($lastRun -lt (Get-Date).AddHours(-2))) {
        $stale = $true
        Write-Warn ('last run was more than 2h ago -- daemon may be stuck or disabled.')
    }
    if ($lastResult -ne 0) {
        Write-Warn ('last result was non-zero (' + $lastResult + ').')
    }

    if ($stale -or $lastResult -ne 0) {
        $exitCode = 1
    } else {
        Write-OK 'task appears healthy (recent run, zero result).'
        $exitCode = 0
    }
} catch {
    Write-Fail ('could not read task info: ' + $_.Exception.Message)
    exit 3
}

# ------------------------------------------------- companion log inspection ---
Write-Section ('Step 3: companion log (' + $LogPath + ')')

if (Test-Path -LiteralPath $LogPath) {
    $log = Get-Item -LiteralPath $LogPath
    $ageMin = [Math]::Round(((Get-Date) - $log.LastWriteTime).TotalMinutes, 1)
    Write-Info ('log mtime: ' + $log.LastWriteTime + ' (' + $ageMin + ' min ago)')
    Write-Info ('log size : ' + [Math]::Round($log.Length / 1KB, 2) + ' KB')
    try {
        $tail = Get-Content -LiteralPath $LogPath -Tail 8
        Write-Host ''
        Write-Info 'last 8 lines:'
        $tail | ForEach-Object { Write-Host ('  ' + $_) -ForegroundColor DarkGray }
    } catch {
        Write-Warn ('could not read tail: ' + $_.Exception.Message)
    }
} else {
    Write-Warn ('log not found at: ' + $LogPath)
    Write-Info 'expected when:'
    Write-Info '  - task was just registered + has not run yet'
    Write-Info '  - working tree is always clean (daemon may skip-and-not-log)'
    Write-Info '  - operator pointed the log elsewhere via the sanctum-auto-push.ps1 arg'
}

Write-Host ''
Write-OK ('exit code: ' + $exitCode)
exit $exitCode
