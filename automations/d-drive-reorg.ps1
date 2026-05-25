# d-drive-reorg.ps1 — execute the 3-folder D:\ reorganization.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24 (screenshot of D:\ Explorer):
#   "I want here all this shit sorted. I want personal folder, sinister sanctum
#    folder and backups thats it. everything else needs to be sorted and such and
#    make sure it all still works and what not."
#
# Target end state (exactly 3 folders at D:\ root, excluding system entries):
#   D:\Personal\          — everything personal (operator's apps, side biz, archives)
#   D:\Sinister Sanctum\  — orchestration hub (UNCHANGED structure; absorbs Skills + worktrees)
#   D:\Backups\           — every backup, dated, organized
#
# Reuses the 2026-05-21 plan at _shared-memory/plans/d-drive-reorg-2026-05-21/plan.md
# but adapts to today's stricter target (LetsText + Research + Seagate go into Personal,
# not stay at root).
#
# Usage:
#   powershell -File d-drive-reorg.ps1                        # dry-run report (default)
#   powershell -File d-drive-reorg.ps1 -Phase 2 -DryRun:$false # execute Phase 2 (purely personal moves)
#   powershell -File d-drive-reorg.ps1 -Phase 3 -DryRun:$false # execute Phase 3 (worktrees + junctions)
#   powershell -File d-drive-reorg.ps1 -Phase 4 -DryRun:$false # execute Phase 4 (Sinister Skills + Sinister/ rename)
#   powershell -File d-drive-reorg.ps1 -Phase all -DryRun:$false  # ALL PHASES (operator only)
#
# Each phase is independently re-runnable; already-moved items are skipped.
# Reference updates happen automatically in CLAUDE.md, projects.json, agent-prefs.json.

[CmdletBinding()]
param(
    [ValidateSet('1','2','3','4','all')] [string]$Phase = '1',
    [bool]$DryRun = $true,
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$logRows = @()

function Log {
    param([string]$Action, [string]$Path, [string]$Detail = '')
    $tag = if ($DryRun) { '[dry-run]' } else { '[exec]' }
    $line = ("{0} {1,-12} {2}  {3}" -f $tag, $Action, $Path, $Detail).TrimEnd()
    Write-Host $line
    $script:logRows += $line
}

function Safe-Move {
    param([string]$From, [string]$To, [string]$Why = '')
    if (-not (Test-Path $From)) { Log 'skip-noent' $From "(source missing)"; return $false }
    if (Test-Path $To) { Log 'skip-exists' $To "(destination already exists, source still at $From)"; return $false }
    $parent = Split-Path $To -Parent
    if (-not (Test-Path $parent)) {
        if ($DryRun) { Log 'mkdir' $parent } else { New-Item -ItemType Directory -Path $parent -Force | Out-Null; Log 'mkdir' $parent }
    }
    Log 'move' "$From -> $To" $Why
    if (-not $DryRun) {
        try { Move-Item -LiteralPath $From -Destination $To -Force; return $true }
        catch { Log 'move-FAIL' $From $_.Exception.Message; return $false }
    }
    return $true
}

function Remove-JunctionSafely {
    param([string]$Path)
    if (-not (Test-Path $Path)) { Log 'skip-noent' $Path "(junction missing)"; return $false }
    $it = Get-Item $Path -Force
    if (-not (($it.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) {
        Log 'skip-notjunc' $Path "(not a junction; refusing)"; return $false
    }
    $target = try { $it.Target } catch { $null }
    Log 'rm-junction' $Path "(target was: $target)"
    if (-not $DryRun) {
        try { [System.IO.Directory]::Delete($Path); return $true }
        catch { Log 'rm-junc-FAIL' $Path $_.Exception.Message; return $false }
    }
    return $true
}

function Update-RefInFile {
    param([string]$File, [string]$Old, [string]$New)
    if (-not (Test-Path $File)) { return 0 }
    $content = Get-Content -LiteralPath $File -Raw -Encoding UTF8
    if (-not $content) { return 0 }
    $oldEsc = [regex]::Escape($Old)
    $matches = [regex]::Matches($content, $oldEsc)
    if ($matches.Count -eq 0) { return 0 }
    Log 'ref-update' $File "($($matches.Count) refs: '$Old' -> '$New')"
    if (-not $DryRun) {
        $new = $content -replace $oldEsc, $New
        [System.IO.File]::WriteAllText($File, $new, [System.Text.UTF8Encoding]::new($false))
    }
    return $matches.Count
}

Write-Host ''
Write-Host ('=== D-drive reorganization - phase ' + $Phase + ' ===') -ForegroundColor Cyan
$drColor = if ($DryRun) { 'Yellow' } else { 'Green' }
Write-Host ('DryRun = ' + $DryRun) -ForegroundColor $drColor
Write-Host 'Pass -DryRun:0 to execute changes.' -ForegroundColor $drColor
Write-Host ''

# ============================================================
# PHASE 1 — already done by previous executions (Mac junk, skeletons)
# Re-runs ensure idempotency.
# ============================================================
if ($Phase -in @('1','all')) {
    Write-Host "--- Phase 1: skeleton + Mac junk ---" -ForegroundColor Magenta
    foreach ($f in @('D:\._', 'D:\.VolumeIcon.icns', 'D:\.VolumeIcon.ico')) {
        if (Test-Path $f) {
            Log 'rm-junk' $f
            if (-not $DryRun) { try { Remove-Item $f -Force } catch { Log 'rm-FAIL' $f $_.Exception.Message } }
        }
    }
    foreach ($d in @('D:\Personal', 'D:\Backups')) {
        if (-not (Test-Path $d)) {
            Log 'mkdir' $d "(skeleton)"
            if (-not $DryRun) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
        }
    }
    # Create MANIFEST.md inside Backups (operator-requested 2026-05-21)
    $manifest = 'D:\Backups\MANIFEST.md'
    if (-not (Test-Path $manifest)) {
        Log 'create' $manifest "(operator-requested text file)"
        if (-not $DryRun) {
            $now = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            $lines = @(
                '# D:\Backups\ — manifest',
                '',
                '> Author: RKOJ-ELENO :: 2026-05-24',
                "> Generated: $now (auto by d-drive-reorg.ps1)",
                '',
                'This folder holds every backup the workstation produces. Everything is dated and organized into subfolders by source.',
                '',
                '## Subfolders',
                '',
                '- `_backups-merged\`  — original D:\_backups\ contents (custodian snapshots)',
                '- `Backups-old\`      — original D:\Backups\ contents (legacy)',
                '- `sanctum-daily\`    — dated robocopy backups of Sinister Sanctum',
                '- `_logs\`            — backup operation logs (robocopy, custodian)',
                '- `d-misnamed\`       — D:\d\ (was a misplaced Sanctum clone — kept for recovery)',
                '- `_shared-memory-root\` — D:\_shared-memory\ (stale root copy)',
                '',
                '## Recovery',
                '',
                'To restore a Sanctum snapshot:',
                '`robocopy "D:\Backups\sanctum-daily\YYYY-MM-DD" "D:\Sinister Sanctum" /MIR /XD .git`'
            )
            Set-Content -LiteralPath $manifest -Value ($lines -join "`n") -Encoding UTF8
        }
    }
}

# ============================================================
# PHASE 2 — PURELY PERSONAL moves (medium risk, ref updates needed)
# Move into D:\Personal\: LetsText, Research, Seagate, jbw-*
# Update: projects.json (D:\LetsText -> D:\Personal\LetsText), agent-prefs if any
# ============================================================
if ($Phase -in @('2','all')) {
    Write-Host ""
    Write-Host "--- Phase 2: personal moves (LetsText, Research, Seagate, jbw-*) ---" -ForegroundColor Magenta
    $personalMoves = @(
        @{From='D:\LetsText';      To='D:\Personal\LetsText';      Why='operator app'}
        @{From='D:\Research';      To='D:\Personal\Research';      Why='personal research'}
        @{From='D:\Seagate';       To='D:\Personal\Seagate';       Why='external-drive legacy'}
        @{From='D:\jbw-deploy';    To='D:\Personal\jbw-deploy';    Why='JB Woodworks deploy worktree'}
        @{From='D:\jbw-proxy';     To='D:\Personal\jbw-proxy';     Why='JB Woodworks proxy worktree'}
        @{From='D:\jbw-standalone';To='D:\Personal\jbw-standalone';Why='JB Woodworks standalone worktree'}
        @{From='D:\jbw-wt';        To='D:\Personal\jbw-wt';        Why='JB Woodworks worktree'}
    )
    foreach ($m in $personalMoves) { $null = Safe-Move @m }

    # Ref updates after moves
    $refs = @(
        @{Old='D:\LetsText';      New='D:\Personal\LetsText'}
        @{Old='D:\\LetsText';     New='D:\\Personal\\LetsText'}      # JSON-escaped form
        @{Old='D:\Research';      New='D:\Personal\Research'}
        @{Old='D:\\Research';     New='D:\\Personal\\Research'}
        @{Old='D:\Seagate';       New='D:\Personal\Seagate'}
        @{Old='D:\\Seagate';      New='D:\\Personal\\Seagate'}
        @{Old='D:\jbw-deploy';    New='D:\Personal\jbw-deploy'}
        @{Old='D:\\jbw-deploy';   New='D:\\Personal\\jbw-deploy'}
        @{Old='D:\jbw-proxy';     New='D:\Personal\jbw-proxy'}
        @{Old='D:\\jbw-proxy';    New='D:\\Personal\\jbw-proxy'}
        @{Old='D:\jbw-standalone';New='D:\Personal\jbw-standalone'}
        @{Old='D:\\jbw-standalone';New='D:\\Personal\\jbw-standalone'}
        @{Old='D:\jbw-wt';        New='D:\Personal\jbw-wt'}
        @{Old='D:\\jbw-wt';       New='D:\\Personal\\jbw-wt'}
    )
    $refFiles = @(
        'D:\Sinister Sanctum\CLAUDE.md',
        'D:\Sinister Sanctum\automations\session-templates\projects.json',
        'D:\Sinister Sanctum\automations\session-templates\personal-projects.json',
        'D:\Sinister Sanctum\automations\session-templates\agent-prefs.json'
    )
    foreach ($f in $refFiles) {
        foreach ($r in $refs) { $null = Update-RefInFile -File $f -Old $r.Old -New $r.New }
    }
}

# ============================================================
# PHASE 3 — Worktrees + junctions (move into Sanctum's worktrees/, then delete root junctions)
# ============================================================
if ($Phase -in @('3','all')) {
    Write-Host ""
    Write-Host "--- Phase 3: Sanctum-side worktrees + junction cleanup ---" -ForegroundColor Magenta
    $sanctumMoves = @(
        @{From='D:\rkoj-eve-picker-wt'; To="$SanctumRoot\worktrees\rkoj-eve-picker";    Why='RKOJ EVE picker worktree'}
        @{From='D:\eve-build-iter33';   To="$SanctumRoot\builds\eve-iter33";            Why='EVE.exe iter33 build artifact'}
    )
    foreach ($m in $sanctumMoves) { $null = Safe-Move @m }

    # Junctions at D:\ root that already target Sanctum-side paths — delete them
    Remove-JunctionSafely -Path 'D:\Sinister-Term-WT'
    Remove-JunctionSafely -Path 'D:\sinister-vault'

    # Update refs that pointed to junction paths
    $junctionRefs = @(
        @{Old='D:\sinister-vault';   New="$SanctumRoot\_vault"}
        @{Old='D:\\sinister-vault';  New=($SanctumRoot.Replace('\','\\') + '\\_vault')}
        @{Old='D:\Sinister-Term-WT'; New="$SanctumRoot\worktrees\sinister-term-wt"}
        @{Old='D:\\Sinister-Term-WT';New=($SanctumRoot.Replace('\','\\') + '\\worktrees\\sinister-term-wt')}
    )
    $refFiles3 = @(
        'D:\Sinister Sanctum\CLAUDE.md',
        'D:\Sinister Sanctum\automations\session-templates\projects.json',
        'D:\Sinister Sanctum\automations\session-templates\personal-projects.json'
    )
    foreach ($f in $refFiles3) {
        foreach ($r in $junctionRefs) { $null = Update-RefInFile -File $f -Old $r.Old -New $r.New }
    }
    Write-Host "  NOTE: 728+ source-code refs to 'sinister-vault' substrings remain. Audit via _shared-memory/audits/d-drive-path-refs-2026-05-21.json." -ForegroundColor Yellow
}

# ============================================================
# PHASE 4 — HIGH RISK: D:\Sinister\Sinister Skills\ + D:\Sinister\ rename
# ============================================================
if ($Phase -in @('4','all')) {
    Write-Host ""
    Write-Host "--- Phase 4: Sinister Skills + Sinister/ rename ---" -ForegroundColor Magenta
    Write-Host "  WARNING: this phase touches 566+ refs. Re-run reference-audit AFTER." -ForegroundColor Red
    $null = Safe-Move -From 'D:\Sinister\Sinister Skills' -To "$SanctumRoot\_sinister-skills" -Why 'skills hub (566 refs)'

    # Move remainder of D:\Sinister\ into D:\Personal\Sinister-folders\
    if (Test-Path 'D:\Sinister') {
        $remaining = Get-ChildItem 'D:\Sinister' -Force | Where-Object { $_.Name -notin @('Sinister Skills') }
        Log 'note' 'D:\Sinister' "remaining items after Skills move: $($remaining.Count) - moving to D:\Personal\Sinister-folders\"
        $null = Safe-Move -From 'D:\Sinister' -To 'D:\Personal\Sinister-folders' -Why 'personal hub residual'
    }

    # Ref updates for Sinister Skills paths
    $skillsRefs = @(
        @{Old='D:\Sinister\Sinister Skills';     New="$SanctumRoot\_sinister-skills"}
        @{Old='D:\\Sinister\\Sinister Skills';   New=($SanctumRoot.Replace('\','\\') + '\\_sinister-skills')}
    )
    $refFiles4 = @(
        'D:\Sinister Sanctum\CLAUDE.md'
    )
    foreach ($f in $refFiles4) {
        foreach ($r in $skillsRefs) { $null = Update-RefInFile -File $f -Old $r.Old -New $r.New }
    }
}

# ============================================================
# Triage: tmp/, d/, _shared-memory/ at root
# ============================================================
if ($Phase -in @('all')) {
    Write-Host ""
    Write-Host "--- Triage: tmp, d, _shared-memory at root ---" -ForegroundColor Magenta
    $null = Safe-Move -From 'D:\d'              -To 'D:\Backups\d-misnamed'           -Why 'misplaced Sanctum clone'
    $null = Safe-Move -From 'D:\_shared-memory' -To 'D:\Backups\_shared-memory-root'  -Why 'stale root copy'
    $null = Safe-Move -From 'D:\_backups'       -To 'D:\Backups\_backups-merged'      -Why 'consolidate'
    $null = Safe-Move -From 'D:\tmp'            -To "$SanctumRoot\tmp"                -Why 'scratch worktrees + freeze'
}

Write-Host ""
Write-Host "=== summary ===" -ForegroundColor Cyan
Write-Host "Actions logged: $($logRows.Count)"
if ($DryRun) {
    Write-Host 'DRY RUN — nothing changed. Re-run with -DryRun:$false to execute.' -ForegroundColor Yellow
} else {
    Write-Host 'EXECUTED. Verify with: Get-ChildItem D:\' -ForegroundColor Green
    Write-Host 'Next: re-run reference-audit at _shared-memory/audits/_scan-d-drive-refs.py' -ForegroundColor Green
}

# Save the log
$logDir = Join-Path $SanctumRoot '_shared-memory\plans\d-drive-reorg-2026-05-24'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir ("run-{0}-phase{1}-{2}.log" -f ((Get-Date).ToString('yyyyMMdd-HHmmss')), $Phase, $(if($DryRun){'dryrun'}else{'exec'}))
$logRows | Set-Content -LiteralPath $logFile -Encoding UTF8
Write-Host "Log: $logFile"
