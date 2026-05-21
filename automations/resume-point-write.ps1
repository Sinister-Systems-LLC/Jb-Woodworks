# Sinister Sanctum :: resume-point writer (v1 :: 2026-05-21)
# Operator: "i need all projects to resume where they left off and always
# ahve resume points." Writes a structured resume-point JSON at
# _shared-memory/resume-points/<project>/<UTC>.json with everything the
# next session needs to pick up cleanly + a bounded pre_warm_reads list
# so the new session loads only what's relevant, not the whole brain.
# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

param(
    [Parameter(Mandatory)][string]$SanctumRoot,
    [Parameter(Mandatory)][string]$ProjectKey,
    [string]$AgentName = '',
    [string]$FocusIntent = '',
    [string]$Mode = '',
    [int]$KeepLast = 20
)

if (-not (Test-Path $SanctumRoot)) {
    Write-Host "[resume-point-write] SanctumRoot not found: $SanctumRoot" -ForegroundColor Red
    exit 1
}

$rpDir = Join-Path $SanctumRoot "_shared-memory\resume-points\$ProjectKey"
New-Item -ItemType Directory -Force -Path $rpDir | Out-Null

$stamp = (Get-Date -Format 'yyyy-MM-ddTHHmmssZ')
$rpFile = Join-Path $rpDir "$stamp.json"

$branch = ''
$head = ''
$headMsg = ''
$recentCommits = @()
try {
    Push-Location $SanctumRoot
    $branch = (& git branch --show-current 2>$null)
    if ($branch) { $branch = $branch.Trim() }
    $head = (& git rev-parse HEAD 2>$null)
    if ($head) { $head = $head.Trim() }
    $headMsg = (& git log -1 --format=%s 2>$null)
    if ($headMsg) { $headMsg = $headMsg.Trim() }
    $recentCommits = @(& git log --oneline -10 2>$null)
    Pop-Location
} catch { Pop-Location -ErrorAction SilentlyContinue }

$progressTop3 = @()
$progressPath = if ($AgentName) {
    Join-Path $SanctumRoot "_shared-memory\PROGRESS\$AgentName.md"
} else {
    Join-Path $SanctumRoot "_shared-memory\PROGRESS\test.md"
}
if (Test-Path $progressPath) {
    $progLines = Get-Content $progressPath -TotalCount 80 -ErrorAction SilentlyContinue
    $headings = @($progLines | Where-Object { $_ -match '^## \d{4}-' } | Select-Object -First 3)
    foreach ($h in $headings) { $progressTop3 += ($h -replace '^##\s*', '').Trim() }
}

$latestPlanDir = $null
$latestPlanArtifact = $null
$plansRoot = Join-Path $SanctumRoot '_shared-memory\plans'
if (Test-Path $plansRoot) {
    $candidate = Get-ChildItem $plansRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match $ProjectKey -or $_.Name -match ($ProjectKey -replace '-', '.') } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($candidate) {
        $latestPlanDir = $candidate.FullName
        $art = Get-ChildItem $candidate.FullName -Filter '*.md' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($art) { $latestPlanArtifact = $art.FullName }
    }
}

$inboxUnread = 0
$inboxPath = if ($AgentName) {
    Join-Path $SanctumRoot "_shared-memory\inbox\$($AgentName.ToLower())"
} else {
    Join-Path $SanctumRoot "_shared-memory\inbox\test"
}
if (Test-Path $inboxPath) {
    $inboxUnread = @(Get-ChildItem $inboxPath -Filter '*.json' -ErrorAction SilentlyContinue).Count
}

$lastTouched = @()
try {
    $cutoff = (Get-Date).AddHours(-24)
    $lastTouched = @(Get-ChildItem $SanctumRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.LastWriteTime -gt $cutoff -and
            $_.FullName -notmatch '\\\.git\\' -and
            $_.FullName -notmatch '\\node_modules\\' -and
            $_.FullName -notmatch '\\\.venv\\' -and
            $_.FullName -notmatch '\\backups\\' -and
            $_.FullName -notmatch '\\dist\\'
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 5 |
        ForEach-Object { $_.FullName.Substring($SanctumRoot.Length + 1) })
} catch { }

$preWarm = @(
    $progressPath,
    $latestPlanArtifact,
    (Join-Path $SanctumRoot '_shared-memory\MASTER-PLAN.md'),
    (Join-Path $SanctumRoot 'automations\session-contracts.md')
) | Where-Object { $_ -and (Test-Path $_) }

$rp = [ordered]@{
    schema_version = 'sinister.resume-point.v1'
    ts_utc = ([datetime]::UtcNow).ToString('o')
    project = $ProjectKey
    agent_name = $AgentName
    mode = $Mode
    focus_intent = $FocusIntent
    git = [ordered]@{
        branch = $branch
        head = $head
        head_msg = $headMsg
        recent_commits = @($recentCommits)
    }
    progress_top3 = @($progressTop3)
    latest_plan = [ordered]@{
        dir = $latestPlanDir
        artifact = $latestPlanArtifact
    }
    inbox_unread_count = $inboxUnread
    last_5_files_touched_24h = @($lastTouched)
    pre_warm_reads = @($preWarm)
}

($rp | ConvertTo-Json -Depth 6) | Out-File $rpFile -Encoding utf8
Write-Host "[resume-point-write] saved: $rpFile" -ForegroundColor Green

try {
    $all = @(Get-ChildItem $rpDir -Filter '*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
    if ($all.Count -gt $KeepLast) {
        $toRemove = $all | Select-Object -Skip $KeepLast
        foreach ($r in $toRemove) {
            Remove-Item $r.FullName -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[resume-point-write] pruned $($toRemove.Count) old resume-points (keep $KeepLast)" -ForegroundColor DarkGray
    }
} catch { }
