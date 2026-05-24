# Author: RKOJ-ELENO :: 2026-05-23
# Sanctum :: daily telemetry rollup (C.13 of sanctum-complete-and-expand master plan)
#
# Walks the fleet's runtime state + emits a daily JSON snapshot to
# _shared-memory/telemetry/daily-<UTC>.json. Operator-facing dashboard
# (C.14 _shared-memory/status/index.html) reads the latest rollup.
#
# Tracked metrics:
#   - canonical_protections : last PASS/FAIL summary from violations.log
#   - lane_heartbeats : per-slug freshness (age in seconds)
#   - operator_queue : open/closed count from OPERATOR-ACTION-QUEUE.md
#   - brain_doctrine : on-disk + indexed count + Rule 7.5 status
#   - inbox_unread : per-lane unread count (from _shared-memory/inbox/_manifest.json)
#   - bot_adoption : per-lane bot.tool mention count in last 7 days of PROGRESS
#   - recent_commits : last 10 git commits (sanctum repo)
#   - resume_point_chain : per-lane resume-point file count
#
# Smoke test: .\telemetry-rollup.ps1 -Verbose ; type _shared-memory\telemetry\daily-*.json

[CmdletBinding()]
param(
    [string]$SanctumRoot = "D:\Sinister Sanctum"
)

$telemetryDir = Join-Path $SanctumRoot "_shared-memory\telemetry"
if (-not (Test-Path $telemetryDir)) { New-Item -ItemType Directory -Path $telemetryDir -Force | Out-Null }

$rollup = [ordered]@{
    schema_version = "sinister.telemetry-daily.v1"
    ts_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    sanctum_root = $SanctumRoot
}

# --- canonical_protections ---
$violationsLog = Join-Path $SanctumRoot "_shared-memory\canonical-protections-violations.log"
$protections = [ordered]@{ source = $violationsLog; last_run = $null; pass = $null; fail = $null }
if (Test-Path $violationsLog) {
    $lines = Get-Content $violationsLog -Tail 30
    $summary = $lines | Where-Object { $_ -match 'PASS=(\d+)\s+FAIL=(\d+)' } | Select-Object -Last 1
    if ($summary -match '\[([^\]]+)\].*PASS=(\d+)\s+FAIL=(\d+)') {
        $protections.last_run = $matches[1]
        $protections.pass = [int]$matches[2]
        $protections.fail = [int]$matches[3]
    }
}
$rollup.canonical_protections = $protections

# --- lane_heartbeats ---
$heartbeats = [ordered]@{}
$hbDir = Join-Path $SanctumRoot "_shared-memory\heartbeats"
if (Test-Path $hbDir) {
    Get-ChildItem $hbDir -Filter '*.json' -File | ForEach-Object {
        try {
            $j = Get-Content $_.FullName -Raw | ConvertFrom-Json
            $age = $null
            if ($j.ts_utc) {
                $t = [datetime]::Parse($j.ts_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal)
                $age = [int]((Get-Date).ToUniversalTime() - $t.ToUniversalTime()).TotalSeconds
            }
            $heartbeats[$_.BaseName] = [ordered]@{ ts_utc = $j.ts_utc; age_sec = $age; display = $j.agent_display }
        } catch { }
    }
}
$rollup.lane_heartbeats = $heartbeats

# --- operator_queue ---
$queueFile = Join-Path $SanctumRoot "_shared-memory\OPERATOR-ACTION-QUEUE.md"
$queue = [ordered]@{ open = 0; closed = 0; critical = 0; high = 0; medium = 0; low = 0 }
if (Test-Path $queueFile) {
    $qc = Get-Content $queueFile -Raw
    $queue.open = ([regex]::Matches($qc, '(?m)^\s*-\s+\[ \]')).Count
    $queue.closed = ([regex]::Matches($qc, '(?m)^\s*-\s+\[x\]')).Count
    $queue.critical = ([regex]::Matches($qc, '🔴')).Count
    $queue.high = ([regex]::Matches($qc, '🟠')).Count
    $queue.medium = ([regex]::Matches($qc, '🟡')).Count
    $queue.low = ([regex]::Matches($qc, '🟢')).Count
}
$rollup.operator_queue = $queue

# --- brain_doctrine ---
$brain = [ordered]@{ on_disk = 0; indexed = 0; orphans = 0; rule_7_5_ceiling = 150; status = "OK" }
$brainCheck = & (Join-Path $SanctumRoot "automations\brain-index-orphan-check.ps1") -SanctumRoot $SanctumRoot -Json 2>$null | ConvertFrom-Json
if ($brainCheck) {
    $brain.on_disk = $brainCheck.on_disk_count
    $brain.indexed = $brainCheck.indexed_count
    $brain.orphans = $brainCheck.orphan_count
    $brain.status = $brainCheck.rule_7_5_status
}
$rollup.brain_doctrine = $brain

# --- inbox_unread ---
$inboxManifest = Join-Path $SanctumRoot "_shared-memory\inbox\_manifest.json"
$inboxStats = [ordered]@{ total = 0; per_lane = @{} }
if (Test-Path $inboxManifest) {
    try {
        $im = Get-Content $inboxManifest -Raw | ConvertFrom-Json
        $inboxStats.total = $im.total_unread
        $perLane = @{}
        $im.per_lane.PSObject.Properties | ForEach-Object { $perLane[$_.Name] = $_.Value }
        $inboxStats.per_lane = $perLane
    } catch { }
}
$rollup.inbox_unread = $inboxStats

# --- bot_adoption ---
$progressDir = Join-Path $SanctumRoot "_shared-memory\PROGRESS"
$botPattern = 'sinister-bus\.|librarian\.|triage\.|researcher\.|scribe\.|curator\.|auditor\.|sentinel\.|custodian\.|stealth-browser\.|translator\.|watcher\.|vault\.'
$botAdoption = [ordered]@{}
if (Test-Path $progressDir) {
    $sevenDaysAgo = (Get-Date).AddDays(-7)
    Get-ChildItem $progressDir -Filter '*.md' -File | ForEach-Object {
        try {
            $content = Get-Content $_.FullName -Raw
            $count = ([regex]::Matches($content, $botPattern)).Count
            $botAdoption[$_.BaseName] = $count
        } catch { }
    }
}
$rollup.bot_adoption = $botAdoption

# --- per_project_protections (iter 6 wire-up) ---
$ppScript = Join-Path $SanctumRoot 'automations\per-project-protections-check.ps1'
$ppData = [ordered]@{ lane_count = 0; full_pass_count = 0; per_lane = @{} }
if (Test-Path $ppScript) {
    try {
        $ppJson = & $ppScript -SanctumRoot $SanctumRoot -Json 2>$null | Out-String
        if ($ppJson) {
            $pp = $ppJson | ConvertFrom-Json
            $ppData.lane_count = $pp.lane_count
            $ppData.full_pass_count = $pp.full_pass_count
            $perLane = @{}
            foreach ($r in $pp.results) {
                $perLane[$r.display] = [ordered]@{
                    score = "$($r.pass_count)/$($r.total)"
                    pp1 = $r.pp1_claude_md
                    pp2 = $r.pp2_settings_json
                    pp3 = $r.pp3_heartbeat_fresh
                    pp3_hb_age_h = $r.pp3_heartbeat_age_hours
                    pp4 = $r.pp4_progress_log
                    pp5_brain_hits = $r.pp5_brain_hits
                }
            }
            $ppData.per_lane = $perLane
        }
    } catch { }
}
$rollup.per_project_protections = $ppData

# --- recent_commits ---
Push-Location $SanctumRoot
$recentCommits = & git log --oneline -10 2>$null
Pop-Location
$rollup.recent_commits = @($recentCommits)

# --- resume_point_chain ---
$rpDir = Join-Path $SanctumRoot "_shared-memory\resume-points"
$resumeStats = [ordered]@{}
if (Test-Path $rpDir) {
    Get-ChildItem $rpDir -Directory | ForEach-Object {
        $count = (Get-ChildItem $_.FullName -Filter '*.json' -File -ErrorAction SilentlyContinue | Measure-Object).Count
        $resumeStats[$_.Name] = $count
    }
}
$rollup.resume_point_chain = $resumeStats

# --- Write output ---
# PowerShell 5.1's `Set-Content -Encoding UTF8` writes a BOM that breaks strict
# JSON parsers (Python json.load, jq). Use .NET UTF8Encoding($false) for BOM-free.
$date = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
$outPath = Join-Path $telemetryDir "daily-$date.json"
$jsonText = $rollup | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText($outPath, $jsonText, [System.Text.UTF8Encoding]::new($false))

# Also write/update _latest.json symlink-equivalent for dashboard
$latestPath = Join-Path $telemetryDir "_latest.json"
[System.IO.File]::WriteAllText($latestPath, $jsonText, [System.Text.UTF8Encoding]::new($false))

Write-Host "[telemetry-rollup] wrote $outPath"
Write-Host "[telemetry-rollup] also: $latestPath (for dashboard)"
Write-Host "  protections: PASS=$($protections.pass) FAIL=$($protections.fail)"
Write-Host "  lanes: $($heartbeats.Count) heartbeats / $($botAdoption.Count) progress logs"
Write-Host "  queue: open=$($queue.open) closed=$($queue.closed)"
Write-Host "  brain: $($brain.on_disk) on-disk / $($brain.indexed) indexed / $($brain.orphans) orphans / status=$($brain.status)"
Write-Host "  inbox: total=$($inboxStats.total) unread"
