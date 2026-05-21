# Sinister Sanctum :: auto-cleanup (v1 :: 2026-05-21)
#
# Prunes stale state to keep the workspace lean:
#   * backups/ dirs > 7 days old (keeps last 7 daily snapshots)
#   * scratch/ subdirs with no mtime change in 30 days
#   * _shared-memory/_archive/ files > 90 days old
#   * /tmp/* > 30 days old (if running on this PC)
#   * automations/window-manager/_build-logs/ > 14 days old
#
# Fired by bootstrap-portability.ps1 on every session start (only does work
# if there's something to clean). Operator directive: "make sure the sanctum
# also auto cleans backups, or things we dont need anymore. tie this into
# session start if needed."
#
# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

param(
    [string]$SanctumRoot = '',
    [switch]$DryRun,
    [switch]$Quiet
)

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}
if (-not (Test-Path $SanctumRoot)) {
    if (-not $Quiet) { Write-Host "[auto-cleanup] SanctumRoot not found: $SanctumRoot" -ForegroundColor Yellow }
    exit 1
}

$totalFreedMb = 0
$action = if ($DryRun) { '(dry-run) would delete' } else { 'deleted' }

function Remove-If-Old {
    param([string]$Path, [int]$DaysOld, [string]$Label, [switch]$Dirs)
    if (-not (Test-Path $Path)) { return 0 }
    $cutoff = (Get-Date).AddDays(-$DaysOld)
    $freedMb = 0
    try {
        if ($Dirs) {
            $targets = Get-ChildItem -Path $Path -Directory -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff }
        } else {
            $targets = Get-ChildItem -Path $Path -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff }
        }
        foreach ($t in $targets) {
            $sizeMb = 0
            try {
                if ($Dirs) {
                    $sizeMb = [math]::Round(((Get-ChildItem $t.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB), 1)
                } else {
                    $sizeMb = [math]::Round(($t.Length / 1MB), 2)
                }
            } catch { }
            if (-not $DryRun) {
                Remove-Item -Path $t.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
            $freedMb += $sizeMb
        }
        if ($targets.Count -gt 0 -and -not $Quiet) {
            Write-Host ("[auto-cleanup] {0} {1} {2} ({3} MB freed)" -f $action, $targets.Count, $Label, $freedMb) -ForegroundColor DarkGray
        }
    } catch {
        if (-not $Quiet) { Write-Host ("[auto-cleanup] {0} clean failed: {1}" -f $Label, $_.Exception.Message) -ForegroundColor Yellow }
    }
    return $freedMb
}

# 1. backups/ dirs > 7 days
$totalFreedMb += Remove-If-Old -Path (Join-Path $SanctumRoot 'backups') -DaysOld 7 -Label 'backup snapshots' -Dirs

# 2. scratch/ subdirs in each project's me/ + eleno/ > 30 days mtime
foreach ($p in @('sinister-snap-emu','sinister-tiktok-emu','sinister-panel','sinister-kernel-apk','sinister-bumble-emu')) {
    foreach ($op in @('me','eleno')) {
        $scratchPath = Join-Path $SanctumRoot "projects\$p\$op\scratch"
        $totalFreedMb += Remove-If-Old -Path $scratchPath -DaysOld 30 -Label "scratch ($p/$op)" -Dirs
    }
}

# 3. _shared-memory/_archive/ > 90 days
$totalFreedMb += Remove-If-Old -Path (Join-Path $SanctumRoot '_shared-memory\_archive') -DaysOld 90 -Label 'archived files'

# 4. window-manager build logs > 14 days
$totalFreedMb += Remove-If-Old -Path (Join-Path $SanctumRoot 'automations\window-manager\_build-logs') -DaysOld 14 -Label 'build logs'

# 5. PROGRESS/_archive > 60 days
$totalFreedMb += Remove-If-Old -Path (Join-Path $SanctumRoot '_shared-memory\PROGRESS\_archive') -DaysOld 60 -Label 'archived PROGRESS'

if (-not $Quiet) {
    if ($totalFreedMb -gt 0) {
        Write-Host ("[auto-cleanup] OK ({0:N1} MB freed total)" -f $totalFreedMb) -ForegroundColor Green
    } else {
        Write-Host "[auto-cleanup] OK (nothing to clean)" -ForegroundColor DarkGray
    }
}
