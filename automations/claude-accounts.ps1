# RKOJ-ELENO :: 2026-05-23
# claude-accounts.ps1 - Multi-Claude account rotation manager library.
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
        _comment           = 'Auto-generated default (no claude-accounts.json on disk). RKOJ-ELENO :: 2026-05-23.'
        version            = 1
        default            = 'operator'
        rotation_strategy  = 'round-robin'
        accounts           = @()
    }
}

function _Acquire-AccountsLock {
    [CmdletBinding()]
    param([int]$MaxRetries = 10, [int]$SleepMs = 200)
    for ($i = 0; $i -lt $MaxRetries; $i++) {
        try {
            $fs = [System.IO.File]::Open($script:AccountsLockFile, 'CreateNew', 'Write', 'None')
            $fs.Close()
            return $true
        } catch {
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

# CLI shim for spawn .sh trailer:
#   powershell -File claude-accounts.ps1 -Action Release -Name operator
if ($MyInvocation.InvocationName -ne '.' -and $args.Count -gt 0) {
    # script-mode CLI parser (only fires when invoked, not dot-sourced)
    $Action = $null; $Name = $null; $RetryAfterSeconds = 0
    for ($i = 0; $i -lt $args.Count; $i++) {
        switch ($args[$i]) {
            '-Action'             { $Action = $args[++$i] }
            '-Name'               { $Name   = $args[++$i] }
            '-RetryAfterSeconds'  { $RetryAfterSeconds = [int]$args[++$i] }
        }
    }
    switch ($Action) {
        'Release'     { Mark-AccountReleased     -Name $Name | Out-Null }
        'Spawned'     { Mark-AccountSpawned      -Name $Name | Out-Null }
        'RateLimited' { Mark-AccountRateLimited  -Name $Name -RetryAfterSeconds $RetryAfterSeconds | Out-Null }
        default       { Write-Host "[claude-accounts] unknown -Action '$Action' (expected Release|Spawned|RateLimited)" }
    }
}
