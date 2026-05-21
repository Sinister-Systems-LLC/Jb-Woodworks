@echo off
REM Sinister Personal :: project launcher (v5 :: simplified, parse-safe)
REM
REM PERSONAL launcher for projects living OUTSIDE Sinister Sanctum
REM (LetsText, JOKR-Global, eve-mcp, Car, Drone, Cell-Network, RKOJ-personal).
REM The launcher PS1 + personal-projects.json DO live in Sanctum.
REM
REM Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

TITLE Sinister Personal :: Project Launcher
setlocal enableextensions

REM Auto-relaunch in Windows Terminal if available + not already there
if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Personal" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

REM STEP 1 - Find Sanctum (we use its launcher PS1)
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Desktop\Sinister Sanctum"

if not defined SANCTUM_ROOT goto :prompt_path
goto :handoff

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0

:prompt_path
echo.
echo  ==============================================================
echo   Sinister Personal :: Sanctum not found
echo  ==============================================================
echo.
echo  Personal projects (LetsText, JOKR-Global, eve-mcp, RKOJ-personal,
echo  Car, Drone, Cell-Network) live at their own roots on D:\, but
echo  this launcher needs the Sinister Sanctum repo for its picker PS1.
echo.
echo  Sanctum was not found at any canonical path. Where is it?
echo  Example: D:\Sinister Sanctum    (or press Enter to abort)
echo.
set /p "SANCTUM_ROOT=  Sanctum path: "

if not defined SANCTUM_ROOT (
    echo.
    echo  [ABORT] No Sanctum path given.
    echo.
    pause
    exit /b 1
)

if not exist "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" (
    echo  [FAIL] That path is not a Sanctum repo.
    pause
    exit /b 1
)

setx SINISTER_SANCTUM_ROOT "%SANCTUM_ROOT%" >nul
echo  [OK] Saved SINISTER_SANCTUM_ROOT for next launch.

:handoff
set "PS1=%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
set "EXTRA_ARGS=-ProjectsFile personal-projects.json -FocusFile personal-focus-suggestions.json"

if /i "%~1"=="resume" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS% -Resume
    goto :done
)
if /i "%~1"=="new" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS% -ForceWizard
    goto :done
)
if "%~1"=="" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS%
    goto :done
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS% %*

:done
endlocal
exit /b %ERRORLEVEL%
