# Author: RKOJ-ELENO :: 2026-05-24
# test-claude-oauth-accounts.ps1 -- smoke tests for the OAuth pivot.
#
# CRITICAL: never touches the operator's real ~/.claude/.credentials.json.
# All test artifacts go under $env:TEMP\sinister-oauth-test\.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$module = Join-Path $root 'automations\claude-oauth-accounts.ps1'
if (-not (Test-Path $module)) { throw "module missing: $module" }

# Synthetic test fixtures.
$testDir = Join-Path $env:TEMP 'sinister-oauth-test'
if (Test-Path $testDir) { Remove-Item -Recurse -Force $testDir }
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
$fakeSlot1 = Join-Path $testDir 'credentials.fake1.json'
$fakeSlot2 = Join-Path $testDir 'credentials.fake2.json'
$fakeApiSlot = Join-Path $testDir 'credentials.fakeapi.json'

# Fake OAuth blobs (claudeAiOauth shape).
$oauth1 = @{ claudeAiOauth = @{ accessToken = 'sk-ant-oat01-test1-FAKE-AAAAAAAAAAAAAAAAAAAAAAAA'; refreshToken = 'sk-ant-ort01-test1-FAKE-AAAAAAAAAAAAAAAAAAAAAAAA'; expiresAt = 9999999999999; scopes = @('user:inference') } } | ConvertTo-Json -Depth 4 -Compress
$oauth2 = @{ claudeAiOauth = @{ accessToken = 'sk-ant-oat01-test2-FAKE-BBBBBBBBBBBBBBBBBBBBBBBB'; refreshToken = 'sk-ant-ort01-test2-FAKE-BBBBBBBBBBBBBBBBBBBBBBBB'; expiresAt = 9999999999999; scopes = @('user:inference') } } | ConvertTo-Json -Depth 4 -Compress
$apiblob = @{ api_key = 'sk-ant-api-test-FAKE-CCCCCCCCCCCCCCCCCCCCCCCC'; account_email = 'test@example.com' } | ConvertTo-Json -Depth 3 -Compress

Set-Content -Path $fakeSlot1   -Value $oauth1 -Encoding UTF8
Set-Content -Path $fakeSlot2   -Value $oauth2 -Encoding UTF8
Set-Content -Path $fakeApiSlot -Value $apiblob -Encoding UTF8

# Load the module via dot-source so we can call internal helpers directly.
$savedClaudeRoot = $env:USERPROFILE
. $module

$pass = 0
$fail = 0
function _assert($cond, $msg) {
    if ($cond) {
        Write-Host "  [PASS] $msg" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  [FAIL] $msg" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host ''
Write-Host '=== test 1: _Is-OAuthCredentialsFile shape detection ===' -ForegroundColor Cyan
_assert (_Is-OAuthCredentialsFile -Path $fakeSlot1)   "OAuth-shape file detected as OAuth"
_assert (-not (_Is-OAuthCredentialsFile -Path $fakeApiSlot)) "API-key-shape file NOT detected as OAuth"
_assert (-not (_Is-OAuthCredentialsFile -Path (Join-Path $testDir 'nope.json'))) "missing file returns false (no exception)"

Write-Host ''
Write-Host '=== test 2: _Hash-File determinism ===' -ForegroundColor Cyan
$h1a = _Hash-File -Path $fakeSlot1
$h1b = _Hash-File -Path $fakeSlot1
$h2  = _Hash-File -Path $fakeSlot2
_assert ($h1a -eq $h1b) "same file -> same hash"
_assert ($h1a -ne $h2)  "different files -> different hash"
_assert ($null -eq (_Hash-File -Path (Join-Path $testDir 'nope.json'))) "missing file -> null hash"

Write-Host ''
Write-Host '=== test 3: _Atomic-Copy semantics ===' -ForegroundColor Cyan
$dest = Join-Path $testDir 'copied.json'
_Atomic-Copy -Source $fakeSlot1 -Destination $dest
_assert (Test-Path $dest) "destination created"
_assert ((_Hash-File -Path $dest) -eq (_Hash-File -Path $fakeSlot1)) "destination matches source content"
# Overwrite existing target.
_Atomic-Copy -Source $fakeSlot2 -Destination $dest
_assert ((_Hash-File -Path $dest) -eq (_Hash-File -Path $fakeSlot2)) "atomic-copy overwrites existing target"

Write-Host ''
Write-Host '=== test 4: Migrate idempotency ===' -ForegroundColor Cyan
$migrateOut1 = & powershell -NoProfile -ExecutionPolicy Bypass -File $module -Action Migrate 2>&1 | Out-String
$migrateOut2 = & powershell -NoProfile -ExecutionPolicy Bypass -File $module -Action Migrate 2>&1 | Out-String
_assert ($migrateOut2 -match 'no-op|already have') "second Migrate call is a no-op"

Write-Host ''
Write-Host '=== test 5: List enumerates all accounts with mode column ===' -ForegroundColor Cyan
$listOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $module -Action List 2>&1 | Out-String
_assert ($listOut -match 'MODE') "List output contains MODE header"
_assert ($listOut -match 'SLOT') "List output contains SLOT header"
_assert ($listOut -match 'EMAIL') "List output contains EMAIL header"

Write-Host ''
Write-Host '=== test 6: MarkLimited writes ISO timestamp ===' -ForegroundColor Cyan
$markOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $module -Action MarkLimited -Name slot4 -Until '2026-06-01T00:00:00Z' 2>&1 | Out-String
_assert ($markOut -match 'rate_limited_until_utc=2026-06-01T00:00:00Z') "MarkLimited writes the timestamp"
$markOut2 = & powershell -NoProfile -ExecutionPolicy Bypass -File $module -Action MarkLimited -Name slot4 -Until '2026-06-01T00:00:00Z' -Weekly 2>&1 | Out-String
_assert ($markOut2 -match 'weekly_reset_at_utc=2026-06-01T00:00:00Z') "MarkLimited -Weekly writes weekly field"
# Reset slot4 to clean state for downstream tests.
$cfg = Get-AccountsConfig
$s4 = $cfg.accounts | Where-Object { $_.name -eq 'slot4' } | Select-Object -First 1
if ($s4) {
    $s4.rate_limited_until_utc = $null
    $s4.weekly_reset_at_utc = $null
    $s4.quota_resets_at_utc = $null
    Save-AccountsConfig -Config $cfg | Out-Null
}

Write-Host ''
Write-Host '=== test 7: bogus action prints help ===' -ForegroundColor Cyan
$badOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $module -Action NonExistent 2>&1 | Out-String
_assert ($badOut -match "unknown -Action 'NonExistent'") "bogus action surfaced"

Write-Host ''
Write-Host '=== summary ===' -ForegroundColor Cyan
Write-Host "  PASS: $pass" -ForegroundColor Green
Write-Host "  FAIL: $fail" -ForegroundColor $(if ($fail -gt 0) { 'Red' } else { 'DarkGray' })

# Cleanup.
Remove-Item -Recurse -Force $testDir -ErrorAction SilentlyContinue

if ($fail -gt 0) { exit 1 } else { exit 0 }
