# seed-resume-points.ps1 — ensure every active lane has at least one resume-point so
# `Start-Sinister-Session.bat` restart restores state ("never closed" per operator
# hard-canonical 2026-05-24T17:01:09Z).
# Author: RKOJ-ELENO :: 2026-05-24
#
# Reads _shared-memory/heartbeats/*.json (active lanes). For each lane, if no resume-point
# exists at the canonical display-name dir, writes a minimal seed resume-point pulling:
#   - branch from heartbeat
#   - focus from heartbeat
#   - last_deliverable from heartbeat
#
# Composes with resume-point-write.ps1 (canonical writer; this seeds the FIRST one).
# Per Resolve-ResumePointDirName convention, display-name dir is canonical.
#
# Usage:
#   powershell -File seed-resume-points.ps1                  # dry-run + report
#   powershell -File seed-resume-points.ps1 -Apply           # actually write seeds
#   powershell -File seed-resume-points.ps1 -Apply -Lane <slug>   # one lane only

[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$Lane = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$HeartbeatDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$ResumeRoot   = Join-Path $SanctumRoot '_shared-memory\resume-points'

# Canonical slug -> display map (mirrors resume-point-write.ps1 v1.3 Resolve-ResumePointDirName).
# When unknown, identity map (slug == display).
$Map = @{
    'sanctum'             = 'Sinister Sanctum'
    'forge'               = 'Sinister Forge'
    'panel'               = 'Sinister Panel'
    'kernel-apk'          = 'Sinister Kernel APK'
    'apk'                 = 'Sinister Kernel APK'
    'sinister-emulator'   = 'Sinister Emulator'
    'sinister-os'         = 'Sinister OS'
    'rkoj'                = 'RKOJ'
    'rkoj-workstation'    = 'RKOJ Workstation'
    'jb-woodworks'        = 'Jb Woodworks'
    'showmasters'         = 'Showmasters'
    'jkor'                = 'JOKR'
    'snap-emulator-api'   = 'sinister-snap-api-quantum'
    'tiktok-emulator-api' = 'TikTok Emulator API'
    'sinister-generator'  = 'Sinister Generator'
    'sinister-term'       = 'Sinister Term'
}

function Resolve-DisplayDir { param([string]$Slug)
    if ($Map.ContainsKey($Slug)) { $Map[$Slug] } else { $Slug }
}

function Should-Skip { param([string]$Slug)
    # Skip non-lane heartbeats (subprocess beats, generic, transient sanctum spawns)
    return ($Slug -match '\.beat$|^phones|^diagnose$|^general$|^inventions$|^sanctum-[0-9a-f]{6}$')
}

$hb = Get-ChildItem -Path $HeartbeatDir -Filter '*.json' -ErrorAction SilentlyContinue
$seeded = @()
$skipped = @()
$alreadyOk = @()

foreach ($f in $hb) {
    $slug = $f.BaseName
    if (Should-Skip $slug) { continue }
    if ($Lane -and $slug -ne $Lane) { continue }

    $display = Resolve-DisplayDir $slug
    $dir = Join-Path $ResumeRoot $display
    $hasRp = (Test-Path $dir) -and (@(Get-ChildItem $dir -Filter '*.json' -ErrorAction SilentlyContinue).Count -gt 0)

    if ($hasRp) { $alreadyOk += $slug; continue }

    # Parse heartbeat for seed material
    try {
        $hbObj = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json
    } catch {
        $skipped += "$slug (heartbeat parse failed: $_)"
        continue
    }

    $branch = if ($hbObj.branch) { $hbObj.branch } else { '(unknown)' }
    $focus  = if ($hbObj.focus)  { $hbObj.focus }  else { 'first-spawn baseline (seeded by seed-resume-points.ps1)' }
    $last   = if ($hbObj.last_deliverable) { $hbObj.last_deliverable } else { '' }

    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmmssZ")
    $tsHuman = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mmZ")
    $rp = [ordered]@{
        schema_version  = 'sinister.resume-point.v1'
        ts_utc          = $tsHuman
        project         = $slug
        agent_name      = $slug
        mode            = 'resume'
        focus_intent    = $focus
        seeded_by       = 'seed-resume-points.ps1 (test-modes-verify lane)'
        seed_reason     = 'no prior resume-point existed; created baseline so Start-Sinister-Session.bat restart restores state'
        git             = [ordered]@{
            branch   = $branch
            head     = '(use git rev-parse HEAD at restore-time)'
            head_msg = ''
        }
        progress_top3   = @(if ($last) { $last } else { 'first session (no prior progress)' })
        last_5_files_touched_24h = @()
        pre_warm_reads  = @(
            "$SanctumRoot\CLAUDE.md",
            "$SanctumRoot\_shared-memory\PROGRESS\$slug.md",
            "$SanctumRoot\_shared-memory\heartbeats\$slug.json"
        )
    }

    $rpPath = Join-Path $dir "$ts.json"

    if ($Apply) {
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $rp | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $rpPath -Encoding UTF8
        $seeded += "$slug -> $rpPath"
    } else {
        $seeded += "$slug -> $rpPath (DRY-RUN)"
    }
}

Write-Output "----- seed-resume-points report -----"
Write-Output "already-ok: $($alreadyOk.Count)"
Write-Output "seeded:     $($seeded.Count)$(if (-not $Apply) { ' (dry-run; pass -Apply to actually write)' })"
Write-Output "skipped:    $($skipped.Count)"
Write-Output ""
if ($seeded.Count -gt 0) {
    Write-Output "Seeded lanes:"
    $seeded | ForEach-Object { Write-Output "  - $_" }
}
if ($skipped.Count -gt 0) {
    Write-Output ""
    Write-Output "Skipped (errors):"
    $skipped | ForEach-Object { Write-Output "  - $_" }
}
