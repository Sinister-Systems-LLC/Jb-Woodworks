# Sinister Sanctum :: sanctum-backup :: scheduled-task installer
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Registers a daily Windows Task Scheduler entry that runs
#     sanctum-backup now
# at the chosen local time (default 03:00). Operator-gated — this script is
# invoked only by `sanctum-backup install-task`, never automatically.

[CmdletBinding()]
param(
    [string]$TaskName = "SinisterSanctumBackup",
    [string]$AtTime   = "03:00",
    [string]$Command  = ""
)

$ErrorActionPreference = "Stop"

if (-not $Command) {
    # Prefer the entry-point shim installed by `pip install -e`. Fall back to
    # `python -m sanctum_backup` if the shim is not on PATH.
    $shim = Get-Command sanctum-backup -ErrorAction SilentlyContinue
    if ($shim) {
        $Command = '"' + $shim.Source + '" now'
    } else {
        $Command = "python -m sanctum_backup now"
    }
}

Write-Host "sanctum-backup install-task"
Write-Host "  task name : $TaskName"
Write-Host "  at time   : $AtTime"
Write-Host "  command   : $Command"

$trigger = New-ScheduledTaskTrigger -Daily -At $AtTime
$action  = New-ScheduledTaskAction  -Execute "cmd.exe" -Argument "/c $Command"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  removing existing task ..."
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings | Out-Null
    Write-Host "  registered."
    exit 0
} catch {
    Write-Error "sanctum-backup install-task failed: $_"
    exit 2
}
