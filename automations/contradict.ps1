# contradict.ps1 -- per-project counter-argument + project-growth driver
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T21:25Z (verbatim):
#   "expand system i alked about where we contracdict ourself and keep growingf
#    and expanding projects"
#
# This script EXPANDS the prior counter-arg.ps1 (single-shot row writer) into a
# per-project growth-loop:
#   1) Pivot   — append a pivot row to counter-arguments.jsonl using the SAME
#      schema as the recent rows operator has been writing in practice:
#        { ts_utc, lane, author, topic, prior_position, new_position,
#          reasoning, artifacts, status }
#   2) Audit   — scan latest plan.md(s) per project; surface unresolved-pivot rows
#      + emit "expansion candidate" rows ("what is the prior plan missing?")
#   3) Surface — render per-lane contradiction tally; flag projects with ZERO
#      pivots in the last 7 days (= growth stagnation signal per operator R3)
#   4) Walk    — for a given lane, list every pivot in chronological order with
#      reasoning so operator can see the project's evolution
#
# Storage: _shared-memory/counter-arguments.jsonl (append-only; sentinel-file lock)
# Per-project view: filter rows by lane field.
#
# Composes with: gradual-growth-memory-push-eve-exe-ready-2026-05-24 R3 (grow
# gradually + never stop + prune-as-add); no-bullshit-tested-before-claimed
# (R4 self-audit -- pivots ARE the self-audit log); master-plan section 5 (D7).
#
# Actions:
#   Pivot   -Lane <l> -Topic "..." -PriorPosition "..." -NewPosition "..."
#           -Reasoning "..." [-Artifacts "path1,path2"]
#                                                Append pivot row.
#   Audit   [-Lane <l>] [-WindowDays 7]          Per-lane stagnation tally + recent
#                                                pivots; lanes with 0 pivots flagged.
#   Walk    -Lane <l> [-Limit 20]                Chronological pivots for one lane.
#   Tally                                        Per-lane pivot count (all-time).

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [ValidateSet('Pivot','Audit','Walk','Tally')] [string]$Action,
    [string]$Lane = '',
    [string]$Topic = '',
    [string]$PriorPosition = '',
    [string]$NewPosition = '',
    [string]$Reasoning = '',
    [string]$Artifacts = '',
    [int]$WindowDays = 7,
    [int]$Limit = 20,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$JsonlPath = Join-Path $SanctumRoot '_shared-memory\counter-arguments.jsonl'
$LockPath  = Join-Path $SanctumRoot '_shared-memory\.counter-arguments.lock'

function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }

function Acquire-Lock { param([int]$TimeoutSec = 10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            try {
                if (Test-Path $LockPath) {
                    $age = ((Get-Date) - (Get-Item $LockPath).LastWriteTime).TotalSeconds
                    if ($age -gt 10) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue }
                }
            } catch {}
            Start-Sleep -Milliseconds 100
        }
    }
}
function Release-Lock { try { if (Test-Path $LockPath) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue } } catch {} }

function Read-Rows {
    if (-not (Test-Path $JsonlPath)) { return @() }
    $rows = @()
    foreach ($l in (Get-Content $JsonlPath -ErrorAction SilentlyContinue)) {
        if (-not $l -or -not $l.Trim()) { continue }
        try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {}
    }
    return $rows
}

switch ($Action) {

    'Pivot' {
        if (-not $Lane -or -not $Topic -or -not $NewPosition) {
            Write-Host "ERR: -Lane, -Topic, -NewPosition required"
            exit 2
        }
        $row = [pscustomobject]@{
            ts_utc          = Utc-Now
            lane            = $Lane
            author          = 'RKOJ-ELENO'
            topic           = $Topic
            prior_position  = $PriorPosition
            new_position    = $NewPosition
            reasoning       = $Reasoning
            artifacts       = @($Artifacts -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
            status          = 'shipped'
        }
        if (-not (Acquire-Lock)) { Write-Host "ERR: lock contention"; exit 3 }
        try {
            $line = $row | ConvertTo-Json -Compress -Depth 6
            Add-Content -LiteralPath $JsonlPath -Value $line -Encoding UTF8
        } finally { Release-Lock }
        Write-Host ("OK: pivot logged for lane=" + $Lane + " topic=" + $Topic.Substring(0, [Math]::Min(60, $Topic.Length)))
        exit 0
    }

    'Audit' {
        $rows = Read-Rows
        $cutoff = (Get-Date).ToUniversalTime().AddDays(-$WindowDays)
        $recent = @($rows | Where-Object {
            try { [DateTime]::Parse($_.ts_utc).ToUniversalTime() -gt $cutoff } catch { $false }
        })
        # Compute per-lane stats
        $lanes = @{}
        foreach ($r in $rows) {
            $l = $r.lane
            if (-not $l) { continue }
            if (-not $lanes.ContainsKey($l)) { $lanes[$l] = @{ total = 0; recent = 0; last_ts = '' } }
            $lanes[$l].total++
            try {
                $rowTs = [DateTime]::Parse($r.ts_utc).ToUniversalTime()
                if ($rowTs -gt $cutoff) { $lanes[$l].recent++ }
                if (-not $lanes[$l].last_ts -or $rowTs -gt [DateTime]::Parse($lanes[$l].last_ts).ToUniversalTime()) {
                    $lanes[$l].last_ts = $r.ts_utc
                }
            } catch {}
        }
        if ($Lane) {
            if (-not $lanes.ContainsKey($Lane)) {
                Write-Host ("STAGNATION: lane=" + $Lane + " has 0 pivots ever -- growth signal")
                exit 0
            }
            $L = $lanes[$Lane]
            Write-Host ("AUDIT lane=" + $Lane + " total=" + $L.total + " recent_${WindowDays}d=" + $L.recent + " last=" + $L.last_ts)
            $laneRecent = @($recent | Where-Object { $_.lane -eq $Lane })
            if ($laneRecent.Count -eq 0) {
                Write-Host ("STAGNATION: 0 pivots in last ${WindowDays}d for " + $Lane + " -- consider running contradict.ps1 -Action Pivot or revisiting plan")
            } else {
                Write-Host ""
                Write-Host "Recent pivots:"
                foreach ($r in $laneRecent) {
                    Write-Host ("  " + $r.ts_utc + " :: " + $r.topic)
                }
            }
            exit 0
        }
        # All lanes
        Write-Host ("AUDIT (all lanes; window=${WindowDays}d)")
        Write-Host ""
        $tableRows = @()
        $sortedLaneNames = @($lanes.Keys) | Sort-Object
        foreach ($laneName in $sortedLaneNames) {
            $L = $lanes[$laneName]
            $tag = if ($L.recent -eq 0) { 'STAGNANT' } else { 'GROWING' }
            $obj = New-Object PSObject
            $obj | Add-Member -MemberType NoteProperty -Name 'Lane' -Value ([string]$laneName)
            $obj | Add-Member -MemberType NoteProperty -Name 'Total' -Value $L.total
            $obj | Add-Member -MemberType NoteProperty -Name "Recent_${WindowDays}d" -Value $L.recent
            $obj | Add-Member -MemberType NoteProperty -Name 'Last' -Value $L.last_ts
            $obj | Add-Member -MemberType NoteProperty -Name 'Signal' -Value $tag
            $tableRows += $obj
        }
        $tableRows | Format-Table -AutoSize | Out-String | Write-Host
        $stagnant = @($tableRows | Where-Object { $_.Signal -eq 'STAGNANT' }).Count
        $growing  = @($tableRows | Where-Object { $_.Signal -eq 'GROWING' }).Count
        Write-Host ("Summary: " + $growing + " GROWING / " + $stagnant + " STAGNANT lanes (window=${WindowDays}d)")
        exit 0
    }

    'Walk' {
        if (-not $Lane) { Write-Host "ERR: -Lane required"; exit 2 }
        $rows = @((Read-Rows) | Where-Object { $_.lane -eq $Lane } | Sort-Object ts_utc | Select-Object -Last $Limit)
        if ($rows.Count -eq 0) { Write-Host ("no pivots for lane=" + $Lane); exit 0 }
        Write-Host ("Pivot walk for lane=" + $Lane + " (last " + $rows.Count + " of all-time)")
        Write-Host ""
        foreach ($r in $rows) {
            Write-Host ("[" + $r.ts_utc + "] " + $r.topic)
            if ($r.prior_position) { Write-Host ("  PRIOR: " + $r.prior_position) }
            if ($r.new_position)   { Write-Host ("  NEW:   " + $r.new_position) }
            if ($r.reasoning)      { Write-Host ("  WHY:   " + ($r.reasoning.Substring(0, [Math]::Min(140, $r.reasoning.Length)))) }
            if ($r.artifacts -and $r.artifacts.Count -gt 0) { Write-Host ("  ART:   " + (($r.artifacts) -join ' | ')) }
            Write-Host ""
        }
        exit 0
    }

    'Tally' {
        $rows = Read-Rows
        $lanes = $rows | Group-Object -Property lane | Sort-Object Count -Descending
        Write-Host ("contradict-tally :: " + $rows.Count + " total pivots across " + $lanes.Count + " lanes")
        Write-Host ""
        $lanes | Select-Object @{n='Lane';e={$_.Name}}, Count | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }
}
