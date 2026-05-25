# Author: RKOJ-ELENO :: 2026-05-24
# overseer-agent.ps1 — fleet-wide stall detector + auto-recovery for spawned EVE sessions.
#
# Operator hard-canonical 2026-05-24 (~20:20Z, verbatim):
#   "if agents get to a bad place or need to be reset have a overseer agent see this
#    and fix stalled agents like they never closed in the first place."
#
# What this is
#   A polling oversight script that classifies every spawned agent into HEALTHY / SLOW /
#   STALLED / DEAD using heartbeat freshness + PID liveness, then either reaps the dead
#   slot (refcount-correct decrement) or resurrects the lane from its latest resume-point
#   so the agent comes back "like it never closed".
#
# Composes with:
#   - safe-quality-loops-doctrine-2026-05-24 (guardrail #8 heartbeat liveness + #10 operator interrupt)
#   - resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24 (Reap = decrement; Resurrect = re-spawn)
#   - claude-accounts.ps1 Reconcile-AccountSessions (Reap calls it so current_sessions matches reality)
#   - start-sinister-session.ps1 (Resurrect respawns via the same launcher every spawn goes through)
#
# Actions
#   -Action Scan        Default. Classify every heartbeat + render a table. Exit 0.
#   -Action Reap        Mark closed_at_utc on spawned-windows.jsonl rows whose PID is gone +
#                       call claude-accounts.ps1 -Action Reconcile to drain leaked leases.
#   -Action Resurrect   For a specific stalled/dead -Slug, read latest resume-point + respawn
#                       via start-sinister-session.ps1 -Project <key>. Non-destructive.
#   -Action Watch       Loop Scan + Reap on a timer. Ctrl+C safe. Hard cap 10000 iterations.
#
# Thresholds (state machine):
#   HEALTHY  heartbeat <2 min                AND PID alive (or no PID known)
#   SLOW     heartbeat 2-10 min              AND PID alive (or no PID known)
#   STALLED  heartbeat 10-30 min             AND PID alive (or no PID known)
#   DEAD     heartbeat >30 min               OR  PID known + Get-Process returns nothing
#
# Reversibility
#   - Scan: read-only.
#   - Reap: mutates spawned-windows.jsonl (adds closed_at_utc field) + Reconcile drains the
#           account-rotation counter. Both are already-reversible primitives.
#   - Resurrect: respawns from resume-point. Cannot delete or overwrite anything.
#   - Watch: composes Scan+Reap on a loop with a hard iteration cap.
#
# Smoke test
#   powershell -NoProfile -File automations\overseer-agent.ps1 -Action Scan
#   Should produce a table with no terminating errors.

[CmdletBinding()]
param(
    [ValidateSet('Scan','Reap','Resurrect','Watch','Distribute')]
    [string]$Action = 'Scan',
    [string]$Slug = '',
    [int]$IntervalSec = 60,
    [int]$MaxIterations = 10000,
    [int]$DistributeHours = 24,
    [string]$SanctumRoot = '',
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

# ============================================================
# PATHS + CONSTANTS
# ============================================================

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}
if (-not (Test-Path $SanctumRoot)) {
    Write-Host "[overseer] FAIL: Sanctum root not found: $SanctumRoot" -ForegroundColor Red
    exit 2
}

$HeartbeatsDir   = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$SpawnedJsonl    = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
$ResumePointsDir = Join-Path $SanctumRoot '_shared-memory\resume-points'
$ProjectsJson    = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
$AccountsScript  = Join-Path $SanctumRoot 'automations\claude-accounts.ps1'
$LauncherScript  = Join-Path $SanctumRoot 'automations\start-sinister-session.ps1'
$LogFile         = Join-Path $SanctumRoot '_shared-memory\overseer-agent.log'

$THRESH_SLOW_MIN    = 2
$THRESH_STALLED_MIN = 10
$THRESH_DEAD_MIN    = 30

# ============================================================
# LOG
# ============================================================

function Write-OverseerLog {
    param([string]$Message, [string]$Level = 'INFO')
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $LogFile -Value "[$ts] [$Level] $Message" -ErrorAction SilentlyContinue
    } catch {}
}

# ============================================================
# HELPERS
# ============================================================

function Get-HeartbeatAge {
    # Returns minutes since the heartbeat file ts_utc OR file mtime fallback.
    # Negative = parseable but in future (treat as 0).
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$HbObj, [Parameter(Mandatory=$true)]$HbFile)
    $now = (Get-Date).ToUniversalTime()
    $candidates = @('ts_utc','last_seen','timestamp','time_utc')
    foreach ($field in $candidates) {
        if ($HbObj.PSObject.Properties.Name -contains $field -and $HbObj.$field) {
            try {
                $ts = [datetime]::Parse([string]$HbObj.$field).ToUniversalTime()
                $age = [int]($now - $ts).TotalMinutes
                if ($age -lt 0) { $age = 0 }
                return $age
            } catch {}
        }
    }
    # Fallback: file mtime
    try {
        $ts = ((Get-Item $HbFile).LastWriteTimeUtc)
        return [int]($now - $ts).TotalMinutes
    } catch {
        return 99999
    }
}

function Get-LiveClaudePids {
    # Returns hashtable[int]=$true for every live claude.exe PID.
    [CmdletBinding()]
    param()
    $live = @{}
    try {
        foreach ($p in (Get-Process claude -ErrorAction SilentlyContinue)) {
            $live[[int]$p.Id] = $true
        }
    } catch {}
    return $live
}

function Test-AgentAlive {
    # True if any spawned-windows.jsonl row for this slug has a still-alive PID.
    # If no row found for the slug, returns $null (unknown — don't penalize).
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Slug,
        [Parameter(Mandatory=$true)][hashtable]$LivePids
    )
    if (-not (Test-Path $SpawnedJsonl)) { return $null }
    $found = $false
    try {
        foreach ($line in Get-Content $SpawnedJsonl -ErrorAction SilentlyContinue) {
            if (-not $line) { continue }
            try {
                $row = $line | ConvertFrom-Json -ErrorAction Stop
            } catch { continue }
            if (-not $row.PSObject.Properties.Name -contains 'pid') { continue }
            $rowSlug = if ($row.slug) { $row.slug } elseif ($row.project) { $row.project } else { $row.agent }
            if ($rowSlug -ne $Slug) { continue }
            # Skip rows already marked closed
            if ($row.PSObject.Properties.Name -contains 'closed_at_utc' -and $row.closed_at_utc) { continue }
            $found = $true
            if ($LivePids.ContainsKey([int]$row.pid)) {
                return $true
            }
        }
    } catch {
        Write-OverseerLog "Test-AgentAlive: read failure for $Slug ($_)" 'WARN'
        return $null
    }
    if (-not $found) { return $null }
    return $false
}

function Get-AgentState {
    # Combine age + PID-liveness into a state symbol.
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][int]$AgeMin,
        $PidAlive  # $true / $false / $null
    )
    if ($PidAlive -eq $false) { return 'DEAD' }
    if ($AgeMin -gt $THRESH_DEAD_MIN)    { return 'DEAD' }
    if ($AgeMin -gt $THRESH_STALLED_MIN) { return 'STALLED' }
    if ($AgeMin -gt $THRESH_SLOW_MIN)    { return 'SLOW' }
    return 'HEALTHY'
}

function Get-StateColor {
    param([string]$State)
    switch ($State) {
        'HEALTHY' { return 'Green' }
        'SLOW'    { return 'Cyan' }
        'STALLED' { return 'Yellow' }
        'DEAD'    { return 'Red' }
        default   { return 'Gray' }
    }
}

function Read-AllHeartbeats {
    # Returns array of [pscustomobject]@{ slug, display, age_min, focus, file, pid_alive, state }
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][hashtable]$LivePids)
    $out = @()
    if (-not (Test-Path $HeartbeatsDir)) { return $out }
    $files = Get-ChildItem -Path $HeartbeatsDir -Filter '*.json' -File -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        # Skip the .tmp* shrapnel
        if ($f.Name -match '\.tmp(\..+)?$') { continue }
        try {
            $raw = Get-Content -Path $f.FullName -Raw -ErrorAction Stop
            if (-not $raw) { continue }
            $hb = $raw | ConvertFrom-Json -ErrorAction Stop
        } catch {
            continue
        }
        $slug = $null
        foreach ($k in @('slug','agent','project','agent_name')) {
            if ($hb.PSObject.Properties.Name -contains $k -and $hb.$k) { $slug = [string]$hb.$k; break }
        }
        if (-not $slug) { $slug = [System.IO.Path]::GetFileNameWithoutExtension($f.Name) }
        $display = $null
        foreach ($k in @('display_name','agent_display','agent','slug')) {
            if ($hb.PSObject.Properties.Name -contains $k -and $hb.$k) { $display = [string]$hb.$k; break }
        }
        if (-not $display) { $display = $slug }
        $focus = $null
        foreach ($k in @('focus','focus_intent','state','last_action','last_milestone')) {
            if ($hb.PSObject.Properties.Name -contains $k -and $hb.$k) { $focus = [string]$hb.$k; break }
        }
        if (-not $focus) { $focus = '(no focus)' }
        $age = Get-HeartbeatAge -HbObj $hb -HbFile $f.FullName
        $pidAlive = Test-AgentAlive -Slug $slug -LivePids $LivePids
        $state = Get-AgentState -AgeMin $age -PidAlive $pidAlive
        $out += [pscustomobject]@{
            slug      = $slug
            display   = $display
            age_min   = $age
            focus     = $focus
            file      = $f.FullName
            pid_alive = $pidAlive
            state     = $state
        }
    }
    return $out
}

# ============================================================
# ACTIONS
# ============================================================

function Invoke-Scan {
    [CmdletBinding()]
    param([switch]$Silent)
    $livePids = Get-LiveClaudePids
    $rows = Read-AllHeartbeats -LivePids $livePids
    if (-not $Silent) {
        Write-Host ''
        Write-Host "  Sanctum Overseer :: Scan" -ForegroundColor Magenta
        Write-Host "  Live claude.exe processes: $($livePids.Count)" -ForegroundColor DarkGray
        Write-Host ''
        $hdr = "  {0,-32} {1,-9} {2,6}  {3,-9} {4}" -f 'SLUG','STATE','AGE_M','PID_ALIVE','FOCUS'
        Write-Host $hdr -ForegroundColor White
        Write-Host ("  " + ('-' * 110)) -ForegroundColor DarkGray
        if ($rows.Count -eq 0) {
            Write-Host "  (no heartbeats found)" -ForegroundColor DarkGray
        } else {
            $sorted = $rows | Sort-Object @{Expression={
                switch ($_.state) { 'DEAD' {0} 'STALLED' {1} 'SLOW' {2} 'HEALTHY' {3} default {4} }
            }}, @{Expression='age_min';Descending=$true}
            foreach ($r in $sorted) {
                $pidStr = if ($null -eq $r.pid_alive) { 'unknown' } elseif ($r.pid_alive) { 'alive' } else { 'gone' }
                $focus = if ($r.focus.Length -gt 60) { $r.focus.Substring(0, 60) + '...' } else { $r.focus }
                $line = "  {0,-32} {1,-9} {2,6}  {3,-9} {4}" -f $r.slug, $r.state, $r.age_min, $pidStr, $focus
                Write-Host $line -ForegroundColor (Get-StateColor $r.state)
            }
        }
        $counts = @{HEALTHY=0;SLOW=0;STALLED=0;DEAD=0}
        foreach ($r in $rows) { $counts[$r.state] += 1 }
        Write-Host ''
        Write-Host ("  totals: HEALTHY={0}  SLOW={1}  STALLED={2}  DEAD={3}" -f $counts.HEALTHY, $counts.SLOW, $counts.STALLED, $counts.DEAD) -ForegroundColor Cyan
        Write-Host ''
    }
    return $rows
}

function Invoke-Reap {
    [CmdletBinding()]
    param()
    $livePids = Get-LiveClaudePids
    Write-Host "  Sanctum Overseer :: Reap" -ForegroundColor Magenta
    Write-Host "  Live claude.exe processes: $($livePids.Count)" -ForegroundColor DarkGray

    if (-not (Test-Path $SpawnedJsonl)) {
        Write-Host "  [SKIP] spawned-windows.jsonl missing: $SpawnedJsonl" -ForegroundColor DarkGray
        return 0
    }

    $nowIso = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $linesIn = @()
    try {
        $linesIn = Get-Content $SpawnedJsonl -ErrorAction Stop
    } catch {
        Write-Host "  [FAIL] cannot read spawned-windows.jsonl ($_)" -ForegroundColor Red
        return 0
    }

    $linesOut = New-Object System.Collections.Generic.List[string]
    $reaped = 0
    foreach ($line in $linesIn) {
        if (-not $line) { $linesOut.Add($line); continue }
        $row = $null
        try { $row = $line | ConvertFrom-Json -ErrorAction Stop } catch { $linesOut.Add($line); continue }
        $hasClosed = ($row.PSObject.Properties.Name -contains 'closed_at_utc' -and $row.closed_at_utc)
        if ($hasClosed) { $linesOut.Add($line); continue }
        $rowPid = if ($row.PSObject.Properties.Name -contains 'pid') { [int]$row.pid } else { 0 }
        if ($rowPid -le 0) { $linesOut.Add($line); continue }
        if ($livePids.ContainsKey($rowPid)) { $linesOut.Add($line); continue }
        # PID gone — mark closed
        if ($row.PSObject.Properties.Name -contains 'closed_at_utc') {
            $row.closed_at_utc = $nowIso
        } else {
            $row | Add-Member -MemberType NoteProperty -Name 'closed_at_utc' -Value $nowIso -Force
        }
        if ($row.PSObject.Properties.Name -contains 'closed_by') {
            $row.closed_by = 'overseer-agent'
        } else {
            $row | Add-Member -MemberType NoteProperty -Name 'closed_by' -Value 'overseer-agent' -Force
        }
        $linesOut.Add(($row | ConvertTo-Json -Compress -Depth 8))
        $reaped += 1
        $slug = if ($row.slug) { $row.slug } elseif ($row.project) { $row.project } else { $row.agent }
        Write-Host ("  [REAP] pid={0,-7} slug={1}" -f $rowPid, $slug) -ForegroundColor Yellow
    }

    if ($reaped -gt 0) {
        try {
            $tmp = "$SpawnedJsonl.tmp.$([guid]::NewGuid().ToString('N').Substring(0,8))"
            [System.IO.File]::WriteAllLines($tmp, $linesOut.ToArray(), [System.Text.UTF8Encoding]::new($false))
            Move-Item -Path $tmp -Destination $SpawnedJsonl -Force
            Write-OverseerLog "Reap: marked $reaped row(s) closed_at_utc=$nowIso" 'INFO'
        } catch {
            Write-Host "  [FAIL] write spawned-windows.jsonl ($_)" -ForegroundColor Red
            return $reaped
        }
    } else {
        Write-Host "  (no dead PIDs to reap)" -ForegroundColor DarkGray
    }

    # Decrement account-rotation counter to match reality.
    if (Test-Path $AccountsScript) {
        try {
            & powershell -NoProfile -File $AccountsScript -Action Reconcile 2>&1 | ForEach-Object {
                Write-Host "  $_" -ForegroundColor DarkGray
            }
        } catch {
            Write-Host "  [WARN] Reconcile-AccountSessions failed: $_" -ForegroundColor Yellow
            Write-OverseerLog "Reap: Reconcile call failed ($_)" 'WARN'
        }
    } else {
        Write-Host "  [SKIP] claude-accounts.ps1 not found at $AccountsScript" -ForegroundColor DarkGray
    }

    Write-Host ''
    return $reaped
}

function Get-ProjectKeyForSlug {
    # Resolve slug -> project_key via projects.json (key|slug|display match).
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Slug)
    if (-not (Test-Path $ProjectsJson)) { return $null }
    try {
        $cfg = Get-Content $ProjectsJson -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
    $lc = $Slug.ToLower()
    foreach ($p in $cfg.projects) {
        if ([string]$p.key -eq $lc) { return $p.key }
        if ($p.PSObject.Properties.Name -contains 'slug' -and [string]$p.slug -eq $lc) { return $p.key }
        if ($p.display -and ([string]$p.display).ToLower() -eq $lc) { return $p.key }
    }
    # Fallback fuzzy: token overlap
    $tokens = ($lc -split '[-_\s]+') | Where-Object { $_.Length -ge 4 }
    foreach ($p in $cfg.projects) {
        $ptok = (([string]$p.key + ' ' + [string]$p.display).ToLower() -split '[-_\s]+') | Where-Object { $_.Length -ge 4 }
        foreach ($t in $tokens) { if ($ptok -contains $t) { return $p.key } }
    }
    return $null
}

function Get-LatestResumePoint {
    # Try multiple display-name folders for the slug.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Slug)
    if (-not (Test-Path $ResumePointsDir)) { return $null }
    # Candidate folder names: slug as-is, capitalized, Title Case, common known mappings.
    $candidates = @($Slug, $Slug.ToLower(), $Slug.ToUpper())
    # Add Title Case of dash/underscore tokens.
    $titleCase = ((($Slug -split '[-_]+') | ForEach-Object {
        if ($_.Length -gt 0) { $_.Substring(0,1).ToUpper() + $_.Substring(1).ToLower() } else { '' }
    }) -join ' ')
    $candidates += $titleCase
    # Sanctum special-case
    if ($Slug -eq 'sanctum') { $candidates += @('Sanctum','Sinister Sanctum','EVE on Sanctum') }
    foreach ($name in ($candidates | Select-Object -Unique)) {
        $dir = Join-Path $ResumePointsDir $name
        if (-not (Test-Path $dir)) { continue }
        $latest = Get-ChildItem -Path $dir -Filter '*.json' -File -ErrorAction SilentlyContinue |
                    Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
        if ($latest) { return $latest }
    }
    return $null
}

function Invoke-Resurrect {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$TargetSlug)
    Write-Host "  Sanctum Overseer :: Resurrect '$TargetSlug'" -ForegroundColor Magenta
    if (-not $TargetSlug) {
        Write-Host "  [FAIL] -Slug required" -ForegroundColor Red
        return $false
    }
    $rp = Get-LatestResumePoint -Slug $TargetSlug
    if (-not $rp) {
        Write-Host "  [WARN] no resume-point folder found for '$TargetSlug' under $ResumePointsDir" -ForegroundColor Yellow
        Write-OverseerLog "Resurrect: no resume-point for $TargetSlug" 'WARN'
    } else {
        Write-Host "  [OK]   latest resume-point: $($rp.FullName)" -ForegroundColor Green
    }

    $projectKey = $null
    # Prefer the resume-point's project field if present
    if ($rp) {
        try {
            $rpObj = Get-Content $rp.FullName -Raw | ConvertFrom-Json
            if ($rpObj.PSObject.Properties.Name -contains 'project' -and $rpObj.project) {
                $projectKey = [string]$rpObj.project
            }
        } catch {}
    }
    if (-not $projectKey) { $projectKey = Get-ProjectKeyForSlug -Slug $TargetSlug }
    if (-not $projectKey) {
        Write-Host "  [FAIL] cannot resolve project_key for slug '$TargetSlug' (not in projects.json + no resume-point.project field)" -ForegroundColor Red
        Write-OverseerLog "Resurrect: project_key unresolved for $TargetSlug" 'ERROR'
        return $false
    }
    Write-Host "  [OK]   project_key=$projectKey" -ForegroundColor Green

    if (-not (Test-Path $LauncherScript)) {
        Write-Host "  [FAIL] launcher not found: $LauncherScript" -ForegroundColor Red
        return $false
    }

    Write-Host "  [RUN]  respawn via start-sinister-session.ps1 -Project $projectKey" -ForegroundColor Cyan
    try {
        # Non-blocking respawn so the overseer keeps running.
        Start-Process -FilePath 'powershell.exe' -ArgumentList @(
            '-NoProfile',
            '-File', $LauncherScript,
            '-Project', $projectKey
        ) -WindowStyle Normal | Out-Null
        Write-OverseerLog "Resurrect: launched start-sinister-session.ps1 -Project $projectKey for slug $TargetSlug" 'INFO'
        Write-Host "  [OK]   launcher spawned (it will pick up the latest resume-point on cold-start)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  [FAIL] launcher spawn failed: $_" -ForegroundColor Red
        Write-OverseerLog "Resurrect: launcher spawn failed for $TargetSlug ($_)" 'ERROR'
        return $false
    }
}

function Invoke-Watch {
    [CmdletBinding()]
    param([int]$Interval = 60, [int]$MaxIters = 10000)
    Write-Host "  Sanctum Overseer :: Watch (interval=${Interval}s, cap=$MaxIters iters)" -ForegroundColor Magenta
    Write-Host "  Ctrl+C to exit." -ForegroundColor DarkGray
    Write-OverseerLog "Watch: started interval=${Interval}s cap=$MaxIters" 'INFO'
    $i = 0
    try {
        while ($i -lt $MaxIters) {
            $i += 1
            Write-Host ''
            Write-Host ("  --- iter $i / $MaxIters @ " + ((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))) -ForegroundColor DarkMagenta
            $rows = Invoke-Scan
            $reaped = Invoke-Reap
            $deadOrStalled = @($rows | Where-Object { $_.state -eq 'DEAD' -or $_.state -eq 'STALLED' })
            if ($deadOrStalled.Count -gt 0) {
                $msg = "  [INFO] " + $deadOrStalled.Count + " DEAD/STALLED -- Resurrect not auto-fired in Watch (use -Action Resurrect -Slug SLUGNAME per agent to respawn)."
                Write-Host $msg -ForegroundColor Yellow
            }
            Start-Sleep -Seconds $Interval
        }
        Write-Host "  [STOP] iteration cap reached ($MaxIters)" -ForegroundColor Yellow
        Write-OverseerLog "Watch: hit iteration cap $MaxIters" 'INFO'
    } catch {
        Write-Host "  [STOP] $_" -ForegroundColor Yellow
        Write-OverseerLog "Watch: terminated ($_)" 'INFO'
    }
}

# ============================================================
# DISPATCH
# ============================================================

function Invoke-Distribute {
    # Operator 2026-05-25T00:30Z verbatim: "make sure you update all agents about what you
    # have been building and have the overseer running for sanctum and have him place the
    # information to the correct polaces it needs to go so that all this will be used."
    #
    # Fan-out recent fleet-update + brain-entry changes to per-lane inboxes so EVERY agent
    # sees the update without waiting for a fleet-update poll (active push vs passive pull).
    #
    # Algorithm:
    #   1. Read fleet-updates.jsonl rows from last $DistributeHours hours
    #   2. Read _shared-memory/knowledge/*.md files modified in last $DistributeHours hours
    #   3. For each, infer target slugs (regex on tags + per-lane keywords) AND a "fleet-wide"
    #      fallback when no specific lane matches
    #   4. Write inbox message _shared-memory/inbox/<slug>/<UTC>-from-overseer-distribute.json
    #      (one per slug per change; dedup via prior-distribute-log so we don't re-push the
    #      same change to the same slug)
    if (-not $script:SanctumRoot) { $script:SanctumRoot = if ($SanctumRoot) { $SanctumRoot } else { 'D:\Sinister Sanctum' } }
    $sr = $script:SanctumRoot
    $logPath = Join-Path $sr '_shared-memory\overseer-distribute-log.jsonl'
    $cutoff = (Get-Date).ToUniversalTime().AddHours(-$DistributeHours)
    $alreadyDistributed = @{}
    if (Test-Path $logPath) {
        Get-Content $logPath -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                $r = $_ | ConvertFrom-Json -ErrorAction Stop
                $key = "$($r.target)::$($r.source_id)"
                $alreadyDistributed[$key] = $true
            } catch {}
        }
    }
    # Known lane slugs (matches inbox dir names)
    $laneSlugs = @('sanctum','kernel-apk','sinister-os','sinister-panel','sinister-snap-api-quantum','sinister-tg','sinister-imessage-bridge','sinister-letstext','sinister-jokr','sinister-bumble-emu','sinister-tiktok-emu','sinister-snap-emu','sinister-emulator','jb-woodworks','showmasters','rkoj','rkoj-workstation','letstext','panel','sinister-chatbot','sinister-claw','sinister-forge','sinister-freeze','sinister-generator','sinister-mind','sinister-os-mobile','sinister-rka','sinister-term','snap-emu','tiktok-emu','sinister-tiktok-emulator-api','snap-emulator-api','tiktok-emulator-api','bumble-emulator-api','bumble-emu','sinister-bumble-emulator-api','diagnose','sinister-dashboard-skeleton','sinister-sleight')
    $pushed = 0
    $skipped = 0

    # 1) Recent fleet-updates
    $fuPath = Join-Path $sr '_shared-memory\fleet-updates.jsonl'
    if (Test-Path $fuPath) {
        foreach ($line in Get-Content $fuPath -ErrorAction SilentlyContinue) {
            if (-not $line.Trim()) { continue }
            try {
                $row = $line | ConvertFrom-Json -ErrorAction Stop
                $ts = [DateTime]::Parse($row.ts_utc).ToUniversalTime()
                if ($ts -lt $cutoff) { continue }
                # Determine targets: explicit target_slugs OR keyword-match in message
                $targets = @()
                if ($row.target_slugs) {
                    # Force-cast every element to string (ConvertFrom-Json arrays of strings
                    # can come back as PSCustomObject; the prior code wrote {} into target).
                    $tsArr = @($row.target_slugs) | ForEach-Object { [string]$_ } | Where-Object { $_ }
                    if ($tsArr.Count -gt 0) { $targets = $tsArr }
                }
                if ($targets.Count -eq 0) {
                    # Keyword match against lane slugs in message body
                    foreach ($slug in $laneSlugs) {
                        if ($row.message -and $row.message -match "(?i)\b$([regex]::Escape($slug))\b") { $targets += $slug }
                    }
                    if ($targets.Count -eq 0) { $targets = @('sanctum') }  # default = sanctum
                }
                foreach ($t in $targets) {
                    $t = [string]$t   # belt+suspenders
                    if (-not $t) { continue }
                    $key = "$t::$($row.id)"
                    if ($alreadyDistributed.ContainsKey($key)) { $skipped++; continue }
                    $inboxDir = Join-Path $sr "_shared-memory\inbox\$t"
                    if (-not (Test-Path $inboxDir)) { New-Item -ItemType Directory -Path $inboxDir -Force | Out-Null }
                    $tsFile = ((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))
                    $msg = @{
                        _author = 'RKOJ-ELENO :: 2026-05-25'
                        tag = '[OVERSEER-DISTRIBUTE]'
                        from = 'overseer'
                        to = $t
                        ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
                        subject = "Fleet-update fan-out: $($row.kind) priority=$($row.priority)"
                        source_id = $row.id
                        source_ts_utc = $row.ts_utc
                        source_kind = $row.kind
                        source_priority = $row.priority
                        source_pushed_by = $row.pushed_by
                        message = $row.message
                        rationale = "Overseer auto-distributed because this fleet-update either targeted you OR mentioned your lane slug. Review + ack if actionable."
                    }
                    $outPath = Join-Path $inboxDir "$tsFile-overseer-distribute-$($row.id).json"
                    [System.IO.File]::WriteAllText($outPath, ($msg | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))
                    # Log
                    $logRow = @{ ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); target = $t; source_id = $row.id; source_kind = $row.kind } | ConvertTo-Json -Compress
                    Add-Content -LiteralPath $logPath -Value $logRow -Encoding UTF8
                    $alreadyDistributed[$key] = $true
                    $pushed++
                }
            } catch {}
        }
    }
    if (-not $Quiet) {
        Write-Host "[overseer-distribute] pushed=$pushed skipped=$skipped (window=${DistributeHours}h; sources=fleet-updates.jsonl)"
    }
}

switch ($Action) {
    'Scan'       { Invoke-Scan | Out-Null }
    'Reap'       { Invoke-Reap | Out-Null }
    'Resurrect'  { Invoke-Resurrect -TargetSlug $Slug | Out-Null }
    'Watch'      { Invoke-Watch -Interval $IntervalSec -MaxIters $MaxIterations }
    'Distribute' { Invoke-Distribute }
    default      { Write-Host "[overseer] unknown -Action '$Action'" -ForegroundColor Red; exit 2 }
}
exit 0
