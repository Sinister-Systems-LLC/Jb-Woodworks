@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM Install-RKOJ-Shortcuts.bat - Thin wrapper for the shortcut installer.
REM Delegates all work to automations\install-rkoj-shortcuts.ps1.
REM Persona: EVE (Sinister Sanctum orchestration agent)
title Install-RKOJ-Shortcuts :: desktop + start-menu .lnk auto-installer
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0..\..\automations\install-rkoj-shortcuts.ps1" %*
set RC=%ERRORLEVEL%
echo.
echo (Install-RKOJ-Shortcuts exit code: %RC%)
pause
exit /b %RC%
