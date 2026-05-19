# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# Fix-RKOJ-Login.ps1 :: one-click recovery when `_vault/auth-keys.json` gets corrupted/truncated.
#
# Trigger: operator hits "can't login" / sees AUTHENTICATING spinner / sees a 0-byte
# `auth-keys.json`. The auth module is set up to auto-regenerate keys when the file is
# missing/empty, but the Claude agent's sandbox blocks bot writes to `_vault/` so the
# operator runs this themselves.
#
# What this does:
#   1. Verify the window-manager venv exists (we need its python to import auth.py)
#   2. Show the current state of auth-keys.json (size + mtime)
#   3. Call auth._ensure_keys_file() via the venv python -- this:
#        - reads auth-keys.json
#        - if empty or invalid JSON, generates fresh operator + leo keys
#        - writes new auth-keys.json + refreshes auth-keys-DELIVER-TO-LEO.txt
#   4. Show the regenerated state
#   5. Open notepad on auth-keys-DELIVER-TO-LEO.txt so the operator can copy the new keys
#   6. (Optional) Launch RKOJ if not already running
#
# Usage:
#   Double-click `C:\Users\Zonia\Desktop\Fix-RKOJ-Login.bat` (the Desktop entry)
#   OR: powershell -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\fix-rkoj-login.ps1"
#
# UTF-8 with BOM. No em-dashes. Sanctum purple theme.

[CmdletBinding()]
param(
    [switch]$NoNotepad,         # skip the notepad open at the end
    [switch]$NoLaunch,          # skip the optional RKOJ relaunch
    [switch]$Force              # regenerate even if file already looks healthy
)

$ErrorActionPreference = 'Continue'

function Write-Step($text, [ConsoleColor]$color = 'Magenta') {
    Write-Host "  [*] $text" -ForegroundColor $color
}
function Write-OK($text) {
    Write-Host "  [OK] $text" -ForegroundColor Green
}
function Write-Fail($text) {
    Write-Host "  [FAIL] $text" -ForegroundColor Red
}
function Write-Warn($text) {
    Write-Host "  [WARN] $text" -ForegroundColor Yellow
}
function Write-Sep {
    Write-Host ('-' * 60) -ForegroundColor DarkMagenta
}

$WmDir = 'D:\Sinister Sanctum\automations\window-manager'
$VenvPy = Join-Path $WmDir '.venv\Scripts\python.exe'
$VaultDir = 'D:\Sinister Sanctum\_vault'
$KeysFile = Join-Path $VaultDir 'auth-keys.json'
$DeliverFile = Join-Path $VaultDir 'auth-keys-DELIVER-TO-LEO.txt'
$RkojBat = 'C:\Users\Zonia\Desktop\RKOJ.bat'

Clear-Host
Write-Host ''
Write-Host '====================================================' -ForegroundColor DarkMagenta
Write-Host '  RKOJ :: Login Recovery' -ForegroundColor Magenta
Write-Host '  Sinister Sanctum :: auth-keys.json regenerator' -ForegroundColor DarkMagenta
Write-Host '====================================================' -ForegroundColor DarkMagenta
Write-Host ''

# 1. Prereqs
Write-Step 'Checking prerequisites...'

if (-not (Test-Path -LiteralPath $VenvPy)) {
    Write-Fail "window-manager venv python not found at $VenvPy"
    Write-Host '       Run Build-Sanctum-Console.bat (or RKOJ rebuild) first to create the venv.' -ForegroundColor Gray
    Read-Host 'Press Enter to exit'
    exit 1
}
Write-OK "venv python: $VenvPy"

if (-not (Test-Path -LiteralPath $VaultDir)) {
    Write-Step 'Creating _vault/ directory (did not exist).'
    New-Item -ItemType Directory -Path $VaultDir -Force | Out-Null
}
Write-OK "vault dir: $VaultDir"

# 2. Show current state
Write-Host ''
Write-Step 'Current auth-keys.json state:'
if (Test-Path -LiteralPath $KeysFile) {
    $info = Get-Item -LiteralPath $KeysFile
    $sizeKb = [Math]::Round($info.Length / 1024, 2)
    Write-Host "       file: $($info.FullName)" -ForegroundColor Gray
    Write-Host "       size: $($info.Length) bytes ($sizeKb KB)" -ForegroundColor Gray
    Write-Host "       mtime: $($info.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    if ($info.Length -eq 0) {
        Write-Warn '0 bytes -- CORRUPTED. Regen needed.'
        $needRegen = $true
    } elseif ($info.Length -lt 80) {
        Write-Warn 'suspiciously small -- regen recommended.'
        $needRegen = $true
    } else {
        Write-OK 'looks healthy.'
        $needRegen = $false
    }
} else {
    Write-Warn 'auth-keys.json does not exist.'
    $needRegen = $true
}

if (-not $needRegen -and -not $Force) {
    Write-Host ''
    Write-Host '  Looks OK already. Use -Force to regenerate anyway.' -ForegroundColor Yellow
    Write-Host ''
    if (-not $NoNotepad) {
        Write-Step 'Opening deliver-to-leo file for reference...'
        if (Test-Path -LiteralPath $DeliverFile) {
            Start-Process notepad.exe -ArgumentList $DeliverFile
        }
    }
    Read-Host 'Press Enter to exit'
    exit 0
}

# 3. Regenerate
Write-Host ''
Write-Step 'Calling auth._ensure_keys_file() via regen-auth-keys.py...' Cyan
$RegenPy = 'D:\Sinister Sanctum\automations\regen-auth-keys.py'
if (-not (Test-Path -LiteralPath $RegenPy)) {
    Write-Fail "regen-auth-keys.py not found at $RegenPy"
    Read-Host 'Press Enter to exit'
    exit 2
}
Push-Location -LiteralPath $WmDir
try {
    # Use a permanent .py file instead of inline -c to dodge PowerShell 5.1's
    # native-command double-quote mangling. See knowledge entry
    # rkoj-cmd-spawn-loop-diagnosis.md for the broader cmd/powershell quirks.
    $output = & $VenvPy $RegenPy 2>&1
    foreach ($line in $output) {
        Write-Host "       $line" -ForegroundColor White
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "regen failed with exit code $LASTEXITCODE"
        Read-Host 'Press Enter to exit'
        exit 2
    }
} finally {
    Pop-Location
}

# 4. Verify new state
Write-Host ''
Write-Step 'Verifying new state...'
if (Test-Path -LiteralPath $KeysFile) {
    $info = Get-Item -LiteralPath $KeysFile
    Write-OK "auth-keys.json: $($info.Length) bytes, mtime $($info.LastWriteTime.ToString('HH:mm:ss'))"
} else {
    Write-Fail 'auth-keys.json still missing after regen?'
    Read-Host 'Press Enter to exit'
    exit 3
}
if (Test-Path -LiteralPath $DeliverFile) {
    $info2 = Get-Item -LiteralPath $DeliverFile
    Write-OK "deliver-to-leo: $($info2.Length) bytes, mtime $($info2.LastWriteTime.ToString('HH:mm:ss'))"
}

# 5. Open notepad on deliver-to-leo (operator copies OPERATOR KEY from there)
if (-not $NoNotepad) {
    Write-Host ''
    Write-Step 'Opening deliver-to-leo.txt for you to copy the OPERATOR key...'
    Start-Process notepad.exe -ArgumentList $DeliverFile
    Start-Sleep -Milliseconds 400
}

# 6. Optional: launch RKOJ if not running
$rkojRunning = (Get-Process -Name 'RKOJ' -ErrorAction SilentlyContinue) -ne $null
if (-not $NoLaunch -and -not $rkojRunning) {
    if (Test-Path -LiteralPath $RkojBat) {
        Write-Host ''
        Write-Step 'RKOJ is not running -- launching Desktop\RKOJ.bat...'
        Start-Process -FilePath $RkojBat -WorkingDirectory (Split-Path $RkojBat)
    }
}

# 7. Final state report
Write-Host ''
Write-Sep
Write-Host '  RECOVERY COMPLETE' -ForegroundColor Green
Write-Sep
Write-Host ''
Write-Host '  Next steps:' -ForegroundColor Magenta
Write-Host '    1. Copy the OPERATOR KEY from the notepad window that just opened' -ForegroundColor White
Write-Host '    2. The RKOJ login page should appear within ~6 seconds' -ForegroundColor White
Write-Host '    3. Paste the OPERATOR KEY into the password field + UNLOCK' -ForegroundColor White
Write-Host '    4. The key will HWID-bind to this machine on first use' -ForegroundColor White
Write-Host ''
Write-Host '  If login still fails:' -ForegroundColor DarkGray
Write-Host '    - Re-run this script with -Force' -ForegroundColor DarkGray
Write-Host '    - Check D:\Sinister Sanctum\_vault\auth-keys.json size is > 200 bytes' -ForegroundColor DarkGray
Write-Host '    - Brain entry: D:\Sinister Sanctum\_shared-memory\knowledge\rkoj-cmd-spawn-loop-diagnosis.md' -ForegroundColor DarkGray
Write-Host ''

Read-Host 'Press Enter to close this window'
exit 0
