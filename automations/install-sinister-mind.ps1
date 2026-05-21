# Sinister Mind :: installer
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Mirrors automations/install-sinister-forge.ps1 but for the Mind package.
# Same v2 fixes: no `2>&1`, orphan ~* sweep, Start-Process isolation.

param(
    [string]$SanctumRoot = '',
    [switch]$Force,
    [switch]$Quiet
)

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}

$mindSrc = Join-Path $SanctumRoot 'projects\sinister-mind\source'
if (-not (Test-Path (Join-Path $mindSrc 'pyproject.toml'))) {
    if (-not $Quiet) { Write-Host "[install-mind] FAIL: $mindSrc\pyproject.toml not found" -ForegroundColor Red }
    exit 1
}

$pythonCmd = $null
foreach ($cmd in @('python', 'py', 'python3')) {
    try {
        $v = & $cmd --version 2>$null
        if ($v -match 'Python 3\.(1[0-9]|[2-9][0-9])') { $pythonCmd = $cmd; break }
    } catch { }
}

if (-not $pythonCmd) {
    if (-not $Quiet) { Write-Host "[install-mind] FAIL: Python 3.10+ not found on PATH." -ForegroundColor Red }
    exit 1
}

if (-not $Quiet) { Write-Host "[install-mind] using $pythonCmd" -ForegroundColor Cyan }

# Sweep orphan ~* dist dirs
try {
    $sitePackages = & $pythonCmd -c "import sysconfig; print(sysconfig.get_paths()['purelib'])" 2>$null
    if ($sitePackages -and (Test-Path $sitePackages)) {
        $orphans = Get-ChildItem -Path $sitePackages -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '~*' }
        foreach ($o in $orphans) {
            if (-not $Quiet) { Write-Host "[install-mind] cleanup orphan: $($o.Name)" -ForegroundColor DarkGray }
            Remove-Item -Path $o.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
} catch { }

# Already installed?
$alreadyInstalled = $false
try {
    $check = & $pythonCmd -c "import mind; print(mind.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $check) {
        $alreadyInstalled = $true
        if (-not $Quiet) { Write-Host "[install-mind] mind already importable (v$check)" -ForegroundColor Green }
    }
} catch { }

if ($alreadyInstalled -and -not $Force) { exit 0 }

if (-not $Quiet) { Write-Host "[install-mind] pip install -e $mindSrc" -ForegroundColor Cyan }

$ErrorActionPreference = 'Continue'
& $pythonCmd -m pip install --quiet --disable-pip-version-check --upgrade pip *>$null

$logFile = Join-Path $env:TEMP "mind-install-$(Get-Date -Format 'yyyyMMddHHmmss').log"
$proc = Start-Process -FilePath $pythonCmd `
    -ArgumentList @('-m', 'pip', 'install', '--disable-pip-version-check', '-e', '.') `
    -WorkingDirectory $mindSrc `
    -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError "$logFile.err"
$code = $proc.ExitCode

if ($code -ne 0) {
    if (-not $Quiet) {
        Write-Host "[install-mind] FAIL: pip install returned $code" -ForegroundColor Red
        if (Test-Path "$logFile.err") { Get-Content "$logFile.err" | Select-Object -Last 20 | ForEach-Object { Write-Host "       $_" -ForegroundColor DarkGray } }
    }
    exit $code
}

try {
    $v = & $pythonCmd -c "import mind; print(mind.__version__)" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $v) {
        if (-not $Quiet) { Write-Host "[install-mind] FAIL: mind installed but not importable" -ForegroundColor Red }
        exit 1
    }
    if (-not $Quiet) { Write-Host "[install-mind] OK - mind v$v installed" -ForegroundColor Green }
} catch {
    if (-not $Quiet) { Write-Host "[install-mind] WARN: import verification skipped" -ForegroundColor Yellow }
}

exit 0
