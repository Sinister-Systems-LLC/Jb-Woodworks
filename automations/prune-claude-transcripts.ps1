# prune-claude-transcripts.ps1 :: archive old ~/.claude/projects transcripts
# Author: RKOJ-ELENO :: 2026-05-24
#
# Doctrine: _shared-memory/knowledge/fleet-freeze-root-cause-2026-05-24.md
#
# Why: ~/.claude/projects accumulates ALL session transcripts (no built-in rotation).
# At 3 GB / 319 files in one subfolder, Defender real-time scan + Claude Code's
# own context-compaction reload dramatically slow down. Old transcripts are
# never touched mid-session - only on `claude --resume <session-id>`.
#
# Action: move transcripts older than $DaysToKeep to ~/.claude/projects-archive/.
# Archive path is OUTSIDE the hot path Claude Code touches every turn, so it
# won't suffer Defender scan pressure during active sessions, but resume still
# works if you symlink or manually copy back.
#
# Default: keep last 14 days. Safe to re-run.

[CmdletBinding()]
param(
    [int]$DaysToKeep = 14,
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
$ProjectsDir = Join-Path $env:USERPROFILE '.claude\projects'
$ArchiveDir = Join-Path $env:USERPROFILE '.claude\projects-archive'

if (-not (Test-Path $ProjectsDir)) {
    Write-Host "Projects dir not found: $ProjectsDir" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $ArchiveDir)) {
    if (-not $DryRun) { New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null }
    Write-Host ("Created archive dir: {0}" -f $ArchiveDir)
}

$cutoff = (Get-Date).AddDays(-$DaysToKeep)
Write-Host ("Archiving transcripts older than {0:yyyy-MM-dd} ({1} days)..." -f $cutoff, $DaysToKeep)

$movedCount = 0
$movedMB = 0.0

Get-ChildItem -Path $ProjectsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $projDir = $_
    $relName = $projDir.Name
    $oldFiles = Get-ChildItem -Path $projDir.FullName -Filter '*.jsonl' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff }

    if ($oldFiles.Count -eq 0) { return }

    $destDir = Join-Path $ArchiveDir $relName
    if (-not (Test-Path $destDir)) {
        if (-not $DryRun) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    }

    foreach ($f in $oldFiles) {
        $destPath = Join-Path $destDir $f.Name
        if (Test-Path $destPath) {
            if (-not $DryRun) { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue }
        } else {
            if ($DryRun) {
                Write-Host ("  [DRY] would move {0,7:N2} MB  {1}/{2}" -f ($f.Length/1MB), $relName, $f.Name) -ForegroundColor DarkGray
            } else {
                try {
                    Move-Item -LiteralPath $f.FullName -Destination $destPath -Force -ErrorAction Stop
                } catch {
                    Write-Host ("  [SKIP] {0} : {1}" -f $f.Name, $_.Exception.Message) -ForegroundColor Yellow
                    continue
                }
            }
        }
        $movedCount++
        $movedMB += ($f.Length / 1MB)
    }
}

$prefix = if ($DryRun) { "[DRY-RUN] would archive" } else { "Archived" }
Write-Host ""
Write-Host ("{0}: {1} file(s), {2:N2} MB" -f $prefix, $movedCount, $movedMB) -ForegroundColor Green
Write-Host ("Hot path remaining at: {0}" -f $ProjectsDir)
Write-Host ("Archive at:           {0}" -f $ArchiveDir)

exit 0
