# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Start-Console.ps1 - popup-aware launcher for RKOJ (the Sanctum workbench).
#
# What this does:
#   1. Kills any stale RKOJ.exe / Sanctum-Console.exe and any listener bound to -Port.
#   2. Launches the chosen backend (frozen exe by default, source python if
#      -FromSource). Hidden by default; -Window shows the pywebview chrome.
#   3. Sleeps 5s, checks the process is still alive. If dead, scans the
#      Windows Application event log for matching messages within the last
#      minute (catches "Failed to load Python DLL" bootloader popups).
#   4. Probes http://127.0.0.1:<Port>/api/health (5s timeout, 3 retries with
#      2s between).
#   5. Always emits a single JSON object to stdout describing the outcome.
#
# UTF-8 with BOM. No em-dashes. No `Read-Host ""`.

[CmdletBinding()]
param(
    [switch]$Window,
    [switch]$Lan,
    [int]$Port = 5077,
    [switch]$FromSource,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

$WmDir       = 'D:\Sinister Sanctum\automations\window-manager'
$ExePath     = Join-Path $WmDir 'dist\RKOJ\RKOJ.exe'
$DesktopExe  = Join-Path $env:USERPROFILE 'Desktop\RKOJ\RKOJ.exe'
$VenvPy      = Join-Path $WmDir '.venv\Scripts\python.exe'
$SrcApp      = Join-Path $WmDir 'desktop_app.py'

$result = [ordered]@{
    ok       = $false
    pid      = $null
    port     = $Port
    backend  = $null
    mode     = $null
    health   = $null
    popups   = @()
    error    = $null
}

function Write-Note($msg, $color = 'DarkGray') {
    if (-not $Quiet) { Write-Host $msg -ForegroundColor $color }
}

# ---------------------------------------------------------------------------
# Step 1: kill stale processes + port listeners.
Write-Note "[1/5] killing stale RKOJ / Sanctum-Console + port $Port listeners"
$killed = 0
foreach ($name in @('RKOJ', 'rkoj', 'Sanctum-Console', 'sanctum-console')) {
    Get-Process -Name $name -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force -ErrorAction Stop
            $killed++
        } catch {
            Write-Note "      could not kill PID $($_.Id): $($_.Exception.Message)" 'Yellow'
        }
    }
}
# Kill any python.exe bound to the target port (source-mode case).
try {
    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $listeners) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop
            $killed++
        } catch {
            Write-Note "      could not kill listener PID $($conn.OwningProcess): $($_.Exception.Message)" 'Yellow'
        }
    }
} catch {
    Write-Note "      Get-NetTCPConnection unavailable: $($_.Exception.Message)" 'Yellow'
}
Write-Note "      killed $killed process(es)"
Start-Sleep -Milliseconds 500

# ---------------------------------------------------------------------------
# Step 2: pick backend + launch.
$backend = $null
$mode    = $null
$argList = @()
if ($FromSource) {
    if (-not (Test-Path $VenvPy)) {
        $result.error = ".venv python missing: $VenvPy"
        $result | ConvertTo-Json -Depth 6
        exit 2
    }
    if (-not (Test-Path $SrcApp)) {
        $result.error = "desktop_app.py missing: $SrcApp"
        $result | ConvertTo-Json -Depth 6
        exit 2
    }
    $backend = $VenvPy
    $mode    = 'source-python'
    $argList = @($SrcApp, '--port', "$Port")
} else {
    if (Test-Path $ExePath) {
        $backend = $ExePath
        $mode    = 'exe-dist'
    } elseif (Test-Path $DesktopExe) {
        $backend = $DesktopExe
        $mode    = 'exe-desktop'
    } else {
        $result.error = "no frozen exe at $ExePath or $DesktopExe; try -FromSource"
        $result | ConvertTo-Json -Depth 6
        exit 2
    }
    $argList = @('--port', "$Port")
}
if (-not $Window) { $argList += '--no-window' }
if ($Lan)         { $argList += '--lan' }

$result.backend = $backend
$result.mode    = $mode

Write-Note "[2/5] launching: $backend $($argList -join ' ')"
$windowStyle = if ($Window) { 'Normal' } else { 'Hidden' }
try {
    $proc = Start-Process -FilePath $backend -ArgumentList $argList -WindowStyle $windowStyle -PassThru -ErrorAction Stop
    $result.pid = $proc.Id
    Write-Note "      pid=$($proc.Id) WindowStyle=$windowStyle"
} catch {
    $result.error = "Start-Process failed: $($_.Exception.Message)"
    $result | ConvertTo-Json -Depth 6
    exit 2
}

# ---------------------------------------------------------------------------
# Step 3: wait 5s, check alive, scan Event Log if dead.
Write-Note "[3/5] sleeping 5s then checking process is alive"
Start-Sleep -Seconds 5

$processAlive = $false
try {
    $live = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($live) { $processAlive = $true }
} catch { }

if (-not $processAlive) {
    Write-Note "      PROCESS DIED within 5s - scanning Event Log for popups" 'Red'
    try {
        $since = (Get-Date).AddMinutes(-1)
        $events = Get-WinEvent -LogName Application -MaxEvents 30 -ErrorAction SilentlyContinue |
            Where-Object { $_.TimeCreated -gt $since -and ($_.Message -like '*RKOJ*' -or $_.Message -like '*Sanctum-Console*') }
        foreach ($ev in $events) {
            $popup = [ordered]@{
                time     = $ev.TimeCreated.ToString('o')
                provider = $ev.ProviderName
                id       = $ev.Id
                message  = ($ev.Message -replace '\s+', ' ').Trim()
            }
            $result.popups += $popup
            Write-Note "      [popup $($ev.ProviderName)/$($ev.Id)] $($popup.message)" 'Red'
        }
    } catch {
        Write-Note "      Get-WinEvent failed: $($_.Exception.Message)" 'Yellow'
    }
    $result.error = if ($result.popups.Count -gt 0) {
        "process died within 5s; $($result.popups.Count) matching event-log entries"
    } else {
        "process died within 5s; no matching event-log entries"
    }
    $result | ConvertTo-Json -Depth 6
    exit 3
}
Write-Note "      process alive"

# ---------------------------------------------------------------------------
# Step 4: probe /api/health (3 retries, 2s between).
Write-Note "[4/5] probing http://127.0.0.1:$Port/api/health"
$healthUrl = "http://127.0.0.1:$Port/api/health"
$health = $null
for ($i = 1; $i -le 3; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        try {
            $health = $resp.Content | ConvertFrom-Json -ErrorAction Stop
        } catch {
            $health = @{ raw = $resp.Content }
        }
        Write-Note "      [OK] health (attempt $i)"
        break
    } catch {
        Write-Note "      attempt $i/3 failed: $($_.Exception.Message)" 'Yellow'
        if ($i -lt 3) { Start-Sleep -Seconds 2 }
    }
}
$result.health = $health

# ---------------------------------------------------------------------------
# Step 5: emit JSON.
if ($health) {
    $result.ok = $true
}
Write-Note "[5/5] done; emitting JSON status"

$result | ConvertTo-Json -Depth 6
if ($result.ok) { exit 0 } else { exit 4 }
