# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# Sanctum auto-push daemon.
#
# Runs every 30 min via SinisterSanctumAutoPush scheduled task. Diffs the
# working tree + checks for unpushed local commits on `main`. If there's
# nothing to do, exits clean. If there's activity, stages everything (the
# .gitignore is the secrets gate), commits with a timestamped chore message,
# and pushes to origin.
#
# Exit codes:
#   0  = pushed (commit landed on origin/main)
#   1  = skipped (no activity OR not on main)
#   2  = lock held (another run in progress)
#   10 = staging/commit failed
#   11 = push failed
#   12 = secret-scrub regex tripped (abort, do NOT push)
#
# Safety rails:
#   - Branch guard: only commits on `main`. Other agents' per-agent branches
#     stay untouched.
#   - Lock file at _shared-memory/.auto-push.lock (cleaned in finally).
#   - Secret regex defense-in-depth beyond .gitignore.
#   - Never force-push.

[CmdletBinding()]
param(
    [string]$RepoRoot   = 'D:\Sinister Sanctum',
    [string]$Branch     = 'main',
    [string]$Remote     = 'origin',
    [int]$LogRotateMB   = 2,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

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
if (Test-Path $lockFile) {
    $lockAge = (Get-Date) - (Get-Item $lockFile).LastWriteTime
    # Stale-lock recovery: if the lock is > 25 min old, prior run hung — take over.
    if ($lockAge.TotalMinutes -lt 25) {
        Write-Log 'skipped' "lock-held age=$([int]$lockAge.TotalMinutes)m path=$lockFile"
        exit 2
    }
    Write-Log 'note' "stale-lock-removed age=$([int]$lockAge.TotalMinutes)m"
    Remove-Item -LiteralPath $lockFile -Force
}

try {
    Set-Content -LiteralPath $lockFile -Value $PID -Encoding utf8

    # ---- Branch guard ----
    $b = Invoke-Git rev-parse --abbrev-ref HEAD
    if ($b.exit -ne 0) {
        Write-Log 'error' "branch-detect-failed: $($b.output)"
        exit 10
    }
    $current = $b.output.Trim()
    if ($current -ne $Branch) {
        Write-Log 'skipped' "not-on-target-branch current=$current target=$Branch"
        exit 1
    }

    # ---- Activity check ----
    $porc = Invoke-Git status --porcelain
    if ($porc.exit -ne 0) {
        Write-Log 'error' "status-failed: $($porc.output)"
        exit 10
    }
    $dirty = -not [string]::IsNullOrWhiteSpace($porc.output)

    # Are there local commits not yet on origin?
    $fetch = Invoke-Git fetch $Remote $Branch
    if ($fetch.exit -ne 0) {
        # Network glitch — log + retry next tick.
        Write-Log 'error' "fetch-failed: $($fetch.output.Split([Environment]::NewLine)[0])"
        exit 11
    }
    $ahead = Invoke-Git rev-list "$Remote/$Branch..HEAD" --count
    $aheadCount = 0
    if ($ahead.exit -eq 0 -and $ahead.output -match '^\d+$') {
        $aheadCount = [int]$ahead.output.Trim()
    }

    if (-not $dirty -and $aheadCount -eq 0) {
        Write-Log 'skipped' 'no-activity'
        exit 1
    }

    # ---- Stage ----
    if ($dirty) {
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
        $msgBody = "Auto-mirror of D:\Sinister Sanctum to origin/$Branch via SinisterSanctumAutoPush.`n`nTop changes:`n - $top10"
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

    # ---- Push ----
    if ($DryRun) {
        Write-Log 'dry-run' "would-push sha=$sha"
        exit 0
    }
    $push = Invoke-Git push $Remote $Branch
    if ($push.exit -ne 0) {
        Write-Log 'error' "push-failed: $($push.output.Split([Environment]::NewLine)[0])"
        exit 11
    }

    Write-Log 'pushed' "sha=$sha to=$Remote/$Branch"
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
