# Author: RKOJ-ELENO :: 2026-05-23
# check-required-plugins.ps1 - verifies the Sanctum plugin allowlist is enabled.
#
# Operator 2026-05-23: "make sure bat file start checks if we have needed pluygins
# and if not installs them". This script is called by Sinister Start.bat first-run +
# can be re-invoked any time via:
#   powershell -File D:\Sinister Sanctum\automations\check-required-plugins.ps1 [-AutoInstall]
#
# Per the 2026-05-19 plugin-discipline doctrine (OPERATOR-DIRECTIVES.md), this script
# ONLY operates on the allowlist at automations/required-plugins.json. No bulk install.
# No marketplace browsing. Just: is the required plugin present? If not, surface +
# optionally install the single named plugin.
#
# Exit codes:
#   0 = all required plugins enabled (or manifest/settings missing - non-fatal)
#   1 = one or more required plugins missing and not installed
#   2 = install attempted but failed

param(
    [switch]$AutoInstall,
    [switch]$Quiet,
    [string]$ManifestPath = 'D:\Sinister Sanctum\automations\required-plugins.json',
    [string]$UserSettings = "$env:USERPROFILE\.claude\settings.json"
)

$ErrorActionPreference = 'Continue'

function Write-Themed {
    param([string]$Text, [string]$Color = 'Magenta')
    if ($Quiet) {
        Write-Host $Text
    } else {
        Write-Host $Text -ForegroundColor $Color
    }
}

function Write-Plain {
    param([string]$Text)
    Write-Host $Text
}

Write-Themed ""
Write-Themed "  ===================================================================="
Write-Themed "   Sinister Sanctum :: Required plugin check"
Write-Themed "  ===================================================================="

# --- Manifest ---
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    Write-Themed "  [WARN] Manifest not found: $ManifestPath" 'Yellow'
    Write-Themed "         Skipping plugin check (non-fatal)." 'Yellow'
    exit 0
}

try {
    $manifest = Get-Content -LiteralPath $ManifestPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
} catch {
    Write-Themed "  [WARN] Failed to parse manifest: $($_.Exception.Message)" 'Yellow'
    Write-Themed "         Skipping plugin check (non-fatal)." 'Yellow'
    exit 0
}

# --- User settings ---
if (-not (Test-Path -LiteralPath $UserSettings)) {
    Write-Themed "  [WARN] User settings not found: $UserSettings" 'Yellow'
    Write-Themed "         Operator may not have run Claude Code yet - skipping (non-fatal)." 'Yellow'
    exit 0
}

try {
    $settings = Get-Content -LiteralPath $UserSettings -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
} catch {
    Write-Themed "  [WARN] Failed to parse user settings: $($_.Exception.Message)" 'Yellow'
    Write-Themed "         Skipping plugin check (non-fatal)." 'Yellow'
    exit 0
}

# Build a hashtable of enabled plugin ids (case-insensitive)
$enabledIds = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
if ($settings.PSObject.Properties.Name -contains 'enabledPlugins' -and $settings.enabledPlugins) {
    foreach ($prop in $settings.enabledPlugins.PSObject.Properties) {
        if ($prop.Value) {
            [void]$enabledIds.Add($prop.Name)
        }
    }
}

Write-Themed ""
Write-Themed "  --- Required plugins ---" 'Magenta'

$requiredTotal = 0
$requiredEnabled = 0
$missingRequired = New-Object 'System.Collections.Generic.List[object]'
$script:installFailed = $false

if ($manifest.PSObject.Properties.Name -contains 'required' -and $manifest.required) {
    foreach ($plugin in $manifest.required) {
        $requiredTotal++
        if ($enabledIds.Contains([string]$plugin.id)) {
            $requiredEnabled++
            Write-Themed ("  [ OK ] {0} - enabled" -f $plugin.name) 'Green'
        } else {
            $missingRequired.Add($plugin) | Out-Null
            if ($AutoInstall) {
                Write-Themed ("  [INST] {0} - installing: {1}" -f $plugin.name, $plugin.install_cmd) 'Yellow'
                $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $plugin.install_cmd) -NoNewWindow -Wait -PassThru
                if ($proc.ExitCode -eq 0) {
                    Write-Themed ("         install OK (exit 0)") 'Green'
                } else {
                    Write-Themed ("         install FAILED (exit {0})" -f $proc.ExitCode) 'Red'
                    $script:installFailed = $true
                }
            } else {
                Write-Themed ("  [MISS] {0} - run: {1}" -f $plugin.name, $plugin.install_cmd) 'Red'
            }
        }
    }
} else {
    Write-Plain "  (none defined in manifest)"
}

Write-Themed ""
Write-Themed "  --- Recommended plugins (not auto-installed) ---" 'Magenta'

$recommendedTotal = 0
$recommendedEnabled = 0

if ($manifest.PSObject.Properties.Name -contains 'recommended' -and $manifest.recommended) {
    foreach ($plugin in $manifest.recommended) {
        $recommendedTotal++
        if ($enabledIds.Contains([string]$plugin.id)) {
            $recommendedEnabled++
            Write-Themed ("  [ OK ] {0} - enabled" -f $plugin.name) 'Green'
        } else {
            Write-Themed ("  [ -- ] {0} (recommended; not auto-installed)" -f $plugin.name) 'DarkGray'
        }
    }
} else {
    Write-Plain "  (none defined in manifest)"
}

Write-Themed ""
Write-Themed "  --------------------------------------------------------------------"
Write-Themed ("   Required: {0}/{1} enabled.  Recommended: {2}/{3} enabled." -f $requiredEnabled, $requiredTotal, $recommendedEnabled, $recommendedTotal) 'Magenta'
Write-Themed "  --------------------------------------------------------------------"
Write-Themed ""

if ($script:installFailed) {
    exit 2
}

if ($missingRequired.Count -gt 0 -and -not $AutoInstall) {
    exit 1
}

# If we auto-installed, the plugins won't show as enabled until Claude Code next reads
# settings. Treat install-attempted-no-failures as success.
exit 0
