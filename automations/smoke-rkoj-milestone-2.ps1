# Author: RKOJ-ELENO :: 2026-05-21
# Smoke: RKOJ.exe Milestone 2 — Layout sanity (process-state only).
# Visual UI assertions are operator-driven; this script verifies the
# process stays healthy across a 30s click-through window.
# Exits 0 on PASS, 1 on FAIL.

param(
    [string]$exePath = 'C:\Users\Zonia\Desktop\RKOJ\RKOJ.exe'
)

$ErrorActionPreference = 'Stop'

function Fail([string]$reason) {
    Write-Host "FAIL: $reason" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $exePath)) {
    Fail "EXE not found at $exePath"
}

$exeDir = Split-Path -Parent $exePath
$crashLog = Join-Path $exeDir 'RKOJ.crash.log'
if (Test-Path -LiteralPath $crashLog) {
    Remove-Item -LiteralPath $crashLog -Force -Confirm:$false
}

# Launch
$proc = Start-Process -FilePath $exePath -PassThru
Start-Sleep -Seconds 6
$proc.Refresh()
if ($proc.HasExited) {
    Fail "Process exited before click-through window opened"
}

$initialTitle = $proc.MainWindowTitle
Write-Host "Launched: PID=$($proc.Id), title='$initialTitle'" -ForegroundColor Cyan
Write-Host "OPERATOR: click through sidebar (Agents, Devices), open File menu," -ForegroundColor Yellow
Write-Host "          click '+ Create Agent', verify visual assertions 2.1-2.7." -ForegroundColor Yellow
Write-Host "          Script will sample process state every 5s for 30s." -ForegroundColor Yellow

# Sample for 30s
for ($i = 1; $i -le 6; $i++) {
    Start-Sleep -Seconds 5
    $proc.Refresh()
    if ($proc.HasExited) {
        Fail "Process crashed at sample $i (exit code: $($proc.ExitCode))"
    }
    if ($proc.MainWindowHandle -eq 0) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Fail "MainWindowHandle dropped to 0 at sample $i"
    }
    Write-Host "  Sample $i/6: alive, title='$($proc.MainWindowTitle)', RSS=$([math]::Round($proc.WorkingSet64/1MB)) MB" -ForegroundColor DarkGray
}

# 2.9 Title still matches family regex
$finalTitle = $proc.MainWindowTitle
if ($finalTitle -notmatch 'Sanctum|Sinister|RKOJ|EVE') {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "MainWindowTitle '$finalTitle' drifted off family regex"
}

# 2.10 No crash log
if (Test-Path -LiteralPath $crashLog) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "RKOJ.crash.log appeared during click-through window"
}

Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue

Write-Host "PASS: Milestone 2 — process survived 30s click-through. Operator confirms UI assertions verbally." -ForegroundColor Green
exit 0
