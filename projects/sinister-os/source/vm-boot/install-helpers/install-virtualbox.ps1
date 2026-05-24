# Author: RKOJ-ELENO :: 2026-05-24
# Sinister OS :: vm-boot :: install-helpers :: install-virtualbox.ps1
#
# Operator-gated VirtualBox installer wrapper. Does NOT auto-install.
# Prints the exact winget command and prompts the operator for confirmation.
#
# Usage:
#   powershell -File source/vm-boot/install-helpers/install-virtualbox.ps1
#   powershell -File source/vm-boot/install-helpers/install-virtualbox.ps1 -Yes  # skip prompt
#
# Why a wrapper?  Per Sinister OS lane hard rule:
#   "No firmware changes without operator authorization."
#   VirtualBox installs kernel drivers + a network filter — it deserves a click.

[CmdletBinding()]
param(
    [switch]$Yes
)

$ErrorActionPreference = 'Stop'

# Already installed?
$candidates = @(
    'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe',
    'C:\Program Files (x86)\Oracle\VirtualBox\VBoxManage.exe'
)
foreach ($p in $candidates) {
    if (Test-Path $p) {
        $ver = & $p --version 2>$null
        Write-Host "VirtualBox already installed: $p (version $ver)" -ForegroundColor Green
        Write-Host "Nothing to do."
        return
    }
}

Write-Host "Sinister OS :: VirtualBox installer wrapper" -ForegroundColor Magenta
Write-Host ""
Write-Host "The following command WILL install Oracle VirtualBox on this machine:"
Write-Host ""
Write-Host "    winget install -e --id Oracle.VirtualBox" -ForegroundColor Cyan
Write-Host ""
Write-Host "Side effects:"
Write-Host "  - Installs to C:\Program Files\Oracle\VirtualBox\"
Write-Host "  - Installs kernel-mode network filter driver (briefly disconnects the network)"
Write-Host "  - Adds 'VirtualBox Host-Only Network' adapter"
Write-Host "  - Requires admin elevation (UAC prompt)"
Write-Host ""

if (-not $Yes) {
    Write-Host "Run with -Yes to proceed, or run the winget command manually." -ForegroundColor Yellow
    return
}

# Confirm winget exists
$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Host "winget not found. Install App Installer from the Microsoft Store, or download VirtualBox manually:" -ForegroundColor Red
    Write-Host "  https://www.virtualbox.org/wiki/Downloads"
    exit 1
}

Write-Host "Running: winget install -e --id Oracle.VirtualBox" -ForegroundColor Green
& winget install -e --id Oracle.VirtualBox
$rc = $LASTEXITCODE
if ($rc -ne 0) {
    Write-Host "winget exited with code $rc" -ForegroundColor Red
    exit $rc
}

Write-Host ""
Write-Host "Done. Verify with: bash source/vm-boot/probe.sh" -ForegroundColor Green
