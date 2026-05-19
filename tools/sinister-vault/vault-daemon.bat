@echo off
REM Author: Sinister Sanctum SV-E agent (Claude) :: 2026-05-19
REM vault-daemon.bat - what Task Scheduler runs to keep SinisterVault alive.
REM
REM Behavior:
REM   1. Launches D:\Sinister Sanctum\tools\sinister-vault\.venv\Scripts\python.exe
REM      running daemon.py (SV-A's file) on loopback port 5078.
REM   2. Restart loop with 3-second sleep between attempts.
REM   3. Max 5 restarts per rolling hour. After cap, exit non-zero so Task
REM      Scheduler's outer RestartCount=5 / Interval=1 min cap takes over
REM      (effective ceiling ~25 restarts/hr, then full stop until next logon).
REM   4. Heartbeat ticker (60-second cadence) is launched as a backgrounded
REM      `start /b` process. Touches _shared-memory\heartbeats\sinister-vault.beat.
REM   5. All output tee'd to _daemon-logs\vault-<UTC-stamp>.log + persistent
REM      _daemon-logs\daemon.log audit trail.
REM
REM Designed to be invoked by:
REM   - Task Scheduler ('SinisterVault' task, AtLogOn trigger; see install-vault-task.ps1)
REM   - The operator, manually, for debugging (just double-click).

setlocal EnableExtensions EnableDelayedExpansion

REM Re-entrant dispatch: if first arg is __HEARTBEAT__, run heartbeat mode and exit.
if /I "%~1"=="__HEARTBEAT__" goto :heartbeat_main

title SinisterVault Daemon

set "VAULT_DIR=D:\Sinister Sanctum\tools\sinister-vault"
set "VENV_PY=%VAULT_DIR%\.venv\Scripts\python.exe"
set "DAEMON_PY=%VAULT_DIR%\daemon.py"
set "PORT=5078"

set "DAEMON_LOG_DIR=%VAULT_DIR%\_daemon-logs"
set "HEARTBEAT_DIR=D:\Sinister Sanctum\_shared-memory\heartbeats"
set "HEARTBEAT_FILE=%HEARTBEAT_DIR%\sinister-vault.beat"
set "AUDIT_LOG=%DAEMON_LOG_DIR%\daemon.log"

if not exist "%DAEMON_LOG_DIR%" mkdir "%DAEMON_LOG_DIR%" >nul 2>&1
if not exist "%HEARTBEAT_DIR%" mkdir "%HEARTBEAT_DIR%" >nul 2>&1

REM Per-launch log gets a UTC-ish stamp (locale-independent via wmic).
set "LOCAL_DT="
for /f "skip=1 delims=" %%T in ('wmic os get LocalDateTime ^| findstr /R "^[0-9]"') do (
    if not defined LOCAL_DT set "LOCAL_DT=%%T"
)
set "STAMP=%LOCAL_DT:~0,8%T%LOCAL_DT:~8,6%"
set "RUN_LOG=%DAEMON_LOG_DIR%\vault-%STAMP%.log"

call :log "==== vault-daemon start (stamp=%STAMP%) ===="

if not exist "%VENV_PY%" (
    call :log "[FATAL] venv python not found at %VENV_PY% - run 'python -m venv .venv && .venv\Scripts\pip install -r requirements.txt' first"
    exit /b 9
)
if not exist "%DAEMON_PY%" (
    call :log "[FATAL] daemon.py not found at %DAEMON_PY% - SV-A file missing"
    exit /b 9
)
call :log "[*] python=%VENV_PY%  daemon=%DAEMON_PY%  port=%PORT%"

REM Spawn heartbeat ticker in background (re-entrant call into __HEARTBEAT__ mode).
start "" /b cmd /c "%~f0" __HEARTBEAT__ "%HEARTBEAT_FILE%"

REM Restart accounting (rolling 1-hour window of attempt timestamps).
set /a RESTART_COUNT=0
call :now_seconds CURRENT_S
set /a WINDOW_START_S=%CURRENT_S%

:loop
set /a RESTART_COUNT+=1
call :now_seconds CURRENT_S
set /a ELAPSED=%CURRENT_S% - %WINDOW_START_S%
if %ELAPSED% LSS 0 set /a ELAPSED+=86400
if %ELAPSED% GEQ 3600 (
    set /a WINDOW_START_S=%CURRENT_S%
    set /a RESTART_COUNT=1
    call :log "[*] rolling-hour window reset"
)

if %RESTART_COUNT% GTR 5 (
    call :log "[FATAL] 5 restarts in <1h - bailing (Task Scheduler outer cap takes over)"
    exit /b 7
)

call :log "[*] attempt %RESTART_COUNT%/5 (window elapsed=%ELAPSED%s) - launching daemon.py"

"%VENV_PY%" "%DAEMON_PY%" --port %PORT% >>"%RUN_LOG%" 2>&1
set "EXIT_RC=%ERRORLEVEL%"
call :log "[*] daemon exited with rc=%EXIT_RC%; sleeping 3s before retry"
timeout /t 3 /nobreak >nul
goto loop

REM ---------------------------------------------------------------------------
:log
set "MSG=%~1"
set "LOG_DT="
for /f "skip=1 delims=" %%T in ('wmic os get LocalDateTime ^| findstr /R "^[0-9]"') do (
    if not defined LOG_DT set "LOG_DT=%%T"
)
set "LOG_TS=%LOG_DT:~0,4%-%LOG_DT:~4,2%-%LOG_DT:~6,2% %LOG_DT:~8,2%:%LOG_DT:~10,2%:%LOG_DT:~12,2%"
echo [%LOG_TS%] %MSG%
>>"%RUN_LOG%" echo [%LOG_TS%] %MSG%
>>"%AUDIT_LOG%" echo [%LOG_TS%] %MSG%
goto :eof

:now_seconds
REM Cheap monotonic-ish seconds via TIME var; rolls over at midnight (handled
REM in :loop with the LSS 0 guard).
for /f "tokens=1-3 delims=:." %%a in ("%TIME%") do (
    set /a "%~1=(((%%a*60)+1%%b%%100)*60)+1%%c%%100"
)
goto :eof

REM ---------------------------------------------------------------------------
:heartbeat_main
REM Re-entrant heartbeat mode: touch %~2 (the .beat file) every 60s.
:heartbeat_tick
>"%~2" echo %DATE% %TIME%
timeout /t 60 /nobreak >nul
goto heartbeat_tick
