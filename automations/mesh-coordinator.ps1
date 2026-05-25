# mesh-coordinator.ps1 — multi-agent file-lock + TTL coordinator
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose:
#   Prevent toe-stepping when 5+ EVE sessions run swarm+loop concurrently.
#   Each agent registers a "focus" (project | path | topic) with a TTL.
#   Other agents Check before they edit; if locked, they pick a different slice.
#
# Storage: _shared-memory/mesh-locks/<sanitized-focus>.json  (one file per active lock)
# Lock shape:
#   { lock_id, focus, owner_slug, owner_display, owner_machine, acquired_utc,
#     expires_utc, heartbeat_utc, ttl_seconds, hint, blast_radius }
#
# Actions:
#   Register   -Slug -Display -Focus [-TtlSeconds 1800] [-Hint] [-BlastRadius single|lane|fleet] [-Force]
#   Heartbeat  -Slug -Focus               (extends expires_utc to now+ttl)
#   Release    -Slug -Focus
#   Check      -Focus                     (returns conflict | clear; flags PEER vs LOCAL owner)
#   List       [-Slug]                    (all active, optionally filtered)
#   ListPeer                              (peer-machine-only locks; needs sinister-link state)
#   Sweep                                 (purge expired locks)
#
# Exit codes: 0 ok / 1 conflict / 2 missing arg / 3 io fail
# Composes with: agent-modes/<slug>.json (swarm+loop flags) + heartbeats/ (per-slug)
#                + sinister-link-state.json (owner_machine -> peer detection)
#
# Cross-machine extension (RKOJ-ELENO :: 2026-05-25):
#   Lock files now carry owner_machine ($env:COMPUTERNAME lowercased). When
#   Sinister LINK is paired and the auto-push daemon has synced the peer's
#   lock files into _shared-memory/mesh-locks/, Check correctly reports peer-
#   owned locks. ListPeer filters to peer-owned-only for "what is Leo doing
#   right now?" visibility.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Register','Heartbeat','Release','Check','List','ListPeer','Sweep')]
    [string]$Action,

    [string]$Slug = '',
    [string]$Display = '',
    [string]$Focus = '',
    [int]$TtlSeconds = 1800,
    [string]$Hint = '',
    [ValidateSet('single','lane','fleet')]
    [string]$BlastRadius = 'lane',
    [switch]$Force,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$LocksDir = Join-Path $SanctumRoot '_shared-memory\mesh-locks'
if (-not (Test-Path $LocksDir)) { New-Item -ItemType Directory -Path $LocksDir -Force | Out-Null }

function Sanitize-Focus { param([string]$f)
    # File-safe slug. Keep alnum + .-_, replace others with _
    $sanitized = ($f -replace '[^a-zA-Z0-9._-]', '_').ToLower()
    if ($sanitized.Length -gt 80) { $sanitized = $sanitized.Substring(0, 80) }
    return $sanitized
}
function Utc-Now { return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function Parse-Utc { param([string]$s) return [DateTime]::Parse($s).ToUniversalTime() }
function Write-Lock { param([string]$Path, [hashtable]$Obj)
    $json = $Obj | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}
function Read-Lock { param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}
function Is-Expired { param($Lock)
    if (-not $Lock) { return $true }
    $exp = Parse-Utc $Lock.expires_utc
    return ([DateTime]::UtcNow -gt $exp)
}

function Get-LocalMachineId {
    # Stable lowercase machine id. Prefer sinister-link-state.local_machine
    # so the value matches what the peer sees in their synced mesh-locks/.
    $statePath = Join-Path $SanctumRoot '_shared-memory\sinister-link-state.json'
    if (Test-Path $statePath) {
        try {
            $s = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($s.local_machine) { return $s.local_machine }
        } catch {}
    }
    $n = $env:COMPUTERNAME
    if (-not $n) { return 'unknown-machine' }
    return $n.ToLower()
}

function Get-PeerMachineId {
    $statePath = Join-Path $SanctumRoot '_shared-memory\sinister-link-state.json'
    if (-not (Test-Path $statePath)) { return '' }
    try {
        $s = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($s.peer -and $s.peer.name) { return $s.peer.name }
    } catch {}
    return ''
}

switch ($Action) {

    'Register' {
        if (-not $Slug -or -not $Focus) { Write-Host "ERR: -Slug and -Focus required"; exit 2 }
        if (-not $Display) { $Display = $Slug }
        $name = Sanitize-Focus $Focus
        $path = Join-Path $LocksDir "$name.json"
        $existing = Read-Lock $path
        if ($existing -and -not (Is-Expired $existing) -and $existing.owner_slug -ne $Slug -and -not $Force) {
            Write-Host "CONFLICT: focus '$Focus' owned by $($existing.owner_slug) (expires $($existing.expires_utc))"
            Write-Host "  hint: $($existing.hint)"
            Write-Host "  use -Force to seize, or pick a different focus slice"
            exit 1
        }
        $now = Utc-Now
        $expires = (Get-Date).ToUniversalTime().AddSeconds($TtlSeconds).ToString("yyyy-MM-ddTHH:mm:ssZ")
        $lock = @{
            lock_id        = [guid]::NewGuid().ToString('N').Substring(0,12)
            focus          = $Focus
            owner_slug     = $Slug
            owner_display  = $Display
            owner_machine  = (Get-LocalMachineId)
            acquired_utc   = $now
            expires_utc    = $expires
            heartbeat_utc  = $now
            ttl_seconds    = $TtlSeconds
            hint           = $Hint
            blast_radius   = $BlastRadius
            seized_from    = if ($existing -and $existing.owner_slug -ne $Slug) { $existing.owner_slug } else { '' }
        }
        Write-Lock $path $lock
        Write-Host "OK: registered '$Focus' to $Slug (expires $expires, ttl ${TtlSeconds}s, blast=$BlastRadius)"
        exit 0
    }

    'Heartbeat' {
        if (-not $Slug -or -not $Focus) { Write-Host "ERR: -Slug and -Focus required"; exit 2 }
        $name = Sanitize-Focus $Focus
        $path = Join-Path $LocksDir "$name.json"
        $existing = Read-Lock $path
        if (-not $existing) { Write-Host "NOTFOUND: no lock for '$Focus'"; exit 1 }
        if ($existing.owner_slug -ne $Slug) { Write-Host "FORBIDDEN: lock owned by $($existing.owner_slug), not $Slug"; exit 1 }
        $now = Utc-Now
        $expires = (Get-Date).ToUniversalTime().AddSeconds([int]$existing.ttl_seconds).ToString("yyyy-MM-ddTHH:mm:ssZ")
        # Rebuild as hashtable for round-trip
        $lock = @{}
        $existing.PSObject.Properties | ForEach-Object { $lock[$_.Name] = $_.Value }
        $lock.heartbeat_utc = $now
        $lock.expires_utc   = $expires
        Write-Lock $path $lock
        Write-Host "OK: heartbeat '$Focus' (expires $expires)"
        exit 0
    }

    'Release' {
        if (-not $Slug -or -not $Focus) { Write-Host "ERR: -Slug and -Focus required"; exit 2 }
        $name = Sanitize-Focus $Focus
        $path = Join-Path $LocksDir "$name.json"
        $existing = Read-Lock $path
        if (-not $existing) { Write-Host "NOTFOUND: no lock for '$Focus'"; exit 0 }
        if ($existing.owner_slug -ne $Slug -and -not $Force) {
            Write-Host "FORBIDDEN: lock owned by $($existing.owner_slug); use -Force to release anyway"
            exit 1
        }
        Remove-Item -LiteralPath $path -Force
        Write-Host "OK: released '$Focus' (was owned by $($existing.owner_slug))"
        exit 0
    }

    'Check' {
        if (-not $Focus) { Write-Host "ERR: -Focus required"; exit 2 }
        $name = Sanitize-Focus $Focus
        $path = Join-Path $LocksDir "$name.json"
        $existing = Read-Lock $path
        if (-not $existing) { Write-Host "CLEAR: '$Focus' has no active lock"; exit 0 }
        if (Is-Expired $existing) { Write-Host "STALE: '$Focus' lock expired at $($existing.expires_utc), owner was $($existing.owner_slug)"; exit 0 }
        $local = Get-LocalMachineId
        $om    = if ($existing.owner_machine) { $existing.owner_machine } else { '(unknown)' }
        $peerTag = if ($existing.owner_machine -and $existing.owner_machine -ne $local) { ' [PEER]' } else { '' }
        Write-Host "LOCKED${peerTag}: '$Focus' by $($existing.owner_slug)@$om until $($existing.expires_utc) (hint: $($existing.hint))"
        exit 1
    }

    'List' {
        $files = Get-ChildItem -LiteralPath $LocksDir -Filter '*.json' -File -ErrorAction SilentlyContinue
        $rows = @()
        $local = Get-LocalMachineId
        foreach ($f in $files) {
            $L = Read-Lock $f.FullName
            if (-not $L) { continue }
            if ($Slug -and $L.owner_slug -ne $Slug) { continue }
            $state = if (Is-Expired $L) { 'EXPIRED' } else { 'ACTIVE' }
            $loc = if ($L.owner_machine -eq $local) { 'LOCAL' } elseif ($L.owner_machine) { 'PEER' } else { 'UNK' }
            $rows += [PSCustomObject]@{
                State   = $state
                Loc     = $loc
                Owner   = $L.owner_slug
                Machine = $L.owner_machine
                Focus   = $L.focus
                Expires = $L.expires_utc
                Blast   = $L.blast_radius
                Hint    = $L.hint
            }
        }
        if ($rows.Count -eq 0) { Write-Host "no active locks"; exit 0 }
        $rows | Sort-Object State, Loc, Owner | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }

    'ListPeer' {
        $peer = Get-PeerMachineId
        if (-not $peer) {
            Write-Host "NOT-PAIRED: no sinister-link state; nothing to list"
            exit 0
        }
        $files = Get-ChildItem -LiteralPath $LocksDir -Filter '*.json' -File -ErrorAction SilentlyContinue
        $rows = @()
        foreach ($f in $files) {
            $L = Read-Lock $f.FullName
            if (-not $L) { continue }
            if ($L.owner_machine -ne $peer) { continue }
            $state = if (Is-Expired $L) { 'EXPIRED' } else { 'ACTIVE' }
            $rows += [PSCustomObject]@{
                State   = $state
                Owner   = $L.owner_slug
                Focus   = $L.focus
                Expires = $L.expires_utc
                Hint    = $L.hint
            }
        }
        if ($rows.Count -eq 0) { Write-Host "no peer locks (peer=$peer)"; exit 0 }
        Write-Host "Peer ($peer) active locks:"
        $rows | Sort-Object State, Owner | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }

    'Sweep' {
        $files = Get-ChildItem -LiteralPath $LocksDir -Filter '*.json' -File -ErrorAction SilentlyContinue
        $removed = 0
        foreach ($f in $files) {
            $L = Read-Lock $f.FullName
            if (-not $L -or (Is-Expired $L)) {
                Remove-Item -LiteralPath $f.FullName -Force
                $removed++
            }
        }
        Write-Host "OK: swept $removed expired lock(s)"
        exit 0
    }
}
