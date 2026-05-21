@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM Direct RKOJ.exe launcher (v0.7.0+).
set "RKOJ_EXE=C:\Users\Zonia\Desktop\RKOJ.exe"
if not exist "%RKOJ_EXE%" (
  echo RKOJ.exe not found at %RKOJ_EXE%.
  echo Build it via "pyinstaller --clean --noconfirm RKOJ.spec" in D:\Sinister Sanctum\automations\build\forge-exe
  pause & exit /b 1
)
if not "%~1"=="" set "SINISTER_PROJECT=%~1"
"%RKOJ_EXE%"
