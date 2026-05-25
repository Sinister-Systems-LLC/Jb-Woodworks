# heartbeat-sweep.ps1 — purge stale per-slug heartbeats
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose:
#   Operator hard-canonical 2026-05-24: prune-as-add. Each spawned session writes
#   a heartbeat under _shared-memory/heartbeats/<slug>.json. Old sessions never
#   clean up — we accumulated 12 stale sanctum-<id>.json files in this directory.
#   This script archives anything not updated within -MaxAgeHours (default 24).
#
# Behavior:
#   - Reads every .json in _shared-memory/heartbeats/
#   - If `last_update_utc` (or file mtime fallback) is older than cutoff:
#     - Move to _shared-memory/heartbeats/_archive/<yyyymmdd>/<filename>
#     - Print one-line summary
#   - Never touches the canonical per-slug heartbeats (sanctum.json,
#     panel.json, etc.) if they are fresh.
#   - Honors -DryRun (default) — only archives when -Apply is passed.
#
# Composes with: mesh-coordinator.ps1, bot-lifecycle.ps1, no-bullshit rule 8 (consolidation > expansion).

[CmdletBinding()]
param(
    [int]$MaxAgeHours = 24,
    [switch]$Apply,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$HbDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$Archive = Join-Path $HbDir '_archive'
if ($Apply -and -not (Test-Path $Archive)) { New-Item -ItemType Directory -Path $Archive -Force | Out-Null }

$cutoff = (Get-Date).ToUniversalTime().AddHours(-$MaxAgeHours)
$mode = if ($Apply) { 'APPLY' } else { 'DRY-RUN' }
Write-Host "heartbeat-sweep ($mode) :: cutoff=$($cutoff.ToString('yyyy-MM-ddTHH:mm:ssZ')) (max age $MaxAgeHours h)"
Write-Host ""

$archived = 0
$kept = 0
$files = Get-ChildItem -LiteralPath $HbDir -Filter '*.json' -File -ErrorAction SilentlyContinue

foreach ($f in $files) {
    $age = $null
    try {
        $raw = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
        $obj = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue
        $tsField = $null
        foreach ($k in @('last_update_utc','ts_utc','heartbeat_utc','updated_utc')) {
            if ($obj -and $obj.PSObject.Properties.Name -contains $k -and $obj.$k) {
                $tsField = $obj.$k; break
            }
        }
        if ($tsField) {
            $age = [DateTime]::Parse($tsField).ToUniversalTime()
        }
    } catch {}
    if (-not $age) { $age = $f.LastWriteTimeUtc }

    if ($age -lt $cutoff) {
        $ageH = [math]::Round(((Get-Date).ToUniversalTime() - $age).TotalHours, 1)
        if ($Apply) {
            $bucket = Join-Path $Archive $age.ToString('yyyyMMdd')
            if (-not (Test-Path $bucket)) { New-Item -ItemType Directory -Path $bucket -Force | Out-Null }
            $dest = Join-Path $bucket $f.Name
            # Don't overwrite existing
            if (Test-Path $dest) {
                $stem = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
                $ext  = [System.IO.Path]::GetExtension($f.Name)
                $dest = Join-Path $bucket "$stem-$(Get-Random -Maximum 9999)$ext"
            }
            Move-Item -LiteralPath $f.FullName -Destination $dest
        }
        Write-Host "  [archive] $($f.Name)  age=${ageH}h"
        $archived++
    } else {
        $kept++
    }
}

Write-Host ""
Write-Host "summary :: archived=$archived  kept=$kept  (mode=$mode)"
if (-not $Apply -and $archived -gt 0) {
    Write-Host "          re-run with -Apply to actually move them"
}
exit 0
