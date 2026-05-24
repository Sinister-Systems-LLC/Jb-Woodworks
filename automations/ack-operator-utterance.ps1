# ack-operator-utterance.ps1 — acknowledge / resolve an operator-utterance row
# Author: RKOJ-ELENO :: 2026-05-24
#
# Usage:
#   powershell -File ack-operator-utterance.ps1 -TsUtc "2026-05-24T12:34:56Z" -AgentSlug sanctum [-Deliverable "..."] [-Resolve]
#
# Finds the row by ts_utc, appends agent slug to agents_acked (if new),
# appends deliverable to deliverables (if provided), flips status new->acknowledged,
# and (only with -Resolve) flips acknowledged->resolved with resolved_at_utc stamp.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$TsUtc,
    [Parameter(Mandatory=$true)] [string]$AgentSlug,
    [string]$Deliverable = '',
    [switch]$Resolve,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$JsonlPath = Join-Path $SanctumRoot '_shared-memory\operator-utterances.jsonl'
$LockPath  = Join-Path $SanctumRoot '_shared-memory\.operator-utterances.lock'

function Acquire-Lock {
    param([string]$Path, [int]$TimeoutSec = 10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            Start-Sleep -Milliseconds 100
        }
    }
}

function Release-Lock {
    param([string]$Path)
    if (Test-Path $Path) { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue }
}

function Read-AllRows {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return @() }
    $rows = @()
    $lines = Get-Content -LiteralPath $Path -Encoding UTF8
    foreach ($line in $lines) {
        if (-not $line.Trim()) { continue }
        try { $rows += ,($line | ConvertFrom-Json) } catch { $rows += ,@{ _raw = $line; _bad = $true } }
    }
    return $rows
}

function Write-AllRows {
    param([string]$Path, [object[]]$Rows)
    $sb = [System.Text.StringBuilder]::new()
    foreach ($r in $Rows) {
        if ($r._bad) { $null = $sb.AppendLine($r._raw); continue }
        $json = $r | ConvertTo-Json -Compress -Depth 10
        $null = $sb.AppendLine($json)
    }
    [System.IO.File]::WriteAllText($Path, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
}

if (-not (Test-Path $JsonlPath)) {
    Write-Error "operator-utterances.jsonl not found at $JsonlPath"
    exit 3
}

if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) {
    Write-Error "Could not acquire lock at $LockPath after 10s"
    exit 2
}

try {
    $rows = @(Read-AllRows -Path $JsonlPath)
    $idx = -1
    for ($i = 0; $i -lt $rows.Count; $i++) {
        if ($rows[$i].ts_utc -eq $TsUtc) { $idx = $i; break }
    }
    if ($idx -lt 0) {
        Write-Error "Row with ts_utc=$TsUtc not found"
        exit 4
    }

    $row = $rows[$idx]

    # agents_acked: append if new
    $ackList = @($row.agents_acked)
    if ($ackList -notcontains $AgentSlug) { $ackList += $AgentSlug }
    $row.agents_acked = $ackList

    # deliverables: append if provided
    if ($Deliverable) {
        $delList = @($row.deliverables)
        $delList += $Deliverable
        $row.deliverables = $delList
    }

    # status transition
    if ($row.status -eq 'new') { $row.status = 'acknowledged' }
    if ($Resolve.IsPresent) {
        if (@($row.deliverables).Count -lt 1) {
            Write-Error "Cannot -Resolve a row with zero deliverables; supply -Deliverable first or in same call"
            exit 5
        }
        $row.status = 'resolved'
        $row.resolved_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    }

    $rows[$idx] = $row
    Write-AllRows -Path $JsonlPath -Rows $rows

    Write-Output "ack ts_utc=$TsUtc agent=$AgentSlug status=$($row.status) deliverables=$(@($row.deliverables).Count)"
} finally {
    Release-Lock -Path $LockPath
}
