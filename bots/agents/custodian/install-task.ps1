# Register the Custodian backup daemon as a Windows Scheduled Task.
# Uses PowerShell native Register-ScheduledTask (more robust than schtasks.exe
# + cmd/c nested-quote dance). Idempotent.
#
# Triggers:
#   - At logon (per-user)
#   - Daily 03:00 restart (so it self-recovers if it died overnight)
#
# No admin needed for current-user logon tasks.

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterCustodian',
    [switch]$Uninstall
)

$ErrorActionPreference = 'Continue'

$AgentDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DaemonScript = Join-Path $AgentDir 'run-daemon.ps1'

if (-not (Test-Path $DaemonScript)) {
    Write-Host "FAIL: run-daemon.ps1 not found at $DaemonScript" -ForegroundColor Red
    exit 1
}

# Robust remove: ignore "not found" errors via -ErrorAction SilentlyContinue
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
$DailyName = "$TaskName-DailyRestart"
Remove-IfExists $DailyName | Out-Null

if ($Uninstall) {
    Write-Host "Uninstalled tasks: $TaskName + $DailyName" -ForegroundColor Green
    exit 0
}

# Build the action via native cmdlets (handles quoting correctly)
$PsExe = (Get-Command powershell.exe).Source
$Arguments = "-WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -File `"$DaemonScript`""

$action = New-ScheduledTaskAction -Execute $PsExe -Argument $Arguments

# Logon trigger
$loginTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
# Daily-restart trigger
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At '3:00am'

# Run as current user, interactive logon (no SYSTEM, no admin elevation needed)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

# Reasonable settings for a background loop
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero)

Write-Host "Registering: $TaskName (at logon)" -ForegroundColor Cyan
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $loginTrigger `
        -Principal $principal -Settings $settings -Description 'Sinister Custodian backup daemon (logon trigger)' -Force | Out-Null
    Write-Host "  [OK] $TaskName registered" -ForegroundColor Green
    $logonOk = $true
} catch {
    Write-Host "  [FAIL] $TaskName not registered: $($_.Exception.Message)" -ForegroundColor Red
    $logonOk = $false
}

Write-Host "Registering: $DailyName (daily 03:00)" -ForegroundColor Cyan
try {
    Register-ScheduledTask -TaskName $DailyName -Action $action -Trigger $dailyTrigger `
        -Principal $principal -Settings $settings -Description 'Sinister Custodian backup daemon (daily restart)' -Force | Out-Null
    Write-Host "  [OK] $DailyName registered" -ForegroundColor Green
    $dailyOk = $true
} catch {
    Write-Host "  [WARN] $DailyName not registered: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "         (logon trigger still active; daily restart skipped)" -ForegroundColor DarkGray
    $dailyOk = $false
}

Write-Host ""
if ($logonOk) {
    Write-Host "=== Installed ===" -ForegroundColor Green
    Write-Host "Tasks:"
    Write-Host "  - $TaskName            (runs at user logon)"
    if ($dailyOk) { Write-Host "  - $DailyName  (restart at 03:00 daily)" }
    Write-Host ""
    Write-Host "Verify:    Get-ScheduledTask -TaskName $TaskName | Format-List State,LastRunTime,NextRunTime"
    Write-Host "Run now:   Start-ScheduledTask -TaskName $TaskName"
    Write-Host "Logs:      D:\_backups\_logs\custodian-<today>.log"
    Write-Host "Uninstall: .\install-task.ps1 -Uninstall"
    exit 0
} else {
    Write-Host "=== INSTALL FAILED ===" -ForegroundColor Red
    Write-Host "Common causes:"
    Write-Host "  - PowerShell not running with sufficient privileges (try Run as Administrator)"
    Write-Host "  - Group Policy blocks Scheduled Tasks for the current user"
    Write-Host "  - Antivirus blocking task creation"
    Write-Host ""
    Write-Host "Fallback: the Custodian daemon still runs when triggered manually:"
    Write-Host "  cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian'"
    Write-Host "  .\run-daemon.ps1 -OneShot"
    exit 1
}
