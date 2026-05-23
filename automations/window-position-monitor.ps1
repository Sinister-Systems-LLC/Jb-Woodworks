# Author: RKOJ-ELENO :: 2026-05-23
# window-position-monitor.ps1
#
# Background watcher for spawned terminal windows. Captures final window
# rect on process exit so the next launch can restore the same position.
#
# Called fire-and-forget by start-sinister-session.ps1 Launch-Session:
#   Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
#     '-NoProfile','-ExecutionPolicy','Bypass',
#     '-File', 'D:\Sinister Sanctum\automations\window-position-monitor.ps1',
#     '-TargetPid', <pid>, '-ProjectKey', <key>, '-SanctumRoot', <root>
#   )
#
# Writes to: <SanctumRoot>\_shared-memory\window-positions\<ProjectKey>.json
# Schema:   { x, y, w, h, monitor_index, ts_utc, captured_at, project_key, agent_pid }
#
# Operator directive 2026-05-23 evening: "i also want the resume of the
# projkect to place it in the same place the terminal was in when it was
# closed. if something is already in that position then just open without
# position set"

param(
    [Parameter(Mandatory=$true)][int]$TargetPid,
    [Parameter(Mandatory=$true)][string]$ProjectKey,
    [Parameter(Mandatory=$true)][string]$SanctumRoot,
    [int]$PollSeconds = 5,
    [int]$MaxLifetimeMinutes = 720
)

$ErrorActionPreference = 'SilentlyContinue'

# Win32 — Add-Type once per session
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

$outDir = Join-Path $SanctumRoot '_shared-memory\window-positions'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outPath = Join-Path $outDir ($ProjectKey + '.json')

$startTime = Get-Date
$maxEnd = $startTime.AddMinutes($MaxLifetimeMinutes)

$lastRect = $null
$attempts = 0

while ((Get-Date) -lt $maxEnd) {
    $proc = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
    if (-not $proc) { break }
    try {
        $hwnd = $proc.MainWindowHandle
        if ($hwnd -and $hwnd -ne [IntPtr]::Zero) {
            $rect = New-Object Win32WinPos+RECT
            $ok = [Win32WinPos]::GetWindowRect($hwnd, [ref]$rect)
            if ($ok) {
                $w = $rect.Right - $rect.Left
                $h = $rect.Bottom - $rect.Top
                if ($w -gt 50 -and $h -gt 50) {
                    $lastRect = @{
                        x = $rect.Left; y = $rect.Top; w = $w; h = $h
                    }
                }
            }
        }
    } catch {}
    $attempts++
    Start-Sleep -Seconds $PollSeconds
}

# Process exited (or watcher timed out). Write last-known good rect.
if ($lastRect) {
    $payload = [pscustomobject]@{
        x              = $lastRect.x
        y              = $lastRect.y
        w              = $lastRect.w
        h              = $lastRect.h
        monitor_index  = 0
        ts_utc         = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        captured_at    = (Get-Date).ToString('o')
        project_key    = $ProjectKey
        agent_pid      = $TargetPid
        watcher        = 'window-position-monitor.ps1'
    }
    try {
        $json = $payload | ConvertTo-Json -Depth 4
        [System.IO.File]::WriteAllText($outPath, $json, [System.Text.UTF8Encoding]::new($false))
    } catch {}
}
