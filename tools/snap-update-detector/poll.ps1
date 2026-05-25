# Author: RKOJ-ELENO :: 2026-05-24
# Lane: kernel-apk (Snap auto-update pipeline, Phase 0)
# Purpose: Poll multiple sources to detect when Snap pushes a new APK version.
#          Writes canonical state to _shared-memory/snap-version-state.json
#          and emits a fleet-update row when a new version is first observed.
# Composes-with:
#   - _shared-memory/knowledge/fleet-update-channel-doctrine-2026-05-24.md
#   - _shared-memory/knowledge/panel-localhost-routing-2026-05-19.md
#   - _shared-memory/knowledge/headless-spawn-pattern-2026-05-23.md
#   - _shared-memory/plans/snap-auto-update-on-snap-version-2026-05-24/design.md
# Pure PowerShell 5.1 (no PS7-only operators, no non-ASCII chars).

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$StateFile = '_shared-memory\snap-version-state.json',
    [string]$CurrentCanonicalVersion = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# ---- Helpers ----------------------------------------------------------------

function Get-IsoUtc {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Try-ParseVersion {
    param([string]$Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return $null }
    $trimmed = $Raw.Trim()
    try {
        return [version]$trimmed
    } catch {
        return $null
    }
}

function Compare-Versions {
    param([string]$A, [string]$B)
    # Returns 1 if A > B, -1 if A < B, 0 if equal, $null if either unparseable
    $va = Try-ParseVersion $A
    $vb = Try-ParseVersion $B
    if (-not $va -or -not $vb) { return $null }
    if ($va -gt $vb) { return 1 }
    if ($va -lt $vb) { return -1 }
    return 0
}

# ---- Source pollers ---------------------------------------------------------

function Get-VersionFromApkMirrorRss {
    Write-Verbose "Source A: polling APKMirror RSS"
    try {
        $url = 'https://www.apkmirror.com/apk/snap-inc/snapchat/feed/'
        $resp = Invoke-RestMethod -Uri $url -TimeoutSec 15 -UseBasicParsing
        # Invoke-RestMethod auto-parses RSS XML into objects with .title etc.
        $titles = @()
        if ($resp -and $resp.title) { $titles += ,$resp.title }
        if ($resp -and $resp.item)  { foreach ($it in $resp.item) { if ($it.title) { $titles += $it.title } } }
        foreach ($t in $titles) {
            $text = if ($t -is [string]) { $t } elseif ($t.'#cdata-section') { $t.'#cdata-section' } else { "$t" }
            if ($text -match 'Snapchat\s+([0-9]+(?:\.[0-9]+){2,3})\s+by\s+Snap\s+Inc') {
                $v = $matches[1]
                $parsed = Try-ParseVersion $v
                if ($parsed) {
                    Write-Verbose ("  apkmirror-rss: " + $v)
                    return $v
                }
            }
        }
        Write-Verbose "  apkmirror-rss: no parseable version in feed"
        return $null
    } catch {
        Write-Warning ("apkmirror-rss failed: " + $_.Exception.Message)
        return $null
    }
}

function Get-VersionFromPlayStoreHtml {
    Write-Verbose "Source B: polling Play Store HTML"
    try {
        $url = 'https://play.google.com/store/apps/details?id=com.snapchat.android'
        $resp = Invoke-WebRequest -Uri $url -TimeoutSec 15 -UseBasicParsing
        $html = $resp.Content
        if (-not $html) { return $null }
        # Modern Play HTML stores version in JS payloads as [\"x.y.z.w\"]; also try Current Version block.
        $rx = [regex]'\[\\?"([0-9]+(?:\.[0-9]+){2,3})\\?"\]'
        $m = $rx.Matches($html)
        foreach ($match in $m) {
            $v = $match.Groups[1].Value
            $parsed = Try-ParseVersion $v
            if ($parsed -and $parsed.Major -ge 5) {
                # Reject obviously-not-Snapchat versions (Major<5 is unlikely for this app)
                Write-Verbose ("  play-store-html: " + $v)
                return $v
            }
        }
        # Fallback: legacy 'Current Version' block
        if ($html -match 'Current Version[^0-9]+([0-9]+(?:\.[0-9]+){2,3})') {
            $v = $matches[1]
            $parsed = Try-ParseVersion $v
            if ($parsed) {
                Write-Verbose ("  play-store-html (legacy): " + $v)
                return $v
            }
        }
        Write-Verbose "  play-store-html: no parseable version in HTML"
        return $null
    } catch {
        Write-Warning ("play-store-html failed: " + $_.Exception.Message)
        return $null
    }
}

function Get-VersionFromPhoneHeartbeat {
    param([string]$Root)
    Write-Verbose "Source C: scanning phone heartbeats"
    $hbDir = Join-Path $Root '_shared-memory\heartbeats'
    if (-not (Test-Path $hbDir)) {
        Write-Verbose "  heartbeats dir missing"
        return $null
    }
    $candidates = @('kernel-apk.json', 'apk.json')
    $best = $null
    foreach ($name in $candidates) {
        $path = Join-Path $hbDir $name
        if (-not (Test-Path $path)) { continue }
        try {
            $raw = Get-Content -Raw -LiteralPath $path -ErrorAction Stop
            $obj = $raw | ConvertFrom-Json -ErrorAction Stop
            $fields = @('snap_version', 'app_version', 'apk_versionName')
            foreach ($f in $fields) {
                $val = $obj.$f
                if ($val) {
                    $parsed = Try-ParseVersion ([string]$val)
                    if ($parsed) {
                        if (-not $best -or ((Compare-Versions ([string]$val) $best) -eq 1)) {
                            $best = [string]$val
                        }
                    }
                }
            }
        } catch {
            Write-Warning ("phone-heartbeat parse failed for " + $name + ": " + $_.Exception.Message)
        }
    }
    if ($best) { Write-Verbose ("  phone-heartbeat: " + $best) }
    return $best
}

# ---- State load/save --------------------------------------------------------

function Load-State {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        $raw = Get-Content -Raw -LiteralPath $Path -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
        return ($raw | ConvertFrom-Json -ErrorAction Stop)
    } catch {
        Write-Warning ("Failed to load state file (treating as missing): " + $_.Exception.Message)
        return $null
    }
}

function Save-State-Atomic {
    param([string]$Path, $StateObj)
    # Single-instance lock note: if concurrent pollers ever exist, gate via
    # _shared-memory/.snap-version-state.lock (acquire-then-write). For now,
    # single-instance via Task Scheduler is fine.
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $tmp = $Path + '.tmp'
    $json = ($StateObj | ConvertTo-Json -Depth 12)
    [System.IO.File]::WriteAllText($tmp, $json, [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

function Emit-FleetUpdate {
    param([string]$Root, [string]$OldVersion, [string]$NewVersion)
    $fuPath = Join-Path $Root '_shared-memory\fleet-updates.jsonl'
    $id = 'fu-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss') + '-' + ([guid]::NewGuid().ToString('N').Substring(0,6))
    $row = [ordered]@{
        id           = $id
        ts_utc       = (Get-IsoUtc)
        priority     = 'high'
        kind         = 'snap-version-detected'
        message      = "SNAP-VERSION-DETECTED: latest_observed_version=$NewVersion exceeds current_canonical_version=$OldVersion. Auto-update pipeline Phase 0 detection. Phase 1 (re-pull + diff) should fire next."
        target_slugs = @('kernel-apk', 'sanctum')
        pushed_by    = 'snap-update-detector'
        acks         = @()
    }
    $line = ($row | ConvertTo-Json -Compress -Depth 6)
    Add-Content -LiteralPath $fuPath -Value $line -Encoding UTF8
}

# ---- Main -------------------------------------------------------------------

$exitCode = 0
$partialFailure = $false

$absStatePath = if ([System.IO.Path]::IsPathRooted($StateFile)) { $StateFile } else { Join-Path $SanctumRoot $StateFile }
Write-Verbose ("State file: " + $absStatePath)

$prevState = Load-State -Path $absStatePath
if (-not $CurrentCanonicalVersion) {
    if ($prevState -and $prevState.current_canonical_version) {
        $CurrentCanonicalVersion = [string]$prevState.current_canonical_version
    } else {
        $CurrentCanonicalVersion = '13.88.1.0'
    }
}
Write-Verbose ("Current canonical: " + $CurrentCanonicalVersion)

$wasUpdatePendingBefore = $false
if ($prevState -and $prevState.is_update_pending) { $wasUpdatePendingBefore = [bool]$prevState.is_update_pending }
$lastPromotion = ''
if ($prevState -and $prevState.last_canonical_promotion_utc) { $lastPromotion = [string]$prevState.last_canonical_promotion_utc }

$history = @()
if ($prevState -and $prevState.poll_history) {
    foreach ($h in $prevState.poll_history) { $history += $h }
}

$sources = @()
$versions = @()

$vA = Get-VersionFromApkMirrorRss
if ($vA) { $sources += 'apkmirror-rss'; $versions += $vA; $history += [ordered]@{ ts_utc = (Get-IsoUtc); source = 'apkmirror-rss'; version = $vA } }
else { $partialFailure = $true }

$vB = Get-VersionFromPlayStoreHtml
if ($vB) { $sources += 'play-store-html'; $versions += $vB; $history += [ordered]@{ ts_utc = (Get-IsoUtc); source = 'play-store-html'; version = $vB } }
else { $partialFailure = $true }

$vC = Get-VersionFromPhoneHeartbeat -Root $SanctumRoot
if ($vC) { $sources += 'phone-heartbeat'; $versions += $vC; $history += [ordered]@{ ts_utc = (Get-IsoUtc); source = 'phone-heartbeat'; version = $vC } }
else { $partialFailure = $true }

# Keep only last 10 history entries
if ($history.Count -gt 10) { $history = $history[($history.Count - 10)..($history.Count - 1)] }

$latestObserved = $CurrentCanonicalVersion
foreach ($v in $versions) {
    $cmp = Compare-Versions $v $latestObserved
    if ($cmp -eq 1) { $latestObserved = $v }
}

$isPending = $false
$cmpFinal = Compare-Versions $latestObserved $CurrentCanonicalVersion
if ($cmpFinal -eq 1) { $isPending = $true }

$state = [ordered]@{
    schema_version              = 'sinister.snap-version-state.v1'
    current_canonical_version   = $CurrentCanonicalVersion
    latest_observed_version     = $latestObserved
    is_update_pending           = $isPending
    detected_at_utc             = (Get-IsoUtc)
    detection_sources           = $sources
    last_canonical_promotion_utc = $lastPromotion
    poll_history                = $history
}

if ($DryRun) {
    Write-Host "DRY-RUN: would write the following state object:"
    Write-Host (($state | ConvertTo-Json -Depth 12))
} else {
    try {
        Save-State-Atomic -Path $absStatePath -StateObj $state
        Write-Verbose ("Wrote state file: " + $absStatePath)
    } catch {
        Write-Error ("Hard failure writing state file: " + $_.Exception.Message)
        exit 2
    }
    if ($isPending -and -not $wasUpdatePendingBefore) {
        try {
            Emit-FleetUpdate -Root $SanctumRoot -OldVersion $CurrentCanonicalVersion -NewVersion $latestObserved
            Write-Verbose "Emitted fleet-update row (kind=snap-version-detected, priority=high)"
        } catch {
            Write-Warning ("Failed to emit fleet-update row: " + $_.Exception.Message)
            $partialFailure = $true
        }
    }
}

if ($partialFailure) { $exitCode = 1 }
exit $exitCode
