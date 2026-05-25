# fleet-freeze-probe.ps1 :: measure causes of fleet "10-min freeze" symptom
# Author: RKOJ-ELENO :: 2026-05-24
#
# Doctrine: _shared-memory/knowledge/fleet-freeze-root-cause-2026-05-24.md
#
# What this measures:
#   1. ~/.claude/projects/ disk footprint (Claude Code transcript hot path).
#      Big footprint => Defender scan + compaction reload pressure.
#   2. Defender real-time scan state + whether .claude paths are excluded.
#   3. Top-N active session transcripts (size + age) - these are what
#      Claude Code touches every turn.
#   4. Scheduled-task cadences + overlap analysis (look for ~10-min clusters).
#   5. _shared-memory/ append-only file size leaderboard (lock-contention risk).
#
# Usage: just run it. No side effects, no destructive ops.
#
# Exit codes:
#   0 = probe completed successfully
#   1 = probe completed but found issues that need operator action
#   2 = unexpected error

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$TopN = 5
)

$ErrorActionPreference = 'Continue'
$ProjectsDir = Join-Path $env:USERPROFILE '.claude\projects'
$FileHistoryDir = Join-Path $env:USERPROFILE '.claude\file-history'

$issues = 0

function Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 64) -ForegroundColor DarkMagenta
    Write-Host "  $Title" -ForegroundColor Magenta
    Write-Host ("=" * 64) -ForegroundColor DarkMagenta
}

function Note([string]$Msg, [string]$Color = 'White') {
    Write-Host "  $Msg" -ForegroundColor $Color
}

function Warn([string]$Msg) {
    Write-Host "  [WARN] $Msg" -ForegroundColor Yellow
    $script:issues++
}

function Bad([string]$Msg) {
    Write-Host "  [ISSUE] $Msg" -ForegroundColor Red
    $script:issues++
}

# ---------------------------------------------------------------
Section "1. Claude Code transcript footprint (~/.claude/projects)"
# ---------------------------------------------------------------

if (-not (Test-Path $ProjectsDir)) {
    Note "Projects dir not found: $ProjectsDir"
} else {
    $allJsonl = Get-ChildItem -Path $ProjectsDir -Recurse -Filter '*.jsonl' -File -ErrorAction SilentlyContinue
    $totalMB = [math]::Round((($allJsonl | Measure-Object Length -Sum).Sum / 1MB), 2)
    $totalCount = $allJsonl.Count
    Note ("Total transcripts: {0} files, {1} MB" -f $totalCount, $totalMB)
    if ($totalMB -gt 1000) { Bad "Transcript pool >1 GB - prune with automations/prune-claude-transcripts.ps1" }
    elseif ($totalMB -gt 500) { Warn "Transcript pool >500 MB - consider pruning" }

    Note ""
    Note ("Top {0} project folders by size:" -f $TopN)
    Get-ChildItem -Path $ProjectsDir -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $sz = (Get-ChildItem -Path $_.FullName -Filter '*.jsonl' -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
        [PSCustomObject]@{ Name = $_.Name; SizeMB = [math]::Round($sz/1MB, 2) }
    } | Sort-Object SizeMB -Descending | Select-Object -First $TopN | ForEach-Object {
        Note ("  {0,8:N2} MB  {1}" -f $_.SizeMB, $_.Name)
    }
}

# ---------------------------------------------------------------
Section "2. Defender real-time scan state"
# ---------------------------------------------------------------

try {
    $mp = Get-MpComputerStatus -ErrorAction Stop
    Note ("RealTimeProtectionEnabled : {0}" -f $mp.RealTimeProtectionEnabled)
    Note ("BehaviorMonitorEnabled    : {0}" -f $mp.BehaviorMonitorEnabled)
    Note ("IoavProtectionEnabled     : {0}" -f $mp.IoavProtectionEnabled)
    if ($mp.RealTimeProtectionEnabled) {
        try {
            $prefs = Get-MpPreference -ErrorAction Stop
            $excluded = $prefs.ExclusionPath
            $claudeExcluded = $false
            foreach ($ep in $excluded) {
                if ($ep -and $ep -match '\.claude') { $claudeExcluded = $true; break }
            }
            if ($claudeExcluded) {
                Note "  ~/.claude paths ARE excluded - Defender will not scan transcripts" 'Green'
            } else {
                Warn "~/.claude paths are NOT excluded - Defender scans every transcript append"
                Note ""
                Note "  Fix (Administrator PowerShell, one-time):" 'Yellow'
                Note "    Add-MpPreference -ExclusionPath `"`$env:USERPROFILE\.claude\projects`"" 'Yellow'
                Note "    Add-MpPreference -ExclusionPath `"`$env:USERPROFILE\.claude\file-history`"" 'Yellow'
                Note "    Add-MpPreference -ExclusionProcess `"claude.exe`"" 'Yellow'
            }
        } catch {
            Warn "Could not read Defender exclusions (need admin): $($_.Exception.Message)"
        }
    }
} catch {
    Note "Defender status unavailable: $($_.Exception.Message)"
}

# ---------------------------------------------------------------
Section "3. Hot transcripts (modified in last 24h, by size)"
# ---------------------------------------------------------------

if (Test-Path $ProjectsDir) {
    $cutoff = (Get-Date).AddDays(-1)
    $hot = Get-ChildItem -Path $ProjectsDir -Recurse -Filter '*.jsonl' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -gt $cutoff } |
        Sort-Object Length -Descending |
        Select-Object -First $TopN
    if ($hot.Count -eq 0) {
        Note "No active sessions (no .jsonl modified in last 24h)"
    } else {
        foreach ($f in $hot) {
            $mb = [math]::Round($f.Length / 1MB, 2)
            $ageMin = [int]((Get-Date) - $f.LastWriteTime).TotalMinutes
            Note ("  {0,7:N2} MB  age={1,4}m  {2}" -f $mb, $ageMin, $f.Name)
            if ($mb -gt 20) { Warn "Active transcript >20 MB - auto-compaction will hit hard here" }
        }
    }
}

# ---------------------------------------------------------------
Section "4. Scheduled tasks (look for ~10-min cadence)"
# ---------------------------------------------------------------

try {
    $tasks = Get-ScheduledTask -ErrorAction SilentlyContinue |
        Where-Object { $_.TaskName -match 'Sinister|Sanctum|RKOJ|Vault|AutoPush|APK|Custodian|fleet-monitor' }
    foreach ($t in $tasks) {
        $trigs = @()
        foreach ($trg in $t.Triggers) {
            $intv = $trg.Repetition.Interval
            $kind = $trg.CimClass.CimClassName -replace 'MSFT_Task',''
            $trigs += ("{0}={1}" -f $kind, $intv)
        }
        $line = "{0,-32} | {1,-10} | {2}" -f $t.TaskName, $t.State, ($trigs -join '; ')
        Note $line
    }
    $tenMin = $tasks | Where-Object { ($_.Triggers | ForEach-Object { $_.Repetition.Interval }) -contains 'PT10M' }
    if ($tenMin) { Warn ("Found PT10M task(s): {0}" -f ($tenMin.TaskName -join ', ')) }
    else { Note "  -> No PT10M-cadence task exists (10-min freeze is NOT from a scheduled task)" 'Green' }
} catch {
    Note "Could not enumerate scheduled tasks: $($_.Exception.Message)"
}

# ---------------------------------------------------------------
Section "5. _shared-memory/ append-only file leaderboard"
# ---------------------------------------------------------------

$sharedMem = Join-Path $SanctumRoot '_shared-memory'
if (Test-Path $sharedMem) {
    $appendOnly = Get-ChildItem -Path $sharedMem -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.jsonl', '.log' } |
        Sort-Object Length -Descending |
        Select-Object -First $TopN
    foreach ($f in $appendOnly) {
        $mb = [math]::Round($f.Length / 1MB, 2)
        $rel = $f.FullName.Substring($SanctumRoot.Length).TrimStart('\','/')
        Note ("  {0,7:N2} MB  {1}" -f $mb, $rel)
        if ($mb -gt 2) { Warn "Append-only file >2 MB ($rel) - consider rotation" }
    }
}

# ---------------------------------------------------------------
Section "Summary"
# ---------------------------------------------------------------

if ($issues -eq 0) {
    Note "No issues found." 'Green'
    exit 0
} else {
    Note ("{0} issue(s) flagged. See [ISSUE]/[WARN] rows above." -f $issues) 'Yellow'
    exit 1
}
