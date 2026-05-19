@echo off
REM One-click: apply the Sinister Purple Obsidian theme to every _vault on D:.
REM
REM What it does:
REM   - Discovers all _vault dirs under D:\Sinister + D:\Sinister Sanctum
REM   - Creates .obsidian/snippets/ if missing
REM   - Copies the canonical sinister-purple.css from Sanctum's vault
REM   - Sets each vault's appearance.json: accent #a855f7, theme moonstone, snippet enabled
REM   - Sets each vault's app.json: snippet enabled
REM
REM Idempotent — safe to re-run after editing the canonical snippet.
REM
REM Usage: double-click this .bat OR run from cmd:
REM   "D:\Sinister Sanctum\automations\APPLY-SINISTER-PURPLE-THEME.bat"
REM   "D:\Sinister Sanctum\automations\APPLY-SINISTER-PURPLE-THEME.bat" /Dry

setlocal

set "SCRIPT=%~dp0apply-sinister-purple-theme.ps1"
if "%~1"=="/Dry" (
    set "ARGS=-DryRun"
) else (
    set "ARGS="
)

echo Running: %SCRIPT% %ARGS%
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" %ARGS%
set EC=%ERRORLEVEL%
echo.
echo Exit: %EC%
pause
exit /b %EC%
