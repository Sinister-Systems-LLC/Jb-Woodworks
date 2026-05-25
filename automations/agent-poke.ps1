# agent-poke.ps1 -- manual KEEP-GOING sender for stalled fleet agents
# Author: RKOJ-ELENO :: 2026-05-25
#
# Purpose:
#   Operator (or any agent) can manually poke a stalled fleet agent to keep
#   going. Composes with the relentless-loop doctrine: operator hard-canonical
#   2026-05-25T02:18Z "make the loop system on our agents actually work. make
#   it agressive." This is the manual-button counterpart to the automated
#   loop-relentless-watchdog (which fires on detected stalls).
#
# Actions:
#   Poke      -Slug <slug> [-Reason <str>] [-Priority normal|high] [-DryRun]
#     Send one KEEP-GOING message to a single agent's inbox.
#
#   PokeAll   [-Reason <str>] [-Priority normal|high] [-DryRun]
#     Send to every active loop=on agent (operator-emergency-button).
#     Determines active set = intersection of:
#       (a) heartbeats/<slug>.json newer than 60 min
#       (b) agent-modes/<slug>.json with loop=true
#
#   Status    [-Tail 50]
#     List recent pokes (last 24h) grouped by slug.
#
# Output:
#   _shared-memory/inbox/<slug>/<utc>-from-agent-poke-<rand>.json
#   schema: sinister.cross-agent-msg.v1 (kind=loop-poke)
#
# Constraints:
#   - PowerShell 5.1-safe (no scriptblock-in-replace)
#   - UTF-8 no-BOM via [System.IO.File]::WriteAllText
#   - mesh-coord lock on inbox dir while writing
#   - Idempotent: random suffix in filename so spam-poke is OK
#
# Exit codes: 0 ok / 1 partial fail / 2 missing arg / 3 io fail

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Poke','PokeAll','Status')]
    [string]$Action,

    [string]$Slug = '',
    [string]$Reason = '',
    [ValidateSet('normal','high')]
    [string]$Priority = 'high',
    [switch]$DryRun,
    [int]$Tail = 50,
    [int]$ActiveMinutes = 60,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'

$InboxRoot     = Join-Path $SanctumRoot '_shared-memory\inbox'
$HeartbeatsDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$ModesDir      = Join-Path $SanctumRoot '_shared-memory\agent-modes'
$MeshCoord     = Join-Path $SanctumRoot 'automations\mesh-coordinator.ps1'

$DefaultBody = "Operator hard-canonical 2026-05-25T02:18Z 'make agents relentlessly pursue goal'. Pick next queue item, ship it, loop. If genuinely blocked: 1-line block reason to OPERATOR-ACTION-QUEUE.md AND ScheduleWakeup <=270s. DO NOT just end turn."

function Utc-Now { return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function Utc-Stamp { return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmm'Z'") }

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function New-PokeFilename {
    param([string]$Slug)
    $stamp = Utc-Stamp
    $rand  = -join ((48..57 + 97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
    return "$stamp-from-agent-poke-$rand.json"
}

function Build-PokePayload {
    param([string]$ToSlug, [string]$Body, [string]$Pri)
    $obj = [ordered]@{
        schema_version  = 'sinister.cross-agent-msg.v1'
        ts_utc          = Utc-Now
        from_slug       = 'agent-poke'
        from_display    = 'Agent Poke (manual)'
        to_slug         = $ToSlug
        priority        = $Pri
        kind            = 'loop-poke'
        subject         = 'KEEP GOING -- operator-requested poke'
        body            = $Body
        expected_action = 'resume iteration OR address utterance OR write block + ScheduleWakeup <=270s'
    }
    return $obj
}

function Acquire-MeshLock {
    param([string]$Focus, [int]$Ttl = 60)
    if (-not (Test-Path $MeshCoord)) { return $true }
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $MeshCoord -Action Register `
            -Slug 'agent-poke' -Display 'Agent Poke' -Focus $Focus -TtlSeconds $Ttl -BlastRadius single -Force *> $null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Release-MeshLock {
    param([string]$Focus)
    if (-not (Test-Path $MeshCoord)) { return }
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $MeshCoord -Action Release `
            -Slug 'agent-poke' -Focus $Focus *> $null
    } catch {}
}

function Send-Poke {
    param([string]$ToSlug, [string]$Body, [string]$Pri, [switch]$Dry)

    $laneDir = Join-Path $InboxRoot $ToSlug
    $payload = Build-PokePayload -ToSlug $ToSlug -Body $Body -Pri $Pri
    $fname   = New-PokeFilename -Slug $ToSlug
    $fpath   = Join-Path $laneDir $fname
    $json    = $payload | ConvertTo-Json -Depth 5

    if ($Dry) {
        Write-Host "[DRY-RUN] would write: $fpath"
        Write-Host $json
        return @{ ok = $true; path = $fpath; dry = $true }
    }

    if (-not (Test-Path $laneDir)) {
        New-Item -ItemType Directory -Path $laneDir -Force | Out-Null
    }

    $focus = "inbox/$ToSlug"
    $locked = Acquire-MeshLock -Focus $focus -Ttl 60
    try {
        Write-Utf8NoBom -Path $fpath -Text $json
        Write-Host "[POKE] $ToSlug ($Pri) -> $fname"
        return @{ ok = $true; path = $fpath; dry = $false }
    } catch {
        Write-Warning "[POKE-FAIL] $ToSlug : $_"
        return @{ ok = $false; path = $fpath; error = "$_" }
    } finally {
        if ($locked) { Release-MeshLock -Focus $focus }
    }
}

function Get-ActiveLoopSlugs {
    param([int]$MaxAgeMinutes)
    $cutoff = (Get-Date).ToUniversalTime().AddMinutes(-$MaxAgeMinutes)
    $active = @()
    if (-not (Test-Path $HeartbeatsDir)) { return $active }

    Get-ChildItem $HeartbeatsDir -Filter '*.json' -File | ForEach-Object {
        $slug = $_.BaseName
        try {
            $hb = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if (-not $hb.ts_utc) { return }
            $ts = [DateTime]::Parse($hb.ts_utc).ToUniversalTime()
            if ($ts -lt $cutoff) { return }
        } catch { return }

        # Check loop mode
        $modeFile = Join-Path $ModesDir "$slug.json"
        $loopOn = $false
        if (Test-Path $modeFile) {
            try {
                $m = Get-Content -LiteralPath $modeFile -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($m.loop -eq $true) { $loopOn = $true }
            } catch {}
        }
        if ($loopOn) { $active += $slug }
    }
    return $active
}

function Show-PokeStatus {
    param([int]$TailN)
    $cutoff = (Get-Date).ToUniversalTime().AddHours(-24)
    if (-not (Test-Path $InboxRoot)) {
        Write-Host "[STATUS] inbox root missing: $InboxRoot"
        return
    }

    $rows = @()
    Get-ChildItem $InboxRoot -Directory | ForEach-Object {
        $laneSlug = $_.Name
        if ($laneSlug -like '_*') { return }
        Get-ChildItem $_.FullName -Filter '*from-agent-poke*.json' -File -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $obj = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                if (-not $obj.ts_utc) { return }
                $ts = [DateTime]::Parse($obj.ts_utc).ToUniversalTime()
                if ($ts -lt $cutoff) { return }
                $rows += [PSCustomObject]@{
                    slug     = $laneSlug
                    ts_utc   = $obj.ts_utc
                    priority = $obj.priority
                    file     = $_.Name
                    body     = ($obj.body -replace '\s+', ' ').Substring(0, [Math]::Min(80, ($obj.body -replace '\s+', ' ').Length))
                }
            } catch {}
        }
    }

    if ($rows.Count -eq 0) {
        Write-Host "[STATUS] no pokes in last 24h"
        return
    }

    $grouped = $rows | Group-Object slug | Sort-Object Count -Descending
    Write-Host ""
    Write-Host "=== Pokes in last 24h ($($rows.Count) total across $($grouped.Count) lanes) ==="
    foreach ($g in $grouped) {
        Write-Host ""
        Write-Host "[$($g.Name)] $($g.Count) pokes"
        $g.Group | Sort-Object ts_utc -Descending | Select-Object -First $TailN | ForEach-Object {
            Write-Host "  $($_.ts_utc) [$($_.priority)] $($_.file)"
        }
    }
}

# --- main dispatch ---

switch ($Action) {
    'Poke' {
        if (-not $Slug) {
            Write-Error "Poke requires -Slug <slug>"
            exit 2
        }
        $body = if ($Reason) { "$Reason`n`n$DefaultBody" } else { $DefaultBody }
        $r = Send-Poke -ToSlug $Slug -Body $body -Pri $Priority -Dry:$DryRun
        if ($r.ok) { exit 0 } else { exit 3 }
    }

    'PokeAll' {
        $slugs = Get-ActiveLoopSlugs -MaxAgeMinutes $ActiveMinutes
        if ($slugs.Count -eq 0) {
            Write-Host "[POKE-ALL] no active loop=on agents found (heartbeats < $ActiveMinutes min + loop=true)"
            exit 0
        }
        Write-Host "[POKE-ALL] poking $($slugs.Count) agents : $($slugs -join ', ')"
        $body = if ($Reason) { "$Reason`n`n$DefaultBody" } else { $DefaultBody }
        $fails = 0
        foreach ($s in $slugs) {
            $r = Send-Poke -ToSlug $s -Body $body -Pri $Priority -Dry:$DryRun
            if (-not $r.ok) { $fails++ }
        }
        if ($fails -gt 0) { exit 1 } else { exit 0 }
    }

    'Status' {
        Show-PokeStatus -TailN $Tail
        exit 0
    }
}
