# quality-monotonic-loop.ps1 - iterate a task until quality stops increasing
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T18:40Z (verbatim):
#   "i want you to focus on roudn robin claude account, contracdict ssytem like
#    in jcode code. working on progress until lquality stops increasing"
#
# Composes with:
#   - counter-arg.ps1 (red-team each iteration before applying improvement)
#   - forever-improve.ps1 (Review-style auditing per work unit)
#   - no-bullshit doctrine rule 8 (quality-degradation expansion limits)
#
# Design:
#   Each iteration runs ScoreCommand to produce a numeric score (higher is better).
#   Between iterations, ImproveCommand is invoked to apply the next improvement.
#   counter-arg.ps1 fires BEFORE each ImproveCommand call to log the red-team angle.
#   Loop stops when MaxIters reached OR score has not improved for PlateauCount
#   consecutive iterations OR score regresses by more than RegressTolerance.
#
# Usage:
#   powershell -File quality-monotonic-loop.ps1 `
#       -Lane sanctum `
#       -TaskName 'round-robin-strict smoke-test' `
#       -ScoreCommand 'powershell -NoProfile -Command ". automations/claude-accounts.ps1; (Get-AccountsConfig).last_rotation_index"' `
#       -ImproveCommand 'powershell -NoProfile -Command ". automations/claude-accounts.ps1; Get-NextAvailableAccount | Out-Null"' `
#       -MaxIters 6 -PlateauCount 2
#
# Stop conditions:
#   1. iter >= MaxIters
#   2. last $PlateauCount iters have score <= score at iter (current - PlateauCount)
#   3. score regressed by more than RegressTolerance from prior best
#   4. ScoreCommand fails (non-numeric output) -> abort with status=score-error
#
# Output: per-iter rows appended to _shared-memory/quality-loop-log.jsonl, final
# summary printed to stdout. Returns final score on success, $null on failure.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$Lane,
    [Parameter(Mandatory=$true)] [string]$TaskName,
    [Parameter(Mandatory=$true)] [string]$ScoreCommand,
    [string]$ImproveCommand = '',
    [int]$MaxIters = 10,
    [int]$PlateauCount = 3,
    [double]$RegressTolerance = 0.0,
    [string]$CounterArgClaim = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$DryRun,
    # RKOJ-ELENO :: 2026-05-25 :: checkpoint+revert wiring (operator hard-canonical
    # "stops once quality goes down and reverts back to the peak of the part").
    # Pass repo-relative paths (files or dirs) to snapshot before each ImproveCommand.
    # When -RevertOnRegression is set and stopReason='regression', the loop calls
    # `python automations/loop_checkpoint.py restore-best` to restore the peak iter.
    # Both params are no-op when empty/unset; legacy callers keep working unchanged.
    [string[]]$CheckpointPaths = @(),
    [switch]$RevertOnRegression
)

$ErrorActionPreference = 'Stop'

$logFile = Join-Path $SanctumRoot '_shared-memory\quality-loop-log.jsonl'
$counterArgScript = Join-Path $SanctumRoot 'automations\counter-arg.ps1'

function _Now { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }

function _AppendLog($obj) {
    $json = $obj | ConvertTo-Json -Compress -Depth 6
    $mutex = New-Object System.Threading.Mutex($false, 'SinisterQualityLoopMutex')
    $null = $mutex.WaitOne(5000)
    try { Add-Content -LiteralPath $logFile -Value $json -Encoding UTF8 }
    finally { $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() }
}

function _RunScore {
    param([string]$Cmd)
    $out = Invoke-Expression $Cmd 2>&1 | Select-Object -Last 1
    $score = $null
    if ($out -match '^-?\d+(\.\d+)?$') {
        $score = [double]$out
    } else {
        # try parse last numeric token in line
        $tok = ($out -split '\s+' | Where-Object { $_ -match '^-?\d+(\.\d+)?$' } | Select-Object -Last 1)
        if ($tok) { $score = [double]$tok }
    }
    return $score
}

$runId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$scoreHistory = @()
$bestScore = [double]::NegativeInfinity
$bestIter = -1
$stopReason = 'max-iters'
$startUtc = _Now

# RKOJ-ELENO :: 2026-05-25 :: checkpoint manager probe. Python module ships at
# automations/loop_checkpoint.py (see no-bat-no-ps1 doctrine for why new artifact
# is .py not .ps1). If the file is missing OR python is not on PATH, checkpoint
# wiring silently no-ops -- legacy behavior preserved.
$ckptScript = Join-Path $SanctumRoot 'automations\loop_checkpoint.py'
$ckptEnabled = ($CheckpointPaths.Count -gt 0) -and (Test-Path $ckptScript)
if ($ckptEnabled) {
    Write-Host "  checkpoint paths: $($CheckpointPaths -join ', ')" -ForegroundColor DarkGray
}

function _CkptSave {
    param([int]$IterN)
    if (-not $ckptEnabled) { return }
    if ($DryRun) {
        Write-Host "  [dry-run] would checkpoint iter=$IterN" -ForegroundColor DarkGray
        return
    }
    try {
        $args = @('save', '--lane', $Lane, '--run-id', $runId, '--iter', "$IterN",
                  '--paths') + $CheckpointPaths + @('--sanctum-root', $SanctumRoot)
        $out = & python $ckptScript @args 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [WARN] checkpoint save failed: $out" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARN] checkpoint save exception: $_" -ForegroundColor Yellow
    }
}

function _CkptRestoreBest {
    if (-not $ckptEnabled) { return $null }
    if ($DryRun) {
        Write-Host "  [dry-run] would restore-best lane=$Lane run=$runId" -ForegroundColor DarkGray
        return $null
    }
    try {
        $out = & python $ckptScript 'restore-best' '--lane' $Lane '--run-id' $runId `
                                    '--sanctum-root' $SanctumRoot 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            return $out.Trim()
        } else {
            Write-Host "  [WARN] restore-best failed (exit=$LASTEXITCODE): $out" -ForegroundColor Yellow
            return $null
        }
    } catch {
        Write-Host "  [WARN] restore-best exception: $_" -ForegroundColor Yellow
        return $null
    }
}

Write-Host "quality-monotonic-loop: run_id=$runId lane=$Lane task='$TaskName' max=$MaxIters plateau=$PlateauCount" -ForegroundColor Cyan

for ($iter = 0; $iter -lt $MaxIters; $iter++) {
    # Snapshot BEFORE the iter's improve fires so iter=0 has a baseline + every
    # subsequent iter snapshots its own pre-improve state. Restore picks the
    # iter with max score from quality-loop-log.jsonl, so the baseline at iter=0
    # also acts as the "ship-the-current-version" rollback if everything degrades.
    _CkptSave -IterN $iter

    if ($iter -gt 0 -and $ImproveCommand -and -not $DryRun) {
        # Red-team BEFORE applying improvement (composes with contradict-system focus)
        if ($CounterArgClaim) {
            $claimText = "$TaskName iter $iter improvement"
            $resolutionText = "iter $($iter-1) score=$($scoreHistory[$iter-1]) best=$bestScore"
            & powershell -NoProfile -File $counterArgScript `
                -Lane $Lane `
                -Claim $claimText `
                -Steelman $CounterArgClaim `
                -RedTeam 'improvement may not be monotone; could regress' `
                -Alt 'stop here and ship current best' `
                -BestPath 'open' `
                -Resolution $resolutionText `
                -Status 'open' 2>&1 | Out-Null
        }
        Invoke-Expression $ImproveCommand | Out-Null
    }

    $score = _RunScore -Cmd $ScoreCommand
    if ($null -eq $score) {
        Write-Host "  iter=$iter score=ERROR (non-numeric output)" -ForegroundColor Red
        _AppendLog ([pscustomobject]@{
            run_id = $runId; ts_utc = (_Now); lane = $Lane; task = $TaskName
            iter = $iter; score = $null; status = 'score-error'
        })
        $stopReason = 'score-error'
        break
    }

    $scoreHistory += $score
    if ($score -gt $bestScore) { $bestScore = $score; $bestIter = $iter }

    _AppendLog ([pscustomobject]@{
        run_id = $runId; ts_utc = (_Now); lane = $Lane; task = $TaskName
        iter = $iter; score = $score; best_score = $bestScore; best_iter = $bestIter
    })

    Write-Host ("  iter={0,-2} score={1,-10} best={2} (iter {3})" -f $iter, $score, $bestScore, $bestIter) -ForegroundColor Green

    # Plateau detection: last $PlateauCount iters had no improvement over (iter - PlateauCount)
    if ($iter -ge $PlateauCount) {
        $windowMax = ($scoreHistory[($iter - $PlateauCount + 1)..$iter] | Measure-Object -Maximum).Maximum
        $referenceScore = $scoreHistory[$iter - $PlateauCount]
        if ($windowMax -le $referenceScore) {
            $stopReason = "plateau-$PlateauCount-iters"
            break
        }
    }

    # Regression detection
    if ($bestScore - $score -gt $RegressTolerance) {
        $stopReason = 'regression'
        break
    }
}

# RKOJ-ELENO :: 2026-05-25 :: revert-to-peak on regression. Operator hard-canonical
# "stops once quality goes down and reverts back to the peak of the part". Only
# fires when -RevertOnRegression and stopReason indicates degradation.
$revertInfo = $null
if ($RevertOnRegression -and ($stopReason -eq 'regression' -or $stopReason -like 'plateau-*') -and $ckptEnabled) {
    Write-Host ''
    Write-Host "[REVERT] $stopReason detected; restoring peak iter $bestIter (score=$bestScore)..." -ForegroundColor Yellow
    $revertInfo = _CkptRestoreBest
    if ($revertInfo) {
        Write-Host "[REVERT] $revertInfo" -ForegroundColor Green
    }
}

$summary = [pscustomobject]@{
    run_id = $runId
    started_utc = $startUtc
    ended_utc = (_Now)
    lane = $Lane
    task = $TaskName
    iters_run = $scoreHistory.Count
    best_score = $bestScore
    best_iter = $bestIter
    stop_reason = $stopReason
    score_history = $scoreHistory
    checkpoint_paths = $CheckpointPaths
    reverted = ($null -ne $revertInfo)
}
_AppendLog ($summary | Select-Object *, @{n='kind';e={'summary'}})

Write-Host ''
Write-Host "FINAL: best_score=$bestScore at iter $bestIter / $($scoreHistory.Count) iters / stop=$stopReason" -ForegroundColor Cyan
if ($revertInfo) { Write-Host "REVERTED to iter $bestIter" -ForegroundColor Cyan }
Write-Host "log: $logFile (run_id=$runId)"

return $bestScore
