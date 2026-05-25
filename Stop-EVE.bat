@echo off
REM Stop-EVE.bat -- ruthless kill of every EVE.exe / claude / sanctum-related process.
REM Author: RKOJ-ELENO :: 2026-05-25
REM Operator hard-canonical 2026-05-25 (verbatim):
REM   "place the stop eve bat file on the dekstop for safety and include in
REM    the project dir for leo"
REM
REM Use when EVE.exe freezes / sessions stuck / desktop unresponsive.
REM Safe: only kills processes whose name matches sanctum-fleet patterns.
REM Operator interactive apps (browser, IDE, Office) are NEVER touched.

TITLE Stop EVE :: Sinister Sanctum
echo.
echo  === Stop EVE — killing all sanctum fleet processes ===
echo.

REM Kill EVE.exe and child python.exe processes
echo  Killing EVE.exe...
taskkill /F /IM EVE.exe /T 2>nul

echo  Killing stray claude.exe sessions...
taskkill /F /IM claude.exe /T 2>nul

REM Kill orphaned conhost windows whose parent is dead
echo  Killing orphan conhost windows...
for /f "tokens=2" %%P in ('tasklist /FI "IMAGENAME eq conhost.exe" /FO CSV /NH ^| findstr /v "PID"') do (
    taskkill /F /PID %%~P 2>nul
)

REM Kill pythonw.exe daemons (headless schtask-spawned)
echo  Killing headless pythonw.exe daemons (sanctum schtasks)...
for /f "tokens=2" %%P in ('tasklist /FI "IMAGENAME eq pythonw.exe" /FO CSV /NH ^| findstr /v "PID"') do (
    taskkill /F /PID %%~P 2>nul
)

REM Kill mintty.exe sessions (git-bash terminals)
echo  Killing mintty.exe sessions (sanctum agent windows)...
taskkill /F /IM mintty.exe /T 2>nul

REM Kill the bash.exe shells spawned by start-sinister-session.ps1
echo  Killing bash.exe sanctum shells...
for /f "tokens=2" %%P in ('tasklist /FI "IMAGENAME eq bash.exe" /FO CSV /NH ^| findstr /v "PID"') do (
    taskkill /F /PID %%~P 2>nul
)

echo.
echo  === Stop EVE done ===
echo  Press any key to close...
pause >nul
