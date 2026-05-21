@echo off
REM Sinister Mind :: Desktop launcher (v2 :: 2026-05-21)
REM Author: RKOJ-ELENO
REM
REM v2 fix: delegate install to automations\install-sinister-mind.ps1 so the
REM stderr WARNING-noise from pip doesn't trip PS 5.1's NativeCommandError.

TITLE Sinister Mind :: visual brain
setlocal enableextensions

if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Mind" cmd.exe /K "\"%~f0\" %*"
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
if exist "%~1\projects\sinister-mind\source\pyproject.toml" set "SANCTUM_ROOT=%~1"
exit /b 0

:no_sanctum
echo  [FAIL] Sinister Sanctum repo not found.
pause
exit /b 1

:ensure_install
python -c "import mind" 2>nul
if not errorlevel 1 goto :launch

echo.
echo  [install] First-run setup - installing mind Python package...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\install-sinister-mind.ps1" -SanctumRoot "%SANCTUM_ROOT%"
if errorlevel 1 (
    echo  [FAIL] mind install failed. See output above.
    pause
    exit /b 1
)

:launch
echo  Launching Sinister Mind on http://127.0.0.1:5079/ ...
python -m mind
exit /b %ERRORLEVEL%
