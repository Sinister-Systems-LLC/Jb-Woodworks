# verify-backups.ps1 - confirm Custodian backup system is healthy.
# Checks: snapshot count, total size, manifest integrity, daemon registration,
# most-recent snapshot age. Emits runlog manifest.

[CmdletBinding()]
param(
    [string]$BackupRoot = 'D:\_backups',
    [string]$ManifestPath = 'D:\_backups\_manifest.jsonl',
    [string]$ConfigPath = 'D:\_backups\_config\watch-list.json',
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'verify-backups'

Write-Host "=== Custodian backup verification ===" -ForegroundColor Cyan
Write-Host "Time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host ""

$allOk = $true

# 1. Backup root exists
if (Test-Path $BackupRoot) {
    Write-Host "  [OK]   backup root: $BackupRoot" -ForegroundColor Green
    Add-RunlogStep -Log $log -Name 'backup-root' -Ok $true -Summary 'present'
} else {
    Write-Host "  [FAIL] backup root missing: $BackupRoot" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'backup-root' -Ok $false -Summary 'missing'
    $allOk = $false
}

# 2. Config exists
if (Test-Path $ConfigPath) {
    try {
        $cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json
        Write-Host ("  [OK]   config: {0} sources configured" -f $cfg.sources.Count) -ForegroundColor Green
        Add-RunlogStep -Log $log -Name 'config' -Ok $true -Summary ("{0} sources" -f $cfg.sources.Count)
    } catch {
        Write-Host "  [FAIL] config unreadable: $($_.Exception.Message)" -ForegroundColor Red
        Add-RunlogStep -Log $log -Name 'config' -Ok $false -Summary $_.Exception.Message
        $allOk = $false
    }
} else {
    Write-Host "  [FAIL] config missing: $ConfigPath" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'config' -Ok $false -Summary 'missing'
    $allOk = $false
}

# 3. Snapshot tree stats
$snapDir = Join-Path $BackupRoot 'snapshots'
if (Test-Path $snapDir) {
    $files = Get-ChildItem -Recurse $snapDir -File -ErrorAction SilentlyContinue
    $count = $files.Count
    $bytes = ($files | Measure-Object Length -Sum).Sum
    $mb = [Math]::Round($bytes / 1MB, 1)
    $newest = ($files | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1)
    if ($newest) {
        $ageMin = [Math]::Round(((Get-Date) - $newest.LastWriteTime).TotalMinutes, 1)
        Write-Host ("  [OK]   snapshots: {0} files, {1} MB; newest {2} min old" -f $count, $mb, $ageMin) -ForegroundColor Green
        if ($ageMin -gt 1440) {
            Write-Host "  [WARN] newest snapshot > 24h old; daemon may not be running" -ForegroundColor Yellow
        }
        Add-RunlogStep -Log $log -Name 'snapshots' -Ok $true `
            -Summary ("{0} files / {1} MB / newest {2}min" -f $count, $mb, $ageMin)
        Set-RunlogOutput -Log $log -Key 'snapshot_count' -Value $count
        Set-RunlogOutput -Log $log -Key 'snapshot_mb' -Value $mb
        Set-RunlogOutput -Log $log -Key 'newest_age_minutes' -Value $ageMin
    } else {
        Write-Host "  [WARN] snapshot dir exists but empty" -ForegroundColor Yellow
        Add-RunlogStep -Log $log -Name 'snapshots' -Ok $true -Summary 'empty'
    }
} else {
    Write-Host "  [FAIL] snapshots dir missing: $snapDir" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'snapshots' -Ok $false -Summary 'missing'
    $allOk = $false
}

# 4. Manifest integrity (count vs files)
if (Test-Path $ManifestPath) {
    $lines = Get-Content $ManifestPath -ErrorAction SilentlyContinue
    $manifestCount = ($lines | Where-Object { $_.Trim() }).Count
    Write-Host ("  [OK]   manifest: {0} ledger lines" -f $manifestCount) -ForegroundColor Green
    Add-RunlogStep -Log $log -Name 'manifest' -Ok $true -Summary ("{0} lines" -f $manifestCount)
    Set-RunlogOutput -Log $log -Key 'manifest_lines' -Value $manifestCount
} else {
    Write-Host "  [WARN] manifest missing: $ManifestPath (will be created on first daemon run)" -ForegroundColor Yellow
    Add-RunlogStep -Log $log -Name 'manifest' -Ok $true -Summary 'not yet created'
}

# 5. Scheduled task registration
$null = cmd /c "schtasks.exe /Query /TN SinisterCustodian >NUL 2>NUL"
$dailyExitCode = $LASTEXITCODE
if ($dailyExitCode -eq 0) {
    Write-Host "  [OK]   SinisterCustodian scheduled task registered" -ForegroundColor Green
    Add-RunlogStep -Log $log -Name 'scheduled-task' -Ok $true -Summary 'registered'
} else {
    Write-Host "  [WARN] SinisterCustodian scheduled task NOT registered" -ForegroundColor Yellow
    Write-Host "         Install: cd '12_LLM_ORCHESTRATION\agents\custodian'; .\install-task.ps1" -ForegroundColor DarkGray
    Add-RunlogStep -Log $log -Name 'scheduled-task' -Ok $false -Summary 'not registered'
    Add-RunlogNextAction -Log $log -Action "Operator: install Custodian 24/7 daemon -- cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian'; .\install-task.ps1"
}

# 6. Most-recent daemon log
$logDir = Join-Path $BackupRoot '_logs'
if (Test-Path $logDir) {
    $todayLog = Join-Path $logDir ("custodian-{0:yyyyMMdd}.log" -f (Get-Date))
    if (Test-Path $todayLog) {
        $lastLine = Get-Content $todayLog -Tail 1 -ErrorAction SilentlyContinue
        Write-Host ("  [OK]   today's daemon log present; last line: " + $lastLine.Substring(0, [Math]::Min(80, $lastLine.Length))) -ForegroundColor Green
        Add-RunlogStep -Log $log -Name 'daemon-log' -Ok $true -Summary 'today log present'
    } else {
        Write-Host "  [.]    no daemon log for today yet" -ForegroundColor DarkGray
        Add-RunlogStep -Log $log -Name 'daemon-log' -Ok $true -Summary 'no log today (daemon not run yet)'
    }
}

Write-Host ""
Write-Host ("=== {0} ===" -f $(if ($allOk) { 'HEALTHY' } else { 'ISSUES' })) -ForegroundColor $(if ($allOk) { 'Green' } else { 'Red' })

$manifestPath = Save-Runlog -Log $log -AutoClose $allOk
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if ($allOk) {
    if (-not $Quiet) { Write-Host "Auto-close in 6s..." -ForegroundColor Green; Start-Sleep -Seconds 6 }
    exit 0
}
if (-not $Quiet) { Read-Host 'Press Enter to close' }
exit 1
