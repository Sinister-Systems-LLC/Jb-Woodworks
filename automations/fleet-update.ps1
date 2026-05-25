# fleet-update.ps1 - fleet-wide auto-update channel
# Author: RKOJ-ELENO :: 2026-05-24
#
# CLAUDE.md cold-start step 11 specifies this script. Operator 19:45Z:
#   "make a auto update system so that when we do changes like that all agents get them"
#
# Storage: _shared-memory/fleet-updates.jsonl  (append-only, sentinel-file lock)
# Schema:  { id, ts_utc, priority(high|normal|low), kind(doctrine|feature|fix|tool|command),
#            message, target_slugs([] = all), acks([{slug, ts_utc}, ...]), pushed_by }
#
# Actions:
#   List   -Slug <s> [-Tail N=5]                       -> JSON rows visible to this slug
#   Push   -Message "..." -Kind doctrine|feature|fix|tool|command
#          -Priority high|normal|low [-TargetSlugs "a,b"] [-PushedBy <slug>]
#   Acked  -Id <row-id> -Slug <s>                       -> append ack to row
#   Stats                                                -> per-priority counts
#
# Cold-start usage:
#   powershell -File automations\fleet-update.ps1 -Action List -Tail 5 -Slug sanctum

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('List','Push','Acked','Stats')] [string]$Action,
    [string]$Slug = '',
    [string]$Id = '',
    [string]$Message = '',
    [string]$Kind = 'feature',
    [ValidateSet('high','normal','low')] [string]$Priority = 'normal',
    [string]$TargetSlugs = '',
    [string]$PushedBy = 'sanctum',
    [int]$Tail = 5,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$JsonlPath = Join-Path $SanctumRoot '_shared-memory\fleet-updates.jsonl'
$LockPath  = Join-Path $SanctumRoot '_shared-memory\.fleet-updates.lock'

# Sentinel-file lock (same convention as log-operator-utterance.ps1).
function Acquire-Lock { param([int]$TimeoutSec=10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            # 10s stale-reclaim.
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
function Release-Lock {
    try { if (Test-Path $LockPath) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue } } catch {}
}

function _Read-Rows {
    if (-not (Test-Path $JsonlPath)) { return @() }
    $rows = @()
    foreach ($l in (Get-Content $JsonlPath -ErrorAction SilentlyContinue)) {
        if (-not $l -or -not $l.Trim()) { continue }
        try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {}
    }
    return $rows
}

function _Write-Rows { param($Rows)
    $tmp = "$JsonlPath.tmp"
    $sb = New-Object System.Text.StringBuilder
    foreach ($r in $Rows) { [void]$sb.AppendLine(($r | ConvertTo-Json -Compress -Depth 6)) }
    [System.IO.File]::WriteAllText($tmp, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
    Move-Item -Path $tmp -Destination $JsonlPath -Force
}

function _Is-Visible { param($Row, [string]$ToSlug)
    if (-not $Row.target_slugs -or @($Row.target_slugs).Count -eq 0) { return $true }  # fleet-wide
    if (-not $ToSlug) { return $true }
    return (@($Row.target_slugs) -contains $ToSlug)
}

function _Has-Acked { param($Row, [string]$Slug)
    if (-not $Row.acks) { return $false }
    foreach ($a in @($Row.acks)) { if ($a.slug -eq $Slug) { return $true } }
    return $false
}

switch ($Action) {
    'List' {
        $rows = _Read-Rows
        $visible = @($rows | Where-Object { _Is-Visible -Row $_ -ToSlug $Slug })
        # Filter out already-acked rows for this slug (avoid re-surfacing handled items).
        if ($Slug) { $visible = @($visible | Where-Object { -not (_Has-Acked -Row $_ -Slug $Slug) }) }
        $out = $visible | Select-Object -Last $Tail
        if ($out.Count -eq 0) { Write-Output '[]'; exit 0 }
        $out | ConvertTo-Json -Depth 6 -Compress
    }
    'Push' {
        if (-not $Message) { Write-Error 'Push requires -Message'; exit 2 }
        if (-not (Acquire-Lock)) { Write-Error 'lock contention'; exit 3 }
        try {
            $rows = @(_Read-Rows)
            $newId = 'fu-' + (Get-Date -Format 'yyyyMMddHHmmss') + '-' + ([guid]::NewGuid().ToString().Substring(0,6))
            $targets = if ($TargetSlugs) { @($TargetSlugs -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) } else { @() }
            $newRow = [pscustomobject]@{
                id           = $newId
                ts_utc       = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
                priority     = $Priority
                kind         = $Kind
                message      = $Message
                target_slugs = $targets
                pushed_by    = $PushedBy
                acks         = @()
            }
            $rows = $rows + $newRow
            _Write-Rows -Rows $rows
            $targetStr = if ($targets.Count -eq 0) { 'fleet-wide' } else { ($targets -join ',') }
            Write-Output ("pushed id=" + $newId + " priority=" + $Priority + " kind=" + $Kind + " targets=" + $targetStr)
        } finally { Release-Lock }
    }
    'Acked' {
        if (-not $Id) { Write-Error 'Acked requires -Id'; exit 2 }
        if (-not $Slug) { Write-Error 'Acked requires -Slug'; exit 2 }
        if (-not (Acquire-Lock)) { Write-Error 'lock contention'; exit 3 }
        try {
            $rows = _Read-Rows
            $found = $false
            foreach ($r in $rows) {
                if ($r.id -ne $Id) { continue }
                $found = $true
                if (-not $r.acks) { $r | Add-Member -MemberType NoteProperty -Name acks -Value @() -Force }
                if (_Has-Acked -Row $r -Slug $Slug) { Write-Output "already-acked id=$Id slug=$Slug"; break }
                $r.acks = @($r.acks) + ,[pscustomobject]@{
                    slug   = $Slug
                    ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
                }
                Write-Output ("acked id=$Id slug=$Slug")
                break
            }
            if (-not $found) { Write-Error "id not found: $Id"; exit 4 }
            _Write-Rows -Rows $rows
        } finally { Release-Lock }
    }
    'Stats' {
        $rows = _Read-Rows
        $high = @($rows | Where-Object { $_.priority -eq 'high' }).Count
        $norm = @($rows | Where-Object { $_.priority -eq 'normal' }).Count
        $low  = @($rows | Where-Object { $_.priority -eq 'low' }).Count
        $total = $rows.Count
        Write-Output ("fleet-updates total=$total high=$high normal=$norm low=$low file=$JsonlPath")
    }
}
