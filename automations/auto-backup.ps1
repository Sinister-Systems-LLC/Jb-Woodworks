# Sinister Sanctum :: auto-backup (v1 :: 2026-05-21)
#
# Snapshots master-lane state to D:\Sinister Sanctum\backups\<YYYY-MM-DD-HHMM>\.
# Runs at most once per 24h (sentinel file gates re-runs).
#
# Fired silently by bootstrap-portability.ps1 on every session start if the
# last backup is stale. Operator directive: "make sure auto backup works on
# the machine the sanctum is on every 24 hours to a folder in the sanctum
# that is not pushed to github called bakcups. start this from the first bat
# file run and make sure there are no popups."
#
# What gets backed up:
#   * _shared-memory/ (PROGRESS + plans + knowledge + cross-agent + inbox)
#   * automations/ (launcher + bootstrap + scripts)
#   * docs/ + SESSION-START/ + SANCTUM.md + CLAUDE.md + DIRECTIVES
#   * .gitignore + .github/workflows/
#
# What is SKIPPED:
#   * _vault/ (operator-private secrets)
#   * backups/ (recursive - no backing up backups)
#   * projects/*/source/ (junctions - source lives in sibling repos)
#   * automations/window-manager/dist/ + .venv/ (rebuilds)
#   * node_modules/ everywhere
#   * .git/ (we use commits for source-history; backup is a parallel safety net)
#
# Backup pruning lives in auto-cleanup.ps1 (deletes backup dirs >7 days old).
#
# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

param(
    [string]$SanctumRoot = '',
    [switch]$Force,
    [switch]$Quiet
)

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}
if (-not (Test-Path $SanctumRoot)) {
    if (-not $Quiet) { Write-Host "[auto-backup] SanctumRoot not found: $SanctumRoot" -ForegroundColor Yellow }
    exit 1
}

$backupsRoot = Join-Path $SanctumRoot 'backups'
$sentinelFile = Join-Path $backupsRoot '.last-backup-utc'
New-Item -ItemType Directory -Force -Path $backupsRoot | Out-Null

# Gate: skip if last backup <24h ago and not -Force
if ((Test-Path $sentinelFile) -and -not $Force) {
    try {
        $lastUtc = [datetime]::Parse((Get-Content $sentinelFile -Raw).Trim())
        $ageHours = (([datetime]::UtcNow) - $lastUtc).TotalHours
        if ($ageHours -lt 24) {
            if (-not $Quiet) { Write-Host ("[auto-backup] skip (last backup {0:N1}h ago, < 24h gate)" -f $ageHours) -ForegroundColor DarkGray }
            exit 0
        }
    } catch { }
}

$stamp = (Get-Date -Format 'yyyy-MM-dd-HHmm')
$snapDir = Join-Path $backupsRoot $stamp
New-Item -ItemType Directory -Force -Path $snapDir | Out-Null

if (-not $Quiet) { Write-Host "[auto-backup] snapshot -> $snapDir" -ForegroundColor Cyan }

# robocopy is the right tool for Windows file mirroring with exclusions.
# /MIR mirrors source to dest; we use /XD to exclude dirs.
$included = @(
    '_shared-memory',
    'automations',
    'docs',
    'SESSION-START',
    'projects'
)
$excludedDirs = @(
    '.git',
    'backups',
    '_vault',
    'node_modules',
    '.venv',
    '__pycache__',
    'dist',
    '.next',
    'source'   # junctions inside projects/<proj>/source/
)
$excludedFiles = @(
    '*.pyc',
    '*.log',
    '.DS_Store'
)

foreach ($subdir in $included) {
    $src = Join-Path $SanctumRoot $subdir
    if (-not (Test-Path $src)) { continue }
    $dst = Join-Path $snapDir $subdir
    $xdArgs = @()
    foreach ($x in $excludedDirs) { $xdArgs += '/XD'; $xdArgs += $x }
    $xfArgs = @()
    foreach ($x in $excludedFiles) { $xfArgs += '/XF'; $xfArgs += $x }
    # /MIR = mirror, /R:1 retry 1, /W:1 wait 1, /NJH /NJS /NDL /NP suppress noise
    & robocopy.exe $src $dst /MIR /R:1 /W:1 /NJH /NJS /NDL /NP /NFL @xdArgs @xfArgs | Out-Null
}

# Copy top-level dotted files (.gitignore + LICENSE + READMEs)
$topFiles = @('.gitignore', 'LICENSE', 'README.md', 'SANCTUM.md', 'CLAUDE.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'INDEX.md', 'LICENSE-CANDIDATES.md', 'PARALLEL-AGENT-COORDINATION.md')
foreach ($f in $topFiles) {
    $src = Join-Path $SanctumRoot $f
    if (Test-Path $src) { Copy-Item -Path $src -Destination $snapDir -Force -ErrorAction SilentlyContinue }
}

# Snapshot a manifest of git state
try {
    $manifest = @{
        utc        = ([datetime]::UtcNow).ToString('o')
        sanctum    = $SanctumRoot
        branch     = (& git -C $SanctumRoot branch --show-current 2>$null).Trim()
        head       = (& git -C $SanctumRoot rev-parse HEAD 2>$null).Trim()
        head_msg   = (& git -C $SanctumRoot log -1 --format=%s 2>$null).Trim()
        excluded   = $excludedDirs
        included   = $included
    }
    ($manifest | ConvertTo-Json -Depth 4) | Out-File (Join-Path $snapDir 'BACKUP-MANIFEST.json') -Encoding utf8
} catch { }

# Update sentinel
([datetime]::UtcNow).ToString('o') | Out-File $sentinelFile -Encoding utf8 -NoNewline

# Total size
try {
    $totalMb = [math]::Round(((Get-ChildItem $snapDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB), 1)
    if (-not $Quiet) { Write-Host ("[auto-backup] OK ({0} MB)" -f $totalMb) -ForegroundColor Green }
} catch { }
