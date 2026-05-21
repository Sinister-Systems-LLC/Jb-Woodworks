# Sinister Sanctum :: resume-point writer (v1.2 :: 2026-05-21)
# Operator: "i need all projects to resume where they left off and always
# ahve resume points." Writes a structured resume-point JSON at
# _shared-memory/resume-points/<project>/<UTC>.json with everything the
# next session needs to pick up cleanly + a bounded pre_warm_reads list
# so the new session loads only what's relevant, not the whole brain.
# Author: RKOJ-ELENO :: 2026-05-21
# v1.1: PROGRESS lookup tries display name ("Sinister X.md") as fallback when
#       AgentName arrived as a slug, AND inbox lookup slugifies AgentName (lower+dashes)
#       so "Sinister Sanctum" -> "sanctum" / "sinister-sanctum" works either way.
#       Was: progress_top3 came back empty when launcher passed slug. Fixed.
# v1.2: latestPlanDir now kebab-cases ProjectKey before regex + tries the
#       "sinister-" stripped variant. Was: ProjectKey='Sinister Sanctum'
#       matched no plan dirs (all kebab-cased like 'sanctum-coaudit-...').
#       Also: Resolve-InboxSlug known-prefix carve-out extended from
#       just 'sanctum' to forge/term/panel/kernel-apk/apk/freeze too.

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

function Resolve-ProgressPath {
    param([string]$Root, [string]$Name)
    if (-not $Name) { return (Join-Path $Root "_shared-memory\PROGRESS\test.md") }
    $candidates = @()
    $candidates += Join-Path $Root "_shared-memory\PROGRESS\$Name.md"
    if ($Name -notmatch '^[Ss]inister ') {
        $titled = ($Name -replace '-', ' ').Trim()
        $titled = (Get-Culture).TextInfo.ToTitleCase($titled.ToLower())
        $candidates += Join-Path $Root "_shared-memory\PROGRESS\Sinister $titled.md"
    }
    $candidates += Join-Path $Root "_shared-memory\PROGRESS\$($Name.ToLower()).md"
    $known = @{
        'sanctum'         = 'Sinister Sanctum.md'
        'forge'           = 'Sinister Forge.md'
        'panel'           = 'Sinister Panel.md'
        'kernel-apk'      = 'Sinister Kernel APK.md'
        'apk'             = 'Sinister Kernel APK.md'
        'term'            = 'Sinister Term.md'
        'sinister-term'   = 'Sinister Term.md'
        'snap-api'        = 'Sinister Snap API.md'
        'tiktok-api'      = 'Sinister TikTok API.md'
        'rkoj'            = 'rkoj-workstation.md'
        'rkoj-workstation'= 'rkoj-workstation.md'
    }
    $key = $Name.ToLower()
    if ($known.ContainsKey($key)) {
        $candidates += Join-Path $Root "_shared-memory\PROGRESS\$($known[$key])"
    }
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    return $candidates[0]
}

$progressPath = Resolve-ProgressPath -Root $SanctumRoot -Name $AgentName

$progressTop3 = @()
if (Test-Path $progressPath) {
    $progLines = Get-Content $progressPath -TotalCount 80 -ErrorAction SilentlyContinue
    $headings = @($progLines | Where-Object { $_ -match '^## \d{4}-' } | Select-Object -First 3)
    foreach ($h in $headings) { $progressTop3 += ($h -replace '^##\s*', '').Trim() }
}

$latestPlanDir = $null
$latestPlanArtifact = $null
$plansRoot = Join-Path $SanctumRoot '_shared-memory\plans'
if (Test-Path $plansRoot) {
    $projectPatterns = @()
    $projectPatterns += [regex]::Escape($ProjectKey)
    $projectKebab = $ProjectKey.Trim().ToLower() -replace '\s+', '-'
    if ($projectKebab -ne $ProjectKey.ToLower()) {
        $projectPatterns += [regex]::Escape($projectKebab)
    }
    if ($projectKebab -match '^sinister-(.+)$') {
        $projectPatterns += [regex]::Escape($matches[1])
    }
    $dotted = $ProjectKey -replace '-', '.'
    if ($dotted -ne $ProjectKey) { $projectPatterns += [regex]::Escape($dotted) }
    $combinedPattern = '(?i)(' + (($projectPatterns | Select-Object -Unique) -join '|') + ')'

    $candidate = Get-ChildItem $plansRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match $combinedPattern } |
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

function Resolve-InboxSlug {
    param([string]$Name)
    if (-not $Name) { return 'test' }
    $s = $Name.Trim().ToLower() -replace '\s+', '-'
    $sinisterShortSlugs = @('sanctum','forge','term','panel','kernel-apk','apk','freeze','vault','os')
    if ($s -match '^sinister-(.+)$' -and $matches[1] -in $sinisterShortSlugs) {
        return $matches[1]
    }
    return $s
}

$inboxSlug = Resolve-InboxSlug -Name $AgentName
$inboxPath = Join-Path $SanctumRoot "_shared-memory\inbox\$inboxSlug"
$inboxUnread = 0
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
