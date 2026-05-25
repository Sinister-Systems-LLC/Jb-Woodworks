# link-download.ps1 -- Phase 2 download stage for drop-link ingest
# Author: RKOJ-ELENO :: 2026-05-24
#
# Doctrine: _shared-memory/knowledge/drop-link-ingest-spec-2026-05-24.md
# Operator hard-canonical 2026-05-24T20:15Z + 20:52Z (keep token use in mind).
#
# Dispatches by classified `kind` (set by link-ingest.ps1 Phase 1) to the right
# downloader. Saves into _shared-memory/inbox/link-ingest/processed/<id>/download/.
# Flips queue row status pending -> processed when done; logs failures.
#
# Per-kind tool:
#   github-repo         gh repo clone --depth 50
#   github-issue        gh api /repos/<o>/<r>/issues/<n>  ->  issue.json
#   github-pr           gh api /repos/<o>/<r>/pulls/<n>   ->  pr.json
#   github-file         curl raw.githubusercontent.com    ->  <basename>
#   github-other        gh api ... (best-effort)          ->  raw.json
#   instagram-video     yt-dlp                            ->  *.mp4 + *.info.json
#   youtube-video       yt-dlp                            ->  *.mp4 + *.info.json
#   generic-url         curl -s -L                        ->  page.html
#
# Hard size caps (defensive against runaway downloads):
#   instagram-video    100 MB
#   youtube-video      200 MB
#   github-repo        500 MB (gh's --depth 50 keeps it bounded)
#   generic-url         10 MB
#
# Actions:
#   Run     -Limit N           process up to N pending rows from queue.jsonl
#   One     -Id <queue-id>     process exactly one row by id
#   Status                     show download stats from log

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [ValidateSet('Run','One','Status')] [string]$Action,
    [int]$Limit = 1,
    [string]$Id = '',
    [int]$TimeoutSec = 120,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$Root      = Join-Path $SanctumRoot '_shared-memory\inbox\link-ingest'
$QueuePath = Join-Path $Root 'queue.jsonl'
$LogPath   = Join-Path $Root 'link-ingest-log.jsonl'
$LockPath  = Join-Path $Root '.queue.lock'
$Processed = Join-Path $Root 'processed'
if (-not (Test-Path $Processed)) { New-Item -ItemType Directory -Path $Processed -Force | Out-Null }

function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Append-Log { param($Row)
    $line = $Row | ConvertTo-Json -Compress -Depth 6
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

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

function Read-Queue {
    if (-not (Test-Path $QueuePath)) { return @() }
    $rows = @()
    foreach ($l in (Get-Content $QueuePath -ErrorAction SilentlyContinue)) {
        if (-not $l -or -not $l.Trim()) { continue }
        try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {}
    }
    return $rows
}
function Write-Queue { param($Rows)
    $tmp = "$QueuePath.tmp"
    $sb = New-Object System.Text.StringBuilder
    foreach ($r in $Rows) { [void]$sb.AppendLine(($r | ConvertTo-Json -Compress -Depth 6)) }
    [System.IO.File]::WriteAllText($tmp, $sb.ToString(), [System.Text.UTF8Encoding]::new($false))
    Move-Item -Path $tmp -Destination $QueuePath -Force
}

function Slug-Of { param([string]$U)
    # Cheap slug from URL host+path
    try {
        $uri = [Uri]$U
        $s = ($uri.Host + $uri.AbsolutePath) -replace '[^a-zA-Z0-9._-]', '_'
        return ($s -replace '_+', '_').TrimEnd('_').ToLower().Substring(0, [Math]::Min(60, $s.Length))
    } catch { return 'unknown' }
}

function Invoke-External { param([string]$Cmd, [string[]]$Args, [string]$OutDir, [int]$Timeout = 120)
    # Runs an external EXE with timeout. Returns @{ ok; stdout; stderr; exitcode }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = $Cmd
    foreach ($a in $Args) { [void]$psi.ArgumentList.Add($a) }
    $psi.WorkingDirectory  = $OutDir
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow  = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $stdOut = New-Object System.Text.StringBuilder
    $stdErr = New-Object System.Text.StringBuilder
    $p.add_OutputDataReceived({ if ($_.Data) { [void]$stdOut.AppendLine($_.Data) } })
    $p.add_ErrorDataReceived({ if ($_.Data) { [void]$stdErr.AppendLine($_.Data) } })
    $p.BeginOutputReadLine(); $p.BeginErrorReadLine()
    if (-not $p.WaitForExit($Timeout * 1000)) {
        try { $p.Kill($true) } catch {}
        return @{ ok=$false; stdout=$stdOut.ToString(); stderr=$stdErr.ToString(); exitcode=-1; reason='timeout' }
    }
    return @{ ok=($p.ExitCode -eq 0); stdout=$stdOut.ToString(); stderr=$stdErr.ToString(); exitcode=$p.ExitCode; reason='' }
}

function Process-Row { param($Row)
    $procDir = Join-Path $Processed ("$($Row.id)-" + (Slug-Of $Row.url))
    $dlDir   = Join-Path $procDir 'download'
    if (-not (Test-Path $dlDir)) { New-Item -ItemType Directory -Path $dlDir -Force | Out-Null }
    [System.IO.File]::WriteAllText((Join-Path $procDir 'source.url'), $Row.url, [System.Text.UTF8Encoding]::new($false))
    Append-Log @{ ts_utc=(Utc-Now); event='download-start'; id=$Row.id; kind=$Row.kind; url=$Row.url; dir=$dlDir }

    $result = @{ ok=$false; reason='unknown-kind' }
    switch ($Row.kind) {
        'github-repo' {
            # RKOJ-ELENO :: 2026-05-24 :: switched from System.Diagnostics.Process to
            # direct `& git` invocation -- the .NET process API loses PATH inheritance for
            # git's child helpers (askpass, credential, etc.) so even `git clone` fails
            # silently (exit=1, stderr empty). Direct invocation uses PowerShell's env.
            $gitPath = Get-Command git -ErrorAction SilentlyContinue
            if (-not $gitPath) { $result = @{ ok=$false; reason='git not found on PATH' }; break }
            $cloneDir = Join-Path $dlDir 'repo'
            if (Test-Path $cloneDir) { Remove-Item -LiteralPath $cloneDir -Recurse -Force -ErrorAction SilentlyContinue }
            # Note: do NOT use 2>&1 here -- PowerShell wraps native stderr as ErrorRecord
            # which sets $? to false and pollutes $LASTEXITCODE. git emits "Cloning into..."
            # on stderr by design. Truth is in the file system: Test-Path .git after.
            $oldEAP = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            try {
                & $gitPath.Source clone --depth 50 $Row.url $cloneDir 2>$null | Out-Null
            } finally {
                $ErrorActionPreference = $oldEAP
            }
            $deposited = (Test-Path (Join-Path $cloneDir '.git'))
            if ($deposited) {
                $result = @{ ok=$true; reason='' }
            } else {
                $result = @{ ok=$false; reason="git clone deposited no .git/ at $cloneDir (check git PATH + url + network)" }
            }
        }
        { $_ -in 'github-issue','github-pr','github-file','github-other' } {
            $ghPath = Get-Command gh -ErrorAction SilentlyContinue
            if (-not $ghPath) { $result = @{ ok=$false; reason='gh CLI not found on PATH' }; break }
            # Extract /owner/repo/(issues|pulls)/N from path
            $apiPath = $Row.path -replace '^/', '' -replace '/pull/', '/pulls/'
            $out = Join-Path $dlDir 'raw.json'
            $r = Invoke-External -Cmd $ghPath.Source -Args @('api', "/repos/$apiPath") -OutDir $dlDir -Timeout 30
            if ($r.ok -and $r.stdout) {
                [System.IO.File]::WriteAllText($out, $r.stdout, [System.Text.UTF8Encoding]::new($false))
                $result = @{ ok=$true; reason='' }
            } else {
                $result = @{ ok=$false; reason="gh api exit=$($r.exitcode) stderr=$($r.stderr -replace '\r?\n', ' ')" }
            }
        }
        { $_ -in 'instagram-video','youtube-video' } {
            $ytPath = Get-Command yt-dlp -ErrorAction SilentlyContinue
            if (-not $ytPath) { $result = @{ ok=$false; reason='yt-dlp not found on PATH' }; break }
            $maxMB = if ($Row.kind -eq 'instagram-video') { 100 } else { 200 }
            $outTpl = Join-Path $dlDir '%(title).80s [%(id)s].%(ext)s'
            $r = Invoke-External -Cmd $ytPath.Source -Args @(
                '--no-warnings', '--no-progress', '--write-info-json',
                '--max-filesize', "${maxMB}M", '-o', $outTpl, $Row.url
            ) -OutDir $dlDir -Timeout $TimeoutSec
            $result = @{ ok=$r.ok; reason=$(if (-not $r.ok) { "yt-dlp exit=$($r.exitcode) stderr=$(($r.stderr -split '\r?\n' | Select-Object -Last 3) -join ' | ')" } else { '' }) }
        }
        'generic-url' {
            $curlPath = Get-Command curl -ErrorAction SilentlyContinue
            if (-not $curlPath) { $result = @{ ok=$false; reason='curl not found on PATH' }; break }
            $out = Join-Path $dlDir 'page.html'
            $r = Invoke-External -Cmd $curlPath.Source -Args @(
                '-s', '-L', '--max-filesize', '10485760', '-A', 'Mozilla/5.0 SinisterIngest/1.0',
                '-o', $out, $Row.url
            ) -OutDir $dlDir -Timeout 30
            $result = @{ ok=$r.ok; reason=$(if (-not $r.ok) { "curl exit=$($r.exitcode)" } else { '' }) }
        }
        default {
            $result = @{ ok=$false; reason="no downloader for kind=$($Row.kind)" }
        }
    }

    Append-Log @{
        ts_utc=(Utc-Now); event=$(if ($result.ok) {'download-ok'} else {'download-fail'})
        id=$Row.id; kind=$Row.kind; dir=$dlDir; reason=$result.reason
    }
    return $result
}

switch ($Action) {

    'Run' {
        $rows = @(Read-Queue | Where-Object { $_.status -eq 'pending' } | Select-Object -First $Limit)
        if ($rows.Count -eq 0) { Write-Host "no pending rows"; exit 0 }
        Write-Host "Processing $($rows.Count) pending row(s) (Limit=$Limit, TimeoutSec=$TimeoutSec)..."
        foreach ($r in $rows) {
            Write-Host ""
            Write-Host ("  id={0} kind={1} url={2}" -f $r.id, $r.kind, $r.url)
            $res = Process-Row $r
            if ($res.ok) {
                Write-Host "    OK"
            } else {
                Write-Host ("    FAIL: " + $res.reason)
            }
            if (-not (Acquire-Lock)) { Write-Host "    (skipped queue update; lock contention)"; continue }
            try {
                $all = Read-Queue
                foreach ($q in $all) {
                    if ($q.id -eq $r.id) {
                        $q | Add-Member -MemberType NoteProperty -Name 'status' -Value (if ($res.ok) { 'processed' } else { 'failed' }) -Force
                        $q | Add-Member -MemberType NoteProperty -Name 'processed_at_utc' -Value (Utc-Now) -Force
                        if (-not $res.ok) { $q | Add-Member -MemberType NoteProperty -Name 'fail_reason' -Value $res.reason -Force }
                    }
                }
                Write-Queue -Rows $all
            } finally { Release-Lock }
        }
        Write-Host ""
        exit 0
    }

    'One' {
        if (-not $Id) { Write-Host "ERR: -Id required"; exit 2 }
        $all = Read-Queue
        $target = $all | Where-Object { $_.id -eq $Id } | Select-Object -First 1
        if (-not $target) { Write-Host "NOTFOUND id=$Id"; exit 1 }
        $res = Process-Row $target
        $msg = if ($res.ok) { "OK" } else { "FAIL: $($res.reason)" }
        Write-Host $msg
        # Flip queue status (parity with Run action) so link-route.ps1 can pick it up.
        if (Acquire-Lock) {
            try {
                $all2 = Read-Queue
                foreach ($q in $all2) {
                    if ($q.id -eq $Id) {
                        $newStatus = if ($res.ok) { 'processed' } else { 'failed' }
                        $q | Add-Member -MemberType NoteProperty -Name 'status' -Value $newStatus -Force
                        $q | Add-Member -MemberType NoteProperty -Name 'processed_at_utc' -Value (Utc-Now) -Force
                        if (-not $res.ok) { $q | Add-Member -MemberType NoteProperty -Name 'fail_reason' -Value $res.reason -Force }
                    }
                }
                Write-Queue -Rows $all2
            } finally { Release-Lock }
        }
        $rc = if ($res.ok) { 0 } else { 1 }
        exit $rc
    }

    'Status' {
        if (-not (Test-Path $LogPath)) { Write-Host "no log yet"; exit 0 }
        $rows = @()
        foreach ($l in (Get-Content $LogPath -ErrorAction SilentlyContinue)) {
            if ($l) { try { $rows += ($l | ConvertFrom-Json -ErrorAction Stop) } catch {} }
        }
        $ok    = @($rows | Where-Object { $_.event -eq 'download-ok' }).Count
        $fail  = @($rows | Where-Object { $_.event -eq 'download-fail' }).Count
        $start = @($rows | Where-Object { $_.event -eq 'download-start' }).Count
        Write-Host ("link-download starts=$start ok=$ok fail=$fail")
        exit 0
    }
}
