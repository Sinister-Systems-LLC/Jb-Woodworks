# Author: RKOJ-ELENO :: 2026-05-21
# install-rkoj-shortcuts.ps1
# Auto-creates RKOJ desktop + Start menu .lnk shortcuts so the operator can pin
# RKOJ to the taskbar, Start menu, etc.
#
# Persona: EVE (Sinister Sanctum orchestration agent)
# Branch:  agent/sinister-sanctum/cli-dispatcher-2026-05-21
#
# Creates 4 shortcuts (idempotent: skips if Target+Args already match):
#   1. C:\Users\Zonia\Desktop\RKOJ.lnk                 -> RKOJ.exe (Forge TUI)
#   2. C:\Users\Zonia\Desktop\RKOJ Shell.lnk           -> RKOJ.exe --shell
#   3. Start Menu\Programs\RKOJ.lnk                    -> RKOJ.exe (Forge TUI)
#   4. Start Menu\Programs\RKOJ Setup Wizard.lnk       -> RKOJ-Setup.bat
#
# Optional: pin-to-taskbar prompt (Windows 10 only).

[CmdletBinding()]
param(
    [switch]$Quiet,
    [switch]$NoPinPrompt
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$SanctumRoot   = 'D:\Sinister Sanctum'
$Desktop       = 'C:\Users\Zonia\Desktop'
$StartMenu     = 'C:\Users\Zonia\AppData\Roaming\Microsoft\Windows\Start Menu\Programs'
$IconCandidate = Join-Path $SanctumRoot 'assets\sinister-logo.ico'
$SetupBat      = Join-Path $SanctumRoot 'tools\session-launcher\RKOJ-Setup.bat'
$ProgressLog   = Join-Path $SanctumRoot '_shared-memory\PROGRESS\setup-runs.log'

function Write-Info($msg) { if (-not $Quiet) { Write-Host "[install-rkoj-shortcuts] $msg" -ForegroundColor Cyan } }
function Write-Ok($msg)   { if (-not $Quiet) { Write-Host "[install-rkoj-shortcuts] $msg" -ForegroundColor Green } }
function Write-Warn2($m)  { Write-Host "[install-rkoj-shortcuts] WARN: $m" -ForegroundColor Yellow }
function Write-Err2($m)   { Write-Host "[install-rkoj-shortcuts] ERR : $m" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# 1. Locate the RKOJ executable
# ---------------------------------------------------------------------------
$RkojExe = $null
$candidates = @(
    (Join-Path $Desktop 'RKOJ.exe'),
    (Join-Path $Desktop 'RKOJ-v1.1.0.exe')
)
foreach ($c in $candidates) {
    if (Test-Path -LiteralPath $c) {
        $RkojExe = $c
        break
    }
}

if (-not $RkojExe) {
    Write-Err2 "Neither RKOJ.exe nor RKOJ-v1.1.0.exe found on Desktop."
    Write-Err2 "Looked in: $($candidates -join '; ')"
    Write-Err2 "Rebuild the RKOJ exe first:"
    Write-Err2 "  pwsh -File 'D:\Sinister Sanctum\automations\build\forge-exe\build.ps1'"
    exit 1
}
Write-Info "Found RKOJ exe: $RkojExe"

# Pick icon
$IconPath = if (Test-Path -LiteralPath $IconCandidate) { $IconCandidate } else { $RkojExe }
Write-Info "Using icon: $IconPath"

# Ensure setup bat exists (warn-only; shortcut still created)
if (-not (Test-Path -LiteralPath $SetupBat)) {
    Write-Warn2 "Setup wizard bat not found: $SetupBat (Start Menu shortcut will still be written)"
}

# ---------------------------------------------------------------------------
# 2. Shortcut spec
# ---------------------------------------------------------------------------
$Shortcuts = @(
    [pscustomobject]@{
        Path        = Join-Path $Desktop 'RKOJ.lnk'
        Target      = $RkojExe
        Arguments   = ''
        WorkingDir  = $SanctumRoot
        Icon        = $IconPath
        Description = 'RKOJ - Sinister Forge TUI (EVE orchestration)'
    },
    [pscustomobject]@{
        Path        = Join-Path $Desktop 'RKOJ Shell.lnk'
        Target      = $RkojExe
        Arguments   = '--shell'
        WorkingDir  = $SanctumRoot
        Icon        = $IconPath
        Description = 'RKOJ Shell - interactive command dispatcher'
    },
    [pscustomobject]@{
        Path        = Join-Path $StartMenu 'RKOJ.lnk'
        Target      = $RkojExe
        Arguments   = ''
        WorkingDir  = $SanctumRoot
        Icon        = $IconPath
        Description = 'RKOJ - Sinister Forge TUI (EVE orchestration)'
    },
    [pscustomobject]@{
        Path        = Join-Path $StartMenu 'RKOJ Setup Wizard.lnk'
        Target      = $SetupBat
        Arguments   = ''
        WorkingDir  = $SanctumRoot
        Icon        = $IconPath
        Description = 'RKOJ first-run setup wizard'
    }
)

# ---------------------------------------------------------------------------
# 3. Create shortcuts (idempotent)
# ---------------------------------------------------------------------------
$WSH = New-Object -ComObject WScript.Shell
$created = 0
$skipped = 0
$failed  = 0

foreach ($s in $Shortcuts) {
    $parent = Split-Path -LiteralPath $s.Path -Parent
    if (-not (Test-Path -LiteralPath $parent)) {
        try {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        } catch {
            Write-Err2 "Could not create parent dir $parent : $($_.Exception.Message)"
            $failed++
            continue
        }
    }

    # Idempotent check: read existing .lnk, compare Target+Args
    if (Test-Path -LiteralPath $s.Path) {
        try {
            $existing = $WSH.CreateShortcut($s.Path)
            if ($existing.TargetPath -eq $s.Target -and $existing.Arguments -eq $s.Arguments) {
                Write-Info "Skip (unchanged): $($s.Path)"
                $skipped++
                continue
            }
        } catch {
            # Fall through and overwrite
        }
    }

    try {
        $lnk = $WSH.CreateShortcut($s.Path)
        $lnk.TargetPath       = $s.Target
        $lnk.Arguments        = $s.Arguments
        $lnk.WorkingDirectory = $s.WorkingDir
        $lnk.IconLocation     = "$($s.Icon),0"
        $lnk.Description      = $s.Description
        $lnk.WindowStyle      = 1   # Normal window
        $lnk.Save()
        Write-Ok "Wrote: $($s.Path)"
        $created++
    } catch {
        Write-Err2 "Failed to write $($s.Path): $($_.Exception.Message)"
        $failed++
    }
}

# ---------------------------------------------------------------------------
# 4. Optional pin-to-taskbar (Windows 10 only)
# ---------------------------------------------------------------------------
$pinResult = 'skipped'
if (-not $NoPinPrompt) {
    $winBuild = [Environment]::OSVersion.Version.Build
    # Windows 10 builds: 10240 .. 19999  (Win11 = 22000+, no shell.application pin verb)
    if ($winBuild -ge 10240 -and $winBuild -lt 22000) {
        Write-Info "Detected Windows 10 (build $winBuild). Taskbar pin is supported."
        $reply = Read-Host "Pin RKOJ.exe to the taskbar now? (y/N)"
        if ($reply -match '^[Yy]') {
            try {
                $shell    = New-Object -ComObject Shell.Application
                $folder   = $shell.Namespace((Split-Path -LiteralPath $RkojExe -Parent))
                $item     = $folder.ParseName((Split-Path -LiteralPath $RkojExe -Leaf))
                $verb     = $item.Verbs() | Where-Object { $_.Name -replace '&','' -match '^Pin to taskbar$' }
                if ($verb) {
                    $verb.DoIt()
                    Write-Ok "Pin-to-taskbar verb invoked."
                    $pinResult = 'invoked'
                } else {
                    Write-Warn2 "Pin-to-taskbar verb not found in shell menu (Windows policy may have removed it)."
                    $pinResult = 'verb-missing'
                }
            } catch {
                Write-Warn2 "Pin-to-taskbar failed: $($_.Exception.Message)"
                $pinResult = 'failed'
            }
        } else {
            Write-Info "Skipping taskbar pin (operator declined)."
        }
    } else {
        Write-Info "OS build $winBuild - taskbar pin verb not available; skipping."
        $pinResult = 'unsupported-os'
    }
}

# ---------------------------------------------------------------------------
# 5. Append setup-runs.log entry
# ---------------------------------------------------------------------------
try {
    $logParent = Split-Path -LiteralPath $ProgressLog -Parent
    if (-not (Test-Path -LiteralPath $logParent)) {
        New-Item -ItemType Directory -Path $logParent -Force | Out-Null
    }
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $entry = "[$ts] install-rkoj-shortcuts.ps1 :: Shortcuts installed: 4 (Desktop x2, Start Menu x2) :: created=$created skipped=$skipped failed=$failed pin=$pinResult"
    Add-Content -LiteralPath $ProgressLog -Value $entry -Encoding utf8
    Write-Ok "Logged to $ProgressLog"
} catch {
    Write-Warn2 "Could not append to $ProgressLog : $($_.Exception.Message)"
}

# ---------------------------------------------------------------------------
# 6. Summary + exit code
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "===== install-rkoj-shortcuts summary =====" -ForegroundColor Magenta
Write-Host "  Created : $created"
Write-Host "  Skipped : $skipped"
Write-Host "  Failed  : $failed"
Write-Host "  Pin     : $pinResult"
Write-Host "=========================================="

if ($failed -gt 0) { exit 2 }
exit 0
