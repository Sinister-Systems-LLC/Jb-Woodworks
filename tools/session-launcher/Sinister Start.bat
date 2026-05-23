@echo off
REM Sinister Start :: direct Sanctum session boot (v5 :: 2026-05-23 — RKOJ-ELENO)
REM
REM v5 changes (operator 2026-05-23 — "bat file closes when i open it"):
REM   - REMOVED wt.exe redirect (was silently failing on some WT installs ->
REM     bat appeared to close instantly with no diagnostic). Operator can
REM     still launch from inside Windows Terminal manually; bat now always
REM     runs in whatever cmd window opened it.
REM   - ADDED step-by-step echoes so operator sees what's running.
REM   - ADDED pause at end of main path so any error stays visible.
REM   - Set SINISTER_USE_WT=1 in env to re-enable the wt.exe redirect.
REM
REM v4 (2026-05-23): EVE.exe probe + PS1 fallback.
REM v3 (2026-05-23 evening): First-run autonomy bootstrap via marker file.
REM v2 (2026-05-21): direct boot, no menu.
REM v1 (pre-2026-05-21): 1/2/3/4/5 picker — removed per operator ask.

TITLE Sinister Sanctum :: Session Online
setlocal enableextensions

REM ----- Explicit autonomy re-setup flag -----
if /I "%~1"=="--setup-autonomy" goto :run_autonomy
if /I "%~1"=="-setup-autonomy"  goto :run_autonomy
if /I "%~1"=="/setup-autonomy"  goto :run_autonomy

REM ----- Optional wt.exe redirect (off by default after v4 silent-close bug) -----
if defined SINISTER_USE_WT (
    if not defined WT_SESSION (
        where wt.exe >nul 2>&1
        if not errorlevel 1 (
            start "" wt.exe new-tab --title "Sinister Sanctum" cmd.exe /K "\"%~f0\" %*"
            exit /b 0
        )
    )
)

echo  [start] Sinister Sanctum session launcher v5
echo  [start] locating Sanctum root...
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum
echo  [ok]    Sanctum root: %SANCTUM_ROOT%

REM ----- First-run autonomy bootstrap (silent skip if marker present) -----
if not exist "%USERPROFILE%\.sanctum-autonomy-granted" (
    echo.
    echo  ====================================================================
    echo   Sinister Sanctum :: First-run autonomy bootstrap
    echo  ====================================================================
    echo   No %%USERPROFILE%%\.sanctum-autonomy-granted marker found.
    echo   Running Grant-Claude-Autonomy.ps1 once before launching the session.
    echo   Re-run any time:  Sinister Start.bat --setup-autonomy
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\grant-claude-autonomy.ps1"
    echo.
)

REM ----- Required plugin check (operator directive 2026-05-23) -----
REM Read-only diff vs required-plugins.json manifest. Prints warnings for missing
REM required plugins; does NOT auto-install (operator approves per 2026-05-19 plugin
REM discipline). Re-run with auto-install:  check-required-plugins.ps1 -AutoInstall
if exist "%SANCTUM_ROOT%\automations\check-required-plugins.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\check-required-plugins.ps1"
)

REM ----- Prefer EVE.exe (thin jcode-speed picker) if available -----
set "EVE_EXE="
if exist "%~dp0EVE.exe" set "EVE_EXE=%~dp0EVE.exe"
if not defined EVE_EXE if exist "%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe" set "EVE_EXE=%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe"
if not defined EVE_EXE if exist "%LOCALAPPDATA%\Sinister\EVE.exe" set "EVE_EXE=%LOCALAPPDATA%\Sinister\EVE.exe"

if defined EVE_EXE (
    echo  [ok]    launching EVE.exe: %EVE_EXE%
    "%EVE_EXE%"
    set "LAUNCH_RC=%ERRORLEVEL%"
    echo.
    echo  [done]  EVE.exe exited with code %LAUNCH_RC%
    pause
    exit /b %LAUNCH_RC%
)

REM ----- Fallback: PS1 launcher (no regression if EVE.exe not built yet) -----
echo  [ok]    EVE.exe not built; launching PS1 picker
echo  [hint]  build EVE.exe: %SANCTUM_ROOT%\automations\eve-launcher\build-eve-exe.bat
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
set "LAUNCH_RC=%ERRORLEVEL%"
echo.
echo  [done]  PS1 launcher exited with code %LAUNCH_RC%
if not "%LAUNCH_RC%"=="0" (
    echo  [warn]  non-zero exit; pausing so you can read the error above.
    pause
)
exit /b %LAUNCH_RC%

:run_autonomy
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum
echo.
echo  ====================================================================
echo   Sinister Sanctum :: Explicit autonomy re-setup (--setup-autonomy)
echo  ====================================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\grant-claude-autonomy.ps1"
echo.
echo  ----------------------------------------------------------------------
echo   Autonomy setup complete. Run Sinister Start.bat (no flags) to boot.
echo  ----------------------------------------------------------------------
pause
exit /b 0

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0

:no_sanctum
echo  [FAIL] Sinister Sanctum repo not found.
echo  Set SINISTER_SANCTUM_ROOT env var or place repo at D:\Sinister Sanctum
pause
exit /b 1
