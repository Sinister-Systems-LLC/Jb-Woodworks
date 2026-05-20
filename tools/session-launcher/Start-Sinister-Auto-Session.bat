@echo off
REM Sinister Sanctum :: AUTONOMOUS LOOP MODE launcher
REM
REM One-click entry point that launches the canonical session-start PS1 with
REM -Mode auto pre-selected. Operator still picks the project + agent name,
REM but the spawned agent enters autonomous-loop mode immediately:
REM   PHASE 1 review every plan-bearing file for the project
REM   PHASE 2 synthesize ONE complete scope-plan to _shared-memory/plans/<proj>-auto-<UTC>/master-plan.md
REM   PHASE 3 TaskCreate every master-actionable row
REM   PHASE 4 invoke /loop (no interval, self-paced) so the agent cycles tasks
REM   PHASE 5 5-check gate per iteration; operator-only gates surface via end-of-turn
REM
REM Path discovery mirrors Start-Sinister-Session.bat (PowerShell resolution).
REM Order: $env:SINISTER_SANCTUM_ROOT -> D:\Sinister Sanctum -> C:\Sinister Sanctum -> %USERPROFILE%\Sinister Sanctum
REM
REM Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-20

TITLE Sinister Sanctum :: AUTONOMOUS LOOP MODE

REM ============================================================
REM Auto-relaunch in Windows Terminal (Cascadia Code; Braille art renders).
REM Mirrors Start-Sinister-Session.bat behavior.
REM ============================================================
IF NOT DEFINED WT_SESSION (
    where wt.exe >nul 2>&1
    IF NOT ERRORLEVEL 1 (
        start "" wt.exe new-tab --title "Sinister AUTO" cmd.exe /K "\"%~f0\""
        exit /b 0
    )
)

FOR /F "usebackq delims=" %%I IN (`powershell -NoProfile -Command "$paths = @($env:SINISTER_SANCTUM_ROOT, 'D:\Sinister Sanctum', 'C:\Sinister Sanctum', (Join-Path $env:USERPROFILE 'Sinister Sanctum')); foreach ($p in $paths) { if ($p -and (Test-Path (Join-Path $p 'automations\start-sinister-session.ps1'))) { Write-Output $p; break } }"`) DO SET "SANCTUM_ROOT=%%I"

IF NOT DEFINED SANCTUM_ROOT (
    echo.
    echo [FAIL] Sinister Sanctum repo not found in any canonical location.
    echo.
    echo If you have a clone elsewhere, set SINISTER_SANCTUM_ROOT env var:
    echo        setx SINISTER_SANCTUM_ROOT "X:\path\to\Sinister Sanctum"
    echo        ^(then open a NEW cmd window for the change to load^)
    echo.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" -Mode auto %*
exit /b %ERRORLEVEL%
