@echo off
REM Author: Claude (Opus 4.7) - Sinister Sanctum Vault-Sync Agent
REM Purpose: Backup foreground launcher for Syncthing.
REM Use this if the NSSM-wrapped Syncthing service is not yet installed
REM (e.g. first-run before install.ps1) or has stopped and you need
REM to bring sync up quickly without admin rights.
REM
REM Closes the window = stops Syncthing. For background, use the service.

setlocal

set "SYNCTHING_EXE=C:\Program Files\Syncthing\syncthing.exe"
set "SYNCTHING_HOME=%LOCALAPPDATA%\Syncthing"

if not exist "%SYNCTHING_EXE%" (
    echo [ERROR] Syncthing not found at "%SYNCTHING_EXE%".
    echo Run install.ps1 first ^(as Administrator^), or install Syncthing manually
    echo from https://syncthing.net/downloads/
    pause
    exit /b 1
)

if not exist "%SYNCTHING_HOME%" (
    echo [INFO] Creating Syncthing config dir: %SYNCTHING_HOME%
    mkdir "%SYNCTHING_HOME%"
)

echo.
echo ===================================================================
echo  Sinister Vault - Syncthing foreground launcher
echo  Binary:   %SYNCTHING_EXE%
echo  Config:   %SYNCTHING_HOME%
echo  Web UI:   http://localhost:8384/
echo.
echo  Closing this window will STOP Syncthing.
echo  For background operation, run install.ps1 to register as a service.
echo ===================================================================
echo.

"%SYNCTHING_EXE%" -no-restart -home "%SYNCTHING_HOME%"

endlocal
