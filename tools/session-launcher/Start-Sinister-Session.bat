@echo off
REM Sinister Sanctum :: session launcher (v18 :: portable across any PC)
REM
REM Drop this .bat + the Sanctum folder on ANY Windows PC and run it:
REM   - If Sanctum auto-discovers in any canonical path, launches immediately.
REM   - If not, INTERACTIVELY prompts for the Sanctum folder path + setx persists.
REM   - Pre-flight checks PowerShell / git / gh / claude / git-bash / API key.
REM   - Then hands off to start-sinister-session.ps1 (the picker).
REM
REM Args:
REM   (none)       -> full picker
REM   resume       -> -Resume (skip pickers, auto-pull last-session.json)
REM   new          -> full picker (alias)
REM   <other>      -> passed through to the PS1
REM
REM Bootstrap delegated to automations\bootstrap-portability.ps1 (operator's
REM "I can place this on any PC in the world" directive 2026-05-21).
REM
REM Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

TITLE Sinister Sanctum :: Session Launcher

REM ============================================================
REM Auto-relaunch in Windows Terminal (Cascadia Code; Braille art renders crisp).
REM Skip if already in WT (WT_SESSION env var) or if wt.exe unavailable.
REM ============================================================
IF NOT DEFINED WT_SESSION (
    where wt.exe >nul 2>&1
    IF NOT ERRORLEVEL 1 (
        start "" wt.exe new-tab --title "Sinister Terminal" cmd.exe /K "\"%~f0\" %*"
        exit /b 0
    )
)

REM ============================================================
REM STEP 1 -- Discover SANCTUM_ROOT via portability bootstrap PS1.
REM           The PS1 prints status to stdout but the LAST line is the path.
REM           We try the standard candidate paths first; if any has the
REM           bootstrap PS1, invoke it (which prompts the operator + sets env
REM           if needed). If none of the candidates even has the bootstrap
REM           PS1 (truly fresh PC), fall back to inline prompt.
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
    REM Call bootstrap; capture its LAST stdout line as SANCTUM_ROOT.
    FOR /F "usebackq delims=" %%I IN (`powershell -NoProfile -ExecutionPolicy Bypass -File "%BOOT_PS1%"`) DO (
        SET "SANCTUM_ROOT=%%I"
    )
) ELSE (
    REM Fallback: pure-cmd interactive prompt + setx persist.
    echo.
    echo  ============================================================
    echo   Sinister Sanctum :: NOT FOUND on this PC
    echo  ============================================================
    echo.
    echo  This bat could not locate the Sinister Sanctum repo at any of:
    echo    %%SINISTER_SANCTUM_ROOT%%
    echo    D:\Sinister Sanctum
    echo    C:\Sinister Sanctum
    echo    %%USERPROFILE%%\Sinister Sanctum
    echo    %%USERPROFILE%%\Desktop\Sinister Sanctum
    echo.
    echo  Where is your Sinister Sanctum clone on this PC?
    echo  ^(Paste the full path, then press Enter. Example: D:\Sinister Sanctum^)
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
        echo         Expected: %SANCTUM_ROOT%\automations\start-sinister-session.ps1
        pause
        exit /b 1
    )

    REM Persist for next launch.
    setx SINISTER_SANCTUM_ROOT "%SANCTUM_ROOT%" >nul
    echo.
    echo  [OK] Saved SINISTER_SANCTUM_ROOT = %SANCTUM_ROOT%
    echo       Next launch will auto-find without prompting.
    echo.
)

IF NOT DEFINED SANCTUM_ROOT (
    echo.
    echo  [FAIL] Bootstrap failed to resolve Sanctum root.
    pause
    exit /b 1
)

REM ============================================================
REM STEP 2 -- Hand off to the main launcher PS1 (interactive picker).
REM ============================================================
IF /I "%~1"=="resume" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" -Resume
) ELSE IF /I "%~1"=="new" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
) ELSE IF "%~1"=="" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
) ELSE (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" %*
)
exit /b %ERRORLEVEL%
