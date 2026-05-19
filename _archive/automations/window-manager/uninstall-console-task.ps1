# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# uninstall-console-task.ps1 - remove the 'RKOJ' scheduled task.
#
# Idempotent: silent no-op if the task does not exist.
#
# UTF-8 with BOM. No em-dashes. No `Read-Host ""`.

[CmdletBinding()]
param(
    [string]$TaskName = 'RKOJ'
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
    Write-Host "Note: any in-flight 'console-daemon.bat' window keeps running until"
    Write-Host "you close it manually (or kill the python.exe / RKOJ.exe child)."
    exit 0
} catch {
    Write-Host "[FAIL] could not uninstall task '$TaskName': $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
