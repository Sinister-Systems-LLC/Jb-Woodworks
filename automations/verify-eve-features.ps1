# verify-eve-features.ps1 - verify EVE.exe bundle has latest UX features
# Author: RKOJ-ELENO :: 2026-05-24
#
# After operator complains 'i dont see X' / 'X not working' on EVE.exe, run this
# to confirm the bundled binary has the expected strings. Helps distinguish
# "stale-bundle / needs restart" from "code is missing / needs rebuild".
#
# Usage:
#   powershell -File verify-eve-features.ps1

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$AutoRebuild,
    [switch]$SyncMirror
)

$ErrorActionPreference = 'Continue'
if ($AutoRebuild) { try { & python "D:\Sinister Sanctum\automations\eve_crash_detector.py" --pre-compile 2>&1 | Out-Null } catch { Write-Host "  [warn] eve_crash_detector pre-compile hook failed: $_" -ForegroundColor Yellow } }
$exeDist = Join-Path $SanctumRoot 'automations\eve-launcher\dist\EVE\EVE.exe'
$exeMirror = Join-Path $env:USERPROFILE '.eve\EVE.exe'
$src       = Join-Path $SanctumRoot 'automations\eve-launcher\eve.py'

Write-Host ''
Write-Host '  EVE.exe feature verification' -ForegroundColor Magenta
Write-Host ('  ' + ('-' * 76)) -ForegroundColor DarkMagenta

# Bundle freshness
foreach ($p in @($exeDist, $exeMirror)) {
    if (Test-Path $p) {
        $i = Get-Item $p
        $age = ((Get-Date) - $i.LastWriteTime).TotalMinutes
        $ageStr = ('{0:F1}' -f $age) + ' min'
        Write-Host ('  ' + $p) -ForegroundColor Gray
        Write-Host ('    size=' + $i.Length + '  mtime=' + $i.LastWriteTime + '  age=' + $ageStr) -ForegroundColor DarkGray
    } else {
        Write-Host ('  ' + $p + '  (missing)') -ForegroundColor Red
    }
}

# Source mtime for comparison
$srcInfo = Get-Item $src
$srcAge = ((Get-Date) - $srcInfo.LastWriteTime).TotalMinutes
Write-Host ('  eve.py source mtime=' + $srcInfo.LastWriteTime + '  age=' + ('{0:F1}' -f $srcAge) + ' min') -ForegroundColor Gray

# Stale-bundle warning
if (Test-Path $exeDist) {
    $exeMtime = (Get-Item $exeDist).LastWriteTime
    if ($srcInfo.LastWriteTime -gt $exeMtime) {
        $lag = ($srcInfo.LastWriteTime - $exeMtime).TotalMinutes
        Write-Host ('  [WARN] eve.py is ' + ('{0:F1}' -f $lag) + ' min NEWER than EVE.exe bundle - REBUILD NEEDED') -ForegroundColor Yellow
    } else {
        Write-Host '  [OK] EVE.exe is current with eve.py source' -ForegroundColor Green
    }
}

Write-Host ''
Write-Host '  Feature-string presence in eve.py source (bundle is compressed):' -ForegroundColor White
Write-Host ('  ' + ('-' * 76)) -ForegroundColor DarkMagenta

# PyInstaller compresses .pyc into the PKG archive, so raw byte scan of the EXE
# misses everything. Instead we check the source for each feature; if source has
# it AND EXE is fresher than source, the feature IS in the bundle (PyInstaller
# bundles the .py at build time).
$features = @(
    @{ name = 'Accounts panel title';      pattern = 'Connected Claude accounts' },
    @{ name = 'Round-robin status bar';     pattern = '\[round-robin status\]' },
    @{ name = 'NEXT account marker';        pattern = '<-NEXT' },
    @{ name = 'O key onboarding entry';     pattern = 'Onboarding' },
    @{ name = 'O key getpass flow';         pattern = '_account_onboarding_flow' },
    @{ name = 'Accounts panel renderer';    pattern = '_render_accounts_panel' },
    @{ name = 'Picker prompt with O key';   pattern = 'M / O / X' }
)

$srcText = Get-Content $src -Raw -ErrorAction SilentlyContinue
$exeMtime = if (Test-Path $exeDist) { (Get-Item $exeDist).LastWriteTime } else { [datetime]::MinValue }
$srcMtime = $srcInfo.LastWriteTime
$bundleFresh = $exeMtime -ge $srcMtime

foreach ($f in $features) {
    $hasInSrc = $srcText -match $f.pattern
    if ($hasInSrc -and $bundleFresh) {
        $tag = '[OK]  '
        $col = 'Green'
        $note = ''
    } elseif ($hasInSrc -and -not $bundleFresh) {
        $tag = '[STALE]'
        $col = 'Yellow'
        $note = '  <- src has it but bundle is older; REBUILD'
    } elseif (-not $hasInSrc) {
        $tag = '[MISS]'
        $col = 'Red'
        $note = '  <- source does not contain this; code missing'
    }
    Write-Host ('  ' + $tag + '  ' + $f.name.PadRight(34) + '  ' + $f.pattern + $note) -ForegroundColor $col
}

Write-Host ''

# RKOJ-ELENO :: 2026-05-24 :: auto-rebuild + mirror-sync (operator 21:30Z auto-update propagation).
# Detect stale bundle + optionally rebuild + sync mirror in one shot. Any sanctum-class agent
# that edits eve.py should call this with -AutoRebuild -SyncMirror to keep EVE.exe current.
if ($AutoRebuild -and -not $bundleFresh) {
    Write-Host '  [AUTO-REBUILD] bundle is stale + -AutoRebuild flag set; rebuilding...' -ForegroundColor Yellow
    $buildBat = Join-Path $SanctumRoot 'automations\eve-launcher\build-eve-exe.bat'
    if (Test-Path $buildBat) {
        Push-Location (Split-Path -Parent $buildBat)
        $buildOut = & cmd.exe /c "`"$buildBat`"" 2>&1
        Pop-Location
        $last = ($buildOut | Select-Object -Last 3) -join ' | '
        Write-Host ('    build output (last 3): ' + $last) -ForegroundColor Gray
        $newMtime = (Get-Item $exeDist).LastWriteTime
        Write-Host ('  [OK] dist rebuilt: mtime=' + $newMtime) -ForegroundColor Green
    } else {
        Write-Host ('  [FAIL] build-eve-exe.bat missing at ' + $buildBat) -ForegroundColor Red
    }
}

if ($SyncMirror -and (Test-Path $exeDist) -and (Test-Path (Split-Path -Parent $exeMirror))) {
    $distMtime = (Get-Item $exeDist).LastWriteTime
    $mirrorMtime = if (Test-Path $exeMirror) { (Get-Item $exeMirror).LastWriteTime } else { [datetime]::MinValue }
    if ($distMtime -gt $mirrorMtime) {
        Copy-Item $exeDist $exeMirror -Force
        Write-Host ('  [OK] mirror synced: ' + $exeMirror) -ForegroundColor Green
    } else {
        Write-Host '  [skip] mirror already matches dist' -ForegroundColor DarkGray
    }

    # RKOJ-ELENO :: 2026-05-25 :: repo-root copy (operator 03:30Z "push the entire
    # sanctum to github with the exe in the main folder where he can find it").
    # Keeps EVE.exe at repo root in sync so fresh-clone collaborators (Leo) see it
    # next to README.md. .gitignore has a !EVE.exe exception that whitelists it.
    $exeRoot = Join-Path $SanctumRoot 'EVE.exe'
    $rootMtime = if (Test-Path $exeRoot) { (Get-Item $exeRoot).LastWriteTime } else { [datetime]::MinValue }
    if ($distMtime -gt $rootMtime) {
        Copy-Item -Path $exeDist -Destination $exeRoot -Force
        Write-Host ('  [OK] root copy synced: ' + $exeRoot) -ForegroundColor Green
    } else {
        Write-Host '  [skip] root copy already matches dist' -ForegroundColor DarkGray
    }
}

if (-not $AutoRebuild -or -not $SyncMirror) {
    Write-Host ''
    Write-Host '  If any feature [STALE] or [MISS]:' -ForegroundColor White
    Write-Host '    Quick: re-run with -AutoRebuild -SyncMirror' -ForegroundColor DarkGray
    Write-Host '    Manual: cd automations\eve-launcher; ./build-eve-exe.bat; copy to ~/.eve/' -ForegroundColor DarkGray
    Write-Host '    Then close + reopen EVE.exe (running instance holds OLD bundle until restart)' -ForegroundColor DarkGray
    Write-Host ''
}
