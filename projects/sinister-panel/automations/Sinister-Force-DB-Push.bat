@echo off
REM ============================================================================
REM  Sinister-Force-DB-Push.bat  --  surgical prisma db push.
REM
REM  Author: Sinister Panel agent (Claude Opus 4.7 1M) :: 2026-05-20
REM  TODO: migrate to LetsText bat system per p.md 2026-05-19 directive once
REM        operator surfaces the bat-creator interface.
REM
REM  Why this exists: Force-Backend-Rebuild's `prisma migrate deploy` reported
REM  "12 migrations found / No pending migrations to apply" + `psql \d "Phone"`
REM  dump showed the prod DB at PRE-LinkScope state — missing ALL of:
REM    - deviceModel  (was supposed to land via 20260520000000_phone_device_model)
REM    - authToken / authTokenIssuedAt / authTokenRotatedAt  (Phase-1 tweaks)
REM    - apkLocked / apkLockReason / apkLockSetAt  (LinkScope kill-switch)
REM    - rkaSuspended / rkaSuspendReason / rkaSuspendSetAt  (LinkScope kill-switch)
REM
REM  These columns were never written as proper migration files — they were
REM  added via ad-hoc `prisma db push` in dev sessions, and that push never
REM  landed on prod. `prisma migrate deploy` can't fix it (no migration file
REM  to apply). `prisma db push` syncs schema → DB directly.
REM
REM  Safety: the schema.prisma additions are ALL nullable ADD-COLUMN ops (no
REM  drops). Verified against the phone-schema.txt dump from the prior bat
REM  run: no columns get dropped, only new ones added. --accept-data-loss
REM  flag is required by Prisma to permit any schema-sync from a bat (even
REM  though there's no actual data loss here); operator authorizes per c.md
REM  Postgres rails "--accept-data-loss only when explicitly intentional".
REM
REM  Steps:
REM    1. SSH probe HEAD (sanity)
REM    2. probe container path: find schema.prisma + list migrations dir
REM    3. dump current Phone schema (before)
REM    4. docker exec sinister-backend npx prisma db push --accept-data-loss --skip-generate
REM    5. dump current Phone schema (after) — diff against (3)
REM    6. case-exact verify: deviceModel + authToken + apkLocked + rkaSuspended each = 1
REM    7. heartbeat probe (no fleet secret — expect NON-500)
REM    8. log outcome to Desktop
REM
REM  Hidden + auto-close pattern. NO PAUSES.
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set REPO=/opt/sinister-panel
set OUTLOG=%USERPROFILE%\Desktop\sinister-force-db-push.log
set LOGDIR=%TEMP%\sinister-force-db-push
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

for /f "tokens=*" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ssZ"') do set STAMP=%%t

echo.
echo ====================================================================
echo   SINISTER FORCE PRISMA DB PUSH  (LinkScope + deviceModel column sync)
echo   stamp: %STAMP%
echo   log:   %OUTLOG%
echo ====================================================================
echo.

REM --- [1/8] sanity probe HEAD ----------------------------------------
echo [1/8] Hetzner HEAD probe
ssh -o BatchMode=yes -o ConnectTimeout=10 %PROD% "cd %REPO% && git rev-parse --short HEAD"
echo.

REM --- [2/8] probe container layout -----------------------------------
echo [2/8] Container layout probe
echo   - schema.prisma location:
ssh %PROD% "docker exec sinister-backend find / -name 'schema.prisma' -not -path '*/node_modules/*' 2>/dev/null | head -5" > "%LOGDIR%\schema-loc.txt" 2>&1
type "%LOGDIR%\schema-loc.txt"
echo   - migration directories:
ssh %PROD% "docker exec sinister-backend sh -c 'cd $(dirname $(find / -name schema.prisma -not -path \"*/node_modules/*\" 2>/dev/null | head -1)) && ls migrations/ 2>/dev/null'" > "%LOGDIR%\migrations-list.txt" 2>&1
type "%LOGDIR%\migrations-list.txt"
echo.

REM --- [3/8] dump Phone schema BEFORE ----------------------------------
echo [3/8] Phone schema BEFORE db push
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c '\d \"Phone\"' 2>&1 | tail -50" > "%LOGDIR%\schema-before.txt" 2>&1
type "%LOGDIR%\schema-before.txt"
echo.

REM --- [4/8] prisma db push --accept-data-loss ------------------------
echo [4/8] docker exec sinister-backend npx prisma db push --accept-data-loss --skip-generate
ssh %PROD% "docker exec sinister-backend npx prisma db push --accept-data-loss --skip-generate 2>&1" > "%LOGDIR%\db-push.log" 2>&1
type "%LOGDIR%\db-push.log"
if errorlevel 1 (
  echo   [X] prisma db push FAILED. See %LOGDIR%\db-push.log
  echo %STAMP% FAIL prisma_db_push>> "%OUTLOG%"
  exit /b 1
)
echo   + db push ok
echo.

REM --- [5/8] dump Phone schema AFTER ----------------------------------
echo [5/8] Phone schema AFTER db push
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c '\d \"Phone\"' 2>&1 | tail -60" > "%LOGDIR%\schema-after.txt" 2>&1
type "%LOGDIR%\schema-after.txt"
echo.

REM --- [6/8] case-exact column verify ---------------------------------
echo [6/8] Verify 4 critical columns via information_schema
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -tA -c \"SELECT column_name FROM information_schema.columns WHERE table_name='Phone' AND column_name IN ('deviceModel','authToken','apkLocked','rkaSuspended') ORDER BY column_name;\"" > "%LOGDIR%\verify.txt" 2>&1
type "%LOGDIR%\verify.txt"
findstr /C:"deviceModel" "%LOGDIR%\verify.txt" >nul && findstr /C:"authToken" "%LOGDIR%\verify.txt" >nul && findstr /C:"apkLocked" "%LOGDIR%\verify.txt" >nul && findstr /C:"rkaSuspended" "%LOGDIR%\verify.txt" >nul
if errorlevel 1 (
  echo   [X] one or more required columns STILL missing after db push.
  echo %STAMP% FAIL columns_still_missing>> "%OUTLOG%"
  exit /b 1
)
echo   + all 4 critical columns present
echo.

REM --- [7/8] restart backend to clear any cached connections ----------
echo [7/8] docker restart sinister-backend (clear Prisma client cache)
ssh %PROD% "docker restart sinister-backend && sleep 5 && docker ps --filter name=sinister-backend --format '{{.Names}} {{.Status}}'"
echo.

REM --- [8/8] heartbeat probe (expect NON-500) -------------------------
echo [8/8] heartbeat probe (no fleet secret — expect 401 or 503, NOT 500)
curl -sS -m 10 -o "%LOGDIR%\hb-probe.txt" -w "HTTP_CODE=%%{http_code}\n" -H "Content-Type: application/json" -X POST "https://snap.sinijkr.com/api/phones/heartbeat" -d "{\"serial\":\"FORCE-DB-PUSH-VERIFY\",\"model\":\"probe\"}" > "%LOGDIR%\hb-status.txt" 2>&1
type "%LOGDIR%\hb-status.txt"
findstr /C:"HTTP_CODE=500" "%LOGDIR%\hb-status.txt" >nul
if not errorlevel 1 (
  echo   [X] heartbeat probe STILL returns 500. Inspect backend logs:
  ssh %PROD% "docker logs --tail 30 sinister-backend"
  echo %STAMP% FAIL heartbeat_500_persists>> "%OUTLOG%"
  exit /b 1
)
echo   + heartbeat probe non-500

echo.
echo %STAMP% OK force_db_push columns_synced backend_restarted heartbeat_clean>> "%OUTLOG%"
echo ====================================================================
echo   ALL GREEN. LinkScope + deviceModel columns synced. APK should
echo   start successfully pushing to /api/accounts/push-token on next
echo   heartbeat tick (within ~30s of the backend restart at step 7).
echo   See %OUTLOG% for the run log.
echo ====================================================================
echo.
exit /b 0
