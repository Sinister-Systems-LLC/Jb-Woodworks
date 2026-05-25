# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Updated: RKOJ-ELENO :: 2026-05-23 — push CURRENT branch (not just main) so
#   per-agent branches (agent/<slug>/<topic>) also propagate to GitHub. Operator
#   directive: "make sure sinsiter bat file everytime it updates it pushes to
#   github ... thats the only github repo we push to ... connects with leo so
#   we can work as one".
#
# Sanctum auto-push daemon.
#
# Runs every 30 min via SinisterSanctumAutoPush scheduled task. Pushes the
# CURRENT branch (whichever one HEAD is on). For `main` it does the original
# stage-everything-and-commit behavior; for any `agent/*` branch it ONLY
# pushes existing commits (no auto-staging — agents own their own staging).
# Either way, also runs `git fetch --all --prune` so Leo's pushed branches
# show up on operator's machine (and vice versa).
#
# Exit codes:
#   0  = pushed (commit landed on origin/<branch>)
#   1  = skipped (no activity)
#   2  = lock held (another run in progress)
#   10 = staging/commit failed
#   11 = push failed
#   12 = secret-scrub regex tripped (abort, do NOT push)
#   13 = push-policy violation (RKOJ-ELENO 2026-05-25; origin URL doesn't match policy)
#
# Safety rails:
#   - Branch handling: on `main` → stage + commit + push.
#                       on `agent/*` → push existing commits only (no auto-add).
#                       on any other branch (e.g. detached HEAD) → skip.
#   - Lock file at _shared-memory/.auto-push.lock (cleaned in finally).
#   - Secret regex defense-in-depth beyond .gitignore.
#   - Never force-push.

[CmdletBinding()]
param(
    [string]$RepoRoot   = 'D:\Sinister Sanctum',
    [string]$Branch     = '',
    [string]$Remote     = 'origin',
    [int]$LogRotateMB   = 2,
    [switch]$DryRun,
    # RKOJ-ELENO :: 2026-05-25 -- on-demand push hook per
    # frequent-detailed-commits-per-agent-2026-05-25.md (operator hard-canonical).
    # Action=PushNow runs the same flow as the scheduled task but bypasses the lock-age
    # skip (still respects active lock with 60s wait). Slug just tags the log line.
    [ValidateSet('','PushNow','Status')]
    [string]$Action     = '',
    [string]$Slug       = ''
)

if ($Action -eq 'Status') {
    $logFile2 = Join-Path $RepoRoot '_shared-memory\auto-push.log'
    if (Test-Path $logFile2) { Get-Content -LiteralPath $logFile2 -Tail 5 } else { 'no-log-yet' }
    exit 0
}

# RKOJ-ELENO :: 2026-05-23 — was 'Stop'; that turned every native-cmd stderr line
# (like `From https://github.com/...` from git fetch) into a terminating exception
# on PS5.1, making auto-push log show "exception: From https://..." instead of
# the actual git operation result. 'Continue' lets Invoke-Git capture and inspect
# its own $LASTEXITCODE without PS pre-empting.
$ErrorActionPreference = 'Continue'

# ---- Paths ----
$logDir    = Join-Path $RepoRoot '_shared-memory'
$logFile   = Join-Path $logDir   'auto-push.log'
$lockFile  = Join-Path $logDir   '.auto-push.lock'

function Write-Log {
    param([string]$Action, [string]$Detail)
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line  = "$stamp | $Action | $Detail"
    Add-Content -LiteralPath $logFile -Value $line -Encoding utf8
    Write-Host $line
}

function Rotate-Log {
    if (-not (Test-Path $logFile)) { return }
    $size = (Get-Item $logFile).Length
    if ($size -gt ($LogRotateMB * 1024 * 1024)) {
        $rot = "$logFile.1"
        if (Test-Path $rot) { Remove-Item -LiteralPath $rot -Force }
        Move-Item -LiteralPath $logFile -Destination $rot -Force
    }
}

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    $out = & git -C $RepoRoot @Args 2>&1
    return @{
        exit   = $LASTEXITCODE
        output = ($out -join "`n")
    }
}

# ---- Pre-flight ----
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
Rotate-Log

# Lock check (prevents concurrent runs even if the task overlaps)
# RKOJ-ELENO :: 2026-05-25 -- PushNow waits up to 60s for an active lock rather
# than skipping immediately, so on-demand pushes from agent code don't silently
# no-op when a scheduled run is mid-flight.
if (Test-Path $lockFile) {
    $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    if ($Action -eq 'PushNow') {
        $waited = 0
        while ((Test-Path $lockFile) -and $waited -lt 60) {
            Start-Sleep -Seconds 2; $waited += 2
        }
        if (Test-Path $lockFile) {
            $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
            if ($lockAge.TotalMinutes -gt 25) {
                Write-Log 'note' "PushNow stale-lock-removed age=$([int]$lockAge.TotalMinutes)m"
                Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
            } else {
                Write-Log 'skipped' "PushNow lock-still-held-after-60s age=$([int]$lockAge.TotalMinutes)m slug=$Slug"
                exit 2
            }
        }
    } else {
        # Stale-lock recovery: if the lock is > 25 min old, prior run hung -- take over.
        if ($lockAge.TotalMinutes -lt 25) {
            Write-Log 'skipped' "lock-held age=$([int]$lockAge.TotalMinutes)m path=$lockFile"
            exit 2
        }
        Write-Log 'note' "stale-lock-removed age=$([int]$lockAge.TotalMinutes)m"
        Remove-Item -LiteralPath $lockFile -Force
    }
}

try {
    Set-Content -LiteralPath $lockFile -Value $PID -Encoding utf8

    # ---- Branch detection + mode selection ----
    # RKOJ-ELENO :: 2026-05-23 — was: only push when on $Branch (default main).
    # Now: push whatever HEAD is on. main = stage + commit + push.
    # agent/* = push existing commits only (no auto-staging — agents own staging).
    $b = Invoke-Git rev-parse --abbrev-ref HEAD
    if ($b.exit -ne 0) {
        Write-Log 'error' "branch-detect-failed: $($b.output)"
        exit 10
    }
    $current = $b.output.Trim()

    # Decide push mode
    $allowAutoStage = $false
    if ($Branch -and $Branch -ne '') {
        # Explicit -Branch override: respect old behavior
        if ($current -ne $Branch) {
            Write-Log 'skipped' "not-on-target-branch current=$current target=$Branch"
            exit 1
        }
        $allowAutoStage = $true
        $TargetBranch = $Branch
    } elseif ($current -eq 'main') {
        # Default: main → stage + commit + push
        $allowAutoStage = $true
        $TargetBranch = 'main'
    } elseif ($current -like 'agent/*') {
        # Per-agent branch → push existing commits only
        $allowAutoStage = $false
        $TargetBranch = $current
    } elseif ($current -eq 'HEAD') {
        Write-Log 'skipped' "detached-HEAD"
        exit 1
    } else {
        # Any other branch (e.g. feature/*, fix/*) → push existing commits only
        $allowAutoStage = $false
        $TargetBranch = $current
    }

    # ---- Global fetch so Leo's branches sync to operator + vice versa ----
    # RKOJ-ELENO :: 2026-05-23 — fetch all branches not just $TargetBranch
    # so multi-operator workflows (Leo + operator on different agent branches)
    # see each other's branches without manual `git fetch`.
    $fetchAll = Invoke-Git fetch $Remote --prune
    if ($fetchAll.exit -ne 0) {
        Write-Log 'warn' "fetch-all-failed (non-fatal): $($fetchAll.output.Split([Environment]::NewLine)[0])"
    }

    # ---- Activity check ----
    $porc = Invoke-Git status --porcelain
    if ($porc.exit -ne 0) {
        Write-Log 'error' "status-failed: $($porc.output)"
        exit 10
    }
    $dirty = -not [string]::IsNullOrWhiteSpace($porc.output)

    # Are there local commits not yet on origin/<TargetBranch>?
    $ahead = Invoke-Git rev-list "$Remote/$TargetBranch..HEAD" --count
    $aheadCount = 0
    if ($ahead.exit -eq 0 -and $ahead.output -match '^\d+$') {
        $aheadCount = [int]$ahead.output.Trim()
    } else {
        # Upstream may not exist yet (new agent branch never pushed) — try without ..
        $headCount = Invoke-Git rev-list HEAD --count
        if ($headCount.exit -eq 0 -and $headCount.output -match '^\d+$') {
            $aheadCount = 1  # treat as "needs push" so first push lands
        }
    }

    # Branch-mode-aware activity check.
    # main-mode (allowAutoStage=true): need EITHER $dirty OR $aheadCount>0 to proceed.
    # agent-mode (allowAutoStage=false): need ONLY $aheadCount>0 (we ignore dirty tree
    #   because the agent owns its own staging — auto-push must never touch agents' WIP).
    if ($allowAutoStage) {
        if (-not $dirty -and $aheadCount -eq 0) {
            Write-Log 'skipped' 'no-activity'
            exit 1
        }
    } else {
        if ($aheadCount -eq 0) {
            Write-Log 'skipped' "no-commits-to-push branch=$TargetBranch (agent-mode)"
            exit 1
        }
        $sha = (Invoke-Git rev-parse --short HEAD).output.Trim()
        Write-Log 'note' "agent-branch-push ahead=$aheadCount sha=$sha branch=$TargetBranch"
    }

    # ---- Stage (main-mode only; agent-mode skips this whole block) ----
    if ($dirty -and $allowAutoStage) {
        $add = Invoke-Git add -A
        if ($add.exit -ne 0) {
            Write-Log 'error' "add-failed: $($add.output)"
            exit 10
        }

        # ---- Secret regex defense-in-depth ----
        # Cheap scan of the staged diff (text portions only). The .gitignore is
        # the primary gate; this is belt + braces.
        $diff = Invoke-Git diff --cached --unified=0
        if ($diff.exit -eq 0 -and $diff.output) {
            $patterns = @(
                'sk-ant-[A-Za-z0-9_-]{20,}',
                'sk_live_[A-Za-z0-9]{20,}',
                'OPENAI_API_KEY\s*=\s*sk-[A-Za-z0-9_-]{20,}',
                '-----BEGIN [A-Z ]*PRIVATE KEY-----',
                'ghp_[A-Za-z0-9]{30,}',
                'github_pat_[A-Za-z0-9_]{50,}'
            )
            foreach ($p in $patterns) {
                if ($diff.output -match $p) {
                    Write-Log 'aborted' "secret-regex-tripped pattern=$p"
                    Invoke-Git reset HEAD | Out-Null
                    exit 12
                }
            }
        }

        # Build commit message
        $changedFiles = Invoke-Git diff --cached --name-only
        $changedLines = @()
        if ($changedFiles.exit -eq 0 -and $changedFiles.output) {
            $changedLines = $changedFiles.output -split "`n" | Where-Object { $_ }
        }
        $changeCount = $changedLines.Count
        $stampUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $top10 = ($changedLines | Select-Object -First 10) -join "`n - "
        $msgSubject = "chore(auto-push): $stampUtc — $changeCount file$(if($changeCount -ne 1){'s'}) changed"
        $msgBody = "Auto-mirror of D:\Sinister Sanctum to $Remote/$TargetBranch via SinisterSanctumAutoPush.`n`nTop changes:`n - $top10"
        if ($changeCount -gt 10) { $msgBody += "`n - ... and $($changeCount - 10) more" }
        $msgFull = "$msgSubject`n`n$msgBody"

        if ($DryRun) {
            Write-Log 'dry-run' "would-commit count=$changeCount"
            exit 0
        }

        # Commit via -F to handle multiline body safely
        $msgFile = [System.IO.Path]::GetTempFileName()
        Set-Content -LiteralPath $msgFile -Value $msgFull -Encoding utf8
        try {
            $commit = Invoke-Git commit -F $msgFile
            if ($commit.exit -ne 0) {
                # Nothing-to-commit edge case (race condition with another writer)
                if ($commit.output -match 'nothing to commit') {
                    Write-Log 'skipped' 'race-condition-empty-commit'
                    exit 1
                }
                Write-Log 'error' "commit-failed: $($commit.output.Split([Environment]::NewLine)[0])"
                exit 10
            }
        } finally {
            Remove-Item -LiteralPath $msgFile -Force -ErrorAction SilentlyContinue
        }

        $sha = (Invoke-Git rev-parse --short HEAD).output.Trim()
        Write-Log 'committed' "sha=$sha count=$changeCount"
    } else {
        $sha = (Invoke-Git rev-parse --short HEAD).output.Trim()
        Write-Log 'note' "pushing-existing-commits ahead=$aheadCount sha=$sha"
    }

    # ---- Pre-push policy guard (RKOJ-ELENO :: 2026-05-25) ----
    # Operator hard-canonical 2026-05-25: single-repo push policy. Refuse to push
    # if the working repo's origin URL diverges from the policy in projects.json
    # (3 carve-outs: LetsText, Showmasters, JB Woodworks).
    $policyScript = Join-Path (Split-Path -Parent $PSCommandPath) 'sanctum-push-policy.ps1'
    if (Test-Path $policyScript) {
        & $policyScript -Action CheckPath -Path $RepoRoot | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Log 'aborted' "push-policy-violation repo=$RepoRoot (run sanctum-push-policy -Action Audit for detail)"
            exit 13
        }
    }

    # ---- Push ----
    # RKOJ-ELENO :: 2026-05-23 — push $TargetBranch (whichever branch HEAD is on),
    # not just $Branch. First-time pushes get -u to track upstream.
    if ($DryRun) {
        Write-Log 'dry-run' "would-push sha=$sha to=$Remote/$TargetBranch"
        exit 0
    }
    # Check if upstream exists; if not, use -u to set it on first push.
    $upstream = Invoke-Git rev-parse --abbrev-ref "$TargetBranch@{upstream}"
    if ($upstream.exit -ne 0) {
        $push = Invoke-Git push -u $Remote $TargetBranch
    } else {
        $push = Invoke-Git push $Remote $TargetBranch
    }
    if ($push.exit -ne 0) {
        Write-Log 'error' "push-failed: $($push.output.Split([Environment]::NewLine)[0])"
        exit 11
    }

    Write-Log 'pushed' "sha=$sha to=$Remote/$TargetBranch"
    exit 0
}
catch {
    Write-Log 'error' "exception: $($_.Exception.Message)"
    exit 10
}
finally {
    if (Test-Path $lockFile) {
        Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
    }
}
