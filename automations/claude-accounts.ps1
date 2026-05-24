# RKOJ-ELENO :: 2026-05-23 (v1) :: 2026-05-24 (v2 - 4-slot expansion + mgmt CLI)
# claude-accounts.ps1 - Multi-Claude account rotation manager library.
#
# v2 (2026-05-24): 4-slot operator-curated allowlist + enabled flag + CLI actions
# (List/Add/Enable/Disable/Remove/Test). Backward compatible with v1.
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

function _Is-AccountAvailable {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Account)
    $now = (Get-Date).ToUniversalTime()
    # v2: enabled gate. Missing field treated as enabled=$true (v1 compat).
    if ($Account.PSObject.Properties.Name -contains 'enabled' -and $Account.enabled -eq $false) { return $false }
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
    param()
    $cfg = Get-AccountsConfig
    if (-not $cfg.accounts -or $cfg.accounts.Count -eq 0) {
        Write-AccountsLog 'Get-NextAvailableAccount: no accounts configured' 'WARN'
        return $null
    }
    # round-robin: pick the account with the lowest current_sessions among available
    $available = @($cfg.accounts | Where-Object { _Is-AccountAvailable -Account $_ })
    if ($available.Count -eq 0) { return $null }
    $best = $available | Sort-Object current_sessions, successful_spawns_today | Select-Object -First 1
    return @{ name = $best.name; account = $best }
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
    Write-AccountsLog "Mark-AccountRateLimited: '$Name' limited until $until ($RetryAfterSeconds s)" 'INFO'
    return (Save-AccountsConfig -Config $cfg)
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
# v2 Management functions (List/Add/Enable/Disable/Remove/Test).
# Each operation flows through Get-AccountsConfig + Save-AccountsConfig which
# uses the existing lock-file pattern.
# ---------------------------------------------------------------------------

function Invoke-AccountList {
    [CmdletBinding()]
    param()
    $cfg = Get-AccountsConfig
    Write-Host ''
    Write-Host ("{0,-10} {1,-8} {2,-6} {3,-10} {4,-22} {5}" -f 'NAME','ENABLED','TIER','SESSIONS','RATE_LIMITED_UNTIL','LABEL')
    Write-Host ("{0,-10} {1,-8} {2,-6} {3,-10} {4,-22} {5}" -f '----','-------','----','--------','------------------','-----')
    foreach ($a in $cfg.accounts) {
        $en = if ($a.PSObject.Properties.Name -contains 'enabled') { $a.enabled } else { $true }
        $sess = "$($a.current_sessions)/$($a.max_sessions_concurrent)"
        $rl = if ($a.rate_limited_until_utc) { $a.rate_limited_until_utc } else { '-' }
        Write-Host ("{0,-10} {1,-8} {2,-6} {3,-10} {4,-22} {5}" -f $a.name, $en, $a.plan_tier, $sess, $rl, $a.label)
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
    if (-not $acct) { Write-Host "[ERROR] slot '$Name' not found. Use -Action List." -ForegroundColor Red; return $false }
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
    if ($Label) { $acct.label = $Label }
    if ($acct.PSObject.Properties.Name -contains 'enabled') { $acct.enabled = $true }
    else { $acct | Add-Member -MemberType NoteProperty -Name 'enabled' -Value $true -Force }
    Write-AccountsLog "Invoke-AccountSetKey: '$Name' creds written to $credsPath + enabled" 'INFO'
    $masked = $ApiKey.Substring(0, [Math]::Min(12, $ApiKey.Length)) + '...'
    Write-Host "[OK] Slot '$Name' configured + enabled. Creds: $credsPath (api_key=$masked)." -ForegroundColor Green
    return (Save-AccountsConfig -Config $cfg)
}

function Invoke-AccountStatus {
    # Compact rotation summary: enabled count / total + per-slot one-liner + how to add more.
    [CmdletBinding()]
    param()
    $cfg = Get-AccountsConfig
    $accts = @($cfg.accounts)
    $enabled = @($accts | Where-Object { $_.enabled -ne $false })
    $disabled = @($accts | Where-Object { $_.enabled -eq $false })
    $rl = @($accts | Where-Object { $_.rate_limited_until_utc })
    Write-Host ''
    Write-Host "  Multi-account rotation status:" -ForegroundColor Cyan
    Write-Host "    strategy:    $($cfg.rotation_strategy)" -ForegroundColor Gray
    Write-Host "    enabled:     $($enabled.Count) / $($accts.Count)" -ForegroundColor Gray
    Write-Host "    rate-limited:$($rl.Count)" -ForegroundColor Gray
    Write-Host ''
    foreach ($a in $accts) {
        $en = if ($a.enabled -eq $false) { 'OFF ' } else { 'ON  ' }
        $sess = "{0}/{1}" -f $a.current_sessions, $a.max_sessions_concurrent
        $color = if ($a.enabled -eq $false) { 'DarkGray' } elseif ($a.rate_limited_until_utc) { 'Yellow' } else { 'Green' }
        Write-Host ("    [{0}] {1,-10} sess={2,-7} spawns_today={3,-3} label={4}" -f $en, $a.name, $sess, $a.successful_spawns_today, $a.label) -ForegroundColor $color
    }
    Write-Host ''
    if ($disabled.Count -gt 0) {
        $first = $disabled[0].name
        Write-Host "  To enable a slot in one command:" -ForegroundColor Cyan
        Write-Host "    powershell -File automations\claude-accounts.ps1 -Action SetKey -Name $first -ApiKey sk-ant-... -Label 'Your label'" -ForegroundColor Gray
        Write-Host ''
    }
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

# CLI shim for spawn .sh trailer + management actions:
#   powershell -File claude-accounts.ps1 -Action Release -Name operator
#   powershell -File claude-accounts.ps1 -Action List
#   powershell -File claude-accounts.ps1 -Action Add -Name slot3 -Label "Alice" -CredentialsFile C:\path\creds.json
#   powershell -File claude-accounts.ps1 -Action Enable -Name slot3
#   powershell -File claude-accounts.ps1 -Action Disable -Name slot3
#   powershell -File claude-accounts.ps1 -Action Remove -Name slot3
#   powershell -File claude-accounts.ps1 -Action Test -Name operator
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
        'Release'     { Mark-AccountReleased     -Name $Name | Out-Null }
        'Spawned'     { Mark-AccountSpawned      -Name $Name | Out-Null }
        'RateLimited' { Mark-AccountRateLimited  -Name $Name -RetryAfterSeconds $RetryAfterSeconds | Out-Null }
        'List'        { Invoke-AccountList }
        'Status'      { Invoke-AccountStatus | Out-Null }
        'Add'         { Invoke-AccountAdd        -Name $Name -Label $Label -CredentialsFile $CredentialsFile | Out-Null }
        'SetKey'      { Invoke-AccountSetKey     -Name $Name -ApiKey $ApiKey -Label $Label | Out-Null }
        'Enable'      { Invoke-AccountSetEnabled -Name $Name -Enabled $true  | Out-Null }
        'Disable'     { Invoke-AccountSetEnabled -Name $Name -Enabled $false | Out-Null }
        'Remove'      { Invoke-AccountRemove     -Name $Name | Out-Null }
        'Test'        { Invoke-AccountTest       -Name $Name | Out-Null }
        default       { Write-Host "[claude-accounts] unknown -Action '$Action' (expected Release|Spawned|RateLimited|List|Status|Add|SetKey|Enable|Disable|Remove|Test)" }
    }
}
