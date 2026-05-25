# claude-accounts-status.ps1 -- visible round-robin + per-account status board
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T21:08Z (verbatim):
#   "i still dont see the claude acocunt logins. status bar round robin system."
#
# Renders the live state of _shared-memory/claude-accounts.json in three modes:
#   Board   (default)  full table of every account: enabled / sessions / login-state / 429-state / today's spawn count
#   Bar                single-line status-bar style suitable for banners / cold-start phrase / EVE.exe pane
#   Json               machine-readable structured output
#
# Login-state is inferred from credentials_file presence + ANTHROPIC_API_KEY env:
#   "logged-in (file)"   credentials_file exists on disk
#   "logged-in (env)"    no file but ANTHROPIC_API_KEY env is set
#   "not-logged-in"      neither
#
# Round-robin cursor is read from cfg.last_rotation_index; the NEXT account to spawn is
# the next ENABLED row after that cursor.

[CmdletBinding()]
param(
    [ValidateSet('Board','Bar','Json')] [string]$Mode = 'Board',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$AccountsFile = Join-Path $SanctumRoot '_shared-memory\claude-accounts.json'
if (-not (Test-Path $AccountsFile)) {
    Write-Host "ERR: $AccountsFile not found"
    exit 1
}

$cfg = Get-Content -LiteralPath $AccountsFile -Raw -Encoding UTF8 | ConvertFrom-Json
$script:DefaultAccountName = $cfg.default

function Login-State { param($Account)
    # Priority order:
    #   (1) per-account credentials_file (multi-account rotation when set up)
    #   (2) ANTHROPIC_API_KEY env var (api-key mode)
    #   (3) ~/.claude/.credentials.json (canonical Claude Code OAuth -- account-agnostic;
    #       only the "default" account inherits this since it can't be split)
    #   (4) NOT-LOGGED-IN
    if ($Account.credentials_file -and (Test-Path $Account.credentials_file)) { return 'logged-in (per-acct file)' }
    if ($Account.env_key -and $env:ANTHROPIC_API_KEY) { return 'logged-in (env)' }
    $oauthFile = Join-Path $env:USERPROFILE '.claude\.credentials.json'
    if ($Account.name -eq $script:DefaultAccountName -and (Test-Path $oauthFile)) {
        return 'logged-in (claude-code oauth)'
    }
    return 'NOT-LOGGED-IN'
}

function Rate-State { param($Account)
    if ($Account.rate_limited_until_utc) {
        try {
            $until = [DateTime]::Parse($Account.rate_limited_until_utc).ToUniversalTime()
            if ($until -gt (Get-Date).ToUniversalTime()) {
                $minLeft = [int]($until - (Get-Date).ToUniversalTime()).TotalMinutes
                return "RATE-LIMITED ${minLeft}m"
            }
        } catch {}
    }
    if ($Account.last_429_at_utc) { return 'recent-429' }
    return 'OK'
}

# Compute next-up cursor for round-robin
$enabled = @($cfg.accounts | Where-Object { $_.enabled -ne $false })
$cursor  = if ($cfg.last_rotation_index -ne $null) { [int]$cfg.last_rotation_index } else { -1 }
$nextIdx = if ($enabled.Count -gt 0) { ($cursor + 1) % $enabled.Count } else { -1 }
$nextAccount = if ($nextIdx -ge 0) { $enabled[$nextIdx].name } else { '(no enabled accounts)' }

# RKOJ-ELENO :: 2026-05-24 :: load sibling oauth-health-poller's per-slot score file
# (written by automations/oauth-health-poller.ps1). Missing file == scoring not yet
# enabled -> Score / NextResetIn columns render as '-' with a footer hint.
$HealthFile = Join-Path $SanctumRoot '_shared-memory\oauth-slot-health.json'
$slotScores = @{}
$slotNextReset = @{}
$haveHealth = $false
if (Test-Path $HealthFile) {
    try {
        $hRaw = Get-Content -LiteralPath $HealthFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($hRaw.slots) {
            foreach ($s in $hRaw.slots) {
                if ($s.name) {
                    if ($s.PSObject.Properties.Name -contains 'score') { $slotScores[[string]$s.name] = [string]$s.score }
                    if ($s.PSObject.Properties.Name -contains 'next_reset_in') { $slotNextReset[[string]$s.name] = [string]$s.next_reset_in }
                    elseif ($s.PSObject.Properties.Name -contains 'next_reset_utc') { $slotNextReset[[string]$s.name] = [string]$s.next_reset_utc }
                }
            }
            $haveHealth = $true
        }
    } catch { $haveHealth = $false }
}

switch ($Mode) {

    'Board' {
        Write-Host ""
        Write-Host ("Claude Accounts :: rotation_strategy=" + $cfg.rotation_strategy + "  cursor=" + $cfg.last_rotation_index + "  next-up=" + $nextAccount)
        Write-Host ""
        $rows = @()
        $i = 0
        foreach ($a in $cfg.accounts) {
            $marker = if ($a.name -eq $nextAccount) { '>>' } elseif ($a.enabled -eq $false) { '--' } else { '  ' }
            $sc = if ($slotScores.ContainsKey([string]$a.name)) { $slotScores[[string]$a.name] } else { '-' }
            $nr = if ($slotNextReset.ContainsKey([string]$a.name)) { $slotNextReset[[string]$a.name] } else { '-' }
            $rows += [PSCustomObject]@{
                '  '         = $marker
                Idx          = $i
                Name         = $a.name
                Tier         = $a.plan_tier
                Login        = Login-State -Account $a
                Sessions     = ("" + $a.current_sessions + "/" + $a.max_sessions_concurrent)
                Rate         = Rate-State -Account $a
                Today        = $a.successful_spawns_today
                Score        = $sc
                NextResetIn  = $nr
                Enabled      = if ($a.enabled -eq $false) { 'no' } else { 'yes' }
            }
            $i++
        }
        $rows | Format-Table -AutoSize | Out-String | Write-Host
        $totalEnabled = $enabled.Count
        $totalLoggedIn = @($cfg.accounts | Where-Object { (Login-State -Account $_) -ne 'NOT-LOGGED-IN' }).Count
        $totalActive = ($cfg.accounts | Measure-Object -Property current_sessions -Sum).Sum
        Write-Host ("Summary: enabled=$totalEnabled  logged-in=$totalLoggedIn  total-active-sessions=$totalActive  daily-spawns=" + (($cfg.accounts | Measure-Object -Property successful_spawns_today -Sum).Sum))
        if (-not $haveHealth) {
            Write-Host ""
            Write-Host "  note: Score / NextResetIn unavailable. Run install-oauth-health-poller.ps1 to enable scoring." -ForegroundColor DarkGray
        }
        Write-Host ""
        exit 0
    }

    'Bar' {
        # RKOJ-ELENO :: 2026-05-24 :: auto-best banner. Operator 23:10Z spec:
        #   accts: [>gmail-main 12%<] [outlook 34%] [proton 8%]  rl: 1 (gmail-2 til Mon)  rot=auto-best
        # Active slot wrapped in >...<; rate-limited slots collapsed into a footer count.
        # Active slot inferred from ~/.claude/.credentials.json hash match against
        # per-slot credentials_file when available; else falls back to the round-robin
        # cursor's "next-up" slot.
        $oauthFile = Join-Path $env:USERPROFILE '.claude\.credentials.json'
        $activeHash = $null
        if (Test-Path $oauthFile) {
            try { $activeHash = (Get-FileHash -Algorithm SHA256 -Path $oauthFile -ErrorAction Stop).Hash } catch {}
        }
        $activeSlotName = $null
        if ($activeHash) {
            foreach ($a in $cfg.accounts) {
                if ($a.credentials_file -and (Test-Path $a.credentials_file)) {
                    try {
                        $h2 = (Get-FileHash -Algorithm SHA256 -Path $a.credentials_file -ErrorAction Stop).Hash
                        if ($h2 -eq $activeHash) { $activeSlotName = $a.name; break }
                    } catch {}
                }
            }
        }
        if (-not $activeSlotName) { $activeSlotName = $nextAccount }

        $nowUtc = (Get-Date).ToUniversalTime()
        $frontParts = @()
        $rlCount = 0
        $rlSample = ''
        foreach ($a in $cfg.accounts) {
            if ($a.enabled -eq $false) { continue }
            $isRL = $false
            $rlUntilStr = ''
            if ($a.rate_limited_until_utc) {
                try {
                    $u = [DateTime]::Parse($a.rate_limited_until_utc).ToUniversalTime()
                    if ($u -gt $nowUtc) {
                        $isRL = $true
                        $rlUntilStr = $u.ToString('ddd HH:mm') + 'Z'
                    }
                } catch {}
            }
            if (-not $isRL -and $a.weekly_reset_at_utc) {
                try {
                    $u = [DateTime]::Parse($a.weekly_reset_at_utc).ToUniversalTime()
                    if ($u -gt $nowUtc) {
                        $isRL = $true
                        $rlUntilStr = $u.ToString('ddd HH:mm') + 'Z'
                    }
                } catch {}
            }
            if ($isRL) {
                $rlCount++
                if (-not $rlSample) { $rlSample = "$($a.name) til $rlUntilStr" }
                continue
            }
            $sc = if ($slotScores.ContainsKey([string]$a.name)) { ' ' + $slotScores[[string]$a.name] + '%' } else { '' }
            $tag = "$($a.name)$sc"
            if ($a.name -eq $activeSlotName) {
                $frontParts += "[>$tag<]"
            } else {
                $frontParts += "[$tag]"
            }
        }
        $rotMode = if ($haveHealth) { 'auto-best' } else { 'round-robin' }
        $footer = if ($rlCount -gt 0) { "  rl: $rlCount ($rlSample)" } else { '' }
        Write-Output (($frontParts -join ' ') + $footer + "  rot=$rotMode")
        exit 0
    }

    'Json' {
        $rows = @()
        $i = 0
        foreach ($a in $cfg.accounts) {
            $rows += @{
                idx = $i
                name = $a.name
                tier = $a.plan_tier
                login_state = Login-State -Account $a
                current_sessions = $a.current_sessions
                max_sessions = $a.max_sessions_concurrent
                rate_state = Rate-State -Account $a
                spawns_today = $a.successful_spawns_today
                last_spawn_utc = $a.last_spawn_at_utc
                enabled = ($a.enabled -ne $false)
                is_next = ($a.name -eq $nextAccount)
            }
            $i++
        }
        $out = @{
            rotation_strategy = $cfg.rotation_strategy
            cursor = $cfg.last_rotation_index
            next_up = $nextAccount
            accounts = $rows
        }
        $out | ConvertTo-Json -Depth 5
        exit 0
    }
}
