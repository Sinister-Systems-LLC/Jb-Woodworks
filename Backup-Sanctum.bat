@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM Manual Sanctum backup trigger -> D:\Backups\sanctum-daily\<YYYY-MM-DD>\
REM
REM Operator 2026-05-21: "back up bat file in the sanctum main directory ...
REM backup sanctum every 24 hours". This is the manual one-shot bat; the 24h
REM scheduled-task variant calls the same logic via SinisterSanctumDailyBackup.
REM
REM Calls the sanctum-backup tool (commit 178fbcf, 47/47 tests).

setlocal
pushd "%~dp0"

REM ISO date YYYY-MM-DD (locale-stable: pull via PowerShell, not %date% which
REM varies by Region setting).
for /f "usebackq tokens=*" %%d in (`powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"`) do set DATE_STAMP=%%d

set DEST=D:\Backups\sanctum-daily\%DATE_STAMP%
if not exist "%DEST%" mkdir "%DEST%"

echo [Backup-Sanctum] Source: D:\Sinister Sanctum
echo [Backup-Sanctum] Dest:   %DEST%
echo [Backup-Sanctum] Retention: 7 days
echo.

REM Prefer the in-tree sanctum-backup tool if it exposes a CLI; fall back to
REM robocopy. Per CHANGELOG / commit 178fbcf the tool ships at
REM tools\sanctum-backup\ with 47/47 tests; the exact entry-point may be
REM run.py, __main__.py, or sanctum_backup.cli — try each.
python -m sanctum_backup --dest "%DEST%" --retention-days 7 2>nul
if %ERRORLEVEL% EQU 0 goto :done

python "%~dp0tools\sanctum-backup\run.py" --dest "%DEST%" --retention-days 7 2>nul
if %ERRORLEVEL% EQU 0 goto :done

echo [Backup-Sanctum] sanctum-backup tool entry-point not found; falling back to robocopy.
robocopy "%~dp0" "%DEST%" /E /XJ /XD __pycache__ .git _vault _vault-personal tmp /XF *.pyc /R:1 /W:1 /NFL /NDL /NJH /NJS
if %ERRORLEVEL% LSS 8 goto :done

echo [Backup-Sanctum] BACKUP FAILED (robocopy exit %ERRORLEVEL%)
popd
exit /b 1

:done
echo.
echo [Backup-Sanctum] Done. Dest: %DEST%
popd
pause
exit /b 0
