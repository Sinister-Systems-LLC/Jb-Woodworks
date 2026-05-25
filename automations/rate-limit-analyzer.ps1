# Author: RKOJ-ELENO :: 2026-05-24
# rate-limit-analyzer.ps1 — analyze claude-accounts.log + rate-limit-causes.jsonl +
# anthropic-throttle-events.jsonl + spawned-windows.jsonl and produce three reports:
#   -Action Report           : last N days summary (default 7), grouped by account/hour/project
#   -Action OptimalAgentCount: scan history; recommend safe concurrent N per plan_tier
#   -Action LiveMonitor      : watch claude.exe count + warn at plan-tier headroom
#
# Composes with: claude-accounts.ps1 (account state), start-sinister-session.ps1
# (writes the source logs), best-agent-count-per-claude-plan-study-2026-05-24.md
# (doctrine that this script empirically validates).

[CmdletBinding()]
param(
    [ValidateSet('Report','OptimalAgentCount','LiveMonitor')]
    [string]$Action = 'Report',

    [string]$Account = '',

    [int]$Days = 7,

    [int]$IntervalSec = 60,

    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'

$accountsLog   = Join-Path $SanctumRoot '_shared-memory\claude-accounts.log'
$causesJsonl   = Join-Path $SanctumRoot '_shared-memory\rate-limit-causes.jsonl'
$throttleJsonl = Join-Path $SanctumRoot '_shared-memory\anthropic-throttle-events.jsonl'
$incidentsJsonl= Join-Path $SanctumRoot '_shared-memory\eve-incidents.jsonl'
$spawnsJsonl   = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
$accountsJson  = Join-Path $SanctumRoot '_shared-memory\claude-accounts.json'

# ---------------------------------------------------------------------------
# Plan-tier recommendations (composes with best-agent-count study).
# Conservative — leave 20% headroom on documented Anthropic ceilings.
# ---------------------------------------------------------------------------
$script:TierRecommendation = @{
    'pro'    = @{ safe = 1; max = 2;  rationale = 'Claude Pro 5h window is tight; serialize work' }
    'max5'   = @{ safe = 2; max = 3;  rationale = 'Max 5x = ~5x Pro; safe parallel = 2 (headroom)' }
    'max'    = @{ safe = 4; max = 6;  rationale = 'Max 20x = ~20x Pro; safe parallel = 4 with 20% headroom' }
    'max20'  = @{ safe = 4; max = 6;  rationale = 'alias of max' }
    'team'   = @{ safe = 5; max = 8;  rationale = 'Team plan: per-seat; check Anthropic console' }
    'enterprise' = @{ safe = 8; max = 12; rationale = 'Enterprise: per-org contract; verify in console' }
    'unknown'= @{ safe = 2; max = 3;  rationale = 'Unknown tier — conservative default' }
}

function Get-PlanTier {
    param([string]$Name)
    if (-not (Test-Path $accountsJson)) { return 'unknown' }
    try {
        $cfg = Get-Content $accountsJson -Raw | ConvertFrom-Json
        $acct = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
        if ($acct -and $acct.plan_tier) { return $acct.plan_tier.ToLower() }
    } catch {}
    return 'unknown'
}

function Get-RateLimitEvents {
    param([int]$DaysBack = 7)
    $cutoff = (Get-Date).ToUniversalTime().AddDays(-$DaysBack)
    $events = @()

    # Source 1: claude-accounts.log (text format)
    if (Test-Path $accountsLog) {
        $rxRL = '^\[(?<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\]\s+\[INFO\]\s+Mark-AccountRateLimited:\s+''(?<acct>[^'']+)''\s+limited until (?<until>\S+)\s+\((?<dur>\d+)\s*s\)'
        foreach ($line in (Get-Content $accountsLog -ErrorAction SilentlyContinue)) {
            if ($line -match $rxRL) {
                $ts = [datetime]::ParseExact($matches['ts'],'yyyy-MM-ddTHH:mm:ssZ',$null).ToUniversalTime()
                if ($ts -ge $cutoff) {
                    $events += [pscustomobject]@{
                        ts_utc          = $ts
                        source          = 'claude-accounts.log'
                        account         = $matches['acct']
                        retry_after_sec = [int]$matches['dur']
                        project         = ''
                        root_cause      = 'plan_quota'
                    }
                }
            }
        }
    }

    # Source 2: rate-limit-causes.jsonl (new, richer log)
    if (Test-Path $causesJsonl) {
        foreach ($line in (Get-Content $causesJsonl -ErrorAction SilentlyContinue)) {
            $line = $line.Trim()
            if (-not $line) { continue }
            try {
                $row = $line | ConvertFrom-Json
                $ts = [datetime]::Parse($row.ts_utc).ToUniversalTime()
                if ($ts -ge $cutoff) {
                    $events += [pscustomobject]@{
                        ts_utc          = $ts
                        source          = 'rate-limit-causes.jsonl'
                        account         = $row.account_name
                        retry_after_sec = [int]($row.retry_after_seconds | ForEach-Object { if ($_) { $_ } else { 0 } })
                        project         = $row.project_key
                        root_cause      = $row.root_cause_guess
                        concurrent      = $row.concurrent_claude_count
                        spawns_5min     = $row.spawns_in_last_5min
                        spawns_30min    = $row.spawns_in_last_30min
                        plan_tier       = $row.plan_tier
                    }
                }
            } catch {}
        }
    }

    # Source 3: anthropic-throttle-events.jsonl (server throttle, not per-account)
    if (Test-Path $throttleJsonl) {
        foreach ($line in (Get-Content $throttleJsonl -ErrorAction SilentlyContinue)) {
            $line = $line.Trim()
            if (-not $line) { continue }
            try {
                $row = $line | ConvertFrom-Json
                $ts = [datetime]::Parse($row.ts_utc).ToUniversalTime()
                if ($ts -ge $cutoff) {
                    $events += [pscustomobject]@{
                        ts_utc          = $ts
                        source          = 'anthropic-throttle-events.jsonl'
                        account         = $row.account
                        retry_after_sec = 0
                        project         = $row.project
                        root_cause      = 'global_throttle'
                    }
                }
            } catch {}
        }
    }

    return ,$events
}

function Get-Spawns {
    param([int]$DaysBack = 7)
    $cutoff = (Get-Date).ToUniversalTime().AddDays(-$DaysBack)
    $spawns = @()
    if (-not (Test-Path $spawnsJsonl)) { return ,$spawns }
    foreach ($line in (Get-Content $spawnsJsonl -ErrorAction SilentlyContinue)) {
        $line = $line.Trim()
        if (-not $line) { continue }
        try {
            $row = $line | ConvertFrom-Json
            if (-not $row.started) { continue }
            $ts = [datetime]::Parse($row.started).ToUniversalTime()
            if ($ts -ge $cutoff) {
                $spawns += [pscustomobject]@{
                    ts_utc  = $ts
                    pid     = $row.pid
                    agent   = $row.agent
                    project = $row.project
                }
            }
        } catch {}
    }
    return ,$spawns
}

function Get-ConcurrentClaudeCount {
    # Count live claude.exe across the workstation.
    try {
        return @(Get-Process -Name claude -ErrorAction SilentlyContinue).Count
    } catch {
        return 0
    }
}

function Invoke-Report {
    Write-Host ''
    Write-Host "=== rate-limit-analyzer :: Report (last $Days day(s)) ===" -ForegroundColor Cyan
    Write-Host ''
    $events = Get-RateLimitEvents -DaysBack $Days
    $spawns = Get-Spawns -DaysBack $Days

    Write-Host ("Total rate-limit events: {0}" -f $events.Count) -ForegroundColor Yellow
    Write-Host ("Total spawns:            {0}" -f $spawns.Count) -ForegroundColor Yellow
    if ($spawns.Count -gt 0) {
        $rate = [math]::Round(($events.Count / [math]::Max(1,$spawns.Count)) * 100, 2)
        Write-Host ("Rate-limit rate:         {0}% (events/spawns)" -f $rate)
    }
    Write-Host ''

    if ($events.Count -eq 0) {
        Write-Host '  (no events in window)' -ForegroundColor DarkGray
        Write-Host ''
        return
    }

    # By account
    Write-Host '-- By account --' -ForegroundColor Cyan
    $events | Group-Object account | Sort-Object Count -Descending | ForEach-Object {
        Write-Host ("  {0,-20} {1,4}" -f $_.Name, $_.Count)
    }
    Write-Host ''

    # By hour-of-day
    Write-Host '-- By hour-of-day (UTC) --' -ForegroundColor Cyan
    $events | Group-Object { $_.ts_utc.Hour } | Sort-Object Name | ForEach-Object {
        $bar = '#' * [math]::Min(40, $_.Count)
        Write-Host ("  {0,2}:00  {1,4}  {2}" -f $_.Name, $_.Count, $bar)
    }
    Write-Host ''

    # By project (only rows that have one)
    $proj = $events | Where-Object { $_.project } | Group-Object project | Sort-Object Count -Descending
    if ($proj) {
        Write-Host '-- By project --' -ForegroundColor Cyan
        $proj | ForEach-Object { Write-Host ("  {0,-25} {1,4}" -f $_.Name, $_.Count) }
        Write-Host ''
    }

    # By root cause
    $rc = $events | Where-Object { $_.root_cause } | Group-Object root_cause | Sort-Object Count -Descending
    if ($rc) {
        Write-Host '-- By root-cause guess --' -ForegroundColor Cyan
        $rc | ForEach-Object { Write-Host ("  {0,-20} {1,4}" -f $_.Name, $_.Count) }
        Write-Host ''
    }

    # By source file
    Write-Host '-- By source log --' -ForegroundColor Cyan
    $events | Group-Object source | Sort-Object Count -Descending | ForEach-Object {
        Write-Host ("  {0,-32} {1,4}" -f $_.Name, $_.Count)
    }
    Write-Host ''
}

function Invoke-OptimalAgentCount {
    Write-Host ''
    Write-Host "=== rate-limit-analyzer :: OptimalAgentCount ===" -ForegroundColor Cyan
    Write-Host ''

    if (-not $Account) {
        # Iterate every account
        if (Test-Path $accountsJson) {
            $cfg = Get-Content $accountsJson -Raw | ConvertFrom-Json
            foreach ($a in $cfg.accounts) {
                if ($a.enabled) {
                    Compute-OptimalForAccount -AccountName $a.name -Tier $a.plan_tier
                }
            }
        } else {
            Write-Host '  (claude-accounts.json missing — nothing to scan)' -ForegroundColor Yellow
        }
        return
    }
    $tier = Get-PlanTier -Name $Account
    Compute-OptimalForAccount -AccountName $Account -Tier $tier
}

function Compute-OptimalForAccount {
    param([string]$AccountName, [string]$Tier)
    $tierKey = if ($Tier) { $Tier.ToLower() } else { 'unknown' }
    if (-not $script:TierRecommendation.ContainsKey($tierKey)) { $tierKey = 'unknown' }
    $rec = $script:TierRecommendation[$tierKey]

    Write-Host ("-- Account '{0}' (tier={1}) --" -f $AccountName, $tierKey) -ForegroundColor Cyan

    $events = Get-RateLimitEvents -DaysBack $Days | Where-Object { $_.account -eq $AccountName }
    $spawns = Get-Spawns -DaysBack $Days

    # For each 429, compute concurrent claude.exe count at time-of-event
    # (using spawn history as best-effort proxy — counts spawns active within 5min).
    $concurrentAtEvent = @()
    foreach ($e in $events) {
        if ($null -ne $e.concurrent -and $e.concurrent -ne '') {
            # Use the actual count we logged
            $concurrentAtEvent += [int]$e.concurrent
        } else {
            # Approximate from spawn history (spawns within +/- 5 min)
            $window = $spawns | Where-Object {
                ($_.ts_utc -ge $e.ts_utc.AddMinutes(-5)) -and ($_.ts_utc -le $e.ts_utc)
            }
            if ($window) { $concurrentAtEvent += $window.Count }
        }
    }

    if ($concurrentAtEvent.Count -gt 0) {
        $avg = [math]::Round(($concurrentAtEvent | Measure-Object -Average).Average, 1)
        $max = ($concurrentAtEvent | Measure-Object -Maximum).Maximum
        $min = ($concurrentAtEvent | Measure-Object -Minimum).Minimum
        Write-Host ("  Empirical: {0} rate-limit events; concurrent-at-event avg={1} min={2} max={3}" -f $events.Count, $avg, $min, $max)
    } else {
        Write-Host ("  Empirical: {0} rate-limit events (no concurrent data captured yet)" -f $events.Count)
    }

    Write-Host ("  Recommended SAFE concurrent: {0}" -f $rec.safe) -ForegroundColor Green
    Write-Host ("  Recommended MAX  concurrent: {0}" -f $rec.max) -ForegroundColor Yellow
    Write-Host ("  Rationale: {0}" -f $rec.rationale) -ForegroundColor DarkGray
    Write-Host ''
}

function Invoke-LiveMonitor {
    Write-Host ''
    Write-Host "=== rate-limit-analyzer :: LiveMonitor (interval ${IntervalSec}s) ===" -ForegroundColor Cyan
    Write-Host '  Press Ctrl+C to stop.' -ForegroundColor DarkGray
    Write-Host ''

    # Tier ceiling = max recommended across enabled accounts
    $tierCeiling = 6
    if (Test-Path $accountsJson) {
        $cfg = Get-Content $accountsJson -Raw | ConvertFrom-Json
        $enabledTiers = $cfg.accounts | Where-Object { $_.enabled } | ForEach-Object {
            $t = if ($_.plan_tier) { $_.plan_tier.ToLower() } else { 'unknown' }
            if (-not $script:TierRecommendation.ContainsKey($t)) { $t = 'unknown' }
            $script:TierRecommendation[$t].max
        }
        if ($enabledTiers) { $tierCeiling = ($enabledTiers | Measure-Object -Sum).Sum }
    }
    $warnAt = [math]::Floor($tierCeiling * 0.8)

    while ($true) {
        $live = Get-ConcurrentClaudeCount
        $ts = (Get-Date).ToString('HH:mm:ss')
        $tag = '[OK]'
        $color = 'Green'
        if ($live -ge $tierCeiling) { $tag = '[OVER]'; $color = 'Red' }
        elseif ($live -ge $warnAt)  { $tag = '[WARN]'; $color = 'Yellow' }
        Write-Host ("[{0}] {1,-6} live claude.exe = {2,2}  (warn>={3}, ceiling={4})" -f $ts, $tag, $live, $warnAt, $tierCeiling) -ForegroundColor $color
        Start-Sleep -Seconds $IntervalSec
    }
}

switch ($Action) {
    'Report'            { Invoke-Report }
    'OptimalAgentCount' { Invoke-OptimalAgentCount }
    'LiveMonitor'       { Invoke-LiveMonitor }
}
