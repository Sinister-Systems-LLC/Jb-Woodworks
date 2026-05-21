@echo off
REM Sinister Forge :: project launcher (v1 :: 2026-05-21)
REM
REM ONE-CLICK entry into the Sinister Forge project — our Sinister-branded
REM multi-LLM coding-agent harness that mines jcode's best features + pairs
REM them with the full Sanctum stack (6 session contracts + 12 bots + Ruflo
REM + Vault + RKOJ + auto-backup + multi-operator partition).
REM
REM Calls the SAME launcher PS1 the Sanctum bat uses (one source of truth)
REM with -Project sinister-forge -Mode forge pre-set. Operator still picks
REM token mode + speed + agent host + agent name + accent + focus inside the
REM picker.
REM
REM Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

TITLE Sinister Forge :: Project Launcher
setlocal enableextensions

if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Forge" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

REM Find Sanctum (same pattern as the other bats)
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
echo   Sinister Forge :: Sanctum not found
echo  ==============================================================
echo.
echo  Forge needs Sanctum installed (the launcher PS1 lives there).
echo  Where is your Sinister Sanctum clone? (Enter to abort)
echo.
set /p "SANCTUM_ROOT=  Sanctum path: "

if not defined SANCTUM_ROOT (
    echo  [ABORT] No Sanctum path.
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

REM Forge mode pre-populates project + mode; operator still answers
REM Token Mode / Speed / Agent Host / Agent name / Accent inside the picker.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Project sinister-forge -Mode forge %*

:done
endlocal
exit /b %ERRORLEVEL%
