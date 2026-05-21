# Author: RKOJ-ELENO :: 2026-05-21
# Smoke: RKOJ.exe Milestone 3 — Agent flow (subprocess + cleanup assertions).
# Operator spawns an agent + sends a turn; this script asserts the
# claude subprocess actually appears, then verifies cleanup on window-X.
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

# Baseline: kill any pre-existing claude procs so we measure deltas cleanly
$preClaude = Get-Process -Name 'claude' -ErrorAction SilentlyContinue
if ($preClaude) {
    Write-Host "WARN: $($preClaude.Count) pre-existing claude.exe procs — assertion will measure delta" -ForegroundColor Yellow
}
$baselineCount = ($preClaude | Measure-Object).Count

# Launch RKOJ
$proc = Start-Process -FilePath $exePath -PassThru
Start-Sleep -Seconds 6
$proc.Refresh()
if ($proc.HasExited) {
    Fail "RKOJ process exited before agent flow could begin"
}

Write-Host "Launched: PID=$($proc.Id)" -ForegroundColor Cyan
Write-Host "OPERATOR: click '+ Create Agent', type a turn, click Send." -ForegroundColor Yellow
Write-Host "          Verify opening output mentions 'EVE' not 'Claude'." -ForegroundColor Yellow
Write-Host "          Script will wait 25s then assert claude subprocess exists." -ForegroundColor Yellow

Start-Sleep -Seconds 25

# 3.5 claude subprocess delta
$nowClaude = Get-Process -Name 'claude' -ErrorAction SilentlyContinue
$nowCount = ($nowClaude | Measure-Object).Count
if ($nowCount -le $baselineCount) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "No new claude.exe subprocess detected (baseline=$baselineCount, now=$nowCount)"
}
Write-Host "  claude subprocess delta: +$($nowCount - $baselineCount)" -ForegroundColor DarkGray

# RKOJ still healthy
$proc.Refresh()
if ($proc.HasExited) {
    Fail "RKOJ crashed during agent flow"
}

Write-Host "OPERATOR: spawn 2 more agents, then close window via X." -ForegroundColor Yellow
Write-Host "          Script will wait 20s then assert all subprocs died with parent." -ForegroundColor Yellow

Start-Sleep -Seconds 20

# 3.9 RKOJ gone
$still = Get-Process -Name 'RKOJ' -ErrorAction SilentlyContinue
if ($still) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Fail "RKOJ.exe still alive after window-X (expected closed by operator)"
}

# 3.10 No orphan claude procs above baseline
Start-Sleep -Seconds 3
$finalClaude = Get-Process -Name 'claude' -ErrorAction SilentlyContinue
$finalCount = ($finalClaude | Measure-Object).Count
if ($finalCount -gt $baselineCount) {
    Fail "Orphan claude.exe procs remain (baseline=$baselineCount, final=$finalCount)"
}

Write-Host "PASS: Milestone 3 — agent flow spawned claude subproc + all children died with parent." -ForegroundColor Green
exit 0
