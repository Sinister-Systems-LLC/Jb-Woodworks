# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: sinister-doctor meta-CLI (C.1 of master plan)
#
# Runs every Sanctum health check in one shot + emits a unified report.
# Composes the 6 individual scripts shipped over /loop iters 1-10:
#
#   1. canonical-protections-check.ps1   (P1-P9 fleet protections)
#   2. per-project-protections-check.ps1 (PP1-PP5 per-lane)
#   3. brain-index-orphan-check.ps1      (Rule 7.5 ceiling)
#   4. inbox-manifest-build.ps1          (per-lane unread counts)
#   5. telemetry-rollup.ps1              (daily metrics roll-up)
#   6. index-resume-search.ps1           (free-text search index)
#
# Modes:
#   (none)    full report to console
#   -Html     write HTML report to _shared-memory/sinister-doctor-<UTC>.html
#   -Json     machine-readable JSON dump
#   -Quick    skip slow steps (telemetry + index-resume-search)
#
# Exit codes: 0 = all green, 1 = at least one yellow, 2 = red (FAIL count > 0)
#
# Smoke: .\sinister-doctor.ps1
# Operator: .\sinister-doctor.ps1 -Html  (writes report; auto-opens via Invoke-Item)

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Html,
    [switch]$Json,
    [switch]$Quick
)

$auto = Join-Path $SanctumRoot 'automations'
$results = [ordered]@{
    ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    sanctum_root = $SanctumRoot
    quick_mode = [bool]$Quick
}
$globalStatus = 'GREEN'  # GREEN | YELLOW | RED
$elapsed = [ordered]@{}

function Run-Check {
    param([string]$Name, [scriptblock]$Block, [switch]$SlowSkippable)
    if ($SlowSkippable -and $Quick) {
        $elapsed[$Name] = 'skipped (quick mode)'
        return $null
    }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $out = & $Block
        $sw.Stop()
        $elapsed[$Name] = "$([math]::Round($sw.Elapsed.TotalSeconds, 2))s"
        return $out
    } catch {
        $sw.Stop()
        $elapsed[$Name] = "$([math]::Round($sw.Elapsed.TotalSeconds, 2))s [ERROR: $($_.Exception.Message)]"
        return $null
    }
}

# Check 1: canonical-protections (P1-P9)
$cp = Run-Check 'canonical_protections' {
    & "$auto\canonical-protections-check.ps1" -Quiet 2>&1 | Out-Null
    $log = Get-Content "$SanctumRoot\_shared-memory\canonical-protections-violations.log" -Tail 12
    $summary = $log | Where-Object { $_ -match 'PASS=(\d+)\s+FAIL=(\d+)' } | Select-Object -Last 1
    if ($summary -match 'PASS=(\d+)\s+FAIL=(\d+)') {
        return [ordered]@{ pass = [int]$matches[1]; fail = [int]$matches[2] }
    }
    return [ordered]@{ pass = 0; fail = 0; note = 'no PASS/FAIL in log' }
}
$results.canonical_protections = $cp
if ($cp -and $cp.fail -gt 0) { $globalStatus = 'RED' }

# Check 2: per-project-protections
$pp = Run-Check 'per_project_protections' {
    $jsonOut = & "$auto\per-project-protections-check.ps1" -Json 2>$null | Out-String
    if ($jsonOut) {
        $obj = $jsonOut | ConvertFrom-Json
        return [ordered]@{
            lane_count = $obj.lane_count
            full_pass_count = $obj.full_pass_count
            weak_lanes = ($obj.results | Where-Object { $_.pass_count -lt 4 }).Count
        }
    }
    return $null
}
$results.per_project_protections = $pp
if ($pp -and $pp.lane_count -and ($pp.full_pass_count / [math]::Max(1, $pp.lane_count)) -lt 0.5 -and $globalStatus -eq 'GREEN') {
    $globalStatus = 'YELLOW'
}

# Check 3: brain hygiene
$brain = Run-Check 'brain_hygiene' {
    $jsonOut = & "$auto\brain-index-orphan-check.ps1" -Json 2>$null | Out-String
    if ($jsonOut) {
        return ($jsonOut | ConvertFrom-Json)
    }
    return $null
}
$results.brain_hygiene = $brain
if ($brain -and $brain.rule_7_5_status -eq 'VIOLATED') { $globalStatus = 'RED' }
elseif ($brain -and $brain.rule_7_5_status -eq 'APPROACHING' -and $globalStatus -eq 'GREEN') { $globalStatus = 'YELLOW' }

# Check 4: inbox manifest
$inbox = Run-Check 'inbox_manifest' {
    & "$auto\inbox-manifest-build.ps1" 2>&1 | Out-Null
    $manifestPath = "$SanctumRoot\_shared-memory\inbox\_manifest.json"
    if (Test-Path $manifestPath) {
        $m = Get-Content $manifestPath -Raw | ConvertFrom-Json
        return [ordered]@{ total_unread = $m.total_unread; lane_count = ($m.per_lane.PSObject.Properties | Measure-Object).Count }
    }
    return $null
}
$results.inbox_manifest = $inbox
if ($inbox -and $inbox.total_unread -gt 100 -and $globalStatus -eq 'GREEN') { $globalStatus = 'YELLOW' }

# Check 5: telemetry rollup (slow-skippable)
$tel = Run-Check 'telemetry_rollup' -SlowSkippable {
    & "$auto\telemetry-rollup.ps1" 2>&1 | Out-Null
    $latestPath = "$SanctumRoot\_shared-memory\telemetry\_latest.json"
    if (Test-Path $latestPath) {
        $t = Get-Content $latestPath -Raw | ConvertFrom-Json
        return [ordered]@{
            ts_utc = $t.ts_utc
            queue_open = $t.operator_queue.open
            queue_closed = $t.operator_queue.closed
            recent_commits_count = ($t.recent_commits | Measure-Object).Count
        }
    }
    return $null
}
$results.telemetry_rollup = $tel
if ($tel -and $tel.queue_open -gt 100 -and $globalStatus -eq 'GREEN') { $globalStatus = 'YELLOW' }

# Check 6: resume-search index (slow-skippable)
$rs = Run-Check 'resume_search_index' -SlowSkippable {
    & "$auto\index-resume-search.ps1" 2>&1 | Out-Null
    $idxPath = "$SanctumRoot\_shared-memory\resume-search-index.json"
    if (Test-Path $idxPath) {
        $i = Get-Content $idxPath -Raw -Encoding UTF8 | ConvertFrom-Json
        return [ordered]@{ entry_count = $i.entry_count; sources = $i.sources }
    }
    return $null
}
$results.resume_search_index = $rs

# Final summary
$results.global_status = $globalStatus
$results.elapsed = $elapsed

# Output
if ($Json) {
    $results | ConvertTo-Json -Depth 8
} elseif ($Html) {
    $reportPath = Join-Path $SanctumRoot ("_shared-memory\sinister-doctor-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".html")
    $statusColor = @{ GREEN = '#7ee787'; YELLOW = '#ffb454'; RED = '#ff6b6b' }[$globalStatus]
    $html = @"
<!doctype html>
<html><head><title>Sinister Doctor :: $($results.ts_utc)</title>
<style>body{background:#0e0a14;color:#e8e4f0;font-family:ui-monospace,monospace;padding:24px}
h1{color:$statusColor;font-size:18px}h2{color:#79c0ff;font-size:13px;margin-top:18px;text-transform:uppercase}
table{width:100%;border-collapse:collapse;margin-top:8px}td{padding:3px 6px;font-size:12px;border-bottom:1px solid #2a2238}
td:first-child{color:#8a82a0}.pass{color:#7ee787}.warn{color:#ffb454}.fail{color:#ff6b6b}pre{background:#0a0710;padding:8px;font-size:11px;color:#8a82a0}
</style></head><body>
<h1>Sinister Doctor :: $globalStatus :: $($results.ts_utc)</h1>
<pre>$($results | ConvertTo-Json -Depth 8)</pre>
</body></html>
"@
    [System.IO.File]::WriteAllText($reportPath, $html, [System.Text.UTF8Encoding]::new($false))
    Write-Host "[sinister-doctor] HTML report -> $reportPath"
    Write-Host "  status: $globalStatus"
} else {
    # Console-friendly summary
    Write-Host ''
    $col = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red' }[$globalStatus]
    Write-Host "  Sinister Doctor :: $globalStatus" -ForegroundColor $col
    Write-Host "  $($results.ts_utc)" -ForegroundColor DarkGray
    Write-Host ('  ' + ('-' * 60)) -ForegroundColor DarkGray
    if ($cp) {
        $kind = if ($cp.fail -eq 0) { 'Green' } else { 'Red' }
        Write-Host ("  P1-P9 protections      PASS={0} FAIL={1}" -f $cp.pass, $cp.fail) -ForegroundColor $kind
    }
    if ($pp) {
        $kind = if ($pp.full_pass_count -ge $pp.lane_count / 2) { 'Green' } else { 'Yellow' }
        Write-Host ("  Per-project PP1-PP5    {0}/{1} fully PASS ({2} weak)" -f $pp.full_pass_count, $pp.lane_count, $pp.weak_lanes) -ForegroundColor $kind
    }
    if ($brain) {
        $kind = if ($brain.rule_7_5_status -eq 'OK') { 'Green' } elseif ($brain.rule_7_5_status -eq 'APPROACHING') { 'Yellow' } else { 'Red' }
        Write-Host ("  Brain (Rule 7.5)       {0} indexed / 150 ceiling [{1}]" -f $brain.indexed_count, $brain.rule_7_5_status) -ForegroundColor $kind
    }
    if ($inbox) {
        $kind = if ($inbox.total_unread -le 75) { 'Green' } elseif ($inbox.total_unread -le 150) { 'Yellow' } else { 'Red' }
        Write-Host ("  Inbox (unread)         {0} across {1} lanes" -f $inbox.total_unread, $inbox.lane_count) -ForegroundColor $kind
    }
    if ($tel) {
        $kind = if ($tel.queue_open -le 75) { 'Green' } elseif ($tel.queue_open -le 100) { 'Yellow' } else { 'Red' }
        Write-Host ("  Operator queue         {0} open / {1} closed" -f $tel.queue_open, $tel.queue_closed) -ForegroundColor $kind
    }
    if ($rs) {
        Write-Host ("  Resume-search index    {0} entries / {1} sources" -f $rs.entry_count, ($rs.sources -join ',')) -ForegroundColor Green
    }
    Write-Host ''
    Write-Host '  Elapsed:' -ForegroundColor DarkGray
    foreach ($k in $elapsed.Keys) {
        Write-Host ("    {0,-25} {1}" -f $k, $elapsed[$k]) -ForegroundColor DarkGray
    }
    Write-Host ''
}

# Exit code: 0 green / 1 yellow / 2 red
switch ($globalStatus) {
    'GREEN'  { exit 0 }
    'YELLOW' { exit 1 }
    'RED'    { exit 2 }
}
