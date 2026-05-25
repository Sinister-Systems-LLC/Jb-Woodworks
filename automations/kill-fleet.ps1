# kill-fleet.ps1 :: tiered force-close for EVE.exe + mintty + claude.exe spawned by the launcher.
#
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator (verbatim 2026-05-24T22:10Z):
#     "same time this happens is when i cannoot close eve exe. it wont close"
#
# Three modes (default Hard). All modes honor -WhatIf for dry-run safety.
#
#   -Mode Soft     : send WM_CLOSE to EVE.exe + mintty windows (graceful 3s grace
#                    period). Useful when the operator wants a polite exit first.
#   -Mode Hard     : Stop-Process -Force on EVE.exe + all mintty.exe + every
#                    claude.exe whose parent chain points back to the launcher
#                    (filter via spawned-windows.jsonl launcher_pid). Operator's
#                    other Claude windows (master Sanctum agent, RKOJ) are
#                    preserved by this filter.
#   -Mode Nuclear  : Hard + clean stale .lock files + truncate launcher logs
#                    that exceed 50 MB (corrupt-tail recovery).
#
# Smoke green path:
#   powershell -File automations/kill-fleet.ps1 -Mode Soft -WhatIf
#       => lists targets, kills nothing
#   powershell -File automations/kill-fleet.ps1 -Mode Hard
#       => stops EVE/mintty/launcher-spawned claudes
#
# Composes with:
#   automations/start-sinister-session.ps1   - emits spawned-windows.jsonl rows
#   _shared-memory/spawned-windows.jsonl     - source-of-truth for launcher PIDs
#   tools/eve-picker/main_menu.py            - K-key shortcut wired in main menu

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet('Soft', 'Hard', 'Nuclear')]
    [string]$Mode = 'Hard',

    # Optional: only kill processes spawned by THIS launcher PID (defaults to all).
    [int]$LauncherPid = 0,

    # Override the sanctum root (defaults to env or D:\Sinister Sanctum).
    [string]$SanctumRoot = $(if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }),

    # Grace period (seconds) for Soft mode.
    [int]$GraceSeconds = 3
)

$ErrorActionPreference = 'Continue'
$script:KilledCount = 0
$script:SkippedCount = 0

function Write-Step($msg, $color = 'White') {
    Write-Host "  [kill-fleet] $msg" -ForegroundColor $color
}

# ---------------------------------------------------------------------------
# 1. Resolve launcher PIDs from spawned-windows.jsonl
# ---------------------------------------------------------------------------

function Get-LauncherPidSet {
    $jsonlPath = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
    $launcherPids = New-Object System.Collections.Generic.HashSet[int]
    $spawnedPids = New-Object System.Collections.Generic.HashSet[int]

    if (-not (Test-Path $jsonlPath)) {
        Write-Step "spawned-windows.jsonl missing at $jsonlPath - will kill ALL claude/mintty/EVE in scope" Yellow
        return @{ LauncherPids = $launcherPids; SpawnedPids = $spawnedPids; HasManifest = $false }
    }

    # Read the JSONL; skip rows where closed_at_utc is set (already dead).
    Get-Content $jsonlPath -ErrorAction SilentlyContinue | ForEach-Object {
        $line = $_.Trim()
        if (-not $line) { return }
        try {
            $obj = $line | ConvertFrom-Json -ErrorAction Stop
        } catch {
            return
        }
        if ($obj.closed_at_utc) { return }
        if ($obj.launcher_pid -and $obj.launcher_pid -gt 0) {
            [void]$launcherPids.Add([int]$obj.launcher_pid)
        }
        if ($obj.pid -and $obj.pid -gt 0) {
            [void]$spawnedPids.Add([int]$obj.pid)
        }
    }

    return @{ LauncherPids = $launcherPids; SpawnedPids = $spawnedPids; HasManifest = $true }
}

# ---------------------------------------------------------------------------
# 2. Collect target processes
# ---------------------------------------------------------------------------

function Get-TargetProcesses {
    param([hashtable]$Manifest)

    $targets = @()

    # EVE.exe — always a target regardless of parentage.
    $eveProcs = Get-Process -Name 'EVE' -ErrorAction SilentlyContinue
    foreach ($p in $eveProcs) {
        $targets += [pscustomobject]@{
            Process = $p; Name = $p.ProcessName; Pid = $p.Id
            Reason = 'EVE.exe (always-target)'
        }
    }

    # mintty.exe — terminal hosts. If we have a manifest, prefer matching by PID.
    $minttyProcs = Get-Process -Name 'mintty' -ErrorAction SilentlyContinue
    foreach ($p in $minttyProcs) {
        $matched = $false
        if ($Manifest.HasManifest -and $Manifest.SpawnedPids.Count -gt 0) {
            # mintty's PID isn't directly in spawned-windows (claude is), but
            # parent-chain match works: if our LauncherPid filter is set, only
            # kill mintty whose grand-parent is the launcher.
            if ($LauncherPid -gt 0) {
                $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue
                if ($owner -and ($owner.ParentProcessId -eq $LauncherPid -or $Manifest.LauncherPids.Contains([int]$owner.ParentProcessId))) {
                    $matched = $true
                }
            } else {
                # No specific launcher filter - mintty is fair game in fleet-kill mode.
                $matched = $true
            }
        } else {
            $matched = $true  # no manifest, fall back to all-mintty kill
        }
        if ($matched) {
            $targets += [pscustomobject]@{
                Process = $p; Name = $p.ProcessName; Pid = $p.Id
                Reason = 'mintty.exe (launcher-spawned)'
            }
        } else {
            $script:SkippedCount++
        }
    }

    # claude.exe — only those listed in spawned-windows.jsonl (preserves
    # operator's master Sanctum agent + RKOJ-side Claude sessions).
    $claudeProcs = Get-Process -Name 'claude' -ErrorAction SilentlyContinue
    foreach ($p in $claudeProcs) {
        $isLauncherSpawned = $false
        if ($Manifest.HasManifest -and $Manifest.SpawnedPids.Contains([int]$p.Id)) {
            $isLauncherSpawned = $true
        }
        # LauncherPid filter overrides manifest membership
        if ($LauncherPid -gt 0) {
            $owner = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue
            if ($owner -and ($owner.ParentProcessId -eq $LauncherPid)) {
                $isLauncherSpawned = $true
            } else {
                $isLauncherSpawned = $false
            }
        }
        if ($isLauncherSpawned) {
            $targets += [pscustomobject]@{
                Process = $p; Name = $p.ProcessName; Pid = $p.Id
                Reason = 'claude.exe (launcher-spawned via manifest)'
            }
        } else {
            $script:SkippedCount++
        }
    }

    return $targets
}

# ---------------------------------------------------------------------------
# 3. Soft close (WM_CLOSE)
# ---------------------------------------------------------------------------

function Send-SoftClose {
    param($Targets)

    foreach ($t in $Targets) {
        if ($PSCmdlet.ShouldProcess("$($t.Name) PID=$($t.Pid)", "WM_CLOSE")) {
            try {
                $t.Process.CloseMainWindow() | Out-Null
                Write-Step "WM_CLOSE -> $($t.Name) PID=$($t.Pid) ($($t.Reason))" Cyan
            } catch {
                Write-Step "CloseMainWindow failed for $($t.Name) PID=$($t.Pid): $_" Yellow
            }
        }
    }

    if ($Targets.Count -gt 0 -and -not $WhatIfPreference) {
        Write-Step "waiting ${GraceSeconds}s for graceful exit..." Gray
        Start-Sleep -Seconds $GraceSeconds
        # Report survivors
        $survivors = $Targets | Where-Object { -not $_.Process.HasExited }
        foreach ($s in $survivors) {
            Write-Step "still alive after grace: $($s.Name) PID=$($s.Pid)" Yellow
        }
        $script:KilledCount = $Targets.Count - $survivors.Count
    }
}

# ---------------------------------------------------------------------------
# 4. Hard kill
# ---------------------------------------------------------------------------

function Send-HardKill {
    param($Targets)

    foreach ($t in $Targets) {
        if ($PSCmdlet.ShouldProcess("$($t.Name) PID=$($t.Pid)", "Stop-Process -Force")) {
            try {
                Stop-Process -Id $t.Pid -Force -ErrorAction Stop
                Write-Step "killed $($t.Name) PID=$($t.Pid) ($($t.Reason))" Green
                $script:KilledCount++
            } catch {
                Write-Step "kill failed $($t.Name) PID=$($t.Pid): $_" Red
            }
        }
    }
}

# ---------------------------------------------------------------------------
# 5. Nuclear cleanup
# ---------------------------------------------------------------------------

function Invoke-NuclearCleanup {
    # Stale lock files
    $lockGlobs = @(
        (Join-Path $SanctumRoot '_shared-memory\.spawned-windows.lock'),
        (Join-Path $SanctumRoot '_shared-memory\*.lock'),
        (Join-Path $SanctumRoot 'automations\session-templates\*.lock')
    )
    foreach ($g in $lockGlobs) {
        Get-ChildItem -Path $g -ErrorAction SilentlyContinue | ForEach-Object {
            if ($PSCmdlet.ShouldProcess($_.FullName, 'Remove stale lock')) {
                try {
                    Remove-Item $_.FullName -Force -ErrorAction Stop
                    Write-Step "removed stale lock: $($_.Name)" Magenta
                } catch {
                    Write-Step "could not remove lock $($_.Name): $_" Yellow
                }
            }
        }
    }

    # Truncate oversized launcher logs (> 50 MB)
    $logDir = Join-Path $SanctumRoot '_shared-memory\session-logs'
    if (Test-Path $logDir) {
        Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 50MB } | ForEach-Object {
            if ($PSCmdlet.ShouldProcess($_.FullName, "Truncate (> 50 MB)")) {
                try {
                    Set-Content -Path $_.FullName -Value "[truncated by kill-fleet.ps1 Nuclear @ $(Get-Date -Format 'o')]`n" -Encoding UTF8
                    Write-Step "truncated oversized log: $($_.Name)" Magenta
                } catch {
                    Write-Step "could not truncate $($_.Name): $_" Yellow
                }
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Write-Step ("Mode={0}  WhatIf={1}  LauncherPid={2}" -f $Mode, $WhatIfPreference, $LauncherPid) Cyan

$manifest = Get-LauncherPidSet
Write-Step ("manifest rows: launchers={0} spawned-claude={1}" -f $manifest.LauncherPids.Count, $manifest.SpawnedPids.Count) Gray

$targets = Get-TargetProcesses -Manifest $manifest
Write-Step ("targets={0}  skipped(operator-owned)={1}" -f $targets.Count, $script:SkippedCount) Cyan

if ($targets.Count -eq 0) {
    Write-Step "nothing to kill; already clean." Green
    if ($Mode -eq 'Nuclear') { Invoke-NuclearCleanup }
    exit 0
}

# Show targets table even in WhatIf for operator visibility
$targets | Select-Object Name, Pid, Reason | Format-Table -AutoSize | Out-String | Write-Host

switch ($Mode) {
    'Soft' {
        Send-SoftClose -Targets $targets
    }
    'Hard' {
        Send-HardKill -Targets $targets
    }
    'Nuclear' {
        Send-HardKill -Targets $targets
        Invoke-NuclearCleanup
    }
}

Write-Step ("done. killed={0} skipped={1}" -f $script:KilledCount, $script:SkippedCount) Green
exit 0
