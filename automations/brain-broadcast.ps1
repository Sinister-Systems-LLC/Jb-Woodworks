# brain-broadcast.ps1 - auto-broadcast brain doctrine changes to the fleet-update channel
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T23:58Z:
#   "make sure all agents have the memory updates as we grow on it daily and it auto updates."
#
# Pipeline:
#   1. Scan _shared-memory/knowledge/*.md for files added/modified since last sweep
#      (mtime >= last-sweep timestamp). Excludes _INDEX.md, _archive/, _TEMPLATE.md.
#   2. For each new/updated doctrine, extract a 1-line summary (first H1 heading OR
#      first operator-verbatim quote OR first non-empty prose line, whichever fires
#      first; capped at 220 chars).
#   3. Push a fleet-update row via fleet-update.ps1 -Action Push
#        -Kind doctrine_update -Priority normal -PushedBy sanctum
#        -Message "BRAIN: <slug> — <summary>"
#   4. Persist sweep state (per-file last-broadcast mtime) in
#      _shared-memory/.brain-broadcast-state.json so the same mtime never re-broadcasts.
#
# Actions:
#   Scan       (default)  -> list candidates, do not push
#   Broadcast              -> Scan + push fleet-update rows for diffs
#   Watch -IntervalSec N   -> loop: every N seconds run Broadcast (default 600 = 10 min)
#   Status                 -> show last-sweep ts + state row count
#
# Idempotency: state file stores { "files": { "<slug>": "<mtime-iso>" }, "last_sweep": "..." }.
# A doctrine only re-broadcasts when its mtime is strictly greater than the stored one.
#
# Composes with:
#   _shared-memory/knowledge/fleet-update-channel-doctrine-2026-05-24.md (the transport)
#   _shared-memory/knowledge/auto-brain-propagation-doctrine-2026-05-24.md (this script's doctrine)
#   automations/start-sinister-session.ps1 Build-Phrase (cold-start RECENT BRAIN UPDATES inject)
#   CLAUDE.md cold-start step 11 (per-agent poll cadence)

[CmdletBinding()]
param(
    [ValidateSet('Scan','Broadcast','Watch','Status','Bootstrap')] [string]$Action = 'Scan',
    [int]$IntervalSec = 600,
    [int]$WindowHours = 24,
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$PushedBy = 'sanctum',
    [int]$MaxPerSweep = 12,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$KnowledgeDir = Join-Path $SanctumRoot '_shared-memory\knowledge'
$StatePath    = Join-Path $SanctumRoot '_shared-memory\.brain-broadcast-state.json'
$FleetScript  = Join-Path $SanctumRoot 'automations\fleet-update.ps1'

function _Load-State {
    if (-not (Test-Path $StatePath)) {
        return [pscustomobject]@{ files = @{}; last_sweep = $null }
    }
    try {
        $raw = Get-Content $StatePath -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        # Normalize files into hashtable.
        $h = @{}
        if ($obj.files) {
            foreach ($p in $obj.files.PSObject.Properties) { $h[$p.Name] = $p.Value }
        }
        return [pscustomobject]@{ files = $h; last_sweep = $obj.last_sweep }
    } catch {
        return [pscustomobject]@{ files = @{}; last_sweep = $null }
    }
}

function _Save-State { param($State)
    $payload = [pscustomobject]@{
        files      = $State.files
        last_sweep = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
    $tmp = "$StatePath.tmp"
    [System.IO.File]::WriteAllText($tmp, ($payload | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
    Move-Item -Path $tmp -Destination $StatePath -Force
}

function _Extract-Summary { param([string]$Path)
    # Prefer (in order): first H1 line, first operator-verbatim quote, first non-empty prose.
    if (-not (Test-Path $Path)) { return '' }
    try {
        $lines = Get-Content $Path -ErrorAction Stop -TotalCount 80
    } catch { return '' }
    $h1 = $null
    $quote = $null
    $first = $null
    foreach ($l in $lines) {
        $t = $l.Trim()
        if (-not $t) { continue }
        if ($t -match '^#\s+(.+)$' -and -not $h1) { $h1 = $matches[1].Trim() }
        if ($t -match '\*"([^"]+)"\*' -and -not $quote) { $quote = $matches[1].Trim() }
        if (-not $first -and $t -notmatch '^(#|>|\||---|\*\*Author|\*\*Created|`)') {
            $first = $t -replace '^\*\s*','' -replace '^-\s*',''
        }
    }
    $pick = $h1
    if (-not $pick) { $pick = $quote }
    if (-not $pick) { $pick = $first }
    if (-not $pick) { $pick = '(no summary extractable)' }
    if ($pick.Length -gt 220) { $pick = $pick.Substring(0, 217) + '...' }
    return $pick
}

function _Get-Candidates { param($State, [int]$WindowHours)
    if (-not (Test-Path $KnowledgeDir)) { return @() }
    $cutoff = (Get-Date).AddHours(-$WindowHours)
    $items = Get-ChildItem -Path $KnowledgeDir -Filter '*.md' -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -notmatch '^_' -and
            $_.FullName -notmatch '\\_archive\\' -and
            $_.LastWriteTime -ge $cutoff
        }
    $out = @()
    foreach ($it in $items) {
        $slug = [System.IO.Path]::GetFileNameWithoutExtension($it.Name)
        $mtimeIso = $it.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
        $prior = $null
        if ($State.files.ContainsKey($slug)) { $prior = [string]$State.files[$slug] }
        $isNew = (-not $prior)
        $isUpdated = ($prior -and ($mtimeIso -gt $prior))
        if ($isNew -or $isUpdated -or $Force) {
            $out += [pscustomobject]@{
                slug      = $slug
                path      = $it.FullName
                mtime_iso = $mtimeIso
                prior     = $prior
                change    = $(if ($isNew) { 'new' } elseif ($isUpdated) { 'updated' } else { 'forced' })
            }
        }
    }
    return @($out)
}

function _Do-Broadcast {
    $state = _Load-State
    $cands = _Get-Candidates -State $state -WindowHours $WindowHours
    if (-not $cands -or $cands.Count -eq 0) {
        Write-Output "no doctrine changes in last $WindowHours h (state at $StatePath)"
        _Save-State -State $state
        return
    }
    if (-not (Test-Path $FleetScript)) {
        Write-Error "fleet-update.ps1 missing at $FleetScript"
        return
    }
    # Sort newest-first; if cap exceeded, only PUSH the top N (newest), but RECORD all in state
    # so older files do not get re-broadcast on the next tick. This handles bootstrap (large
    # initial window) without flooding fleet-updates.jsonl.
    $cands = @($cands | Sort-Object @{Expression='mtime_iso';Descending=$true})
    $totalCands = $cands.Count
    $pushable = $cands
    $skipped = 0
    if ($MaxPerSweep -gt 0 -and $cands.Count -gt $MaxPerSweep) {
        $pushable = $cands | Select-Object -First $MaxPerSweep
        $skipped = $cands.Count - $MaxPerSweep
    }
    $count = 0
    foreach ($c in $pushable) {
        $summary = _Extract-Summary -Path $c.path
        $msg = ('BRAIN ' + $c.change + ': ' + $c.slug + ' - ' + $summary)
        if ($msg.Length -gt 480) { $msg = $msg.Substring(0, 477) + '...' }
        try {
            $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $FleetScript `
                -Action Push -Message $msg -Kind 'doctrine_update' `
                -Priority 'normal' -PushedBy $PushedBy 2>&1
            Write-Output ("broadcast " + $c.change + ' ' + $c.slug + ' -> ' + ($out -join ' '))
            $state.files[$c.slug] = $c.mtime_iso
            $count++
        } catch {
            Write-Output ("FAIL " + $c.slug + ' :: ' + $_.Exception.Message)
        }
    }
    # Record skipped candidates in state too — they were "in window" at this sweep moment
    # but did not get pushed (cap). Mark them at their current mtime so they will not
    # re-broadcast until their content actually changes.
    foreach ($c in $cands) {
        if (-not $state.files.ContainsKey($c.slug)) { $state.files[$c.slug] = $c.mtime_iso }
    }
    _Save-State -State $state
    Write-Output ("broadcast count=" + $count + " total_candidates=" + $totalCands + " skipped_by_cap=" + $skipped + " state=" + $StatePath)
}

switch ($Action) {
    'Scan' {
        $state = _Load-State
        $cands = _Get-Candidates -State $state -WindowHours $WindowHours
        if (-not $cands -or $cands.Count -eq 0) {
            Write-Output "no doctrine changes in last $WindowHours h"
            exit 0
        }
        Write-Output ("candidates=" + $cands.Count + " (window=" + $WindowHours + "h)")
        foreach ($c in $cands) {
            $summary = _Extract-Summary -Path $c.path
            Write-Output ("  [" + $c.change + "] " + $c.slug + " mtime=" + $c.mtime_iso)
            Write-Output ("      summary: " + $summary)
        }
    }
    'Broadcast' {
        _Do-Broadcast
        exit 0
    }
    'Bootstrap' {
        # Seed-only: scan, but only PUSH the very newest 3 (avoid flooding); record state
        # for all in-window files so subsequent Broadcast sweeps start from a clean diff.
        $MaxPerSweep = 3
        _Do-Broadcast
        exit 0
    }
    'Watch' {
        Write-Output ("brain-broadcast Watch loop starting interval=" + $IntervalSec + "s window=" + $WindowHours + "h")
        while ($true) {
            try { [void](_Do-Broadcast) } catch { Write-Output ("watch-tick FAIL :: " + ($_.Exception.Message)) }
            Start-Sleep -Seconds $IntervalSec
        }
    }
    'Status' {
        $state = _Load-State
        $cnt = if ($state.files) { @($state.files.Keys).Count } else { 0 }
        Write-Output ("last_sweep=" + $state.last_sweep + " tracked_files=" + $cnt + " state=" + $StatePath)
    }
}
