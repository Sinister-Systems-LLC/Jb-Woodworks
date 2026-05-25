# Author: RKOJ-ELENO :: 2026-05-24
# window-position-monitor.ps1
#
# TWO MODES:
#   (A) Per-PID watcher (LEGACY, do not change call surface)
#       Fire-and-forget per spawn. Polls one process, writes last-known rect
#       on exit. Called by start-sinister-session.ps1 Launch-Session as:
#         -TargetPid <pid> -ProjectKey <key> -SanctumRoot <root>
#
#   (B) Fleet sweep (NEW 2026-05-24, RKOJ-ELENO)
#       -Action Snapshot         : one-shot — for every live spawn in
#                                  spawned-windows.jsonl, write its current
#                                  position .json (if changed > 50px).
#       -Action Watch -IntervalSec 30  : loop Snapshot on a timer (cap 10000 iters).
#       Detects process exit between snapshots: writes the last-known rect
#       one final time so reopen lands where it was closed (even after crash).
#
# Writes to: <SanctumRoot>\_shared-memory\window-positions\<ProjectKey>.json
# Schema:    { x, y, w, h, monitor_index, ts_utc, captured_at, project_key, agent_pid, watcher }
#
# Operator directive 2026-05-24 19:45Z: "i want sessions to reopen in the
# position on the desktop that they were closed in"
# (reinforces 2026-05-23 evening: "i also want the resume of the projkect to
# place it in the same place the terminal was in when it was closed.")

param(
    # Per-PID mode (legacy, call surface frozen)
    [int]$TargetPid = 0,
    [string]$ProjectKey = '',
    [string]$SanctumRoot = '',
    [int]$PollSeconds = 15,
    [int]$MaxLifetimeMinutes = 60,
    # Fleet sweep mode (new)
    [ValidateSet('','Snapshot','Watch')]
    [string]$Action = '',
    [int]$IntervalSec = 30,
    [int]$MaxIterations = 10000,
    [int]$MinDeltaPx = 50
)

$ErrorActionPreference = 'SilentlyContinue'

# ============================================================
# Win32 — Add-Type once per session (shared across both modes)
# ============================================================
if (-not ('Win32WinPos' -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32WinPos {
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@ -ErrorAction SilentlyContinue
}

# ============================================================
# SHARED HELPERS
# ============================================================
function Get-SanctumRoot {
    param([string]$Hint)
    if ($Hint -and (Test-Path $Hint)) { return (Resolve-Path $Hint).Path }
    # Script lives at <SanctumRoot>\automations\window-position-monitor.ps1
    $self = $PSCommandPath
    if (-not $self) { $self = $MyInvocation.MyCommand.Path }
    if ($self) { return (Split-Path -Parent (Split-Path -Parent $self)) }
    return 'D:\Sinister Sanctum'
}

function Get-WindowOwningPid {
    # claude.exe / bash.exe / mintty-child processes have no MainWindowHandle —
    # walk up the parent chain (Win32_Process.ParentProcessId) until we find an
    # ancestor with a non-zero MainWindowHandle (the terminal: mintty,
    # WindowsTerminal, conhost, etc.). Cap walk depth to avoid loops.
    param([int]$StartPid, [int]$MaxDepth = 8)
    $cur = Get-Process -Id $StartPid -ErrorAction SilentlyContinue
    if (-not $cur) { return $null }
    for ($d = 0; $d -lt $MaxDepth; $d++) {
        if ($cur.MainWindowHandle -ne 0 -and $cur.MainWindowHandle -ne [IntPtr]::Zero) {
            return $cur
        }
        $ppid = $null
        try {
            $ppid = (Get-CimInstance Win32_Process -Filter "ProcessId=$($cur.Id)" -ErrorAction SilentlyContinue).ParentProcessId
        } catch {}
        if (-not $ppid -or $ppid -eq 0) { return $null }
        $next = Get-Process -Id $ppid -ErrorAction SilentlyContinue
        if (-not $next) { return $null }
        # Stop if we've climbed too high (explorer/services/wininit are not session windows)
        if ($next.ProcessName -in @('explorer','services','wininit','svchost','smss','csrss','winlogon','System')) {
            return $null
        }
        $cur = $next
    }
    return $null
}

function Get-ProcessWindowRect {
    param(
        [int]$ProcId,
        [int]$FallbackPid = 0
    )
    try {
        $owner = Get-WindowOwningPid -StartPid $ProcId
        if (-not $owner -and $FallbackPid -gt 0) {
            $owner = Get-WindowOwningPid -StartPid $FallbackPid
        }
        if (-not $owner) { return $null }
        $hwnd = $owner.MainWindowHandle
        if (-not $hwnd -or $hwnd -eq [IntPtr]::Zero) { return $null }
        $rect = New-Object Win32WinPos+RECT
        $ok = [Win32WinPos]::GetWindowRect($hwnd, [ref]$rect)
        if (-not $ok) { return $null }
        $w = $rect.Right - $rect.Left
        $h = $rect.Bottom - $rect.Top
        if ($w -le 50 -or $h -le 50) { return $null }
        return @{ x = $rect.Left; y = $rect.Top; w = $w; h = $h; owner_pid = $owner.Id; owner_name = $owner.ProcessName }
    } catch { return $null }
}

function Write-PositionJson {
    param(
        [string]$OutDir,
        [string]$ProjectKey,
        [int]$ProcId,
        [hashtable]$Rect,
        [string]$Watcher
    )
    try {
        if (-not (Test-Path $OutDir)) {
            New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
        }
        $outPath = Join-Path $OutDir ($ProjectKey + '.json')
        $payload = [pscustomobject]@{
            x              = $Rect.x
            y              = $Rect.y
            w              = $Rect.w
            h              = $Rect.h
            monitor_index  = 0
            ts_utc         = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            captured_at    = (Get-Date).ToString('o')
            project_key    = $ProjectKey
            agent_pid      = $ProcId
            watcher        = $Watcher
        }
        $json = $payload | ConvertTo-Json -Depth 4
        [System.IO.File]::WriteAllText($outPath, $json, [System.Text.UTF8Encoding]::new($false))
        return $true
    } catch { return $false }
}

function Read-SpawnedWindows {
    param([string]$SanctumRoot)
    $path = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
    if (-not (Test-Path $path)) { return @() }
    $rows = @()
    try {
        $lines = Get-Content -LiteralPath $path -Encoding UTF8 -ErrorAction SilentlyContinue
        foreach ($ln in $lines) {
            if ([string]::IsNullOrWhiteSpace($ln)) { continue }
            try {
                $row = $ln | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($row -and $row.pid -and $row.project) { $rows += $row }
            } catch {}
        }
    } catch {}
    # De-dupe: latest row per PID wins (file is append-only).
    $byPid = @{}
    foreach ($r in $rows) { $byPid[[int]$r.pid] = $r }
    return @($byPid.Values)
}

function Is-Live-Spawn {
    param($Row)
    try {
        $p = Get-Process -Id ([int]$Row.pid) -ErrorAction SilentlyContinue
        return [bool]$p
    } catch { return $false }
}

function Rect-Changed {
    param($Old, $New, [int]$MinDelta)
    if (-not $Old) { return $true }
    if (-not $New) { return $false }
    if ([Math]::Abs($Old.x - $New.x) -ge $MinDelta) { return $true }
    if ([Math]::Abs($Old.y - $New.y) -ge $MinDelta) { return $true }
    if ([Math]::Abs($Old.w - $New.w) -ge $MinDelta) { return $true }
    if ([Math]::Abs($Old.h - $New.h) -ge $MinDelta) { return $true }
    return $false
}

# ============================================================
# MODE A — PER-PID WATCHER (legacy contract)
# ============================================================
function Invoke-PerPidWatcher {
    param(
        [int]$TargetPid,
        [string]$ProjectKey,
        [string]$SanctumRoot,
        [int]$PollSeconds,
        [int]$MaxLifetimeMinutes
    )
    $outDir = Join-Path $SanctumRoot '_shared-memory\window-positions'
    if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    $startTime = Get-Date
    $maxEnd = $startTime.AddMinutes($MaxLifetimeMinutes)
    $lastRect = $null
    $zeroHwndStreak = 0

    while ((Get-Date) -lt $maxEnd) {
        $proc = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
        if (-not $proc) { break }
        try {
            $hwnd = $proc.MainWindowHandle
            if ($hwnd -and $hwnd -ne [IntPtr]::Zero) {
                $zeroHwndStreak = 0
                $rect = Get-ProcessWindowRect -ProcId $TargetPid
                if ($rect) { $lastRect = $rect }
            } else {
                $zeroHwndStreak++
                if ($zeroHwndStreak -ge 3) { break }
            }
        } catch {}
        Start-Sleep -Seconds $PollSeconds
    }
    if ($lastRect) {
        Write-PositionJson -OutDir $outDir -ProjectKey $ProjectKey -ProcId $TargetPid -Rect $lastRect -Watcher 'window-position-monitor.ps1:per-pid'
    }
}

# ============================================================
# MODE B — FLEET SWEEP (snapshot / watch)
# ============================================================
function Invoke-FleetSnapshot {
    param(
        [string]$SanctumRoot,
        [hashtable]$LastRects,
        [hashtable]$LastSeenPid,
        [int]$MinDeltaPx,
        [switch]$Quiet
    )
    $outDir = Join-Path $SanctumRoot '_shared-memory\window-positions'
    $rows = Read-SpawnedWindows -SanctumRoot $SanctumRoot
    $live = 0
    $written = 0
    $exited = 0

    # Track which PIDs we've seen alive at least once
    $alivePids = @{}

    foreach ($row in $rows) {
        $procId = [int]$row.pid
        $key = [string]$row.project
        if (-not $key) { continue }
        if (Is-Live-Spawn -Row $row) {
            $live++
            $alivePids[$procId] = $true
            $launcherPid = 0
            try { if ($row.launcher_pid) { $launcherPid = [int]$row.launcher_pid } } catch {}
            $rect = Get-ProcessWindowRect -ProcId $procId -FallbackPid $launcherPid
            if ($rect) {
                $old = $LastRects[$key]
                if (Rect-Changed -Old $old -New $rect -MinDelta $MinDeltaPx) {
                    if (Write-PositionJson -OutDir $outDir -ProjectKey $key -ProcId $procId -Rect $rect -Watcher 'window-position-monitor.ps1:sweep') {
                        $written++
                        $LastRects[$key] = $rect
                        if (-not $Quiet) {
                            Write-Host ("  [WRITE] {0,-22} pid={1,-6} {2},{3} {4}x{5}" -f $key,$procId,$rect.x,$rect.y,$rect.w,$rect.h)
                        }
                    }
                }
                # Cache PID->key mapping for exit-detection on next pass
                $LastSeenPid[$procId] = @{ key = $key; rect = $rect }
            }
        }
    }

    # Exit detection: any PID we saw last sweep but is NOT alive now -> write last known
    $deadPids = @()
    foreach ($dp in @($LastSeenPid.Keys)) {
        if (-not $alivePids.ContainsKey($dp)) {
            $entry = $LastSeenPid[$dp]
            if ($entry -and $entry.rect -and $entry.key) {
                if (Write-PositionJson -OutDir $outDir -ProjectKey $entry.key -ProcId $dp -Rect $entry.rect -Watcher 'window-position-monitor.ps1:sweep-exit') {
                    $exited++
                    if (-not $Quiet) {
                        Write-Host ("  [EXIT ] {0,-22} pid={1,-6} final {2},{3} {4}x{5}" -f $entry.key,$dp,$entry.rect.x,$entry.rect.y,$entry.rect.w,$entry.rect.h) -ForegroundColor Yellow
                    }
                }
            }
            $deadPids += $dp
        }
    }
    foreach ($dp in $deadPids) { $LastSeenPid.Remove($dp) | Out-Null }

    return @{ live = $live; written = $written; exited = $exited; total_rows = $rows.Count }
}

function Invoke-FleetWatch {
    param(
        [string]$SanctumRoot,
        [int]$IntervalSec,
        [int]$MaxIterations,
        [int]$MinDeltaPx
    )
    $lastRects = @{}
    $lastSeenPid = @{}
    Write-Host "window-position-monitor :: Watch mode (interval=${IntervalSec}s, max-iters=$MaxIterations, min-delta=${MinDeltaPx}px)" -ForegroundColor Cyan
    Write-Host "SanctumRoot: $SanctumRoot"
    for ($i = 1; $i -le $MaxIterations; $i++) {
        try {
            $stats = Invoke-FleetSnapshot -SanctumRoot $SanctumRoot -LastRects $lastRects -LastSeenPid $lastSeenPid -MinDeltaPx $MinDeltaPx
            Write-Host ("[{0,4}] {1} live | {2} written | {3} exited (rows scanned: {4})" -f $i,$stats.live,$stats.written,$stats.exited,$stats.total_rows) -ForegroundColor DarkGray
        } catch {
            Write-Host ("[{0,4}] ERROR: {1}" -f $i,$_.Exception.Message) -ForegroundColor Red
        }
        Start-Sleep -Seconds $IntervalSec
    }
}

# ============================================================
# DISPATCH
# ============================================================
try {
    if ($Action -eq 'Snapshot' -or $Action -eq 'Watch') {
        $root = Get-SanctumRoot -Hint $SanctumRoot
        if ($Action -eq 'Snapshot') {
            $lastRects = @{}
            $lastSeenPid = @{}
            Write-Host "window-position-monitor :: Snapshot (one-shot)" -ForegroundColor Cyan
            Write-Host "SanctumRoot: $root"
            $stats = Invoke-FleetSnapshot -SanctumRoot $root -LastRects $lastRects -LastSeenPid $lastSeenPid -MinDeltaPx $MinDeltaPx
            Write-Host ("DONE :: live={0} written={1} exited={2} rows_scanned={3}" -f $stats.live,$stats.written,$stats.exited,$stats.total_rows) -ForegroundColor Green
            exit 0
        } else {
            Invoke-FleetWatch -SanctumRoot $root -IntervalSec $IntervalSec -MaxIterations $MaxIterations -MinDeltaPx $MinDeltaPx
            exit 0
        }
    } else {
        # Legacy per-PID mode — require the three legacy params
        if ($TargetPid -le 0 -or -not $ProjectKey -or -not $SanctumRoot) {
            Write-Host "ERROR: legacy per-PID mode requires -TargetPid, -ProjectKey, -SanctumRoot" -ForegroundColor Red
            Write-Host "       fleet sweep: -Action Snapshot | -Action Watch [-IntervalSec 30]" -ForegroundColor Yellow
            exit 2
        }
        Invoke-PerPidWatcher -TargetPid $TargetPid -ProjectKey $ProjectKey -SanctumRoot $SanctumRoot -PollSeconds $PollSeconds -MaxLifetimeMinutes $MaxLifetimeMinutes
        exit 0
    }
} catch {
    Write-Host "FATAL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
