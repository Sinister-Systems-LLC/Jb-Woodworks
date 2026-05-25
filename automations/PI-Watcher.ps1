# Author: RKOJ-ELENO :: 2026-05-24
# PI-Watcher.ps1 -- auto-detect + auto-fix Play Integrity degradation on both phones
# Runs via scheduled task SinisterKernelAPK-PI-Watcher every 30 min.
# Composes with:
#   automations/Fix-PI-Both-Phones.bat (the fix sequence)
#   automations/Install-PI-Watcher-Task.ps1 (scheduled-task installer)
#   _shared-memory/plans/kernel-apk-andrewt407-x5-2026-05-24/master-plan.md (iter 0 prevention)
# Operator hard-canonical 2026-05-24T23:46Z: "dont let that shit happen again".

param(
    [string]$P1Serial = "2A061JEGR09301",
    [string]$P2Serial = "26031JEGR17598",
    [string]$SanctumRoot = "D:\Sinister Sanctum",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$utc = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$progressPath = Join-Path $SanctumRoot "_shared-memory\PROGRESS\Sinister Kernel APK.md"
$fixBat       = Join-Path $SanctumRoot "automations\Fix-PI-Both-Phones.bat"

function Test-PhoneReachable {
    param([string]$Serial)
    $null = & adb -s $Serial get-state 2>$null
    return ($LASTEXITCODE -eq 0)
}

function Get-PIVerdict {
    param([string]$Serial)
    $out = & adb -s $Serial shell "content query --uri content://com.scottyab.rootbeer.sample.provider/playintegrity" 2>$null
    if (-not $out) { return "unknown" }
    $strong = if ($out -match "STRONG_INTEGRITY\s*=\s*(1|true)") { 1 } else { 0 }
    $device = if ($out -match "DEVICE_INTEGRITY\s*=\s*(1|true)") { 1 } else { 0 }
    $basic  = if ($out -match "BASIC_INTEGRITY\s*=\s*(1|true)") { 1 } else { 0 }
    $sum = $strong + $device + $basic
    if ($sum -eq 0 -and $out -notmatch "INTEGRITY") { return "unknown" }
    return "$sum/3"
}

function Add-ProgressRow {
    param([string]$Msg)
    if (-not (Test-Path $progressPath)) { return }
    $row = "`r`n`r`n---`r`n`r`n## $utc -- PI-Watcher: $Msg`r`n`r`n**Author:** RKOJ-ELENO :: PI-Watcher.ps1 ($utc)`r`n"
    $existing = Get-Content $progressPath -Raw
    $headerAnchor = "Append-only progress log. Most recent at top."
    $idx = $existing.IndexOf($headerAnchor)
    if ($idx -lt 0) { return }
    $insertAt = $idx + $headerAnchor.Length
    $before = $existing.Substring(0, $insertAt)
    $after  = $existing.Substring($insertAt)
    Set-Content -Path $progressPath -Value ($before + $row + $after) -NoNewline -Encoding UTF8
}

Write-Host "=== PI-Watcher tick :: $utc ===" -ForegroundColor Cyan

$p1Reach = Test-PhoneReachable -Serial $P1Serial
$p2Reach = Test-PhoneReachable -Serial $P2Serial

if (-not $p1Reach -and -not $p2Reach) {
    Write-Host "[SKIP] Neither phone reachable. Exit clean." -ForegroundColor Yellow
    exit 0
}

$p1Verdict = if ($p1Reach) { Get-PIVerdict -Serial $P1Serial } else { "unreachable" }
$p2Verdict = if ($p2Reach) { Get-PIVerdict -Serial $P2Serial } else { "unreachable" }

Write-Host ("P1 ({0}): {1}" -f $P1Serial, $p1Verdict)
Write-Host ("P2 ({0}): {1}" -f $P2Serial, $p2Verdict)

$p1Degraded = ($p1Reach -and $p1Verdict -ne "3/3" -and $p1Verdict -ne "unknown")
$p2Degraded = ($p2Reach -and $p2Verdict -ne "3/3" -and $p2Verdict -ne "unknown")
$needsFix = $p1Degraded -or $p2Degraded

if (-not $needsFix) {
    Write-Host "[OK] No degradation detected. No action." -ForegroundColor Green
    exit 0
}

if ($DryRun) {
    Write-Host ("[DRY-RUN] Would fire Fix-PI-Both-Phones.bat (P1={0} P2={1})" -f $p1Verdict, $p2Verdict) -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $fixBat)) {
    Write-Host ("[FAIL] Fix bat missing: {0}" -f $fixBat) -ForegroundColor Red
    Add-ProgressRow -Msg "PI degraded but Fix-PI-Both-Phones.bat missing at expected path; manual intervention required."
    exit 13
}

Write-Host "[ACTION] PI degraded -- firing Fix-PI-Both-Phones.bat" -ForegroundColor Magenta
& cmd /c "`"$fixBat`""
$fixExit = $LASTEXITCODE

# Re-probe post-fix
Start-Sleep -Seconds 5
$p1AfterReach = Test-PhoneReachable -Serial $P1Serial
$p2AfterReach = Test-PhoneReachable -Serial $P2Serial
$p1After = if ($p1AfterReach) { Get-PIVerdict -Serial $P1Serial } else { "unreachable" }
$p2After = if ($p2AfterReach) { Get-PIVerdict -Serial $P2Serial } else { "unreachable" }

$msg = ("PI degraded -> auto-fix fired (exit={0}). Before: P1={1} P2={2}. After: P1={3} P2={4}." -f $fixExit, $p1Verdict, $p2Verdict, $p1After, $p2After)
Write-Host $msg
Add-ProgressRow -Msg $msg
exit 0
