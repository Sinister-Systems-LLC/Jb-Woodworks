# RKOJ-ELENO :: 2026-05-23
# test-claude-accounts.ps1 - Phase 1 smoke test for the rotation library.
#
# Runs the full lease/rate-limit/wait cycle against the on-disk JSON and prints
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
Write-Host '=== claude-accounts Phase 1 smoke test ==='
Write-Host ''

# Snapshot original state for restore
$orig = Get-AccountsConfig
$origJson = $orig | ConvertTo-Json -Depth 12

# --- Check 1: Get-AccountsConfig returns object with accounts array ---
$cfg = Get-AccountsConfig
_Check 'Get-AccountsConfig returns config' ($null -ne $cfg) "version=$($cfg.version) accounts=$($cfg.accounts.Count)"

# --- Check 2: Get-NextAvailableAccount returns operator ---
$next = Get-NextAvailableAccount
_Check 'Get-NextAvailableAccount returns operator' ($null -ne $next -and $next.name -eq 'operator') "got: $(if ($next) { $next.name } else { '<null>' })"

# --- Check 3: Mark-AccountSpawned increments current_sessions ---
$null = Mark-AccountSpawned -Name 'operator'
$cfg2 = Get-AccountsConfig
$op2 = $cfg2.accounts | Where-Object { $_.name -eq 'operator' }
_Check 'Mark-AccountSpawned: current_sessions=1' ($op2.current_sessions -eq 1) "current_sessions=$($op2.current_sessions) spawns_today=$($op2.successful_spawns_today)"

# --- Check 4: Mark-AccountRateLimited sets rate_limited_until_utc ---
$null = Mark-AccountRateLimited -Name 'operator' -RetryAfterSeconds 30
$cfg3 = Get-AccountsConfig
$op3 = $cfg3.accounts | Where-Object { $_.name -eq 'operator' }
_Check 'Mark-AccountRateLimited: rate_limited_until_utc set' ($null -ne $op3.rate_limited_until_utc) "rate_limited_until_utc=$($op3.rate_limited_until_utc)"

# --- Check 5: Get-NextAvailableAccount returns $null when only account is limited ---
$next2 = Get-NextAvailableAccount
_Check 'Get-NextAvailableAccount returns null when all limited' ($null -eq $next2) "got: $(if ($next2) { $next2.name } else { '<null>' })"

# --- Check 6: Get-WaitUntilAnyAvailable returns the timestamp ---
$wait = Get-WaitUntilAnyAvailable
_Check 'Get-WaitUntilAnyAvailable returns timestamp' ($null -ne $wait -and $wait -match '^\d{4}-\d{2}-\d{2}T') "wait_until=$wait"

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
