@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM JB Woodworks - one-click Next.js dev server.

setlocal
set ROOT=D:\Sinister Sanctum\projects\jb-woodworks
cd /d "%ROOT%" || (echo Could not cd to %ROOT% & pause & exit /b 1)

echo.
echo  ============================================
echo   JB Woodworks  -  Local Dev (Next.js 15)
echo  ============================================
echo.
echo   URL:  http://127.0.0.1:3000
echo   Mode: dev + hot reload
echo.
echo  ============================================
echo.

start "" cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:3000/"
call npm run dev
