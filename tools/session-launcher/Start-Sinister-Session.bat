@echo off
REM RKOJ workbench available - see RKOJ.bat for one-click launch.
REM ============================================================
REM  Start-Sinister-Session.bat  (v7 :: Agent SS-A 2026-05-19)
REM
REM  Themed launcher for any Sinister Sanctum work session.
REM  - Skull + SINISTER block-letter logo
REM  - Live trophy case (Sinister Panel + RKA stats)
REM  - Pre-flight rows: github / memory / files / bots / custodian / venv
REM      + RKOJ console (127.0.0.1:5077) + Sinister Vault (127.0.0.1:5078)
REM      + Custodian/Gitea combined row
REM  - Project picker (Sanctum default) + mode picker (RKOJ default)
REM      * pass -Mode rkoj to skip pickers + launch the workbench EXE only
REM  - Custom prompt option (C) with save-as-template
REM  - New project option (N) appends to registry
REM  - Resume-from-cycle-point prompt (hits RKOJ /api/cycle-points)
REM  - Schedule-this-spawn prompt (POSTs /api/schedule to Vault or RKOJ)
REM  - Pre-trusts the project folder in ~/.claude.json
REM  - Auto-spawns git-bash and runs claude --dangerously-skip-permissions
REM  - Sends the cold-start phrase as the first message
REM ============================================================

TITLE Sinister Sanctum :: Session Start  ::  RKOJ at :5077

IF NOT EXIST "D:\Sinister Sanctum\automations\start-sinister-session.ps1" (
    echo [FAIL] start-sinister-session.ps1 not found at D:\Sinister Sanctum\automations\
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\start-sinister-session.ps1" %*
exit /b %ERRORLEVEL%
