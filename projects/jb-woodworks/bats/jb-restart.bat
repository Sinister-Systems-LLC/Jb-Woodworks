@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM JB Woodworks - kill port 3000, then relaunch Next.js dev.

call "%~dp0jb-kill.bat"
timeout /t 1 /nobreak >nul
call "%~dp0jb-dev.bat"
