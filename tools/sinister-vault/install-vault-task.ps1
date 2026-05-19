# Sinister Vault - register Windows scheduled task that auto-starts the daemon
# at user logon.
#
# Author: Sinister Sanctum SV-A agent (Claude) :: 2026-05-19
# Merged + extended by: Sinister Sanctum SV-E agent (Claude) :: 2026-05-19
#
# What this does:
#   - Removes any prior 'SinisterVault' task (idempotent re-run).
#   - Registers a Hidden, AtLogon, run-forever task that exec's vault-daemon.bat.
#   - Reports Verify / Run-now / Logs / Uninstall commands at the end.
#
# Pattern mirrored from automations\window-manager\install-console-task.ps1.
# Uses native cmdlets (Register-ScheduledTask) instead of schtasks.exe because
# PowerShell 5.1 wraps schtasks stderr lines as ErrorRecords even on success
# (knowledge: SESSION-START\03-GOTCHAS.md powershell-stderr-wrap).
#
# Usage (one-time, from any PowerShell prompt):
#   powershell -ExecutionPolicy Bypass -File install-vault-task.ps1
#   powershell -ExecutionPolicy Bypass -File install-vault-task.ps1 -Uninstall
#
# UTF-8 with BOM. No em-dashes. No `Read-Host ""`.

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterVault',
    [string]$BatPath  = (Join-Path $PSScriptRoot 'vault-daemon.bat'),
    [switch]$Uninstall
)

$ErrorActionPreference = 'Continue'

if (-not (Test-Path -LiteralPath $BatPath)) {
    Write-Host "FAIL: vault-daemon.bat not found at $BatPath" -ForegroundColor Red
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

# Build the action: cmd.exe /c "<vault-daemon.bat>"
$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c "' + $BatPath + '"')

# AtLogOn (not AtStartup): the vault daemon reads per-user account files in
# D:\sinister-vault\accounts\ that key off the current logged-in user. Cold
# boot before logon would bind to the wrong identity. Also: port 5078 is
# bound in the user session so RKOJ (also user-context) can reach it.
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
        -Description 'Sinister Vault daemon - 1 TB quota monitor + unified audit log (loopback :5078).' `
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
    Write-Host "Logs:      D:\Sinister Sanctum\tools\sinister-vault\_daemon-logs\vault-<stamp>.log"
    Write-Host "           (audit trail: _daemon-logs\daemon.log)"
    Write-Host "Heartbeat: D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-vault.beat"
    Write-Host "           (stale if mtime > 120s old)"
    Write-Host "Uninstall: .\install-vault-task.ps1 -Uninstall"
    Write-Host "           (or: .\uninstall-vault-task.ps1)"
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
