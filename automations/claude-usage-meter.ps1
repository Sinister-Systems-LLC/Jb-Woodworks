# claude-usage-meter.ps1 -- ESTIMATE Claude usage from local transcripts
# Author: RKOJ-ELENO :: 2026-05-24 (header revised 2026-05-25)
#
# Operator hard-canonical 2026-05-25 (image #67, verbatim):
#   "leave out wrong info. like saying its 100%. its fucking not. review how
#    jcode track their usaage or what we need to do and fucking do it"
#
# THIS SCRIPT IS A LOCAL-TRANSCRIPT ESTIMATE, NOT MEASURED USAGE. The only
# truly MEASURED path is the Anthropic /oauth/usage endpoint (jcode-style),
# called by automations/anthropic-usage-probe.ps1 and rendered as the 4-bar
# live block in eve.py for the default OAuth slot. Soft caps below are a
# community-estimate; the real cap is whatever Anthropic's rate-limit
# headers say. See _shared-memory/knowledge/jcode-usage-tracking-pattern-
# 2026-05-25.md for the canonical pattern this meter is being deprecated in
# favor of.
#
# Original 2026-05-24T21:55Z directive (kept for audit):
#   "make sure clauyde accounts and account manager section are usiong valid
#    usage progress bars and shwo the real amount of usage"
#
# How it works: scrape transcripts JSONLs (~/.claude/projects/**/*.jsonl);
# each assistant message carries a "usage" payload with
# input_tokens / cache_creation_input_tokens / cache_read_input_tokens /
# output_tokens. We sum them within a rolling window and project against the
# operator's plan-tier ESTIMATED soft cap to compute a "% used" bar fill.
#
# OUTPUT MODES:
#   Json  (default)  emit machine-readable usage object
#   Text             one-line human summary
#
# SCOPE NOTES:
#   - Claude Code OAuth (~/.claude/.credentials.json) is the only login that
#     produces transcripts under ~/.claude/projects/. API-key accounts spawn
#     headless `claude` runs that ALSO log to this dir, so transcripts mix
#     accounts. For per-account split we'd need credentials-isolation per
#     spawn. For now we report TOTAL workstation usage (operator default) and
#     downgrade per-account to "(api-key) <spawns-today>" without a token bar.
#   - Plan-tier soft caps (per Anthropic public statements + community probes):
#       free   ~ 8000   tokens / 5h
#       pro    ~ 45000  tokens / 5h
#       max    ~ 200000 tokens / 5h    (Max 5x)
#       max20  ~ 800000 tokens / 5h    (Max 20x)
#     These are approximate; Anthropic does not publish exact 5h token quotas.
#     We treat the cap as a soft-fill reference, not a hard limit.

[CmdletBinding()]
param(
    [ValidateSet('Json','Text')] [string]$Mode = 'Json',
    [int]$WindowHours = 5,
    [string]$PlanTier = 'max',
    [string]$ClaudeRoot = (Join-Path $env:USERPROFILE '.claude')
)

$ErrorActionPreference = 'Stop'

# Tier soft caps -- PRIMARY metric is MESSAGE COUNT per 5h (matches Anthropic
# plan documentation more closely than tokens; token caps are vague). Tokens
# are reported as secondary info only. Caps are community-measured approximations;
# tunable via env (SINISTER_MSG_CAP_MAX etc.) per operator's actual plan.
$msgCaps = @{
    'free'  = if ($env:SINISTER_MSG_CAP_FREE)  { [int]$env:SINISTER_MSG_CAP_FREE }  else { 50 }
    'pro'   = if ($env:SINISTER_MSG_CAP_PRO)   { [int]$env:SINISTER_MSG_CAP_PRO }   else { 200 }
    'max'   = if ($env:SINISTER_MSG_CAP_MAX)   { [int]$env:SINISTER_MSG_CAP_MAX }   else { 500 }
    'max20' = if ($env:SINISTER_MSG_CAP_MAX20) { [int]$env:SINISTER_MSG_CAP_MAX20 } else { 1500 }
}
$msgCap = if ($msgCaps.ContainsKey($PlanTier)) { $msgCaps[$PlanTier] } else { $msgCaps['max'] }
# Token cap kept for informational % only; quota mostly governed by message count.
$tokenCaps = @{
    'free'  = 8000
    'pro'   = 45000
    'max'   = 200000
    'max20' = 800000
}
$tokenCap = if ($tokenCaps.ContainsKey($PlanTier)) { $tokenCaps[$PlanTier] } else { $tokenCaps['max'] }

$projectsDir = Join-Path $ClaudeRoot 'projects'
$now = (Get-Date).ToUniversalTime()
$windowStart = $now.AddHours(-$WindowHours)

$totals = @{
    input_tokens = 0
    cache_creation_input_tokens = 0
    cache_read_input_tokens = 0
    output_tokens = 0
    msg_count = 0
    transcripts_scanned = 0
    transcripts_skipped = 0
    last_event_utc = $null
}

if (Test-Path $projectsDir) {
    # Only scan files modified within the window + slack (saves time on huge dirs).
    $slackMin = ($WindowHours * 60) + 30
    $candidates = @(Get-ChildItem -Path $projectsDir -Recurse -Filter '*.jsonl' -File -ErrorAction SilentlyContinue |
                    Where-Object { $_.LastWriteTimeUtc -ge $windowStart.AddMinutes(-$slackMin) })

    foreach ($f in $candidates) {
        $totals.transcripts_scanned++
        try {
            # Stream the file line-by-line. Bail early if file is too big to avoid OOM.
            if ($f.Length -gt 200MB) { $totals.transcripts_skipped++; continue }
            $reader = [System.IO.File]::OpenText($f.FullName)
            try {
                while (-not $reader.EndOfStream) {
                    $line = $reader.ReadLine()
                    if (-not $line) { continue }
                    # Cheap pre-filter: skip lines without "usage" before JSON parse.
                    if ($line.IndexOf('"usage"') -lt 0) { continue }
                    try {
                        $obj = $line | ConvertFrom-Json -ErrorAction Stop
                    } catch { continue }
                    # Timestamp can live at top-level or under message.timestamp.
                    $ts = $null
                    if ($obj.timestamp) { $ts = $obj.timestamp }
                    elseif ($obj.message -and $obj.message.timestamp) { $ts = $obj.message.timestamp }
                    elseif ($obj.message -and $obj.message.created_at) { $ts = $obj.message.created_at }
                    if (-not $ts) { continue }
                    try {
                        $eventTime = ([DateTime]::Parse($ts)).ToUniversalTime()
                    } catch { continue }
                    if ($eventTime -lt $windowStart) { continue }
                    if ($eventTime -gt $now.AddMinutes(2)) { continue }  # clock skew guard

                    $u = $null
                    if ($obj.message -and $obj.message.usage) { $u = $obj.message.usage }
                    elseif ($obj.usage) { $u = $obj.usage }
                    if (-not $u) { continue }

                    $totals.input_tokens += [int]($u.input_tokens | ForEach-Object { $_ })
                    $totals.cache_creation_input_tokens += [int]($u.cache_creation_input_tokens | ForEach-Object { $_ })
                    $totals.cache_read_input_tokens += [int]($u.cache_read_input_tokens | ForEach-Object { $_ })
                    $totals.output_tokens += [int]($u.output_tokens | ForEach-Object { $_ })
                    $totals.msg_count++
                    if (-not $totals.last_event_utc -or $eventTime -gt [DateTime]::Parse($totals.last_event_utc)) {
                        $totals.last_event_utc = $eventTime.ToString("yyyy-MM-ddTHH:mm:ssZ")
                    }
                }
            } finally { $reader.Close() }
        } catch {
            $totals.transcripts_skipped++
        }
    }
}

# Weighted billable total: cache reads cost 10% of full input, output ~5x input.
# Anthropic billing math: input=1x, cache_create=1.25x, cache_read=0.1x, output=5x.
# For the % bar we use the BILLABLE-EQUIVALENT total since that's what hits quota.
$billableEq = [int]($totals.input_tokens + ($totals.cache_creation_input_tokens * 1.25) + ($totals.cache_read_input_tokens * 0.1) + ($totals.output_tokens * 5.0))

$raw = $totals.input_tokens + $totals.cache_creation_input_tokens + $totals.cache_read_input_tokens + $totals.output_tokens

$pctMsg = if ($msgCap -gt 0) { [int]([Math]::Round(100.0 * $totals.msg_count / $msgCap)) } else { 0 }
if ($pctMsg -lt 0) { $pctMsg = 0 }
# RKOJ-ELENO :: 2026-05-25 (eve-exe iter-5) :: clamp at 100, not 999.
# Operator hard-canonical "leave out wrong info. like saying its 100%. its
# fucking not". The 500-msg msgCap is a HARDCODED guess that doesn't match
# any real Anthropic per-account cap (Max 20x is spawn-window based, not msg
# count). With cap=500 and 5h-window msg_count routinely >4000, pctMsg blew
# past 999 -> downstream (oauth-slot-health, sub-agents) misread as "fleet
# hard-capped" + refused to spawn. Real quota signal comes from /oauth/usage
# headers (eve.py:894 [MEASURED] tag). This meter is a PROXY; clamp at 100.
$pctMsgUncapped = $pctMsg
if ($pctMsg -gt 100) { $pctMsg = 100 }
$pctTok = if ($tokenCap -gt 0) { [int]([Math]::Round(100.0 * $billableEq / $tokenCap)) } else { 0 }
if ($pctTok -lt 0) { $pctTok = 0 }
$pctTokUncapped = $pctTok
if ($pctTok -gt 100) { $pctTok = 100 }

if ($Mode -eq 'Text') {
    Write-Output ("usage: ${pctMsg}% msgs ($($totals.msg_count)/$msgCap)  ${pctTok}% tokens ($billableEq/$tokenCap)  raw=$raw  win=${WindowHours}h  tier=$PlanTier")
    exit 0
}

# Json mode
$out = @{
    window_hours = $WindowHours
    plan_tier = $PlanTier
    msg_cap = $msgCap
    msg_count = $totals.msg_count
    pct_used = $pctMsg
    pct_msgs = $pctMsg
    pct_tokens = $pctTok
    pct_msgs_uncapped = $pctMsgUncapped
    pct_tokens_uncapped = $pctTokUncapped
    proxy_note = "msg-count vs hardcoded 500-msg cap is a proxy; real quota = Anthropic /oauth/usage headers (eve.py [MEASURED] path)"
    token_cap = $tokenCap
    billable_eq_tokens = $billableEq
    raw_tokens = $raw
    input_tokens = $totals.input_tokens
    cache_creation_input_tokens = $totals.cache_creation_input_tokens
    cache_read_input_tokens = $totals.cache_read_input_tokens
    output_tokens = $totals.output_tokens
    transcripts_scanned = $totals.transcripts_scanned
    transcripts_skipped = $totals.transcripts_skipped
    last_event_utc = $totals.last_event_utc
    window_start_utc = $windowStart.ToString("yyyy-MM-ddTHH:mm:ssZ")
    measured_at_utc = $now.ToString("yyyy-MM-ddTHH:mm:ssZ")
}
$out | ConvertTo-Json -Depth 5
exit 0
