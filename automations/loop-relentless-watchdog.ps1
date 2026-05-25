# loop-relentless-watchdog.ps1 — detect stalled loop=on agents and poke them
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25T02:18Z:
#   "make the loop system on our agents actually work. make it agressive and
#    make it hafve agents relentless pursue goal within our guidelines using
#    our tools iwhen on."
#
# Composes with:
#   - CLAUDE.md operator-canonical 2026-05-24 "LOOP MODE = continuous iteration"
#     (rules 1-7; same-turn iteration, ScheduleWakeup cap 270s)
#   - _shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md
#     (12 guardrails per iteration)
#   - mesh-coordinator.ps1 (file lock around watchdog-state edits)
#   - fleet-update.ps1 (poke is a peer "kind=loop-poke" cross-agent message)
#   - ps51-scriptblock-replace-bug-2026-05-25.md (NO scriptblock-in-replace; PS 5.1 safe)
#
# Stall detection (any of 3 signals trips a stall):
#   1. heartbeat_stale  : mtime > 8 min ago AND heartbeat JSON has `loop_iter`
#   2. focus_stuck      : same `focus_intent` for 3 consecutive ticks (>=15 min)
#   3. iter_stalled     : same `loop_iter` value across 3 consecutive ticks
#
# Poke mechanism:
#   Write _shared-memory/inbox/<slug>/<utc>-from-loop-watchdog-poke.json
#   (kind=loop-poke, priority=high, dedup via state's has_been_poked_this_cycle bit)
#
# Actions:
#   Scan    (default) — full pass, write pokes
#   DryRun  — scan + report but DO NOT write pokes
#   Status  — print current watchdog-state JSON
#   Reset   — clear watchdog-state (use after operator pause)
#
# Cap: max 5 pokes per Scan run. If 5+ agents stalled the fleet has a bigger
# problem -> surface row to OPERATOR-ACTION-QUEUE.md instead.

[CmdletBinding()]
param(
    [ValidateSet('Scan','DryRun','Status','Reset')]
    [string]$Action = 'Scan',

    [string]$SanctumRoot = 'D:\Sinister Sanctum',

    # Sweep tasks, NOT iterative agents -- exclude from stall detection.
    [string[]]$Exclude = @(
        'sanctum-mesh-foundation',
        'sinister-link',
        'sinister-overseer-distribute'
    ),

    [int]$HeartbeatStaleMinutes = 8,
    [int]$TickThreshold = 3,           # consecutive identical ticks => stall
    [int]$MaxPokesPerRun = 5
)

$ErrorActionPreference = 'Stop'

# ---------- paths --------------------------------------------------------
$HeartbeatDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$InboxRoot    = Join-Path $SanctumRoot '_shared-memory\inbox'
$StatePath    = Join-Path $SanctumRoot '_shared-memory\loop-watchdog-state.json'
$QueuePath    = Join-Path $SanctumRoot '_shared-memory\OPERATOR-ACTION-QUEUE.md'
$MeshCoord    = Join-Path $SanctumRoot 'automations\mesh-coordinator.ps1'

# ---------- utility ------------------------------------------------------
function Utc-Now { return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function Utc-Stamp { return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmmZ") }

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        if (-not $raw) { return $null }
        return $raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function To-Hashtable {
    # Convert a PSCustomObject to a hashtable (PS 5.1 ConvertFrom-Json returns PSCustomObject only).
    param($Obj)
    if ($null -eq $Obj) { return @{} }
    $h = @{}
    foreach ($p in $Obj.PSObject.Properties) {
        $h[$p.Name] = $p.Value
    }
    return $h
}

function Load-State {
    $obj = Read-JsonFile -Path $StatePath
    if ($null -eq $obj) {
        return @{
            schema_version = 'sinister.loop-watchdog-state.v1'
            created_utc = (Utc-Now)
            last_tick_utc = $null
            tick_count = 0
            agents = @{}     # slug -> @{ last_focus, last_iter, ticks_same_focus, ticks_same_iter, last_poke_cycle_id }
        }
    }
    $h = To-Hashtable $obj
    if (-not $h.ContainsKey('agents') -or $null -eq $h['agents']) {
        $h['agents'] = @{}
    } else {
        # convert nested PSCustomObject -> hashtable
        $agentsH = @{}
        foreach ($p in $obj.agents.PSObject.Properties) {
            $agentsH[$p.Name] = To-Hashtable $p.Value
        }
        $h['agents'] = $agentsH
    }
    if (-not $h.ContainsKey('tick_count')) { $h['tick_count'] = 0 }
    return $h
}

function Save-State {
    param([hashtable]$State)
    $json = $State | ConvertTo-Json -Depth 8
    Write-Utf8NoBom -Path $StatePath -Content $json
}

function Try-MeshLock {
    param([string]$Focus, [int]$TtlSec = 120)
    if (-not (Test-Path $MeshCoord)) { return $true }   # mesh-coord missing => no lock available, proceed
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $MeshCoord `
            -Action Register -Slug 'loop-relentless-watchdog' `
            -Display 'Loop Watchdog' -Focus $Focus -TtlSeconds $TtlSec `
            -Hint 'watchdog-state edit' -BlastRadius single 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $true   # mesh-coord failed => degrade gracefully
    }
}

function Try-MeshRelease {
    param([string]$Focus)
    if (-not (Test-Path $MeshCoord)) { return }
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $MeshCoord `
            -Action Release -Slug 'loop-relentless-watchdog' -Focus $Focus 2>$null | Out-Null
    } catch { }
}

function Get-LoopHeartbeats {
    if (-not (Test-Path $HeartbeatDir)) { return @() }
    $files = Get-ChildItem -LiteralPath $HeartbeatDir -Filter '*.json' -File
    $results = @()
    foreach ($f in $files) {
        $obj = Read-JsonFile -Path $f.FullName
        if ($null -eq $obj) { continue }
        # Must have loop_iter to be a candidate
        $hasLoopIter = $false
        $loopIterVal = $null
        if ($obj.PSObject.Properties.Name -contains 'loop_iter') {
            $loopIterVal = $obj.loop_iter
            if ($null -ne $loopIterVal) { $hasLoopIter = $true }
        }
        if (-not $hasLoopIter) { continue }

        # derive slug
        $slug = $null
        if ($obj.PSObject.Properties.Name -contains 'slug' -and $obj.slug) {
            $slug = [string]$obj.slug
        } else {
            $slug = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
        }

        if ($Exclude -contains $slug) { continue }

        $focus = $null
        if ($obj.PSObject.Properties.Name -contains 'focus_intent') { $focus = [string]$obj.focus_intent }
        elseif ($obj.PSObject.Properties.Name -contains 'current_focus') { $focus = [string]$obj.current_focus }
        elseif ($obj.PSObject.Properties.Name -contains 'loop_goal') { $focus = [string]$obj.loop_goal }
        else { $focus = '' }

        $results += [PSCustomObject]@{
            Slug = $slug
            Path = $f.FullName
            MtimeUtc = $f.LastWriteTimeUtc
            LoopIter = $loopIterVal
            Focus = $focus
            Display = ($(if ($obj.PSObject.Properties.Name -contains 'agent_display') { $obj.agent_display } else { $slug }))
        }
    }
    return $results
}

function Build-Poke-Body {
    param([string]$Signal, [int]$Tick)
    $b = "Operator hard-canonical 2026-05-25T02:18Z: 'make it aggressive and have agents relentlessly pursue goal'. " +
         "Your last $Tick ticks show $Signal. Per CLAUDE.md LOOP MODE rules 1-2: immediately start next iteration in SAME turn. " +
         "If genuinely blocked: write a 1-line block reason to OPERATOR-ACTION-QUEUE.md AND ScheduleWakeup cap 270s. DO NOT just end turn."
    return $b
}

function Write-Poke {
    param([string]$Slug, [string]$Signal, [int]$Tick, [bool]$DryRun)
    $inboxDir = Join-Path $InboxRoot $Slug
    if (-not (Test-Path $inboxDir)) {
        if ($DryRun) {
            return @{ Path = (Join-Path $inboxDir ((Utc-Stamp) + '-from-loop-watchdog-poke.json')); Wrote = $false; Reason = 'inbox-dir-missing-would-create' }
        }
        New-Item -ItemType Directory -Path $inboxDir -Force | Out-Null
    }
    $fname = (Utc-Stamp) + '-from-loop-watchdog-poke.json'
    $fpath = Join-Path $inboxDir $fname
    $msg = [ordered]@{
        schema_version = 'sinister.cross-agent-msg.v1'
        ts_utc = (Utc-Now)
        from_slug = 'loop-relentless-watchdog'
        from_display = 'Loop Watchdog'
        to_slug = $Slug
        priority = 'high'
        kind = 'loop-poke'
        subject = 'STOP STOPPING - keep iterating on your loop goal'
        body = (Build-Poke-Body -Signal $Signal -Tick $Tick)
        stall_signal = $Signal
        tick_count = $Tick
        expected_action = 'resume iteration OR write block + ScheduleWakeup OR address operator interrupt'
        author = 'RKOJ-ELENO :: 2026-05-25'
    }
    if ($DryRun) {
        return @{ Path = $fpath; Wrote = $false; Reason = 'dry-run' }
    }
    $json = ($msg | ConvertTo-Json -Depth 5)
    Write-Utf8NoBom -Path $fpath -Content $json
    return @{ Path = $fpath; Wrote = $true; Reason = 'ok' }
}

function Surface-To-Operator-Queue {
    param([int]$StallCount, [string[]]$Slugs)
    if (-not (Test-Path $QueuePath)) { return $false }
    $stamp = Utc-Now
    $slugList = ($Slugs -join ', ')
    $row = "`n- [ ] $stamp loop-relentless-watchdog: $StallCount stalled loop=on agents in one cycle ($slugList) - fleet-level issue, NOT individual poke. Investigate spawn pipeline / API throttle / mass blocker.`n"
    try {
        Add-Content -LiteralPath $QueuePath -Value $row -Encoding UTF8
        return $true
    } catch {
        return $false
    }
}

# ---------- action: Status ----------------------------------------------
if ($Action -eq 'Status') {
    $state = Load-State
    Write-Output "==> loop-relentless-watchdog state @ $(Utc-Now)"
    Write-Output ("    state path     : " + $StatePath)
    if (-not (Test-Path $StatePath)) {
        Write-Output "    (no state file yet; will be created on first Scan)"
        exit 0
    }
    Write-Output ("    last_tick_utc  : " + $state['last_tick_utc'])
    Write-Output ("    tick_count     : " + $state['tick_count'])
    Write-Output ("    agents tracked : " + ($state['agents'].Keys.Count))
    foreach ($slug in ($state['agents'].Keys | Sort-Object)) {
        $a = $state['agents'][$slug]
        $f = if ($a.last_focus) { ($a.last_focus.ToString()).Substring(0, [Math]::Min(60, $a.last_focus.ToString().Length)) } else { '(none)' }
        Write-Output ("      - {0,-30} iter={1,-4} sameFocusTicks={2} sameIterTicks={3} focus='{4}...'" -f $slug, $a.last_iter, $a.ticks_same_focus, $a.ticks_same_iter, $f)
    }
    exit 0
}

# ---------- action: Reset -----------------------------------------------
if ($Action -eq 'Reset') {
    if (Test-Path $StatePath) {
        Remove-Item -LiteralPath $StatePath -Force
        Write-Output "OK: watchdog state cleared ($StatePath)"
    } else {
        Write-Output "(no state file present; nothing to clear)"
    }
    exit 0
}

# ---------- action: Scan / DryRun ---------------------------------------
$isDryRun = ($Action -eq 'DryRun')
$lockFocus = 'loop-watchdog-state'
$lockAcquired = Try-MeshLock -Focus $lockFocus -TtlSec 120
if (-not $lockAcquired) {
    Write-Output "WARN: could not acquire mesh-coord lock on '$lockFocus'; proceeding without lock (state may race)"
}

try {
    $state = Load-State
    $state['tick_count'] = [int]$state['tick_count'] + 1
    $cycleId = "tick-$($state['tick_count'])"
    $state['last_tick_utc'] = Utc-Now

    $hbs = Get-LoopHeartbeats
    $now = [DateTime]::UtcNow
    $stalls = @()
    $seenSlugs = @{}

    foreach ($hb in $hbs) {
        $seenSlugs[$hb.Slug] = $true
        $prev = $null
        if ($state['agents'].ContainsKey($hb.Slug)) {
            $prev = $state['agents'][$hb.Slug]
        }

        $ageMin = [Math]::Round(($now - $hb.MtimeUtc).TotalMinutes, 1)
        $heartbeatStale = ($ageMin -gt $HeartbeatStaleMinutes)

        # Update consecutive-tick counters
        $ticksSameFocus = 1
        $ticksSameIter = 1
        if ($null -ne $prev) {
            if ($prev.last_focus -and ($prev.last_focus -eq $hb.Focus) -and $hb.Focus) {
                $ticksSameFocus = [int]$prev.ticks_same_focus + 1
            }
            if (($null -ne $prev.last_iter) -and ([string]$prev.last_iter -eq [string]$hb.LoopIter)) {
                $ticksSameIter = [int]$prev.ticks_same_iter + 1
            }
        }

        $focusStuck = ($ticksSameFocus -ge $TickThreshold)
        $iterStalled = ($ticksSameIter -ge $TickThreshold)

        $stallSignals = @()
        if ($heartbeatStale) { $stallSignals += "heartbeat_stale(${ageMin}min)" }
        if ($focusStuck) { $stallSignals += "focus_stuck($ticksSameFocus ticks)" }
        if ($iterStalled) { $stallSignals += "iter_stalled(iter=$($hb.LoopIter) x$ticksSameIter ticks)" }

        $isStalled = ($stallSignals.Count -gt 0)

        # dedup: only poke once per cycle per slug
        $lastPokeCycle = $null
        if ($null -ne $prev -and $prev.last_poke_cycle_id) { $lastPokeCycle = $prev.last_poke_cycle_id }
        $alreadyPokedThisCycle = ($lastPokeCycle -eq $cycleId)

        $agentRow = @{
            last_focus = $hb.Focus
            last_iter = $hb.LoopIter
            ticks_same_focus = $ticksSameFocus
            ticks_same_iter = $ticksSameIter
            last_seen_utc = (Utc-Now)
            last_mtime_utc = $hb.MtimeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ")
            last_age_min = $ageMin
            last_poke_cycle_id = $lastPokeCycle
        }

        if ($isStalled -and -not $alreadyPokedThisCycle) {
            $stalls += [PSCustomObject]@{
                Slug = $hb.Slug
                Display = $hb.Display
                Signals = ($stallSignals -join ' + ')
                Focus = $hb.Focus
                LoopIter = $hb.LoopIter
                AgeMin = $ageMin
                TicksSameFocus = $ticksSameFocus
                TicksSameIter = $ticksSameIter
                AgentRow = $agentRow
            }
        } else {
            $state['agents'][$hb.Slug] = $agentRow
        }
    }

    # Apply cap + decide pokes
    $pokes = @()
    $stallCount = $stalls.Count
    $surfacedQueue = $false

    if ($stallCount -ge $MaxPokesPerRun) {
        # Fleet-level problem: surface to OPERATOR-ACTION-QUEUE instead of mass-poking
        if (-not $isDryRun) {
            $surfacedQueue = Surface-To-Operator-Queue -StallCount $stallCount -Slugs ($stalls | ForEach-Object { $_.Slug })
        }
        Write-Output "WARN: $stallCount stalled loop=on agents detected (>= cap of $MaxPokesPerRun) -- surfacing to OPERATOR-ACTION-QUEUE, NOT mass-poking."
        # Still update state for tracking (don't poke)
        foreach ($s in $stalls) {
            $state['agents'][$s.Slug] = $s.AgentRow
        }
    } else {
        foreach ($s in $stalls) {
            $writeRes = Write-Poke -Slug $s.Slug -Signal $s.Signals -Tick ($s.TicksSameFocus + $s.TicksSameIter) -DryRun:$isDryRun
            $pokes += [PSCustomObject]@{
                Slug = $s.Slug
                Signals = $s.Signals
                Wrote = $writeRes.Wrote
                Path = $writeRes.Path
                Reason = $writeRes.Reason
            }
            $agentRow = $s.AgentRow
            if ($writeRes.Wrote) {
                $agentRow['last_poke_cycle_id'] = $cycleId
                $agentRow['last_poke_utc'] = Utc-Now
            }
            $state['agents'][$s.Slug] = $agentRow
        }
    }

    # Prune state for slugs we did not see this scan (heartbeat removed / exclude added)
    $toRemove = @()
    foreach ($k in @($state['agents'].Keys)) {
        if (-not $seenSlugs.ContainsKey($k)) { $toRemove += $k }
    }
    foreach ($k in $toRemove) { [void]$state['agents'].Remove($k) }

    if (-not $isDryRun) {
        Save-State -State $state
    }

    # Report
    Write-Output "==> loop-relentless-watchdog $Action @ $(Utc-Now) (cycle $cycleId)"
    Write-Output ("    heartbeats scanned (loop_iter present, not excluded): " + $hbs.Count)
    Write-Output ("    stalls detected this run: " + $stallCount)
    if ($stallCount -gt 0) {
        foreach ($s in $stalls) {
            Write-Output ("      STALL  slug={0,-28} signals={1}" -f $s.Slug, $s.Signals)
        }
    }
    Write-Output ("    pokes written (or would-be in DryRun): " + ($pokes | Where-Object { $_.Wrote -or $isDryRun } | Measure-Object).Count)
    foreach ($p in $pokes) {
        $tag = if ($isDryRun) { '[DRY]' } elseif ($p.Wrote) { '[OK ]' } else { '[SKIP]' }
        Write-Output ("      $tag slug={0,-28} -> {1}" -f $p.Slug, $p.Path)
    }
    if ($surfacedQueue) {
        Write-Output "    (surfaced fleet-level row to OPERATOR-ACTION-QUEUE.md)"
    }
    if ($isDryRun) {
        Write-Output "    DRY-RUN: state NOT persisted, no inbox writes."
    }
    exit 0
} finally {
    Try-MeshRelease -Focus $lockFocus
}
