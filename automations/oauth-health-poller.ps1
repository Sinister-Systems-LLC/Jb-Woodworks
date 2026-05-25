# oauth-health-poller.ps1 -- Sanctum OAuth slot auto-health poll + best-slot picker
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24 ~23:10Z (verbatim):
#   "this entire round robin needs to be auto. detect the accounts that
#    should be used and what is out of credits etc."
#
# RUNS EVERY 5 MINUTES (scheduled task SinisterOAuthHealthPoll, registered via
# automations/install-oauth-health-poller.ps1). On each tick:
#
#   1. Clear expired rate-limit flags (rate_limited_until_utc < now).
#   2. Clear expired weekly-reset flags (weekly_reset_at_utc < now).
#   3. For each OAuth slot whose credentials file is present, attempt to decode
#      the JWT's `exp` claim and log a WARN if expiry is within 24h.
#   4. Score each slot:
#        availability_score = enabled_factor * not_limited_factor * (1 - usage_pct_5h/100)
#      where:
#        enabled_factor       = 1 if account.enabled, else 0
#        not_limited_factor   = 1 if not currently rate-limited AND not weekly-capped, else 0
#        usage_pct_5h         = fleet-wide 5h usage % (claude-usage-meter); subtracted
#                               because high usage slot is closer to its cap soft-line
#      Range: 0.0 .. 1.0
#   5. Write a per-slot snapshot to _shared-memory/oauth-slot-health.json.
#   6. Update claude-accounts.json `last_rotation_index` to point at the highest-scored slot.
#
# COMPOSES WITH:
#   automations/claude-oauth-accounts.ps1   -- PickBest reads the snapshot
#   automations/claude-wrapper.ps1          -- consumes PickBest pre-spawn
#   automations/claude-usage-meter.ps1      -- usage_pct_5h source
#   automations/start-sinister-session.ps1  -- spawn flow consumes PickBest

[CmdletBinding()]
param(
    [string]$SanctumRoot = '',
    [switch]$Quiet,
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}

$script:AccountsFile = Join-Path $SanctumRoot '_shared-memory\claude-accounts.json'
$script:HealthFile   = Join-Path $SanctumRoot '_shared-memory\oauth-slot-health.json'
$script:LogFile      = Join-Path $SanctumRoot '_shared-memory\oauth-health-poller.log'
$script:UsageMeter   = Join-Path $SanctumRoot 'automations\claude-usage-meter.ps1'

function Write-PollerLog {
    param([string]$Message, [string]$Level = 'INFO')
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $script:LogFile -Value "[$ts] [$Level] $Message" -ErrorAction SilentlyContinue
    } catch {}
}
function Say { param([string]$M, [string]$C = 'DarkGray') if (-not $Quiet) { Write-Host $M -ForegroundColor $C } }

function Try-DecodeJwtExp {
    # Decode a JWT and return its `exp` as a UTC DateTime, or $null.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = Get-Content -Path $Path -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        $tok = $null
        if ($obj.claudeAiOauth -and $obj.claudeAiOauth.accessToken) { $tok = $obj.claudeAiOauth.accessToken }
        elseif ($obj.accessToken) { $tok = $obj.accessToken }
        if (-not $tok) { return $null }
        $parts = $tok -split '\.'
        if ($parts.Count -lt 2) { return $null }
        # Base64URL decode payload.
        $payload = $parts[1].Replace('-', '+').Replace('_', '/')
        switch ($payload.Length % 4) { 2 { $payload += '==' } 3 { $payload += '=' } }
        $bytes = [Convert]::FromBase64String($payload)
        $json  = [Text.Encoding]::UTF8.GetString($bytes)
        $claims = $json | ConvertFrom-Json
        if ($claims.exp) {
            $epoch = [datetime]'1970-01-01T00:00:00Z'
            return ($epoch.AddSeconds([double]$claims.exp)).ToUniversalTime()
        }
    } catch {}
    return $null
}

function Get-FleetUsagePct {
    # Returns 0-100 (int), or 0 on any failure. Best-effort.
    if (-not (Test-Path $script:UsageMeter)) { return 0 }
    try {
        $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script:UsageMeter -Mode Json 2>$null
        $obj = ($out -join "`n") | ConvertFrom-Json -ErrorAction Stop
        if ($obj.pct_used -ne $null) { return [int]$obj.pct_used }
    } catch {}
    return 0
}

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if (-not (Test-Path $script:AccountsFile)) {
    Say "[poller] FAIL accounts file missing: $script:AccountsFile" 'Red'
    Write-PollerLog "FAIL accounts file missing" 'ERROR'
    exit 2
}

$now = (Get-Date).ToUniversalTime()
$cfg = $null
try {
    $cfg = Get-Content $script:AccountsFile -Raw | ConvertFrom-Json
} catch {
    Say "[poller] FAIL could not parse accounts file: $($_.Exception.Message)" 'Red'
    Write-PollerLog "parse-fail: $($_.Exception.Message)" 'ERROR'
    exit 3
}
if (-not $cfg.accounts) {
    Say "[poller] no accounts in config; nothing to poll" 'Yellow'
    exit 0
}

$fleetUsagePct = Get-FleetUsagePct
$slots = @()
$changed = $false

foreach ($a in $cfg.accounts) {
    $name = [string]$a.name
    $mode = if ($a.PSObject.Properties.Name -contains 'auth_mode' -and $a.auth_mode) { $a.auth_mode } else { 'api_key' }
    $enabled = if ($a.PSObject.Properties.Name -contains 'enabled') { [bool]$a.enabled } else { $true }

    # 1. Clear expired rate-limit.
    $rateLimited = $false
    if ($a.rate_limited_until_utc) {
        try {
            $until = ([datetime]::Parse($a.rate_limited_until_utc)).ToUniversalTime()
            if ($until -lt $now) {
                if (-not $DryRun) { $a.rate_limited_until_utc = $null }
                if ($a.PSObject.Properties.Name -contains 'quota_resets_at_utc' -and $a.quota_resets_at_utc -and (-not $DryRun)) {
                    try {
                        $q = ([datetime]::Parse($a.quota_resets_at_utc)).ToUniversalTime()
                        if ($q -lt $now) { $a.quota_resets_at_utc = $null }
                    } catch {}
                }
                $changed = $true
                Write-PollerLog "cleared rate_limited_until_utc for slot=$name (was $until)"
            } else {
                $rateLimited = $true
            }
        } catch {}
    }

    # 2. Clear expired weekly-reset.
    $weeklyCapped = $false
    if ($a.weekly_reset_at_utc) {
        try {
            $w = ([datetime]::Parse($a.weekly_reset_at_utc)).ToUniversalTime()
            if ($w -lt $now) {
                if (-not $DryRun) { $a.weekly_reset_at_utc = $null }
                $changed = $true
                Write-PollerLog "cleared weekly_reset_at_utc for slot=$name (was $w)"
            } else {
                $weeklyCapped = $true
            }
        } catch {}
    }

    # 3. JWT expiry check (OAuth only).
    $jwtExpUtc = $null
    $jwtWarn   = $false
    if ($mode -eq 'oauth' -and $a.credentials_file -and (Test-Path $a.credentials_file)) {
        $jwtExpUtc = Try-DecodeJwtExp -Path $a.credentials_file
        if ($jwtExpUtc -and ($jwtExpUtc - $now).TotalHours -lt 24) {
            $jwtWarn = $true
            Write-PollerLog "slot=$name token expires soon at $jwtExpUtc" 'WARN'
        }
    }

    # 4. Score. enabledFactor + notLimitedFactor are hard gates (0 = excluded);
    # usageFactor floors at 0.1 so a high-usage fleet still leaves SOMETHING > 0
    # to rank against (otherwise rounding pushes every slot to 0 and next_up_slot
    # falls through to "first weekly-capped one we saw"). Range: 0..1.
    $enabledFactor = if ($enabled) { 1.0 } else { 0.0 }
    $notLimitedFactor = if ($rateLimited -or $weeklyCapped) { 0.0 } else { 1.0 }
    $usageFactor = [Math]::Max(0.1, 1.0 - ($fleetUsagePct / 100.0))
    $score = $enabledFactor * $notLimitedFactor * $usageFactor
    # Apply a small bonus ONLY if the slot is otherwise viable (not limited/capped/disabled).
    # Without this guard, a credentials-present-but-weekly-capped slot would still rank
    # above a true zero, defeating the limit gate.
    if ($score -gt 0 -and $a.credentials_file -and (Test-Path $a.credentials_file)) { $score += 0.05 }
    if ($score -gt 1.0) { $score = 1.0 }

    $slots += [pscustomobject]@{
        name                = $name
        auth_mode           = $mode
        enabled             = $enabled
        rate_limited        = $rateLimited
        weekly_capped       = $weeklyCapped
        rate_limited_until_utc = $a.rate_limited_until_utc
        weekly_reset_at_utc = $a.weekly_reset_at_utc
        jwt_exp_utc         = if ($jwtExpUtc) { $jwtExpUtc.ToString('yyyy-MM-ddTHH:mm:ssZ') } else { $null }
        jwt_expiring_soon   = $jwtWarn
        usage_pct_5h        = $fleetUsagePct
        # Sibling claude-oauth-accounts.ps1::PickBest reads `score` (0..100 scale).
        # Keep `availability_score` (0..1) as the local doctrine score; expose
        # `score` as score * 100 so both consumers see the same ranking.
        score               = [Math]::Round($score * 100, 2)
        availability_score  = [Math]::Round($score, 4)
        has_credentials     = ($a.credentials_file -and (Test-Path $a.credentials_file))
    }
}

# 5. Pick highest-scored slot as next-up.
$ranked = @($slots | Sort-Object -Property availability_score -Descending)
$nextUp = if ($ranked.Count -gt 0 -and $ranked[0].availability_score -gt 0) { $ranked[0].name } else { $null }

# 6. Update last_rotation_index to point at the best slot's position in the ENABLED OAuth list
# so the legacy RotateToNext path (which still indexes into eligible accounts) lines up with it.
if ($nextUp -and (-not $DryRun)) {
    $oauthEnabled = @($cfg.accounts | Where-Object {
        $_.PSObject.Properties.Name -contains 'auth_mode' -and $_.auth_mode -eq 'oauth' -and $_.enabled -ne $false -and $_.credentials_file -and (Test-Path $_.credentials_file)
    })
    if ($oauthEnabled.Count -gt 0) {
        $idx = 0
        for ($i = 0; $i -lt $oauthEnabled.Count; $i++) {
            if ($oauthEnabled[$i].name -eq $nextUp) { $idx = $i; break }
        }
        if ($cfg.PSObject.Properties.Name -contains 'last_rotation_index') { $cfg.last_rotation_index = $idx }
        else { $cfg | Add-Member -MemberType NoteProperty -Name 'last_rotation_index' -Value $idx -Force }
        $changed = $true
    }
}

if ($changed -and (-not $DryRun)) {
    try {
        ($cfg | ConvertTo-Json -Depth 10) | Set-Content -Path $script:AccountsFile -Encoding UTF8
        Write-PollerLog "wrote accounts.json (rotation_index updated)"
    } catch {
        Write-PollerLog "WRITE-FAIL accounts.json: $($_.Exception.Message)" 'ERROR'
    }
}

# Snapshot.
$snapshot = [pscustomobject]@{
    measured_at_utc    = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')
    fleet_usage_pct_5h = $fleetUsagePct
    next_up_slot       = $nextUp
    slots              = $slots
    notes              = @(
        'availability_score range 0.0..1.05. PickBest reads slots[].name where score=max.',
        'Snapshot considered stale by PickBest after 10 minutes. Re-run poller every 5m.'
    )
}
try {
    ($snapshot | ConvertTo-Json -Depth 6) | Set-Content -Path $script:HealthFile -Encoding UTF8
} catch {
    Write-PollerLog "WRITE-FAIL health file: $($_.Exception.Message)" 'ERROR'
}

if (-not $Quiet) {
    Write-Host ""
    Write-Host "  [oauth-health-poller] tick @ $($now.ToString('HH:mm:ssZ'))  fleet_usage=${fleetUsagePct}%  next_up=$nextUp" -ForegroundColor Cyan
    foreach ($s in $ranked) {
        $tag = if ($s.rate_limited) { 'LIM' } elseif ($s.weekly_capped) { 'WK ' } elseif (-not $s.enabled) { 'OFF' } else { 'OK ' }
        $color = if ($s.availability_score -gt 0.5) { 'Green' } elseif ($s.availability_score -gt 0) { 'Yellow' } else { 'DarkGray' }
        Write-Host ("    [{0}] {1,-18} mode={2,-7} score={3:F2}  {4}" -f $tag, $s.name, $s.auth_mode, $s.availability_score, $(if ($s.jwt_expiring_soon) { 'JWT<24h' } else { '' })) -ForegroundColor $color
    }
    Write-Host ""
}

exit 0
