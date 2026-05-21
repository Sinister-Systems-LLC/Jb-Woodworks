# Author: RKOJ-ELENO :: 2026-05-21
# Smoke: RKOJ.exe Milestone 1 — Chrome boots cleanly.
# Exits 0 on PASS, 1 on FAIL (with single-line reason).

param(
    [string]$exePath = 'C:\Users\Zonia\Desktop\RKOJ\RKOJ.exe'
)

$ErrorActionPreference = 'Stop'

function Fail([string]$reason) {
    Write-Host "FAIL: $reason" -ForegroundColor Red
    exit 1
}

# 1.1 EXE exists
if (-not (Test-Path -LiteralPath $exePath)) {
    Fail "EXE not found at $exePath"
}

$exeDir = Split-Path -Parent $exePath
$crashLog = Join-Path $exeDir 'RKOJ.crash.log'
if (Test-Path -LiteralPath $crashLog) {
    Remove-Item -LiteralPath $crashLog -Force -Confirm:$false
}

# 1.2 Launch via Start-Process -PassThru
$proc = Start-Process -FilePath $exePath -PassThru
if ($null -eq $proc -or $null -eq $proc.Id) {
    Fail "Start-Process returned null/no PID"
}

# 1.3 Wait 6s, verify still alive
Start-Sleep -Seconds 6
$proc.Refresh()
if ($proc.HasExited) {
    Fail "Process exited within 6s (exit code: $($proc.ExitCode))"
}

# 1.4 MainWindowTitle matches regex
$title = $proc.MainWindowTitle
if ($title -notmatch 'Sanctum|Sinister|RKOJ|EVE') {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "MainWindowTitle '$title' does not match Sanctum|Sinister|RKOJ|EVE"
}

# 1.5 No crash log written
if (Test-Path -LiteralPath $crashLog) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "RKOJ.crash.log appeared within 6s of launch"
}

# 1.6 Has window handle
if ($proc.MainWindowHandle -eq 0) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "MainWindowHandle is 0 (no GUI window)"
}

# 1.7 Working set sane (30 MB - 800 MB)
$ws = $proc.WorkingSet64
if ($ws -lt 30MB -or $ws -gt 800MB) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "Working set $([math]::Round($ws/1MB)) MB outside 30-800 MB range"
}

# 1.8-1.9 Clean shutdown, no zombies
Stop-Process -Id $proc.Id -Force
Start-Sleep -Seconds 3
$zombies = Get-Process -Name 'RKOJ' -ErrorAction SilentlyContinue
if ($zombies) {
    Fail "Zombie RKOJ processes still alive after Stop-Process"
}

# 1.10 Re-launch verifies repeatability
$proc2 = Start-Process -FilePath $exePath -PassThru
Start-Sleep -Seconds 6
$proc2.Refresh()
if ($proc2.HasExited) {
    Fail "Re-launch process exited within 6s"
}
Stop-Process -Id $proc2.Id -Force -ErrorAction SilentlyContinue

Write-Host "PASS: Milestone 1 — chrome boots cleanly (title='$title', RSS=$([math]::Round($ws/1MB)) MB)" -ForegroundColor Green
exit 0
