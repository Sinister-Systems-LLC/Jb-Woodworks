# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: resume-point free-text search index builder (C.11 of master plan)
#
# Expands the launcher's free-text resume-point search to also index:
#   - PROGRESS log entries (per-lane, last 90 days)
#   - Recent git commit messages (last 200 commits)
#   - Brain entry tags (from _INDEX.md)
#
# Output: _shared-memory/resume-search-index.json — a flat list of
# {source, lane, key, ts, snippet} entries the launcher Pick-ResumeRow can
# score against the operator's free-text query.
#
# Smoke test: .\index-resume-search.ps1 -Verbose
# Operator usage: re-built nightly via SinisterCustodian or on-demand

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$ProgressMaxAgeDays = 90,
    [int]$CommitsLimit = 200
)

$outPath = Join-Path $SanctumRoot '_shared-memory\resume-search-index.json'

$entries = New-Object System.Collections.ArrayList

# --- Source A: resume-points (existing source; for completeness) ---
$rpDir = Join-Path $SanctumRoot '_shared-memory\resume-points'
if (Test-Path $rpDir) {
    Get-ChildItem $rpDir -Directory | ForEach-Object {
        $lane = $_.Name
        Get-ChildItem $_.FullName -Filter '*.json' -File -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $j = Get-Content $_.FullName -Raw | ConvertFrom-Json
                $snippet = ($j.focus_intent + ' ' + ($j.git.head_msg) + ' ' + (($j.progress_top3 -join ' ')))
                if ($snippet.Length -gt 400) { $snippet = $snippet.Substring(0, 400) }
                [void]$entries.Add([ordered]@{
                    source = 'resume-point'
                    lane = $lane
                    key = $_.BaseName
                    ts = $j.ts_utc
                    snippet = $snippet
                    path = $_.FullName
                })
            } catch { }
        }
    }
}

# --- Source B: PROGRESS log entries (last N days) ---
$progressDir = Join-Path $SanctumRoot '_shared-memory\PROGRESS'
$cutoff = (Get-Date).AddDays(-$ProgressMaxAgeDays)
if (Test-Path $progressDir) {
    Get-ChildItem $progressDir -Filter '*.md' -File | ForEach-Object {
        $lane = $_.BaseName
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { return }
        # Split on `## ` (markdown level-2 headers = per-turn entries, most-recent first)
        $sections = $content -split "(?m)^## " | Where-Object { $_ }
        foreach ($s in $sections) {
            $firstLine = ($s -split "`n", 2)[0].Trim()
            # Try to parse ISO date from header like "2026-05-24 07:55Z — ..."
            $ts = $null
            if ($firstLine -match '(\d{4}-\d{2}-\d{2}[\sT]\d{2}:?\d{2}Z?)') {
                try { $ts = [datetime]::Parse($matches[1].Replace(' ', 'T').TrimEnd('Z')).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') } catch { }
            }
            # Cut snippet to first 400 chars
            $snippet = $s.Substring(0, [Math]::Min(400, $s.Length)).Replace("`r","").Replace("`n"," ")
            [void]$entries.Add([ordered]@{
                source = 'progress'
                lane = $lane
                key = $firstLine.Substring(0, [Math]::Min(80, $firstLine.Length))
                ts = $ts
                snippet = $snippet
                path = $_.FullName
            })
        }
    }
}

# --- Source C: recent git commits ---
Push-Location $SanctumRoot
$gitLog = & git log --oneline -$CommitsLimit --pretty=format:"%H|%aI|%s" 2>$null
Pop-Location
if ($gitLog) {
    foreach ($line in @($gitLog)) {
        $parts = $line -split '\|', 3
        if ($parts.Count -lt 3) { continue }
        [void]$entries.Add([ordered]@{
            source = 'commit'
            lane = if ($parts[2] -match '^(\w+):') { $matches[1] } else { 'unknown' }
            key = $parts[0].Substring(0, 7)
            ts = $parts[1]
            snippet = $parts[2]
            path = $parts[0]
        })
    }
}

# --- Source D: brain entry tags from _INDEX.md ---
$brainIndex = Join-Path $SanctumRoot '_shared-memory\knowledge\_INDEX.md'
if (Test-Path $brainIndex) {
    $brainLines = Get-Content $brainIndex
    foreach ($line in $brainLines) {
        if ($line -notmatch '^\|\s*([a-z][a-z0-9._-]+)\s*\|') { continue }
        $slug = $matches[1]
        if ($slug -eq 'slug') { continue }  # header row
        # Extract status + tags columns (positions 3 + 4 in the 6-col table)
        $cols = $line -split '\|'
        if ($cols.Count -lt 5) { continue }
        $status = if ($cols.Count -ge 4) { $cols[3].Trim() } else { '' }
        $tags = if ($cols.Count -ge 5) { $cols[4].Trim() } else { '' }
        $title = if ($cols.Count -ge 3) { $cols[2].Trim().Substring(0, [Math]::Min(200, $cols[2].Trim().Length)) } else { '' }
        [void]$entries.Add([ordered]@{
            source = 'brain'
            lane = 'sanctum'
            key = $slug
            ts = $null
            snippet = "$title  [status: $status]  [tags: $tags]"
            path = $brainIndex
        })
    }
}

# --- Write output ---
$out = [ordered]@{
    schema_version = 'sinister.resume-search-index.v1'
    ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    sources = @('resume-point', 'progress', 'commit', 'brain')
    entry_count = $entries.Count
    entries = @($entries)
}
$json = $out | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($outPath, $json, [System.Text.UTF8Encoding]::new($false))

Write-Host "[index-resume-search] wrote $outPath"
Write-Host "  entries: $($entries.Count)"
foreach ($src in @('resume-point', 'progress', 'commit', 'brain')) {
    $count = ($entries | Where-Object { $_.source -eq $src } | Measure-Object).Count
    Write-Host "    $src : $count"
}
