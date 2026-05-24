# Author: RKOJ-ELENO :: 2026-05-25
#
# Brain stale-claim scanner. Walks _shared-memory/knowledge/ and reports
# every "likely / probably / should be / may need / might be / defer to /
# next sweep / TODO / FIXME" hit so per-lane agents can audit + resolve.
#
# Usage:
#   .\brain-stale-claim-scan.ps1                    # scan all brain entries
#   .\brain-stale-claim-scan.ps1 -LaneFilter snap   # only entries matching slug or tag containing 'snap'
#   .\brain-stale-claim-scan.ps1 -MinHits 3         # only entries with >=3 hits (high-concentration)
#   .\brain-stale-claim-scan.ps1 -Json              # machine-readable output
#
# Per Bug #2 of memory-system add/fix broadcast 2026-05-25.

[CmdletBinding()]
param(
    [string]$LaneFilter = '',
    [int]$MinHits = 1,
    [switch]$Json,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'

$BrainDir = Join-Path $SanctumRoot '_shared-memory\knowledge'
if (-not (Test-Path $BrainDir)) {
    Write-Error "Brain dir not found: $BrainDir"
    exit 2
}

# Stale-claim markers. Each gets flagged; the operator/agent decides whether each hit is true staleness.
$Patterns = @(
    '\blikely\b',
    '\bprobably\b',
    '\bshould be\b',
    '\bshould have\b',
    '\bmay need\b',
    '\bmight be\b',
    '\bmight need\b',
    '\bdefer to\b',
    '\bnext sweep\b',
    '\bverify on next\b',
    '\bTODO\b',
    '\bFIXME\b',
    '\buntested\)',
    '\(untested\b'
)
$JoinedPattern = ($Patterns -join '|')

$skipNames = @('README.md', '_INDEX.md', '_TEMPLATE.md', 'CONTRIBUTING.md')

$results = @()

Get-ChildItem -Path $BrainDir -Filter '*.md' -File | ForEach-Object {
    $name = $_.Name
    if ($skipNames -contains $name) { return }

    if ($LaneFilter) {
        # Match if slug contains lane filter, OR file content has tag mentioning it
        $slugMatch = $name -like "*$LaneFilter*"
        if (-not $slugMatch) {
            # Try tag-line match — first 80 lines should cover the tags block
            $head = Get-Content $_.FullName -TotalCount 80 -ErrorAction SilentlyContinue
            $tagMatch = ($head -match "(?i)tags?:.*$LaneFilter") -ne $null
            if (-not $tagMatch) { return }
        }
    }

    $matches = Select-String -Path $_.FullName -Pattern $JoinedPattern -AllMatches -ErrorAction SilentlyContinue
    if ($matches.Count -lt $MinHits) { return }

    $hitLines = @()
    foreach ($m in $matches) {
        $marker = ($m.Matches | ForEach-Object { $_.Value }) -join ','
        $hitLines += [PSCustomObject]@{
            line   = $m.LineNumber
            marker = $marker
            text   = $m.Line.Trim().Substring(0, [Math]::Min(120, $m.Line.Trim().Length))
        }
    }

    $results += [PSCustomObject]@{
        file       = $name
        hit_count  = $matches.Count
        hits       = $hitLines
    }
}

$results = $results | Sort-Object hit_count -Descending

if ($Json) {
    $payload = [PSCustomObject]@{
        schema     = 'sanctum.brain-stale-claim-scan.v1'
        ts_utc     = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        lane_filter = $LaneFilter
        min_hits   = $MinHits
        brain_dir  = $BrainDir
        entry_count_scanned = ($results | Measure-Object).Count
        total_hits = ($results | Measure-Object hit_count -Sum).Sum
        entries    = $results
    }
    $payload | ConvertTo-Json -Depth 6
    return
}

# Human-readable output
Write-Host ''
Write-Host '=== Brain stale-claim scan ===' -ForegroundColor Cyan
Write-Host ("Brain dir : " + $BrainDir)
if ($LaneFilter) { Write-Host ("Lane filter: " + $LaneFilter) }
Write-Host ("Min hits  : " + $MinHits)
Write-Host ("Entries with >=$MinHits hits: " + ($results | Measure-Object).Count)
Write-Host ("Total hits: " + (($results | Measure-Object hit_count -Sum).Sum))
Write-Host ''

if (-not $results) {
    Write-Host 'No stale-claim hits found (under current filter).' -ForegroundColor Green
    return
}

foreach ($r in $results) {
    Write-Host ('--- ' + $r.file + ' (' + $r.hit_count + ' hit(s)) ---') -ForegroundColor Yellow
    foreach ($h in $r.hits) {
        $color = if ($h.marker -match 'TODO|FIXME|untested') { 'Red' } else { 'Gray' }
        Write-Host ('  L' + $h.line.ToString().PadLeft(4) + '  [' + $h.marker + ']  ' + $h.text) -ForegroundColor $color
    }
    Write-Host ''
}

Write-Host '=== Next steps (per Bug #2 of memory-system broadcast 2026-05-25) ===' -ForegroundColor Cyan
Write-Host '1. Read each flagged entry top-to-bottom.'
Write-Host '2. For each hit, ask: "is the claim still speculative, or has downstream evidence resolved it?"'
Write-Host '3. If resolved: ADD an "Update YYYY-MM-DD - resolved" block in-place (do NOT spawn a new entry).'
Write-Host '4. If still speculative: leave alone (genuine epistemic hedges are fine).'
Write-Host '5. After edits, bump the _INDEX.md row Updated date + add resolved tag if applicable.'
Write-Host ''
