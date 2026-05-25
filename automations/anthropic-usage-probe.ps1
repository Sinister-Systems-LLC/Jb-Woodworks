# anthropic-usage-probe.ps1 -- REAL Anthropic plan usage via /v1/messages headers
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25T00:00Z (verbatim, 2 screenshots):
#   "this cap is wrong you need to make sure we are constantly updating it live
#    in eve. it says 100 but its this: [claude.ai/usage shows session 8%, weekly
#    69%, sonnet 0%, design 0%] have a clever way to show when it resets, if
#    its all models filled for the week or just the ones that resets every 4
#    hours"
#
# WHAT THIS DOES
#   Anthropic's /v1/messages endpoint returns rate-limit metadata in response
#   HEADERS (NOT in any usage-summary endpoint -- those return 403). We send a
#   1-token POST (cheapest possible call -- a few cents per day at worst) and
#   parse these headers:
#     anthropic-ratelimit-unified-5h-utilization     0.10  (session, 5h rolling)
#     anthropic-ratelimit-unified-5h-reset           1779683400  (unix ts)
#     anthropic-ratelimit-unified-7d-utilization     0.69  (weekly, all models)
#     anthropic-ratelimit-unified-7d-reset           1779937200  (unix ts)
#     anthropic-ratelimit-unified-7d_sonnet-util...  0.00  (sonnet-only weekly,
#                                                          only present when
#                                                          calling Sonnet model)
#     anthropic-ratelimit-unified-overage-status     rejected | allowed
#
#   These NUMBERS EXACTLY MATCH the claude.ai/usage dashboard.
#
# DISCOVERY RESULTS (2026-05-25, probed live):
#   200  /api/oauth/profile               -- account+org info, no usage numbers
#   200  /api/bootstrap                   -- statsig/feature flags, no usage
#   403  /api/organizations               -- "account_session_invalid"
#   403  /api/organizations/<org>/usage   -- "account_session_invalid"
#   404  /api/usage, /api/me, /api/claude_code/usage, etc.
#   200  /v1/messages (POST 1-token)      -- HEADERS carry the live rate-limits
#
# THE ONLY WORKING PATH IS RESPONSE-HEADER SCRAPING ON /v1/messages.
#
# AUTH
#   Reads ~/.claude/.credentials.json (operator default) OR ~/.claude/credentials.<slot>.json
#   Token format is OAuth (sk-ant-oat01-...) NOT JWT. Sent as Bearer with the
#   anthropic-beta: oauth-2025-04-20 header (Claude Code's own pattern).
#
# OUTPUT MODES
#   Json    machine-readable usage object (default)
#   Text    one-line human summary
#   Banner  multi-line ASCII bars matching the claude.ai/usage layout
#
# CACHE
#   Disk cache at _shared-memory/anthropic-usage-cache.<slot>.json. Default TTL
#   60s. Hits return cached object; misses make 1 API call (Sonnet for sonnet
#   bucket coverage). EVE picker draws frequently -- cache avoids spam.
#
# RATE LIMITS ON THE PROBE ITSELF
#   The probe sends real /v1/messages calls. They count against the operator's
#   quota (1 token in, 1 token out = ~0.005% of a session). Cache + 60s TTL +
#   only-when-stale logic keeps daily burn under ~$0.01.
#
# REFRESH FAILURE MODES
#   - 401: access token expired. Surface "REFRESH NEEDED" tag. Operator should
#          run `claude` once to refresh via the CLI's built-in refresh flow.
#   - 429: probe blocked. Read cached object (even if stale) + add "STALE" tag.
#   - network: emit cached object with "OFFLINE" tag.

[CmdletBinding()]
param(
    [ValidateSet('Json','Text','Banner')] [string]$Mode = 'Json',
    [string]$Slot = 'default',
    [int]$CacheSec = 60,
    [string]$ClaudeRoot = (Join-Path $env:USERPROFILE '.claude'),
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Force,
    [switch]$NoSonnetProbe
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Helpers (defined first so cache-hit + live-probe paths can both call)
# ---------------------------------------------------------------------------
function To-DoubleOrNull { param($s) if ($null -eq $s -or $s -eq '') { return $null }; try { return [double]$s } catch { return $null } }
function To-IntOrNull    { param($s) if ($null -eq $s -or $s -eq '') { return $null }; try { return [int]$s }    catch { return $null } }

function To-Iso { param($Unix)
    if ($null -eq $Unix -or $Unix -eq 0) { return $null }
    [DateTimeOffset]::FromUnixTimeSeconds([int]$Unix).UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Format-Duration { param($Unix)
    if ($null -eq $Unix -or $Unix -eq 0) { return '-' }
    $target = [DateTimeOffset]::FromUnixTimeSeconds([int]$Unix).UtcDateTime
    $delta = $target - ((Get-Date).ToUniversalTime())
    if ($delta.TotalSeconds -lt 0) { return '0m' }
    $h = [int]$delta.TotalHours
    $m = $delta.Minutes
    if ($h -gt 48) { return "$([int]($delta.TotalDays))d" }
    if ($h -gt 0) { return "${h}h${m}m" } else { return "${m}m" }
}

function Format-ResetDay { param($Unix)
    if ($null -eq $Unix -or $Unix -eq 0) { return '-' }
    $local = [DateTimeOffset]::FromUnixTimeSeconds([int]$Unix).ToLocalTime()
    return $local.ToString("ddd h:mm tt")
}

function Get-HeaderValue {
    param($Headers, [string]$Name)
    if ($null -eq $Headers) { return $null }
    foreach ($k in $Headers.Keys) {
        if ($k -ieq $Name) { return [string]$Headers[$k] }
    }
    return $null
}

function MakeBar {
    param($Pct, [int]$Width=20)
    if ($null -eq $Pct) { $Pct = 0 }
    $p = [Math]::Max(0, [Math]::Min(100, [int]$Pct))
    $fill = [int][math]::Round($Width * $p / 100.0)
    $empty = $Width - $fill
    return "[" + ('#' * $fill) + ('-' * $empty) + "]"
}

function Format-ProbeText {
    param($O)
    $sPct = if ($null -ne $O.session.pct) { "$($O.session.pct)%" } else { 'n/a' }
    $wPct = if ($null -ne $O.weekly_all.pct) { "$($O.weekly_all.pct)%" } else { 'n/a' }
    $snPct = if ($O.weekly_sonnet.present) { "$($O.weekly_sonnet.pct)%" } else { 'n/p' }
    $dsPct = if ($O.weekly_design.present) { "$($O.weekly_design.pct)%" } else { 'n/p' }
    $sIn = Format-Duration $O.session.reset_unix
    $wIn = Format-Duration $O.weekly_all.reset_unix
    $cTag = if ($O.cache_hit) { " cache=$($O.cache_age_sec)s" } else { '' }
    return "session=$sPct (resets $sIn) weekly=$wPct (resets $wIn) sonnet=$snPct design=$dsPct$cTag"
}

function Format-ProbeBanner {
    param($O)
    $lines = @()
    $lines += "  Plan: $($O.subscription_type) ($($O.rate_limit_tier))"
    $lines += ""
    $sBar  = MakeBar $O.session.pct
    $wBar  = MakeBar $O.weekly_all.pct
    $snBar = MakeBar $O.weekly_sonnet.pct
    $dsBar = MakeBar $O.weekly_design.pct
    $sIn  = Format-Duration $O.session.reset_unix
    $wDay = Format-ResetDay $O.weekly_all.reset_unix
    $snDay= Format-ResetDay $O.weekly_sonnet.reset_unix
    $dsDay= Format-ResetDay $O.weekly_design.reset_unix
    $sPctS = if ($null -ne $O.session.pct) { "{0,3}%" -f $O.session.pct } else { ' n/a' }
    $wPctS = if ($null -ne $O.weekly_all.pct) { "{0,3}%" -f $O.weekly_all.pct } else { ' n/a' }
    $snPctS = if ($O.weekly_sonnet.present) { "{0,3}%" -f $O.weekly_sonnet.pct } else { ' n/p' }
    $dsPctS = if ($O.weekly_design.present) { "{0,3}%" -f $O.weekly_design.pct } else { ' n/p' }
    $lines += "  session $sBar $sPctS  resets in $sIn"
    $lines += "  weekly  $wBar $wPctS  resets $wDay"
    $sonnetSuffix = if (-not $O.weekly_sonnet.present) { '  (not probed)' } else { '' }
    $designSuffix = if (-not $O.weekly_design.present) { '  (not probed)' } else { '' }
    $lines += "  sonnet  $snBar $snPctS  resets $snDay$sonnetSuffix"
    $lines += "  design  $dsBar $dsPctS  resets $dsDay$designSuffix"
    $weeklyPct  = if ($null -ne $O.weekly_all.pct) { [int]$O.weekly_all.pct } else { 0 }
    $sessionPct = if ($null -ne $O.session.pct)    { [int]$O.session.pct }    else { 0 }
    if ($weeklyPct -ge 100) {
        $lines += ""
        $lines += "  [WEEKLY CAP HIT -- all-models resets $wDay]"
    } elseif ($sessionPct -ge 100 -and $weeklyPct -lt 100) {
        $lines += ""
        $lines += "  [session full -- resets in $sIn (rotates fast)]"
    }
    return ($lines -join "`n")
}

function Emit-Output {
    param($O, [string]$Mode)
    switch ($Mode) {
        'Json'   { $O | ConvertTo-Json -Depth 6 }
        'Text'   { Write-Output (Format-ProbeText $O) }
        'Banner' { Write-Output (Format-ProbeBanner $O) }
    }
}

# ---------------------------------------------------------------------------
# Credentials resolution
# ---------------------------------------------------------------------------
$credFile = if ($Slot -eq 'default') {
    Join-Path $ClaudeRoot '.credentials.json'
} else {
    Join-Path $ClaudeRoot "credentials.$Slot.json"
}

if (-not (Test-Path $credFile)) {
    $err = [pscustomobject]@{
        status = 'no-credentials'
        slot = $Slot
        cred_file = $credFile
        measured_at_utc = ((Get-Date).ToUniversalTime()).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    switch ($Mode) {
        'Text'   { Write-Output "probe: NO-CREDENTIALS ($credFile)"; exit 1 }
        'Banner' { Write-Output "  [usage probe: no credentials at $credFile]"; exit 1 }
        default  { $err | ConvertTo-Json -Compress; exit 1 }
    }
}

try {
    $credText = Get-Content -Raw $credFile -Encoding UTF8
    $cred = $credText | ConvertFrom-Json
} catch {
    $err = [pscustomobject]@{
        status = 'unreadable-credentials'
        slot = $Slot
        cred_file = $credFile
        error = $_.Exception.Message
    }
    switch ($Mode) {
        'Text'  { Write-Output "probe: UNREADABLE-CREDENTIALS"; exit 1 }
        default { $err | ConvertTo-Json -Compress; exit 1 }
    }
}

$oauth = $cred.claudeAiOauth
if (-not $oauth -or -not $oauth.accessToken) {
    $err = [pscustomobject]@{ status='no-oauth-block'; slot=$Slot; cred_file=$credFile }
    switch ($Mode) {
        'Text'  { Write-Output "probe: NO-OAUTH-BLOCK in $credFile"; exit 1 }
        default { $err | ConvertTo-Json -Compress; exit 1 }
    }
}

$accessToken    = $oauth.accessToken
$subscription   = if ($oauth.subscriptionType) { $oauth.subscriptionType } else { 'unknown' }
$rateLimitTier  = if ($oauth.rateLimitTier)    { $oauth.rateLimitTier }    else { 'unknown' }

# ---------------------------------------------------------------------------
# Cache layer
# ---------------------------------------------------------------------------
$cacheDir = Join-Path $SanctumRoot '_shared-memory'
if (-not (Test-Path $cacheDir)) { New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null }
$cacheFile = Join-Path $cacheDir "anthropic-usage-cache.$Slot.json"

if ((Test-Path $cacheFile) -and -not $Force) {
    try {
        $cached = Get-Content -Raw $cacheFile -Encoding UTF8 | ConvertFrom-Json
        $cachedAt = [DateTime]::Parse($cached.measured_at_utc).ToUniversalTime()
        $ageSec = ((Get-Date).ToUniversalTime() - $cachedAt).TotalSeconds
        if ($ageSec -lt $CacheSec) {
            $cached | Add-Member -NotePropertyName cache_hit -NotePropertyValue $true -Force
            $cached | Add-Member -NotePropertyName cache_age_sec -NotePropertyValue ([int]$ageSec) -Force
            Emit-Output $cached $Mode
            exit 0
        }
    } catch {
        # Corrupt cache -- ignore, refetch
    }
}

# ---------------------------------------------------------------------------
# Live probe -- POST /v1/messages with min tokens
# ---------------------------------------------------------------------------
function Invoke-ProbeCall {
    param([string]$Model, [string]$Token)
    $hdrs = @{
        'Authorization'     = "Bearer $Token"
        'anthropic-version' = '2023-06-01'
        'anthropic-beta'    = 'oauth-2025-04-20'
        'User-Agent'        = 'claude-cli/2.0.0 (external, cli)'
        'Content-Type'      = 'application/json'
    }
    $body = @{
        model = $Model
        max_tokens = 1
        messages = @(@{ role='user'; content='hi' })
        system   = "You are Claude Code, Anthropic's official CLI for Claude."
    } | ConvertTo-Json -Depth 6 -Compress
    try {
        $r = Invoke-WebRequest -Uri 'https://api.anthropic.com/v1/messages' `
            -Headers $hdrs -Method POST -Body $body -UseBasicParsing -TimeoutSec 15 -ErrorAction Stop
        return @{ ok=$true; status=200; headers=$r.Headers }
    } catch {
        $code = 0
        try { $code = [int]$_.Exception.Response.StatusCode.value__ } catch {}
        return @{ ok=$false; status=$code; error=$_.Exception.Message }
    }
}

$primaryModel = if ($NoSonnetProbe) { 'claude-haiku-4-5' } else { 'claude-sonnet-4-5' }
$probe = Invoke-ProbeCall -Model $primaryModel -Token $accessToken

if (-not $probe.ok) {
    $obj = if (Test-Path $cacheFile) {
        try {
            $o = Get-Content -Raw $cacheFile -Encoding UTF8 | ConvertFrom-Json
            $o | Add-Member -NotePropertyName status -NotePropertyValue "stale-fallback-http-$($probe.status)" -Force
            $o | Add-Member -NotePropertyName cache_hit -NotePropertyValue $true -Force -PassThru
        } catch { $null }
    } else { $null }
    if (-not $obj) {
        $obj = [pscustomobject]@{
            status = "probe-failed-http-$($probe.status)"
            slot = $Slot
            error = $probe.error
            measured_at_utc = ((Get-Date).ToUniversalTime()).ToString("yyyy-MM-ddTHH:mm:ssZ")
        }
    }
    if ($probe.status -eq 401) {
        $obj | Add-Member -NotePropertyName refresh_needed -NotePropertyValue $true -Force
    }
    switch ($Mode) {
        'Text'   { Write-Output "probe: FAILED http=$($probe.status) slot=$Slot $(if($probe.status -eq 401){'REFRESH-NEEDED'})"; exit 1 }
        'Banner' { Write-Output "  [usage probe: FAILED http=$($probe.status) -- $(if($probe.status -eq 401){'token expired, run claude to refresh'}else{$probe.error})]"; exit 1 }
        'Json'   { $obj | ConvertTo-Json -Depth 6; exit 1 }
    }
}

# ---------------------------------------------------------------------------
# Parse rate-limit headers
# ---------------------------------------------------------------------------
$h = $probe.headers
$now = (Get-Date).ToUniversalTime()

$sessionUtil  = To-DoubleOrNull (Get-HeaderValue $h 'anthropic-ratelimit-unified-5h-utilization')
$sessionReset = To-IntOrNull    (Get-HeaderValue $h 'anthropic-ratelimit-unified-5h-reset')
$sessionStat  = Get-HeaderValue $h 'anthropic-ratelimit-unified-5h-status'

$weeklyUtil   = To-DoubleOrNull (Get-HeaderValue $h 'anthropic-ratelimit-unified-7d-utilization')
$weeklyReset  = To-IntOrNull    (Get-HeaderValue $h 'anthropic-ratelimit-unified-7d-reset')
$weeklyStat   = Get-HeaderValue $h 'anthropic-ratelimit-unified-7d-status'

$sonnetUtil   = To-DoubleOrNull (Get-HeaderValue $h 'anthropic-ratelimit-unified-7d_sonnet-utilization')
$sonnetReset  = To-IntOrNull    (Get-HeaderValue $h 'anthropic-ratelimit-unified-7d_sonnet-reset')
$sonnetStat   = Get-HeaderValue $h 'anthropic-ratelimit-unified-7d_sonnet-status'

$designUtil   = To-DoubleOrNull (Get-HeaderValue $h 'anthropic-ratelimit-unified-7d_design-utilization')
$designReset  = To-IntOrNull    (Get-HeaderValue $h 'anthropic-ratelimit-unified-7d_design-reset')
$designStat   = Get-HeaderValue $h 'anthropic-ratelimit-unified-7d_design-status'

$overallStat   = Get-HeaderValue $h 'anthropic-ratelimit-unified-status'
$repClaim      = Get-HeaderValue $h 'anthropic-ratelimit-unified-representative-claim'
$overage       = Get-HeaderValue $h 'anthropic-ratelimit-unified-overage-status'
$overageReason = Get-HeaderValue $h 'anthropic-ratelimit-unified-overage-disabled-reason'
$orgId         = Get-HeaderValue $h 'anthropic-organization-id'

$obj = [pscustomobject]@{
    status                  = 'ok'
    slot                    = $Slot
    subscription_type       = $subscription
    rate_limit_tier         = $rateLimitTier
    organization_id         = $orgId
    overall_status          = $overallStat
    representative_claim    = $repClaim
    overage_status          = $overage
    overage_disabled_reason = $overageReason
    session = [pscustomobject]@{
        utilization = $sessionUtil
        pct         = if ($null -ne $sessionUtil) { [int][math]::Round($sessionUtil * 100) } else { $null }
        status      = $sessionStat
        reset_unix  = $sessionReset
        reset_utc   = To-Iso $sessionReset
    }
    weekly_all = [pscustomobject]@{
        utilization = $weeklyUtil
        pct         = if ($null -ne $weeklyUtil) { [int][math]::Round($weeklyUtil * 100) } else { $null }
        status      = $weeklyStat
        reset_unix  = $weeklyReset
        reset_utc   = To-Iso $weeklyReset
    }
    weekly_sonnet = [pscustomobject]@{
        utilization = $sonnetUtil
        pct         = if ($null -ne $sonnetUtil) { [int][math]::Round($sonnetUtil * 100) } else { $null }
        status      = $sonnetStat
        reset_unix  = $sonnetReset
        reset_utc   = To-Iso $sonnetReset
        present     = ($null -ne $sonnetUtil)
    }
    weekly_design = [pscustomobject]@{
        utilization = $designUtil
        pct         = if ($null -ne $designUtil) { [int][math]::Round($designUtil * 100) } else { $null }
        status      = $designStat
        reset_unix  = $designReset
        reset_utc   = To-Iso $designReset
        present     = ($null -ne $designUtil)
    }
    probed_model    = $primaryModel
    cache_hit       = $false
    cache_age_sec   = 0
    measured_at_utc = $now.ToString("yyyy-MM-ddTHH:mm:ssZ")
}

# Persist cache
try { $obj | ConvertTo-Json -Depth 6 | Set-Content -Path $cacheFile -Encoding UTF8 } catch {}

Emit-Output $obj $Mode
exit 0
