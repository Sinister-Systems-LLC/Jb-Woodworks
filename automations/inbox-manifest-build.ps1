# Author: RKOJ-ELENO :: 2026-05-23
# Sanctum :: inbox manifest builder (C.14 dashboard data source)
#
# Scans _shared-memory/inbox/<lane>/*.json, counts unread per lane
# (any .json not in _archive/), writes _shared-memory/inbox/_manifest.json
# in the shape the status dashboard expects:
#
#   { "schema_version":"sinister.inbox-manifest.v1",
#     "ts_utc":"...",
#     "per_lane": {"sinister-panel":3, "kernel-apk":5, ...},
#     "total_unread": 12 }
#
# Idempotent. Safe to run from cron. Stdlib-only PowerShell.
# Smoke test: .\inbox-manifest-build.ps1 -Verbose ; cat _shared-memory\inbox\_manifest.json

[CmdletBinding()]
param(
    [string]$SanctumRoot = "D:\Sinister Sanctum"
)

$inboxRoot = Join-Path $SanctumRoot "_shared-memory\inbox"
if (-not (Test-Path $inboxRoot)) {
    Write-Error "Inbox root not found: $inboxRoot"
    exit 2
}

$perLane = [ordered]@{}
$total = 0

Get-ChildItem $inboxRoot -Directory | Sort-Object Name | ForEach-Object {
    $lane = $_.Name
    if ($lane -like '_*') { return }
    $jsons = Get-ChildItem $_.FullName -Filter '*.json' -File -ErrorAction SilentlyContinue
    $count = ($jsons | Measure-Object).Count
    $perLane[$lane] = $count
    $total += $count
    Write-Verbose "  $lane : $count unread"
}

$manifest = [ordered]@{
    schema_version = "sinister.inbox-manifest.v1"
    ts_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    per_lane = $perLane
    total_unread = $total
}

$outPath = Join-Path $inboxRoot "_manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Set-Content -Path $outPath -Encoding UTF8
Write-Host "[inbox-manifest-build] wrote $outPath (total unread = $total across $($perLane.Count) lanes)"
