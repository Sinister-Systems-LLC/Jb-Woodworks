# Author: RKOJ-ELENO :: 2026-05-21
# Purpose: Silence the remaining 2 scheduled tasks that spawn visible PowerShell/Python windows
#          every 5-15 minutes. The 3 tasks in the root folder were patched without elevation.
#          The 2 in \Sinister\ subfolder need ADMIN to modify.
#
# Operator 2026-05-21 (verbatim): "still a powershell window popus up every 1-5 minutes.
#                                  fix this shit im tired of asking"
#
# Run AS ADMINISTRATOR (right-click → Run as administrator).

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: must run as Administrator" -ForegroundColor Red
    Write-Host "Right-click this .ps1 and 'Run with PowerShell as Administrator', OR"
    Write-Host "Right-click PowerShell -> Run as Administrator, then:"
    Write-Host "  pwsh -File `"$($MyInvocation.MyCommand.Path)`""
    exit 1
}

function Patch-Task([string]$name, [string]$path, [string]$exe, [string]$exeArgs) {
    try {
        $action = New-ScheduledTaskAction -Execute $exe -Argument $exeArgs
        Set-ScheduledTask -TaskName $name -TaskPath $path -Action $action -ErrorAction Stop | Out-Null
        Write-Host "OK $path$name" -ForegroundColor Green
    } catch {
        Write-Host "FAIL $path$name : $_" -ForegroundColor Red
    }
}

# 2 remaining tasks need admin elevation
Patch-Task -name "Sinister-fleet-monitor" -path "\Sinister\" -exe "C:\Users\Zonia\jupyter-workstation\Scripts\pythonw.exe" -exeArgs '"C:\Users\Zonia\Desktop\Tools\cron\fleet_monitor.py"'
Patch-Task -name "Sinister-sheets-sync"   -path "\Sinister\" -exe "C:\Users\Zonia\jupyter-workstation\Scripts\pythonw.exe" -exeArgs '"C:\Users\Zonia\Desktop\Tools\cron\sheets_sync.py"'

Write-Host ""
Write-Host "Done. Popups should stop within the next task cadence (5-15 min)." -ForegroundColor Green
Write-Host "Verify: schtasks /Query /TN '\\Sinister\\Sinister-fleet-monitor' /FO LIST /V | findstr 'Task To Run'"
