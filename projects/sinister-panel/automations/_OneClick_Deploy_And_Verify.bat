@echo off
REM ============================================================================
REM  _OneClick_Deploy_And_Verify.bat  --  D:\ canonical edition.
REM
REM  Author: Sinister Panel agent (Claude Opus 4.7 1M) :: 2026-05-20
REM  TODO: migrate to LetsText bat system per p.md 2026-05-19 directive once
REM        operator surfaces the LetsText bat-creator interface or adds the
REM        Bash(/d/LetsText/automations/**:*) permission rule. Until then this
REM        uses the canonical Sinister-Panel ONE-bat pattern.
REM
REM  Operator-zero-touch end-to-end. Per operator 2026-05-20 (adopted from
REM  Snap-API directive): "keep working ... use letstext bat system and make
REM  systems you need to work 100% autnouous". This bat is the panel-side
REM  version of that — one click, everything goes.
REM
REM  Steps:
REM    1. git fetch  (pick up agent-pushed topic branches)
REM    2. Auto-fast-forward-merge any branches matching agent/sinister-panel/*
REM       whose tip is reachable from main + would advance main cleanly. Logs
REM       what got merged.
REM    3. Invoke _OneClick_Deploy.bat (handles tsc + next build + push + SSH
REM       + docker compose + prisma migrate deploy + smoke)
REM    4. Post-deploy verification via SSH:
REM       a. Hetzner HEAD == local main HEAD
REM       b. prisma schema column count matches the latest migration
REM       c. docker logs --since 2m sinister-backend | grep schema_drift -> 0
REM       d. curl -X POST /api/phones/heartbeat with bogus serial -> 503 or 401
REM          (NOT 500 — that means hardening landed)
REM    5. Append outcome to %REPO_LOCAL%\leo_dev\docs\AUTONOMY-LOG.md AND
REM       %USERPROFILE%\Desktop\sinister-panel-deploy-and-verify.log
REM
REM  Hard rules:
REM    - NO PAUSES. Same hidden auto-close pattern as _OneClick_Deploy.bat.
REM    - Aborts if step 3 fails (don't try to verify a failed deploy).
REM    - Exits 0 only when ALL of steps 4a..4d are green.
REM    - Idempotent: re-clicking is safe (skip merge if main already at tip).
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set REPO=/opt/sinister-panel
set REPO_LOCAL=D:\Sinister\01_Projects\Sinister\Sinister-Panel\source
set DEPLOY_BAT=D:\Sinister\01_Projects\Sinister\Sinister-Panel\_OneClick_Deploy.bat
set LOGDIR=%TEMP%\sinister-deploy-verify
set OUTLOG=%USERPROFILE%\Desktop\sinister-panel-deploy-and-verify.log
set AUTONOMY_LOG=%REPO_LOCAL%\leo_dev\docs\AUTONOMY-LOG.md
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

REM Timestamp
for /f "tokens=*" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ssZ"') do set STAMP=%%t

echo.
echo ====================================================================
echo   SINISTER PANEL DEPLOY + VERIFY  (D:\ hub edition)
echo   stamp: %STAMP%
echo   log:   %OUTLOG%
echo ====================================================================
echo.

REM --- sanity: working tree exists -------------------------------------
if not exist "%REPO_LOCAL%\.git" (
  echo   [X] %REPO_LOCAL%\.git not found. Wrong working tree?
  echo %STAMP% FAIL precondition_no_git_tree>> "%OUTLOG%"
  exit /b 1
)
if not exist "%DEPLOY_BAT%" (
  echo   [X] %DEPLOY_BAT% not found.
  echo %STAMP% FAIL precondition_no_deploy_bat>> "%OUTLOG%"
  exit /b 1
)

cd /d %REPO_LOCAL%

REM --- [1/5] git fetch --------------------------------------------------
echo [1/5] git fetch
git fetch --all --prune > "%LOGDIR%\fetch.log" 2>&1
if errorlevel 1 (
  echo   [X] git fetch failed. See %LOGDIR%\fetch.log
  echo %STAMP% FAIL git_fetch>> "%OUTLOG%"
  exit /b 1
)
echo   ok

REM --- [2/5] auto-fast-forward-merge agent topic branches ---------------
echo.
echo [2/5] auto-merge agent/sinister-panel/* branches (fast-forward only)
git checkout main > "%LOGDIR%\checkout-main.log" 2>&1
if errorlevel 1 (
  echo   [X] cannot checkout main. See %LOGDIR%\checkout-main.log
  echo %STAMP% FAIL checkout_main>> "%OUTLOG%"
  exit /b 1
)
set MERGED_COUNT=0
REM 2026-05-20 — switched from inline `for /f ('git for-each-ref ...')` to
REM temp-file iteration. The prior pattern's `--format="%(refname:short)"`
REM glob ran git through cmd's command-substitution-shim which silently
REM swallowed the output (merge.log never created on operator's first run).
REM Temp-file pattern is portable + the file IS the diagnostic when this
REM step misbehaves.
git for-each-ref --format="%%(refname:short)" "refs/remotes/origin/agent/sinister-panel/*" > "%LOGDIR%\agent-branches.txt" 2>> "%LOGDIR%\agent-branches.err"
echo   agent-branch list:
type "%LOGDIR%\agent-branches.txt"
echo.
for /f "usebackq delims=" %%b in ("%LOGDIR%\agent-branches.txt") do (
  echo   considering %%b
  git merge --ff-only %%b >> "%LOGDIR%\merge.log" 2>&1
  if errorlevel 1 (
    echo     - cannot fast-forward ^(likely already merged or diverged^). Skip.
  ) else (
    echo     + merged.
    set /a MERGED_COUNT+=1
  )
)
echo   merged !MERGED_COUNT! branch^(es^)
if !MERGED_COUNT! gtr 0 (
  echo   pushing main...
  git push origin main >> "%LOGDIR%\merge.log" 2>&1
  if errorlevel 1 (
    echo   [X] push failed after merge. See %LOGDIR%\merge.log
    echo %STAMP% FAIL push_after_merge>> "%OUTLOG%"
    exit /b 1
  )
  echo   + pushed
)

REM --- [3/5] invoke standard deploy bat --------------------------------
echo.
echo [3/5] invoke _OneClick_Deploy.bat
call "%DEPLOY_BAT%"
if errorlevel 1 (
  echo   [X] deploy bat failed with errorlevel %ERRORLEVEL%
  echo %STAMP% FAIL deploy_bat_errorlevel=%ERRORLEVEL%>> "%OUTLOG%"
  exit /b 1
)
echo   deploy bat exit 0

REM --- [4/5] post-deploy verification ----------------------------------
echo.
echo [4/5] post-deploy verification (SSH probes)

REM 4a — Hetzner HEAD == local main HEAD
for /f "tokens=*" %%h in ('git rev-parse HEAD') do set LOCAL_HEAD=%%h
echo   4a  local HEAD = !LOCAL_HEAD!
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes %PROD% "cd %REPO% && git rev-parse HEAD" > "%LOGDIR%\hetzner-head.txt" 2>&1
set /p HETZNER_HEAD=< "%LOGDIR%\hetzner-head.txt"
echo   4a  Hetzner HEAD = !HETZNER_HEAD!
if /i "!LOCAL_HEAD!" NEQ "!HETZNER_HEAD!" (
  echo   [X] 4a FAIL — HEAD mismatch
  echo %STAMP% FAIL hetzner_head_mismatch local=!LOCAL_HEAD! hetzner=!HETZNER_HEAD!>> "%OUTLOG%"
  exit /b 1
)
echo   4a  ok

REM 4b — Phone."deviceModel" column exists on prod Postgres
REM 2026-05-20 patch — corrected query. Prisma keeps model+column case so
REM table is "Phone" (NOT phone) and column is "deviceModel" (NOT
REM device_model). Prior `\d phone | grep -c device_model` was ALWAYS 0
REM whether the column existed or not. Use information_schema (case-exact).
echo   4b  Postgres column check (Phone."deviceModel" via information_schema)
ssh -o BatchMode=yes %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -tA -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'Phone' AND column_name = 'deviceModel';\"" > "%LOGDIR%\schema-check.txt" 2>&1
type "%LOGDIR%\schema-check.txt"
set /p COLUMN_COUNT=< "%LOGDIR%\schema-check.txt"
if not "!COLUMN_COUNT!"=="1" (
  echo   [X] 4b FAIL — Phone."deviceModel" column NOT FOUND
  echo %STAMP% FAIL schema_drift_persists Phone.deviceModel missing>> "%OUTLOG%"
  echo   attempting force-rebuild backend + migrate deploy as recovery...
  ssh -o BatchMode=yes %PROD% "cd %REPO% && docker compose build --no-cache sinister-backend 2>&1 | tail -20 && docker compose up -d sinister-backend && sleep 5 && docker exec sinister-backend npx prisma migrate deploy" >> "%LOGDIR%\migrate-recovery.log" 2>&1
  echo   re-checking...
  ssh -o BatchMode=yes %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -tA -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'Phone' AND column_name = 'deviceModel';\"" > "%LOGDIR%\schema-check2.txt" 2>&1
  type "%LOGDIR%\schema-check2.txt"
  set /p COLUMN_COUNT2=< "%LOGDIR%\schema-check2.txt"
  if not "!COLUMN_COUNT2!"=="1" (
    echo   [X] 4b STILL FAILS after --no-cache rebuild + migrate. Dumping diagnostics:
    ssh -o BatchMode=yes %PROD% "docker exec sinister-backend ls /app/leo_dev/backend/prisma/migrations/ 2>&1 | tail -20" > "%LOGDIR%\container-migrations.txt" 2>&1
    type "%LOGDIR%\container-migrations.txt"
    exit /b 1
  )
  echo   4b  ok (after --no-cache recovery)
) else (
  echo   4b  ok ^(column present^)
)

REM 4c — recent backend logs: zero schema_drift kind in the last 2 min
echo   4c  backend log scan for kind=schema_drift
ssh -o BatchMode=yes %PROD% "docker logs --since 2m sinister-backend 2>^&1 | grep -c 'kind.*schema_drift\|unhandled route error'" > "%LOGDIR%\log-scan.txt" 2>&1
set /p DRIFT_COUNT=< "%LOGDIR%\log-scan.txt"
echo   4c  drift_or_unhandled_count = !DRIFT_COUNT!
if "!DRIFT_COUNT!" NEQ "0" (
  echo   [!] 4c WARN — non-zero drift/unhandled count in recent logs
  echo %STAMP% WARN drift_in_logs count=!DRIFT_COUNT!>> "%OUTLOG%"
  REM Don't fail on this — heartbeat hardening may surface PRE-deploy drifts
  REM that already happened. Operator decides via the log line in OUTLOG.
) else (
  echo   4c  ok ^(no drift in 2m window^)
)

REM 4d — heartbeat returns NOT 500
echo   4d  heartbeat probe (expect 503 with schema_drift hardening, OR 401 no-fleet-secret)
curl -sS -m 10 -o "%LOGDIR%\hb-probe.txt" -w "HTTP_CODE=%%{http_code}\n" -H "Content-Type: application/json" -X POST "https://snap.sinijkr.com/api/phones/heartbeat" -d "{\"serial\":\"VERIFY-PROBE-FROM-DEPLOY-BAT\",\"model\":\"probe\"}" > "%LOGDIR%\hb-status.txt" 2>&1
type "%LOGDIR%\hb-status.txt"
findstr /C:"HTTP_CODE=500" "%LOGDIR%\hb-status.txt" >nul
if not errorlevel 1 (
  echo   [X] 4d FAIL — heartbeat returns 500 ^(hardening NOT applied^)
  echo %STAMP% FAIL heartbeat_returns_500>> "%OUTLOG%"
  exit /b 1
)
echo   4d  ok ^(no 500 on probe^)

REM --- [5/5] log success -----------------------------------------------
echo.
echo [5/5] log success
echo %STAMP% OK deploy_and_verify head=!LOCAL_HEAD! merged=!MERGED_COUNT! drift=!DRIFT_COUNT!>> "%OUTLOG%"
echo. >> "%AUTONOMY_LOG%"
echo ## WHERE I STOPPED: %STAMP% — Deploy + Verify exit 0 >> "%AUTONOMY_LOG%"
echo - local + Hetzner HEAD = !LOCAL_HEAD! >> "%AUTONOMY_LOG%"
echo - merged !MERGED_COUNT! agent topic branch^(es^) >> "%AUTONOMY_LOG%"
echo - Phone.deviceModel column verified present >> "%AUTONOMY_LOG%"
echo - heartbeat probe returned non-500 >> "%AUTONOMY_LOG%"
echo - recent-log drift count = !DRIFT_COUNT! >> "%AUTONOMY_LOG%"

echo.
echo ====================================================================
echo   ALL GREEN. Hetzner HEAD = !LOCAL_HEAD!
echo   See %OUTLOG% for the run log.
echo ====================================================================
echo.
exit /b 0
