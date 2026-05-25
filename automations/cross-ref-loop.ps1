# cross-ref-loop.ps1 — fleet-wide cross-reference + quality-ceiling probe.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T17:21:54Z:
#   "make our claude memory smarter ... agents fuck perfectly fully by them
#    selves towards their goal and fully loop and continue to work nd not stop.
#    just like in jcode cross reference. contracdict itself and what not until
#    quality drops. so that it gets to the highest point it can."
#
# Composes with:
#   - counter-arg.ps1            (logs single contradictions resolved by judgment)
#   - jcode-parity-probe.ps1     (empirical feature-presence test)
#   - no-bullshit doctrine R4    (continuous self-audit)
#   - no-bullshit doctrine R8    (10 quality-degradation signals = ceiling)
#
# What it does (v0.1, READ-ONLY):
#   1. Extracts recent shipped/claimed lines from PROGRESS/<lane>.md.
#   2. For each claim, derives keywords + cross-refs against:
#        - brain entries (_shared-memory/knowledge/*.md)
#        - sibling-lane PROGRESS (other lanes' recent turns)
#        - operator-utterances tail
#   3. Flags claims as SUPPORTED / UNSUPPORTED / CONTRADICTION / OPERATOR-DIRECTED.
#   4. Runs the 10 quality-ceiling signals from no-bullshit R8.
#   5. Returns exit code = (unsupported + contradiction count); 0 = clean.
#
# v0.1 is READ-ONLY by design: it SURFACES, the calling agent decides to log a
# real counter-arg via counter-arg.ps1 with judgment. Auto-logging every
# unsupported claim would flood counter-arguments.jsonl with noise.
#
# Usage:
#   powershell -File cross-ref-loop.ps1 -Lane test-modes
#   powershell -File cross-ref-loop.ps1 -Lane test-modes -TopN 10 -Json
#   powershell -File cross-ref-loop.ps1 -Lane all   # iterates every lane with PROGRESS
#
# The "loop" in the name refers to the agent calling this each /loop iter:
#   - PASS  -> proceed with next work
#   - WARN  -> log counter-args for top findings, then proceed
#   - FAIL  -> ceiling hit; STOP expanding, consolidate (R8 of no-bullshit)

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$Lane,
    [int]$TopN = 8,
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Json,
    [switch]$Verbose2
)

$ErrorActionPreference = 'Continue'

$progressDir   = Join-Path $SanctumRoot '_shared-memory\PROGRESS'
$brainDir      = Join-Path $SanctumRoot '_shared-memory\knowledge'
$resumeRoot    = Join-Path $SanctumRoot '_shared-memory\resume-points'
$utterFile     = Join-Path $SanctumRoot '_shared-memory\operator-utterances.jsonl'
$queueFile     = Join-Path $SanctumRoot '_shared-memory\OPERATOR-ACTION-QUEUE.md'
$plansDir      = Join-Path $SanctumRoot '_shared-memory\plans'
$claudeMd      = Join-Path $SanctumRoot 'CLAUDE.md'

# ---------- helpers ----------

function Get-ClaimKeywords {
    param([string]$Claim)
    # Lowercase, strip punctuation, take >=4-char tokens, dedup, drop very common stopwords.
    $stop = @('this','that','with','from','have','will','what','when','done','then','they',
              'been','were','your','their','than','which','also','into','more','make','just',
              'work','test','only','some','like','need','here','same','about','each','very',
              'parse','clean','still','again','using','where','those','these','because')
    $words = ($Claim -replace '[^a-zA-Z0-9 _-]',' ').ToLower() -split '\s+' |
             Where-Object { $_.Length -ge 4 -and $stop -notcontains $_ } |
             Select-Object -Unique
    $words
}

function Get-RecentClaims {
    param([string]$LaneName, [int]$Top)
    $file = Join-Path $progressDir "$LaneName.md"
    if (-not (Test-Path $file)) { return @() }
    $lines = Get-Content $file -ErrorAction SilentlyContinue
    # Claims = lines starting with "- **" (the bolded-verb pattern from no-bullshit doctrine)
    $claims = @()
    foreach ($l in $lines) {
        if ($l -match '^\s*-\s+\*\*([^*]+)\*\*\s*(.*)$') {
            $verb = $matches[1].Trim()
            $rest = $matches[2].Trim()
            $full = ("$verb $rest").Trim()
            if ($full.Length -gt 10) { $claims += $full }
        }
        if ($claims.Count -ge $Top) { break }
    }
    $claims
}

function Get-BrainKeywordHits {
    param([string[]]$Keywords)
    if (-not (Test-Path $brainDir)) { return 0 }
    $allBrain = Get-ChildItem $brainDir -Filter '*.md' -ErrorAction SilentlyContinue
    $hits = 0
    foreach ($f in $allBrain) {
        $content = (Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue).ToLower()
        if (-not $content) { continue }
        foreach ($k in $Keywords) {
            if ($content -match [regex]::Escape($k)) { $hits++; break }
        }
    }
    $hits
}

function Get-SiblingContradictions {
    param([string]$LaneName, [string[]]$Keywords)
    $cont = @()
    # Exclude non-lane files (README.md, _INDEX.md, etc.) — real lane files don't start with _ or capital README.
    $others = Get-ChildItem $progressDir -Filter '*.md' -ErrorAction SilentlyContinue |
              Where-Object { $_.BaseName -ne $LaneName -and $_.BaseName -notmatch '^(README|_INDEX|_README|TEMPLATE)$' }
    # Word-boundary regex to avoid 'blocked' inside 'unblocked', 'fail' inside 'available', etc.
    $contradictMarkers = @('\bfail(ed|s)?\b','\bbroke(n)?\b','\bwrong\b','\brevert(ed)?\b','\brollback\b','\bdisputed\b','\bregress(ed|ion)?\b','\bcontradict(s|ed)?\b')
    foreach ($f in $others) {
        $content = Get-Content $f.FullName -ErrorAction SilentlyContinue
        if (-not $content) { continue }
        $kwHit = $false
        foreach ($line in $content[0..([Math]::Min(120, $content.Count - 1))]) {
            $low = $line.ToLower()
            $kwMatch = $false
            foreach ($k in $Keywords) {
                # require keyword as standalone word too
                if ($low -match ('\b' + [regex]::Escape($k) + '\b')) { $kwMatch = $true; break }
            }
            if (-not $kwMatch) { continue }
            foreach ($m in $contradictMarkers) {
                if ($low -match $m) {
                    $cont += "$($f.BaseName): $($line.Trim().Substring(0,[Math]::Min(80,$line.Trim().Length)))"
                    $kwHit = $true; break
                }
            }
            if ($kwHit) { break }
        }
    }
    $cont | Select-Object -Unique
}

function Get-OperatorDirected {
    param([string[]]$Keywords)
    if (-not (Test-Path $utterFile)) { return $false }
    $tail = Get-Content $utterFile -Tail 30 -ErrorAction SilentlyContinue
    foreach ($l in $tail) {
        $low = $l.ToLower()
        foreach ($k in $Keywords) {
            if ($low -match [regex]::Escape($k)) { return $true }
        }
    }
    return $false
}

function Get-QualityCeiling {
    $signals = [ordered]@{}

    # 1. brain count vs 150
    $brainCount = @(Get-ChildItem $brainDir -Filter '*.md' -ErrorAction SilentlyContinue).Count
    $signals['brain_md_count']      = @{ val=$brainCount; cap=150; fired=($brainCount -gt 150) }

    # 2. PROGRESS file size for this lane vs 300 KB
    $progFile = Join-Path $progressDir "$Lane.md"
    $progKB = if (Test-Path $progFile) { [int]((Get-Item $progFile).Length / 1024) } else { 0 }
    $signals['progress_kb']         = @{ val=$progKB; cap=300; fired=($progKB -gt 300) }

    # 3. resume-points per lane (search both Sanctum + lane-specific dirs)
    $rpCount = 0
    if (Test-Path $resumeRoot) {
        $rpCount = @(Get-ChildItem $resumeRoot -Recurse -Filter '*.json' -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name -match $Lane -or $_.DirectoryName -match $Lane }).Count
        if ($rpCount -eq 0) {
            $rpCount = @(Get-ChildItem (Join-Path $resumeRoot 'Sinister Sanctum') -Filter '*.json' -ErrorAction SilentlyContinue).Count
        }
    }
    $signals['resume_points_lane']  = @{ val=$rpCount; cap=20; fired=($rpCount -gt 20) }

    # 4. queue rows vs 25 (count of "## " section headers in queue file)
    $queueRows = 0
    if (Test-Path $queueFile) {
        $queueRows = (Select-String -Path $queueFile -Pattern '^##\s' -ErrorAction SilentlyContinue).Count
    }
    $signals['queue_sections']      = @{ val=$queueRows; cap=25; fired=($queueRows -gt 25) }

    # 5. active plans vs 12
    $planCount = 0
    if (Test-Path $plansDir) {
        $planCount = @(Get-ChildItem $plansDir -Directory -ErrorAction SilentlyContinue).Count
    }
    $signals['active_plans']        = @{ val=$planCount; cap=12; fired=($planCount -gt 12) }

    # 6. cold-start step count vs 10 (number of "^N\. " lines in the cold-start section of CLAUDE.md)
    $coldStartSteps = 0
    if (Test-Path $claudeMd) {
        $c = Get-Content $claudeMd -Raw -ErrorAction SilentlyContinue
        if ($c -match '(?s)## Cold-start.*?(?=##\s)') {
            $section = $matches[0]
            $coldStartSteps = ([regex]::Matches($section, '(?m)^\d+\.\s')).Count
        }
    }
    $signals['cold_start_steps']    = @{ val=$coldStartSteps; cap=11; fired=($coldStartSteps -gt 11) }

    # 7. launcher script size vs 1500 lines
    $launcher = Join-Path $SanctumRoot 'automations\start-sinister-session.ps1'
    $launcherLines = 0
    if (Test-Path $launcher) { $launcherLines = @(Get-Content $launcher -ErrorAction SilentlyContinue).Count }
    $signals['launcher_lines']      = @{ val=$launcherLines; cap=1500; fired=($launcherLines -gt 1500) }

    $signals
}

# ---------- analyze ----------

$lanesToRun = @()
if ($Lane -eq 'all') {
    $lanesToRun = Get-ChildItem $progressDir -Filter '*.md' -ErrorAction SilentlyContinue |
                  ForEach-Object { $_.BaseName }
} else {
    $lanesToRun = @($Lane)
}

$allResults = @()
foreach ($currentLane in $lanesToRun) {
    $claims = Get-RecentClaims -LaneName $currentLane -Top $TopN
    if (-not $claims -or $claims.Count -eq 0) {
        $allResults += [PSCustomObject]@{
            lane=$currentLane; status='no-claims'; analyzed=0;
            supported=0; unsupported=0; contradictions=0; operator_directed=0
        }
        continue
    }

    $supported    = 0
    $unsupported  = 0
    $contradicted = 0
    $opDirected   = 0
    $details      = @()

    foreach ($claim in $claims) {
        $kws = Get-ClaimKeywords -Claim $claim
        if ($kws.Count -lt 2) { continue }
        $topKws = $kws | Select-Object -First 8

        $brainHits = Get-BrainKeywordHits -Keywords $topKws
        $sibContras = Get-SiblingContradictions -LaneName $currentLane -Keywords $topKws
        $isOpDirected = Get-OperatorDirected -Keywords $topKws

        $tag = if ($sibContras.Count -gt 0) {
                   $contradicted++; 'CONTRADICTION'
               } elseif ($brainHits -eq 0) {
                   $unsupported++; 'UNSUPPORTED'
               } else {
                   $supported++; 'SUPPORTED'
               }
        if ($isOpDirected) { $opDirected++ }

        $details += [PSCustomObject]@{
            tag = $tag
            claim = $claim.Substring(0, [Math]::Min(110, $claim.Length))
            keywords = ($topKws -join ',')
            brain_hits = $brainHits
            sibling_contra = if ($sibContras.Count -gt 0) { $sibContras[0] } else { '' }
            operator_directed = $isOpDirected
        }
    }

    $allResults += [PSCustomObject]@{
        lane = $currentLane
        analyzed = $claims.Count
        supported = $supported
        unsupported = $unsupported
        contradictions = $contradicted
        operator_directed = $opDirected
        details = $details
    }
}

# ---------- quality ceiling ----------
$ceiling = Get-QualityCeiling
$ceilingFired = @($ceiling.GetEnumerator() | Where-Object { $_.Value.fired }).Count

# ---------- report ----------
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$totalUns = ($allResults | Measure-Object -Property unsupported -Sum).Sum
$totalCon = ($allResults | Measure-Object -Property contradictions -Sum).Sum
$exitCode = [int]$totalUns + [int]$totalCon + [int]$ceilingFired

if ($Json) {
    [ordered]@{
        ts_utc = $ts
        lanes = $allResults
        ceiling = $ceiling
        ceiling_fired_count = $ceilingFired
        total_unsupported = [int]$totalUns
        total_contradictions = [int]$totalCon
        exit_code = $exitCode
        verdict = if ($exitCode -eq 0) { 'PASS' } elseif ($ceilingFired -gt 0) { 'CEILING-FAIL' } else { 'WARN' }
    } | ConvertTo-Json -Depth 6
    exit $exitCode
}

$verdict = if ($exitCode -eq 0) { 'PASS' } elseif ($ceilingFired -gt 0) { 'CEILING-FAIL' } else { 'WARN' }
Write-Output ""
Write-Output "[$ts] cross-ref-loop :: verdict=$verdict unsupported=$totalUns contradictions=$totalCon ceiling-fired=$ceilingFired"
Write-Output ""

foreach ($r in $allResults) {
    Write-Output "=== lane: $($r.lane) (analyzed=$($r.analyzed) SUP=$($r.supported) UNS=$($r.unsupported) CON=$($r.contradictions) OP-DIR=$($r.operator_directed)) ==="
    foreach ($d in $r.details) {
        $line = "  [{0,-13}] {1}" -f $d.tag, $d.claim
        if ($d.sibling_contra) { $line += "`n      sib: $($d.sibling_contra)" }
        Write-Output $line
    }
    Write-Output ""
}

Write-Output "=== quality-ceiling (R8 of no-bullshit doctrine) ==="
foreach ($k in $ceiling.Keys) {
    $v = $ceiling[$k]
    $mark = if ($v.fired) { '[FIRED]' } else { '[ok]   ' }
    Write-Output ("  $mark {0,-22} {1}/{2}" -f $k, $v.val, $v.cap)
}
Write-Output ""

if ($ceilingFired -gt 0) {
    Write-Output "CEILING HIT -- STOP expanding, consolidate first (no-bullshit doctrine rule 8)."
} elseif ($exitCode -gt 0) {
    Write-Output "Findings present. Log a counter-arg via counter-arg.ps1 for the top contradiction/unsupported, then proceed."
} else {
    Write-Output "Clean. Proceed with next work unit."
}

exit $exitCode
