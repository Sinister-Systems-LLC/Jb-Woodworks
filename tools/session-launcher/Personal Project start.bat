@echo off
REM Sinister Personal :: project launcher (v3 :: portable across any PC)
REM
REM Same PS1 as Start-Sinister-Session.bat, but passes:
REM   -ProjectsFile personal-projects.json
REM   -FocusFile personal-focus-suggestions.json
REM
REM So the project picker shows JOKR / RKOJ-personal / Car / Drone / LetsText
REM / Cell-Network / Eve instead of the Sanctum-fleet entries.
REM
REM PARITY: every change to the launcher PS1 (start-sinister-session.ps1)
REM propagates here automatically (same script + different -ProjectsFile flag).
REM
REM Bootstrap delegated to automations\bootstrap-portability.ps1 - prompts for
REM Sanctum folder location if not found, persists via setx, runs pre-flight
REM checks (PowerShell / git / gh / claude / git-bash / API key).
REM
REM Args:
REM   (none)        -> full picker (personal projects)
REM   resume        -> -Resume (auto-pull last-session.json)
REM   new           -> -ForceWizard (full picker even if last-session exists)
REM   <other>       -> verbatim passthrough
REM
REM Path discovery (D: drive preferred per operator directive 2026-05-21):
REM   1. %SINISTER_SANCTUM_ROOT%
REM   2. D:\Sinister Sanctum         (canonical primary)
REM   3. C:\Sinister Sanctum         (fallback)
REM   4. %USERPROFILE%\Sinister Sanctum
REM   5. %USERPROFILE%\Desktop\Sinister Sanctum
REM
REM Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

TITLE Sinister Personal :: Project Launcher

REM ============================================================
REM Auto-relaunch in Windows Terminal (Cascadia Code; Braille art renders).
REM ============================================================
IF NOT DEFINED WT_SESSION (
    where wt.exe >nul 2>&1
    IF NOT ERRORLEVEL 1 (
        start "" wt.exe new-tab --title "Sinister Personal" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

REM ============================================================
REM STEP 1 -- Discover SANCTUM_ROOT via portability bootstrap PS1.
REM ============================================================

SET "BOOT_PS1="
FOR %%C IN (
    "%SINISTER_SANCTUM_ROOT%\automations\bootstrap-portability.ps1"
    "D:\Sinister Sanctum\automations\bootstrap-portability.ps1"
    "C:\Sinister Sanctum\automations\bootstrap-portability.ps1"
    "%USERPROFILE%\Sinister Sanctum\automations\bootstrap-portability.ps1"
    "%USERPROFILE%\Desktop\Sinister Sanctum\automations\bootstrap-portability.ps1"
) DO (
    IF EXIST "%%~C" (
        IF NOT DEFINED BOOT_PS1 SET "BOOT_PS1=%%~C"
    )
)

IF DEFINED BOOT_PS1 (
    FOR /F "usebackq delims=" %%I IN (`powershell -NoProfile -ExecutionPolicy Bypass -File "%BOOT_PS1%"`) DO (
        SET "SANCTUM_ROOT=%%I"
    )
) ELSE (
    echo.
    echo  ============================================================
    echo   Sinister Sanctum :: NOT FOUND on this PC
    echo  ============================================================
    echo.
    echo  Where is your Sinister Sanctum clone on this PC?
    echo  ^(Paste the full path. Example: D:\Sinister Sanctum^)
    echo.
    set /p "SANCTUM_ROOT=  Path: "

    IF NOT DEFINED SANCTUM_ROOT (
        echo  [FAIL] No path entered. To clone the repo, run:
        echo         git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"
        pause
        exit /b 1
    )

    IF NOT EXIST "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" (
        echo  [FAIL] That path does not contain a Sanctum repo.
        pause
        exit /b 1
    )

    setx SINISTER_SANCTUM_ROOT "%SANCTUM_ROOT%" >nul
    echo  [OK] Saved SINISTER_SANCTUM_ROOT for next launch.
)

IF NOT DEFINED SANCTUM_ROOT (
    echo  [FAIL] Bootstrap failed to resolve Sanctum root.
    pause
    exit /b 1
)

REM ============================================================
REM STEP 2 -- Hand off to the SHARED launcher PS1 with PERSONAL project file.
REM ============================================================

set "PS1=%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
set "EXTRA_ARGS=-ProjectsFile personal-projects.json -FocusFile personal-focus-suggestions.json"

IF /I "%~1"=="resume" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS% -Resume
) ELSE IF /I "%~1"=="new" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS% -ForceWizard
) ELSE IF "%~1"=="" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS%
) ELSE (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %EXTRA_ARGS% %*
)
exit /b %ERRORLEVEL%
