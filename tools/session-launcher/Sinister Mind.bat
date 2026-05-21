@echo off
REM Sinister Mind :: Desktop launcher (v1 :: 2026-05-21)
REM Author: RKOJ-ELENO
REM
REM One-click entry into the Sinister Mind visual mind-graph. Auto-installs
REM the Flask package on first run; subsequent runs are instant. Opens
REM http://127.0.0.1:5079/ in the default browser.

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
echo  [FAIL] Sinister Sanctum repo not found. Clone it first:
echo    git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"
pause
exit /b 1

:ensure_install
python -c "import mind" 2>nul
if not errorlevel 1 goto :launch

echo.
echo  [install] First-run setup - installing mind Python package...
pushd "%SANCTUM_ROOT%\projects\sinister-mind\source"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -e .
set "INSTALL_CODE=%ERRORLEVEL%"
popd
if not "%INSTALL_CODE%"=="0" (
    echo  [FAIL] mind install failed. Install Python 3.10+ if missing.
    pause
    exit /b 1
)

:launch
echo  Launching Sinister Mind on http://127.0.0.1:5079/ ...
python -m mind
exit /b %ERRORLEVEL%
