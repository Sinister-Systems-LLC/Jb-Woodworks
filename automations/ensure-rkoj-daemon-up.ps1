# ensure-rkoj-daemon-up.ps1 — auto-start the RKOJ Workstation daemon (port 5077) if it's down.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Origin: jcode-parity-probe v0.3 surfaced R21 FAIL (tcp:5077 closed) on a clean working machine.
# Companion to ensure-docker-up.ps1 — same shape: idempotent, exit-0-if-up, bounded wait, skip-if-up.
#
# The RKOJ Workstation daemon (Qt + HTTP API server) lives at:
#   automations/window-manager/desktop_app.py
# It binds :5077 (REST API, used by Forge `F2 toggle_rkoj`, Mind /diagrams, others per
# jcode-feature-matrix.md R21 + memory-graph-render Stage 3).
#
# Usage:
#   powershell -File ensure-rkoj-daemon-up.ps1                  # default: 20 s wait, start if down
#   powershell -File ensure-rkoj-daemon-up.ps1 -TimeoutSec 60   # longer wait if cold-start is slow
#   powershell -File ensure-rkoj-daemon-up.ps1 -CheckOnly       # report only

[CmdletBinding()]
param(
    [int]$TimeoutSec = 20,
    [switch]$CheckOnly,
    [int]$Port = 5077,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Continue'

function Test-RkojUp {
    param([int]$P)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $task = $tcp.ConnectAsync('127.0.0.1', $P)
        $ok = $task.Wait(500) -and $tcp.Connected
        $tcp.Close()
        return $ok
    } catch { return $false }
}

if (Test-RkojUp -P $Port) {
    Write-Output "rkoj-up tcp:$Port"
    exit 0
}

Write-Output "rkoj-down tcp:$Port"
if ($CheckOnly) { exit 2 }

$daemonPy = Join-Path $SanctumRoot 'automations\window-manager\desktop_app.py'
if (-not (Test-Path $daemonPy)) {
    Write-Output "daemon-source-not-found ($daemonPy)"
    exit 2
}

# Find a usable python.exe
$python = & where.exe python.exe 2>$null | Select-Object -First 1
if (-not $python) { $python = & where.exe python 2>$null | Select-Object -First 1 }
if (-not $python) {
    Write-Output "python-not-in-path"
    exit 2
}

Write-Output "starting: $python $daemonPy"
# Detached spawn via Start-Process so the daemon survives THIS process exit.
# Hidden window + WMI-style invocation so no console attached. Equivalent pattern to
# automations/hidden-spawn.ps1.
$workdir = Join-Path $SanctumRoot 'automations\window-manager'
try {
    $p = Start-Process -FilePath $python -ArgumentList "`"$daemonPy`"" -WorkingDirectory $workdir -WindowStyle Hidden -PassThru
    Write-Output "spawned-pid: $($p.Id)"
} catch {
    Write-Output "spawn-failed: $_"
    exit 2
}

# Bounded wait
$start = Get-Date
while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSec) {
    Start-Sleep -Seconds 1
    if (Test-RkojUp -P $Port) {
        $elapsed = [int]((Get-Date) - $start).TotalSeconds
        Write-Output "rkoj-up-after ${elapsed}s"
        exit 0
    }
}

Write-Output "timeout-after ${TimeoutSec}s (daemon never bound :$Port)"
exit 2
