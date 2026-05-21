# Author: RKOJ-ELENO :: 2026-05-21
# ship-rkoj-qt-to-desktop.ps1
#
# Runs AFTER the PyQt6 sub-agent's PyInstaller build lands at
#   D:\Sinister Sanctum\tools\sinister-rkoj-qt\dist\RKOJ\
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
    [string]$DistDir = 'D:\Sinister Sanctum\tools\sinister-rkoj-qt\dist',
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

if (Test-Path $onefile) {
    Write-Host "[ship-rkoj-qt] onefile build detected: $onefile" -ForegroundColor Cyan
    $destExe = Join-Path $DesktopDir 'RKOJ.exe'
    Copy-Item -LiteralPath $onefile -Destination $destExe -Force
    Write-Host "[ship-rkoj-qt] copied -> $destExe"
    # Update RKOJ.lnk to point at the Desktop EXE
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut(Join-Path $DesktopDir 'RKOJ.lnk')
    $sc.TargetPath = $destExe
    $sc.WorkingDirectory = $DesktopDir
    $sc.Description = 'Sinister Sanctum :: RKOJ native PyQt6 desktop UI'
    $sc.IconLocation = "$destExe,0"
    $sc.Save()
    Write-Host "[ship-rkoj-qt] RKOJ.lnk -> $destExe"
} elseif (Test-Path $folderExe) {
    Write-Host "[ship-rkoj-qt] folder build detected: $folderExe" -ForegroundColor Cyan
    $destFolder = Join-Path $DesktopDir 'RKOJ'
    # Wipe existing destination if any (it's our own ship target)
    if (Test-Path $destFolder) {
        Write-Host "[ship-rkoj-qt] removing existing $destFolder ..."
        Remove-Item -LiteralPath $destFolder -Recurse -Force
    }
    Copy-Item -LiteralPath $folder -Destination $destFolder -Recurse -Force
    Write-Host "[ship-rkoj-qt] copied folder -> $destFolder"
    # Update RKOJ.lnk to point at the Desktop folder's EXE
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut(Join-Path $DesktopDir 'RKOJ.lnk')
    $sc.TargetPath = Join-Path $destFolder 'RKOJ.exe'
    $sc.WorkingDirectory = $destFolder
    $sc.Description = 'Sinister Sanctum :: RKOJ native PyQt6 desktop UI'
    $sc.IconLocation = "$(Join-Path $destFolder 'RKOJ.exe'),0"
    $sc.Save()
    Write-Host "[ship-rkoj-qt] RKOJ.lnk -> $(Join-Path $destFolder 'RKOJ.exe')"
} else {
    Write-Host "[ship-rkoj-qt] ERROR: neither onefile nor folder build found in $DistDir" -ForegroundColor Red
    Get-ChildItem $DistDir | Format-Table Name, Mode -AutoSize
    exit 1
}

Write-Host ""
Write-Host "[ship-rkoj-qt] SHIPPED. Operator double-clicks Desktop/RKOJ.lnk or Desktop/RKOJ.exe." -ForegroundColor Green
