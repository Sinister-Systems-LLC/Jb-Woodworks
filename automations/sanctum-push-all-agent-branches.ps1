# Author: RKOJ-ELENO :: 2026-05-25
#
# sanctum-push-all-agent-branches.ps1 -- iterate over every local agent/*
# branch and push any that are ahead of their upstream. Runs frequently
# (every 5 min via SinisterPushAllAgents scheduled task) so operator-facing
# Leo-sync surface stays fresh without depending on which branch the
# auto-push daemon's shell happens to be on at any given moment.
#
# Operator hard-canonical 2026-05-25T02:02Z verbatim:
#     "push it and complete everything... once eve is done... need the pushes
#      with detailed committs to happen often per agent running... baked into
#      memory with no issues that connects with leo"
#
# Composes with:
#   - sanctum-auto-push (existing 30-min current-branch daemon -- THIS adds
#     the every-agent fan-out the daemon doesn't do)
#   - sanctum-push-policy (refuses out-of-policy pushes, exit 13)
#   - branch-convention-2026-05-25 (only push agent/<project-key>/* names)
#   - sinister-headless (this script is invoked via -WindowStyle Hidden cron)
#   - sinister-link-doctrine (Leo's machine also runs this; both peers fan)
#   - frequent-detailed-commits-per-agent-2026-05-25 (the per-commit-message
#     discipline this script enables by surfacing every push)
#
# What it does (per invocation):
#   1. git fetch --all --prune (mirror sanctum-auto-push pattern; Leo's
#      branches show up + vice versa)
#   2. for each local agent/* branch:
#       a. ls-remote to determine if upstream exists + sha
#       b. compare local HEAD sha to upstream sha
#       c. if local > upstream (branch ahead): git push origin <branch>
#       d. if no upstream: push with -u to create
#       e. capture rc + duration; log to JSONL
#   3. write summary JSONL row + return
#
# Exit codes:
#   0 = OK (zero or more pushes succeeded; no errors)
#   1 = at least one push failed (rest still attempted)
#   2 = git fetch failed (network or repo problem; pushes skipped)
#   3 = no agent/* branches found (probably running outside sanctum repo)

[CmdletBinding()]
param(
    [string]$RepoRoot = 'D:\Sinister Sanctum',
    [string]$Remote   = 'origin',
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$logDir = Join-Path $RepoRoot '_shared-memory\sinister-term-history'
$logJsonl = Join-Path $logDir 'push-all-agent-branches.jsonl'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

function Write-LogRow {
    param([hashtable]$Row)
    try {
        $line = ($Row | ConvertTo-Json -Compress -Depth 5)
        Add-Content -Path $logJsonl -Value $line -Encoding utf8
    } catch {}
}

function _git {
    # PS5.1 gotcha: `$Args` is an automatic variable shadowing function params.
    # Renamed to $GitArgs to avoid the shadow that swallowed for-each-ref args.
    param([string[]]$GitArgs)
    Push-Location $RepoRoot
    try {
        $combined = & git @GitArgs 2>&1
        $rc = $LASTEXITCODE
        return @{ rc = $rc; out = ($combined -join "`n") }
    } finally {
        Pop-Location
    }
}

$startTs = (Get-Date).ToUniversalTime().ToString('o')

# Step 1: fetch (so we have fresh upstream refs)
if (-not $Quiet) { Write-Host "[*] fetching all + prune..." }
# Note: NOT --quiet (we want "From <url>" lines for diagnostics).
# Continue PAST fetch errors -- common cause is localhost:3000 Gitea down
# while origin (GitHub) is fine. The actual push step is what matters for
# the operator's "agents push to GitHub for Leo sync" goal. Pushes use their
# own per-remote auth; a failed fetch doesn't gate them.
$fetch = _git @('fetch','--all','--prune')
$fetchPartial = ($fetch.rc -ne 0)
if ($fetchPartial) {
    Write-LogRow @{
        ts_utc = $startTs; phase = 'fetch'; rc = $fetch.rc; warning = 'fetch_partial_continuing'
        first_err_lines = ($fetch.out -split "`n" | Select-Object -First 3) -join ' | '
    }
    if (-not $Quiet) { Write-Host "[!] fetch rc=$($fetch.rc) (likely localhost remote down) -- continuing to push step" }
}

# Step 2: enumerate local agent/* branches
$branchList = _git @('for-each-ref','--format=%(refname:short)','refs/heads/agent/')
if ($branchList.rc -ne 0 -or -not $branchList.out) {
    if (-not $Quiet) { Write-Host "[?] no agent/* branches found" }
    Write-LogRow @{ ts_utc = $startTs; phase = 'enum'; result = 'no_agent_branches' }
    exit 3
}
$branches = ($branchList.out -split "`n" | Where-Object { $_.Trim() })

$pushed = 0
$failed = 0
$skipped = 0
$created = 0
$details = @()

foreach ($b in $branches) {
    $b = $b.Trim()
    if (-not $b) { continue }

    # Get local + upstream SHAs
    $localSha = (_git @('rev-parse','--verify','--quiet',$b)).out.Trim()
    if (-not $localSha) { continue }

    $remoteSha = (_git @('rev-parse','--verify','--quiet',"$Remote/$b")).out.Trim()

    if (-not $remoteSha) {
        # Branch doesn't exist on remote yet -- create with -u
        if ($DryRun) {
            if (-not $Quiet) { Write-Host "[?] would create-and-push $b (no upstream)" }
            $skipped++
            continue
        }
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $push = _git @('push','-u',$Remote,$b)
        $sw.Stop()
        $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        if ($push.rc -eq 0) {
            $created++
            if (-not $Quiet) { Write-Host "[+] created+pushed $b ($($elapsed)s)" }
            $details += @{ branch = $b; action = 'created'; elapsed_s = $elapsed; rc = 0 }
        } else {
            $failed++
            if (-not $Quiet) { Write-Host "[x] create-push failed $b rc=$($push.rc)" }
            $err = ($push.out -split "`n" | Select-Object -First 2) -join '; '
            $details += @{ branch = $b; action = 'create_failed'; rc = $push.rc; err = $err }
        }
        continue
    }

    if ($localSha -eq $remoteSha) {
        $skipped++
        continue
    }

    # Local is different from remote; check if local is AHEAD (not diverged)
    # rev-list local..remote = commits remote has but local doesn't (should be 0 for clean ahead)
    $behind = (_git @('rev-list','--count',"${b}..${Remote}/${b}")).out.Trim()
    $ahead  = (_git @('rev-list','--count',"${Remote}/${b}..${b}")).out.Trim()

    if ($behind -ne '0') {
        # Diverged -- do NOT auto-push; surface for operator decision
        $skipped++
        if (-not $Quiet) { Write-Host "[!] $b DIVERGED (ahead=$ahead behind=$behind) -- skipping" }
        $details += @{ branch = $b; action = 'diverged_skip'; ahead = [int]$ahead; behind = [int]$behind }
        continue
    }

    if ($DryRun) {
        if (-not $Quiet) { Write-Host "[?] would push $b ($ahead ahead)" }
        $skipped++
        continue
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $push = _git @('push',$Remote,$b)
    $sw.Stop()
    $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    if ($push.rc -eq 0) {
        $pushed++
        if (-not $Quiet) { Write-Host "[+] pushed $b ($ahead commits, $($elapsed)s)" }
        $details += @{ branch = $b; action = 'pushed'; commits = [int]$ahead; elapsed_s = $elapsed; rc = 0 }
    } else {
        $failed++
        if (-not $Quiet) { Write-Host "[x] push failed $b rc=$($push.rc)" }
        $err = ($push.out -split "`n" | Select-Object -First 2) -join '; '
        $details += @{ branch = $b; action = 'push_failed'; rc = $push.rc; err = $err }
    }
}

$endTs = (Get-Date).ToUniversalTime().ToString('o')
Write-LogRow @{
    ts_utc_start  = $startTs
    ts_utc_end    = $endTs
    phase         = 'summary'
    branches_seen = $branches.Count
    pushed        = $pushed
    created       = $created
    skipped       = $skipped
    failed        = $failed
    details       = $details
    dry_run       = [bool]$DryRun
}

if (-not $Quiet) {
    Write-Host ("push-all-agent-branches :: seen={0} pushed={1} created={2} skipped={3} failed={4}" -f `
        $branches.Count, $pushed, $created, $skipped, $failed)
}
if ($failed -gt 0) { exit 1 } else { exit 0 }
