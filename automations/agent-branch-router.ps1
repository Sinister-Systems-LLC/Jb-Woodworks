# agent-branch-router.ps1 :: per-spawn branch convention enforcer
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25 ~00:50Z: every agent uses a branch
# named per the canonical convention so parallel sessions never collide
# and all agents know what to do.
#
# Canonical format:
#   agent/<project-key>/<short-topic>-<utc-date>
#
# Modes:
#   (default)   -- create-or-switch to canonical branch + push if behind
#   -DryRun     -- print the intended commands without executing
#   -CheckOnly  -- detect WRONG branch (e.g. accidentally on main), offer
#                  to switch
#
# Composes with:
#   docs/BRANCH-CONVENTION.md
#   automations/sanctum-push-policy.ps1   (pre-push guard)
#   _shared-memory/knowledge/branch-convention-2026-05-25.md

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectKey,

    [string]$Topic = 'work',

    [string]$UtcDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd'),

    [string]$RepoRoot = '',

    [switch]$DryRun,

    [switch]$CheckOnly,

    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Continue'

function Get-Projects {
    $registry = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
    if (-not (Test-Path $registry)) {
        Write-Host "FAIL: projects.json not found at $registry" -ForegroundColor Red
        exit 2
    }
    return (Get-Content -LiteralPath $registry -Raw | ConvertFrom-Json).projects
}

function Sanitize-Topic {
    param([string]$t)
    $clean = $t.ToLowerInvariant()
    $clean = $clean -replace '[^a-z0-9-]', '-'
    $clean = $clean -replace '-+', '-'
    $clean = $clean.Trim('-')
    if ($clean.Length -gt 30) { $clean = $clean.Substring(0, 30).TrimEnd('-') }
    if (-not $clean) { $clean = 'work' }
    return $clean
}

function Resolve-Project {
    param([string]$Key)
    $projects = Get-Projects
    foreach ($p in $projects) {
        if ($p.key -eq $Key) { return $p }
    }
    return $null
}

function Get-CanonicalPrefix {
    param($Project)
    if ($Project.branch_prefix) { return $Project.branch_prefix.TrimEnd('/') + '/' }
    return "agent/$($Project.key)/"
}

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
    $out = & git -C $script:RepoPath @Args 2>&1
    return @{ exit = $LASTEXITCODE; output = ($out -join "`n") }
}

# ---- resolve project ----
$proj = Resolve-Project -Key $ProjectKey
if (-not $proj) {
    Write-Host "FAIL: project key '$ProjectKey' not found in projects.json" -ForegroundColor Red
    exit 2
}

# ---- resolve repo root ----
if (-not $RepoRoot) {
    $RepoRoot = $proj.root
}
# If the project root has no .git, walk up to find one (e.g. projects/foo/ -> Sanctum root)
$script:RepoPath = $RepoRoot
$walker = $RepoRoot
while ($walker -and -not (Test-Path (Join-Path $walker '.git'))) {
    $parent = Split-Path -Parent $walker
    if (-not $parent -or $parent -eq $walker) { break }
    $walker = $parent
}
if ($walker -and (Test-Path (Join-Path $walker '.git'))) {
    $script:RepoPath = $walker
} else {
    Write-Host "FAIL: no .git found at or above $RepoRoot" -ForegroundColor Red
    exit 2
}

# ---- compose branch name ----
$prefix = Get-CanonicalPrefix -Project $proj
$cleanTopic = Sanitize-Topic -t $Topic
$branchName = "${prefix}${cleanTopic}-${UtcDate}"

Write-Host ""
Write-Host "agent-branch-router :: key=$ProjectKey topic=$cleanTopic date=$UtcDate" -ForegroundColor Magenta
Write-Host "  repo=$($script:RepoPath)" -ForegroundColor DarkGray
Write-Host "  target=$branchName" -ForegroundColor DarkGray

# ---- detect current branch ----
$cur = Invoke-Git rev-parse --abbrev-ref HEAD
if ($cur.exit -ne 0) {
    Write-Host "FAIL: git rev-parse failed: $($cur.output)" -ForegroundColor Red
    exit 2
}
$current = $cur.output.Trim()
Write-Host "  current=$current" -ForegroundColor DarkGray

# ---- WRONG-branch detection ----
$onMain = ($current -eq 'main' -or $current -eq 'master')
$onValidAgent = ($current -like "$prefix*")

if ($CheckOnly) {
    if ($onValidAgent) {
        Write-Host "OK: already on canonical agent branch ($current)" -ForegroundColor Green
        exit 0
    }
    if ($onMain) {
        Write-Host "WARN: on '$current' -- should be on agent branch ($branchName)" -ForegroundColor Yellow
        Write-Host "      Run without -CheckOnly to switch automatically." -ForegroundColor DarkGray
        exit 1
    }
    Write-Host "WARN: current branch '$current' doesn't match prefix '$prefix'" -ForegroundColor Yellow
    exit 1
}

# ---- create or switch ----
if ($current -eq $branchName) {
    Write-Host "OK: already on target branch ($branchName)" -ForegroundColor Green
} elseif ($onValidAgent -and -not $onMain) {
    # Operator/agent already on a different canonical agent branch for this project. Honor it; don't churn.
    Write-Host "NOTE: keeping current valid agent branch ($current) instead of creating new ($branchName)" -ForegroundColor Cyan
    $branchName = $current
} else {
    # Check if target branch already exists
    $exists = Invoke-Git rev-parse --verify --quiet $branchName
    $cmdDesc = if ($exists.exit -eq 0) { "switch to existing $branchName" } else { "create + switch to $branchName" }
    if ($DryRun) {
        Write-Host "DRY-RUN: would $cmdDesc" -ForegroundColor Yellow
    } else {
        if ($exists.exit -eq 0) {
            $sw = Invoke-Git checkout $branchName
        } else {
            $sw = Invoke-Git checkout -b $branchName
        }
        if ($sw.exit -ne 0) {
            Write-Host "FAIL: checkout failed: $($sw.output.Split([Environment]::NewLine)[0])" -ForegroundColor Red
            exit 2
        }
        Write-Host "OK: switched to $branchName" -ForegroundColor Green
    }
}

# ---- pre-push policy guard ----
$policyScript = Join-Path $SanctumRoot 'automations\sanctum-push-policy.ps1'
if (Test-Path $policyScript) {
    if ($DryRun) {
        Write-Host "DRY-RUN: would run sanctum-push-policy -Action CheckPath -Path $($script:RepoPath)" -ForegroundColor Yellow
    } else {
        & $policyScript -Action CheckPath -Path $script:RepoPath | Out-Host
        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARN: push-policy guard tripped; skipping push step." -ForegroundColor Yellow
            exit $LASTEXITCODE
        }
    }
} else {
    Write-Host "WARN: sanctum-push-policy.ps1 not found; skipping policy guard" -ForegroundColor Yellow
}

# ---- push if commits exist + upstream not in sync ----
if ($DryRun) {
    Write-Host "DRY-RUN: would push $branchName to origin (with -u on first push)" -ForegroundColor Yellow
    exit 0
}

$upstream = Invoke-Git rev-parse --abbrev-ref "$branchName@{upstream}"
if ($upstream.exit -ne 0) {
    Write-Host "NOTE: no upstream set; would use -u on first push (deferring to sanctum-auto-push daemon)" -ForegroundColor Cyan
} else {
    $ahead = Invoke-Git rev-list "origin/$branchName..HEAD" --count
    if ($ahead.exit -eq 0 -and [int]($ahead.output.Trim()) -gt 0) {
        Write-Host "NOTE: $($ahead.output.Trim()) commit(s) ahead of origin; deferring push to sanctum-auto-push daemon" -ForegroundColor Cyan
    }
}

exit 0
