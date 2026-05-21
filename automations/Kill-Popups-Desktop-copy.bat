@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM One-click killer for the last 2 PowerShell-popup scheduled tasks.
REM Self-elevates via UAC, then runs silence-task-popups-admin.ps1.

setlocal

REM Check if already elevated
net session >nul 2>&1
if %errorLevel% == 0 goto :elevated

REM Not elevated — relaunch self via PowerShell with -Verb RunAs (UAC prompt)
echo [Kill-Popups] Requesting Administrator elevation...
powershell -Command "Start-Process -Verb RunAs -FilePath '%~f0'"
exit /b 0

:elevated
echo [Kill-Popups] Running as Administrator.
echo.

set PS_SCRIPT=D:\Sinister Sanctum\automations\silence-task-popups-admin.ps1

if not exist "%PS_SCRIPT%" (
    echo ERROR: %PS_SCRIPT% not found.
    echo The Sanctum repo may be moved or this is a fresh machine.
    echo Look for silence-task-popups-admin.ps1 inside D:\Sinister Sanctum\automations\
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
echo.
echo [Kill-Popups] Done. Verify zero popups after the next 5-15 min cadence.
echo.
pause
exit /b 0
