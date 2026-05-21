@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM One-click launcher for RKOJ.exe (Forge TUI default).
REM
REM Operator 2026-05-21: "make sure we have exe RKOJ start ... in the sanctum main directory".
REM
REM Resolution order:
REM   1. Desktop RKOJ.exe (canonical operator-facing artifact, written by the ship pipeline)
REM   2. PyInstaller build/dist RKOJ.exe (in-tree fallback)
REM   3. Print rebuild instructions

setlocal
set EXE_DESKTOP=%USERPROFILE%\Desktop\RKOJ.exe
set EXE_BUILD=%~dp0automations\build\forge-exe\dist\RKOJ.exe

if exist "%EXE_DESKTOP%" (
    echo [RKOJ-Start] Launching Desktop RKOJ.exe
    start "" "%EXE_DESKTOP%"
    exit /b 0
)

if exist "%EXE_BUILD%" (
    echo [RKOJ-Start] Launching build\dist RKOJ.exe
    start "" "%EXE_BUILD%"
    exit /b 0
)

echo [RKOJ-Start] RKOJ.exe not found on Desktop or in build\dist.
echo.
echo To build:    pwsh "%~dp0automations\build\forge-exe\build.ps1"
echo To install:  re-run the RKOJ-Setup wizard ("%~dp0automations\install-rkoj-task.ps1")
echo.
pause
exit /b 1
