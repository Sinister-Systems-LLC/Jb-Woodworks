# Sinister Forge :: installer (v2)
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Idempotent installer. v2 fixes two operator-observed bugs:
#   (1) PowerShell 5.1's `2>&1` on native exes wraps stderr WARNINGs as
#       NativeCommandError - false alarm even when pip exit code is 0.
#       Fix: drop the `2>&1`, capture exit code directly.
#   (2) Leftover `~rida-tools*` (orphan pip-uninstall remnants) in
#       site-packages pollutes every install with WARNING noise.
#       Fix: pre-install sweep removes any `~*` dist dirs.

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

# Find a Python 3.10+ on PATH
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

# Sweep orphan ~* dist dirs (left behind by aborted pip uninstalls)
try {
    $sitePackages = & $pythonCmd -c "import sysconfig; print(sysconfig.get_paths()['purelib'])" 2>$null
    if ($sitePackages -and (Test-Path $sitePackages)) {
        $orphans = Get-ChildItem -Path $sitePackages -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '~*' }
        foreach ($o in $orphans) {
            if (-not $Quiet) { Write-Host "[install-forge] cleanup orphan: $($o.Name)" -ForegroundColor DarkGray }
            Remove-Item -Path $o.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
} catch { }

# Already installed?
$alreadyInstalled = $false
try {
    $check = & $pythonCmd -c "import forge; print(forge.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $check) {
        $alreadyInstalled = $true
        if (-not $Quiet) { Write-Host "[install-forge] forge already importable (v$check)" -ForegroundColor Green }
    }
} catch { }

if ($alreadyInstalled -and -not $Force) {
    exit 0
}

if (-not $Quiet) { Write-Host "[install-forge] pip install -e $forgeSrc" -ForegroundColor Cyan }

# v2 fix: do NOT use `2>&1`. PS 5.1 wraps stderr as NativeCommandError which
# trips on harmless pip WARNINGs. Capture stdout+stderr to a tempfile, check
# $LASTEXITCODE directly. ErrorActionPreference=Continue so stderr lines don't
# kill the script.
$ErrorActionPreference = 'Continue'

Push-Location $forgeSrc
try {
    # Upgrade pip quietly (ignore warnings)
    & $pythonCmd -m pip install --quiet --disable-pip-version-check --upgrade pip *>$null

    # The actual install. Use Start-Process to fully isolate stderr from
    # PowerShell's error pipeline.
    $logFile = Join-Path $env:TEMP "forge-install-$(Get-Date -Format 'yyyyMMddHHmmss').log"
    $proc = Start-Process -FilePath $pythonCmd `
        -ArgumentList @('-m', 'pip', 'install', '--disable-pip-version-check', '-e', '.') `
        -WorkingDirectory $forgeSrc `
        -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError "$logFile.err"
    $code = $proc.ExitCode
    Pop-Location

    if ($code -ne 0) {
        if (-not $Quiet) {
            Write-Host "[install-forge] FAIL: pip install returned $code" -ForegroundColor Red
            Write-Host "       stderr tail:" -ForegroundColor Yellow
            if (Test-Path "$logFile.err") { Get-Content "$logFile.err" | Select-Object -Last 20 | ForEach-Object { Write-Host "       $_" -ForegroundColor DarkGray } }
        }
        exit $code
    }
} catch {
    Pop-Location
    if (-not $Quiet) { Write-Host "[install-forge] FAIL: $($_.Exception.Message)" -ForegroundColor Red }
    exit 1
}

# Verify import works post-install
try {
    $v = & $pythonCmd -c "import forge; print(forge.__version__)" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $v) {
        if (-not $Quiet) { Write-Host "[install-forge] FAIL: forge installed but not importable" -ForegroundColor Red }
        exit 1
    }
    if (-not $Quiet) { Write-Host "[install-forge] OK - forge v$v installed" -ForegroundColor Green }
} catch {
    if (-not $Quiet) { Write-Host "[install-forge] WARN: import verification skipped" -ForegroundColor Yellow }
}

exit 0
