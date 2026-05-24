# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: brain-archive-orphans :: move on-disk-but-not-indexed brain entries
#
# brain-index-orphan-check.ps1 reports 33 orphan files (on disk in
# _shared-memory/knowledge/ but NOT indexed in _INDEX.md). These are
# typically per-lane entries the lane shipped without updating master index.
#
# This script moves them to _shared-memory/knowledge/_archive/ so:
#   1. on_disk_count drops
#   2. Lanes can still find them (in _archive/) if they want to re-index
#   3. Future Rule 7.5 audits stay clean
#
# Conservative: -DryRun by default; requires -Yes to apply.
# Reversible: `git mv` the file back from _archive/ + add row to _INDEX.md.
#
# Smoke: .\brain-archive-orphans.ps1 -DryRun

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Yes,
    [switch]$DryRun
)

$knowledgeDir = Join-Path $SanctumRoot '_shared-memory\knowledge'
$archiveDir = Join-Path $knowledgeDir '_archive'

# Get orphan list from brain-index-orphan-check.ps1 -Json
$checkScript = Join-Path $SanctumRoot 'automations\brain-index-orphan-check.ps1'
if (-not (Test-Path $checkScript)) {
    Write-Error "brain-index-orphan-check.ps1 not found at $checkScript"
    exit 2
}
$jsonOut = & $checkScript -SanctumRoot $SanctumRoot -Json 2>$null | Out-String
$result = $jsonOut | ConvertFrom-Json
$orphans = $result.orphans
if (-not $orphans -or $orphans.Count -eq 0) {
    Write-Host "[brain-archive-orphans] no orphans to archive" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Orphans on disk but not in _INDEX.md: $($orphans.Count)" -ForegroundColor Yellow
foreach ($o in $orphans) { Write-Host "  $o" -ForegroundColor DarkGray }
Write-Host ""

if ($DryRun -and -not $Yes) {
    Write-Host "[DRY RUN] would move each to $archiveDir\<slug>.md" -ForegroundColor Cyan
    exit 0
}

if (-not $Yes) {
    $ans = Read-Host "Move all $($orphans.Count) orphans to _archive/ ? [y/N]"
    if ($ans -notmatch '^[yY]') { Write-Host "Aborted."; exit 0 }
}

if (-not (Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
}

$moved = 0
$failed = 0
foreach ($slug in $orphans) {
    $src = Join-Path $knowledgeDir "$slug.md"
    $dst = Join-Path $archiveDir "$slug.md"
    if (-not (Test-Path $src)) {
        Write-Host "  [SKIP] $slug (file missing -- odd)" -ForegroundColor Yellow
        continue
    }
    if (Test-Path $dst) {
        Write-Host "  [SKIP] $slug (already in archive)" -ForegroundColor Yellow
        continue
    }
    try {
        Move-Item -Path $src -Destination $dst -ErrorAction Stop
        Write-Host "  [OK]   $slug -> _archive/" -ForegroundColor Green
        $moved++
    } catch {
        Write-Host "  [FAIL] $slug : $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "Summary: $moved archived / $failed failed (of $($orphans.Count) candidates)" -ForegroundColor $(if ($failed -eq 0) { 'Green' } else { 'Yellow' })

if ($moved -gt 0) {
    Write-Host ""
    Write-Host "Recommended next steps:" -ForegroundColor DarkGray
    Write-Host "  1. Re-run sinister-doctor to confirm Rule 7.5 status now reflects the cleanup"
    Write-Host "  2. git add -A _shared-memory/knowledge/_archive/ ; git commit -m 'brain: archive orphans'"
    Write-Host "  3. Notify lanes via inbox/[lane]/ if they should re-index any of the archived entries"
}
exit 0
