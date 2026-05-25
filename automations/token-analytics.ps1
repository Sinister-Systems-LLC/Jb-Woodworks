# token-analytics.ps1 -- Deep token-usage analytics + waste-detection +
#                        recommendations engine for the Sinister fleet.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24 ~23:30Z (verbatim):
#   "in parrallel add to teh account tab a token menu so that we can track
#    all token use and see places where we can improve our token use and
#    make better systems to become more token efficent"
#
# DATA SOURCE: ~/.claude/projects/**/*.jsonl  (Claude Code transcripts).
#   Each line is a message envelope; assistant messages carry a `usage`
#   payload (input_tokens / cache_creation_input_tokens /
#   cache_read_input_tokens / output_tokens) and a `message.model` slug.
#
# REUSES: claude-usage-meter.ps1's parse strategy (stream-line + pre-filter
#         on "usage" before ConvertFrom-Json) -- this script extends it with
#         multi-window + per-project + per-session + per-model breakouts +
#         waste-detection + recommendations. The meter stays the canonical
#         single-window probe used by the live status-bar.
#
# ACTIONS:
#   Summary          (default)  1h/5h/24h/7d windows + raw + billable + cost
#   ByProject                   per-project totals + cache hit ratio + cost
#   BySession                   top 10 sessions (files) by billable-eq
#   ByModel                     group by message.model
#   CacheReport                 per-project cache hit ratio + savings estimate
#   WasteReport                 flag wasteful patterns (low cache, abandoned cache,
#                               context bloat, tool-loop sessions)
#   Recommendations             5-10 prioritized recommendations
#   Json                        machine-readable everything-at-once
#
# COST MODEL (Anthropic billing math, Claude Opus 4.x as the reference rate):
#   input         = 1.00x  ($15 / M tokens for opus, $3 / M for sonnet)
#   cache_create  = 1.25x
#   cache_read    = 0.10x  (so cache_read savings = 0.9 * cache_read)
#   output        = 5.00x  ($75 / M tokens opus, $15 / M sonnet)
# We compute "billable-eq tokens" = input + 1.25*cc + 0.10*cr + 5.0*out so all
# windows + projects can be compared on one scalar. Cost dollar estimates use
# the Opus rate for messages whose model contains "opus" else Sonnet rate.

[CmdletBinding()]
param(
    [ValidateSet('Summary','ByProject','BySession','ByModel','CacheReport','WasteReport','Recommendations','Json')]
    [string]$Action = 'Summary',

    [string]$ClaudeRoot = (Join-Path $env:USERPROFILE '.claude'),

    # Per-action knobs
    [int]$TopN = 10,
    [int]$ContextBloatThresholdTokens = 200000,
    [int]$ToolLoopThresholdMsgs = 100,

    # ASCII-only output (PowerShell unicode-blockdraw doctrine).
    [switch]$NoColor
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Color tokens (ASCII-safe; same palette eve.py uses).
# ---------------------------------------------------------------------------
$useColor = -not $NoColor.IsPresent -and -not $env:NO_COLOR -and $env:TERM -ne 'dumb'
function _c([string]$code) { if ($useColor) { $code } else { '' } }
$PURPLE  = _c "`e[38;5;141m"
$BRIGHTP = _c "`e[38;5;177m"
$DARKP   = _c "`e[38;5;91m"
$WHITE   = _c "`e[97m"
$SOFT    = _c "`e[38;5;245m"
$DIM     = _c "`e[38;5;240m"
$OK      = _c "`e[38;5;46m"
$WARN    = _c "`e[38;5;220m"
$FAIL    = _c "`e[38;5;196m"
$RESET   = _c "`e[0m"
$BOLD    = _c "`e[1m"

function _header([string]$title) {
    Write-Host ""
    Write-Host "  $DARKP---$RESET $WHITE$BOLD$title$RESET $DARKP---$RESET"
    Write-Host ""
}

function _footer([string]$summary) {
    Write-Host ""
    Write-Host "  $DIM---$RESET $SOFT$summary$RESET"
}

# ---------------------------------------------------------------------------
# Project-dir slug -> human path. `D--Sinister-Sanctum` -> `D:\Sinister Sanctum`.
# Heuristic: first 2 chars are drive-letter + dash + dash -> "X:\"; remaining
# dashes are spaces (best-effort; matches Claude Code's dir-naming convention).
# ---------------------------------------------------------------------------
function _humanize_project([string]$slug) {
    if (-not $slug) { return '?' }
    if ($slug.Length -ge 3 -and $slug[1] -eq '-' -and $slug[2] -eq '-') {
        $drive = $slug.Substring(0, 1).ToUpper()
        $rest = $slug.Substring(3) -replace '-', ' '
        return "${drive}:\$rest"
    }
    return $slug -replace '-', ' '
}

# ---------------------------------------------------------------------------
# Core scanner -- single pass over all transcripts, builds per-msg records.
# Returns array of [PSCustomObject]@{ project, session_id, model, ts_utc,
#   input, cache_create, cache_read, output, tools }.
#
# Performance: pre-filters lines on `"usage"` substring before JSON parse;
# bails out of files >200MB; respects $MaxFiles to cap scan size if needed.
# ---------------------------------------------------------------------------
function _scan_transcripts {
    param(
        [string]$ProjectsDir,
        [int]$MaxFileSizeMB = 200,
        [int]$MaxFiles = 0  # 0 = unlimited
    )
    $records = New-Object 'System.Collections.Generic.List[psobject]'
    if (-not (Test-Path $ProjectsDir)) {
        return ,$records
    }
    $files = @(Get-ChildItem -Path $ProjectsDir -Recurse -Filter '*.jsonl' -File -ErrorAction SilentlyContinue)
    if ($MaxFiles -gt 0 -and $files.Count -gt $MaxFiles) {
        # Sort newest first then trim.
        $files = $files | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First $MaxFiles
    }

    foreach ($f in $files) {
        if ($f.Length -gt ($MaxFileSizeMB * 1MB)) { continue }
        # Project = parent dir name; session = file basename (no .jsonl).
        $project = $f.Directory.Name
        $session = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
        try {
            $reader = [System.IO.File]::OpenText($f.FullName)
            try {
                while (-not $reader.EndOfStream) {
                    $line = $reader.ReadLine()
                    if (-not $line) { continue }
                    if ($line.IndexOf('"usage"') -lt 0) { continue }
                    try {
                        $obj = $line | ConvertFrom-Json -ErrorAction Stop
                    } catch { continue }

                    # Extract timestamp.
                    $ts = $null
                    if ($obj.timestamp) { $ts = $obj.timestamp }
                    elseif ($obj.message -and $obj.message.timestamp) { $ts = $obj.message.timestamp }
                    elseif ($obj.message -and $obj.message.created_at) { $ts = $obj.message.created_at }
                    $tsUtc = $null
                    if ($ts) {
                        try { $tsUtc = ([DateTime]::Parse($ts)).ToUniversalTime() } catch {}
                    }

                    # Extract usage payload.
                    $u = $null
                    if ($obj.message -and $obj.message.usage) { $u = $obj.message.usage }
                    elseif ($obj.usage) { $u = $obj.usage }
                    if (-not $u) { continue }

                    # Extract model + tool count.
                    $model = '?'
                    if ($obj.message -and $obj.message.model) { $model = [string]$obj.message.model }
                    elseif ($obj.model) { $model = [string]$obj.model }
                    $tools = 0
                    if ($obj.message -and $obj.message.content) {
                        try {
                            $tools = @($obj.message.content | Where-Object { $_.type -eq 'tool_use' }).Count
                        } catch { $tools = 0 }
                    }

                    $rec = [PSCustomObject]@{
                        project      = $project
                        session_id   = $session
                        model        = $model
                        ts_utc       = $tsUtc
                        input        = [int64]($u.input_tokens                | ForEach-Object { $_ })
                        cache_create = [int64]($u.cache_creation_input_tokens | ForEach-Object { $_ })
                        cache_read   = [int64]($u.cache_read_input_tokens     | ForEach-Object { $_ })
                        output       = [int64]($u.output_tokens               | ForEach-Object { $_ })
                        tools        = [int]$tools
                    }
                    $records.Add($rec)
                }
            } finally { $reader.Close() }
        } catch { continue }
    }
    return ,$records
}

# ---------------------------------------------------------------------------
# Helpers: cost + billable-eq math.
# ---------------------------------------------------------------------------

# Per-million-token cost ($USD) for Opus 4.x; Sonnet rates ~5x cheaper.
$opusRate = @{ input = 15.00; cache_create = 18.75; cache_read = 1.50; output = 75.00 }
$sonRate  = @{ input =  3.00; cache_create =  3.75; cache_read = 0.30; output = 15.00 }

function _cost_usd([psobject]$rec) {
    $rate = if ($rec.model -match 'opus') { $opusRate } else { $sonRate }
    $c =  ($rec.input        * $rate['input']        / 1000000.0)
    $c += ($rec.cache_create * $rate['cache_create'] / 1000000.0)
    $c += ($rec.cache_read   * $rate['cache_read']   / 1000000.0)
    $c += ($rec.output       * $rate['output']       / 1000000.0)
    return $c
}

function _billable_eq([psobject]$rec) {
    return [int64]($rec.input + ($rec.cache_create * 1.25) + ($rec.cache_read * 0.1) + ($rec.output * 5.0))
}

function _fmt_num([int64]$n) {
    if ($n -ge 1000000000) { return "{0:N2}B" -f ($n / 1000000000.0) }
    if ($n -ge 1000000)    { return "{0:N2}M" -f ($n / 1000000.0) }
    if ($n -ge 1000)       { return "{0:N1}K" -f ($n / 1000.0) }
    return "$n"
}

function _fmt_pct([double]$num, [double]$denom) {
    if ($denom -le 0) { return '   - ' }
    $p = 100.0 * $num / $denom
    return ("{0,5:N1}%" -f $p)
}

# ---------------------------------------------------------------------------
# Window summarizer -- given $records + window-start UTC, fold to per-window totals.
# ---------------------------------------------------------------------------
function _window_totals {
    param([System.Collections.Generic.List[psobject]]$Records, [DateTime]$Since)
    $tot = @{
        input = [int64]0; cache_create = [int64]0; cache_read = [int64]0; output = [int64]0
        msgs = 0; billable_eq = [int64]0; cost_usd = 0.0
    }
    foreach ($r in $Records) {
        if (-not $r.ts_utc) { continue }
        if ($r.ts_utc -lt $Since) { continue }
        $tot.input        += $r.input
        $tot.cache_create += $r.cache_create
        $tot.cache_read   += $r.cache_read
        $tot.output       += $r.output
        $tot.msgs         += 1
        $tot.billable_eq  += _billable_eq $r
        $tot.cost_usd     += _cost_usd $r
    }
    return $tot
}

# ---------------------------------------------------------------------------
# ACTION: Summary -- 4 rolling windows + cache hit + cost.
# ---------------------------------------------------------------------------
function Show-Summary {
    param([System.Collections.Generic.List[psobject]]$Records)
    _header "Token Analytics :: Summary"

    $now = (Get-Date).ToUniversalTime()
    $windows = @(
        @{ label = '1h';  hours = 1 },
        @{ label = '5h';  hours = 5 },
        @{ label = '24h'; hours = 24 },
        @{ label = '7d';  hours = (24*7) }
    )

    Write-Host ("  {0,-6} {1,7} {2,10} {3,10} {4,10} {5,10} {6,10} {7,10} {8,8}" -f `
        'Window','Msgs','Input','CacheW','CacheR','Output','Total','Billable','Cost$')
    Write-Host "  $DIM------ ------- ---------- ---------- ---------- ---------- ---------- ---------- --------$RESET"

    foreach ($w in $windows) {
        $since = $now.AddHours(-$w.hours)
        $t = _window_totals -Records $Records -Since $since
        $raw = $t.input + $t.cache_create + $t.cache_read + $t.output
        $costStr = "{0,7:N2}" -f $t.cost_usd
        Write-Host ("  $WHITE{0,-6}$RESET {1,7} {2,10} {3,10} {4,10} {5,10} {6,10} {7,10} {8,8}" -f `
            $w.label, $t.msgs,
            (_fmt_num $t.input), (_fmt_num $t.cache_create),
            (_fmt_num $t.cache_read), (_fmt_num $t.output),
            (_fmt_num $raw), (_fmt_num $t.billable_eq), $costStr)
    }

    # Cache hit ratio over last 24h (the meaningful default window).
    $t24 = _window_totals -Records $Records -Since $now.AddHours(-24)
    $cacheRatio = if (($t24.cache_create + $t24.cache_read) -gt 0) {
        100.0 * $t24.cache_read / ($t24.cache_create + $t24.cache_read)
    } else { 0.0 }
    $cacheCol = if ($cacheRatio -gt 60) { $OK } elseif ($cacheRatio -gt 30) { $WARN } else { $FAIL }
    Write-Host ""
    Write-Host ("  $SOFT Cache hit ratio (24h):$RESET $cacheCol{0,5:N1}%$RESET  $DIM(fleet target >60%)$RESET" -f $cacheRatio)
    $savings = [int64](0.9 * $t24.cache_read)
    Write-Host ("  $SOFT Savings vs no-cache (24h):$RESET $OK{0}$RESET tokens" -f (_fmt_num $savings))

    $projCount = ($Records | Select-Object -ExpandProperty project -Unique | Measure-Object).Count
    _footer "$($Records.Count) total transcript-messages scanned across $projCount projects"
}

# ---------------------------------------------------------------------------
# ACTION: ByProject -- per-project totals + cache + cost.
# ---------------------------------------------------------------------------
function Show-ByProject {
    param([System.Collections.Generic.List[psobject]]$Records)
    _header "Token Analytics :: By Project"

    $groups = $Records | Group-Object project
    $rows = foreach ($g in $groups) {
        $inp = ($g.Group | Measure-Object input -Sum).Sum
        $cc  = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr  = ($g.Group | Measure-Object cache_read   -Sum).Sum
        $out = ($g.Group | Measure-Object output       -Sum).Sum
        $msgs = $g.Count
        $billable = [int64]($inp + ($cc * 1.25) + ($cr * 0.1) + ($out * 5.0))
        $cacheRatio = if (($cc + $cr) -gt 0) { 100.0 * $cr / ($cc + $cr) } else { 0.0 }
        $cost = 0.0
        foreach ($r in $g.Group) { $cost += _cost_usd $r }
        [PSCustomObject]@{
            project = $g.Name
            msgs = $msgs
            input = [int64]$inp
            cache_create = [int64]$cc
            cache_read = [int64]$cr
            output = [int64]$out
            billable = $billable
            cache_ratio = $cacheRatio
            cost = $cost
        }
    }
    $rows = $rows | Sort-Object billable -Descending

    Write-Host ("  {0,-45} {1,6} {2,9} {3,9} {4,9} {5,8} {6,8}" -f `
        'Project','Msgs','Input','CacheR','Output','Cache%','Cost$')
    Write-Host "  $DIM--------------------------------------------- ------ --------- --------- --------- -------- --------$RESET"
    foreach ($r in $rows) {
        $proj = _humanize_project $r.project
        if ($proj.Length -gt 45) { $proj = $proj.Substring(0, 42) + '...' }
        $col = if ($r.cache_ratio -gt 60) { $OK } elseif ($r.cache_ratio -gt 30) { $WARN } else { $FAIL }
        Write-Host ("  $WHITE{0,-45}$RESET {1,6} {2,9} {3,9} {4,9} $col{5,7:N1}%$RESET {6,8:N2}" -f `
            $proj, $r.msgs, (_fmt_num $r.input), (_fmt_num $r.cache_read),
            (_fmt_num $r.output), $r.cache_ratio, $r.cost)
    }

    $totalProjects = ($rows | Measure-Object).Count
    $totalCost = ($rows | Measure-Object cost -Sum).Sum
    _footer ("$totalProjects projects scanned; total cost-eq: `$" + ("{0:N2}" -f $totalCost))
}

# ---------------------------------------------------------------------------
# ACTION: BySession -- top-N sessions (single transcript files) by billable.
# ---------------------------------------------------------------------------
function Show-BySession {
    param([System.Collections.Generic.List[psobject]]$Records, [int]$Top = 10)
    _header "Token Analytics :: Top $Top Sessions (by billable-eq)"

    $groups = $Records | Group-Object session_id
    $rows = foreach ($g in $groups) {
        $inp = ($g.Group | Measure-Object input -Sum).Sum
        $cc  = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr  = ($g.Group | Measure-Object cache_read   -Sum).Sum
        $out = ($g.Group | Measure-Object output       -Sum).Sum
        $billable = [int64]($inp + ($cc * 1.25) + ($cr * 0.1) + ($out * 5.0))
        $msgs = $g.Count
        $tools = ($g.Group | Measure-Object tools -Sum).Sum
        $first = ($g.Group | ForEach-Object { $_.project } | Select-Object -First 1)
        $avgT = if ($msgs -gt 0) { [int64]($billable / $msgs) } else { [int64]0 }
        [PSCustomObject]@{
            session = $g.Name
            project = $first
            msgs = $msgs
            tools = [int]$tools
            billable = $billable
            avg_per_msg = $avgT
        }
    }
    $rows = $rows | Sort-Object billable -Descending | Select-Object -First $Top

    Write-Host ("  {0,-40} {1,-30} {2,6} {3,6} {4,11} {5,11}" -f `
        'Session','Project','Msgs','Tools','Billable','Avg/Msg')
    Write-Host "  $DIM---------------------------------------- ------------------------------ ------ ------ ----------- -----------$RESET"
    foreach ($r in $rows) {
        $sid = if ($r.session.Length -gt 40) { $r.session.Substring(0, 37) + '...' } else { $r.session }
        $proj = _humanize_project $r.project
        if ($proj.Length -gt 30) { $proj = $proj.Substring(0, 27) + '...' }
        Write-Host ("  $WHITE{0,-40}$RESET {1,-30} {2,6} {3,6} {4,11} {5,11}" -f `
            $sid, $proj, $r.msgs, $r.tools, (_fmt_num $r.billable), (_fmt_num $r.avg_per_msg))
    }

    _footer "Showing top $Top of $(($Records | Group-Object session_id).Count) total sessions"
}

# ---------------------------------------------------------------------------
# ACTION: ByModel -- group by message.model.
# ---------------------------------------------------------------------------
function Show-ByModel {
    param([System.Collections.Generic.List[psobject]]$Records)
    _header "Token Analytics :: By Model"

    $groups = $Records | Group-Object model
    $rows = foreach ($g in $groups) {
        $inp = ($g.Group | Measure-Object input -Sum).Sum
        $cc  = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr  = ($g.Group | Measure-Object cache_read   -Sum).Sum
        $out = ($g.Group | Measure-Object output       -Sum).Sum
        $msgs = $g.Count
        $billable = [int64]($inp + ($cc * 1.25) + ($cr * 0.1) + ($out * 5.0))
        $cost = 0.0
        foreach ($r in $g.Group) { $cost += _cost_usd $r }
        [PSCustomObject]@{
            model = $g.Name
            msgs = $msgs
            input = [int64]$inp
            output = [int64]$out
            billable = $billable
            cost = $cost
        }
    }
    $rows = $rows | Sort-Object billable -Descending

    Write-Host ("  {0,-40} {1,8} {2,10} {3,10} {4,11} {5,10}" -f `
        'Model','Msgs','Input','Output','Billable','Cost$')
    Write-Host "  $DIM---------------------------------------- -------- ---------- ---------- ----------- ----------$RESET"
    foreach ($r in $rows) {
        $m = if ($r.model.Length -gt 40) { $r.model.Substring(0, 37) + '...' } else { $r.model }
        Write-Host ("  $WHITE{0,-40}$RESET {1,8} {2,10} {3,10} {4,11} {5,10:N2}" -f `
            $m, $r.msgs, (_fmt_num $r.input), (_fmt_num $r.output),
            (_fmt_num $r.billable), $r.cost)
    }

    _footer "$(($rows | Measure-Object).Count) distinct models seen"
}

# ---------------------------------------------------------------------------
# ACTION: CacheReport -- per-project cache efficiency.
# ---------------------------------------------------------------------------
function Show-CacheReport {
    param([System.Collections.Generic.List[psobject]]$Records)
    _header "Token Analytics :: Cache Report"

    $groups = $Records | Group-Object project
    $rows = foreach ($g in $groups) {
        $cc = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr = ($g.Group | Measure-Object cache_read   -Sum).Sum
        $inp = ($g.Group | Measure-Object input -Sum).Sum
        $ratio = if (($cc + $cr) -gt 0) { 100.0 * $cr / ($cc + $cr) } else { 0.0 }
        $savings = [int64](0.9 * $cr)
        [PSCustomObject]@{
            project = $g.Name; msgs = $g.Count
            cache_create = [int64]$cc; cache_read = [int64]$cr
            input = [int64]$inp; cache_ratio = $ratio; savings = $savings
        }
    }
    $rows = $rows | Sort-Object cache_ratio -Descending

    Write-Host ("  {0,-50} {1,6} {2,10} {3,10} {4,8} {5,11}" -f `
        'Project','Msgs','CacheCreate','CacheRead','Hit%','Savings')
    Write-Host "  $DIM-------------------------------------------------- ------ ---------- ---------- -------- -----------$RESET"
    foreach ($r in $rows) {
        $p = _humanize_project $r.project
        if ($p.Length -gt 50) { $p = $p.Substring(0, 47) + '...' }
        $col = if ($r.cache_ratio -gt 60) { $OK } elseif ($r.cache_ratio -gt 30) { $WARN } else { $FAIL }
        Write-Host ("  $WHITE{0,-50}$RESET {1,6} {2,10} {3,10} $col{4,7:N1}%$RESET {5,11}" -f `
            $p, $r.msgs, (_fmt_num $r.cache_create), (_fmt_num $r.cache_read),
            $r.cache_ratio, (_fmt_num $r.savings))
    }

    # Fleet aggregate.
    $totalCC = ($Records | Measure-Object cache_create -Sum).Sum
    $totalCR = ($Records | Measure-Object cache_read -Sum).Sum
    $fleetRatio = if (($totalCC + $totalCR) -gt 0) { 100.0 * $totalCR / ($totalCC + $totalCR) } else { 0.0 }
    $fleetCol = if ($fleetRatio -gt 60) { $OK } elseif ($fleetRatio -gt 30) { $WARN } else { $FAIL }
    _footer ("Fleet-wide cache hit ratio: " + ("{0:N1}" -f $fleetRatio) + "% (target >60%)")
}

# ---------------------------------------------------------------------------
# ACTION: WasteReport -- flag wasteful patterns.
# ---------------------------------------------------------------------------
function Show-WasteReport {
    param([System.Collections.Generic.List[psobject]]$Records, [int]$BloatTokens, [int]$ToolLoopMsgs)
    _header "Token Analytics :: Waste Report"

    $now = (Get-Date).ToUniversalTime()
    $flags = New-Object 'System.Collections.Generic.List[psobject]'

    # 1) Sessions with high cache_create / low cache_read = built cache, didn't use.
    $sessGroups = $Records | Group-Object session_id
    foreach ($g in $sessGroups) {
        $cc = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr = ($g.Group | Measure-Object cache_read -Sum).Sum
        if ($cc -gt 100000 -and $cr -lt ($cc * 0.5)) {
            $first = ($g.Group | ForEach-Object { $_.project } | Select-Object -First 1)
            $flags.Add([PSCustomObject]@{
                severity = 'med'
                kind = 'abandoned-cache'
                target = $g.Name.Substring(0, [Math]::Min(28, $g.Name.Length))
                project = _humanize_project $first
                detail = "cache_create=$(_fmt_num $cc) but cache_read=$(_fmt_num $cr) (cache built, barely used)"
            })
        }
    }

    # 2) Per-project: avg tokens/msg > BloatTokens = context bloat.
    $projGroups = $Records | Group-Object project
    foreach ($g in $projGroups) {
        $billableSum = [int64]0
        foreach ($r in $g.Group) { $billableSum += (_billable_eq $r) }
        $avg = if ($g.Count -gt 0) { [int64]($billableSum / $g.Count) } else { [int64]0 }
        if ($avg -gt $BloatTokens -and $g.Count -ge 10) {
            $flags.Add([PSCustomObject]@{
                severity = 'high'
                kind = 'context-bloat'
                target = '(project-wide)'
                project = _humanize_project $g.Name
                detail = "avg billable=$(_fmt_num $avg) per msg over $($g.Count) msgs (threshold $(_fmt_num ([int64]$BloatTokens)))"
            })
        }
    }

    # 3) Sessions with >ToolLoopMsgs messages averaging >50 tool uses = tool loop.
    foreach ($g in $sessGroups) {
        if ($g.Count -lt $ToolLoopMsgs) { continue }
        $totTools = ($g.Group | Measure-Object tools -Sum).Sum
        $avgTools = if ($g.Count -gt 0) { [double]$totTools / $g.Count } else { 0.0 }
        if ($avgTools -ge 0.5) {
            $first = ($g.Group | ForEach-Object { $_.project } | Select-Object -First 1)
            $flags.Add([PSCustomObject]@{
                severity = 'med'
                kind = 'tool-loop'
                target = $g.Name.Substring(0, [Math]::Min(28, $g.Name.Length))
                project = _humanize_project $first
                detail = "$($g.Count) msgs, $totTools tool calls (avg $('{0:N1}' -f $avgTools)/msg)"
            })
        }
    }

    # 4) Per-project cache hit < 20% AND >50 msgs = caching-broken.
    foreach ($g in $projGroups) {
        if ($g.Count -lt 50) { continue }
        $cc = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr = ($g.Group | Measure-Object cache_read -Sum).Sum
        if (($cc + $cr) -le 0) { continue }
        $ratio = 100.0 * $cr / ($cc + $cr)
        if ($ratio -lt 20) {
            $flags.Add([PSCustomObject]@{
                severity = 'high'
                kind = 'no-caching'
                target = '(project-wide)'
                project = _humanize_project $g.Name
                detail = "$('{0:N1}' -f $ratio)% cache hit rate over $($g.Count) msgs (fleet target >60%)"
            })
        }
    }

    if ($flags.Count -eq 0) {
        Write-Host "  $OK No waste patterns detected at current thresholds.$RESET"
        _footer "thresholds: bloat=$(_fmt_num ([int64]$BloatTokens))/msg, tool-loop=$ToolLoopMsgs msgs, no-caching <20% (>=50 msgs)"
        return
    }

    Write-Host ("  {0,-6} {1,-16} {2,-30} {3,-30} {4}" -f 'Sev','Kind','Target','Project','Detail')
    Write-Host "  $DIM------ ---------------- ------------------------------ ------------------------------ ---------$RESET"
    foreach ($f in $flags) {
        $col = if ($f.severity -eq 'high') { $FAIL } elseif ($f.severity -eq 'med') { $WARN } else { $DIM }
        $proj = if ($f.project.Length -gt 30) { $f.project.Substring(0, 27) + '...' } else { $f.project }
        Write-Host ("  $col{0,-6}$RESET {1,-16} $WHITE{2,-30}$RESET {3,-30} $DIM{4}$RESET" -f `
            $f.severity, $f.kind, $f.target, $proj, $f.detail)
    }
    _footer "$($flags.Count) waste patterns flagged"
}

# ---------------------------------------------------------------------------
# ACTION: Recommendations -- 5-10 prioritized actionable suggestions.
# ---------------------------------------------------------------------------
function Show-Recommendations {
    param([System.Collections.Generic.List[psobject]]$Records, [int]$BloatTokens, [int]$ToolLoopMsgs)
    _header "Token Analytics :: Recommendations"

    if ($Records.Count -eq 0) {
        Write-Host "  $DIM no records to analyze; nothing to recommend.$RESET"
        _footer "0 recommendations"
        return
    }

    $recs = New-Object 'System.Collections.Generic.List[psobject]'
    $now = (Get-Date).ToUniversalTime()

    # 1. Fleet cache target.
    $totalCC = ($Records | Measure-Object cache_create -Sum).Sum
    $totalCR = ($Records | Measure-Object cache_read -Sum).Sum
    $fleetRatio = if (($totalCC + $totalCR) -gt 0) { 100.0 * $totalCR / ($totalCC + $totalCR) } else { 0.0 }
    if ($fleetRatio -lt 60) {
        $gap = 60 - $fleetRatio
        $recs.Add([PSCustomObject]@{
            prio = if ($fleetRatio -lt 30) { 'P0' } else { 'P1' }
            rec = ("Fleet cache hit ratio is {0:N1}% (target >60%). Gap of {1:N1}pp. Audit CLAUDE.md + system prompts for stable prefixes; enable prompt caching on long system prompts." -f $fleetRatio, $gap)
        })
    }

    # 2. Per-project worst cache offenders.
    $projGroups = $Records | Group-Object project
    foreach ($g in $projGroups) {
        if ($g.Count -lt 50) { continue }
        $cc = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr = ($g.Group | Measure-Object cache_read -Sum).Sum
        if (($cc + $cr) -le 0) { continue }
        $r = 100.0 * $cr / ($cc + $cr)
        if ($r -lt 25) {
            $proj = _humanize_project $g.Name
            $recs.Add([PSCustomObject]@{
                prio = 'P1'
                rec = ("Project '{0}' has {1:N1}% cache hit over {2} msgs. Consider stable prompt prefix (CLAUDE.md frozen first 4K tokens) for caching." -f $proj, $r, $g.Count)
            })
        }
    }

    # 3. Sessions with avg tokens/msg over bloat threshold.
    $sessGroups = $Records | Group-Object session_id
    $bloated = New-Object 'System.Collections.Generic.List[psobject]'
    foreach ($g in $sessGroups) {
        if ($g.Count -lt 20) { continue }
        $bSum = [int64]0
        foreach ($r in $g.Group) { $bSum += (_billable_eq $r) }
        $avg = [int64]($bSum / $g.Count)
        if ($avg -gt $BloatTokens) {
            $first = ($g.Group | ForEach-Object { $_.project } | Select-Object -First 1)
            $bloated.Add([PSCustomObject]@{ session = $g.Name; project = $first; avg = $avg; msgs = $g.Count })
        }
    }
    if ($bloated.Count -gt 0) {
        $top = $bloated | Sort-Object avg -Descending | Select-Object -First 1
        $proj = _humanize_project $top.project
        $recs.Add([PSCustomObject]@{
            prio = 'P1'
            rec = ("$($bloated.Count) sessions have avg billable >{0} tokens/msg (worst: '{1}' in '{2}' at {3} avg over {4} msgs). Use /compact or shorter sessions." -f (_fmt_num ([int64]$BloatTokens)), $top.session.Substring(0, [Math]::Min(12, $top.session.Length)), $proj, (_fmt_num $top.avg), $top.msgs)
        })
    }

    # 4. High-cost projects this week.
    $weekStart = $now.AddDays(-7)
    $weekRecords = $Records | Where-Object { $_.ts_utc -and $_.ts_utc -ge $weekStart }
    if ($weekRecords) {
        $weekProj = $weekRecords | Group-Object project
        $costs = foreach ($g in $weekProj) {
            $c = 0.0
            foreach ($r in $g.Group) { $c += _cost_usd $r }
            [PSCustomObject]@{ project = $g.Name; cost = $c; msgs = $g.Count }
        }
        $top = $costs | Sort-Object cost -Descending | Select-Object -First 1
        if ($top -and $top.cost -gt 50) {
            $proj = _humanize_project $top.project
            $recs.Add([PSCustomObject]@{
                prio = if ($top.cost -gt 200) { 'P0' } else { 'P1' }
                rec = ("Project '{0}' cost-eq `${1:N2} this week ({2} msgs). Investigate sub-agent fan-out / context size / model choice (Sonnet for ~5x savings vs Opus where quality allows)." -f $proj, $top.cost, $top.msgs)
            })
        }
    }

    # 5. Model mix recommendation.
    $modelGroups = $Records | Group-Object model
    $opusMsgs = 0; $sonnetMsgs = 0
    foreach ($g in $modelGroups) {
        if ($g.Name -match 'opus') { $opusMsgs += $g.Count }
        elseif ($g.Name -match 'sonnet') { $sonnetMsgs += $g.Count }
    }
    if ($opusMsgs -gt 0 -and ($opusMsgs + $sonnetMsgs) -gt 0) {
        $opusPct = 100.0 * $opusMsgs / ($opusMsgs + $sonnetMsgs)
        if ($opusPct -gt 80) {
            $recs.Add([PSCustomObject]@{
                prio = 'P2'
                rec = ("{0:N1}% of messages use Opus. Audit per-task tier-down: Sonnet at ~20% Opus cost; reserve Opus for architecture / hard reasoning / 1M-context tasks." -f $opusPct)
            })
        }
    }

    # 6. Tool-loop sessions.
    $toolLoopCount = 0
    foreach ($g in $sessGroups) {
        if ($g.Count -ge $ToolLoopMsgs) {
            $totTools = ($g.Group | Measure-Object tools -Sum).Sum
            if ($totTools -gt ($g.Count * 0.5)) { $toolLoopCount++ }
        }
    }
    if ($toolLoopCount -gt 0) {
        $recs.Add([PSCustomObject]@{
            prio = 'P2'
            rec = ("$toolLoopCount sessions exceed $ToolLoopMsgs msgs with >50% tool-use density. Likely sub-agent fan-out or retry loops. Tighten task scope; cap sub-agents per loop; add early-exit heuristics.")
        })
    }

    # 7. Abandoned-cache sessions.
    $abandoned = 0
    foreach ($g in $sessGroups) {
        $cc = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr = ($g.Group | Measure-Object cache_read -Sum).Sum
        if ($cc -gt 1000000 -and $cr -lt ($cc * 0.3)) { $abandoned++ }
    }
    if ($abandoned -gt 0) {
        $recs.Add([PSCustomObject]@{
            prio = 'P2'
            rec = ("$abandoned sessions built >1M cache tokens but used <30%. Likely short-lived sessions wasting cache-creation premium (1.25x). Avoid spawning fresh sessions for one-shot tasks.")
        })
    }

    # 8. 24h spike.
    $t24 = _window_totals -Records $Records -Since $now.AddHours(-24)
    $t7d = _window_totals -Records $Records -Since $now.AddDays(-7)
    if ($t7d.msgs -gt 0) {
        $dailyAvg = $t7d.msgs / 7.0
        if ($t24.msgs -gt ($dailyAvg * 2)) {
            $recs.Add([PSCustomObject]@{
                prio = 'P2'
                rec = ("Last 24h msgs ({0}) is {1:N1}x the 7-day daily average ({2:N0}). Volume spike -- if intentional (loop-mode push) ignore; if not, look for runaway sub-agents." -f $t24.msgs, ($t24.msgs / $dailyAvg), $dailyAvg)
            })
        }
    }

    # 9. Always-present: stable-prefix doctrine.
    $recs.Add([PSCustomObject]@{
        prio = 'P3'
        rec = "Standing rule: keep system prompts + tool descriptions + CLAUDE.md cold-start block STABLE across spawns (no per-spawn timestamps in cached region) -- cache invalidation kills hit ratio."
    })

    # 10. Always-present: prune brain.
    $rec10 = "Brain index review: per no-bullshit rule 8, brain >150 rows triggers consolidation. Current row count visible in _shared-memory/knowledge/_INDEX.md."
    $recs.Add([PSCustomObject]@{ prio = 'P3'; rec = $rec10 })

    # Print
    $i = 1
    foreach ($r in ($recs | Sort-Object { switch ($_.prio) { 'P0' { 0 } 'P1' { 1 } 'P2' { 2 } 'P3' { 3 } default { 4 } } })) {
        $col = switch ($r.prio) { 'P0' { $FAIL } 'P1' { $WARN } 'P2' { $BRIGHTP } default { $DIM } }
        Write-Host ("  $col[$($r.prio)]$RESET $WHITE#{0:D2}$RESET $($r.rec)" -f $i)
        Write-Host ""
        $i++
    }
    _footer "$($recs.Count) recommendations (sort: P0 > P1 > P2 > P3)"
}

# ---------------------------------------------------------------------------
# ACTION: Json -- machine-readable bundle of all relevant aggregates.
# ---------------------------------------------------------------------------
function Show-Json {
    param([System.Collections.Generic.List[psobject]]$Records)

    $now = (Get-Date).ToUniversalTime()
    $windows = @{}
    foreach ($w in @(@{l='1h';h=1},@{l='5h';h=5},@{l='24h';h=24},@{l='7d';h=168})) {
        $t = _window_totals -Records $Records -Since $now.AddHours(-$w.h)
        $windows[$w.l] = $t
    }

    $byProj = @()
    foreach ($g in ($Records | Group-Object project)) {
        $cc = ($g.Group | Measure-Object cache_create -Sum).Sum
        $cr = ($g.Group | Measure-Object cache_read -Sum).Sum
        $inp = ($g.Group | Measure-Object input -Sum).Sum
        $out = ($g.Group | Measure-Object output -Sum).Sum
        $ratio = if (($cc + $cr) -gt 0) { 100.0 * $cr / ($cc + $cr) } else { 0.0 }
        $cost = 0.0
        foreach ($r in $g.Group) { $cost += _cost_usd $r }
        $byProj += [PSCustomObject]@{
            project = $g.Name
            msgs = $g.Count
            input_tokens = $inp
            cache_create_tokens = $cc
            cache_read_tokens = $cr
            output_tokens = $out
            cache_hit_pct = [Math]::Round($ratio, 2)
            cost_usd = [Math]::Round($cost, 4)
        }
    }

    $byModel = @()
    foreach ($g in ($Records | Group-Object model)) {
        $cost = 0.0
        foreach ($r in $g.Group) { $cost += _cost_usd $r }
        $byModel += [PSCustomObject]@{
            model = $g.Name
            msgs = $g.Count
            input = ($g.Group | Measure-Object input -Sum).Sum
            output = ($g.Group | Measure-Object output -Sum).Sum
            cost_usd = [Math]::Round($cost, 4)
        }
    }

    $bundle = [PSCustomObject]@{
        scanned_at_utc = $now.ToString("yyyy-MM-ddTHH:mm:ssZ")
        total_messages = $Records.Count
        total_sessions = ($Records | Group-Object session_id).Count
        total_projects = ($Records | Group-Object project).Count
        windows = $windows
        by_project = $byProj
        by_model = $byModel
    }
    $bundle | ConvertTo-Json -Depth 6
}

# ---------------------------------------------------------------------------
# Main dispatch.
# ---------------------------------------------------------------------------
$projectsDir = Join-Path $ClaudeRoot 'projects'
$records = _scan_transcripts -ProjectsDir $projectsDir

switch ($Action) {
    'Summary'         { Show-Summary -Records $records }
    'ByProject'       { Show-ByProject -Records $records }
    'BySession'       { Show-BySession -Records $records -Top $TopN }
    'ByModel'         { Show-ByModel -Records $records }
    'CacheReport'     { Show-CacheReport -Records $records }
    'WasteReport'     { Show-WasteReport -Records $records -BloatTokens $ContextBloatThresholdTokens -ToolLoopMsgs $ToolLoopThresholdMsgs }
    'Recommendations' { Show-Recommendations -Records $records -BloatTokens $ContextBloatThresholdTokens -ToolLoopMsgs $ToolLoopThresholdMsgs }
    'Json'            { Show-Json -Records $records }
}
exit 0
