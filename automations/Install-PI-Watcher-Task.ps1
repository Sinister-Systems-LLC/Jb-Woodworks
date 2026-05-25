# Author: RKOJ-ELENO :: 2026-05-24
# Install-PI-Watcher-Task.ps1 -- registers Windows scheduled task SinisterKernelAPK-PI-Watcher
# Watcher runs every 30 min. Auto-detects + auto-fixes PI degradation on both phones.
# Composes with: automations/PI-Watcher.ps1 + automations/Fix-PI-Both-Phones.bat
# Operator hard-canonical 2026-05-24T23:46Z: "dont let that shit happen again".

param(
    [int]$IntervalMinutes = 30,
    [switch]$Unregister
)

$taskName    = "SinisterKernelAPK-PI-Watcher"
$watcherPath = "D:\Sinister Sanctum\automations\PI-Watcher.ps1"

if ($Unregister) {
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "[OK] Unregistered scheduled task '$taskName'." -ForegroundColor Green
    } else {
        Write-Host "[SKIP] Scheduled task '$taskName' not present." -ForegroundColor Yellow
    }
    exit 0
}

if (-not (Test-Path $watcherPath)) {
    Write-Error ("Watcher script not found: {0}" -f $watcherPath)
    exit 13
}

$action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"{0}`"" -f $watcherPath)
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(2)) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::FromDays(365))
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Host ("[OK] Scheduled task '{0}' registered: runs PI-Watcher every {1} min, starting in 2 min." -f $taskName, $IntervalMinutes) -ForegroundColor Green
Write-Host ("Verify:    schtasks /Query /TN {0}" -f $taskName)
Write-Host ("Manual run: schtasks /Run /TN {0}" -f $taskName)
Write-Host ("Disable:    powershell -File `"{0}`" -Unregister" -f $PSCommandPath)
