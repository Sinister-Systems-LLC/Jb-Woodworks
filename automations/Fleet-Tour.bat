@echo off
:: Author: RKOJ-ELENO :: 2026-05-24
:: Sanctum :: Fleet Tour :: one-click "show me everything healthy" demo
::
:: Runs the full fleet health stack in one shot for operator (or new lane) demo:
::   1. sinister-doctor (default mode console summary)
::   2. sinister-doctor -Html (HTML report)
::   3. opens latest HTML report in default browser
::   4. shows per-project-protections autofix preview (dry-run; no changes)
::   5. shows brain-archive-orphans preview (dry-run; no changes)
::
:: Read-only by default. No state changes. Safe to run any time.

setlocal enableextensions
set "ROOT=%~dp0.."
set "AUTO=%ROOT%\automations"

echo.
echo ============================================================
echo   Sinister Sanctum :: Fleet Tour
echo ============================================================
echo   READ-ONLY demo. No state changes. Safe to run any time.
echo.

echo --- Step 1/5 :: sinister-doctor (console summary) ---
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%AUTO%\sinister-doctor.ps1" -Quick
echo.

echo --- Step 2/5 :: sinister-doctor -Html (writing report) ---
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%AUTO%\sinister-doctor.ps1" -Quick -Html
echo.

echo --- Step 3/5 :: opening latest HTML report in browser ---
for /f "delims=" %%I in ('dir /b /o-d "%ROOT%\_shared-memory\sinister-doctor-*.html" 2^>nul') do (
    set "LATEST=%%I"
    goto :found_latest
)
:found_latest
if defined LATEST (
    echo   opening: %ROOT%\_shared-memory\%LATEST%
    start "" "%ROOT%\_shared-memory\%LATEST%"
) else (
    echo   [WARN] no HTML report found - sinister-doctor -Html may have failed
)
echo.

echo --- Step 4/5 :: per-project autofix preview (dry-run) ---
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%AUTO%\per-project-protections-autofix.ps1" -DryRun -Yes
echo.

echo --- Step 5/5 :: brain-orphans archive preview (dry-run) ---
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%AUTO%\brain-archive-orphans.ps1" -DryRun
echo.

echo ============================================================
echo   Fleet Tour complete. Next operator actions (all opt-in):
echo.
echo     Apply per-project autofix:
echo       powershell -ExecutionPolicy Bypass -File "%AUTO%\per-project-protections-autofix.ps1" -Yes
echo.
echo     Archive brain orphans:
echo       powershell -ExecutionPolicy Bypass -File "%AUTO%\brain-archive-orphans.ps1" -Yes
echo.
echo     Install daily sinister-doctor cron:
echo       powershell -ExecutionPolicy Bypass -File "%AUTO%\install-sinister-doctor-task.ps1"
echo ============================================================
echo.
pause
endlocal
exit /b 0
