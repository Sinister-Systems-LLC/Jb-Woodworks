@echo off
REM Sinister Forge :: Desktop launcher (v3 :: 2026-05-21)
REM Author: RKOJ-ELENO
REM
REM v3 fix: delegate install to automations\install-sinister-forge.ps1 (v2
REM with orphan ~* sweep + Start-Process isolation so PS 5.1 doesn't wrap
REM pip stderr warnings as NativeCommandError).

TITLE Sinister Forge :: operator console
setlocal enableextensions

if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Forge" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum
goto :ensure_install

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\projects\sinister-forge\source\pyproject.toml" set "SANCTUM_ROOT=%~1"
exit /b 0

:no_sanctum
echo  [FAIL] Sinister Sanctum repo not found.
pause
exit /b 1

:ensure_install
python -c "import forge" 2>nul
if not errorlevel 1 goto :launch

echo.
echo  [install] First-run setup - installing forge Python package...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\install-sinister-forge.ps1" -SanctumRoot "%SANCTUM_ROOT%"
if errorlevel 1 (
    echo  [FAIL] Forge install failed. See output above.
    pause
    exit /b 1
)

:launch
echo  Launching Sinister Forge...
python -m forge
exit /b %ERRORLEVEL%
