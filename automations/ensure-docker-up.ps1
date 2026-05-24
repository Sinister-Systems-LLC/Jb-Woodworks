# ensure-docker-up.ps1 — auto-start Docker Desktop if its daemon is down, with bounded wait + skip-if-up.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Origin: operator hard-canonical 2026-05-24T16:05:32Z verbatim:
#   "make sure ... if the docker things we ened are not open they are uauto opened and claude has access
#    to create them if neeeded and auto start them."
#
# Idempotent. Safe to call before any docker-dependent script (sinister-os stack, docker-stack/, etc.).
# Returns exit 0 if daemon is reachable, exit 2 if start failed or wait timed out.
#
# Usage:
#   powershell -File ensure-docker-up.ps1                  # default: 90 s wait, start if down
#   powershell -File ensure-docker-up.ps1 -TimeoutSec 180  # longer wait for slow boot
#   powershell -File ensure-docker-up.ps1 -CheckOnly       # report only, do not start

[CmdletBinding()]
param(
    [int]$TimeoutSec = 90,
    [switch]$CheckOnly,
    [string]$DockerDesktopPath = ''
)

$ErrorActionPreference = 'Continue'

function Test-DockerUp {
    $r = & docker ps --format "{{.Names}}" 2>$null
    return ($LASTEXITCODE -eq 0)
}

if (Test-DockerUp) {
    Write-Output "docker-up (no action needed)"
    exit 0
}

Write-Output "docker-down"
if ($CheckOnly) { exit 2 }

# Resolve Docker Desktop path
if (-not $DockerDesktopPath -or -not (Test-Path $DockerDesktopPath)) {
    $candidates = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    )
    $DockerDesktopPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $DockerDesktopPath) {
    Write-Output "docker-desktop-not-found (install or pass -DockerDesktopPath)"
    exit 2
}

Write-Output "starting: $DockerDesktopPath"
Start-Process -FilePath $DockerDesktopPath -WindowStyle Minimized -ErrorAction SilentlyContinue | Out-Null

# Bounded wait
$start = Get-Date
$tick = 0
while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSec) {
    Start-Sleep -Seconds 3
    $tick++
    if (Test-DockerUp) {
        $elapsed = [int]((Get-Date) - $start).TotalSeconds
        Write-Output "docker-up-after ${elapsed}s"
        exit 0
    }
    if ($tick % 5 -eq 0) {
        $elapsed = [int]((Get-Date) - $start).TotalSeconds
        Write-Output "still-waiting ${elapsed}s/${TimeoutSec}s"
    }
}

Write-Output "timeout-after ${TimeoutSec}s (docker daemon never became reachable)"
exit 2
