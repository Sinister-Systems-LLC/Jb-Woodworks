@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM JB Woodworks - first-time setup. Installs npm deps + generates Prisma client.

setlocal
set ROOT=D:\Sinister Sanctum\projects\jb-woodworks
cd /d "%ROOT%" || (echo Could not cd to %ROOT% & pause & exit /b 1)

echo [1/3] Installing npm dependencies...
call npm install
echo.
echo [2/3] Generating Prisma client...
call npx prisma generate
echo.
echo [3/3] Done. Launch with bats\jb-dev.bat
pause
