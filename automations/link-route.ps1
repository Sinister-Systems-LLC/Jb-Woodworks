# link-route.ps1 -- Phase 3 routing brain for drop-link ingest
# Author: RKOJ-ELENO :: 2026-05-24
#
# Doctrine: _shared-memory/knowledge/drop-link-ingest-spec-2026-05-24.md section "Phase 3"
# Plan: _shared-memory/plans/sanctum-bot-mcp-expansion-2026-05-24T2115Z/plan.md (P1 item 1)
#
# Reads a processed link-ingest entry (download landed) and decides which action
# to take: archive / project-fork / doctrine-update / system-update / skip.
# Writes a proposal row to _shared-memory/OPERATOR-ACTION-QUEUE.md with a
# diff-preview line so operator can approve / dismiss with one ack.
#
# Phase 3a (THIS SHIP) = RULE-BASED routing (no LLM calls; $0 spend per operator
# token-efficiency directive). The rules are:
#
#   github-repo:
#     has LICENSE file + README + .git/ present  -> ARCHIVE (add to external-imports/CANDIDATES.md)
#     no LICENSE                                  -> ARCHIVE-AS-UNLICENSED (operator review before use)
#     looks like a complete app (Dockerfile + multiple source dirs)  -> PROJECT-FORK candidate
#     single-script repo (1-3 source files)       -> EXTRACT-TO-TOOLS candidate
#
#   github-issue / github-pr:                     -> ARCHIVE (snippet for context)
#   github-file:                                  -> EXTRACT-TO-TOOLS (single file = pure utility)
#
#   instagram-video / youtube-video:
#     has transcript.txt or *.srt                 -> DOCTRINE-UPDATE candidate (queue review for novel technique)
#     no transcript yet                           -> SKIP (wait for transcriber bot to land)
#
#   generic-url:
#     page.html present + text-extract feasible   -> DOCTRINE-UPDATE candidate
#
# Phase 3b (next iter) = LLM-ASSISTED routing via scribe (Haiku ~$0.02/decision)
# OR mcp__ruflo__wasm_agent_prompt (Haiku-on-WASM $0). Compares against existing
# brain entries before proposing; suppresses duplicates per JCODE-style dedup.
#
# Actions:
#   Route     -Id <link-ingest-id>      route a single processed entry
#   RouteAll  [-Limit N]                route all processed-status entries (default N=5)
#   Status                              show routing decision counters from log

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [ValidateSet('Route','RouteAll','Status')] [string]$Action,
    [string]$Id = '',
    [int]$Limit = 5,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$IngestRoot = Join-Path $SanctumRoot '_shared-memory\inbox\link-ingest'
$QueuePath  = Join-Path $IngestRoot 'queue.jsonl'
$LogPath    = Join-Path $IngestRoot 'link-ingest-log.jsonl'
$Processed  = Join-Path $IngestRoot 'processed'
$OperatorQ  = Join-Path $SanctumRoot '_shared-memory\OPERATOR-ACTION-QUEUE.md'

function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Append-Log { param($Row)
    $line = $Row | ConvertTo-Json -Compress -Depth 6
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}
function Read-Queue {
    if (-not (Test-Path $QueuePath)) { return @() }
    $rows = @()
    foreach ($l in (Get-Content $QueuePath -ErrorAction SilentlyContinue)) {
        if (-not $l -or -not $l.Trim()) { continue }
        try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {}
    }
    return $rows
}

function Find-ProcessedDir { param([string]$IngestId)
    $candidates = Get-ChildItem -LiteralPath $Processed -Directory -ErrorAction SilentlyContinue |
                  Where-Object { $_.Name -like "$IngestId-*" }
    if ($candidates.Count -eq 0) { return $null }
    return $candidates[0].FullName
}

function Decide-Action { param($Row, [string]$ProcDir)
    $dlDir = Join-Path $ProcDir 'download'
    switch ($Row.kind) {
        'github-repo' {
            $repoDir = Join-Path $dlDir 'repo'
            if (-not (Test-Path $repoDir)) { return @{ action='SKIP'; reason='no repo dir (download incomplete?)' } }
            $hasLicense = (Test-Path (Join-Path $repoDir 'LICENSE')) -or (Test-Path (Join-Path $repoDir 'LICENSE.md')) -or (Test-Path (Join-Path $repoDir 'LICENSE.txt'))
            $hasReadme  = (Test-Path (Join-Path $repoDir 'README.md')) -or (Test-Path (Join-Path $repoDir 'README'))
            $hasDocker  = (Test-Path (Join-Path $repoDir 'Dockerfile')) -or (Test-Path (Join-Path $repoDir 'docker-compose.yml'))
            $srcDirs = @(Get-ChildItem -LiteralPath $repoDir -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -notin @('.git','node_modules','.github','docs','test','tests','__pycache__') }).Count
            $srcFiles = @(Get-ChildItem -LiteralPath $repoDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @('.py','.ts','.js','.rs','.go','.sh','.ps1') }).Count
            if ($hasDocker -or $srcDirs -ge 3) {
                return @{ action='PROJECT-FORK'; reason="hasDocker=$hasDocker srcDirs=$srcDirs (complete app)"; target='projects/_pending-from-links/<slug>/' }
            }
            if ($srcFiles -ge 1 -and $srcDirs -le 1 -and -not $hasDocker) {
                return @{ action='EXTRACT-TO-TOOLS'; reason="srcFiles=$srcFiles srcDirs=$srcDirs (utility-shape)"; target='tools/<slug>/' }
            }
            if (-not $hasLicense) {
                return @{ action='ARCHIVE-UNLICENSED'; reason='no LICENSE found; operator review before use'; target='_shared-memory/external-imports/CANDIDATES.md (flagged)' }
            }
            return @{ action='ARCHIVE'; reason="LICENSE=$hasLicense README=$hasReadme srcDirs=$srcDirs (library shape)"; target='_shared-memory/external-imports/CANDIDATES.md' }
        }
        'github-issue' { return @{ action='ARCHIVE'; reason='github issue snippet for context'; target='_shared-memory/external-imports/CANDIDATES.md (issue ref)' } }
        'github-pr'    { return @{ action='ARCHIVE'; reason='github PR snippet for context'; target='_shared-memory/external-imports/CANDIDATES.md (pr ref)' } }
        'github-file'  { return @{ action='EXTRACT-TO-TOOLS'; reason='single-file github extract'; target='tools/<slug>/' } }
        'github-other' { return @{ action='ARCHIVE'; reason='generic github resource'; target='_shared-memory/external-imports/CANDIDATES.md' } }
        { $_ -in 'instagram-video','youtube-video' } {
            $hasTranscript = @(Get-ChildItem -LiteralPath $dlDir -Filter '*.srt' -File -ErrorAction SilentlyContinue).Count -gt 0 -or
                             @(Get-ChildItem -LiteralPath $dlDir -Filter '*.txt' -File -ErrorAction SilentlyContinue).Count -gt 0
            if (-not $hasTranscript) {
                return @{ action='SKIP'; reason='video downloaded but no transcript yet (waiting for transcriber bot)'; target='(re-route after transcriber lands)' }
            }
            return @{ action='DOCTRINE-CANDIDATE'; reason='video + transcript present; novel-technique review'; target='_shared-memory/knowledge/from-ingest-<slug>-<date>.md (proposed)' }
        }
        'generic-url' {
            $page = Join-Path $dlDir 'page.html'
            if (-not (Test-Path $page)) { return @{ action='SKIP'; reason='no page.html (download incomplete)' } }
            return @{ action='DOCTRINE-CANDIDATE'; reason='generic url with extractable html'; target='_shared-memory/knowledge/from-ingest-<slug>-<date>.md (proposed)' }
        }
        default {
            return @{ action='SKIP'; reason="no rule for kind=$($Row.kind)" }
        }
    }
}

function Surface-To-OperatorQueue { param($Row, $Decision, [string]$ProcDir)
    $ts = Utc-Now
    $priority = if ($Decision.action -eq 'ARCHIVE-UNLICENSED') { '🟠 high' } elseif ($Decision.action -eq 'SKIP') { '🟢 low' } else { '🟡 medium' }
    $heading = "## $ts -- $priority -- Drop-link routing proposal: $($Decision.action) for $($Row.kind)"
    $body = @"

> Author: RKOJ-ELENO :: 2026-05-24 (sanctum lane / link-route)

**URL:** $($Row.url)
**Ingest id:** $($Row.id)
**Decision:** $($Decision.action)
**Rationale:** $($Decision.reason)
**Proposed target:** $($Decision.target)
**Download dir:** $ProcDir

**Operator actions:**
- [ ] approve (sanctum executes the action next lane turn)
- [ ] dismiss (link-route marks decided=dismissed; sweep removes processed dir after 7 days)
- [ ] override -> different action (reply via inbox to sanctum)

---

"@
    Add-Content -LiteralPath $OperatorQ -Value ($heading + $body) -Encoding UTF8
}

switch ($Action) {

    'Route' {
        if (-not $Id) { Write-Host "ERR: -Id required"; exit 2 }
        $row = (Read-Queue) | Where-Object { $_.id -eq $Id } | Select-Object -First 1
        if (-not $row) { Write-Host "NOTFOUND id=$Id"; exit 1 }
        if ($row.status -ne 'processed') { Write-Host "SKIP: row status=$($row.status), not 'processed'"; exit 0 }
        $procDir = Find-ProcessedDir $Id
        if (-not $procDir) { Write-Host "NOTFOUND processed dir for id=$Id"; exit 1 }
        $decision = Decide-Action -Row $row -ProcDir $procDir
        Write-Host ("ROUTE id={0} kind={1} -> {2}" -f $row.id, $row.kind, $decision.action)
        Write-Host ("  reason: " + $decision.reason)
        Write-Host ("  target: " + $decision.target)
        Append-Log @{ ts_utc=(Utc-Now); event='route-decided'; id=$row.id; kind=$row.kind; action=$decision.action; reason=$decision.reason; target=$decision.target }
        if ($decision.action -ne 'SKIP') {
            Surface-To-OperatorQueue -Row $row -Decision $decision -ProcDir $procDir
            Write-Host "  -> proposal row APPENDED to OPERATOR-ACTION-QUEUE.md"
        }
        exit 0
    }

    'RouteAll' {
        $rows = @((Read-Queue) | Where-Object { $_.status -eq 'processed' } | Select-Object -First $Limit)
        if ($rows.Count -eq 0) { Write-Host "no processed rows pending route"; exit 0 }
        foreach ($r in $rows) {
            $procDir = Find-ProcessedDir $r.id
            if (-not $procDir) { Write-Host ("  [skip] no processed dir for " + $r.id); continue }
            $decision = Decide-Action -Row $r -ProcDir $procDir
            Write-Host ("ROUTE id={0} kind={1} -> {2}" -f $r.id, $r.kind, $decision.action)
            Append-Log @{ ts_utc=(Utc-Now); event='route-decided'; id=$r.id; kind=$r.kind; action=$decision.action; reason=$decision.reason; target=$decision.target }
            if ($decision.action -ne 'SKIP') { Surface-To-OperatorQueue -Row $r -Decision $decision -ProcDir $procDir }
        }
        exit 0
    }

    'Status' {
        if (-not (Test-Path $LogPath)) { Write-Host "no log yet"; exit 0 }
        $rows = @()
        foreach ($l in (Get-Content $LogPath -ErrorAction SilentlyContinue)) {
            if ($l) { try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {} }
        }
        $routed = @($rows | Where-Object { $_.event -eq 'route-decided' })
        $byAction = $routed | Group-Object -Property action | Select-Object Name, Count
        Write-Host ("link-route :: " + $routed.Count + " routing decisions logged")
        if ($byAction) { $byAction | Format-Table -AutoSize | Out-String | Write-Host }
        exit 0
    }
}
