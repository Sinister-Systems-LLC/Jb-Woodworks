# Author: RKOJ-ELENO :: 2026-05-23
# Sanctum :: clone-missing-sources.ps1
#
# Iterates projects.json and clones any project whose `root` is missing but has
# a `github` remote. Skips projects without a github remote or projects already
# present. Designed for fresh-checkout operators (Leo etc.) who pull the Sanctum
# umbrella but don't yet have the per-project sub-repos.
#
# Auth: uses whatever git auth the operator has configured (SSH key preferred,
# https + GH_TOKEN works too). If clone fails, surface the error + move on.
#
# Modes:
#   -DryRun           # show what would clone, don't actually clone
#   -Only <key>       # clone just one project by key
#   -Verbose          # extra detail
#
# Smoke test: .\clone-missing-sources.ps1 -DryRun

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Only = '',
    [switch]$DryRun
)

$projectsFile = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
if (-not (Test-Path $projectsFile)) {
    Write-Error "projects.json not found at $projectsFile"
    exit 2
}

# Read projects.json (tolerant of BOM)
$raw = [System.IO.File]::ReadAllText($projectsFile)
# Strip UTF-8 BOM if present
if ($raw.Length -gt 0 -and [int]$raw[0] -eq 0xFEFF) { $raw = $raw.Substring(1) }
$proj = $raw | ConvertFrom-Json

$candidates = @()
foreach ($p in $proj.projects) {
    if (-not $p.github -or -not $p.root) { continue }
    if ($Only -and $p.key -ne $Only) { continue }
    # Skip the umbrella Sanctum repo itself
    if ($p.root -ieq $SanctumRoot) { continue }
    # Skip if root exists with .git (standalone clone)
    if (Test-Path (Join-Path $p.root '.git')) { continue }
    # Skip if root exists with substantive content (integrated into monorepo)
    # Threshold: any file or subdir present = integrated, not missing.
    if (Test-Path $p.root) {
        $hasContent = (Get-ChildItem $p.root -Force -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($hasContent) { continue }
    }
    # Genuinely missing: dir doesn't exist OR is empty
    $candidates += $p
}

if ($candidates.Count -eq 0) {
    Write-Host "[clone-missing-sources] nothing to clone -- every project with a github remote either has its own .git/ OR has content already (integrated into monorepo)" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Missing-source projects: $($candidates.Count)" -ForegroundColor Yellow
foreach ($p in $candidates) {
    Write-Host "  - $($p.key)" -ForegroundColor Yellow
    Write-Host "      remote: git@github.com:$($p.github).git" -ForegroundColor DarkGray
    Write-Host "      target: $($p.root)" -ForegroundColor DarkGray
}
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] no clones performed. Run without -DryRun to clone." -ForegroundColor Cyan
    exit 0
}

$cloned = 0
$failed = 0
foreach ($p in $candidates) {
    $remoteSsh = "git@github.com:$($p.github).git"
    $remoteHttps = "https://github.com/$($p.github).git"
    # Ensure parent dir exists
    $parent = Split-Path $p.root -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }

    Write-Host "[$($p.key)] cloning $remoteSsh -> $($p.root)" -ForegroundColor Cyan
    & git clone $remoteSsh "$($p.root)" 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    if ($LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $p.root '.git'))) {
        Write-Host "  [OK] $($p.key) cloned" -ForegroundColor Green
        $cloned++
        continue
    }
    # Fall back to https
    Write-Host "  [INFO] SSH clone failed, retrying with HTTPS" -ForegroundColor Yellow
    & git clone $remoteHttps "$($p.root)" 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    if ($LASTEXITCODE -eq 0 -and (Test-Path (Join-Path $p.root '.git'))) {
        Write-Host "  [OK] $($p.key) cloned (via HTTPS)" -ForegroundColor Green
        $cloned++
    } else {
        Write-Host "  [FAIL] $($p.key) clone failed (both SSH and HTTPS)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "Summary: $cloned cloned / $failed failed (of $($candidates.Count) candidates)" -ForegroundColor $(if ($failed -eq 0) { 'Green' } else { 'Yellow' })

if ($failed -gt 0) {
    Write-Host ""
    Write-Host "Common fixes for failures:" -ForegroundColor DarkGray
    Write-Host "  - SSH key not set up: ssh-keygen -t ed25519 -C your@email.com   then add ~/.ssh/id_ed25519.pub to https://github.com/settings/keys"
    Write-Host "  - HTTPS auth: set `$env:GH_TOKEN to a personal access token with `repo` scope"
    Write-Host "  - Repo access: confirm the org has invited your GitHub account to Sinister-Systems-LLC"
    exit 1
}
exit 0
