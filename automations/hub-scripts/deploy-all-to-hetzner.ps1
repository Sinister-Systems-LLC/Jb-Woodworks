# deploy-all-to-hetzner.ps1 - one-click orchestrator: for each Hetzner project
# with pending commits, run its source-side deploy bat. Operator runs this.
#
# Idempotent: if nothing is pending, exits OK without doing anything.
# Always runs check-hetzner-state.ps1 first to identify what's pending.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [switch]$DryRun,
    [switch]$Quiet,
    [switch]$Force          # deploy even if check shows in-sync (operator override)
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'deploy-all-to-hetzner'

# Deploy bat per project. Operator confirms these paths.
$Deploys = @(
    @{ name='sinister-panel';
       source='C:\Users\Zonia\Desktop\Sinister-Panel';
       bat='Sinister_OneClick_Deploy.bat' }
    # RKA: no one-click bat documented yet; operator SSH-deploys manually.
    # Add here when one exists:
    # @{ name='sinister-rka';
    #    source='C:\Users\Zonia\Desktop\Sinister RKA GOOD';
    #    bat='deploy-hetzner.bat' }
)

Write-Host "=== Deploy all to Hetzner ===" -ForegroundColor Cyan
Write-Host "DryRun=$DryRun  Force=$Force"
Write-Host ""

# Step 1: state check (re-runs check-hetzner-state.ps1; reads its manifest)
Write-Host "[1] Pre-flight: check Hetzner state" -ForegroundColor Yellow
$check = Join-Path $PSScriptRoot 'check-hetzner-state.ps1'
if (Test-Path $check) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $check -Quiet | ForEach-Object { Write-Host "    $_" }
} else {
    Write-Host "  [WARN] check-hetzner-state.ps1 not found; proceeding without pre-flight"
}

# Read latest check manifest to get pending list
$manifestDir = Join-Path $HubRoot '12_LLM_ORCHESTRATION\runtime-state\script-runs'
$latestCheck = Get-ChildItem -Path $manifestDir -Filter 'check-hetzner-state-*.json' -ErrorAction SilentlyContinue |
               Sort-Object LastWriteTime -Descending | Select-Object -First 1
$pendingFromCheck = @()
if ($latestCheck) {
    try {
        $m = Get-Content $latestCheck.FullName -Raw | ConvertFrom-Json
        if ($m.outputs.pending_deploys) {
            $pendingFromCheck = @($m.outputs.pending_deploys)
        }
    } catch {}
}

Write-Host ""
Write-Host "Pending deploys (per state check): $($pendingFromCheck -join ', ')" -ForegroundColor Cyan

# Step 2: per-project deploy
foreach ($d in $Deploys) {
    Write-Host ""
    Write-Host "[2.$($d.name)]" -ForegroundColor Yellow
    $shouldDeploy = $Force -or ($pendingFromCheck -contains $d.name)
    if (-not $shouldDeploy) {
        Write-Host "  [SKIP] not in pending list (use -Force to deploy anyway)" -ForegroundColor DarkGray
        Add-RunlogStep -Log $log -Name $d.name -Ok $true -Summary 'skipped (not pending)'
        continue
    }
    $batPath = Join-Path $d.source $d.bat
    if (-not (Test-Path $batPath)) {
        Write-Host "  [FAIL] deploy bat not found: $batPath" -ForegroundColor Red
        Add-RunlogStep -Log $log -Name $d.name -Ok $false -Summary "deploy bat missing: $($d.bat)"
        continue
    }
    if ($DryRun) {
        Write-Host "  [DRY] would run: $batPath" -ForegroundColor DarkGray
        Add-RunlogStep -Log $log -Name $d.name -Ok $true -Summary 'dry-run'
        continue
    }
    $stepStart = Get-Date
    Write-Host "  Running: $batPath" -ForegroundColor Green
    Push-Location $d.source
    try {
        & cmd /c $batPath 2>&1 | ForEach-Object { Write-Host "    $_" }
        $rc = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    $ms = [int]((Get-Date) - $stepStart).TotalMilliseconds
    Add-RunlogStep -Log $log -Name $d.name -Ok ($rc -eq 0) -Ms $ms -Summary "deploy bat exit $rc"
}

# Step 3: post-flight state check
Write-Host ""
Write-Host "[3] Post-flight: re-check Hetzner state" -ForegroundColor Yellow
if (Test-Path $check) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $check -Quiet | ForEach-Object { Write-Host "    $_" }
}

Set-RunlogOutput -Log $log -Key 'attempted_deploys' -Value ($Deploys | ForEach-Object { $_.name })
Add-RunlogNextAction -Log $log -Action 'Operator: in Claude session, run sinister-bus.runlog_latest deploy-all-to-hetzner for the full rollup.'
Add-RunlogNextAction -Log $log -Action 'Operator: verify live behaviour at the URLs (sinister-panel: https://snap.sinijkr.com/).'

$allOk = ($log.errors.Count -eq 0)
$manifestPath = Save-Runlog -Log $log -AutoClose $allOk

Write-Host ""
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if ($allOk) {
    if (-not $Quiet) { Write-Host "Done. Window will auto-close in 5s." -ForegroundColor Green; Start-Sleep -Seconds 5 }
    exit 0
}
if (-not $Quiet) { Read-Host 'Press Enter to close' }
exit 1
