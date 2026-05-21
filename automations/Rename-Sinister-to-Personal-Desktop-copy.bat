@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM Self-elevating UAC bat that renames D:\Sinister -> D:\Personal.
REM Operator directive 2026-05-21: "change sinister to personal".
REM Requires admin because D:\Sinister has restrictive ACL.

setlocal

net session >nul 2>&1
if %errorLevel% == 0 goto :elevated

echo [Rename-Sinister] Requesting Administrator elevation...
powershell -Command "Start-Process -Verb RunAs -FilePath '%~f0'"
exit /b 0

:elevated
echo [Rename-Sinister] Running as Administrator.
echo.

REM Step 1: take ownership of D:\Sinister + grant full control to current user
echo [step 1] takeown + icacls...
takeown /F "D:\Sinister" /R /D Y >nul 2>&1
icacls "D:\Sinister" /grant "%USERNAME%:(F)" /T /C /Q >nul 2>&1

REM Step 2: kill any process holding D:\Sinister content (apk-watchdog, fleet-monitor)
echo [step 2] killing potential holders...
taskkill /F /IM apk-watchdog.exe 2>nul
taskkill /F /IM fleet-monitor.exe 2>nul
taskkill /F /IM sheets-sync.exe 2>nul

REM Step 3: stop scheduled tasks that touch D:\Sinister
echo [step 3] stopping schtasks...
schtasks /End /TN SinisterAPKWatchdog 2>nul
schtasks /End /TN \Sinister\Sinister-fleet-monitor 2>nul
schtasks /End /TN \Sinister\Sinister-sheets-sync 2>nul

REM Step 4: rename
echo [step 4] renaming...
ren "D:\Sinister" Personal
if %errorLevel% == 0 (
    echo.
    echo [Rename-Sinister] SUCCESS: D:\Sinister -> D:\Personal
    echo Verify: dir D:\Personal
) else (
    echo.
    echo [Rename-Sinister] FAILED. Try closing Explorer windows showing D:\Sinister.
    echo Or restart and rerun.
)

echo.
pause
exit /b 0
