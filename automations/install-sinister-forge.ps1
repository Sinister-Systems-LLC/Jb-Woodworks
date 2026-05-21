# Sinister Forge :: installer
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Idempotent installer. Verifies Python 3.10+, pip-installs the forge
# package in editable mode from projects/sinister-forge/source/. Called
# automatically by `Sinister Forge.bat` on Desktop if the forge command
# is not on PATH.

param(
    [string]$SanctumRoot = '',
    [switch]$Force,
    [switch]$Quiet
)

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}

$forgeSrc = Join-Path $SanctumRoot 'projects\sinister-forge\source'
if (-not (Test-Path (Join-Path $forgeSrc 'pyproject.toml'))) {
    if (-not $Quiet) { Write-Host "[install-forge] FAIL: $forgeSrc\pyproject.toml not found" -ForegroundColor Red }
    exit 1
}

$pythonCmd = $null
foreach ($cmd in @('python', 'py', 'python3')) {
    try {
        $v = & $cmd --version 2>$null
        if ($v -match 'Python 3\.(1[0-9]|[2-9][0-9])') {
            $pythonCmd = $cmd
            break
        }
    } catch { }
}

if (-not $pythonCmd) {
    if (-not $Quiet) {
        Write-Host "[install-forge] FAIL: Python 3.10+ not found on PATH." -ForegroundColor Red
        Write-Host "       Install Python 3.11+ from https://www.python.org/downloads/ then re-run." -ForegroundColor Yellow
    }
    exit 1
}

if (-not $Quiet) { Write-Host "[install-forge] using $pythonCmd" -ForegroundColor Cyan }

# Already installed?
$alreadyInstalled = $false
try {
    $check = & $pythonCmd -c "import forge; print(forge.__version__)" 2>$null
    if ($check) { $alreadyInstalled = $true; if (-not $Quiet) { Write-Host "[install-forge] forge already importable (v$check)" -ForegroundColor Green } }
} catch { }

if ($alreadyInstalled -and -not $Force) {
    exit 0
}

if (-not $Quiet) { Write-Host "[install-forge] pip install -e $forgeSrc" -ForegroundColor Cyan }

Push-Location $forgeSrc
try {
    & $pythonCmd -m pip install --quiet --upgrade pip 2>&1 | Out-Null
    & $pythonCmd -m pip install --quiet -e . 2>&1
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) {
        if (-not $Quiet) { Write-Host "[install-forge] FAIL: pip install returned $code" -ForegroundColor Red }
        exit $code
    }
} catch {
    Pop-Location
    if (-not $Quiet) { Write-Host "[install-forge] FAIL: $($_.Exception.Message)" -ForegroundColor Red }
    exit 1
}

if (-not $Quiet) { Write-Host "[install-forge] OK - forge command available" -ForegroundColor Green }
exit 0
