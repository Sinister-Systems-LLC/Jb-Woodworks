# RKOJ-ELENO :: 2026-05-23 (v1) :: 2026-05-24 (v2 - 4-slot + mgmt CLI coverage)
# test-claude-accounts.ps1 - Phase 1+2 smoke test for the rotation library.
#
# Runs the full lease/rate-limit/wait cycle PLUS v2 management CLI actions
# (List/Add/Enable/Disable/Remove/Test) against the on-disk JSON and prints
# [PASS] / [FAIL] per check. Restores state at end.

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here 'claude-accounts.ps1')

$script:Total = 0
$script:Passed = 0

function _Check {
    param([string]$Name, [bool]$Condition, [string]$Detail = '')
    $script:Total++
    if ($Condition) {
        $script:Passed++
        Write-Host "[PASS] $Name"
        if ($Detail) { Write-Host "       $Detail" -ForegroundColor DarkGray }
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        if ($Detail) { Write-Host "       $Detail" -ForegroundColor Red }
    }
}

Write-Host ''
Write-Host '=== claude-accounts Phase 1+2 smoke test (v2 schema + mgmt CLI) ==='
Write-Host ''

# Snapshot original state for restore
$orig = Get-AccountsConfig
$origJson = $orig | ConvertTo-Json -Depth 12

# --- Check 1: Get-AccountsConfig returns object with accounts array ---
$cfg = Get-AccountsConfig
_Check 'Get-AccountsConfig returns config' ($null -ne $cfg) "version=$($cfg.version) accounts=$($cfg.accounts.Count)"

# --- Check 2: v2 schema - version is 2 ---
_Check 'v2 schema: version=2' ($cfg.version -eq 2) "version=$($cfg.version)"

# --- Check 3: v2 schema - 4 slots seeded ---
_Check 'v2 schema: 4 slots seeded' ($cfg.accounts.Count -eq 4) "accounts.Count=$($cfg.accounts.Count)"

# --- Check 4: v2 schema - every account has enabled field ---
$missingEnabled = @($cfg.accounts | Where-Object { $_.PSObject.Properties.Name -notcontains 'enabled' })
_Check 'v2 schema: every account has enabled field' ($missingEnabled.Count -eq 0) "missing=$($missingEnabled.Count)"

# --- Check 5: v2 schema - max_concurrent_global set ---
_Check 'v2 schema: max_concurrent_global set' ($null -ne $cfg.max_concurrent_global) "max_concurrent_global=$($cfg.max_concurrent_global)"

# --- Check 6: Get-NextAvailableAccount returns operator (only enabled account by default) ---
$next = Get-NextAvailableAccount
_Check 'Get-NextAvailableAccount returns operator' ($null -ne $next -and $next.name -eq 'operator') "got: $(if ($next) { $next.name } else { '<null>' })"

# --- Check 7: enabled gate - disabled slots are skipped ---
# All non-operator slots start as enabled:false, so they should never be returned.
$disabled = @($cfg.accounts | Where-Object { $_.enabled -eq $false })
$disabledNames = ($disabled | ForEach-Object { $_.name }) -join ','
$nextSkipsDisabled = $true
foreach ($d in $disabled) {
    if ($next.name -eq $d.name) { $nextSkipsDisabled = $false; break }
}
_Check 'Get-NextAvailableAccount skips enabled=false slots' $nextSkipsDisabled "disabled slots=$disabledNames; picked=$($next.name)"

# --- Check 8: Mark-AccountSpawned increments current_sessions ---
$null = Mark-AccountSpawned -Name 'operator'
$cfg2 = Get-AccountsConfig
$op2 = $cfg2.accounts | Where-Object { $_.name -eq 'operator' }
_Check 'Mark-AccountSpawned: current_sessions incremented' ($op2.current_sessions -ge 1) "current_sessions=$($op2.current_sessions) spawns_today=$($op2.successful_spawns_today)"

# --- Check 9: Mark-AccountRateLimited sets rate_limited_until_utc ---
$null = Mark-AccountRateLimited -Name 'operator' -RetryAfterSeconds 30
$cfg3 = Get-AccountsConfig
$op3 = $cfg3.accounts | Where-Object { $_.name -eq 'operator' }
_Check 'Mark-AccountRateLimited: rate_limited_until_utc set' ($null -ne $op3.rate_limited_until_utc) "rate_limited_until_utc=$($op3.rate_limited_until_utc)"

# --- Check 10: Get-NextAvailableAccount returns $null when only enabled account is limited ---
$next2 = Get-NextAvailableAccount
_Check 'Get-NextAvailableAccount returns null when all enabled limited' ($null -eq $next2) "got: $(if ($next2) { $next2.name } else { '<null>' })"

# --- Check 11: Get-WaitUntilAnyAvailable returns the timestamp ---
$wait = Get-WaitUntilAnyAvailable
_Check 'Get-WaitUntilAnyAvailable returns timestamp' ($null -ne $wait -and $wait -match '^\d{4}-\d{2}-\d{2}T') "wait_until=$wait"

# --- CLI MGMT CHECKS (v2) ---------------------------------------------------

# --- Check 12: Invoke-AccountList runs without throwing ---
$listOk = $true
try { Invoke-AccountList | Out-Null } catch { $listOk = $false }
_Check 'CLI List: runs without throwing' $listOk ''

# --- Check 13: Invoke-AccountAdd configures slot3 ---
$fakeCreds = Join-Path $env:TEMP 'creds.test-slot3.json'
'{ "api_key": "sk-ant-api03-TEST-DUMMY-KEY-NEVER-USE" }' | Out-File -FilePath $fakeCreds -Encoding utf8 -Force
$null = Invoke-AccountAdd -Name 'slot3' -Label 'Test slot3' -CredentialsFile $fakeCreds
$cfg4 = Get-AccountsConfig
$s3 = $cfg4.accounts | Where-Object { $_.name -eq 'slot3' }
_Check 'CLI Add: slot3 label updated' ($s3.label -eq 'Test slot3') "label=$($s3.label)"
_Check 'CLI Add: slot3 credentials_file updated' ($s3.credentials_file -eq $fakeCreds) "creds=$($s3.credentials_file)"
_Check 'CLI Add: slot3 auto-enabled' ($s3.enabled -eq $true) "enabled=$($s3.enabled)"

# --- Check 16: Invoke-AccountSetEnabled - Disable ---
$null = Invoke-AccountSetEnabled -Name 'slot3' -Enabled $false
$cfg5 = Get-AccountsConfig
$s3d = $cfg5.accounts | Where-Object { $_.name -eq 'slot3' }
_Check 'CLI Disable: slot3 disabled' ($s3d.enabled -eq $false) "enabled=$($s3d.enabled)"

# --- Check 17: Invoke-AccountSetEnabled - Enable ---
$null = Invoke-AccountSetEnabled -Name 'slot3' -Enabled $true
$cfg6 = Get-AccountsConfig
$s3e = $cfg6.accounts | Where-Object { $_.name -eq 'slot3' }
_Check 'CLI Enable: slot3 enabled' ($s3e.enabled -eq $true) "enabled=$($s3e.enabled)"

# --- Check 18: Invoke-AccountTest passes for valid creds file ---
$testResult = Invoke-AccountTest -Name 'slot3'
_Check 'CLI Test: slot3 with valid creds returns true' ($testResult -eq $true) "result=$testResult"

# --- Check 19: Invoke-AccountTest fails for missing file ---
Remove-Item -Path $fakeCreds -Force -ErrorAction SilentlyContinue
$testFail = Invoke-AccountTest -Name 'slot3'
_Check 'CLI Test: missing file returns false' ($testFail -eq $false) "result=$testFail"

# --- Check 20: Invoke-AccountRemove resets slot3 ---
$null = Invoke-AccountRemove -Name 'slot3'
$cfg7 = Get-AccountsConfig
$s3r = $cfg7.accounts | Where-Object { $_.name -eq 'slot3' }
_Check 'CLI Remove: slot3 label reset' ($s3r.label -eq '(unconfigured)') "label=$($s3r.label)"
_Check 'CLI Remove: slot3 disabled' ($s3r.enabled -eq $false) "enabled=$($s3r.enabled)"

# --- Restore state ---
Write-Host ''
Write-Host '--- restoring original state ---'
$cfgR = Get-AccountsConfig
foreach ($a in $cfgR.accounts) {
    if ($a.name -eq 'operator') {
        $a.rate_limited_until_utc = $null
        $a.last_429_at_utc = $null
        $a.current_sessions = 0
        # also reset spawns_today bump so the test is idempotent
        $a.successful_spawns_today = 0
        if ($a.PSObject.Properties.Name -contains 'last_spawn_at_utc') { $a.last_spawn_at_utc = $null }
    }
}
$null = Save-AccountsConfig -Config $cfgR
$cfgFinal = Get-AccountsConfig
$opFinal = $cfgFinal.accounts | Where-Object { $_.name -eq 'operator' }
_Check 'Restore: rate_limited_until_utc cleared' ($null -eq $opFinal.rate_limited_until_utc) "rate_limited_until_utc=$($opFinal.rate_limited_until_utc)"
_Check 'Restore: current_sessions=0' ($opFinal.current_sessions -eq 0) "current_sessions=$($opFinal.current_sessions)"

Write-Host ''
Write-Host "=== RESULT: $script:Passed / $script:Total PASS ==="
if ($script:Passed -eq $script:Total) {
    Write-Host '[ALL GREEN]' -ForegroundColor Green
    exit 0
} else {
    Write-Host '[FAILURES PRESENT]' -ForegroundColor Red
    exit 1
}
