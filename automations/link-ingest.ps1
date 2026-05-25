# link-ingest.ps1 -- drop-link ingest entrypoint (Phase 1: classify + queue + log)
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T20:15Z (verbatim):
#   "a system where i can drop and instagram video link into or github link, you
#    download the video listen to what its saying and make a move or download
#    github source and review and place it into our archieves or start project
#    with it or update our systems where you see fit with this. make sure this
#    system grows with us and learns from its mistakes and gets better"
#
# Phase 1 (THIS SHIP): classification + queue + log. Pipeline stages 2-6 (download,
# transcribe, analyze, act, learn) land in subsequent iters per the master plan
# at _shared-memory/plans/sanctum-master-plan-2026-05-24T2020Z/plan.md section 4.
#
# Actions:
#   Add      -Url <URL> [-Note "..."]            classify + queue the URL
#   List     [-Status pending|processed|all]     show queue
#   Process  [-Limit N]                          DRY-RUN of stage 2 (download) -- not implemented yet, prints plan
#   Status                                       summary counters

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [ValidateSet('Add','List','Process','Status')] [string]$Action,
    [string]$Url = '',
    [string]$Note = '',
    [ValidateSet('pending','processed','all')] [string]$Status = 'pending',
    [int]$Limit = 1,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$Root      = Join-Path $SanctumRoot '_shared-memory\inbox\link-ingest'
$QueuePath = Join-Path $Root 'queue.jsonl'
$LogPath   = Join-Path $Root 'link-ingest-log.jsonl'
$LockPath  = Join-Path $Root '.queue.lock'
$Processed = Join-Path $Root 'processed'

if (-not (Test-Path $Root))      { New-Item -ItemType Directory -Path $Root -Force | Out-Null }
if (-not (Test-Path $Processed)) { New-Item -ItemType Directory -Path $Processed -Force | Out-Null }

function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function New-Id { return (Utc-Now).Replace(':','').Replace('-','') + '-' + ([guid]::NewGuid().ToString('N').Substring(0,6)) }

function Acquire-Lock { param([int]$TimeoutSec = 10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            try {
                if (Test-Path $LockPath) {
                    $age = ((Get-Date) - (Get-Item $LockPath).LastWriteTime).TotalSeconds
                    if ($age -gt 10) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue }
                }
            } catch {}
            Start-Sleep -Milliseconds 100
        }
    }
}
function Release-Lock { try { if (Test-Path $LockPath) { Remove-Item $LockPath -Force -ErrorAction SilentlyContinue } } catch {} }

function Classify-Url { param([string]$U)
    if (-not $U) { return [pscustomobject]@{ kind='invalid'; host=''; reason='empty url' } }
    if ($U -notmatch '^https?://') { return [pscustomobject]@{ kind='invalid'; host=''; reason='missing http(s):// scheme' } }
    try { $uri = [Uri]$U } catch { return [pscustomobject]@{ kind='invalid'; host=''; reason="cannot parse: $($_.Exception.Message)" } }
    if (-not $uri.Host) { return [pscustomobject]@{ kind='invalid'; host=''; reason='no host parseable from url' } }
    $h = $uri.Host.ToLower()
    $p = $uri.AbsolutePath
    if ($h -match '(^|\.)instagram\.com$' -and $p -match '^/(p|reel|reels|tv)/') {
        return [pscustomobject]@{ kind='instagram-video'; host=$h; path=$p; reason='matches /p/|/reel(s)?/|/tv/ pattern' }
    }
    if ($h -match '(^|\.)github\.com$') {
        if     ($p -match '^/[^/]+/[^/]+/issues/\d+')        { return [pscustomobject]@{ kind='github-issue'; host=$h; path=$p; reason='matches /issues/N' } }
        elseif ($p -match '^/[^/]+/[^/]+/pull/\d+')          { return [pscustomobject]@{ kind='github-pr';    host=$h; path=$p; reason='matches /pull/N' } }
        elseif ($p -match '^/[^/]+/[^/]+/blob/')             { return [pscustomobject]@{ kind='github-file';  host=$h; path=$p; reason='matches /blob/' } }
        elseif ($p -match '^/[^/]+/[^/]+/?$')                { return [pscustomobject]@{ kind='github-repo';  host=$h; path=$p; reason='matches /owner/repo' } }
        else                                                  { return [pscustomobject]@{ kind='github-other'; host=$h; path=$p; reason='github but no specific pattern' } }
    }
    if ($h -match '(^|\.)youtube\.com$' -or $h -eq 'youtu.be') {
        return [pscustomobject]@{ kind='youtube-video'; host=$h; path=$p; reason='youtube host' }
    }
    return [pscustomobject]@{ kind='generic-url'; host=$h; path=$p; reason='no specific matcher hit' }
}

function Read-QueueRows {
    if (-not (Test-Path $QueuePath)) { return @() }
    $rows = @()
    foreach ($l in (Get-Content $QueuePath -ErrorAction SilentlyContinue)) {
        if (-not $l -or -not $l.Trim()) { continue }
        try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {}
    }
    return $rows
}

function Append-Row { param($Row, [string]$Path)
    $line = $Row | ConvertTo-Json -Compress -Depth 6
    Add-Content -LiteralPath $Path -Value $line -Encoding UTF8
}

switch ($Action) {
    'Add' {
        if (-not $Url) { Write-Host "ERR: -Url required"; exit 2 }
        $cls = Classify-Url $Url
        if ($cls.kind -eq 'invalid') { Write-Host "ERR: invalid url: $($cls.reason)"; exit 3 }
        if (-not (Acquire-Lock)) { Write-Host "ERR: lock contention"; exit 4 }
        try {
            $id  = New-Id
            $row = [pscustomobject]@{
                id          = $id
                ts_utc      = Utc-Now
                url         = $Url
                note        = $Note
                kind        = $cls.kind
                host        = $cls.host
                path        = $cls.path
                classify_reason = $cls.reason
                status      = 'pending'
                added_by    = 'sanctum'
            }
            Append-Row -Row $row -Path $QueuePath
            Append-Row -Row ([pscustomobject]@{ ts_utc=(Utc-Now); event='queued'; id=$id; kind=$cls.kind; url=$Url }) -Path $LogPath
            Write-Host ("OK: queued id={0} kind={1} url={2}" -f $id, $cls.kind, $Url)
        } finally { Release-Lock }
        exit 0
    }

    'List' {
        $rows = Read-QueueRows
        if ($Status -ne 'all') { $rows = @($rows | Where-Object { $_.status -eq $Status }) }
        if ($rows.Count -eq 0) { Write-Host "no rows (status=$Status)"; exit 0 }
        $rows | Select-Object id, ts_utc, status, kind, @{n='url';e={if ($_.url.Length -gt 60) { $_.url.Substring(0,57)+'...' } else { $_.url }}} | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }

    'Process' {
        # Phase 1: NOT-YET-IMPLEMENTED stage 2 download. Print plan; do not execute.
        $rows = @(Read-QueueRows | Where-Object { $_.status -eq 'pending' } | Select-Object -First $Limit)
        if ($rows.Count -eq 0) { Write-Host "no pending rows to process"; exit 0 }
        Write-Host "DRY-RUN (Phase 1; download/transcribe/analyze/act not shipped yet)"
        foreach ($r in $rows) {
            $planFor = switch ($r.kind) {
                'github-repo'      { "gh repo clone $($r.url) -> processed/<id>/download/" }
                'github-issue'     { "gh issue view -> processed/<id>/download/issue.md" }
                'github-pr'        { "gh pr view -> processed/<id>/download/pr.md" }
                'github-file'      { "raw download via gh api -> processed/<id>/download/" }
                'github-other'     { "fallback: gh api fetch + save JSON" }
                'instagram-video'  { "stealth-browser open + yt-dlp/instaloader -> processed/<id>/download/*.mp4 + caption.txt" }
                'youtube-video'    { "yt-dlp + whisper transcribe -> processed/<id>/download/*.mp4 + transcript.srt" }
                default            { "generic-url: stealth-browser fetch + readability extract -> processed/<id>/download/page.html + text.txt" }
            }
            Write-Host ("  id={0} kind={1}" -f $r.id, $r.kind)
            Write-Host ("    plan: $planFor")
            Write-Host ("    next: scribe.summarize + classify action (archive | project-fork | doctrine-update | system-update) + OPERATOR-ACTION-QUEUE landing-row")
            Append-Row -Row ([pscustomobject]@{ ts_utc=(Utc-Now); event='process-dryrun'; id=$r.id; kind=$r.kind; plan=$planFor }) -Path $LogPath
        }
        exit 0
    }

    'Status' {
        $rows = Read-QueueRows
        $pending   = @($rows | Where-Object { $_.status -eq 'pending' }).Count
        $processed = @($rows | Where-Object { $_.status -eq 'processed' }).Count
        $total     = $rows.Count
        Write-Host ("link-ingest total={0} pending={1} processed={2}" -f $total, $pending, $processed)
        Write-Host ("  queue: $QueuePath")
        Write-Host ("  log:   $LogPath")
        exit 0
    }
}
