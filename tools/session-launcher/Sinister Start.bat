@echo off
REM Sinister Start :: direct Sanctum session boot (v2 :: 2026-05-21)
REM Author: RKOJ-ELENO
REM
REM Operator 2026-05-21: skip the menu, just boot the SANCTUM CORE animation.
REM No 1/2/3/4/5 picker — double-click goes straight to start-sinister-session.ps1
REM which renders the Sinister Sanctum operator-console boot.

TITLE Sinister Sanctum :: Session Online
setlocal enableextensions

REM Prefer Windows Terminal (frameless-ish + better Unicode) if available + not already inside one.
if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Sanctum" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum

REM Direct boot — no menu.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
exit /b %ERRORLEVEL%

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0

:no_sanctum
echo  [FAIL] Sinister Sanctum repo not found.
echo  Set SINISTER_SANCTUM_ROOT env var or place repo at D:\Sinister Sanctum
pause
exit /b 1
