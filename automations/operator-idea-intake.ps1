# operator-idea-intake.ps1 — mass intake + review ledger for operator-dumped ideas/links
# Author: RKOJ-ELENO :: 2026-05-24
#
# Origin: operator hard-canonical 2026-05-24 (15:42:25Z) — verbatim:
#   "in parrallel i need a system where i can mass put in github links ideas etc and its then
#    reviewed to see if we can pull things from the ideas or github repos to benefit our projects
#    and forever expand them"
#
# This is the v1 starter — append-only JSONL at _shared-memory/operator-ideas.jsonl, lock-based,
# mirrors the operator-utterance pattern. Review is operator-or-agent triggered (not auto-LLM yet);
# sanctum lane is expected to extend with curator-bot integration (Haiku ~$0.05/scan) per
# bot-fleet-quick-reference.md and the github-first-sourcing-doctrine.
#
# Actions:
#   Add     — append a new idea row (URL or free text). Auto-detects kind. Auto-tags.
#   List    — print pending/all rows in a table. Filter by status.
#   Mark    — flip status (pending/reviewed/adopted/rejected) + record deliverable lane + note.
#   Review  — surface top-N pending rows for an agent to review (stub: lists; doesn't call LLM yet).
#
# Status lifecycle:  pending  ->  reviewed  ->  (adopted | rejected)
#
# Usage:
#   powershell -File operator-idea-intake.ps1 -Action Add -Url "https://github.com/foo/bar" [-Note "..."] [-TargetLane jb-woodworks]
#   powershell -File operator-idea-intake.ps1 -Action Add -Text "free-form idea text" [-TargetLane sanctum]
#   powershell -File operator-idea-intake.ps1 -Action List [-Status pending|reviewed|adopted|rejected|all]
#   powershell -File operator-idea-intake.ps1 -Action Mark -Id <ts_utc> -Status reviewed [-DeliverableLane <lane>] [-Note "..."]
#   powershell -File operator-idea-intake.ps1 -Action Review [-Top 5] [-Lane <slug>]

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Add','List','Mark','Review')]
    [string]$Action,

    [string]$Url = '',
    [string]$Text = '',
    [string]$Id = '',
    [ValidateSet('pending','reviewed','adopted','rejected','all','')]
    [string]$Status = '',
    [string]$Note = '',
    [string]$TargetLane = '',
    [string]$DeliverableLane = '',
    [int]$Top = 5,
    [string]$Lane = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$JsonlPath = Join-Path $SanctumRoot '_shared-memory\operator-ideas.jsonl'
$LockPath  = Join-Path $SanctumRoot '_shared-memory\.operator-ideas.lock'

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

function Read-Rows {
    if (-not (Test-Path $JsonlPath)) { return @() }
    $rows = @()
    Get-Content -LiteralPath $JsonlPath -Encoding UTF8 | ForEach-Object {
        if ($_.Trim()) {
            try { $rows += ($_ | ConvertFrom-Json) } catch { }
        }
    }
    return $rows
}

function Get-IdeaKind {
    param([string]$U)
    if (-not $U) { return 'text' }
    if ($U -match '^https?://github\.com/[^/]+/[^/]+') { return 'github-repo' }
    if ($U -match '^https?://gitlab\.com/[^/]+/[^/]+') { return 'gitlab-repo' }
    if ($U -match '^https?://([^.]+\.)?(npmjs\.com|pypi\.org|crates\.io|rubygems\.org)') { return 'package' }
    if ($U -match '^https?://(arxiv\.org|huggingface\.co)') { return 'paper-or-model' }
    if ($U -match '^https?://') { return 'web-link' }
    return 'text'
}

function Get-AutoTags {
    param([string]$Body)
    $stop = @('the','and','for','with','this','that','have','from','they','them','will','what','make','need','want','your','also','just','like','keep','more','only','when','then','than','some','here','there','where','which','how','our','are','was','were','has','had','its','to','of','in','on','at','as','be','is','an','a','i','we','you','my','do','if','or','no','yes','so','all','any','can','use','add','get','set','fix','run','let','out','off','now','one','two','too','but','not','his','her','him','she','he','https','http','www','com','org','net','io')
    $clean = $Body.ToLower() -replace '[^a-z0-9\s\-_]', ' '
    $words = $clean -split '\s+' | Where-Object { $_ -and $_.Length -ge 4 -and $stop -notcontains $_ }
    $freq = @{}
    foreach ($w in $words) { if ($freq.ContainsKey($w)) { $freq[$w]++ } else { $freq[$w] = 1 } }
    $ranked = $freq.GetEnumerator() | Sort-Object -Property @{Expression='Value';Descending=$true}
    return @($ranked | Select-Object -First 5 | ForEach-Object { $_.Key })
}

switch ($Action) {

    'Add' {
        if (-not $Url -and -not $Text) {
            Write-Error "Add requires either -Url or -Text"
            exit 2
        }
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $kind = Get-IdeaKind -U $Url
        $body = if ($Text) { $Text } else { '' }
        $tagSource = if ($Text) { $Text } else { $Url + ' ' + $Note }
        $tags = Get-AutoTags -Body $tagSource

        if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) {
            Write-Error "Could not acquire lock at $LockPath after 10s"
            exit 2
        }
        try {
            $row = [ordered]@{
                ts_utc           = $ts
                kind             = $kind
                url              = $Url
                text             = $body
                note             = $Note
                target_lane_hint = $TargetLane
                tags             = @($tags)
                status           = 'pending'
                reviewed_by      = @()
                deliverable_lane = ''
                review_note      = ''
                resolved_at_utc  = $null
            }
            $json = $row | ConvertTo-Json -Compress -Depth 10
            $sw = [System.IO.StreamWriter]::new($JsonlPath, $true, [System.Text.UTF8Encoding]::new($false))
            $sw.WriteLine($json)
            $sw.Close()
            Write-Output $ts
        } finally {
            Release-Lock -Path $LockPath
        }
    }

    'List' {
        $rows = Read-Rows
        if (-not $Status -or $Status -eq 'all') { $filtered = $rows } else { $filtered = $rows | Where-Object { $_.status -eq $Status } }
        if (-not $filtered) {
            Write-Output "(no rows)"
            return
        }
        $filtered | Sort-Object ts_utc -Descending | ForEach-Object {
            $tagStr = if ($_.tags) { ($_.tags -join ',') } else { '' }
            $body = if ($_.url) { $_.url } else { $_.text }
            $preview = if ($body.Length -gt 70) { $body.Substring(0,70) + '...' } else { $body }
            "{0}  {1,-12}  {2,-9}  [{3}]  {4}" -f $_.ts_utc, $_.kind, $_.status, $tagStr, $preview
        }
    }

    'Mark' {
        if (-not $Id) { Write-Error "Mark requires -Id <ts_utc>"; exit 2 }
        if (-not $Status -or $Status -eq 'all') { Write-Error "Mark requires -Status pending|reviewed|adopted|rejected"; exit 2 }
        $rows = Read-Rows
        $found = $false
        $newRows = @()
        foreach ($r in $rows) {
            if ($r.ts_utc -eq $Id) {
                $found = $true
                $r.status = $Status
                if ($DeliverableLane) { $r.deliverable_lane = $DeliverableLane }
                if ($Note) { $r.review_note = $Note }
                if ($Lane -and ($r.reviewed_by -notcontains $Lane)) { $r.reviewed_by = @($r.reviewed_by) + $Lane }
                if ($Status -eq 'adopted' -or $Status -eq 'rejected') {
                    $r.resolved_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
                }
            }
            $newRows += $r
        }
        if (-not $found) { Write-Error "No row with ts_utc=$Id"; exit 2 }

        if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) { Write-Error "Could not acquire lock"; exit 2 }
        try {
            $sw = [System.IO.StreamWriter]::new($JsonlPath, $false, [System.Text.UTF8Encoding]::new($false))
            foreach ($r in $newRows) { $sw.WriteLine(($r | ConvertTo-Json -Compress -Depth 10)) }
            $sw.Close()
            Write-Output "marked id=$Id status=$Status"
        } finally {
            Release-Lock -Path $LockPath
        }
    }

    'Review' {
        $rows = Read-Rows
        $pending = $rows | Where-Object { $_.status -eq 'pending' }
        if ($Lane) { $pending = $pending | Where-Object { $_.target_lane_hint -eq $Lane -or -not $_.target_lane_hint } }
        $topRows = $pending | Sort-Object ts_utc | Select-Object -First $Top
        if (-not $topRows) {
            Write-Output "(no pending rows)"
            return
        }
        Write-Output "----- Review queue (top $Top pending) -----"
        $topRows | ForEach-Object {
            $body = if ($_.url) { $_.url } else { $_.text }
            Write-Output ("{0}  kind={1}  tags=[{2}]  hint={3}" -f $_.ts_utc, $_.kind, ($_.tags -join ','), $_.target_lane_hint)
            Write-Output ("  body: {0}" -f $body)
            if ($_.note) { Write-Output ("  note: {0}" -f $_.note) }
            Write-Output ("  next: powershell -File operator-idea-intake.ps1 -Action Mark -Id {0} -Status reviewed -DeliverableLane <lane> -Note '<finding>'" -f $_.ts_utc)
            Write-Output ""
        }
        Write-Output "(stub: this is a list-only surface. sanctum lane will extend with curator-bot Haiku scan ~`$0.05/idea per bot-fleet-quick-reference.md)"
    }
}
