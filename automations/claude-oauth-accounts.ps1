# Author: RKOJ-ELENO :: 2026-05-24
# claude-oauth-accounts.ps1 -- OAuth-mode multi-account manager for Claude Code
# Max 20x subscriptions.
#
# Operator hard-canonical 2026-05-24 ~22:50Z (verbatim):
#   "i need you to change how the account system works so we can login accounts
#    and not use api key approach as its not what we want we want logged in
#    claude 20x max session and going off that usage."
#
# WHY THIS EXISTS:
#   Max 20x ($200/mo) subscription quota only applies to OAuth sessions used by
#   Anthropic's first-party apps (Claude.ai web/desktop + Claude Code CLI).
#   API keys hit a SEPARATE pay-as-you-go Console account that does NOT consume
#   Max quota. The fleet must pool Max 20x quota across N logged-in accounts;
#   the only way to do that is OAuth-rotation, not API-key-rotation.
#
# HOW IT WORKS:
#   Claude Code stores its single active OAuth blob at ~/.claude/.credentials.json
#   (JSON shape: {claudeAiOauth:{accessToken,refreshToken,expiresAt,scopes,...}}).
#   The CLI does NOT natively support multi-account isolation. We solve this by
#   keeping per-slot copies at ~/.claude/credentials.<slot>.json and atomically
#   swapping the active slot BEFORE spawn time. The CLI sees one valid OAuth blob
#   per session; rotation = swap-then-spawn.
#
# ACTIONS:
#   Login         -Name <slot>             -- run `claude login` against the slot
#                                             (operator clicks through OAuth in
#                                             browser); capture the blob into
#                                             ~/.claude/credentials.<slot>.json
#   Use           -Name <slot>             -- atomically activate the slot
#                                             (~/.claude/.credentials.json <- slot copy)
#   Active                                 -- print which slot is currently active
#                                             (by content hash compare)
#   List                                   -- list all OAuth slots + state
#   LogoutSlot    -Name <slot>             -- remove ~/.claude/credentials.<slot>.json
#   WhoAmI        -Name <slot>             -- probe Anthropic profile API for email
#   RotateToNext                           -- pick next enabled non-rate-limited
#                                             OAuth slot, call Use on it
#   MarkLimited   -Name <slot> -Until <iso>-- operator-set "limited til monday"
#   Migrate                                -- one-time: add OAuth fields to legacy
#                                             api-key rows (auth_mode, display_name,
#                                             oauth_email, quota_resets_at_utc,
#                                             weekly_reset_at_utc).
#
# COMPOSES WITH:
#   automations/claude-accounts.ps1            -- legacy api-key path (still valid;
#                                                 auth_mode='api_key')
#   automations/claude-usage-meter.ps1         -- meters fleet OAuth transcripts
#   automations/start-sinister-session.ps1     -- spawn flow consumes Use+RotateToNext
#   tools/eve-picker/account_manager.py        -- EVE.exe sub-page consumes via subprocess
#
# CAP-COST HONEST ASSESSMENT:
#   * If Anthropic rate-limits Max 20x by ACCOUNT (per OAuth identity), swapping
#     credentials between N logged-in accounts DOES pool quota. This is the
#     intended green path.
#   * If Anthropic ALSO rate-limits by IP, all N accounts share the local
#     workstation's IP cap and rotation will not help past that ceiling.
#     Operator can mitigate by mesh-routing some spawns through Tailscale exit
#     nodes (out-of-scope for this iter).
#   * Anthropic may detect "account swapping" as suspicious. We do NOT obfuscate
#     anything; this is a legitimate use pattern (one operator, multiple legit
#     accounts they own).

$script:SanctumRoot      = Split-Path -Parent $PSScriptRoot
if (-not $script:SanctumRoot -or -not (Test-Path $script:SanctumRoot)) {
    $script:SanctumRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$script:AccountsFile     = Join-Path $script:SanctumRoot '_shared-memory\claude-accounts.json'
$script:AccountsLockFile = Join-Path $script:SanctumRoot '_shared-memory\.claude-accounts.lock'
$script:OAuthLogFile     = Join-Path $script:SanctumRoot '_shared-memory\claude-oauth-accounts.log'
$script:ClaudeRoot       = Join-Path $env:USERPROFILE '.claude'
$script:ActiveCredsFile  = Join-Path $script:ClaudeRoot '.credentials.json'

function Write-OAuthLog {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Message, [string]$Level = 'INFO')
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $script:OAuthLogFile -Value "[$ts] [$Level] $Message" -ErrorAction SilentlyContinue
    } catch {}
}

# Eagerly load the legacy module so Get-AccountsConfig + Save-AccountsConfig + lock helpers
# are available in the script-level scope. (A lazy-import inside a function dot-sources into
# the FUNCTION scope which makes the symbols invisible to subsequent calls -- bug discovered
# during smoke-test 2026-05-24.)
$script:_AccountsLibLoaded = $false
function _Import-AccountsLib {
    if ($script:_AccountsLibLoaded) { return }
    $lib = Join-Path $script:SanctumRoot 'automations\claude-accounts.ps1'
    if (-not (Test-Path $lib)) {
        throw "claude-accounts.ps1 missing at $lib (required for shared config + lock)."
    }
    # Dot-source at the SCRIPT scope so the imported functions are callable from any
    # function in this module. The `. (Join-Path ...)` form dot-sources into the caller's
    # scope, which is THIS module's script scope when invoked at the module top level (below).
    . $lib
    $script:_AccountsLibLoaded = $true
}
# Module-load-time import (runs in script scope -> Get-AccountsConfig etc. land here).
$_accountsLibPath = Join-Path $script:SanctumRoot 'automations\claude-accounts.ps1'
if (Test-Path $_accountsLibPath) {
    . $_accountsLibPath
    $script:_AccountsLibLoaded = $true
}

function _Slot-CredentialsPath {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    return (Join-Path $script:ClaudeRoot ("credentials.$Name.json"))
}

function _Hash-File {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        return (Get-FileHash -Algorithm SHA256 -Path $Path -ErrorAction Stop).Hash
    } catch { return $null }
}

function _Atomic-Copy {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )
    if (-not (Test-Path $Source)) { throw "Source missing: $Source" }
    $destDir = Split-Path $Destination -Parent
    if ($destDir -and -not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    $tmp = "$Destination.tmp.$([guid]::NewGuid().ToString().Substring(0,8))"
    Copy-Item -Path $Source -Destination $tmp -Force
    Move-Item -Path $tmp -Destination $Destination -Force
}

function _Is-OAuthCredentialsFile {
    # Returns $true if the file at $Path looks like the Claude Code OAuth shape
    # ({claudeAiOauth:{accessToken,refreshToken,expiresAt,...}}). Returns $false
    # for our Sanctum {api_key:"..."} files or missing/unreadable files.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    try {
        $raw = Get-Content -Path $Path -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        if ($obj.PSObject.Properties.Name -contains 'claudeAiOauth' -and $obj.claudeAiOauth.accessToken) {
            return $true
        }
        return $false
    } catch { return $false }
}

function _Try-DecodeOAuthEmail {
    # Best-effort: read an OAuth credentials file and probe Anthropic's profile
    # API for the account email. Returns $null on failure (never throws).
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = Get-Content -Path $Path -Raw -ErrorAction Stop
        $obj = $raw | ConvertFrom-Json -ErrorAction Stop
        $token = $null
        if ($obj.claudeAiOauth -and $obj.claudeAiOauth.accessToken) {
            $token = $obj.claudeAiOauth.accessToken
        } elseif ($obj.accessToken) {
            $token = $obj.accessToken
        } elseif ($obj.api_key) {
            $token = $obj.api_key
        }
        if (-not $token) { return $null }
        # Reuse legacy resolver if loaded; otherwise inline-probe.
        if (Get-Command Get-AnthropicEmailFromKey -ErrorAction SilentlyContinue) {
            return (Get-AnthropicEmailFromKey -Key $token)
        }
        try {
            $headers = @{ 'Authorization' = "Bearer $token"; 'anthropic-version' = '2023-06-01' }
            $resp = Invoke-RestMethod -Uri 'https://api.anthropic.com/api/oauth/profile' -Headers $headers -Method GET -TimeoutSec 10 -ErrorAction Stop
            if ($resp.account.email) { return [string]$resp.account.email }
        } catch {}
    } catch {}
    return $null
}

# ---------------------------------------------------------------------------
# Migration: ensure every account row has auth_mode + display_name +
# oauth_email + quota_resets_at_utc + weekly_reset_at_utc fields. Legacy rows
# default to auth_mode='api_key'. NEW rows added by the operator default to
# auth_mode='oauth'.
# ---------------------------------------------------------------------------

function Invoke-OAuthMigrate {
    [CmdletBinding()]
    param([switch]$Quiet)
    _Import-AccountsLib
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) {
        if (-not $Quiet) { Write-Host '[migrate] no accounts to migrate.' -ForegroundColor Yellow }
        return $true
    }
    $changed = $false
    foreach ($a in $cfg.accounts) {
        if (-not ($a.PSObject.Properties.Name -contains 'auth_mode')) {
            # Detect mode from the existing credentials_file shape.
            $mode = 'api_key'
            if ($a.credentials_file -and (Test-Path $a.credentials_file) -and (_Is-OAuthCredentialsFile -Path $a.credentials_file)) {
                $mode = 'oauth'
            }
            $a | Add-Member -MemberType NoteProperty -Name 'auth_mode' -Value $mode -Force
            $changed = $true
        }
        if (-not ($a.PSObject.Properties.Name -contains 'display_name')) {
            $disp = if ($a.label) { ($a.label -split ' \(')[0].Trim() } else { $a.name }
            $a | Add-Member -MemberType NoteProperty -Name 'display_name' -Value $disp -Force
            $changed = $true
        }
        if (-not ($a.PSObject.Properties.Name -contains 'oauth_email')) {
            $a | Add-Member -MemberType NoteProperty -Name 'oauth_email' -Value $null -Force
            $changed = $true
        }
        if (-not ($a.PSObject.Properties.Name -contains 'quota_resets_at_utc')) {
            $a | Add-Member -MemberType NoteProperty -Name 'quota_resets_at_utc' -Value $null -Force
            $changed = $true
        }
        if (-not ($a.PSObject.Properties.Name -contains 'weekly_reset_at_utc')) {
            $a | Add-Member -MemberType NoteProperty -Name 'weekly_reset_at_utc' -Value $null -Force
            $changed = $true
        }
    }
    if ($changed) {
        Save-AccountsConfig -Config $cfg | Out-Null
        Write-OAuthLog "Invoke-OAuthMigrate: added missing fields to $($cfg.accounts.Count) rows" 'INFO'
        if (-not $Quiet) { Write-Host "[migrate] OK -- added missing OAuth fields to $($cfg.accounts.Count) rows." -ForegroundColor Green }
    } else {
        if (-not $Quiet) { Write-Host '[migrate] no-op -- all rows already have OAuth fields.' -ForegroundColor DarkGray }
    }
    return $true
}

# ---------------------------------------------------------------------------
# Login: capture a fresh OAuth blob for one slot.
# WORKFLOW (operator-driven; we scaffold, operator executes):
#   1. Operator runs: claude-oauth-accounts.ps1 -Action Login -Name <slot>
#   2. Script archives current ~/.claude/.credentials.json (if any) to a safe
#      sideline path.
#   3. Script prints the exact `claude login` command for operator to run
#      INTERACTIVELY in a separate window (browser OAuth flow).
#   4. After operator confirms login complete, script captures the newly-written
#      ~/.claude/.credentials.json into ~/.claude/credentials.<slot>.json.
#   5. Script restores the prior credentials.json so the operator's current
#      session is not disrupted.
#   6. Script writes/updates the slot row with auth_mode=oauth + oauth_email
#      (probed) + credentials_file path.
#
# We do NOT run `claude login` ourselves -- it requires interactive browser
# auth that only the operator can complete.
# ---------------------------------------------------------------------------

function Invoke-OAuthLoginScaffold {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [string]$DisplayName = ''
    )
    _Import-AccountsLib
    if (-not (Test-Path $script:ClaudeRoot)) {
        New-Item -ItemType Directory -Path $script:ClaudeRoot -Force | Out-Null
    }
    $slotCreds  = _Slot-CredentialsPath -Name $Name
    $sideline   = Join-Path $script:ClaudeRoot ".credentials.json.preserved.$Name"
    $hashBefore = _Hash-File -Path $script:ActiveCredsFile

    Write-Host ''
    Write-Host '  --- OAuth Login Scaffold ---' -ForegroundColor Cyan
    Write-Host ''
    Write-Host "  Slot:           $Name" -ForegroundColor White
    Write-Host "  Slot creds:     $slotCreds" -ForegroundColor DarkGray
    Write-Host "  Sideline (bak): $sideline" -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '  STEP 1 of 4: preserving currently-active credentials (if any)' -ForegroundColor Yellow
    if (Test-Path $script:ActiveCredsFile) {
        _Atomic-Copy -Source $script:ActiveCredsFile -Destination $sideline
        Write-Host "    OK -- copied current .credentials.json -> $sideline" -ForegroundColor Green
    } else {
        Write-Host '    (no active credentials.json yet)' -ForegroundColor DarkGray
    }

    Write-Host ''
    Write-Host '  STEP 2 of 4: run claude auth login in a SEPARATE terminal window' -ForegroundColor Yellow
    Write-Host '    Open a NEW PowerShell or bash window and run:' -ForegroundColor White
    Write-Host ''
    Write-Host '        claude auth login' -ForegroundColor Cyan
    Write-Host '        (legacy CLI: `claude login`)' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '    Browser opens to console.anthropic.com OAuth.' -ForegroundColor DarkGray
    Write-Host '    Sign in with the Max 20x account email you want for this slot.' -ForegroundColor DarkGray
    Write-Host '    On success, claude prints "Logged in as ...".' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '    Press Enter HERE when login completes (or X+Enter to abort).' -ForegroundColor White
    $resp = Read-Host '  >'
    if ($resp -match '^(x|X|q|Q)') {
        Write-Host '  Aborted. Restoring sideline.' -ForegroundColor Yellow
        if (Test-Path $sideline) {
            _Atomic-Copy -Source $sideline -Destination $script:ActiveCredsFile
            Remove-Item $sideline -Force -ErrorAction SilentlyContinue
        }
        return $false
    }

    Write-Host ''
    Write-Host '  STEP 3 of 4: capturing freshly-written credentials' -ForegroundColor Yellow
    if (-not (Test-Path $script:ActiveCredsFile)) {
        Write-Host '    FAIL -- .credentials.json not found. Did login succeed?' -ForegroundColor Red
        if (Test-Path $sideline) {
            _Atomic-Copy -Source $sideline -Destination $script:ActiveCredsFile
            Remove-Item $sideline -Force -ErrorAction SilentlyContinue
            Write-Host '    Sideline restored.' -ForegroundColor DarkGray
        }
        return $false
    }
    $hashAfter = _Hash-File -Path $script:ActiveCredsFile
    if ($hashBefore -and ($hashAfter -eq $hashBefore)) {
        Write-Host '    WARN -- .credentials.json hash unchanged. Did you actually log in to a DIFFERENT account?' -ForegroundColor Yellow
        Write-Host '            Continuing anyway -- the slot will mirror the previously-active session.' -ForegroundColor Yellow
    }
    if (-not (_Is-OAuthCredentialsFile -Path $script:ActiveCredsFile)) {
        Write-Host "    FAIL -- $script:ActiveCredsFile is not OAuth shape (missing claudeAiOauth.accessToken)." -ForegroundColor Red
        if (Test-Path $sideline) {
            _Atomic-Copy -Source $sideline -Destination $script:ActiveCredsFile
            Remove-Item $sideline -Force -ErrorAction SilentlyContinue
        }
        return $false
    }
    _Atomic-Copy -Source $script:ActiveCredsFile -Destination $slotCreds
    Write-Host "    OK -- captured slot credentials to $slotCreds" -ForegroundColor Green
    $email = _Try-DecodeOAuthEmail -Path $slotCreds
    if ($email) {
        Write-Host "    Detected email: $email" -ForegroundColor Cyan
    } else {
        Write-Host '    (email probe failed -- can set manually later)' -ForegroundColor DarkGray
    }

    Write-Host ''
    Write-Host '  STEP 4 of 4: restoring previous active credentials' -ForegroundColor Yellow
    if (Test-Path $sideline) {
        _Atomic-Copy -Source $sideline -Destination $script:ActiveCredsFile
        Remove-Item $sideline -Force -ErrorAction SilentlyContinue
        Write-Host "    OK -- restored prior .credentials.json (was: hash $($hashBefore.Substring(0,8))...)." -ForegroundColor Green
    } else {
        Write-Host '    (no prior session to restore; slot is now ALSO the active session)' -ForegroundColor DarkGray
    }

    # Persist the slot row.
    $cfg = Get-AccountsConfig
    $acct = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if (-not $acct) {
        # Auto-add slot (infinite accounts mode).
        $acct = [pscustomobject]@{
            name                    = $Name
            label                   = $(if ($email) { "$email ($Name)" } else { $Name })
            display_name            = $(if ($DisplayName) { $DisplayName } elseif ($email) { ($email -split '@')[0] } else { $Name })
            enabled                 = $true
            auth_mode               = 'oauth'
            oauth_email             = $email
            credentials_file        = $slotCreds
            env_key                 = 'ANTHROPIC_API_KEY'
            current_sessions        = 0
            max_sessions_concurrent = 5
            plan_tier               = 'max'
            successful_spawns_today = 0
            rate_limited_until_utc  = $null
            last_429_at_utc         = $null
            last_spawn_at_utc       = $null
            quota_resets_at_utc     = $null
            weekly_reset_at_utc     = $null
            fleet_share             = 0.0
        }
        if (-not $cfg.accounts) { $cfg | Add-Member -MemberType NoteProperty -Name accounts -Value @() -Force }
        $cfg.accounts = @($cfg.accounts) + @($acct)
    } else {
        $updates = @{
            auth_mode        = 'oauth'
            credentials_file = $slotCreds
            oauth_email      = $email
            enabled          = $true
        }
        if ($DisplayName) { $updates['display_name'] = $DisplayName }
        elseif ($email -and -not ($acct.PSObject.Properties.Name -contains 'display_name' -and $acct.display_name)) {
            $updates['display_name'] = ($email -split '@')[0]
        }
        if ($email -and (-not $acct.label -or $acct.label -match '\(unconfigured\)')) {
            $updates['label'] = "$email ($Name)"
        }
        foreach ($k in $updates.Keys) {
            if ($acct.PSObject.Properties.Name -contains $k) { $acct.$k = $updates[$k] }
            else { $acct | Add-Member -MemberType NoteProperty -Name $k -Value $updates[$k] -Force }
        }
    }
    Save-AccountsConfig -Config $cfg | Out-Null
    Write-OAuthLog "Invoke-OAuthLoginScaffold: slot=$Name email=$email creds=$slotCreds" 'INFO'

    Write-Host ''
    Write-Host '  --- DONE ---' -ForegroundColor Green
    Write-Host "  Slot '$Name' is now an OAuth slot. Next spawn that picks this slot will" -ForegroundColor Green
    Write-Host '  swap its credentials in (claude-oauth-accounts.ps1 -Action Use) before' -ForegroundColor Green
    Write-Host '  starting claude.' -ForegroundColor Green
    Write-Host ''
    return $true
}

function Invoke-OAuthUse {
    # Swap a slot's credentials into ~/.claude/.credentials.json atomically.
    # Backs up the previously-active file to ~/.claude/.credentials.json.<prev>.bak
    # WHERE <prev> = the slot whose hash matches the current active file, or 'unknown'.
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    _Import-AccountsLib
    $slotCreds = _Slot-CredentialsPath -Name $Name
    if (-not (Test-Path $slotCreds)) {
        Write-Host "[oauth-use] FAIL slot '$Name' has no credentials file at $slotCreds. Run Login first." -ForegroundColor Red
        Write-OAuthLog "Invoke-OAuthUse: slot=$Name MISSING $slotCreds" 'ERROR'
        return $false
    }
    if (-not (_Is-OAuthCredentialsFile -Path $slotCreds)) {
        Write-Host "[oauth-use] FAIL slot '$Name' credentials are not OAuth shape -- it may be an api_key slot." -ForegroundColor Red
        return $false
    }
    if (-not (Test-Path $script:ClaudeRoot)) {
        New-Item -ItemType Directory -Path $script:ClaudeRoot -Force | Out-Null
    }
    # Best-effort backup of currently active.
    if (Test-Path $script:ActiveCredsFile) {
        $prev = 'unknown'
        $activeHash = _Hash-File -Path $script:ActiveCredsFile
        $cfg = Get-AccountsConfig
        foreach ($a in $cfg.accounts) {
            if ($a.PSObject.Properties.Name -contains 'credentials_file' -and $a.credentials_file -and (Test-Path $a.credentials_file)) {
                $h = _Hash-File -Path $a.credentials_file
                if ($h -and $h -eq $activeHash) { $prev = $a.name; break }
            }
        }
        $bak = Join-Path $script:ClaudeRoot ".credentials.json.$prev.bak"
        Copy-Item -Path $script:ActiveCredsFile -Destination $bak -Force -ErrorAction SilentlyContinue
    }
    _Atomic-Copy -Source $slotCreds -Destination $script:ActiveCredsFile
    Write-OAuthLog "Invoke-OAuthUse: activated slot=$Name" 'INFO'
    Write-Host "[oauth-use] OK -- active slot is now '$Name'." -ForegroundColor Green
    return $true
}

function Invoke-OAuthActive {
    # Print which slot's credentials match the currently-active .credentials.json.
    [CmdletBinding()]
    param()
    _Import-AccountsLib
    if (-not (Test-Path $script:ActiveCredsFile)) {
        Write-Host '[oauth-active] no .credentials.json present (no active OAuth session).' -ForegroundColor Yellow
        return $null
    }
    $activeHash = _Hash-File -Path $script:ActiveCredsFile
    $cfg = Get-AccountsConfig
    foreach ($a in $cfg.accounts) {
        if (-not ($a.PSObject.Properties.Name -contains 'credentials_file') -or -not $a.credentials_file) { continue }
        if (-not (Test-Path $a.credentials_file)) { continue }
        $h = _Hash-File -Path $a.credentials_file
        if ($h -and $h -eq $activeHash) {
            Write-Host ("[oauth-active] slot='{0}' email='{1}' tier='{2}'" -f $a.name, $a.oauth_email, $a.plan_tier) -ForegroundColor Green
            return $a.name
        }
    }
    Write-Host '[oauth-active] active .credentials.json does NOT match any tracked slot.' -ForegroundColor Yellow
    Write-Host '               (likely the operator ran claude login outside the Sanctum flow.' -ForegroundColor DarkGray
    Write-Host '                Run -Action Login -Name <slot> to capture it into a slot.)' -ForegroundColor DarkGray
    return $null
}

function Invoke-OAuthList {
    [CmdletBinding()]
    param()
    _Import-AccountsLib
    $cfg = Get-AccountsConfig
    $activeHash = if (Test-Path $script:ActiveCredsFile) { _Hash-File -Path $script:ActiveCredsFile } else { $null }
    Write-Host ''
    Write-Host ("  {0,-3} {1,-18} {2,-6} {3,-9} {4,-32} {5,-7} {6}" -f 'ACT','SLOT','MODE','ENABLED','EMAIL','TIER','LIMITED_UNTIL') -ForegroundColor Cyan
    Write-Host ("  {0,-3} {1,-18} {2,-6} {3,-9} {4,-32} {5,-7} {6}" -f '---','----','----','-------','-----','----','-------------') -ForegroundColor DarkGray
    foreach ($a in $cfg.accounts) {
        $mode = if ($a.PSObject.Properties.Name -contains 'auth_mode' -and $a.auth_mode) { $a.auth_mode } else { 'api_key' }
        $en = if ($a.PSObject.Properties.Name -contains 'enabled') { $a.enabled } else { $true }
        $email = if ($a.PSObject.Properties.Name -contains 'oauth_email' -and $a.oauth_email) { $a.oauth_email } else { '-' }
        $tier = if ($a.plan_tier) { $a.plan_tier } else { '-' }
        $lim  = if ($a.weekly_reset_at_utc) { "wk:$($a.weekly_reset_at_utc)" } elseif ($a.rate_limited_until_utc) { $a.rate_limited_until_utc } else { '-' }
        $act = '   '
        if ($activeHash -and $a.credentials_file -and (Test-Path $a.credentials_file)) {
            $h = _Hash-File -Path $a.credentials_file
            if ($h -and $h -eq $activeHash) { $act = ' * ' }
        }
        $color = if ($mode -eq 'oauth') { 'Green' } else { 'DarkGray' }
        Write-Host ("  {0,-3} {1,-18} {2,-6} {3,-9} {4,-32} {5,-7} {6}" -f $act, $a.name, $mode, $en, $email, $tier, $lim) -ForegroundColor $color
    }
    Write-Host ''
    Write-Host '  * = currently active OAuth slot (.credentials.json matches this slot)' -ForegroundColor DarkGray
    Write-Host ''
    return $true
}

function Invoke-OAuthLogoutSlot {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    _Import-AccountsLib
    $slotCreds = _Slot-CredentialsPath -Name $Name
    $wasActive = $false
    if ((Test-Path $script:ActiveCredsFile) -and (Test-Path $slotCreds)) {
        $h1 = _Hash-File -Path $script:ActiveCredsFile
        $h2 = _Hash-File -Path $slotCreds
        if ($h1 -and $h2 -and $h1 -eq $h2) { $wasActive = $true }
    }
    if (Test-Path $slotCreds) {
        Remove-Item -Path $slotCreds -Force -ErrorAction SilentlyContinue
        Write-Host "[oauth-logout] removed $slotCreds" -ForegroundColor Green
    } else {
        Write-Host "[oauth-logout] no creds file for slot '$Name' (already logged out)." -ForegroundColor DarkGray
    }
    if ($wasActive -and (Test-Path $script:ActiveCredsFile)) {
        Remove-Item -Path $script:ActiveCredsFile -Force -ErrorAction SilentlyContinue
        Write-Host '[oauth-logout] also cleared active .credentials.json (was the active slot).' -ForegroundColor Yellow
    }
    # Mark slot disabled in config + clear oauth_email.
    $cfg = Get-AccountsConfig
    $acct = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if ($acct) {
        if ($acct.PSObject.Properties.Name -contains 'enabled') { $acct.enabled = $false }
        if ($acct.PSObject.Properties.Name -contains 'oauth_email') { $acct.oauth_email = $null }
        Save-AccountsConfig -Config $cfg | Out-Null
    }
    Write-OAuthLog "Invoke-OAuthLogoutSlot: slot=$Name was_active=$wasActive" 'INFO'
    return $true
}

function Invoke-OAuthWhoAmI {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Name)
    _Import-AccountsLib
    $slotCreds = _Slot-CredentialsPath -Name $Name
    if (-not (Test-Path $slotCreds)) {
        Write-Host "[oauth-whoami] FAIL no creds file for slot '$Name' at $slotCreds." -ForegroundColor Red
        return $null
    }
    $email = _Try-DecodeOAuthEmail -Path $slotCreds
    if ($email) {
        Write-Host "[oauth-whoami] slot='$Name' -> email='$email'" -ForegroundColor Green
        # Cache in config.
        $cfg = Get-AccountsConfig
        $acct = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
        if ($acct) {
            if ($acct.PSObject.Properties.Name -contains 'oauth_email') { $acct.oauth_email = $email }
            else { $acct | Add-Member -MemberType NoteProperty -Name 'oauth_email' -Value $email -Force }
            Save-AccountsConfig -Config $cfg | Out-Null
        }
        return $email
    }
    Write-Host "[oauth-whoami] slot='$Name' -> email UNKNOWN (probe failed; token may be expired)." -ForegroundColor Yellow
    return $null
}

function Invoke-OAuthRotateToNext {
    # Pick the next enabled non-rate-limited OAuth slot, call Use on it, return its name.
    # Round-robin uses claude-accounts.json `last_rotation_index`.
    [CmdletBinding()]
    param()
    _Import-AccountsLib
    $cfg = Get-AccountsConfig
    $oauths = @($cfg.accounts | Where-Object {
        $_.PSObject.Properties.Name -contains 'auth_mode' -and $_.auth_mode -eq 'oauth' -and
        $_.enabled -ne $false -and
        $_.credentials_file -and (Test-Path $_.credentials_file)
    })
    if ($oauths.Count -eq 0) {
        Write-Host '[oauth-rotate] no OAuth slots available (have you run Login on at least one?).' -ForegroundColor Yellow
        return $null
    }
    $now = (Get-Date).ToUniversalTime()
    $eligible = @($oauths | Where-Object {
        $rl = $_.rate_limited_until_utc
        $wk = $_.weekly_reset_at_utc
        $ok = $true
        if ($rl) {
            try { if (([datetime]::Parse($rl)).ToUniversalTime() -gt $now) { $ok = $false } } catch {}
        }
        if ($wk) {
            try { if (([datetime]::Parse($wk)).ToUniversalTime() -gt $now) { $ok = $false } } catch {}
        }
        $ok
    })
    if ($eligible.Count -eq 0) {
        Write-Host '[oauth-rotate] all OAuth slots are rate-limited.' -ForegroundColor Yellow
        return $null
    }
    $startIdx = if ($cfg.PSObject.Properties.Name -contains 'last_rotation_index') { [int]$cfg.last_rotation_index } else { 0 }
    $pick = $eligible[$startIdx % $eligible.Count]
    $cfg.last_rotation_index = ($startIdx + 1) % [Math]::Max($eligible.Count, 1)
    Save-AccountsConfig -Config $cfg | Out-Null
    if (Invoke-OAuthUse -Name $pick.name) {
        Write-Host "[oauth-rotate] activated slot='$($pick.name)' (round-robin idx $startIdx of $($eligible.Count))." -ForegroundColor Green
        return $pick.name
    }
    return $null
}

# ---------------------------------------------------------------------------
# PickBest -- automatic best-slot picker. RKOJ-ELENO :: 2026-05-24
# Operator hard-canonical 2026-05-24 ~23:10Z:
#   "you need to detect the accounts that should be used and what is out of
#    credits etc. this entire round robin needs to be auto."
#
# Reads _shared-memory/oauth-slot-health.json (written by the sibling
# oauth-health-poller agent) for per-slot scores in [0..100]. Higher is
# fresher / lower 429 risk / more remaining quota. If the health file is
# missing or has no scoreable rows, falls back to "first eligible slot in
# round-robin order" using existing Get-AccountsConfig + eligibility rules.
#
# Output: PRINTS the chosen slot name on ONE LINE to stdout (so callers can
# capture it via subprocess stdout). Diagnostic info goes to stderr.
# Exit 0 = picked something; exit 1 = no eligible slot.
# ---------------------------------------------------------------------------

function Invoke-OAuthPickBest {
    [CmdletBinding()]
    param([switch]$Quiet)
    _Import-AccountsLib
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) {
        if (-not $Quiet) { [Console]::Error.WriteLine('[pick-best] no accounts in claude-accounts.json') }
        return $null
    }
    $now = (Get-Date).ToUniversalTime()

    # Eligibility: enabled, has credentials file (OAuth shape preferred), not currently rate-limited.
    $eligible = @($cfg.accounts | Where-Object {
        if ($_.enabled -eq $false) { return $false }
        if (-not ($_.PSObject.Properties.Name -contains 'credentials_file') -or -not $_.credentials_file) { return $false }
        if (-not (Test-Path $_.credentials_file)) { return $false }
        $rl = $_.rate_limited_until_utc
        $wk = $_.weekly_reset_at_utc
        if ($rl) {
            try { if (([datetime]::Parse($rl)).ToUniversalTime() -gt $now) { return $false } } catch {}
        }
        if ($wk) {
            try { if (([datetime]::Parse($wk)).ToUniversalTime() -gt $now) { return $false } } catch {}
        }
        return $true
    })

    if ($eligible.Count -eq 0) {
        if (-not $Quiet) { [Console]::Error.WriteLine('[pick-best] no eligible OAuth/api_key slots (all enabled slots are rate-limited or missing creds)') }
        return $null
    }

    # Load sibling poller's score file (best-effort).
    $healthFile = Join-Path $script:SanctumRoot '_shared-memory\oauth-slot-health.json'
    $scores = @{}
    if (Test-Path $healthFile) {
        try {
            $h = Get-Content -LiteralPath $healthFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
            if ($h.slots) {
                foreach ($s in $h.slots) {
                    if ($s.name -and ($s.PSObject.Properties.Name -contains 'score')) {
                        $scores[[string]$s.name] = [double]$s.score
                    }
                }
            }
        } catch {
            if (-not $Quiet) { [Console]::Error.WriteLine("[pick-best] warn: could not parse $healthFile ($($_.Exception.Message)); falling back to round-robin")}
        }
    }

    $pick = $null
    if ($scores.Count -gt 0) {
        # Highest-score eligible slot wins. Tiebreak: lower current_sessions, then OAuth before api_key.
        $ranked = $eligible | Sort-Object @{
            Expression = { if ($scores.ContainsKey($_.name)) { -[double]$scores[$_.name] } else { 0 } }
        }, @{
            Expression = { if ($_.PSObject.Properties.Name -contains 'current_sessions') { [int]$_.current_sessions } else { 0 } }
        }, @{
            Expression = { if ($_.auth_mode -eq 'oauth') { 0 } else { 1 } }
        }
        $pick = $ranked | Select-Object -First 1
    } else {
        # No score file -- fall back to round-robin via last_rotation_index.
        $startIdx = if ($cfg.PSObject.Properties.Name -contains 'last_rotation_index') { [int]$cfg.last_rotation_index } else { 0 }
        $pick = $eligible[$startIdx % $eligible.Count]
    }

    if (-not $pick) {
        if (-not $Quiet) { [Console]::Error.WriteLine('[pick-best] ranker returned nothing (defensive)') }
        return $null
    }

    # SINGLE-LINE stdout = slot name (caller captures via subprocess stdout).
    [Console]::Out.WriteLine($pick.name)
    if (-not $Quiet) {
        $sc = if ($scores.ContainsKey($pick.name)) { $scores[$pick.name] } else { 'n/a' }
        [Console]::Error.WriteLine("[pick-best] picked '$($pick.name)' (auth_mode=$($pick.auth_mode) score=$sc eligible_count=$($eligible.Count))")
    }
    return $pick.name
}

function Invoke-OAuthAutoMark429 {
    # RKOJ-ELENO :: 2026-05-24 :: idempotent mark used by claude-wrapper.ps1 when
    # a 429 is detected in claude's output. Sets rate_limited_until_utc (always)
    # and weekly_reset_at_utc (when -Weekly). If $RetryAfter is empty/blank,
    # default to now + 5h (or +168h when -Weekly).
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [string]$RetryAfter = '',
        [switch]$Weekly
    )
    _Import-AccountsLib
    $now = (Get-Date).ToUniversalTime()
    $until = $null
    if ($RetryAfter) {
        try { $until = ([datetime]::Parse($RetryAfter)).ToUniversalTime() } catch { $until = $null }
    }
    if (-not $until) {
        $hrs = if ($Weekly) { 168 } else { 5 }
        $until = $now.AddHours($hrs)
    }
    $iso = $until.ToString('yyyy-MM-ddTHH:mm:ssZ')
    $cfg = Get-AccountsConfig
    $acct = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if (-not $acct) {
        Write-Host "[oauth-automark429] FAIL no slot named '$Name'." -ForegroundColor Red
        Write-OAuthLog "Invoke-OAuthAutoMark429: slot '$Name' not found" 'ERROR'
        return $false
    }
    # Idempotent widen-only: only push the rate-limit further out, never shrink.
    $prevUntil = $null
    if ($acct.PSObject.Properties.Name -contains 'rate_limited_until_utc' -and $acct.rate_limited_until_utc) {
        try { $prevUntil = ([datetime]::Parse($acct.rate_limited_until_utc)).ToUniversalTime() } catch {}
    }
    if (-not $prevUntil -or $until -gt $prevUntil) {
        if ($acct.PSObject.Properties.Name -contains 'rate_limited_until_utc') { $acct.rate_limited_until_utc = $iso }
        else { $acct | Add-Member -MemberType NoteProperty -Name 'rate_limited_until_utc' -Value $iso -Force }
    }
    $nowIso = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')
    if ($acct.PSObject.Properties.Name -contains 'last_429_at_utc') { $acct.last_429_at_utc = $nowIso }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'last_429_at_utc' -Value $nowIso -Force }
    if ($Weekly) {
        $prevW = $null
        if ($acct.PSObject.Properties.Name -contains 'weekly_reset_at_utc' -and $acct.weekly_reset_at_utc) {
            try { $prevW = ([datetime]::Parse($acct.weekly_reset_at_utc)).ToUniversalTime() } catch {}
        }
        if (-not $prevW -or $until -gt $prevW) {
            if ($acct.PSObject.Properties.Name -contains 'weekly_reset_at_utc') { $acct.weekly_reset_at_utc = $iso }
            else { $acct | Add-Member -MemberType NoteProperty -Name 'weekly_reset_at_utc' -Value $iso -Force }
        }
    }
    Save-AccountsConfig -Config $cfg | Out-Null
    Write-OAuthLog "Invoke-OAuthAutoMark429: slot=$Name until=$iso weekly=$Weekly" 'INFO'
    Write-Host "[oauth-automark429] slot='$Name' rate_limited_until_utc=$iso weekly=$Weekly" -ForegroundColor Yellow
    return $true
}

function Invoke-OAuthMarkLimited {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$Until,
        [switch]$Weekly
    )
    _Import-AccountsLib
    try { $u = ([datetime]::Parse($Until)).ToUniversalTime() } catch {
        Write-Host "[oauth-marklimited] FAIL could not parse -Until '$Until' (use ISO-8601 like '2026-05-30T00:00:00Z')." -ForegroundColor Red
        return $false
    }
    $cfg = Get-AccountsConfig
    $acct = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if (-not $acct) {
        Write-Host "[oauth-marklimited] FAIL no slot named '$Name'." -ForegroundColor Red
        return $false
    }
    $iso = $u.ToString('yyyy-MM-ddTHH:mm:ssZ')
    if ($Weekly) {
        if ($acct.PSObject.Properties.Name -contains 'weekly_reset_at_utc') { $acct.weekly_reset_at_utc = $iso }
        else { $acct | Add-Member -MemberType NoteProperty -Name 'weekly_reset_at_utc' -Value $iso -Force }
        Write-Host "[oauth-marklimited] '$Name' weekly_reset_at_utc=$iso (Max plan weekly cap)" -ForegroundColor Yellow
    } else {
        if ($acct.PSObject.Properties.Name -contains 'rate_limited_until_utc') { $acct.rate_limited_until_utc = $iso }
        else { $acct | Add-Member -MemberType NoteProperty -Name 'rate_limited_until_utc' -Value $iso -Force }
        if ($acct.PSObject.Properties.Name -contains 'quota_resets_at_utc') { $acct.quota_resets_at_utc = $iso }
        else { $acct | Add-Member -MemberType NoteProperty -Name 'quota_resets_at_utc' -Value $iso -Force }
        Write-Host "[oauth-marklimited] '$Name' rate_limited_until_utc=$iso" -ForegroundColor Yellow
    }
    Save-AccountsConfig -Config $cfg | Out-Null
    Write-OAuthLog "Invoke-OAuthMarkLimited: slot=$Name weekly=$Weekly until=$iso" 'INFO'
    return $true
}

# ---------------------------------------------------------------------------
# CLI shim.
# Usage examples:
#   powershell -File claude-oauth-accounts.ps1 -Action Migrate
#   powershell -File claude-oauth-accounts.ps1 -Action Login -Name sinister-gmail
#   powershell -File claude-oauth-accounts.ps1 -Action Use -Name sinister-gmail
#   powershell -File claude-oauth-accounts.ps1 -Action Active
#   powershell -File claude-oauth-accounts.ps1 -Action List
#   powershell -File claude-oauth-accounts.ps1 -Action LogoutSlot -Name sinister-gmail
#   powershell -File claude-oauth-accounts.ps1 -Action WhoAmI -Name sinister-gmail
#   powershell -File claude-oauth-accounts.ps1 -Action RotateToNext
#   powershell -File claude-oauth-accounts.ps1 -Action MarkLimited -Name sinister-gmail -Until 2026-05-30T00:00:00Z [-Weekly]
# ---------------------------------------------------------------------------

if ($MyInvocation.InvocationName -ne '.' -and $args.Count -gt 0) {
    $Action = $null; $Name = $null; $Until = $null; $DisplayName = ''; $Weekly = $false; $RetryAfter = ''
    for ($i = 0; $i -lt $args.Count; $i++) {
        switch ($args[$i]) {
            '-Action'      { $Action = $args[++$i] }
            '-Name'        { $Name   = $args[++$i] }
            '-Until'       { $Until  = $args[++$i] }
            '-RetryAfter'  { $RetryAfter = $args[++$i] }
            '-DisplayName' { $DisplayName = $args[++$i] }
            '-Weekly'      { $Weekly = $true }
        }
    }
    switch ($Action) {
        'Migrate'      { Invoke-OAuthMigrate | Out-Null }
        'Login'        { Invoke-OAuthLoginScaffold -Name $Name -DisplayName $DisplayName | Out-Null }
        'Use'          { Invoke-OAuthUse -Name $Name | Out-Null }
        'Active'       { Invoke-OAuthActive | Out-Null }
        'List'         { Invoke-OAuthList | Out-Null }
        'LogoutSlot'   { Invoke-OAuthLogoutSlot -Name $Name | Out-Null }
        'WhoAmI'       { Invoke-OAuthWhoAmI -Name $Name | Out-Null }
        'RotateToNext' { Invoke-OAuthRotateToNext | Out-Null }
        'PickBest'     {
            # RKOJ-ELENO :: 2026-05-24 :: stdout = single slot name; exit 1 on no eligible.
            $picked = Invoke-OAuthPickBest
            if (-not $picked) { exit 1 } else { exit 0 }
        }
        'MarkLimited'  { Invoke-OAuthMarkLimited -Name $Name -Until $Until -Weekly:$Weekly | Out-Null }
        'AutoMark429'  { Invoke-OAuthAutoMark429 -Name $Name -RetryAfter $RetryAfter -Weekly:$Weekly | Out-Null }
        default        { Write-Host "[claude-oauth-accounts] unknown -Action '$Action' (expected Migrate|Login|Use|Active|List|LogoutSlot|WhoAmI|RotateToNext|PickBest|MarkLimited|AutoMark429)" -ForegroundColor Red }
    }
}
