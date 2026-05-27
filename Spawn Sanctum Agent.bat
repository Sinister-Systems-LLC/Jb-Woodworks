@echo off
REM Spawn Sanctum Agent :: ROOT SHIM (v12, unify-with-automations 2026-05-27)
REM Author: RKOJ-ELENO :: 2026-05-27
REM
REM v12 (sanctum lane, operator-verbatim trigger 2026-05-27T03:07Z:
REM   "FIX `Spawn Sanctum Agent.bat`. The operator reports it is broken.").
REM
REM Diagnosis:
REM   - Root bat was at v10 (20-lane + lane-21 only-in-header) and STILL used
REM     the old shared-creds spawn path (slot-swap overwrites parent
REM     .credentials.json -> 401 storm killed the operator's parent session).
REM   - automations\Spawn-Sanctum-Agent.bat was at v11.1 with per-lane
REM     CLAUDE_CONFIG_DIR isolation (safe) but only 20 lanes.
REM   - Two source-of-truth bats = guaranteed drift. Confirmed: recent
REM     spawn-fleet-*\ run dirs from 2026-05-26T22:05Z onward showed
REM     ok_count=0 / fail_count=1 with NO lane log written = silent
REM     picker-exit before lane spawn (no isolation = no slot pick = abort).
REM   - projects.json picker.visible_keys[] was missing sinister-ascii-converter
REM     (project entry exists at index 28 but not promoted to the visible list).
REM
REM Fix:
REM   1. Bumped automations\Spawn-Sanctum-Agent.bat v11.1 -> v12 with
REM      LANE_21=sinister-ascii-converter (parity with operator's v10-stub).
REM   2. THIS root bat is now a SHIM that delegates to the v12 in automations\.
REM      One source of truth = no drift.
REM   3. -Repair preserved as a pass-through flag (already works in v12).
REM
REM Smoke (sanctum iter, this turn):
REM   "Spawn Sanctum Agent.bat" -Repair < NUL    -> rc=0, all 4 preflight OK
REM   "Spawn Sanctum Agent.bat" -Help < NUL      -> v12 help banner, rc=0
REM
REM USAGE -- exactly the same as before (the shim is transparent):
REM   "Spawn Sanctum Agent.bat"             (interactive picker)
REM   "Spawn Sanctum Agent.bat" -All        (all 21 lanes)
REM   "Spawn Sanctum Agent.bat" -SoloSanctum
REM   "Spawn Sanctum Agent.bat" -Lanes sanctum,sinister-memory,sinister-term
REM   "Spawn Sanctum Agent.bat" -Repair     (preflight only)
REM   "Spawn Sanctum Agent.bat" -DryRun     (full plumbing, no mintty spawn)

setlocal enableextensions

REM Resolve SANCTUM_ROOT in the same priority order as the v12 (env -> D: -> C: -> user).
set "SANCTUM_ROOT="
if defined SINISTER_SANCTUM_ROOT if exist "%SINISTER_SANCTUM_ROOT%\automations\Spawn-Sanctum-Agent.bat" set "SANCTUM_ROOT=%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT if exist "D:\Sinister Sanctum\automations\Spawn-Sanctum-Agent.bat" set "SANCTUM_ROOT=D:\Sinister Sanctum"
if not defined SANCTUM_ROOT if exist "C:\Sinister Sanctum\automations\Spawn-Sanctum-Agent.bat" set "SANCTUM_ROOT=C:\Sinister Sanctum"
if not defined SANCTUM_ROOT if exist "%USERPROFILE%\Sinister Sanctum\automations\Spawn-Sanctum-Agent.bat" set "SANCTUM_ROOT=%USERPROFILE%\Sinister Sanctum"

if not defined SANCTUM_ROOT (
    color 4F
    echo.
    echo  [FAIL] Sinister Sanctum repo not found.
    echo         Tried: %%SINISTER_SANCTUM_ROOT%% / D:\Sinister Sanctum
    echo                C:\Sinister Sanctum / %%USERPROFILE%%\Sinister Sanctum
    echo         Fix: set SINISTER_SANCTUM_ROOT env var, OR place repo at D:\Sinister Sanctum
    echo.
    pause
    exit /b 1
)

set "V12_BAT=%SANCTUM_ROOT%\automations\Spawn-Sanctum-Agent.bat"
if not exist "%V12_BAT%" (
    color 4F
    echo.
    echo  [FAIL] Spawn-Sanctum-Agent.bat ^(v12^) not found at:
    echo         %V12_BAT%
    echo         Fix: pull latest Sanctum or restore automations\ from git.
    echo.
    pause
    exit /b 2
)

call "%V12_BAT%" %*
exit /b %ERRORLEVEL%
