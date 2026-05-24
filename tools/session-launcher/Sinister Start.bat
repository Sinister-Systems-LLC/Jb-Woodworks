@echo off
REM Sinister Start :: thin shim - hands off to EVE.exe
REM Author: RKOJ-ELENO :: 2026-05-24 (v7 - all logic absorbed into eve.py)
TITLE EVE :: Sinister Sanctum
setlocal
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT (
    echo  [FAIL] Sinister Sanctum repo not found. Set SINISTER_SANCTUM_ROOT.
    pause
    exit /b 1
)
set "EVE_EXE=%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE\EVE.exe"
if exist "%EVE_EXE%" (
    pushd "%SANCTUM_ROOT%"
    start "" "%EVE_EXE%" %*
    popd
    exit /b 0
)
pushd "%SANCTUM_ROOT%"
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
popd
exit /b 0

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0
