@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM JB Woodworks - stop anything on port 3000.

echo Stopping JB Woodworks (port 3000)...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do (
  echo   Killing PID %%P
  taskkill /F /PID %%P 2>nul
)
echo Done.
timeout /t 2 /nobreak >nul
