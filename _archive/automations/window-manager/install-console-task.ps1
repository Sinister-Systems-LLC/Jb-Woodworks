# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# install-console-task.ps1 - register the 'RKOJ' scheduled task.
#
# What this does:
#   - Removes any prior 'RKOJ' task (idempotent re-run).
#   - Registers a Hidden, AtLogon, run-forever task that exec's the daemon bat.
#   - Reports Verify / Run-now / Logs / Uninstall commands at the end.
#
# Pattern copied from the Custodian's install-task.ps1 (lines 27-114). Uses
# native cmdlets (Register-ScheduledTask) instead of schtasks.exe because
# PowerShell 5.1 wraps schtasks stderr lines as ErrorRecords even on success
# (knowledge: SESSION-START\03-GOTCHAS.md powershell-stderr-wrap).
#
# UTF-8 with BOM. No em-dashes. No `Read-Host ""`.

[CmdletBinding()]
param(
    [string]$TaskName = 'RKOJ',
    [switch]$Uninstall
)

$ErrorActionPreference = 'Continue'

$AgentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatPath  = Join-Path $AgentDir 'console-daemon.bat'

if (-not (Test-Path $BatPath)) {
    Write-Host "FAIL: console-daemon.bat not found at $BatPath" -ForegroundColor Red
    exit 1
}

function Remove-IfExists($name) {
    try {
        $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
        if ($t) {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction Stop
            Write-Host "  Removed existing task: $name" -ForegroundColor Yellow
            return $true
        }
    } catch {
        Write-Host "  [WARN] could not check/remove '$name': $($_.Exception.Message)" -ForegroundColor Yellow
    }
    return $false
}

Remove-IfExists $TaskName | Out-Null

if ($Uninstall) {
    Write-Host "Uninstalled task: $TaskName" -ForegroundColor Green
    exit 0
}

# Build the action: cmd.exe /c "<console-daemon.bat>"
# Quoting: outer single-quote string lets us embed the bat path verbatim.
# Then PowerShell expands $BatPath inside the double-quoted argument.
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c "' + $BatPath + '"')

# AtLogOn (not AtStartup): HWID-binding needs user session; loopback :5077
# network ordering is finicky at cold-boot.
$loginTrigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"

# Interactive principal so the daemon shares the operator's desktop session
# (needed for pywebview / Edge WebView2 chrome on the source-python fallback).
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -Hidden `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Write-Host "Registering: $TaskName (at logon, hidden, run-forever)" -ForegroundColor Cyan
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $loginTrigger `
        -Principal $principal -Settings $settings `
        -Description 'Sinister Sanctum Console daemon - always-on local web console (loopback :5077).' `
        -Force | Out-Null
    Write-Host "  [OK] $TaskName registered" -ForegroundColor Green
    $logonOk = $true
} catch {
    Write-Host "  [FAIL] $TaskName not registered: $($_.Exception.Message)" -ForegroundColor Red
    $logonOk = $false
}

Write-Host ''
if ($logonOk) {
    Write-Host '=== Installed ===' -ForegroundColor Green
    Write-Host "Task:"
    Write-Host "  - $TaskName  (runs at user logon, hidden, restarts on crash)"
    Write-Host ''
    Write-Host "Verify:    Get-ScheduledTask -TaskName $TaskName | Format-List State,LastRunTime,NextRunTime"
    Write-Host "Run now:   Start-ScheduledTask -TaskName $TaskName"
    Write-Host "Logs:      D:\Sinister Sanctum\automations\window-manager\_daemon-logs\console-<stamp>.log"
    Write-Host "           (audit trail: _daemon-logs\daemon.log)"
    Write-Host "Heartbeat: D:\Sinister Sanctum\_shared-memory\heartbeats\sanctum-console.beat"
    Write-Host "           (stale if mtime > 120s old)"
    Write-Host "Uninstall: .\install-console-task.ps1 -Uninstall"
    Write-Host "           (or: .\uninstall-console-task.ps1)"
    exit 0
} else {
    Write-Host '=== INSTALL FAILED ===' -ForegroundColor Red
    Write-Host "Common causes:"
    Write-Host "  - PowerShell not running with sufficient privileges (try Run as Administrator)"
    Write-Host "  - Group Policy blocks Scheduled Tasks for the current user"
    Write-Host "  - Antivirus blocking task creation"
    Write-Host ''
    Write-Host "Fallback: the daemon still runs when invoked manually:"
    Write-Host "  cmd /c `"$BatPath`""
    exit 1
}
