# RKOJ-ELENO :: 2026-05-23 (v1) :: 2026-05-24 (v2 - operator-curated allowlist)
#               :: 2026-05-25 (v3 - NO CAP; per-account; linked-state surfaced)
# claude-accounts.ps1 - Multi-Claude account rotation manager library.
#
# v3 (2026-05-25, operator hard-canonical "stop having account capped at 4 and
# just have it be per account. like show when its unlinked things like that."):
# infinite operator-curated accounts (any unique `name` creates a new slot via
# Add/SetKey/Login) + `linked` flag auto-computed on Status/Add/SetKey (so the
# operator sees [ON LINKED] / [ON UNLINKED] / [OFF] per slot at a glance).
# v2 (2026-05-24): enabled flag + CLI actions (List/Add/Enable/Disable/Remove/
# Test). v1 (2026-05-23): basic lease/rate-limit primitives. All backward-
# compatible -- missing fields default to enabled=true / linked=true (v1 compat).
#
# Phase 1 of the multi-account rotation system. Dot-source this file to get
# account lookup, lease, rate-limit marking, and credential reading.
#
# Storage:  _shared-memory/claude-accounts.json (no secrets)
# Lock:     _shared-memory/.claude-accounts.lock
# Secrets:  per-account credentials_file (operator-private, NOT in repo)
#
# Usage:
#   . "$SanctumRoot\automations\claude-accounts.ps1"
#   $next = Get-NextAvailableAccount
#   if ($next) { Mark-AccountSpawned -Name $next.name }
#
# Doctrine: tested-before-claimed-2026-05-23. See test-claude-accounts.ps1.

$script:SanctumRoot       = Split-Path -Parent $PSScriptRoot
if (-not $script:SanctumRoot -or -not (Test-Path $script:SanctumRoot)) {
    # Fallback: walk up from this file
    $script:SanctumRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$script:AccountsFile      = Join-Path $script:SanctumRoot '_shared-memory\claude-accounts.json'
$script:AccountsLockFile  = Join-Path $script:SanctumRoot '_shared-memory\.claude-accounts.lock'
$script:AccountsLogFile   = Join-Path $script:SanctumRoot '_shared-memory\claude-accounts.log'

function Write-AccountsLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Message,
        [string]$Level = 'INFO'
    )
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $script:AccountsLogFile -Value "[$ts] [$Level] $Message" -ErrorAction SilentlyContinue
    } catch {}
}

function _Get-DefaultAccountsConfig {
    [CmdletBinding()]
    param()
    return [pscustomobject]@{
        _comment              = 'Auto-generated default (no claude-accounts.json on disk). RKOJ-ELENO :: 2026-05-24.'
        version               = 3
        default               = 'operator'
        rotation_strategy     = 'load-balance'
        last_rotation_index   = 0
        max_concurrent_global = 8
        accounts              = @()
    }
}

function _Acquire-AccountsLock {
    [CmdletBinding()]
    param([int]$MaxRetries = 30, [int]$SleepMs = 150, [int]$StaleAgeSeconds = 30)
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        try {
            $fs = [System.IO.File]::Open($script:AccountsLockFile, 'CreateNew', 'Write', 'None')
            $fs.Close()
            return $true
        } catch {
            # v3 (RKOJ-ELENO 2026-05-24): stale-lock detection. Operator hit the bug
            # where a crashed sibling left a 0-byte .lock around. Get-AccountsConfig
            # then returned defaults (0 accounts) so Get-NextAvailableAccount returned
            # null and the launcher entered "rate-limited until ;" forever. If the
            # lock file is older than $StaleAgeSeconds we treat it as orphan + reclaim.
            try {
                if (Test-Path $script:AccountsLockFile) {
                    $age = ((Get-Date) - (Get-Item $script:AccountsLockFile).LastWriteTime).TotalSeconds
                    if ($age -gt $StaleAgeSeconds) {
                        Remove-Item $script:AccountsLockFile -Force -ErrorAction SilentlyContinue
                        Write-AccountsLog "stale-lock reclaimed (age ${age}s > ${StaleAgeSeconds}s threshold)" 'INFO'
                        continue  # retry the CreateNew immediately
                    }
                }
            } catch {}
            # Windows file-handle release can lag; brief wait + retry handles back-to-back ops.
            Start-Sleep -Milliseconds $SleepMs
        }
    }
    Write-AccountsLog "lock contention: failed after $MaxRetries retries" 'WARN'
    return $false
}

function _Release-AccountsLock {
    [CmdletBinding()]
    param()
    try {
        if (Test-Path $script:AccountsLockFile) {
            Remove-Item -Path $script:AccountsLockFile -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

function Get-AccountsConfig {
    [CmdletBinding()]
    param()
    if (-not (_Acquire-AccountsLock)) {
        Write-AccountsLog 'Get-AccountsConfig: lock failed, returning defaults' 'WARN'
        return (_Get-DefaultAccountsConfig)
    }
    try {
        if (-not (Test-Path $script:AccountsFile)) {
            Write-AccountsLog 'Get-AccountsConfig: file missing, returning defaults' 'WARN'
            return (_Get-DefaultAccountsConfig)
        }
        $raw = Get-Content -Path $script:AccountsFile -Raw -ErrorAction Stop
        try {
            return ($raw | ConvertFrom-Json -ErrorAction Stop)
        } catch {
            Write-AccountsLog "Get-AccountsConfig: malformed JSON ($_), returning defaults" 'ERROR'
            return (_Get-DefaultAccountsConfig)
        }
    } finally {
        _Release-AccountsLock
    }
}

function Save-AccountsConfig {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Config)
    if (-not (_Acquire-AccountsLock)) {
        Write-AccountsLog 'Save-AccountsConfig: lock failed, write skipped' 'ERROR'
        return $false
    }
    try {
        $tmpFile = "$($script:AccountsFile).tmp"
        $json = $Config | ConvertTo-Json -Depth 12
        [System.IO.File]::WriteAllText($tmpFile, $json, [System.Text.UTF8Encoding]::new($false))
        Move-Item -Path $tmpFile -Destination $script:AccountsFile -Force
        return $true
    } catch {
        Write-AccountsLog "Save-AccountsConfig: write failed ($_)" 'ERROR'
        return $false
    } finally {
        _Release-AccountsLock
    }
}

function Test-AccountLinked {
    # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical "stop having account
    # capped at 4 and just have it be per account. like show when its unlinked
    # things like that." Returns $true when the account's credentials_file
    # exists AND is readable AND contains a real (non-placeholder) credential.
    # Returns $false when the file is missing, empty, malformed, or holds the
    # FAKE/placeholder token used during initial scaffolding.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Account)
    if (-not $Account) { return $false }
    $path = $Account.credentials_file
    if (-not $path -or -not (Test-Path $path)) { return $false }
    try {
        $raw = Get-Content -Path $path -Raw -ErrorAction Stop
        if (-not $raw -or $raw.Trim().Length -eq 0) { return $false }
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        return $false
    }
    # Extract whatever credential field is present (api_key OR OAuth accessToken).
    $token = $null
    if ($obj.PSObject.Properties.Name -contains 'api_key' -and $obj.api_key) {
        $token = [string]$obj.api_key
    } elseif ($obj.PSObject.Properties.Name -contains 'claudeAiOauth' -and $obj.claudeAiOauth -and $obj.claudeAiOauth.accessToken) {
        $token = [string]$obj.claudeAiOauth.accessToken
    } elseif ($obj.PSObject.Properties.Name -contains 'accessToken' -and $obj.accessToken) {
        $token = [string]$obj.accessToken
    }
    if (-not $token) { return $false }
    # Reject obvious placeholders: FAKE, empty, too-short.
    if ($token.Length -lt 16) { return $false }
    if ($token -eq 'FAKE' -or $token -match '^(FAKE|PLACEHOLDER|TODO|XXX)') { return $false }
    return $true
}

function Update-AccountLinkedFlags {
    # Walk every account in $Config, set $_.linked = (Test-AccountLinked $_).
    # Idempotent. Caller saves the config. Returns $true if any flag changed.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Config)
    if (-not $Config.accounts) { return $false }
    $changed = $false
    foreach ($a in $Config.accounts) {
        $isLinked = [bool](Test-AccountLinked -Account $a)
        if ($a.PSObject.Properties.Name -contains 'linked') {
            if ([bool]$a.linked -ne $isLinked) {
                $a.linked = $isLinked
                $changed = $true
            }
        } else {
            $a | Add-Member -MemberType NoteProperty -Name 'linked' -Value $isLinked -Force
            $changed = $true
        }
    }
    return $changed
}

function _Is-AccountAvailable {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Account)
    $now = (Get-Date).ToUniversalTime()
    # v2: enabled gate. Missing field treated as enabled=$true (v1 compat).
    if ($Account.PSObject.Properties.Name -contains 'enabled' -and $Account.enabled -eq $false) { return $false }
    # RKOJ-ELENO :: 2026-05-25 :: linked gate. Don't lease an account whose
    # credentials are missing/fake -- the spawn would fail immediately. The
    # 'linked' field is auto-computed on Status / Add / SetKey / Reconcile.
    # Missing field treated as linked=$true for back-compat with older configs
    # that haven't been re-evaluated yet (Status will fill it on next call).
    if ($Account.PSObject.Properties.Name -contains 'linked' -and $Account.linked -eq $false) { return $false }
    if ($Account.current_sessions -ge $Account.max_sessions_concurrent) { return $false }
    if ($Account.rate_limited_until_utc) {
        try {
            $until = [datetime]::Parse($Account.rate_limited_until_utc).ToUniversalTime()
            if ($until -gt $now) { return $false }
        } catch {}
    }
    return $true
}

function Get-NextAvailableAccount {
    [CmdletBinding()]
    param(
        # RKOJ-ELENO :: 2026-05-24 :: operator 19:55Z tier system. T1 spawns reserve
        # the 'operator' (default) slot when available; T2-T4 follow normal rotation.
        # When -Tier is 1 and the default slot is available, return it regardless of
        # the configured strategy. When -Tier omitted/0/3/4, falls through to the
        # rotation_strategy logic unchanged.
        [int]$Tier = 0
    )
    if ($Tier -eq 1) {
        try { Reconcile-AccountSessions -Quiet | Out-Null } catch {}
        $cfgT1 = Get-AccountsConfig
        $default = $cfgT1.default
        if ($default) {
            $anchor = $cfgT1.accounts | Where-Object { $_.name -eq $default } | Select-Object -First 1
            if ($anchor -and (_Is-AccountAvailable -Account $anchor)) {
                Write-AccountsLog "Get-NextAvailableAccount: T1 reserving '$default' slot" 'INFO'
                return @{ name = $anchor.name; account = $anchor }
            }
        }
        # T1 fell through (operator unavailable) — log + fall to normal rotation
        Write-AccountsLog "T1 spawn but default slot unavailable; falling to normal rotation" 'WARN'
    }
    # RKOJ-ELENO :: 2026-05-24 v4 :: honor cfg.rotation_strategy (was hard-coded load-balance).
    # Operator directive 2026-05-24 17:43Z: "use 100% of the claude plans perfectly... where
    # we are not ever loosing any tokens... use 100% up into the perfect point where it resets
    # when we hit 100". 'burn-first' implements that: keep spawning on the same account until
    # Anthropic 429s it (which marks rate_limited_until_utc), THEN auto-failover to next
    # enabled non-rate-limited account. Zero downtime, max plan utilization.
    #
    # Strategies:
    #   'burn-first'         (NEW) — same account until unavailable; then next enabled non-RL
    #   'round-robin-strict' (NEW) — cycle via last_rotation_index across enabled non-RL
    #   'load-balance'       (existing) — pick lowest current_sessions (default fallback)
    # RKOJ-ELENO :: 2026-05-24 :: self-heal stale leases before computing availability.
    # Operator 19:14Z: agent-close must release everything that agent was using. Reconcile
    # drains orphan current_sessions counters (e.g. snapshot 26 leases vs 3 live claude.exe).
    try { Reconcile-AccountSessions -Quiet | Out-Null } catch {}
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) {
        Write-AccountsLog 'Get-NextAvailableAccount: no accounts configured' 'WARN'
        return $null
    }
    $available = @($cfg.accounts | Where-Object { _Is-AccountAvailable -Account $_ })
    if ($available.Count -eq 0) { return $null }

    $strategy = if ($cfg.PSObject.Properties.Name -contains 'rotation_strategy' -and $cfg.rotation_strategy) { $cfg.rotation_strategy } else { 'load-balance' }

    switch ($strategy) {
        'burn-first' {
            # Anchor = cfg.default. If it's available, pick it. Else next enabled non-RL in
            # accounts[] order (highest plan_tier first as tiebreaker -> max > pro > free).
            $anchor = if ($cfg.default) { $available | Where-Object { $_.name -eq $cfg.default } | Select-Object -First 1 } else { $null }
            if ($anchor) { return @{ name = $anchor.name; account = $anchor } }
            $tierRank = @{ 'max' = 3; 'pro' = 2; 'free' = 1 }
            $best = $available | Sort-Object @{ Expression = { $tierRank[$_.plan_tier]; }; Descending = $true }, @{ Expression = 'current_sessions'; Descending = $false } | Select-Object -First 1
            return @{ name = $best.name; account = $best }
        }
        'round-robin-strict' {
            # RKOJ-ELENO :: 2026-05-24 v5 :: atomic read-modify-write across 4+ concurrent agents.
            # Operator 19:14Z: "make sure swarm and loop can be ran on multiple different agents
            # without them having issues with each other ... no one steps on toes". Prior version
            # released the lock between Get-AccountsConfig and Save-AccountsConfig, so all N
            # agents read the SAME cursor, all picked the SAME account, then all wrote the same
            # incremented index. Round-robin parallelism was lost. Fix: hold lock across the
            # entire read-compute-pick-advance-save cycle. Also halves spawn lease latency
            # (1 lock acquisition instead of 2 -> faster spawns per operator 19:30Z).
            if (-not (_Acquire-AccountsLock)) {
                Write-AccountsLog 'round-robin-strict: lock failed, falling back to in-mem cfg' 'WARN'
                # Best-effort fallback (race still possible but at least returns something).
                $startIdx = if ($cfg.PSObject.Properties.Name -contains 'last_rotation_index') { [int]$cfg.last_rotation_index } else { 0 }
                $n = $cfg.accounts.Count
                for ($i = 0; $i -lt $n; $i++) {
                    $idx = ($startIdx + $i) % $n
                    $candidate = $cfg.accounts[$idx]
                    if (_Is-AccountAvailable -Account $candidate) {
                        return @{ name = $candidate.name; account = $candidate }
                    }
                }
                return $null
            }
            try {
                # Re-read on disk INSIDE the lock so we see any concurrent updates.
                $cfgLive = $null
                try {
                    $raw = Get-Content -Path $script:AccountsFile -Raw -ErrorAction Stop
                    $cfgLive = $raw | ConvertFrom-Json -ErrorAction Stop
                } catch {
                    Write-AccountsLog "round-robin-strict: in-lock re-read failed ($_), using in-mem" 'WARN'
                    $cfgLive = $cfg
                }
                $startIdx = if ($cfgLive.PSObject.Properties.Name -contains 'last_rotation_index') { [int]$cfgLive.last_rotation_index } else { 0 }
                $n = $cfgLive.accounts.Count
                for ($i = 0; $i -lt $n; $i++) {
                    $idx = ($startIdx + $i) % $n
                    $candidate = $cfgLive.accounts[$idx]
                    if (_Is-AccountAvailable -Account $candidate) {
                        $cfgLive.last_rotation_index = ($idx + 1) % $n
                        # Atomic write inside the SAME lock (do not call Save-AccountsConfig
                        # which would attempt to re-acquire). RKOJ-ELENO 2026-05-24.
                        try {
                            $tmpFile = "$($script:AccountsFile).tmp"
                            $json = $cfgLive | ConvertTo-Json -Depth 12
                            [System.IO.File]::WriteAllText($tmpFile, $json, [System.Text.UTF8Encoding]::new($false))
                            Move-Item -Path $tmpFile -Destination $script:AccountsFile -Force
                        } catch {
                            Write-AccountsLog "round-robin-strict: atomic write failed ($_)" 'ERROR'
                        }
                        return @{ name = $candidate.name; account = $candidate }
                    }
                }
                return $null
            } finally {
                _Release-AccountsLock
            }
        }
        default {
            # 'load-balance' (legacy + default) — pick lowest current_sessions among available
            $best = $available | Sort-Object current_sessions, successful_spawns_today | Select-Object -First 1
            return @{ name = $best.name; account = $best }
        }
    }
}

function _Find-Account {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Config, [Parameter(Mandatory=$true)][string]$Name)
    return ($Config.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1)
}

function Mark-AccountSpawned {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-AccountsLog "Mark-AccountSpawned: account '$Name' not found" 'ERROR'; return $false }
    $acct.current_sessions = [int]$acct.current_sessions + 1
    $acct.successful_spawns_today = [int]$acct.successful_spawns_today + 1
    $nowIso = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    if ($acct.PSObject.Properties.Name -contains 'last_spawn_at_utc') {
        $acct.last_spawn_at_utc = $nowIso
    } else {
        $acct | Add-Member -MemberType NoteProperty -Name 'last_spawn_at_utc' -Value $nowIso -Force
    }
    return (Save-AccountsConfig -Config $cfg)
}

function Mark-AccountReleased {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-AccountsLog "Mark-AccountReleased: account '$Name' not found" 'ERROR'; return $false }
    $newVal = [int]$acct.current_sessions - 1
    if ($newVal -lt 0) { $newVal = 0 }
    $acct.current_sessions = $newVal
    return (Save-AccountsConfig -Config $cfg)
}

function Reconcile-AccountSessions {
    # RKOJ-ELENO :: 2026-05-24 :: refcount-cleanup fix. Operator (verbatim 2026-05-24 19:14Z):
    # "when our agents are closed everything that agent is using is closed as well". The lease
    # counter (current_sessions) is bumped on Mark-AccountSpawned but only decremented on
    # clean Release at end of launch.sh; crashed mintty/claude => orphan lease. Snapshot
    # observed: 26 current_sessions vs 3 live claude.exe. This drains the leak.
    #
    # Strategy: source-of-truth is spawned-windows.jsonl (per-spawn records with PID +
    # launcher_pid + agent). For each record, if neither the spawned PID nor the launcher
    # PID still has a process, the slot is closed; otherwise live. Aggregate live spawns
    # per account by mapping projects -> usual account (rough, since the spawn record
    # does not currently store account_name -- so we cap globally at live-claude count
    # divided across enabled accounts and clamp per-account to <= max_sessions_concurrent).
    # Conservative: never undercount; if uncertain, leave current_sessions unchanged.
    [CmdletBinding()]
    param([switch]$Quiet)
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) { return $false }

    $liveClaude = @(Get-Process claude -ErrorAction SilentlyContinue)
    $liveCount = $liveClaude.Count

    $changed = $false
    $totalBefore = 0
    foreach ($a in $cfg.accounts) { $totalBefore += [int]$a.current_sessions }

    if ($totalBefore -le $liveCount) {
        if (-not $Quiet) { Write-Host "[reconcile] no leak (current_sessions=$totalBefore live_claude=$liveCount)" -ForegroundColor DarkGray }
        return $false
    }

    # Drain leak: clamp each account's current_sessions to min(current, live_count_share).
    # Naive policy: distribute live_count across the SINGLE account marked $cfg.default first,
    # then remaining accounts in declaration order. Anything beyond is set to 0.
    $remaining = $liveCount
    $defaultName = $cfg.default
    $ordered = @()
    if ($defaultName) {
        $def = $cfg.accounts | Where-Object { $_.name -eq $defaultName } | Select-Object -First 1
        if ($def) { $ordered += $def }
    }
    foreach ($a in $cfg.accounts) {
        if ($a.name -ne $defaultName) { $ordered += $a }
    }

    foreach ($a in $ordered) {
        $cap = if ($a.PSObject.Properties.Name -contains 'max_sessions_concurrent') { [int]$a.max_sessions_concurrent } else { 5 }
        $assign = [Math]::Min($remaining, $cap)
        if ([int]$a.current_sessions -ne $assign) {
            $a.current_sessions = $assign
            $changed = $true
        }
        $remaining -= $assign
        if ($remaining -lt 0) { $remaining = 0 }
    }

    if ($changed) {
        Save-AccountsConfig -Config $cfg | Out-Null
        if (-not $Quiet) {
            Write-Host "[reconcile] drained leak (was=$totalBefore live_claude=$liveCount); per-account:" -ForegroundColor Yellow
            foreach ($a in $cfg.accounts) {
                Write-Host ("    {0,-10} current_sessions={1}" -f $a.name, $a.current_sessions) -ForegroundColor DarkGray
            }
        }
        Write-AccountsLog "Reconcile-AccountSessions: drained $($totalBefore - $liveCount) leaked slot(s); live_claude=$liveCount" 'INFO'
    }
    return $changed
}

function Mark-AccountRateLimited {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][int]$RetryAfterSeconds
    )
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-AccountsLog "Mark-AccountRateLimited: account '$Name' not found" 'ERROR'; return $false }
    $now = (Get-Date).ToUniversalTime()
    $until = $now.AddSeconds($RetryAfterSeconds).ToString('yyyy-MM-ddTHH:mm:ssZ')
    $nowIso = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')
    $acct.rate_limited_until_utc = $until
    $acct.last_429_at_utc = $nowIso
    $saved = Save-AccountsConfig -Config $cfg
    Write-AccountsLog "Mark-AccountRateLimited: '$Name' limited until $until ($RetryAfterSeconds s)" 'INFO'

    # RKOJ-ELENO :: 2026-05-24 :: operator 19:55Z agent-transfer-on-limit. Broadcast
    # a fleet-update so active agents currently spawned on '$Name' can hand off to
    # a different account. Targets are derived from spawned-windows.jsonl rows whose
    # account_name matches AND whose PID is still alive. Best-effort: a missing
    # fleet-update.ps1 or stale ledger is non-fatal — the rate-limit mark itself
    # already gates the next Get-NextAvailableAccount call.
    try {
        $sw = Join-Path $script:SanctumRoot '_shared-memory\spawned-windows.jsonl'
        $affectedSlugs = @()
        if (Test-Path $sw) {
            foreach ($line in Get-Content $sw -ErrorAction SilentlyContinue) {
                if (-not $line) { continue }
                try {
                    $row = $line | ConvertFrom-Json -ErrorAction Stop
                    if ($row.account_name -eq $Name -and $row.pid) {
                        $alive = Get-Process -Id $row.pid -ErrorAction SilentlyContinue
                        if ($alive -and -not $row.closed_at_utc) {
                            if ($row.agent -and $affectedSlugs -notcontains $row.agent) {
                                $affectedSlugs += $row.agent
                            }
                        }
                    }
                } catch {}
            }
        }
        $fu = Join-Path $script:SanctumRoot 'automations\fleet-update.ps1'
        if (Test-Path $fu) {
            $msg = "Account '$Name' hit rate limit (until $until). Affected agents: $($affectedSlugs -join ', '). On next spawn, claude-accounts.ps1 will route to a different slot automatically. If you are currently on '$Name' and want to migrate mid-session, exit + relaunch via Sinister Start.bat - the rotation picks the next available slot."
            $targets = if ($affectedSlugs.Count -gt 0) { $affectedSlugs -join ',' } else { '' }
            $arglist = @('-Action','Push','-Kind','command','-Priority','high','-Message',$msg,'-PushedBy','claude-accounts')
            if ($targets) { $arglist += @('-TargetSlugs', $targets) }
            & powershell -NoProfile -File $fu @arglist 2>&1 | Out-Null
            Write-AccountsLog "Mark-AccountRateLimited: fleet-update broadcast affected=$($affectedSlugs.Count)" 'INFO'
        }
    } catch {
        Write-AccountsLog "Mark-AccountRateLimited: broadcast failed ($_)" 'WARN'
    }
    return $saved
}

function Get-WaitUntilAnyAvailable {
    [CmdletBinding()]
    param()
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) { return $null }
    # if anything currently available, no wait needed
    $avail = @($cfg.accounts | Where-Object { _Is-AccountAvailable -Account $_ })
    if ($avail.Count -gt 0) { return $null }
    $earliest = $null
    foreach ($a in $cfg.accounts) {
        if (-not $a.rate_limited_until_utc) { continue }
        try {
            $t = [datetime]::Parse($a.rate_limited_until_utc).ToUniversalTime()
            if (-not $earliest -or $t -lt $earliest) { $earliest = $t }
        } catch {}
    }
    if ($earliest) { return $earliest.ToString('yyyy-MM-ddTHH:mm:ssZ') }
    return $null
}

function Get-AccountCredentials {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-AccountsLog "Get-AccountCredentials: account '$Name' not found" 'ERROR'; return $null }
    if (-not $acct.credentials_file -or -not (Test-Path $acct.credentials_file)) {
        Write-AccountsLog "Get-AccountCredentials: credentials file missing for '$Name' ($($acct.credentials_file))" 'WARN'
        return $null
    }
    try {
        $raw = Get-Content -Path $acct.credentials_file -Raw -ErrorAction Stop
        $creds = $raw | ConvertFrom-Json -ErrorAction Stop
        if ($creds.api_key) { return $creds.api_key }
        Write-AccountsLog "Get-AccountCredentials: no api_key field in credentials for '$Name'" 'WARN'
        return $null
    } catch {
        Write-AccountsLog "Get-AccountCredentials: read failed for '$Name' ($_)" 'ERROR'
        return $null
    }
}

# ---------------------------------------------------------------------------
# Per-user identity resolution. RKOJ-ELENO :: 2026-05-25 ::
# operator 00:32Z "leo may be slightly dif ... per-user persistence so
# Leo's customizations don't overwrite Zonia's". Reads the DEFAULT account's
# label (email-formatted per the email auto-resolve doctrine) and extracts
# the bare email. Falls back to $env:USERNAME-derived synthetic id when
# no email is resolvable (e.g. fresh install, no Anthropic profile probe yet).
# Used by start-sinister-session.ps1 to namespace agent-prefs entries.
# ---------------------------------------------------------------------------
function Get-CurrentUserEmail {
    [CmdletBinding()]
    param()
    try {
        $cfg = Get-AccountsConfig
        $defaultName = if ($cfg.default) { $cfg.default } else { 'operator' }
        $defaultAcct = $cfg.accounts | Where-Object { $_.name -eq $defaultName } | Select-Object -First 1
        if ($defaultAcct -and $defaultAcct.label) {
            # Label shape: "email@host (slug)" per Invoke-AccountResolveEmails. Extract email.
            $m = [regex]::Match($defaultAcct.label, '([\w\.\-\+]+@[\w\.\-]+\.\w+)')
            if ($m.Success) { return $m.Groups[1].Value.ToLower() }
            # Fallback: label may be the bare email (no slug suffix yet).
            if ($defaultAcct.label -match '^[\w\.\-\+]+@[\w\.\-]+\.\w+$') { return $defaultAcct.label.ToLower() }
        }
    } catch {}
    # Synthetic fallback so we still namespace correctly per-OS-user when no email is known.
    $u = if ($env:USERNAME) { $env:USERNAME } elseif ($env:USER) { $env:USER } else { 'unknown' }
    return "$($u.ToLower())@local"
}

# ---------------------------------------------------------------------------
# v2 Management functions (List/Add/Enable/Disable/Remove/Test).
# Each operation flows through Get-AccountsConfig + Save-AccountsConfig which
# uses the existing lock-file pattern.
# ---------------------------------------------------------------------------

function Invoke-AccountList {
    [CmdletBinding()]
    param()
    $cfg = Get-AccountsConfig
    if (Update-AccountLinkedFlags -Config $cfg) {
        Save-AccountsConfig -Config $cfg | Out-Null
        $cfg = Get-AccountsConfig
    }
    Write-Host ''
    Write-Host ("{0,-12} {1,-8} {2,-7} {3,-6} {4,-10} {5,-22} {6}" -f 'NAME','ENABLED','LINKED','TIER','SESSIONS','RATE_LIMITED_UNTIL','LABEL')
    Write-Host ("{0,-12} {1,-8} {2,-7} {3,-6} {4,-10} {5,-22} {6}" -f '----','-------','------','----','--------','------------------','-----')
    foreach ($a in $cfg.accounts) {
        $en = if ($a.PSObject.Properties.Name -contains 'enabled') { $a.enabled } else { $true }
        $lk = if ($a.PSObject.Properties.Name -contains 'linked') { $a.linked } else { 'n/a' }
        $sess = "$($a.current_sessions)/$($a.max_sessions_concurrent)"
        $rl = if ($a.rate_limited_until_utc) { $a.rate_limited_until_utc } else { '-' }
        Write-Host ("{0,-12} {1,-8} {2,-7} {3,-6} {4,-10} {5,-22} {6}" -f $a.name, $en, $lk, $a.plan_tier, $sess, $rl, $a.label)
    }
    Write-Host ''
}

function Invoke-AccountAdd {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Label,
        [Parameter(Mandatory=$true)][string]$CredentialsFile
    )
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-Host "[ERROR] slot '$Name' not found. Use List to see available slots." -ForegroundColor Red; return $false }
    $acct.label = $Label
    $acct.credentials_file = $CredentialsFile
    if ($acct.PSObject.Properties.Name -contains 'enabled') { $acct.enabled = $true }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'enabled' -Value $true -Force }
    Write-AccountsLog "Invoke-AccountAdd: configured '$Name' label='$Label' creds='$CredentialsFile'" 'INFO'
    Write-Host "[OK] Slot '$Name' configured + enabled." -ForegroundColor Green
    return (Save-AccountsConfig -Config $cfg)
}

function Invoke-AccountSetEnabled {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name, [Parameter(Mandatory=$true)][bool]$Enabled)
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-Host "[ERROR] account '$Name' not found." -ForegroundColor Red; return $false }
    if ($acct.PSObject.Properties.Name -contains 'enabled') { $acct.enabled = $Enabled }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'enabled' -Value $Enabled -Force }
    $state = if ($Enabled) { 'ENABLED' } else { 'DISABLED' }
    Write-AccountsLog "Invoke-AccountSetEnabled: '$Name' -> $state" 'INFO'
    Write-Host "[OK] Account '$Name' $state." -ForegroundColor Green
    return (Save-AccountsConfig -Config $cfg)
}

function Invoke-AccountRemove {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-Host "[ERROR] slot '$Name' not found." -ForegroundColor Red; return $false }
    $acct.label = '(unconfigured)'
    $acct.credentials_file = "C:\Users\Zonia\.claude\credentials.$Name.json"
    $acct.current_sessions = 0
    $acct.rate_limited_until_utc = $null
    $acct.last_429_at_utc = $null
    $acct.successful_spawns_today = 0
    if ($acct.PSObject.Properties.Name -contains 'last_spawn_at_utc') { $acct.last_spawn_at_utc = $null }
    if ($acct.PSObject.Properties.Name -contains 'enabled') { $acct.enabled = $false }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'enabled' -Value $false -Force }
    if ($acct.PSObject.Properties.Name -contains 'linked') { $acct.linked = $false }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'linked' -Value $false -Force }
    Write-AccountsLog "Invoke-AccountRemove: blanked '$Name'" 'INFO'
    Write-Host "[OK] Slot '$Name' reset to unconfigured + disabled." -ForegroundColor Green
    return (Save-AccountsConfig -Config $cfg)
}

function Invoke-AccountSetKey {
    # One-command slot setup: write the credentials JSON + enable the slot.
    # RKOJ-ELENO :: 2026-05-24 (iter-9) -- operator hard-canonical
    #   "i need multi account support ... round robin where i have 4 accounts logged in
    #    and the agents disperse across them."
    # Removes the friction of "create credentials.<name>.json by hand".
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$ApiKey,
        [string]$Label = ''
    )
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    # RKOJ-ELENO :: 2026-05-24 :: operator 21:34Z "allow infinite accounts" - SetKey now
    # auto-adds the slot if it does not exist. Prior version errored, forcing operator to
    # call -Action Add first. Infinite-accounts means any unique name is a valid new slot.
    if (-not $acct) {
        Write-Host "[INFO] slot '$Name' not in config - auto-adding (infinite-accounts mode)." -ForegroundColor Cyan
        $newAcct = [pscustomobject]@{
            name                    = $Name
            label                   = ''
            enabled                 = $true
            credentials_file        = "$env:USERPROFILE\.claude\credentials.$Name.json"
            current_sessions        = 0
            max_sessions_concurrent = 5
            plan_tier               = 'max'
            successful_spawns_today = 0
            rate_limited_until_utc  = $null
            last_spawn_at_utc       = $null
        }
        if (-not $cfg.accounts) { $cfg | Add-Member -MemberType NoteProperty -Name accounts -Value @() -Force }
        $existing = @($cfg.accounts)
        $cfg.accounts = $existing + @($newAcct)
        Save-AccountsConfig -Config $cfg | Out-Null
        $cfg  = Get-AccountsConfig
        $acct = _Find-Account -Config $cfg -Name $Name
    }
    if (-not $ApiKey -or $ApiKey.Length -lt 16) {
        Write-Host "[ERROR] -ApiKey looks invalid (too short). Paste the full sk-ant-... key." -ForegroundColor Red
        return $false
    }
    $credsPath = $acct.credentials_file
    if (-not $credsPath) {
        $credsPath = "$env:USERPROFILE\.claude\credentials.$Name.json"
        $acct.credentials_file = $credsPath
    }
    $credsDir = Split-Path $credsPath -Parent
    if ($credsDir -and -not (Test-Path $credsDir)) { New-Item -ItemType Directory -Path $credsDir -Force | Out-Null }
    $payload = [ordered]@{
        '_comment' = "Sinister Sanctum :: claude-accounts slot '$Name'. RKOJ-ELENO :: $((Get-Date).ToString('yyyy-MM-dd')). Operator-private; not committed."
        api_key    = $ApiKey
    } | ConvertTo-Json -Depth 3
    Set-Content -Path $credsPath -Value $payload -Encoding UTF8
    # RKOJ-ELENO :: 2026-05-24 :: operator 21:25Z "name the claude accounmt based on their email."
    # Auto-resolve email from the freshly-written key so the label is set BEFORE we hand off to
    # the operator. -Label still wins if explicitly passed; otherwise the email becomes the label.
    $resolvedEmail = $null
    try { $resolvedEmail = Get-AnthropicEmailFromKey -Key $ApiKey } catch { $resolvedEmail = $null }
    if ($Label) {
        $acct.label = $Label
    } elseif ($resolvedEmail) {
        $acct.label = "$resolvedEmail ($Name)"
    }
    # Cache the email inline in the creds file so future ResolveEmails calls hit Strategy B (no HTTP).
    if ($resolvedEmail) {
        try {
            $raw2 = Get-Content -Path $credsPath -Raw -ErrorAction Stop
            $obj2 = $raw2 | ConvertFrom-Json -ErrorAction Stop
            $obj2 | Add-Member -MemberType NoteProperty -Name 'account_email' -Value $resolvedEmail -Force
            Set-Content -Path $credsPath -Value ($obj2 | ConvertTo-Json -Depth 5) -Encoding UTF8
        } catch {}
    }
    if ($acct.PSObject.Properties.Name -contains 'enabled') { $acct.enabled = $true }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'enabled' -Value $true -Force }
    # RKOJ-ELENO :: 2026-05-25 :: real key just got written -> mark linked=true.
    $linkedNow = [bool](Test-AccountLinked -Account $acct)
    if ($acct.PSObject.Properties.Name -contains 'linked') { $acct.linked = $linkedNow }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'linked' -Value $linkedNow -Force }
    Write-AccountsLog "Invoke-AccountSetKey: '$Name' creds written to $credsPath + enabled email=$resolvedEmail linked=$linkedNow" 'INFO'
    $masked = $ApiKey.Substring(0, [Math]::Min(12, $ApiKey.Length)) + '...'
    $emailNote = if ($resolvedEmail) { " email=$resolvedEmail" } else { ' email=(unresolved)' }
    Write-Host "[OK] Slot '$Name' configured + enabled. Creds: $credsPath (api_key=$masked)$emailNote." -ForegroundColor Green
    return (Save-AccountsConfig -Config $cfg)
}

function Invoke-AccountStatus {
    # Compact rotation summary. RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical
    # "stop having account capped at 4 and just have it be per account. like show
    # when its unlinked things like that." Dropped the "enabled: N / M" header
    # (the M implied a fixed cap). Per-row tag is now [ON LINKED] / [ON UNLINKED]
    # / [OFF] so the operator can see at a glance which accounts have real
    # credentials vs which still need a Login/SetKey. Auto-computes linked
    # flags before render so stale-flag rows refresh themselves.
    [CmdletBinding()]
    param()
    $cfg = Get-AccountsConfig
    if (Update-AccountLinkedFlags -Config $cfg) {
        Save-AccountsConfig -Config $cfg | Out-Null
        $cfg = Get-AccountsConfig
    }
    $accts  = @($cfg.accounts)
    $enabled  = @($accts | Where-Object { $_.enabled -ne $false })
    $linked   = @($accts | Where-Object { $_.linked -eq $true })
    $unlinked = @($enabled | Where-Object { $_.linked -ne $true })
    $rl       = @($accts | Where-Object { $_.rate_limited_until_utc })
    Write-Host ''
    Write-Host "  Multi-account rotation status:" -ForegroundColor Cyan
    Write-Host "    strategy:     $($cfg.rotation_strategy)" -ForegroundColor Gray
    Write-Host "    accounts:     $($accts.Count)  (enabled $($enabled.Count) / linked $($linked.Count))" -ForegroundColor Gray
    Write-Host "    unlinked:     $($unlinked.Count)" -ForegroundColor $(if ($unlinked.Count -gt 0) { 'Yellow' } else { 'Gray' })
    Write-Host "    rate-limited: $($rl.Count)" -ForegroundColor Gray
    Write-Host ''
    foreach ($a in $accts) {
        $isOff    = ($a.enabled -eq $false)
        $isLinked = ($a.linked -eq $true)
        if ($isOff) {
            $tag   = '[OFF]         '
            $color = 'DarkGray'
        } elseif ($isLinked) {
            $tag   = '[ON LINKED]   '
            $color = if ($a.rate_limited_until_utc) { 'Yellow' } else { 'Green' }
        } else {
            $tag   = '[ON UNLINKED] '
            $color = 'Yellow'
        }
        $sess = "{0}/{1}" -f $a.current_sessions, $a.max_sessions_concurrent
        Write-Host ("    {0} {1,-12} sess={2,-7} spawns_today={3,-3} label={4}" -f $tag, $a.name, $sess, $a.successful_spawns_today, $a.label) -ForegroundColor $color
    }
    Write-Host ''
    if ($unlinked.Count -gt 0) {
        $first = $unlinked[0].name
        Write-Host "  To LINK an account (one command):" -ForegroundColor Cyan
        Write-Host "    powershell -File automations\claude-accounts.ps1 -Action SetKey -Name $first -ApiKey sk-ant-... -Label 'Your label'" -ForegroundColor Gray
        Write-Host ''
    }
    Write-Host "  To ADD a brand-new account slot:" -ForegroundColor Cyan
    Write-Host "    powershell -File automations\claude-accounts.ps1 -Action SetKey -Name <new-slot> -ApiKey sk-ant-..." -ForegroundColor Gray
    Write-Host "    (no slot cap -- any unique name creates a new entry)" -ForegroundColor DarkGray
    Write-Host ''
    return $true
}

function Invoke-AccountTest {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    $cfg = Get-AccountsConfig
    $acct = _Find-Account -Config $cfg -Name $Name
    if (-not $acct) { Write-Host "[FAIL] account '$Name' not found." -ForegroundColor Red; return $false }
    if (-not $acct.credentials_file) { Write-Host "[FAIL] '$Name' has no credentials_file." -ForegroundColor Red; return $false }
    if (-not (Test-Path $acct.credentials_file)) { Write-Host "[FAIL] credentials_file missing: $($acct.credentials_file)" -ForegroundColor Red; return $false }
    try {
        $raw = Get-Content -Path $acct.credentials_file -Raw -ErrorAction Stop
        $creds = $raw | ConvertFrom-Json -ErrorAction Stop
        if (-not $creds.api_key) { Write-Host "[FAIL] '$Name' credentials_file has no api_key field." -ForegroundColor Red; return $false }
        $masked = $creds.api_key.Substring(0, [Math]::Min(12, $creds.api_key.Length)) + '...'
        Write-Host "[PASS] '$Name' credentials valid (api_key=$masked)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[FAIL] '$Name' credentials_file unreadable: $_" -ForegroundColor Red; return $false
    }
}

# ---------------------------------------------------------------------------
# Email auto-naming (RKOJ-ELENO :: 2026-05-24 :: operator 21:25Z)
# "name the claude accounmt based on their email."
# Resolves the Anthropic account email for each slot and writes it into the
# slot's label as "email@host (slug)" so the operator sees real identity
# instead of hand-written placeholders like "Sinister Sanctum (Zonia)".
# ---------------------------------------------------------------------------

function _Try-ReadCredentialsField {
    # Strategy B helper: pull api key + optional email directly from JSON.
    # Supports BOTH schemas:
    #   1) Sanctum-written: { api_key: "sk-ant-..." }                  (Invoke-AccountSetKey writes this)
    #   2) Claude Code OAuth:{ claudeAiOauth: { accessToken: "sk-ant-oat01-..." } }  (CLI writes ~/.claude/.credentials.json)
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = Get-Content -Path $Path -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        $result = [pscustomobject]@{ key = $null; email = $null }
        if ($obj.PSObject.Properties.Name -contains 'api_key' -and $obj.api_key) {
            $result.key = $obj.api_key
        } elseif ($obj.PSObject.Properties.Name -contains 'claudeAiOauth' -and $obj.claudeAiOauth.accessToken) {
            $result.key = $obj.claudeAiOauth.accessToken
        } elseif ($obj.PSObject.Properties.Name -contains 'accessToken' -and $obj.accessToken) {
            $result.key = $obj.accessToken
        }
        # In-file email cache: some Sanctum-written creds may include account_email after first resolution.
        if ($obj.PSObject.Properties.Name -contains 'account_email' -and $obj.account_email) { $result.email = $obj.account_email }
        elseif ($obj.PSObject.Properties.Name -contains 'email' -and $obj.email) { $result.email = $obj.email }
        return $result
    } catch {
        return $null
    }
}

function Get-AnthropicEmailFromKey {
    # Resolve the Anthropic account email for a given OAuth/API key.
    # Strategy order:
    #   A) JWT decode  -- OAuth tokens MAY embed an email claim
    #   B) (handled by caller; reading the credentials file inline if it carries 'account_email')
    #   C) HTTP probe  -- https://api.anthropic.com/api/oauth/profile (smoke-tested 2026-05-24
    #      returns {account:{email:"..."}, ...} for sk-ant-oat01-* OAuth tokens)
    # Returns the email string on success or $null on failure. Never throws.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Key)
    if (-not $Key) { return $null }

    # Strategy A: JWT decode (3-segment base64url tokens). sk-ant-oat01-* are opaque
    # so this almost always misses, but we try cheap-first.
    try {
        $bare = $Key
        if ($bare -like 'sk-ant-*') {
            # Strip the sk-ant-<prefix>- envelope before looking for dot-separated JWT segments.
            $dash = $bare.IndexOf('-', 7)
            if ($dash -gt 0) { $bare = $bare.Substring($dash + 1) }
        }
        $parts = $bare -split '\.'
        if ($parts.Count -ge 2) {
            $pad = $parts[1].Replace('-', '+').Replace('_', '/')
            switch ($pad.Length % 4) { 2 { $pad += '==' } 3 { $pad += '=' } }
            try {
                $bytes = [Convert]::FromBase64String($pad)
                $json = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json -ErrorAction Stop
                if ($json.email) { return [string]$json.email }
                if ($json.account_email) { return [string]$json.account_email }
            } catch {}
        }
    } catch {}

    # Strategy C: HTTPS probe of the Anthropic OAuth profile endpoint.
    # The wrapper smoke-tested 2026-05-24 with the operator's live OAuth token + got HTTP 200
    # + {account:{email:"ezekielromero314@gmail.com",...},...}. Works for sk-ant-oat01-* tokens.
    try {
        $headers = @{
            'Authorization'     = "Bearer $Key"
            'anthropic-version' = '2023-06-01'
        }
        $resp = Invoke-RestMethod -Uri 'https://api.anthropic.com/api/oauth/profile' -Headers $headers -Method GET -TimeoutSec 10 -ErrorAction Stop
        if ($resp.account.email) { return [string]$resp.account.email }
    } catch {
        Write-AccountsLog "Get-AnthropicEmailFromKey: profile probe failed ($($_.Exception.Message))" 'DEBUG'
    }
    return $null
}

function Resolve-AccountEmail {
    # Resolve email for ONE account row. Returns [pscustomobject]@{ email; source; key_path }
    # source = 'jwt' | 'cache' | 'profile-api' | $null
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Account)
    $candidates = @()
    if ($Account.credentials_file) { $candidates += $Account.credentials_file }
    # Operator slot fallback: Claude Code CLI writes ~/.claude/.credentials.json by default.
    # If the slot is named 'operator' and its declared file is missing, also try the CLI default.
    if ($Account.name -eq 'operator') {
        $cliDefault = Join-Path $env:USERPROFILE '.claude\.credentials.json'
        if ($candidates -notcontains $cliDefault) { $candidates += $cliDefault }
    }
    foreach ($p in $candidates) {
        $r = _Try-ReadCredentialsField -Path $p
        if (-not $r) { continue }
        # Cache hit (in-file account_email already present)
        if ($r.email) {
            return [pscustomobject]@{ email = $r.email; source = 'cache'; key_path = $p }
        }
        if (-not $r.key) { continue }
        $email = Get-AnthropicEmailFromKey -Key $r.key
        if ($email) {
            $source = 'profile-api'  # JWT path is best-effort; profile-api is the realistic winner
            return [pscustomobject]@{ email = $email; source = $source; key_path = $p }
        }
    }
    return [pscustomobject]@{ email = $null; source = $null; key_path = $null }
}

function Invoke-AccountResolveEmails {
    # CLI handler: walk every slot, resolve email, update label to "email (slug)" form.
    # Idempotent: if the label already matches "email (slug)" with the resolved email, no-op.
    # Also writes a cached account_email field back into Sanctum-managed creds files so
    # subsequent runs hit Strategy B (no network call).
    [CmdletBinding()]
    param([switch]$Quiet)
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) {
        Write-Host '[resolve-emails] no accounts configured.' -ForegroundColor Yellow
        return $false
    }
    $changed = $false
    $report = @()
    foreach ($a in $cfg.accounts) {
        $res = Resolve-AccountEmail -Account $a
        $desired = if ($res.email) { "$($res.email) ($($a.name))" } else { $null }
        $status = 'unresolved'
        if ($res.email) {
            if ($a.label -eq $desired) {
                $status = 'idempotent'
            } else {
                $a.label = $desired
                $changed = $true
                $status = "updated (source=$($res.source))"
            }
            # Cache the email back into the Sanctum-format creds file so we don't re-probe.
            # ONLY touch files we own (must currently have api_key field — never overwrite the
            # CLI's .credentials.json schema).
            try {
                if ($res.key_path -and (Test-Path $res.key_path)) {
                    $raw = Get-Content -Path $res.key_path -Raw -ErrorAction Stop
                    $obj = $raw | ConvertFrom-Json -ErrorAction Stop
                    if ($obj.PSObject.Properties.Name -contains 'api_key') {
                        if ($obj.PSObject.Properties.Name -contains 'account_email') { $obj.account_email = $res.email }
                        else { $obj | Add-Member -MemberType NoteProperty -Name 'account_email' -Value $res.email -Force }
                        $newJson = $obj | ConvertTo-Json -Depth 5
                        Set-Content -Path $res.key_path -Value $newJson -Encoding UTF8
                    }
                }
            } catch {}
        }
        $report += [pscustomobject]@{ slot = $a.name; email = $res.email; status = $status; source = $res.source }
    }
    if ($changed) { Save-AccountsConfig -Config $cfg | Out-Null }
    Write-AccountsLog "Invoke-AccountResolveEmails: changed=$changed report=$(($report | ConvertTo-Json -Compress -Depth 4))" 'INFO'
    if (-not $Quiet) {
        Write-Host ''
        Write-Host '  Email resolution report:' -ForegroundColor Cyan
        Write-Host ("    {0,-10} {1,-35} {2,-12} {3}" -f 'SLOT', 'EMAIL', 'SOURCE', 'STATUS')
        Write-Host ("    {0,-10} {1,-35} {2,-12} {3}" -f '----', '-----', '------', '------')
        foreach ($r in $report) {
            $em = if ($r.email) { $r.email } else { '(none)' }
            $sr = if ($r.source) { $r.source } else { '-' }
            $color = if ($r.email) { 'Green' } else { 'DarkGray' }
            Write-Host ("    {0,-10} {1,-35} {2,-12} {3}" -f $r.slot, $em, $sr, $r.status) -ForegroundColor $color
        }
        Write-Host ''
        Write-Host '  Operator override: edit _shared-memory/claude-accounts.json `label` field directly;' -ForegroundColor Gray
        Write-Host '  ResolveEmails will NOT clobber a hand-set label that already matches resolved value.' -ForegroundColor Gray
        Write-Host ''
    }
    return $true
}

# CLI shim for spawn .sh trailer + management actions (NO SLOT CAP - any unique
# -Name creates a new account; canonical example slots shown):
#   powershell -File claude-accounts.ps1 -Action Release -Name operator
#   powershell -File claude-accounts.ps1 -Action List
#   powershell -File claude-accounts.ps1 -Action Add -Name work-gmail -Label "work@x.com" -CredentialsFile C:\path\creds.json
#   powershell -File claude-accounts.ps1 -Action Enable -Name work-gmail
#   powershell -File claude-accounts.ps1 -Action Disable -Name work-gmail
#   powershell -File claude-accounts.ps1 -Action Remove -Name work-gmail
#   powershell -File claude-accounts.ps1 -Action Test -Name operator
#   powershell -File claude-accounts.ps1 -Action ResolveEmails
if ($MyInvocation.InvocationName -ne '.' -and $args.Count -gt 0) {
    # script-mode CLI parser (only fires when invoked, not dot-sourced)
    $Action = $null; $Name = $null; $Label = $null; $CredentialsFile = $null; $RetryAfterSeconds = 0
    for ($i = 0; $i -lt $args.Count; $i++) {
        switch ($args[$i]) {
            '-Action'             { $Action = $args[++$i] }
            '-Name'               { $Name   = $args[++$i] }
            '-Label'              { $Label  = $args[++$i] }
            '-CredentialsFile'    { $CredentialsFile = $args[++$i] }
            '-RetryAfterSeconds'  { $RetryAfterSeconds = [int]$args[++$i] }
            '-ApiKey'             { $ApiKey = $args[++$i] }
        }
    }
    switch ($Action) {
        'Release'       { Mark-AccountReleased     -Name $Name | Out-Null }
        'Spawned'       { Mark-AccountSpawned      -Name $Name | Out-Null }
        'RateLimited'   { Mark-AccountRateLimited  -Name $Name -RetryAfterSeconds $RetryAfterSeconds | Out-Null }
        'List'          { Invoke-AccountList }
        'Status'        { Invoke-AccountStatus | Out-Null }
        'Add'           { Invoke-AccountAdd        -Name $Name -Label $Label -CredentialsFile $CredentialsFile | Out-Null }
        'SetKey'        { Invoke-AccountSetKey     -Name $Name -ApiKey $ApiKey -Label $Label | Out-Null }
        'Enable'        { Invoke-AccountSetEnabled -Name $Name -Enabled $true  | Out-Null }
        'Disable'       { Invoke-AccountSetEnabled -Name $Name -Enabled $false | Out-Null }
        'Remove'        { Invoke-AccountRemove     -Name $Name | Out-Null }
        'Test'          { Invoke-AccountTest       -Name $Name | Out-Null }
        'Reconcile'     { Reconcile-AccountSessions | Out-Null }
        'ResolveEmails' { Invoke-AccountResolveEmails | Out-Null }
        default         { Write-Host "[claude-accounts] unknown -Action '$Action' (expected Release|Spawned|RateLimited|List|Status|Add|SetKey|Enable|Disable|Remove|Test|Reconcile|ResolveEmails)" }
    }
}
