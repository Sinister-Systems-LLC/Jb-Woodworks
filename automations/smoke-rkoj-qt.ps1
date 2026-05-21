# Author: RKOJ-ELENO :: 2026-05-21
# smoke-rkoj-qt.ps1 — verify the PyQt6 RKOJ.exe pops a real Qt window.
#
# Runs after the sub-agent's PyInstaller build completes. Launches the EXE,
# waits 6 sec, checks if a window with title containing "Sanctum" / "Sinister"
# / "RKOJ" exists, then terminates cleanly.

[CmdletBinding()]
param(
    [string]$ExePath = 'D:\Sinister Sanctum\tools\sinister-rkoj-qt\dist\RKOJ\RKOJ.exe',
    [int]$WaitSec = 6
)

if (-not (Test-Path $ExePath)) {
    Write-Host "[smoke-rkoj-qt] ERROR: $ExePath not found. PyQt6 sub-agent may still be building." -ForegroundColor Red
    exit 1
}

Write-Host "[smoke-rkoj-qt] launching $ExePath ..." -ForegroundColor Cyan
$proc = Start-Process -FilePath $ExePath -PassThru
Start-Sleep -Seconds $WaitSec

# Look for any window of the launched process (or its children).
$found = $false
$titles = @()
Get-Process | Where-Object { $_.MainWindowTitle -and ($_.MainWindowTitle -match 'Sanctum|Sinister|RKOJ|EVE') } | ForEach-Object {
    $found = $true
    $titles += "$($_.ProcessName) ($($_.Id)): $($_.MainWindowTitle)"
}

if ($found) {
    Write-Host "[smoke-rkoj-qt] PASS — Qt window detected:" -ForegroundColor Green
    $titles | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "[smoke-rkoj-qt] FAIL — no Qt window with Sanctum/Sinister/RKOJ/EVE in title." -ForegroundColor Red
    Write-Host "  Process state: $(if ($proc.HasExited) { 'exited code ' + $proc.ExitCode } else { 'still running, pid=' + $proc.Id })"
}

# Cleanup
try {
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "[smoke-rkoj-qt] terminated pid $($proc.Id)"
    }
} catch { }

if ($found) { exit 0 } else { exit 1 }
