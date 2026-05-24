# forever-improve.ps1 - fleet-wide forever-improve review pass
# Author: RKOJ-ELENO :: 2026-05-24
#
# Composes with: forever-improve-review-doctrine-2026-05-24.md
#                no-bullshit-tested-before-claimed-doctrine-2026-05-23.md (rule 5 + rule 8)
#                loop-quality-gate.ps1 (sibling; produces stop-signals where this produces suggestions)
#
# Usage:
#   powershell -File forever-improve.ps1 -Action Review       -Target <path>          [-Lane sanctum]
#   powershell -File forever-improve.ps1 -Action ReviewCommit -Sha <hash>             [-Lane sanctum]
#   powershell -File forever-improve.ps1 -Action Tally                                [-Lane <slug>]
#   powershell -File forever-improve.ps1 -Action Drain                                [-MaxTurns 3]
#
# Appends to D:\Sinister Sanctum\_shared-memory\improvement-log.jsonl with lock-based concurrent writes.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Review','ReviewCommit','Tally','Drain')]
    [string]$Action,

    [string]$Target = '',
    [string]$Sha = '',
    [string]$Lane = 'sanctum',
    [int]$MaxTurns = 3,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$LogPath  = Join-Path $SanctumRoot '_shared-memory\improvement-log.jsonl'
$LockPath = Join-Path $SanctumRoot 'automations\improvement-log.lock'

function Acquire-Lock {
    param([string]$Path, [int]$TimeoutSec = 10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            Start-Sleep -Milliseconds 100
        }
    }
}

function Release-Lock {
    param([string]$Path)
    if (Test-Path $Path) { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue }
}

function Append-Row {
    param([hashtable]$Row)
    $logDir = Split-Path $LogPath -Parent
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) {
        Write-Error "Could not acquire lock at $LockPath after 10s"
        return $false
    }
    try {
        $json = $Row | ConvertTo-Json -Compress -Depth 10
        $sw = [System.IO.StreamWriter]::new($LogPath, $true, [System.Text.UTF8Encoding]::new($false))
        $sw.WriteLine($json)
        $sw.Close()
        return $true
    } finally {
        Release-Lock -Path $LockPath
    }
}

function Read-Log {
    if (-not (Test-Path $LogPath)) { return @() }
    $lines = Get-Content -LiteralPath $LogPath -Encoding UTF8 | Where-Object { $_ -and $_.Trim() }
    $rows = @()
    foreach ($l in $lines) {
        try { $rows += (ConvertFrom-Json $l) } catch { }
    }
    return $rows
}

function Get-TargetType {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 'unknown' }
    if ((Get-Item $Path).PSIsContainer) { return 'directory' }
    switch -Regex ($Path) {
        '\.md$'          { return 'doctrine' }
        '\.ps1$'         { return 'script-ps1' }
        '\.py$'          { return 'script-py' }
        '\.(sh|bat)$'    { return 'script-shell' }
        '\.(ts|tsx|js|jsx)$' { return 'script-js' }
        '\.json$'        { return 'config' }
        default          { return 'file' }
    }
}

# ----- Review pass: 5-question structured pass on a target file -----
function Invoke-Review {
    param([string]$TargetPath, [string]$LaneSlug, [string]$Context = '')

    if (-not (Test-Path $TargetPath)) {
        Write-Error "Target not found: $TargetPath"
        return
    }

    $resolved = (Resolve-Path -LiteralPath $TargetPath).Path
    $rel = $resolved
    if ($resolved.StartsWith($SanctumRoot, [StringComparison]::OrdinalIgnoreCase)) {
        $rel = $resolved.Substring($SanctumRoot.Length).TrimStart('\','/')
    }
    $targetType = Get-TargetType -Path $resolved

    $isDir = (Get-Item $resolved).PSIsContainer
    $content = ''
    $lineCount = 0
    if (-not $isDir) {
        try {
            $content = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 -ErrorAction Stop
            $lineCount = ($content -split "`n").Count
        } catch { $content = '' }
    }

    $findings = @()

    # Q1 - completeness: TODO / FIXME / XXX / stub / placeholder
    if (-not $isDir -and $content) {
        $todoMatches = [regex]::Matches($content, '(?i)\b(TODO|FIXME|XXX|HACK|stub|placeholder|not[\s\-]?yet[\s\-]?implemented)\b')
        if ($todoMatches.Count -gt 0) {
            $sample = ($todoMatches | Select-Object -First 3 | ForEach-Object { $_.Value }) -join ', '
            $sev = if ($todoMatches.Count -ge 5) { 'major' } else { 'minor' }
            $findings += @{ severity=$sev; area='Q1-completeness'; suggestion="Resolve $($todoMatches.Count) TODO/FIXME/stub markers (e.g. $sample) before marking shipped." }
        }
    }

    # Q2 - consistency: heuristic - Author line + sanctum-doctrine slug-format for .md
    if ($targetType -eq 'doctrine') {
        if ($content -notmatch '(?i)Author:\*?\*?\s*RKOJ-ELENO') {
            $findings += @{ severity='major'; area='Q2-consistency'; suggestion='Add an `Author: RKOJ-ELENO :: <date>` header (canonical 2026-05-21 authorship rule).' }
        }
        if ($content -notmatch '(?im)^##\s+(Status|TL;DR)') {
            $findings += @{ severity='minor'; area='Q2-consistency'; suggestion='Add a `## Status` or `## TL;DR` section to match other doctrines in `_shared-memory/knowledge/`.' }
        }
        if ($content -notmatch '(?i)(composes with|cross.reference|see also|related doctrine)') {
            $findings += @{ severity='minor'; area='Q2-consistency'; suggestion='Add a `Composes with:` / `See also:` section linking related doctrines so the brain stays interconnected.' }
        }
        if ($content -notmatch '(?i)\bUpdated:\s*202[5-6]-\d{2}-\d{2}\b') {
            $findings += @{ severity='minor'; area='Q2-consistency'; suggestion='Add an `Updated: YYYY-MM-DD` line (rule 5 of no-bullshit doctrine: every meaningful refactor bumps the date).' }
        }
        if ($content -notmatch '(?i)\b(anti-pattern|never|do not|avoid)\b') {
            $findings += @{ severity='minor'; area='Q2-consistency'; suggestion='Document anti-patterns / NEVERs so future agents know the failure modes, not just the success path.' }
        }
    }
    if ($targetType -like 'script-*') {
        if ($content -notmatch '(?im)Author:\s*RKOJ-ELENO') {
            $findings += @{ severity='major'; area='Q2-consistency'; suggestion='Add `Author: RKOJ-ELENO :: <date>` header line (canonical 2026-05-21 authorship rule).' }
        }
    }

    # Q3 - simplicity: line-count signals (rule 7 of no-bullshit: scripts >1500 lines need split)
    if (-not $isDir -and $lineCount -gt 0) {
        if ($targetType -like 'script-*' -and $lineCount -gt 1500) {
            $findings += @{ severity='major'; area='Q3-simplicity'; suggestion="Script is $lineCount lines (>1500 limit per rule 7 of no-bullshit doctrine). Refactor into focused modules." }
        } elseif ($targetType -like 'script-*' -and $lineCount -gt 800) {
            $findings += @{ severity='minor'; area='Q3-simplicity'; suggestion="Script is $lineCount lines; approaching 1500-line consolidation threshold. Consider extracting helper module." }
        }
        if ($targetType -eq 'doctrine' -and $lineCount -gt 300) {
            $findings += @{ severity='minor'; area='Q3-simplicity'; suggestion="Doctrine is $lineCount lines. Consider splitting into focused sub-doctrines (rule 8 of no-bullshit doctrine signals doctrine bloat)." }
        }
    }

    # Q4 - verifiability: presence of smoke-test reference / acceptance criterion
    if (-not $isDir -and $content) {
        $hasSmokePattern = ($content -match '(?i)(smoke[\s\-]?test|acceptance[\s\-]?test|verified|exit[\s\-]?code|Pester|pytest|self[\s\-]?test|--test\b)')
        if (-not $hasSmokePattern) {
            $sev = if ($targetType -like 'script-*') { 'major' } else { 'minor' }
            $findings += @{ severity=$sev; area='Q4-verifiability'; suggestion='No smoke-test / acceptance-criterion reference found. Add an inline `# smoke:` comment or a sibling `.test.ps1` / `_test.py` file.' }
        }
        # Q4b: docs/.md should reference a concrete pass-criterion or measurable outcome
        if ($targetType -eq 'doctrine') {
            $hasMeasurable = ($content -match '(?i)(measured|exit code|PASS=|verified|asserted|criterion|<\s*\d+\s*(ms|s|kb|mb))')
            if (-not $hasMeasurable) {
                $findings += @{ severity='minor'; area='Q4-verifiability'; suggestion='Doc has no measurable pass-criterion (`measured`, `PASS=N`, `<X ms`, etc). Add one so the next agent can confirm the doc still holds.' }
            }
        }
    }

    # Q5 also acts as a heuristic: warn if doc is large but has no Table-of-Contents anchor
    if ($targetType -eq 'doctrine' -and $lineCount -gt 150) {
        if ($content -notmatch '(?im)^\s*-\s*\[.*\]\(#') {
            $findings += @{ severity='minor'; area='Q5-navigability'; suggestion="Doc is $lineCount lines but has no in-page anchor links. Add a short table-of-contents at the top for fast jump-to-section." }
        }
    }

    # Q5 - next improvement increment (always emit; concrete + scoped)
    $nextAction = ''
    if ($findings.Count -gt 0) {
        $top = $findings | Sort-Object @{Expression={ if ($_.severity -eq 'major') {0} else {1} }} | Select-Object -First 1
        $nextAction = "Resolve top finding ($($top.area)): $($top.suggestion)"
    } else {
        $nextAction = "No findings - target is clean against current heuristics. Next: add deeper acceptance test or extend the review heuristics to cover this target type."
    }

    $row = [ordered]@{
        ts_utc          = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        target          = $rel
        target_type     = $targetType
        line_count      = $lineCount
        reviewer_slug   = $LaneSlug
        context         = $Context
        findings        = @($findings)
        next_action     = $nextAction
        status          = 'open'
        acted_on_at     = $null
        dismissed_at    = $null
        dismissed_reason= $null
    }

    if (Append-Row -Row $row) {
        Write-Output "----- forever-improve review -----"
        Write-Output "target:        $rel"
        Write-Output "target_type:   $targetType"
        Write-Output "line_count:    $lineCount"
        Write-Output "reviewer:      $LaneSlug"
        Write-Output "findings:      $($findings.Count)"
        foreach ($f in $findings) {
            Write-Output "  [$($f.severity)] $($f.area) - $($f.suggestion)"
        }
        Write-Output "next_action:   $nextAction"
        Write-Output "logged_to:     $LogPath"
    }
}

# ----- ReviewCommit: review `git show <sha>` -----
function Invoke-ReviewCommit {
    param([string]$ShaArg, [string]$LaneSlug)

    Push-Location $SanctumRoot
    try {
        $resolvedSha = (& git rev-parse $ShaArg 2>$null).Trim()
        if (-not $resolvedSha) {
            Write-Error "Could not resolve sha: $ShaArg"
            return
        }
        $msg = (& git log -1 --format='%s' $resolvedSha 2>$null).Trim()
        $files = & git show --name-only --format= $resolvedSha 2>$null | Where-Object { $_ -and $_.Trim() }
        $stat = & git show --shortstat --format= $resolvedSha 2>$null | Where-Object { $_ -and $_.Trim() } | Select-Object -First 1

        $findings = @()

        # Q1 - completeness: WIP / TODO in subject
        if ($msg -match '(?i)\b(WIP|TODO|FIXME|temp|tmp)\b') {
            $findings += @{ severity='major'; area='Q1-completeness'; suggestion="Commit subject contains WIP/TODO marker: '$msg'. Either finish or rename to a verb that matches no-bullshit doctrine (scaffolded/parse-clean/smoke-tested/shipped)." }
        }

        # Q2 - consistency: subject line conventions
        if ($msg.Length -gt 80) {
            $findings += @{ severity='minor'; area='Q2-consistency'; suggestion="Commit subject is $($msg.Length) chars (>80). Shorten or move detail to body." }
        }
        if ($msg -notmatch '^[a-z]+(\([a-z0-9\-]+\))?:') {
            $findings += @{ severity='minor'; area='Q2-consistency'; suggestion="Commit subject doesn't follow `verb(scope): summary` convention. Examples: 'sanctum:', 'fix(launcher):', 'ship(seraphim):'." }
        }

        # Q3 - simplicity: file count + lines changed
        if ($files -and $files.Count -gt 20) {
            $findings += @{ severity='major'; area='Q3-simplicity'; suggestion="Commit touches $($files.Count) files. Rule 6 of no-bullshit doctrine: one focused subject per commit. Consider splitting." }
        }

        # Q4 - verifiability: evidence in body?
        $body = (& git log -1 --format='%B' $resolvedSha 2>$null)
        if ($body -notmatch '(?i)(smoke|verified|tested|exit[\s\-]?code|measured|smoke[\s\-]?tested)') {
            $findings += @{ severity='minor'; area='Q4-verifiability'; suggestion='Commit body has no smoke/verified/tested evidence string. Per rule 2 of no-bullshit doctrine, claims need evidence in the same turn.' }
        }

        # Q5 - next increment
        $nextAction = ''
        if ($findings.Count -gt 0) {
            $top = $findings | Sort-Object @{Expression={ if ($_.severity -eq 'major') {0} else {1} }} | Select-Object -First 1
            $nextAction = "Address top finding for commit $resolvedSha ($($top.area)): $($top.suggestion)"
        } else {
            $nextAction = "Commit $resolvedSha passes 5-question pass. Next: confirm a downstream lane consumes the change without regression."
        }

        $row = [ordered]@{
            ts_utc          = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            target          = "commit:$resolvedSha"
            target_type     = 'commit'
            commit_subject  = $msg
            commit_files    = @($files)
            commit_shortstat= $stat
            reviewer_slug   = $LaneSlug
            findings        = @($findings)
            next_action     = $nextAction
            status          = 'open'
            acted_on_at     = $null
            dismissed_at    = $null
            dismissed_reason= $null
        }

        if (Append-Row -Row $row) {
            Write-Output "----- forever-improve review (commit) -----"
            Write-Output "sha:           $resolvedSha"
            Write-Output "subject:       $msg"
            Write-Output "files:         $($files.Count)"
            Write-Output "shortstat:     $stat"
            Write-Output "findings:      $($findings.Count)"
            foreach ($f in $findings) {
                Write-Output "  [$($f.severity)] $($f.area) - $($f.suggestion)"
            }
            Write-Output "next_action:   $nextAction"
            Write-Output "logged_to:     $LogPath"
        }
    } finally {
        Pop-Location
    }
}

# ----- Tally: count {open, acted-on, dismissed, expired} per lane -----
function Invoke-Tally {
    param([string]$LaneFilter = '')
    $rows = Read-Log
    if ($rows.Count -eq 0) {
        Write-Output "improvement-log empty: $LogPath"
        return
    }
    if ($LaneFilter) {
        $rows = $rows | Where-Object { $_.reviewer_slug -eq $LaneFilter }
    }
    $byLane = $rows | Group-Object -Property reviewer_slug
    Write-Output "----- forever-improve tally -----"
    Write-Output ("{0,-20} {1,6} {2,6} {3,6} {4,6} {5,6}" -f 'lane','open','acted','dismiss','expired','total')
    Write-Output ("{0,-20} {1,6} {2,6} {3,6} {4,6} {5,6}" -f '----','----','-----','-------','-------','-----')
    foreach ($g in $byLane) {
        $open    = @($g.Group | Where-Object { $_.status -eq 'open' }).Count
        $acted   = @($g.Group | Where-Object { $_.status -eq 'acted-on' }).Count
        $dism    = @($g.Group | Where-Object { $_.status -eq 'dismissed' }).Count
        $exp     = @($g.Group | Where-Object { $_.status -eq 'expired' }).Count
        Write-Output ("{0,-20} {1,6} {2,6} {3,6} {4,6} {5,6}" -f $g.Name, $open, $acted, $dism, $exp, $g.Count)
    }
    Write-Output ""
    Write-Output "total rows: $($rows.Count)"
}

# ----- Drain: mark expired rows older than $MaxTurns lane-turns -----
function Invoke-Drain {
    param([int]$Turns = 3)
    $rows = Read-Log
    if ($rows.Count -eq 0) { Write-Output "improvement-log empty: nothing to drain"; return }

    # Heuristic: 1 lane-turn ~= 30 minutes wall (rule-of-thumb; adjustable)
    # Conservative: 3 turns = 90 minutes. Operator can re-tune via -MaxTurns.
    $cutoffMin = $Turns * 30
    $now = (Get-Date).ToUniversalTime()
    $expiredCount = 0
    $newLines = @()
    foreach ($r in $rows) {
        $obj = $r
        if ($obj.status -eq 'open') {
            try {
                $ts = [datetime]::Parse($obj.ts_utc).ToUniversalTime()
                $ageMin = ($now - $ts).TotalMinutes
                if ($ageMin -gt $cutoffMin) {
                    $obj | Add-Member -NotePropertyName 'status' -NotePropertyValue 'expired' -Force
                    $obj | Add-Member -NotePropertyName 'dismissed_at' -NotePropertyValue $now.ToString("yyyy-MM-ddTHH:mm:ssZ") -Force
                    $obj | Add-Member -NotePropertyName 'dismissed_reason' -NotePropertyValue "auto-expired after $Turns turns (~$cutoffMin min)" -Force
                    $expiredCount++
                }
            } catch { }
        }
        $newLines += ($obj | ConvertTo-Json -Compress -Depth 10)
    }

    if ($expiredCount -gt 0) {
        if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) {
            Write-Error "Could not acquire lock at $LockPath after 10s"
            return
        }
        try {
            [System.IO.File]::WriteAllLines($LogPath, $newLines, [System.Text.UTF8Encoding]::new($false))
        } finally {
            Release-Lock -Path $LockPath
        }
    }
    Write-Output "drain complete: $expiredCount rows expired (age > $cutoffMin min)"
}

# ----- Dispatch -----
switch ($Action) {
    'Review' {
        if (-not $Target) { Write-Error '-Target required for Review'; exit 2 }
        Invoke-Review -TargetPath $Target -LaneSlug $Lane
    }
    'ReviewCommit' {
        if (-not $Sha) { Write-Error '-Sha required for ReviewCommit'; exit 2 }
        Invoke-ReviewCommit -ShaArg $Sha -LaneSlug $Lane
    }
    'Tally' {
        if ($Lane -and $Lane -ne 'sanctum') {
            Invoke-Tally -LaneFilter $Lane
        } else {
            Invoke-Tally
        }
    }
    'Drain' {
        Invoke-Drain -Turns $MaxTurns
    }
}
