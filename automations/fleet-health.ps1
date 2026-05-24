# fleet-health.ps1 — one-command full-fleet health snapshot.
# Author: RKOJ-ELENO :: 2026-05-24 (iter-10)
#
# Aggregates the smaller probes/checks into a single human-skimmable report:
#   - canonical-protections-check (P1-P13)
#   - jcode-parity-probe (31 rows)
#   - claude-accounts (rotation state)
#   - lane-plan tally (cross-lane todo/done counts)
#   - heartbeat freshness per lane (stale-detection)
#   - sibling-git-contention level (open git processes)
#
# Exit 0 if all healthy; exit N where N = count of subsystems flagged.
#
# Usage:
#   powershell -File fleet-health.ps1                    # full report
#   powershell -File fleet-health.ps1 -Quiet             # summary-line only
#   powershell -File fleet-health.ps1 -StaleMinutes 30   # tune heartbeat staleness threshold

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$StaleMinutes = 30,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$subsystems = @()

function Add-Subsystem {
    param([string]$Name, [bool]$Ok, [string]$Detail)
    $script:subsystems += [PSCustomObject]@{
        name = $Name
        ok = $Ok
        detail = $Detail
    }
}

function Get-FirstLineMatch {
    param([string[]]$Lines, [string]$Pattern)
    $hit = $Lines | Select-String $Pattern | Select-Object -First 1
    if ($hit) { return $hit.Line.Trim() }
    return '(no summary line found)'
}

# 1. canonical-protections
$cp = & "$SanctumRoot\automations\canonical-protections-check.ps1" 2>&1
$cpExit = $LASTEXITCODE
$cpLine = Get-FirstLineMatch -Lines $cp -Pattern 'canonical-protections-check ::'
Add-Subsystem 'canonical-protections' ($cpExit -eq 0) $cpLine

# 2. jcode-parity-probe
$pp = & "$SanctumRoot\automations\jcode-parity-probe.ps1" 2>&1
$ppExit = $LASTEXITCODE
$ppLine = Get-FirstLineMatch -Lines $pp -Pattern 'jcode-parity-probe ::'
Add-Subsystem 'jcode-parity-probe' ($ppExit -eq 0) $ppLine

# 3. claude-accounts rotation
$acctLib = "$SanctumRoot\automations\claude-accounts.ps1"
$enCnt = 0; $totalCnt = 0; $rlCnt = 0
if (Test-Path $acctLib) {
    . $acctLib
    $cfg = Get-AccountsConfig
    $totalCnt = @($cfg.accounts).Count
    $enCnt = @($cfg.accounts | Where-Object { $_.enabled -ne $false }).Count
    $rlCnt = @($cfg.accounts | Where-Object { $_.rate_limited_until_utc }).Count
}
$acctOk = ($enCnt -ge 1) -and ($rlCnt -lt $enCnt)
Add-Subsystem 'claude-accounts' $acctOk "$enCnt/$totalCnt enabled | $rlCnt rate-limited"

# 4. lane-plan cross-fleet tally
$planDir = "$SanctumRoot\_shared-memory\lane-plans"
$todo = 0; $inprog = 0; $done = 0; $laneCount = 0
if (Test-Path $planDir) {
    $files = Get-ChildItem $planDir -Filter '*.md' -ErrorAction SilentlyContinue
    $laneCount = $files.Count
    foreach ($f in $files) {
        $cur = ''
        Get-Content $f.FullName | ForEach-Object {
            if ($_ -match '^## (TODO|IN-PROGRESS|DONE)$') { $cur = $Matches[1] }
            elseif ($_ -match '^- \[') {
                switch ($cur) { 'TODO' { $todo++ } 'IN-PROGRESS' { $inprog++ } 'DONE' { $done++ } }
            }
        }
    }
}
Add-Subsystem 'lane-plans' $true "$laneCount lanes | todo=$todo | in-progress=$inprog | done=$done"

# 5. heartbeat freshness
$hbDir = "$SanctumRoot\_shared-memory\heartbeats"
$cutoff = (Get-Date).ToUniversalTime().AddMinutes(-$StaleMinutes)
$fresh = 0; $stale = 0; $staleList = @()
if (Test-Path $hbDir) {
    $hbs = Get-ChildItem $hbDir -Filter '*.json' -ErrorAction SilentlyContinue
    foreach ($f in $hbs) {
        $slug = $f.BaseName
        if ($slug -match '\.beat$|^phones|^diagnose$|^general$|^inventions$|^sanctum-[0-9a-f]{6}$') { continue }
        try {
            $hb = Get-Content $f.FullName -Raw | ConvertFrom-Json
            $hbTs = if ($hb.ts_utc) { [datetime]::Parse($hb.ts_utc).ToUniversalTime() } else { $f.LastWriteTimeUtc }
            if ($hbTs -ge $cutoff) { $fresh++ } else { $stale++; $staleList += $slug }
        } catch {
            $stale++; $staleList += "$slug (parse-err)"
        }
    }
}
Add-Subsystem 'heartbeats' ($stale -eq 0 -or $stale -le 5) "fresh=$fresh | stale($StaleMinutes min)=$stale"

# 6. git contention (open git.exe processes)
$gitProcs = @(Get-Process git -ErrorAction SilentlyContinue).Count
$gitLockPresent = Test-Path "$SanctumRoot\.git\index.lock"
$gitOk = ($gitProcs -lt 5) -and (-not $gitLockPresent)
$gitDetail = "git.exe procs=$gitProcs | index.lock=$gitLockPresent"
Add-Subsystem 'git-contention' $gitOk $gitDetail

# Report
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$okCount = @($subsystems | Where-Object { $_.ok }).Count
$failCount = @($subsystems | Where-Object { -not $_.ok }).Count

if ($Quiet) {
    Write-Output "[$ts] fleet-health :: OK=$okCount FAIL=$failCount / $($subsystems.Count)"
} else {
    Write-Output ""
    Write-Output "  ===== FLEET HEALTH SNAPSHOT @ $ts ====="
    Write-Output ""
    foreach ($s in $subsystems) {
        $tag = $(if ($s.ok) { '[OK]    ' } else { '[ALERT] ' })
        Write-Output ("  $tag {0,-22} {1}" -f $s.name, $s.detail)
    }
    Write-Output ""
    Write-Output ("  Summary: OK=$okCount FAIL=$failCount / $($subsystems.Count)")
    if ($staleList.Count -gt 0 -and $staleList.Count -le 10) {
        Write-Output "  Stale lanes: $($staleList -join ', ')"
    } elseif ($staleList.Count -gt 10) {
        Write-Output "  Stale lanes ($($staleList.Count) total, showing first 10): $(($staleList | Select-Object -First 10) -join ', ')"
    }
    Write-Output ""
}

exit $failCount
