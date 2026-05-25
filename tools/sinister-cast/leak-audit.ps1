# Author: RKOJ-ELENO :: 2026-05-24
# Lane: kernel-apk (EVE on Sinister Kernel APK, purple accent)
# Tool: sinister-cast / leak-audit.ps1
# Purpose: PC->phone leak-audit scanner. Pre-flight diagnostic for SinisterCast
#          deployment. Measures whether PC-side ADB exposure is detectable from
#          on-phone surfaces that Snap (and any other on-phone fingerprinter)
#          can read. Outputs structured JSON + human markdown.
#
# Composes with:
#   - Parent plan: D:\Sinister Sanctum\_shared-memory\plans\kernel-apk-adb-view-system-2026-05-24\plan.md (Phase B)
#   - Sibling: bridge.py (next to this script; SinisterCast PC-side bridge daemon)
#
# Surface inventory audited (mirrors Phase B.1 of parent plan):
#   #1 USB vendor/serial             (adb get-serialno + getprop ro.product.vendor.manufacturer)
#   #2 sys.usb.config                (getprop sys.usb.config)
#   #3 ADB_ENABLED                   (settings get global adb_enabled)
#   #4 /proc/bus/usb/devices         (cat /proc/bus/usb/devices ; root-only on Pixel 6a userdebug variants)
#   #5 ADB_WIFI_ENABLED              (settings get global adb_wifi_enabled)
#   #6 DEVELOPMENT_SETTINGS_ENABLED  (settings get global development_settings_enabled)
#   #7 Wakelocks from com.android.adb (dumpsys power | grep adb)
#   #8 dumpsys battery USB-state     (dumpsys battery | grep -E 'powered|USB|AC')
#   #9 /proc/net/tcp port 9001 (hex 2351) (cat /proc/net/tcp | grep :2351)
#
# Pure PowerShell 5.1 compatible. No && / ternary / null-coalescing.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$DeviceSerial = "",

    [Parameter(Mandatory = $false)]
    [string]$OutputDir = "",

    [Parameter(Mandatory = $false)]
    [switch]$Json,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# DeviceSerial is only required for live runs; dry-run enumerates the 9 surfaces without hitting a phone.
if (-not $DryRun -and [string]::IsNullOrWhiteSpace($DeviceSerial)) {
    Write-Host ""
    Write-Host "ERROR: -DeviceSerial is required unless -DryRun is set." -ForegroundColor 'Red'
    Write-Host "  Live run: -DeviceSerial <adb-serial>" -ForegroundColor 'DarkGray'
    Write-Host "  Dry run:  -DryRun (enumerates surfaces, no phone needed)" -ForegroundColor 'DarkGray'
    exit 2
}
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = $ScriptDir
}
if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# -------- Console color helpers (purple accent = #c084fc closest console approx) --------
$AccentColor = 'Magenta'   # console approximation of #c084fc
$DimColor    = 'DarkGray'
$OkColor     = 'Green'
$WarnColor   = 'Yellow'
$BadColor    = 'Red'

function Write-Accent([string]$s) { Write-Host $s -ForegroundColor $AccentColor }
function Write-Dim([string]$s)    { Write-Host $s -ForegroundColor $DimColor }
function Write-RiskColored([string]$risk, [string]$text) {
    $color = $OkColor
    if ($risk -eq 'MEDIUM') { $color = $WarnColor }
    if ($risk -eq 'HIGH')   { $color = $BadColor }
    if ($risk -eq 'UNKNOWN') { $color = $DimColor }
    if ($risk -eq 'ROOT-REQUIRED') { $color = $DimColor }
    Write-Host $text -ForegroundColor $color
}

# -------- Pre-flight: adb on PATH --------
$AdbCmd = Get-Command -Name 'adb' -ErrorAction SilentlyContinue
if (-not $DryRun -and $null -eq $AdbCmd) {
    Write-Host ""
    Write-Host "ERROR: 'adb' not found on PATH." -ForegroundColor $BadColor
    Write-Host "  Install Android platform-tools and add to PATH, then re-run." -ForegroundColor $DimColor
    Write-Host "  https://developer.android.com/tools/releases/platform-tools" -ForegroundColor $DimColor
    exit 2
}

# -------- Pre-flight: device reachable --------
if (-not $DryRun) {
    $stateRaw = & adb -s $DeviceSerial get-state 2>&1
    $stateExit = $LASTEXITCODE
    $stateText = ($stateRaw | Out-String).Trim()
    if ($stateExit -ne 0 -or $stateText -ne 'device') {
        Write-Host ""
        Write-Host "ERROR: device '$DeviceSerial' not in 'device' state." -ForegroundColor $BadColor
        Write-Host "  adb get-state returned: '$stateText' (exit=$stateExit)" -ForegroundColor $DimColor
        Write-Host "  Check: adb devices ; ensure phone unlocked + USB-debug authorized." -ForegroundColor $DimColor
        exit 3
    }
}

# -------- Surface check definitions --------
# Each check is a hashtable consumed by Invoke-Check
$Checks = @(
    @{
        Num         = 1
        Surface     = 'USB vendor/serial (get-serialno + ro.product.vendor.manufacturer)'
        AdbArgs     = @(@('get-serialno'), @('shell', 'getprop', 'ro.product.vendor.manufacturer'))
        RootOnly    = $false
        Rubric      = 'serialno+manufacturer'
    },
    @{
        Num         = 2
        Surface     = 'sys.usb.config'
        AdbArgs     = @(@('shell', 'getprop', 'sys.usb.config'))
        RootOnly    = $false
        Rubric      = 'sys.usb.config'
    },
    @{
        Num         = 3
        Surface     = 'Settings.Global.ADB_ENABLED'
        AdbArgs     = @(@('shell', 'settings', 'get', 'global', 'adb_enabled'))
        RootOnly    = $false
        Rubric      = 'adb_enabled'
    },
    @{
        Num         = 4
        Surface     = '/proc/bus/usb/devices'
        AdbArgs     = @(@('shell', 'cat', '/proc/bus/usb/devices'))
        RootOnly    = $true
        Rubric      = 'usb_devices'
    },
    @{
        Num         = 5
        Surface     = 'Settings.Global.ADB_WIFI_ENABLED'
        AdbArgs     = @(@('shell', 'settings', 'get', 'global', 'adb_wifi_enabled'))
        RootOnly    = $false
        Rubric      = 'adb_wifi_enabled'
    },
    @{
        Num         = 6
        Surface     = 'Settings.Global.DEVELOPMENT_SETTINGS_ENABLED'
        AdbArgs     = @(@('shell', 'settings', 'get', 'global', 'development_settings_enabled'))
        RootOnly    = $false
        Rubric      = 'development_settings_enabled'
    },
    @{
        Num         = 7
        Surface     = 'Wakelocks from com.android.adb (dumpsys power | grep adb)'
        AdbArgs     = @(@('shell', 'dumpsys power | grep -i adb'))
        RootOnly    = $false
        Rubric      = 'adb_wakelocks'
    },
    @{
        Num         = 8
        Surface     = 'dumpsys battery USB-state'
        AdbArgs     = @(@('shell', "dumpsys battery | grep -E 'powered|USB|AC'"))
        RootOnly    = $false
        Rubric      = 'battery_usb'
    },
    @{
        Num         = 9
        Surface     = '/proc/net/tcp port 9001 (hex 2351) -- SinisterCast viewer port'
        AdbArgs     = @(@('shell', 'cat /proc/net/tcp | grep :2351'))
        RootOnly    = $false
        Rubric      = 'sinistercast_port'
    }
)

# -------- Rubric: per-surface risk evaluation --------
# Each rubric receives raw output and returns @{ Risk = 'LOW|MEDIUM|HIGH|UNKNOWN|ROOT-REQUIRED' ; Interpretation = '...' }
function Get-RubricVerdict {
    param(
        [string]$Rubric,
        [string]$Raw,
        [bool]$IsDryRun
    )

    $verdict = @{ Risk = 'UNKNOWN'; Interpretation = '(no verdict logic for this rubric)' }
    $rawLow = $Raw.ToLower()

    if ($IsDryRun) {
        $verdict.Risk = 'UNKNOWN'
        $verdict.Interpretation = 'DRY-RUN: command not executed; rubric pending real output.'
        return $verdict
    }

    switch ($Rubric) {
        'serialno+manufacturer' {
            if ([string]::IsNullOrWhiteSpace($Raw)) {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = 'Empty result -- device may be offline mid-check.'
            } else {
                # Any non-empty serial is exposed via ADB-USB. WiFi-ADB serial is the IP:port form.
                if ($Raw -match ':\d+$') {
                    $verdict.Risk = 'LOW'
                    $verdict.Interpretation = 'Serial appears IP-based (WiFi-ADB). PC USB fingerprint not leaking.'
                } else {
                    $verdict.Risk = 'MEDIUM'
                    $verdict.Interpretation = 'Hardware serial visible via USB-ADB. Migrate to WiFi-ADB (adb tcpip 5555) to remove this surface.'
                }
            }
        }
        'sys.usb.config' {
            if ($rawLow -match 'mtp,adb' -or $rawLow -match 'ptp,adb') {
                $verdict.Risk = 'HIGH'
                $verdict.Interpretation = 'sys.usb.config shows USB-cable ADB mode (mtp,adb / ptp,adb). Snap can read this prop and infer wired PC. Switch to WiFi-ADB.'
            } elseif ($rawLow -match 'none,adb' -or $rawLow -match 'adb$') {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'sys.usb.config shows wireless-mode ADB (none,adb / adb). No USB-cable fingerprint.'
            } else {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = "Unexpected sys.usb.config value: '$Raw'. Investigate manually."
            }
        }
        'adb_enabled' {
            if ($Raw -match '^\s*1\s*$') {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = 'ADB_ENABLED=1 -- visible to any app with Settings.Global read. Hide via lukeprivacy KPM hide-target if not already.'
            } elseif ($Raw -match '^\s*0\s*$') {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'ADB_ENABLED=0 -- surface clean. (But ADB would not be working at all if truly 0; confirm.)'
            } else {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = "Unexpected adb_enabled value: '$Raw'."
            }
        }
        'usb_devices' {
            if ($Raw -match 'permission denied' -or $rawLow -match 'no such file' -or [string]::IsNullOrWhiteSpace($Raw)) {
                $verdict.Risk = 'ROOT-REQUIRED'
                $verdict.Interpretation = '/proc/bus/usb/devices unreadable without root or absent on this kernel build. Skipped -- re-run with root shell if visibility needed.'
            } elseif ($rawLow -match 'product=18d1' -or $rawLow -match 'bus=01') {
                $verdict.Risk = 'HIGH'
                $verdict.Interpretation = 'USB device tree readable -- Snap (with root or unusual permission) could enumerate Google vendor + PC HCD. Migrate to WiFi-ADB to empty this tree.'
            } else {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = 'USB device tree readable but content does not match known PC-cable signature. Inspect manually.'
            }
        }
        'adb_wifi_enabled' {
            if ($Raw -match '^\s*1\s*$') {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = 'ADB_WIFI_ENABLED=1 -- visible to apps with Settings.Global read. Hide via lukeprivacy KPM hide-target.'
            } elseif ($Raw -match '^\s*0\s*$' -or $rawLow -match 'null') {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'ADB_WIFI_ENABLED unset/0 -- surface clean.'
            } else {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = "Unexpected adb_wifi_enabled value: '$Raw'."
            }
        }
        'development_settings_enabled' {
            if ($Raw -match '^\s*1\s*$') {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = 'DEVELOPMENT_SETTINGS_ENABLED=1 -- visible to apps. Hide via lukeprivacy KPM hide-target.'
            } elseif ($Raw -match '^\s*0\s*$' -or $rawLow -match 'null') {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'DEVELOPMENT_SETTINGS_ENABLED unset/0 -- surface clean.'
            } else {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = "Unexpected development_settings_enabled value: '$Raw'."
            }
        }
        'adb_wakelocks' {
            if ([string]::IsNullOrWhiteSpace($Raw)) {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'No adb-related wakelocks present in dumpsys power. Clean.'
            } elseif ($rawLow -match 'adb') {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = 'adb wakelock(s) visible via dumpsys power. Apps with WAKE_LOCK perm can read this. Filter via lukeprivacy KPM if Snap is on the target list.'
            } else {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = 'Unexpected wakelock output -- inspect raw.'
            }
        }
        'battery_usb' {
            if ($rawLow -match 'usb powered: true' -or $rawLow -match 'powered: usb') {
                $verdict.Risk = 'HIGH'
                $verdict.Interpretation = 'dumpsys battery reports USB power source -- directly visible to all apps, confirms cable. Switch to WiFi-ADB OR spoof battery source for com.snapchat.android.'
            } elseif ($rawLow -match 'ac powered: true' -or $rawLow -match 'usb powered: false') {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'No USB power source reported. WiFi-ADB scenario likely.'
            } else {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = 'Could not parse battery power source from raw output.'
            }
        }
        'sinistercast_port' {
            if ([string]::IsNullOrWhiteSpace($Raw)) {
                $verdict.Risk = 'LOW'
                $verdict.Interpretation = 'Port 9001 not present in /proc/net/tcp. SinisterCast not currently listening (or already hidden via lukeprivacy KPM).'
            } elseif ($Raw -match ':2351') {
                $verdict.Risk = 'MEDIUM'
                $verdict.Interpretation = 'Port 9001 (hex 2351) enumerable via /proc/net/tcp. Snap can read this. Add hide-target to lukeprivacy KPM for SinisterCast deployments.'
            } else {
                $verdict.Risk = 'UNKNOWN'
                $verdict.Interpretation = 'Output present but did not match :2351 -- inspect raw.'
            }
        }
        default {
            $verdict.Risk = 'UNKNOWN'
            $verdict.Interpretation = "(no rubric implemented for '$Rubric')"
        }
    }

    return $verdict
}

# -------- Adb invocation wrapper --------
function Invoke-AdbCmd {
    param(
        [string]$Serial,
        [string[]]$AdbArgs,
        [bool]$IsDryRun
    )
    $argsRendered = ($AdbArgs -join ' ')
    $cmdLine = "adb -s $Serial $argsRendered"
    if ($IsDryRun) {
        return @{ CmdLine = $cmdLine; Raw = "(dry-run: not executed)"; ExitCode = 0 }
    }
    $allArgs = @('-s', $Serial) + $AdbArgs
    $output = & adb @allArgs 2>&1
    $exit = $LASTEXITCODE
    $raw = ($output | Out-String).Trim()
    return @{ CmdLine = $cmdLine; Raw = $raw; ExitCode = $exit }
}

# -------- Per-check executor --------
function Invoke-Check {
    param(
        [hashtable]$Check,
        [string]$Serial,
        [bool]$IsDryRun
    )

    $combinedRaw = ''
    $combinedCmds = @()
    foreach ($argSet in $Check.AdbArgs) {
        $res = Invoke-AdbCmd -Serial $Serial -AdbArgs $argSet -IsDryRun $IsDryRun
        $combinedCmds += $res.CmdLine
        if ($combinedRaw.Length -gt 0) { $combinedRaw += "`n---`n" }
        $combinedRaw += $res.Raw
    }

    $verdict = Get-RubricVerdict -Rubric $Check.Rubric -Raw $combinedRaw -IsDryRun $IsDryRun

    # Root-only override: in dry-run we surface ROOT-REQUIRED for clarity
    if ($Check.RootOnly -and $IsDryRun) {
        $verdict.Risk = 'ROOT-REQUIRED'
        $verdict.Interpretation = 'DRY-RUN: root-only surface. Will report ROOT-REQUIRED if shell lacks root at audit time.'
    }

    return @{
        Num            = $Check.Num
        Surface        = $Check.Surface
        Commands       = $combinedCmds
        Raw            = $combinedRaw
        Risk           = $verdict.Risk
        Interpretation = $verdict.Interpretation
        RootOnly       = $Check.RootOnly
    }
}

# -------- Run all checks --------
Write-Host ""
Write-Accent "============================================================"
Write-Accent "  Sinister Cast -- Leak Audit"
Write-Accent "  Author: RKOJ-ELENO :: 2026-05-24"
Write-Accent "============================================================"
Write-Dim   "  Device:    $DeviceSerial"
$modeLabel = 'LIVE'
if ($DryRun) { $modeLabel = 'DRY-RUN (no adb calls)' }
Write-Dim   "  Mode:      $modeLabel"
Write-Dim   "  OutputDir: $OutputDir"
Write-Host  ""

$findings = @()
foreach ($check in $Checks) {
    Write-Host ("  [{0}] {1}" -f $check.Num, $check.Surface)
    $finding = Invoke-Check -Check $check -Serial $DeviceSerial -IsDryRun:$DryRun.IsPresent
    $findings += $finding
    Write-RiskColored -risk $finding.Risk -text ("      -> Risk: {0,-14} | {1}" -f $finding.Risk, $finding.Interpretation)
}

# -------- Overall risk = max --------
$riskRank = @{ 'LOW' = 1; 'ROOT-REQUIRED' = 1; 'UNKNOWN' = 2; 'MEDIUM' = 3; 'HIGH' = 4 }
$overallRank = 0
$overallRisk = 'LOW'
foreach ($f in $findings) {
    $r = $riskRank[$f.Risk]
    if ($null -eq $r) { $r = 2 }
    if ($r -gt $overallRank) {
        $overallRank = $r
        $overallRisk = $f.Risk
    }
}
# Normalize UNKNOWN/ROOT-REQUIRED never being the "winner" if any concrete LOW/MEDIUM/HIGH is present
$concreteRisks = $findings | Where-Object { $_.Risk -in @('LOW','MEDIUM','HIGH') }
if ($concreteRisks.Count -gt 0) {
    $maxConcreteRank = 0
    $maxConcreteRisk = 'LOW'
    foreach ($c in $concreteRisks) {
        $r = $riskRank[$c.Risk]
        if ($r -gt $maxConcreteRank) {
            $maxConcreteRank = $r
            $maxConcreteRisk = $c.Risk
        }
    }
    if ($maxConcreteRank -ge $overallRank) {
        $overallRisk = $maxConcreteRisk
    }
}

Write-Host ""
Write-Accent "------------------------------------------------------------"
Write-RiskColored -risk $overallRisk -text ("  Overall risk: {0}" -f $overallRisk)
Write-Accent "------------------------------------------------------------"
Write-Host ""

# -------- Render markdown report --------
$tsUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmmssZ")
$serialSafe = ($DeviceSerial -replace '[^A-Za-z0-9._-]', '_')
$mdPath   = Join-Path $OutputDir ("leak-audit-{0}-{1}.md" -f $serialSafe, $tsUtc)
$jsonPath = Join-Path $OutputDir ("leak-audit-{0}-{1}.json" -f $serialSafe, $tsUtc)

$mdLines = @()
$mdLines += "# Sinister Cast -- Leak Audit Report"
$mdLines += ""
$mdLines += "> Author: RKOJ-ELENO :: 2026-05-24"
$mdLines += "> Tool: ``tools/sinister-cast/leak-audit.ps1``"
$mdLines += "> Composes with: parent plan ``_shared-memory/plans/kernel-apk-adb-view-system-2026-05-24/plan.md`` (Phase B)"
$mdLines += ""
$mdLines += "| Field | Value |"
$mdLines += "|---|---|"
$mdLines += "| Device serial | ``$DeviceSerial`` |"
$mdLines += "| Timestamp (UTC) | ``$tsUtc`` |"
$mdLines += "| Mode | $modeLabel |"
$mdLines += "| Overall risk | **$overallRisk** |"
$mdLines += ""
$mdLines += "## Findings"
$mdLines += ""
$mdLines += "| # | Surface | Risk | Interpretation |"
$mdLines += "|---|---|---|---|"
foreach ($f in $findings) {
    $interpEsc = $f.Interpretation -replace '\|', '\|'
    $surfaceEsc = $f.Surface -replace '\|', '\|'
    $mdLines += "| {0} | {1} | **{2}** | {3} |" -f $f.Num, $surfaceEsc, $f.Risk, $interpEsc
}
$mdLines += ""
$mdLines += "## Raw evidence"
$mdLines += ""
foreach ($f in $findings) {
    $mdLines += "### [{0}] {1}" -f $f.Num, $f.Surface
    $mdLines += ""
    $mdLines += "Commands:"
    $mdLines += '```'
    foreach ($c in $f.Commands) { $mdLines += $c }
    $mdLines += '```'
    $mdLines += ""
    $mdLines += "Raw output:"
    $mdLines += '```'
    if ([string]::IsNullOrWhiteSpace($f.Raw)) {
        $mdLines += "(empty)"
    } else {
        foreach ($line in ($f.Raw -split "`n")) { $mdLines += $line.TrimEnd() }
    }
    $mdLines += '```'
    $mdLines += ""
    $mdLines += "Risk: **{0}**  --  {1}" -f $f.Risk, $f.Interpretation
    $mdLines += ""
}
$mdLines += "## Notes"
$mdLines += ""
$mdLines += "- Risk ladder: LOW < UNKNOWN/ROOT-REQUIRED < MEDIUM < HIGH."
$mdLines += "- Overall risk = max of all per-surface risks (concrete LOW/MEDIUM/HIGH outrank UNKNOWN/ROOT-REQUIRED)."
$mdLines += "- This is a pre-flight audit; closure work items are tracked under Phase B.2 of the parent plan."
$mdLines += "- See ``leak-audit.README.md`` next to this script for invocation examples."
$mdLines += ""

$mdContent = $mdLines -join [Environment]::NewLine
Set-Content -LiteralPath $mdPath -Value $mdContent -Encoding UTF8
Write-Dim ("  Wrote markdown: {0}" -f $mdPath)

# -------- Render JSON report --------
if ($Json.IsPresent) {
    $findingsForJson = @()
    foreach ($f in $findings) {
        $findingsForJson += [pscustomobject]@{
            num            = $f.Num
            surface        = $f.Surface
            commands       = $f.Commands
            raw            = $f.Raw
            risk           = $f.Risk
            interpretation = $f.Interpretation
            root_only      = $f.RootOnly
        }
    }
    $jsonObj = [pscustomobject]@{
        schema        = 'sinister.leak-audit.v1'
        ts_utc        = $tsUtc
        device_serial = $DeviceSerial
        mode          = $modeLabel
        findings      = $findingsForJson
        overall_risk  = $overallRisk
    }
    $jsonText = $jsonObj | ConvertTo-Json -Depth 8
    Set-Content -LiteralPath $jsonPath -Value $jsonText -Encoding UTF8
    Write-Dim ("  Wrote JSON:     {0}" -f $jsonPath)
}

Write-Host ""
Write-Accent "  Done."
Write-Host ""

exit 0
