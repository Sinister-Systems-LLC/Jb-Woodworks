# Author: RKOJ-ELENO :: 2026-05-23
# Sanctum :: per-project canonical-protections check (C.2 of master plan)
#
# Sister script to canonical-protections-check.ps1 (which validates fleet-level
# protections P1-P9). This one validates per-lane protections for every project
# in automations/session-templates/projects.json:
#
#   PP1 :: lane has CLAUDE.md at its root (or product-repo root)
#   PP2 :: lane has .claude/settings.json (with plugin enablement OR explicitly opt-out)
#   PP3 :: lane has a fresh heartbeat (<24h old)
#   PP4 :: lane has a PROGRESS log in _shared-memory/PROGRESS/<display>.md
#   PP5 :: lane's brain-entries are indexed in _INDEX.md (lane-tagged)
#
# Run modes:
#   -All                    # check every lane (default)
#   -Lane <slug>            # single lane
#   -Json                   # machine-readable for telemetry rollup
#
# Smoke test: .\per-project-protections-check.ps1 -Lane sanctum -Verbose

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Lane = '',
    [switch]$Json
)

$projectsFile = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
if (-not (Test-Path $projectsFile)) {
    Write-Error "projects.json not found at $projectsFile"
    exit 2
}

# BOM-tolerant JSON read (PowerShell 5.1 ConvertFrom-Json mis-handles BOM in
# some edge cases; sibling scripts hit same issue).
$rawJson = [System.IO.File]::ReadAllText($projectsFile)
if ($rawJson.Length -gt 0 -and [int]$rawJson[0] -eq 0xFEFF) { $rawJson = $rawJson.Substring(1) }
$projData = $rawJson | ConvertFrom-Json

# Iter 5 fix: hard-skip entries with null/empty root. The .root field is a
# string from JSON parsing; PowerShell truthiness handles null + empty cleanly.
# Test-Path tolerates spaces in paths when called this way.
$allLanes = $projData.projects | Where-Object { $_ -and $_.root -and (Test-Path $_.root) }

if ($Lane) {
    $lanes = $allLanes | Where-Object { $_.key -eq $Lane -or $_.display -eq $Lane }
    if (-not $lanes) {
        Write-Error "Lane '$Lane' not found in projects.json"
        exit 2
    }
} else {
    $lanes = $allLanes
}

$heartbeatsDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$progressDir = Join-Path $SanctumRoot '_shared-memory\PROGRESS'
$brainIndex = Join-Path $SanctumRoot '_shared-memory\knowledge\_INDEX.md'
$brainIndexContent = if (Test-Path $brainIndex) { Get-Content $brainIndex -Raw } else { '' }

$results = @()

# NOTE: $lane case-INSENSITIVELY shadows the [string]$Lane param, which coerces
# every PSCustomObject to "" in the loop body. Iter 5 fix: use $proj instead.
foreach ($proj in $lanes) {
    # Defensive: skip if entry somehow has null root (filter above should
    # have caught it, but belt-and-suspenders since the prior bug crashed here).
    if (-not $proj -or -not $proj.root) { continue }
    $key = $proj.key
    $display = if ($proj.display) { $proj.display } else { $key }
    $root = $proj.root

    # PP1: CLAUDE.md presence
    $cmCandidates = @(
        (Join-Path $root 'CLAUDE.md'),
        (Join-Path $root 'source\CLAUDE.md'),
        (Join-Path $root 'source\source\CLAUDE.md')
    )
    $cmFound = $cmCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    $pp1 = [bool]$cmFound

    # PP2: .claude/settings.json present (lane has Claude Code config)
    $settingsCandidates = @(
        (Join-Path $root '.claude\settings.json'),
        (Join-Path $root '.claude\settings.local.json'),
        (Join-Path $root 'source\.claude\settings.json')
    )
    $settingsFound = $settingsCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    $pp2 = [bool]$settingsFound

    # PP3: heartbeat freshness (look for <key>.json or first match)
    $hbFiles = @(
        (Join-Path $heartbeatsDir "$key.json"),
        (Join-Path $heartbeatsDir "$($key -replace '^sinister-','').json")
    )
    $hbFound = $hbFiles | Where-Object { Test-Path $_ } | Select-Object -First 1
    $hbAge = $null
    $pp3 = $false
    if ($hbFound) {
        try {
            $hb = Get-Content $hbFound -Raw | ConvertFrom-Json
            if ($hb.ts_utc) {
                $t = [datetime]::Parse($hb.ts_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal)
                $hbAge = [int]((Get-Date).ToUniversalTime() - $t.ToUniversalTime()).TotalHours
                $pp3 = ($hbAge -lt 24)
            }
        } catch { }
    }

    # PP4: PROGRESS log presence (try display, key, "Sinister X" forms)
    $sinisterPrefix = if ($display -notlike 'Sinister *') { "Sinister $display.md" } else { $null }
    $progressCandidates = @(
        (Join-Path $progressDir "$display.md"),
        (Join-Path $progressDir "$key.md"),
        $(if ($sinisterPrefix) { Join-Path $progressDir $sinisterPrefix })
    ) | Where-Object { $_ }
    $progressFound = $progressCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    $pp4 = [bool]$progressFound

    # PP5: brain-entries indexed - check if any brain entry tagged with the lane key exists
    # Heuristic: search _INDEX.md for the lane key as a substring in tag/slug positions.
    $brainHits = 0
    if ($brainIndexContent) {
        $brainHits = ([regex]::Matches($brainIndexContent, "(?i)\b$([regex]::Escape($key))\b")).Count
    }
    $pp5 = ($brainHits -gt 0)

    $laneResult = [ordered]@{
        key = $key
        display = $display
        root = $root
        pp1_claude_md = $pp1
        pp2_settings_json = $pp2
        pp3_heartbeat_fresh = $pp3
        pp3_heartbeat_age_hours = $hbAge
        pp4_progress_log = $pp4
        pp5_brain_hits = $brainHits
        pass_count = @($pp1, $pp2, $pp3, $pp4, $pp5) | Where-Object { $_ } | Measure-Object | Select-Object -ExpandProperty Count
        total = 5
    }
    $results += [PSCustomObject]$laneResult
}

if ($Json) {
    $out = [ordered]@{
        schema_version = 'sinister.per-project-protections.v1'
        ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        lane_count = $results.Count
        full_pass_count = ($results | Where-Object { $_.pass_count -eq $_.total } | Measure-Object).Count
        results = $results
    }
    $out | ConvertTo-Json -Depth 5
} else {
    Write-Host ''
    Write-Host "Per-project protections check ($($results.Count) lanes)" -ForegroundColor DarkMagenta
    Write-Host ''
    Write-Host ("  {0,-20} {1,-5} {2,-5} {3,-5} {4,-5} {5,-5} {6,-6}" -f 'Lane','PP1','PP2','PP3','PP4','PP5','Score') -ForegroundColor DarkGray
    Write-Host ("  " + ('-' * 60)) -ForegroundColor DarkGray
    foreach ($r in $results) {
        $sym = @{$true='OK';$false='--'}
        $col = if ($r.pass_count -eq $r.total) { 'Green' } elseif ($r.pass_count -ge 3) { 'Yellow' } else { 'Red' }
        $line = "  {0,-20} {1,-5} {2,-5} {3,-5} {4,-5} {5,-5} {6,-6}" -f `
            $r.display, $sym[$r.pp1_claude_md], $sym[$r.pp2_settings_json], `
            $sym[$r.pp3_heartbeat_fresh], $sym[$r.pp4_progress_log], $sym[$r.pp5_brain_hits -gt 0], `
            "$($r.pass_count)/$($r.total)"
        Write-Host $line -ForegroundColor $col
    }
    Write-Host ''
    $fullPass = ($results | Where-Object { $_.pass_count -eq $_.total } | Measure-Object).Count
    Write-Host "  $fullPass / $($results.Count) lanes fully PASS" -ForegroundColor $(if ($fullPass -eq $results.Count) { 'Green' } else { 'Yellow' })
}

$weakLanes = ($results | Where-Object { $_.pass_count -lt 3 } | Measure-Object).Count
if ($weakLanes -gt 0) { exit 1 } else { exit 0 }
