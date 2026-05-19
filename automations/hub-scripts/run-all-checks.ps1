# run-all-checks.ps1 - one-shot operator dashboard. Read-only.
# Runs verify-backups + check-hetzner-state + garden_cli in sequence,
# prints a 3-line summary at the end. Auto-closes when all green.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'run-all-checks'

function Section($title) {
    Write-Host ""
    Write-Host ("=== {0} ===" -f $title) -ForegroundColor Cyan
}

$summary = @()
$anyFail = $false

# --- 1. Verify backups ---
Section 'Verify Backups'
$stepStart = Get-Date
$verifyScript = Join-Path $PSScriptRoot 'verify-backups.ps1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verifyScript -Quiet 2>&1 | ForEach-Object { Write-Host "  $_" }
$verifyRc = $LASTEXITCODE
$verifyMs = [int]((Get-Date) - $stepStart).TotalMilliseconds
Add-RunlogStep -Log $log -Name 'verify-backups' -Ok ($verifyRc -eq 0) -Ms $verifyMs -Summary "exit $verifyRc"
if ($verifyRc -ne 0) { $anyFail = $true }

# Pull stats from the latest verify-backups manifest for the summary line
$mdir = Join-Path $HubRoot '12_LLM_ORCHESTRATION\runtime-state\script-runs'
$latestVerify = Get-ChildItem $mdir -Filter 'verify-backups-*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestVerify) {
    try {
        $vm = Get-Content $latestVerify.FullName -Raw | ConvertFrom-Json
        $summary += ("[BACKUPS]   {0} files / {1} MB / scheduled-task={2}" -f $vm.outputs.snapshot_count, $vm.outputs.snapshot_mb, $(if ($vm.steps | Where-Object { $_.name -eq 'scheduled-task' -and $_.ok }) { 'REGISTERED' } else { 'NOT REGISTERED' }))
    } catch {}
}

# --- 2. Check Hetzner state ---
Section 'Check Hetzner State'
$stepStart = Get-Date
$hetznerScript = Join-Path $PSScriptRoot 'check-hetzner-state.ps1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $hetznerScript -Quiet 2>&1 | ForEach-Object { Write-Host "  $_" }
$hetznerRc = $LASTEXITCODE
$hetznerMs = [int]((Get-Date) - $stepStart).TotalMilliseconds
Add-RunlogStep -Log $log -Name 'check-hetzner-state' -Ok ($hetznerRc -eq 0) -Ms $hetznerMs -Summary "exit $hetznerRc"
if ($hetznerRc -ne 0) { $anyFail = $true }

$latestHetzner = Get-ChildItem $mdir -Filter 'check-hetzner-state-*.json' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestHetzner) {
    try {
        $hm = Get-Content $latestHetzner.FullName -Raw | ConvertFrom-Json
        $pending = if ($hm.outputs.pending_deploys) { $hm.outputs.pending_deploys.Count } else { 0 }
        $svcs = $hm.outputs.services
        $upCount = 0; $totalCount = 0
        foreach ($k in $svcs.PSObject.Properties.Name) { $totalCount++; if ($svcs.$k.http_ok) { $upCount++ } }
        $summary += ("[HETZNER]   {0}/{1} services up / {2} pending deploys" -f $upCount, $totalCount, $pending)
    } catch {}
}

# --- 3. Memory garden ---
Section 'Memory Garden'
$stepStart = Get-Date
$gardenScript = Join-Path $HubRoot '12_LLM_ORCHESTRATION\agents\_shared\garden_cli.py'
& python $gardenScript 2>&1 | ForEach-Object { Write-Host "  $_" }
$gardenRc = $LASTEXITCODE
$gardenMs = [int]((Get-Date) - $stepStart).TotalMilliseconds
Add-RunlogStep -Log $log -Name 'memory-garden' -Ok ($gardenRc -eq 0) -Ms $gardenMs -Summary "exit $gardenRc"
if ($gardenRc -ne 0) { $anyFail = $true }

# Read garden snapshot for summary
$gardenJson = Join-Path $HubRoot '12_LLM_ORCHESTRATION\runtime-state\memory-garden-latest.json'
if (Test-Path $gardenJson) {
    try {
        $gj = Get-Content $gardenJson -Raw | ConvertFrom-Json
        $summary += ("[GARDEN]    {0} facts / {1} calls / {2} bots active" -f $gj.totals.facts, $gj.totals.calls, $gj.totals.bots_with_facts)
    } catch {}
}

# --- Summary ---
Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
foreach ($line in $summary) { Write-Host "  $line" -ForegroundColor White }
if (-not $summary) { Write-Host "  (no summary data captured)" -ForegroundColor DarkGray }

Set-RunlogOutput -Log $log -Key 'summary_lines' -Value $summary
$manifestPath = Save-Runlog -Log $log -AutoClose (-not $anyFail)
Write-Host ""
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if (-not $anyFail) {
    if (-not $Quiet) { Write-Host "All checks green. Window auto-closes in 12s." -ForegroundColor Green; Start-Sleep -Seconds 12 }
    exit 0
}
if (-not $Quiet) { Read-Host "Some checks failed. Press Enter to close" }
exit 1
