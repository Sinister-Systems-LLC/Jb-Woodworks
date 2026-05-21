@echo off
REM Sinister Forge :: Desktop launcher (v2 :: 2026-05-21)
REM Author: RKOJ-ELENO
REM
REM One-click entry into the Sinister Forge TUI. On first run, auto-installs
REM the Python package from projects\sinister-forge\source\ if not present.
REM Subsequent runs are instant.
REM
REM Forge spawns its own pickers + multi-pane scrolling buffers - it does
REM NOT use the launcher PS1 picker (that's the path for the per-project
REM bats). Forge IS the picker/manager.

TITLE Sinister Forge :: operator console
setlocal enableextensions

REM Auto-relaunch in Windows Terminal for the right typography
if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Forge" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

REM Find Sanctum
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
echo.
echo  ==============================================================
echo   Sinister Forge :: Sanctum not found on this PC
echo  ==============================================================
echo.
echo  Forge source lives at projects\sinister-forge\source\ inside the
echo  Sinister Sanctum repo. Clone it first:
echo.
echo    git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"
echo.
pause
exit /b 1

:ensure_install
REM Try to import forge; if fails, run the installer
python -c "import forge" 2>nul
if not errorlevel 1 goto :launch
echo.
echo  [install] First-run setup - installing forge Python package...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\install-sinister-forge.ps1" -SanctumRoot "%SANCTUM_ROOT%"
if errorlevel 1 (
    echo.
    echo  [FAIL] Forge install failed. See output above. Install Python 3.10+ if missing.
    pause
    exit /b 1
)

:launch
echo.
echo  Launching Sinister Forge...
echo.
python -m forge
exit /b %ERRORLEVEL%
