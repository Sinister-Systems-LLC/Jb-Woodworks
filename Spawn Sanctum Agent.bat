@echo off
REM Spawn Sanctum Agent :: canonical sanctum spawn entry-point (mirrors "Sinister Start.bat" launcher chain)
REM Author: RKOJ-ELENO :: 2026-05-25
REM
REM Created to fix the broken Desktop shim "C:\Users\Zonia\Desktop\Spawn Sanctum Agent.bat"
REM (operator screenshot 2026-05-25T~13:14Z: "fix this fucking now and stop it from breaking").
REM
REM Same launcher chain as "Sinister Start.bat":
REM   1. Try EVE.exe stable copy (%USERPROFILE%\.eve\EVE.exe).
REM   2. Try EVE.exe dist build (automations\eve-launcher\dist\EVE\EVE.exe).
REM   3. Fall back to PS1 launcher (automations\start-sinister-session.ps1).
REM
REM "Spawn Sanctum Agent" semantics: passes -Project sanctum so the picker
REM skips the project list and goes straight to the agent prefs page.
REM Operator can still pick a different project from inside EVE.exe.
REM
REM Per operator hard-canonical 2026-05-25 (no-bat-no-ps1-doctrine):
REM   "Existing .bat files in the main dir = legacy entry points; this one
REM    fixes a broken canonical that the desktop shim depends on, NOT a new
REM    operator-clicked surface."
REM
REM Per operator hard-canonical 2026-05-24 (session-start-auto-update-propagation):
REM   Any EVE.exe / PS1 launcher update auto-propagates here -- this file only
REM   handles env-var + path resolution; the real work is downstream.

TITLE EVE :: Spawn Sanctum Agent
mode con: cols=220 lines=65 >nul 2>&1
setlocal enableextensions

set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT (
    color 4F
    echo.
    echo  [FAIL] Sinister Sanctum repo not found.
    echo         Tried: %%SINISTER_SANCTUM_ROOT%% / D:\Sinister Sanctum
    echo                C:\Sinister Sanctum / %%USERPROFILE%%\Sinister Sanctum
    echo         Fix: set the SINISTER_SANCTUM_ROOT env var or place repo at D:\Sinister Sanctum
    echo.
    pause
    exit /b 1
)

set "EVE_EXE_STABLE=%USERPROFILE%\.eve\EVE.exe"
set "EVE_EXE_DIST=%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE\EVE.exe"
set "EVE_EXE="
if exist "%EVE_EXE_STABLE%" set "EVE_EXE=%EVE_EXE_STABLE%"
if not defined EVE_EXE if exist "%EVE_EXE_DIST%" set "EVE_EXE=%EVE_EXE_DIST%"
set "PS1_LAUNCHER=%SANCTUM_ROOT%\automations\start-sinister-session.ps1"

pushd "%SANCTUM_ROOT%"

REM Operator hard-canonical 2026-05-25T21:46Z (utterance): *"this needs to
REM just launch the sinsiter sanctum agetn"* -- skip the picker and go
REM straight to the sanctum lane. Forward any additional args verbatim
REM so operator can still tweak modes/loop/swarm if needed.
if defined EVE_EXE (
    "%EVE_EXE%" -Project sanctum %*
    set "_RC=%ERRORLEVEL%"
) else if exist "%PS1_LAUNCHER%" (
    echo  [info] EVE.exe missing at %EVE_EXE_STABLE%
    echo  [info] Falling back to PowerShell launcher (sanctum project)...
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1_LAUNCHER%" -Project sanctum %*
    set "_RC=%ERRORLEVEL%"
) else (
    color 4F
    echo.
    echo  [FAIL] Neither EVE.exe nor start-sinister-session.ps1 found.
    echo         EVE.exe stable: %EVE_EXE_STABLE%
    echo         EVE.exe dist:   %EVE_EXE_DIST%
    echo         PS1:            %PS1_LAUNCHER%
    echo         Fix: cd %SANCTUM_ROOT%\automations\eve-launcher ^&^& build-eve-exe.bat
    echo.
    pause
    popd
    exit /b 2
)

popd
if "%~1"=="" (
    if not "%_RC%"=="0" (
        echo.
        echo  [info] EVE.exe exited with code %_RC%
        pause
    )
)
exit /b %_RC%

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0
