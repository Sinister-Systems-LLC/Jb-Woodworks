@echo off
:: Author: RKOJ-ELENO :: 2026-05-23
:: Leo + new-operator helper: double-click to auto-clone every missing per-project source/
:: dir from GitHub. Runs the Sanctum's automations\clone-missing-sources.ps1 with friendly
:: pause on exit so the operator can read the result.
::
:: First-run path for a fresh Sanctum checkout where projects/*/source dirs are empty
:: but projects.json lists their github remotes.

setlocal
set "ROOT=%~dp0.."
set "PS_SCRIPT=%ROOT%\automations\clone-missing-sources.ps1"

echo.
echo ============================================================
echo   Sinister Sanctum :: Clone Missing Sub-Project Sources
echo ============================================================
echo.
echo Auth: requires either SSH key in ~/.ssh/ OR GH_TOKEN env var.
echo.
echo Press Ctrl+C to abort. Any key to continue...
pause >nul

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set EC=%ERRORLEVEL%

echo.
echo Exit code: %EC%
echo.
pause
endlocal
exit /b %EC%
