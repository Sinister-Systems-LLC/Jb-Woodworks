# RKOJ Workbench - register Windows scheduled task that auto-starts the
# console daemon at user logon.
#
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# What this does:
#   - Removes any prior 'RKOJ' task (idempotent re-run).
#   - Registers a Hidden, AtLogon, run-forever task that exec's console-daemon.bat.
#   - Reports Verify / Run-now / Logs / Uninstall commands at the end.
#
# Pattern mirrored from tools\sinister-vault\install-vault-task.ps1 (the
# canonical scheduled-task pattern this file is modeled on). Uses native
# cmdlets (Register-ScheduledTask) instead of schtasks.exe because
# PowerShell 5.1 wraps schtasks stderr lines as ErrorRecords even on success
# (knowledge: SESSION-START\03-GOTCHAS.md powershell-stderr-wrap).
#
# Why a `-BatPath` parameter (vs deriving from $PSScriptRoot):
#   When invoked via `powershell -ExecutionPolicy Bypass -File ...`,
#   $PSScriptRoot is reliable from PS 3.0 onward, but a corner case occurs
#   when this script is dot-sourced or wrapped by other launchers. Exposing
#   `-BatPath` lets the caller (operator, install-task-everything.ps1, the
#   PROGRESS audit) point at the correct bat without ambiguity. Default
#   value uses $PSScriptRoot for the common case.
#
# Usage (one-time, from any PowerShell prompt):
#   powershell -ExecutionPolicy Bypass -File install-rkoj-task.ps1
#   powershell -ExecutionPolicy Bypass -File install-rkoj-task.ps1 -Uninstall
#   powershell -ExecutionPolicy Bypass -File install-rkoj-task.ps1 -BatPath "<full>\console-daemon.bat"
#
# UTF-8 with BOM. No em-dashes. No `Read-Host ""`.

[CmdletBinding()]
param(
    [string]$TaskName = 'RKOJ',
    [string]$BatPath  = (Join-Path $PSScriptRoot 'console-daemon.bat'),
    [switch]$Uninstall
)

$ErrorActionPreference = 'Continue'

if (-not (Test-Path -LiteralPath $BatPath)) {
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
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c "' + $BatPath + '"')

# AtLogOn (not AtStartup): RKOJ needs the user desktop environment for
# pywebview / Edge-WebView2 chrome (source-python fallback path). HWID-bound
# auth also keys off the logged-in user. Cold boot before logon would bind
# to the wrong identity. Loopback :5077 is bound in the user session so
# vault (also user-context) can call it.
$loginTrigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"

# Interactive principal at Highest: shares the operator desktop session so
# audit events include live user context. Highest needed to register tasks
# with RestartCount/RestartInterval on some host policies.
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
        -Description 'RKOJ Workbench daemon - keeps the desktop window-manager server alive on port 5077.' `
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
    Write-Host "Heartbeat: D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj-runtime.beat"
    Write-Host "           (server.py _runtime_heartbeat_loop writes every 30s; stale if mtime > 120s old)"
    Write-Host "Health:    curl http://127.0.0.1:5077/api/health"
    Write-Host "Uninstall: .\install-rkoj-task.ps1 -Uninstall"
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
