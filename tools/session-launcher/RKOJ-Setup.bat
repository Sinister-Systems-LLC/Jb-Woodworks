@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM RKOJ-Setup.bat - Thin wrapper for the first-run setup wizard.
REM Delegates all heavy lifting to automations/rkoj-setup.ps1.
REM Persona: EVE (Sinister Sanctum orchestration agent)
title RKOJ-Setup :: Sinister Sanctum first-run wizard
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0..\..\automations\rkoj-setup.ps1" %*
set RC=%ERRORLEVEL%
echo.
echo (RKOJ-Setup exit code: %RC%)
pause
exit /b %RC%
