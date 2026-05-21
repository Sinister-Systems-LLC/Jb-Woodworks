# Sinister Sanctum :: context-pruner (v1 :: 2026-05-21)
# Operator: "clean as it works with things we dont need so the context never
# gets filled up or capped." Rotates stale inbox/cross-agent/plans/PROGRESS
# into _archive/ subdirs so agent CONTEXT-REVIEW reads stay bounded.
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
    if (-not $Quiet) { Write-Host "[context-pruner] SanctumRoot not found: $SanctumRoot" -ForegroundColor Red }
    exit 1
}

$moved = 0
$action = if ($DryRun) { 'would' } else { 'did' }

function Move-To-Archive {
    param([string]$Path)
    $dir = Split-Path $Path -Parent
    $archive = Join-Path $dir '_archive'
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $archive | Out-Null
        Move-Item -Path $Path -Destination $archive -Force -ErrorAction SilentlyContinue
    }
}

foreach ($slug in @('test','panel','kernel-apk','rkoj','snap-emu','tiktok-emu','sinister-bumble','letstext','sinister-emulator','sanctum-audit','me','eleno')) {
    $inboxDir = Join-Path $SanctumRoot "_shared-memory\inbox\$slug"
    if (-not (Test-Path $inboxDir)) { continue }
    $cutoff = (Get-Date).AddDays(-7)
    $old = @(Get-ChildItem $inboxDir -Filter '*.json' -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff -and $_.Directory.Name -ne '_archive' })
    foreach ($f in $old) {
        Move-To-Archive $f.FullName
        $moved++
    }
}

$crossDir = Join-Path $SanctumRoot '_shared-memory\cross-agent'
if (Test-Path $crossDir) {
    $cutoff = (Get-Date).AddDays(-30)
    $old = @(Get-ChildItem $crossDir -Filter '*.md' -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff -and $_.Directory.Name -ne '_archive' })
    foreach ($f in $old) {
        Move-To-Archive $f.FullName
        $moved++
    }
}

$plansRoot = Join-Path $SanctumRoot '_shared-memory\plans'
if (Test-Path $plansRoot) {
    $cutoff = (Get-Date).AddDays(-14)
    $candidates = @(Get-ChildItem $plansRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff -and (Test-Path (Join-Path $_.FullName 'plan.json')) -and $_.Name -ne '_archive' })
    foreach ($p in $candidates) {
        try {
            $pj = Get-Content (Join-Path $p.FullName 'plan.json') -Raw | ConvertFrom-Json
            if ($pj.status -eq 'shipped' -or $pj.status -eq 'completed') {
                $archive = Join-Path $plansRoot '_archive'
                if (-not $DryRun) {
                    New-Item -ItemType Directory -Force -Path $archive | Out-Null
                    Move-Item -Path $p.FullName -Destination $archive -Force -ErrorAction SilentlyContinue
                }
                $moved++
            }
        } catch { }
    }
}

$progressRoot = Join-Path $SanctumRoot '_shared-memory\PROGRESS'
if (Test-Path $progressRoot) {
    $progressArchive = Join-Path $progressRoot '_archive'
    foreach ($f in Get-ChildItem $progressRoot -Filter '*.md' -ErrorAction SilentlyContinue) {
        if ($f.Directory.Name -eq '_archive') { continue }
        $lines = Get-Content $f.FullName -ErrorAction SilentlyContinue
        if ($lines.Count -gt 2000) {
            $keep = $lines | Select-Object -First 1000
            $arch = $lines | Select-Object -Skip 1000
            if (-not $DryRun) {
                New-Item -ItemType Directory -Force -Path $progressArchive | Out-Null
                $archiveFile = Join-Path $progressArchive ("{0}-pre-{1:yyyy-MM-dd-HHmm}.md" -f $f.BaseName, (Get-Date))
                $arch | Out-File $archiveFile -Encoding utf8
                $keep | Out-File $f.FullName -Encoding utf8
            }
            $moved++
            if (-not $Quiet) { Write-Host "[context-pruner] $action rotate $($f.Name): kept 1000 / archived $($arch.Count)" -ForegroundColor DarkGray }
        }
    }
}

if (-not $Quiet) {
    if ($moved -gt 0) {
        Write-Host "[context-pruner] OK ($moved items $action archive)" -ForegroundColor Green
    } else {
        Write-Host "[context-pruner] OK (nothing to prune)" -ForegroundColor DarkGray
    }
}
