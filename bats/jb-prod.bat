@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM JB Woodworks - local production smoke (Next.js build + start).

setlocal
set ROOT=D:\Sinister Sanctum\projects\jb-woodworks
cd /d "%ROOT%" || (echo Could not cd to %ROOT% & pause & exit /b 1)

echo.
echo  ============================================
echo   JB Woodworks  -  Local PRODUCTION (Next.js)
echo  ============================================
echo.
echo   URL:  http://127.0.0.1:3000
echo   Mode: optimized build, no hot reload
echo.
echo  ============================================
echo.

call npm run build || (echo Build failed & pause & exit /b 1)
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:3000/"
call npm start
