@echo off
REM UNLOCK-AND-PUSH.bat - kill stale git locks then run PUSH-TO-GITHUB.bat
REM
REM Use this when PUSH-TO-GITHUB.bat reports:
REM   fatal: Unable to create '.../.git/index.lock': File exists.
REM
REM It:
REM   1. Waits 10 seconds for any in-flight git process to finish
REM   2. Kills any orphaned git.exe still running (none if no real work pending)
REM   3. Removes .git/index.lock if present
REM   4. Removes .git/HEAD.lock if present
REM   5. Re-runs PUSH-TO-GITHUB.bat
REM
REM Safe: only removes *.lock files (locks), never touches actual git objects.

setlocal EnableDelayedExpansion

set "SOURCE=D:\Sinister Sanctum\projects\sinister-snap-emu\source"
set "PUSH_BAT=%~dp0PUSH-TO-GITHUB.bat"

echo ============================================================
echo UNLOCK-AND-PUSH  Sinister Snap EMU
echo ============================================================
echo.

echo [1/5] Wait 10s for any in-flight git process to finish on its own...
timeout /t 10 /nobreak
echo.

echo [2/5] Check for running git.exe processes...
tasklist /FI "IMAGENAME eq git.exe" /FO TABLE 2>NUL | findstr /I "git.exe" >NUL
if not errorlevel 1 (
    echo   Found orphaned git.exe processes:
    tasklist /FI "IMAGENAME eq git.exe" /FO TABLE 2>NUL
    echo.
    echo   Killing them ^(safe - they are stalled^):
    taskkill /F /IM git.exe 2>NUL
    timeout /t 2 /nobreak >NUL
) else (
    echo   No orphaned git.exe - good
)
echo.

echo [3/5] Remove stale index.lock if present...
if exist "%SOURCE%\.git\index.lock" (
    del /F /Q "%SOURCE%\.git\index.lock"
    if not exist "%SOURCE%\.git\index.lock" (
        echo   removed index.lock
    ) else (
        echo   FAIL: could not remove index.lock - may need admin or file is open elsewhere
    )
) else (
    echo   no index.lock - good
)
echo.

echo [4/5] Remove other stale .lock files in .git/...
for %%f in (HEAD.lock config.lock packed-refs.lock) do (
    if exist "%SOURCE%\.git\%%f" (
        del /F /Q "%SOURCE%\.git\%%f"
        echo   removed %%f
    )
)
echo.

echo [5/5] Re-running PUSH-TO-GITHUB.bat...
echo ============================================================
echo.

if not exist "%PUSH_BAT%" (
    echo FAIL: push bat not found at %PUSH_BAT%
    pause
    exit /b 2
)

call "%PUSH_BAT%"
exit /b %ERRORLEVEL%
