# claude-wrapper.ps1 -- Auto-429-detect wrapper around `claude` CLI
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24 ~23:10Z (verbatim):
#   "this entire round robin needs to be auto. detect the accounts that
#    should be used and what is out of credits etc."
#
# WHAT THIS IS:
#   A drop-in shim. Instead of running `claude <args>`, run
#   `powershell -File claude-wrapper.ps1 -- <args>`. The wrapper:
#     1. Picks the best slot (PickBest, else RotateToNext) and `Use`s it.
#     2. Streams stdout/stderr through, captures a tail buffer for 429 detect.
#     3. On exit, scans for rate-limit signals (HTTP 429, "rate limit reached",
#        JSON {type:rate_limit_error}, "try again at <time>", "weekly usage").
#     4. If a 429 is detected -> parse reset, mark slot limited, rotate, optionally
#        retry (RetryOnRateLimit default ON). If no 429 -> bump success counters.
#
# COMPOSES WITH:
#   automations/claude-oauth-accounts.ps1   -- PickBest / RotateToNext / Use /
#                                              AutoMark429 actions
#   automations/claude-accounts.ps1         -- legacy api-key path still honored
#   automations/oauth-health-poller.ps1     -- writes oauth-slot-health.json which
#                                              PickBest reads
#
# SAFETY:
#   - Never crashes the operator's `claude` session on its own bugs: every
#     wrapper-side error is caught + logged + the original exit code is preserved.
#   - The wrapper does NOT modify the operator's transcript or .credentials.json
#     except via the documented Use/AutoMark429 actions.

[CmdletBinding()]
param(
    # Forward EVERYTHING after `--` to claude. Use the `--` separator to make
    # PS stop parsing -Switches that belong to claude itself. Example:
    #   powershell -File claude-wrapper.ps1 -RetryOnRateLimit -- --print "hello"
    [string]$Slot = '',
    [switch]$NoAutoPick,
    [switch]$NoRetryOnRateLimit,
    [int]$MaxRetries = 1,
    [int]$TailBufferLines = 400,
    [switch]$DryRun,
    [switch]$Quiet,
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$ClaudeArgs
)

$ErrorActionPreference = 'Continue'
$RetryOnRateLimit = -not $NoRetryOnRateLimit

$script:SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
$script:WrapperLog  = Join-Path $script:SanctumRoot '_shared-memory\claude-wrapper.log'
$script:OAuthLib    = Join-Path $script:SanctumRoot 'automations\claude-oauth-accounts.ps1'
$script:HealthFile  = Join-Path $script:SanctumRoot '_shared-memory\oauth-slot-health.json'
$script:AccountsFile= Join-Path $script:SanctumRoot '_shared-memory\claude-accounts.json'

function Write-WrapperLog {
    param([string]$Message, [string]$Level = 'INFO')
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $script:WrapperLog -Value "[$ts] [$Level] $Message" -ErrorAction SilentlyContinue
    } catch {}
}

function Write-Status {
    param([string]$Message, [string]$Color = 'DarkGray')
    if (-not $Quiet) { Write-Host $Message -ForegroundColor $Color }
}

# ---------------------------------------------------------------------------
# 429 detection.
# Returns a hashtable with:
#   detected   = $true | $false
#   retry_after_utc = ISO string or $null
#   weekly     = $true if pattern suggests weekly Max-plan cap
#   raw_match  = the matching line (for log)
# ---------------------------------------------------------------------------
function Detect-RateLimit {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Buffer)
    $result = @{ detected = $false; retry_after_utc = $null; weekly = $false; raw_match = $null }
    if (-not $Buffer) { return $result }

    # Per-pattern check. Order: most-specific first.
    $patterns = @(
        # Direct JSON error type
        @{ rx = '"type"\s*:\s*"rate_limit_error"';                 weekly = $false; tag = 'json-rate_limit_error' },
        @{ rx = '"error"\s*:\s*\{[^}]*"type"\s*:\s*"rate_limit';   weekly = $false; tag = 'json-error-type-rl' },
        # HTTP-style mentions
        @{ rx = '\bHTTP[/ ]?(?:1\.[01] )?429\b';                   weekly = $false; tag = 'http-429' },
        @{ rx = '\b429\b.*(?:Too Many Requests|rate.?limit)';      weekly = $false; tag = '429-too-many' },
        @{ rx = '(?:Too Many Requests).*\b429\b';                  weekly = $false; tag = '429-too-many-2' },
        @{ rx = 'status[^a-z]*429';                                weekly = $false; tag = 'status-429' },
        # Anthropic CLI phrasing
        @{ rx = "you've hit your (?:5-hour |weekly )?usage limit"; weekly = $true;  tag = 'cli-hit-usage' },
        @{ rx = 'usage limit (?:reached|hit|exceeded)';            weekly = $false; tag = 'cli-usage-limit' },
        @{ rx = 'rate limit (?:reached|hit|exceeded)';             weekly = $false; tag = 'cli-rate-limit' },
        @{ rx = 'quota (?:reached|exceeded|exhausted)';            weekly = $false; tag = 'cli-quota' },
        @{ rx = 'weekly (?:usage )?(?:limit|cap|reset)';           weekly = $true;  tag = 'cli-weekly' },
        @{ rx = 'limit (?:will )?reset (?:on |at )';               weekly = $false; tag = 'cli-limit-reset' },
        @{ rx = 'try again (?:in|at|on)\s';                        weekly = $false; tag = 'cli-try-again' }
    )

    foreach ($p in $patterns) {
        $m = [regex]::Match($Buffer, $p.rx, [Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if ($m.Success) {
            $result.detected  = $true
            $result.weekly    = [bool]$p.weekly
            $result.raw_match = ($m.Value.Substring(0, [Math]::Min(160, $m.Value.Length)))
            break
        }
    }
    if (-not $result.detected) { return $result }

    # Try to extract a reset timestamp.
    # 1) ISO timestamp anywhere in the buffer near rate-limit terms.
    $isoRx = '(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)'
    $m1 = [regex]::Match($Buffer, $isoRx)
    if ($m1.Success) {
        try {
            $dt = ([datetime]::Parse($m1.Groups[1].Value)).ToUniversalTime()
            if ($dt -gt (Get-Date).ToUniversalTime() -and $dt -lt (Get-Date).ToUniversalTime().AddDays(14)) {
                $result.retry_after_utc = $dt.ToString('yyyy-MM-ddTHH:mm:ssZ')
            }
        } catch {}
    }

    # 2) "in N (minutes|hours|days)" relative
    if (-not $result.retry_after_utc) {
        $m2 = [regex]::Match($Buffer, '(?:in|after)\s+(\d+)\s*(second|minute|hour|day)s?', 'IgnoreCase')
        if ($m2.Success) {
            $n = [int]$m2.Groups[1].Value
            $unit = $m2.Groups[2].Value.ToLower()
            $secs = switch ($unit) { 'second' { $n } 'minute' { $n * 60 } 'hour' { $n * 3600 } 'day' { $n * 86400 } default { 0 } }
            if ($secs -gt 0) {
                $result.retry_after_utc = (Get-Date).ToUniversalTime().AddSeconds($secs).ToString('yyyy-MM-ddTHH:mm:ssZ')
            }
        }
    }

    # 3) Bare HH:MM (assume today UTC; if past, roll to tomorrow).
    if (-not $result.retry_after_utc) {
        $m3 = [regex]::Match($Buffer, '(?:at|by)\s+(\d{1,2}):(\d{2})\s*(am|pm|AM|PM)?')
        if ($m3.Success) {
            try {
                $hh = [int]$m3.Groups[1].Value
                $mm = [int]$m3.Groups[2].Value
                $ampm = $m3.Groups[3].Value.ToLower()
                if ($ampm -eq 'pm' -and $hh -lt 12) { $hh += 12 }
                if ($ampm -eq 'am' -and $hh -eq 12) { $hh = 0 }
                $now = (Get-Date).ToUniversalTime()
                $tgt = [datetime]::new($now.Year, $now.Month, $now.Day, $hh, $mm, 0, [DateTimeKind]::Utc)
                if ($tgt -lt $now) { $tgt = $tgt.AddDays(1) }
                $result.retry_after_utc = $tgt.ToString('yyyy-MM-ddTHH:mm:ssZ')
            } catch {}
        }
    }

    # 4) Default fallback: 5h from now (Max plan 5h window).
    if (-not $result.retry_after_utc) {
        $hrs = if ($result.weekly) { 168 } else { 5 }
        $result.retry_after_utc = (Get-Date).ToUniversalTime().AddHours($hrs).ToString('yyyy-MM-ddTHH:mm:ssZ')
    }

    # If reset > 24h out, treat as weekly cap (Max plan weekly reset).
    try {
        $resetDt = [datetime]::Parse($result.retry_after_utc).ToUniversalTime()
        if (($resetDt - (Get-Date).ToUniversalTime()).TotalHours -gt 24) { $result.weekly = $true }
    } catch {}

    return $result
}

# ---------------------------------------------------------------------------
# Slot picker: prefer PickBest (health-poller-aware), fall back to RotateToNext.
# Returns the slot name actually activated, or $null on failure.
# ---------------------------------------------------------------------------
function Pick-And-Activate-Slot {
    [CmdletBinding()]
    param([string]$ForceSlot = '')
    if ($ForceSlot) {
        Write-Status "[wrapper] -Slot $ForceSlot supplied; activating directly." 'DarkGray'
        $useOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:OAuthLib -Action Use -Name $ForceSlot 2>&1
        if ($LASTEXITCODE -eq 0 -or $useOut -match '\[oauth-use\] OK') { return $ForceSlot }
        return $null
    }
    if ($NoAutoPick) {
        Write-Status "[wrapper] -NoAutoPick set; using whatever slot is currently active." 'DarkGray'
        $activeOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:OAuthLib -Action Active 2>&1
        $m = [regex]::Match([string]$activeOut, "slot='([^']+)'")
        if ($m.Success) { return $m.Groups[1].Value }
        return $null
    }

    # Try PickBest (added by this PR).
    $best = $null
    try {
        $pickOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:OAuthLib -Action PickBest 2>&1
        # PickBest prints "<slot-name>" on its OWN line on success (followed by INFO/WARN lines).
        # Parse defensively.
        $lines = ($pickOut | Out-String) -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
        foreach ($line in $lines) {
            if ($line -match '^[A-Za-z0-9._\-]+$' -and $line.Length -lt 50) { $best = $line; break }
            if ($line -match "PickBest:\s+([A-Za-z0-9._\-]+)") { $best = $matches[1]; break }
        }
    } catch {}

    if ($best) {
        Write-Status "[wrapper] PickBest -> $best" 'Cyan'
        $useOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:OAuthLib -Action Use -Name $best 2>&1
        if ($LASTEXITCODE -eq 0 -or $useOut -match '\[oauth-use\] OK') { return $best }
        Write-Status "[wrapper] PickBest slot '$best' Use failed; falling back to RotateToNext" 'Yellow'
    }

    $rotateOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:OAuthLib -Action RotateToNext 2>&1
    $m = [regex]::Match([string]$rotateOut, "activated slot='([^']+)'")
    if ($m.Success) {
        Write-Status "[wrapper] RotateToNext -> $($m.Groups[1].Value)" 'Cyan'
        return $m.Groups[1].Value
    }
    Write-Status "[wrapper] RotateToNext returned no slot. Continuing with whatever is currently active." 'Yellow'
    return $null
}

# ---------------------------------------------------------------------------
# Update success counters on clean exit. Best-effort, never throws.
# ---------------------------------------------------------------------------
function Bump-Success {
    [CmdletBinding()]
    param([string]$SlotName)
    if (-not $SlotName) { return }
    try {
        if (-not (Test-Path $script:AccountsFile)) { return }
        $cfg = Get-Content $script:AccountsFile -Raw | ConvertFrom-Json
        $acct = $cfg.accounts | Where-Object { $_.name -eq $SlotName } | Select-Object -First 1
        if (-not $acct) { return }
        $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        if ($acct.PSObject.Properties.Name -contains 'current_sessions')        { $acct.current_sessions        = [int]$acct.current_sessions + 1 }
        if ($acct.PSObject.Properties.Name -contains 'successful_spawns_today') { $acct.successful_spawns_today = [int]$acct.successful_spawns_today + 1 }
        if ($acct.PSObject.Properties.Name -contains 'last_spawn_at_utc')       { $acct.last_spawn_at_utc       = $now }
        else { $acct | Add-Member -MemberType NoteProperty -Name 'last_spawn_at_utc' -Value $now -Force }
        ($cfg | ConvertTo-Json -Depth 10) | Set-Content -Path $script:AccountsFile -Encoding UTF8
        Write-WrapperLog "Bump-Success slot=$SlotName"
    } catch {
        Write-WrapperLog "Bump-Success failed: $($_.Exception.Message)" 'WARN'
    }
}

# ---------------------------------------------------------------------------
# Run claude once, capture exit code, return tail buffer + exit code.
# We use a tee-style approach: stream claude's output to console AND capture
# the LAST N lines into a ring buffer (TailBufferLines).
# ---------------------------------------------------------------------------
function Invoke-Claude-Once {
    [CmdletBinding()]
    param([string[]]$Args)
    $ring = New-Object System.Collections.Generic.Queue[string]
    $maxLines = [Math]::Max(40, $TailBufferLines)
    $exit = 1

    if ($DryRun) {
        Write-Status "[wrapper] DRY-RUN: would invoke: claude $($Args -join ' ')" 'Yellow'
        return @{ exit = 0; tail = '' }
    }

    # Resolve claude command path (operator-supplied default = 'claude' on PATH).
    $claudeExe = if ($env:SINISTER_CLAUDE_EXE) { $env:SINISTER_CLAUDE_EXE } else { 'claude' }

    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $claudeExe
        foreach ($a in $Args) { $psi.ArgumentList.Add($a) }
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.UseShellExecute        = $false
        $psi.CreateNoWindow         = $false

        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $psi
        $outEvent = Register-ObjectEvent -InputObject $p -EventName OutputDataReceived -Action {
            if ($Event.SourceEventArgs.Data) {
                $line = $Event.SourceEventArgs.Data
                [Console]::WriteLine($line)
                $q = $Event.MessageData
                $q.Enqueue($line)
                while ($q.Count -gt 600) { [void]$q.Dequeue() }
            }
        } -MessageData $ring
        $errEvent = Register-ObjectEvent -InputObject $p -EventName ErrorDataReceived -Action {
            if ($Event.SourceEventArgs.Data) {
                $line = $Event.SourceEventArgs.Data
                [Console]::Error.WriteLine($line)
                $q = $Event.MessageData
                $q.Enqueue($line)
                while ($q.Count -gt 600) { [void]$q.Dequeue() }
            }
        } -MessageData $ring

        $null = $p.Start()
        $p.BeginOutputReadLine()
        $p.BeginErrorReadLine()
        $p.WaitForExit()
        # Drain residual events.
        Start-Sleep -Milliseconds 150
        Unregister-Event -SourceIdentifier $outEvent.Name -ErrorAction SilentlyContinue
        Unregister-Event -SourceIdentifier $errEvent.Name -ErrorAction SilentlyContinue
        $exit = $p.ExitCode
    } catch {
        Write-WrapperLog "Invoke-Claude-Once exception: $($_.Exception.Message)" 'ERROR'
        $exit = 99
    }

    $tail = ($ring.ToArray() -join "`n")
    # Cap tail to last N lines to keep regex cheap.
    $lines = $tail -split "`n"
    if ($lines.Count -gt $maxLines) {
        $tail = ($lines[($lines.Count - $maxLines)..($lines.Count - 1)] -join "`n")
    }
    return @{ exit = $exit; tail = $tail }
}

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if (-not (Test-Path $script:OAuthLib)) {
    Write-Host "[wrapper] FAIL claude-oauth-accounts.ps1 missing at $script:OAuthLib" -ForegroundColor Red
    exit 2
}

$activeSlot = Pick-And-Activate-Slot -ForceSlot $Slot
Write-WrapperLog "MAIN: activeSlot=$activeSlot args='$($ClaudeArgs -join ' ')'"

$attempt = 0
$lastExit = 1
while ($true) {
    $attempt++
    Write-Status "[wrapper] attempt $attempt / $($MaxRetries + 1)  slot=$activeSlot" 'DarkGray'
    $r = Invoke-Claude-Once -Args $ClaudeArgs
    $lastExit = $r.exit
    $rl = Detect-RateLimit -Buffer $r.tail

    if (-not $rl.detected) {
        Write-WrapperLog "MAIN: clean exit code=$lastExit slot=$activeSlot"
        Bump-Success -SlotName $activeSlot
        break
    }

    # Rate limited.
    Write-Host ""
    Write-Host "  [AUTO-429] slot=$activeSlot rate-limited (weekly=$($rl.weekly)) until=$($rl.retry_after_utc); rotating to next" -ForegroundColor Yellow
    Write-Host "             match: $($rl.raw_match)" -ForegroundColor DarkGray
    Write-WrapperLog "AUTO-429 slot=$activeSlot until=$($rl.retry_after_utc) weekly=$($rl.weekly) match=$($rl.raw_match)" 'WARN'

    # Mark + rotate via the new AutoMark429 action.
    $markArgs = @('-Action','AutoMark429','-Name',$activeSlot,'-RetryAfter',$rl.retry_after_utc)
    if ($rl.weekly) { $markArgs += '-Weekly' }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $script:OAuthLib @markArgs 2>&1 | ForEach-Object { Write-Status $_ 'DarkGray' }

    if (-not $RetryOnRateLimit -or $attempt -gt $MaxRetries) {
        Write-WrapperLog "MAIN: stopping (RetryOnRateLimit=$RetryOnRateLimit attempt=$attempt MaxRetries=$MaxRetries)"
        break
    }

    $nextSlot = Pick-And-Activate-Slot
    if (-not $nextSlot -or $nextSlot -eq $activeSlot) {
        Write-Host "  [AUTO-429] no other healthy slot available; not retrying" -ForegroundColor Yellow
        Write-WrapperLog "MAIN: no rotation candidate; aborting retries"
        break
    }
    $activeSlot = $nextSlot
    Write-Host "  [AUTO-429] rotated to slot=$activeSlot; retrying" -ForegroundColor Cyan
}

exit $lastExit
