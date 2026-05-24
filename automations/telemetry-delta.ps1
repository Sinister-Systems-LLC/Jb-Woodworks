# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: telemetry-delta :: compare two daily snapshots, surface meaningful changes
#
# Reads two _shared-memory/telemetry/daily-*.json files (default: most-recent
# vs second-most-recent) and reports deltas:
#   - global_status change (GREEN/YELLOW/RED transitions)
#   - per_project_protections full_pass_count delta
#   - per-lane PP score changes (which lanes improved or regressed)
#   - brain on_disk + indexed deltas
#   - operator_queue open + closed deltas
#   - inbox_unread total delta
#   - heartbeat staleness changes (lanes that went dark)
#
# Modes:
#   (none)         most-recent vs second-most-recent in telemetry/
#   -Json          machine-readable
#   -A <path> -B <path>   explicit pair
#
# Smoke: .\telemetry-delta.ps1

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Json,
    [string]$A = '',
    [string]$B = ''
)

$telemetryDir = Join-Path $SanctumRoot '_shared-memory\telemetry'
if (-not (Test-Path $telemetryDir)) {
    Write-Error "telemetry dir missing"
    exit 2
}

# Pick snapshots
if (-not $A -or -not $B) {
    $files = Get-ChildItem $telemetryDir -Filter 'daily-*.json' -File | Sort-Object LastWriteTime -Descending
    if ($files.Count -lt 2) {
        Write-Error "need at least 2 daily snapshots; found $($files.Count)"
        exit 2
    }
    $newPath = $files[0].FullName
    $oldPath = $files[1].FullName
} else {
    $newPath = $A
    $oldPath = $B
}

$new = Get-Content $newPath -Raw | ConvertFrom-Json
$old = Get-Content $oldPath -Raw | ConvertFrom-Json

$delta = [ordered]@{
    schema_version = 'sinister.telemetry-delta.v1'
    ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    new_snapshot = (Split-Path $newPath -Leaf)
    old_snapshot = (Split-Path $oldPath -Leaf)
    deltas = [ordered]@{}
    lane_changes = @()
}

# Canonical-protections delta
if ($new.canonical_protections -and $old.canonical_protections) {
    $d = [ordered]@{
        pass_delta = $new.canonical_protections.pass - $old.canonical_protections.pass
        fail_delta = $new.canonical_protections.fail - $old.canonical_protections.fail
    }
    if ($d.pass_delta -ne 0 -or $d.fail_delta -ne 0) {
        $delta.deltas.canonical_protections = $d
    }
}

# Per-project deltas
if ($new.per_project_protections -and $old.per_project_protections) {
    $fullPassDelta = $new.per_project_protections.full_pass_count - $old.per_project_protections.full_pass_count
    if ($fullPassDelta -ne 0) {
        $delta.deltas.per_project_full_pass = [ordered]@{
            from = $old.per_project_protections.full_pass_count
            to = $new.per_project_protections.full_pass_count
            delta = $fullPassDelta
        }
    }
    # Per-lane score changes
    foreach ($pp in $new.per_project_protections.per_lane.PSObject.Properties) {
        $lane = $pp.Name
        $newScore = $pp.Value.score
        $oldEntry = $old.per_project_protections.per_lane.$lane
        if ($oldEntry -and $oldEntry.score -ne $newScore) {
            $delta.lane_changes += [PSCustomObject]@{
                lane = $lane
                pp_from = $oldEntry.score
                pp_to = $newScore
            }
        }
    }
}

# Brain deltas
if ($new.brain_doctrine -and $old.brain_doctrine) {
    $onDisk = $new.brain_doctrine.on_disk - $old.brain_doctrine.on_disk
    $indexed = $new.brain_doctrine.indexed - $old.brain_doctrine.indexed
    if ($onDisk -ne 0 -or $indexed -ne 0) {
        $delta.deltas.brain = [ordered]@{
            on_disk_delta = $onDisk
            indexed_delta = $indexed
            status_change = if ($new.brain_doctrine.status -ne $old.brain_doctrine.status) { "$($old.brain_doctrine.status) -> $($new.brain_doctrine.status)" } else { $null }
        }
    }
}

# Queue deltas
if ($new.operator_queue -and $old.operator_queue) {
    $open = $new.operator_queue.open - $old.operator_queue.open
    $closed = $new.operator_queue.closed - $old.operator_queue.closed
    if ($open -ne 0 -or $closed -ne 0) {
        $delta.deltas.operator_queue = [ordered]@{ open_delta = $open; closed_delta = $closed }
    }
}

# Inbox delta
if ($new.inbox_unread -and $old.inbox_unread) {
    $total = $new.inbox_unread.total - $old.inbox_unread.total
    if ($total -ne 0) {
        $delta.deltas.inbox_total = [ordered]@{ from = $old.inbox_unread.total; to = $new.inbox_unread.total; delta = $total }
    }
}

if ($Json) {
    $delta | ConvertTo-Json -Depth 6
} else {
    Write-Host ''
    Write-Host "  telemetry-delta :: $($delta.old_snapshot) -> $($delta.new_snapshot)" -ForegroundColor DarkMagenta
    Write-Host "  $($delta.ts_utc)" -ForegroundColor DarkGray
    Write-Host ('  ' + ('-' * 60)) -ForegroundColor DarkGray

    if ($delta.deltas.Count -eq 0 -and $delta.lane_changes.Count -eq 0) {
        Write-Host '  no meaningful changes between snapshots' -ForegroundColor Green
    } else {
        foreach ($k in $delta.deltas.Keys) {
            $v = $delta.deltas[$k]
            Write-Host ('    ' + $k + ': ' + ($v | ConvertTo-Json -Compress)) -ForegroundColor Yellow
        }
        if ($delta.lane_changes.Count -gt 0) {
            Write-Host ''
            Write-Host "  lane changes ($($delta.lane_changes.Count)):" -ForegroundColor Yellow
            foreach ($lc in $delta.lane_changes) {
                $arrow = if (($lc.pp_to -split '/')[0] -gt ($lc.pp_from -split '/')[0]) { '^' } else { 'v' }
                $col = if ($arrow -eq '^') { 'Green' } else { 'Red' }
                Write-Host ("    $arrow  $($lc.lane) :: $($lc.pp_from) -> $($lc.pp_to)") -ForegroundColor $col
            }
        }
    }
    Write-Host ''
}
exit 0
