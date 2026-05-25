@echo off
REM Sinister Start :: Sanctum entry point - hands off to EVE.exe
REM Author: RKOJ-ELENO :: 2026-05-24 (v8 - inline-run, no `start ""` so operator
REM sees the picker in the same window they opened. v7 used `start ""` which
REM looked like nothing happened from the operator's POV.)
TITLE EVE :: Sinister Sanctum
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

REM v9 (2026-05-24 evening): probe stable user-profile copy FIRST so the
REM launcher survives parallel-agent dist/EVE wipes during fleet rebuilds.
REM The stable copy is mirrored from dist/EVE/ by automations/eve-launcher
REM after each successful build (see make-icon.py + build-eve-exe.bat).
set "EVE_EXE_STABLE=%USERPROFILE%\.eve\EVE.exe"
set "EVE_EXE_DIST=%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE\EVE.exe"
set "EVE_EXE="
if exist "%EVE_EXE_STABLE%" set "EVE_EXE=%EVE_EXE_STABLE%"
if not defined EVE_EXE if exist "%EVE_EXE_DIST%" set "EVE_EXE=%EVE_EXE_DIST%"
set "PS1_LAUNCHER=%SANCTUM_ROOT%\automations\start-sinister-session.ps1"

pushd "%SANCTUM_ROOT%"

if defined EVE_EXE (
    REM v8: run EVE.exe inline (this same window) so operator sees the picker
    REM immediately. EVE.exe handles its own stdin/stdout in this console.
    "%EVE_EXE%" %*
    set "_RC=%ERRORLEVEL%"
) else if exist "%PS1_LAUNCHER%" (
    REM Fallback: PS1 launcher if EVE.exe is missing (not built / dist wiped).
    echo  [info] EVE.exe missing at %EVE_EXE%
    echo  [info] Falling back to PowerShell launcher...
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1_LAUNCHER%" %*
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
REM If EVE.exe / PS1 exited cleanly (operator quit), pause so the window doesn't
REM vanish before they can see any final output. Skip the pause when launched
REM with command-line args (suggests scripted invocation, not interactive).
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
