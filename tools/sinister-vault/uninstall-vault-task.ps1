# Author: Sinister Sanctum SV-E agent (Claude) :: 2026-05-19
# uninstall-vault-task.ps1 - remove the 'SinisterVault' scheduled task.
#
# Idempotent: silent no-op if the task does not exist.
#
# UTF-8 with BOM. No em-dashes. No `Read-Host ""`.

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterVault'
)

$ErrorActionPreference = 'Continue'

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "[*] Task '$TaskName' is not registered. Nothing to do." -ForegroundColor DarkGray
    exit 0
}

try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    Write-Host "[OK] Task '$TaskName' uninstalled." -ForegroundColor Green
    Write-Host ''
    Write-Host "Note: any in-flight 'vault-daemon.bat' window keeps running until"
    Write-Host "you close it manually (or kill the python.exe child running daemon.py)."
    exit 0
} catch {
    Write-Host "[FAIL] could not uninstall task '$TaskName': $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
