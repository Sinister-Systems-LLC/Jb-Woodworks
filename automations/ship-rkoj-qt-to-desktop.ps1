# Author: RKOJ-ELENO :: 2026-05-21
# ship-rkoj-qt-to-desktop.ps1
#
# Runs AFTER the PyQt6 sub-agent's PyInstaller build lands at
#   D:\Sinister Sanctum\projects\rkoj\source\dist\RKOJ\
# (Relocated from tools/sinister-rkoj-qt/ to projects/rkoj/source/ 2026-05-21.)
#
# Two paths:
#   A) folder-build: copy whole dist/RKOJ/ to C:\Users\Zonia\Desktop\RKOJ\
#      then point RKOJ.lnk at it.
#   B) onefile-build: copy single EXE to C:\Users\Zonia\Desktop\RKOJ.exe
#      then update RKOJ.lnk to point at C:\Users\Zonia\Desktop\RKOJ.exe.
#
# Operator (2026-05-21): "let me know once rkoj is done. place on desktop once it is".

[CmdletBinding()]
param(
    [string]$DistDir = 'D:\Sinister Sanctum\projects\rkoj\source\sinister_rkoj_qt\dist',
    [string]$DesktopDir = 'C:\Users\Zonia\Desktop'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $DistDir)) {
    Write-Host "[ship-rkoj-qt] ERROR: $DistDir not found. PyQt6 sub-agent still building?" -ForegroundColor Red
    exit 1
}

# Detect onefile vs folder build
$onefile = Join-Path $DistDir 'RKOJ.exe'
$folder  = Join-Path $DistDir 'RKOJ'
$folderExe = Join-Path $folder 'RKOJ.exe'

# v1.6.82 — operator directive: ONLY ONE RKOJ entry on Desktop.
# Always nuke any stray RKOJ.lnk before shipping (we don't create one
# anymore — the EXE alone is the operator's entry point).
$strayLnk = Join-Path $DesktopDir 'RKOJ.lnk'
if (Test-Path $strayLnk) {
    Remove-Item -LiteralPath $strayLnk -Force -ErrorAction SilentlyContinue
    Write-Host "[ship-rkoj-qt] removed stray RKOJ.lnk"
}

if (Test-Path $onefile) {
    Write-Host "[ship-rkoj-qt] onefile build detected: $onefile" -ForegroundColor Cyan
    $destExe = Join-Path $DesktopDir 'RKOJ.exe'
    Copy-Item -LiteralPath $onefile -Destination $destExe -Force
    Write-Host "[ship-rkoj-qt] copied -> $destExe"
} elseif (Test-Path $folderExe) {
    Write-Host "[ship-rkoj-qt] folder build detected: $folderExe" -ForegroundColor Cyan
    $destFolder = Join-Path $DesktopDir 'RKOJ'
    if (Test-Path $destFolder) {
        Write-Host "[ship-rkoj-qt] removing existing $destFolder ..."
        Remove-Item -LiteralPath $destFolder -Recurse -Force
    }
    Copy-Item -LiteralPath $folder -Destination $destFolder -Recurse -Force
    Write-Host "[ship-rkoj-qt] copied folder -> $destFolder"
} else {
    Write-Host "[ship-rkoj-qt] ERROR: neither onefile nor folder build found in $DistDir" -ForegroundColor Red
    Get-ChildItem $DistDir | Format-Table Name, Mode -AutoSize
    exit 1
}

Write-Host ""
Write-Host "[ship-rkoj-qt] SHIPPED. Operator double-clicks Desktop/RKOJ.exe (only one entry, no shortcut)." -ForegroundColor Green
