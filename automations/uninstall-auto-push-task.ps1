# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# Removes the SinisterSanctumAutoPush scheduled task. Idempotent.

[CmdletBinding()]
param([string]$TaskName = 'SinisterSanctumAutoPush')

$ErrorActionPreference = 'Stop'
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed $TaskName."
} else {
    Write-Host "$TaskName not registered (nothing to do)."
}
