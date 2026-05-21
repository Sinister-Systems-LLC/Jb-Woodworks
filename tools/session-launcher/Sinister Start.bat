@echo off
REM Sinister Start :: unified Desktop entry  (v1 :: 2026-05-21)
REM Author: RKOJ-ELENO :: 2026-05-21
REM
REM One bat. Picks which surface to launch:
REM    1) Session   = Start-Sinister-Session.bat (per-project session via launcher PS1)
REM    2) Forge     = Sinister Forge.bat (multi-LLM TUI harness, all 11 projects)
REM    3) Mind      = Sinister Mind.bat (visual brain graph, http://127.0.0.1:5079/)
REM    4) Personal  = Personal Project start.bat (personal-fleet projects)
REM    5) RKOJ      = launch the RKOJ workbench EXE (http://127.0.0.1:5077/)
REM
REM 2026-05-21 patch (RKOJ-ELENO): if RKOJ.exe v0.7.0+ exists on Desktop,
REM prefer it as the default surface. Old picker still reachable with arg "menu".

TITLE Sinister Start :: unified launcher
setlocal enableextensions

REM ============================================================
REM STEP 0 -- Prefer RKOJ.exe v0.7.0+ if present (jcode-form parity).
REM           Unless arg 1 is "menu" (force-show picker), launch the EXE.
REM ============================================================
set "RKOJ_EXE=C:\Users\Zonia\Desktop\RKOJ.exe"
if exist "%RKOJ_EXE%" (
    if /i not "%~1"=="menu" (
        if not "%~1"=="" set "SINISTER_PROJECT=%~1"
        start "" "%RKOJ_EXE%"
        exit /b 0
    )
)

if not defined WT_SESSION (
    where wt.exe >nul 2>&1
    if not errorlevel 1 (
        start "" wt.exe new-tab --title "Sinister Start" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum
goto :pick

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0

:no_sanctum
echo  [FAIL] Sinister Sanctum repo not found.
pause
exit /b 1

:pick
cls
echo.
echo  ============================================================
echo    S I N I S T E R   S T A R T   ::   unified launcher
echo  ============================================================
echo.
echo    1) Session    Per-project Claude session  (launcher PS1)
echo    2) Forge      Multi-LLM TUI harness  (jcode-paired)
echo    3) Mind       Visual brain graph  (Flask + D3.js)
echo    4) Personal   Personal-fleet projects  (LetsText/JOKR/etc)
echo    5) RKOJ       Workbench EXE  (http://127.0.0.1:5077/)
echo    Q) Quit
echo.
set /p "PICK=    choice [1-5/Q, default=2 Forge]: "
if /i "%PICK%"=="Q" exit /b 0
if "%PICK%"=="" set "PICK=2"
if "%PICK%"=="1" goto :session
if "%PICK%"=="2" goto :forge
if "%PICK%"=="3" goto :mind
if "%PICK%"=="4" goto :personal
if "%PICK%"=="5" goto :rkoj
goto :pick

:session
if exist "%USERPROFILE%\Desktop\Start-Sinister-Session.bat" (
    call "%USERPROFILE%\Desktop\Start-Sinister-Session.bat"
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
)
exit /b %ERRORLEVEL%

:forge
if exist "%USERPROFILE%\Desktop\Sinister Forge.bat" (
    call "%USERPROFILE%\Desktop\Sinister Forge.bat"
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\install-sinister-forge.ps1" -SanctumRoot "%SANCTUM_ROOT%"
    python -m forge
)
exit /b %ERRORLEVEL%

:mind
if exist "%USERPROFILE%\Desktop\Sinister Mind.bat" (
    call "%USERPROFILE%\Desktop\Sinister Mind.bat"
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\install-sinister-mind.ps1" -SanctumRoot "%SANCTUM_ROOT%"
    python -m mind
)
exit /b %ERRORLEVEL%

:personal
if exist "%USERPROFILE%\Desktop\Personal Project start.bat" (
    call "%USERPROFILE%\Desktop\Personal Project start.bat"
) else (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" -ProjectsFile personal-projects.json -FocusFile personal-focus-suggestions.json
)
exit /b %ERRORLEVEL%

:rkoj
if exist "%USERPROFILE%\Desktop\RKOJ.bat" (
    call "%USERPROFILE%\Desktop\RKOJ.bat"
) else (
    start "" "http://127.0.0.1:5077/"
    powershell.exe -NoProfile -Command "Write-Host 'RKOJ EXE not found at Desktop\RKOJ.bat. Opened http://127.0.0.1:5077/ in browser; start RKOJ manually if not running.'"
)
exit /b %ERRORLEVEL%
