# Author: Sinister Kernel APK (Claude agent, 2026-05-21)
# sinister-recovery-watchdog/watchdog.ps1
#
# One poll cycle: for each connected phone, tail boot_events.jsonl + error_log.jsonl,
# compare against state.json, emit [ALERT] JSON to inbox/kernel-apk/ on NEW events.
#
# Designed to be invoked every ~60s by a scheduled task. Each run is independent;
# state.json carries cross-run memory.

#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$ScriptRoot = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$ErrorRateThreshold = 5,
    [int]$ErrorWindowRows = 10
)

# Fix 2026-05-21T20:0xZ kernel-apk: $MyInvocation.MyCommand.Path is $null when
# the script is invoked via `powershell -File`. $PSScriptRoot is the reliable
# PS5.1+ built-in that resolves correctly under -File / dot-source / module
# load. Resolve here in the body (not in the param default) so the runtime
# always has access.
if (-not $ScriptRoot) {
    if ($PSScriptRoot) {
        $ScriptRoot = $PSScriptRoot
    } elseif ($MyInvocation.MyCommand.Path) {
        $ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    } else {
        $ScriptRoot = (Get-Location).Path
    }
}

$ErrorActionPreference = 'Stop'
$VerbosePreference = 'SilentlyContinue'

$StatePath = Join-Path $ScriptRoot 'state.json'
$LogPath = Join-Path $ScriptRoot 'watchdog.log'
$InboxDir = Join-Path $SanctumRoot '_shared-memory\inbox\kernel-apk'

function Write-WdLog {
    param([string]$Level, [string]$Msg)
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format 'o'), $Level, $Msg
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
}

function Rotate-LogIfNeeded {
    if ((Test-Path $LogPath) -and (Get-Item $LogPath).Length -gt 5MB) {
        Move-Item -Path $LogPath -Destination "$LogPath.1" -Force
    }
}

function Read-State {
    if (Test-Path $StatePath) {
        try { return Get-Content $StatePath -Raw | ConvertFrom-Json }
        catch { Write-WdLog WARN "state.json parse fail, starting fresh: $_" }
    }
    return [pscustomobject]@{
        version = '1.0'
        created_utc = (Get-Date -Format 'o')
        phones = [pscustomobject]@{}
    }
}

function Save-State {
    param($State)
    $State | ConvertTo-Json -Depth 8 | Set-Content -Path $StatePath -Encoding UTF8
}

function Get-AdbDevices {
    # Returns USB-attached Pixel 6a serials only.
    # The `-notmatch '^(127\.0\.0\.1|172\.|10\.)'` filter intentionally excludes:
    #   - 127.0.0.1:port - Cuttlefish virtual devices (cvd-1/2/3 not in scope)
    #   - 172.*  - Docker bridge addresses
    #   - 10.*   - operator's LAN range
    # The watchdog scope is the production Pixel 6a fleet (P1 2A061JEGR09301
    # + P2 26031JEGR17598). Cuttlefish-side health is operator-managed; not
    # in this watchdog's lane.
    try {
        $raw = & adb devices 2>&1
        if ($LASTEXITCODE -ne 0) { return @() }
        return $raw |
            Where-Object { $_ -match '^\S+\s+device$' -and $_ -notmatch '^List of' } |
            ForEach-Object { ($_ -split '\s+')[0] } |
            Where-Object { $_ -notmatch '^(127\.0\.0\.1|172\.|10\.)' }
    } catch {
        Write-WdLog ERROR "adb devices failed: $_"
        return @()
    }
}

function Tail-PhoneJsonl {
    param([string]$Serial, [string]$RemotePath, [int]$Lines = 5)
    try {
        $raw = & adb -s $Serial shell "su -c 'tail -$Lines $RemotePath 2>/dev/null'" 2>&1
        if ($LASTEXITCODE -ne 0) { return @() }
        return $raw |
            Where-Object { $_ -match '^\s*\{' } |
            ForEach-Object {
                try { $_ | ConvertFrom-Json } catch { $null }
            } |
            Where-Object { $_ -ne $null }
    } catch {
        Write-WdLog WARN "tail $RemotePath on $Serial failed: $_"
        return @()
    }
}

function Emit-Alert {
    param([string]$Serial, [string]$Tag, [string]$Subject, [hashtable]$Body)
    $ts = ([datetime]::UtcNow).ToString('yyyy-MM-ddTHHmmZ')
    $safeSerial = $Serial -replace '[^A-Za-z0-9]', '_'
    $fname = "${ts}-${Tag}-${safeSerial}.json"
    $path = Join-Path $InboxDir $fname
    $payload = @{
        _author = "sinister-recovery-watchdog :: $(Get-Date -Format 'yyyy-MM-dd')"
        tag = "[ALERT $Tag]"
        from = 'recovery-watchdog'
        to = 'kernel-apk'
        ts_utc = (Get-Date -Format 'o')
        phone_serial = $Serial
        subject = $Subject
    } + $Body
    if (-not (Test-Path $InboxDir)) { New-Item -ItemType Directory -Path $InboxDir -Force | Out-Null }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $path -Encoding UTF8
    Write-WdLog ALERT "emitted $fname"
}

# === Main poll cycle ===

Rotate-LogIfNeeded
Write-WdLog INFO "poll cycle start"

$state = Read-State
$devices = Get-AdbDevices

if ($devices.Count -eq 0) {
    Write-WdLog INFO "no devices attached"
    exit 1
}

foreach ($serial in $devices) {
    Write-WdLog INFO "checking $serial"

    # Initialize per-phone state on first sight.
    # Fix 2026-05-21T19:5xZ kernel-apk: parenthesize the `-not ... -contains` test.
    # PowerShell 5.1 operator precedence evaluates `-not` BEFORE `-contains`, so
    # the prior form `if (-not $state.phones.PSObject.Properties.Name -contains $serial)`
    # evaluated `(-not $array) -contains $serial` which is always $false because
    # `-not $array` is `$false` (a boolean, not a serial). With parens, the test
    # correctly evaluates `-not ($array -contains $serial)`, true on first sight.
    if (-not ($state.phones.PSObject.Properties.Name -contains $serial)) {
        $state.phones | Add-Member -NotePropertyName $serial -NotePropertyValue ([pscustomobject]@{
            last_seen_boot_event_ts_ms = 0
            last_check_utc = (Get-Date -Format 'o')
            consecutive_alerts = 0
        }) -Force
    }
    $phoneState = $state.phones.$serial

    # --- boot_events.jsonl scan ---
    $bootEvents = Tail-PhoneJsonl -Serial $serial -RemotePath '/data/adb/sinister/boot_events.jsonl' -Lines 5
    foreach ($evt in $bootEvents) {
        if (-not $evt.ts_ms) { continue }
        if ($evt.ts_ms -le $phoneState.last_seen_boot_event_ts_ms) { continue }
        # NEW event
        if ($evt.boot_mode -eq 'recovery' -or $evt.bootmode -eq 'recovery') {
            Emit-Alert -Serial $serial -Tag 'recovery-boot' -Subject "ALERT: recovery boot detected on $serial" -Body @{
                event = $evt
                action_recommended = 'Check phone health; if recovery mode persists, may indicate kernel issue or operator action in progress'
            }
        }
        $phoneState.last_seen_boot_event_ts_ms = $evt.ts_ms
    }

    # --- error_log.jsonl runaway-error scan ---
    $errorRows = Tail-PhoneJsonl -Serial $serial -RemotePath '/data/adb/sinister/error_log.jsonl' -Lines $ErrorWindowRows
    $failCount = ($errorRows | Where-Object { $_.status -like 'failed:*' }).Count
    if ($failCount -ge $ErrorRateThreshold) {
        Emit-Alert -Serial $serial -Tag 'runaway-error' -Subject "ALERT: error rate spike on $serial - $failCount failures in last $ErrorWindowRows iters" -Body @{
            failed_count_last_window = $failCount
            threshold = $ErrorRateThreshold
            window_rows = $ErrorWindowRows
            recent_failures = @($errorRows | Where-Object { $_.status -like 'failed:*' } | Select-Object -First 5)
        }
    }

    $phoneState.last_check_utc = (Get-Date -Format 'o')
}

Save-State -State $state
Write-WdLog INFO "poll cycle done"
exit 0
