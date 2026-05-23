# Author: RKOJ-ELENO :: 2026-05-23
# Sanctum :: brain index orphan check (B.10 of sanctum-complete-and-expand master plan)
#
# Verifies every _shared-memory/knowledge/*.md file is indexed as a row in
# _shared-memory/knowledge/_INDEX.md. Reports on-disk-orphans (files that exist
# but have no _INDEX row). Exits 0 = clean, 1 = orphans found.
#
# Lane responsibility: per-lane brain entries should be indexed by the lane that
# added them. Master sanctum runs this audit periodically + drops [INFO] inbox
# messages to lanes with orphans.
#
# Smoke test: .\brain-index-orphan-check.ps1 -Verbose

[CmdletBinding()]
param(
    [string]$SanctumRoot = "D:\Sinister Sanctum",
    [switch]$Json
)

$knowledgeDir = Join-Path $SanctumRoot "_shared-memory\knowledge"
$indexFile = Join-Path $knowledgeDir "_INDEX.md"

if (-not (Test-Path $indexFile)) {
    Write-Error "_INDEX.md not found at $indexFile"
    exit 2
}

# Meta files to exclude from orphan list
$metaFiles = @('README', '_INDEX', '_TEMPLATE')

# On-disk .md files
$diskSlugs = Get-ChildItem $knowledgeDir -Filter '*.md' -File |
    ForEach-Object { $_.BaseName } |
    Where-Object { $_ -notin $metaFiles } |
    Sort-Object -Unique

# Indexed slugs (table row format: `| slug | title | ...`)
$indexContent = Get-Content $indexFile -Raw
$indexedSlugs = [regex]::Matches($indexContent, '(?m)^\|\s*([a-z][a-z0-9._-]+)\s*\|') |
    ForEach-Object { $_.Groups[1].Value } |
    Sort-Object -Unique

$orphans = $diskSlugs | Where-Object { $_ -notin $indexedSlugs }
$missingFiles = $indexedSlugs | Where-Object { $_ -notin $diskSlugs }

if ($Json) {
    $result = [ordered]@{
        ts_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        on_disk_count = $diskSlugs.Count
        indexed_count = $indexedSlugs.Count
        orphan_count = $orphans.Count
        missing_file_count = $missingFiles.Count
        orphans = $orphans
        missing_files = $missingFiles
        rule_7_5_brain_ceiling = 150
        rule_7_5_status = if ($diskSlugs.Count -ge 150) { "VIOLATED" } elseif ($diskSlugs.Count -ge 120) { "APPROACHING" } else { "OK" }
    }
    $result | ConvertTo-Json -Depth 5
} else {
    Write-Host "Brain index hygiene check ($($diskSlugs.Count) on-disk / $($indexedSlugs.Count) indexed)"
    Write-Host ""
    if ($orphans.Count -gt 0) {
        Write-Host "ORPHANS ($($orphans.Count)) - on disk, not in _INDEX.md:" -ForegroundColor Yellow
        foreach ($o in $orphans) { Write-Host "  $o" -ForegroundColor Yellow }
        Write-Host ""
    }
    if ($missingFiles.Count -gt 0) {
        Write-Host "MISSING FILES ($($missingFiles.Count)) - indexed but no .md on disk:" -ForegroundColor Red
        foreach ($m in $missingFiles) { Write-Host "  $m" -ForegroundColor Red }
        Write-Host ""
    }
    if ($orphans.Count -eq 0 -and $missingFiles.Count -eq 0) {
        Write-Host "CLEAN - every on-disk brain entry is indexed and vice versa." -ForegroundColor Green
    }
    # Rule 7.5 ceiling check
    Write-Host ""
    if ($diskSlugs.Count -ge 150) {
        Write-Host "Rule 7.5 brain-row ceiling: VIOLATED ($($diskSlugs.Count) at or above 150). STOP expanding; consolidate first." -ForegroundColor Red
    } elseif ($diskSlugs.Count -ge 120) {
        Write-Host "Rule 7.5 brain-row ceiling: APPROACHING ($($diskSlugs.Count) / 150)" -ForegroundColor Yellow
    } else {
        Write-Host "Rule 7.5 brain-row ceiling: OK ($($diskSlugs.Count) / 150)" -ForegroundColor Green
    }
}

if ($orphans.Count -gt 0 -or $missingFiles.Count -gt 0) { exit 1 } else { exit 0 }
