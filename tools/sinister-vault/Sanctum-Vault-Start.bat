@echo off
:: Sinister Vault daemon — foreground console start
:: Author: Sinister Sanctum SV-A agent (Claude) :: 2026-05-19

setlocal
set "VAULT_DIR=%~dp0"
cd /d "%VAULT_DIR%"

title Sinister Vault (port 5078)

set "PYEXE=python"
where py >nul 2>&1
if %errorlevel%==0 set "PYEXE=py -3"

echo [vault] starting daemon from %VAULT_DIR%
echo [vault] python: %PYEXE%
echo [vault] port:   5078    max-gb: 1024    warn-gb: 950
echo.

%PYEXE% "%VAULT_DIR%daemon.py" --port 5078 --max-gb 1024 --warn-gb 950

set "RC=%errorlevel%"
echo.
echo [vault] daemon exited with code %RC%
pause
endlocal & exit /b %RC%
