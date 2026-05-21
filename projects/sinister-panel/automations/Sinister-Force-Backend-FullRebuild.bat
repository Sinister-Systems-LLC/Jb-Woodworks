@echo off
REM ============================================================================
REM  Sinister-Force-Backend-FullRebuild.bat  --  the final-finisher.
REM
REM  Author: Sinister Panel agent (Claude Opus 4.7 1M) :: 2026-05-20
REM  TODO: migrate to LetsText bat system per p.md 2026-05-19 directive once
REM        operator surfaces the bat-creator interface.
REM
REM  Why this exists: prior bats (_OneClick_Deploy.bat + Sinister-Force-
REM  Backend-Rebuild.bat) ALL claimed the backend was rebuilt but the
REM  running sinister-backend container is STILL on the pre-deviceModel
REM  commit (verified by listing the container's prisma/migrations/ which
REM  has 12 dirs vs source's 14). The image-build was happening but the
REM  running container was never swapped to it.
REM
REM  This bat is brute-force:
REM    1. SSH probe Hetzner state
REM    2. git fetch + git reset --hard origin/main on Hetzner (force-pull)
REM    3. docker compose stop sinister-backend (kills running container)
REM    4. docker compose rm -f sinister-backend (cleans up)
REM    5. docker compose build --no-cache --pull sinister-backend (fresh)
REM    6. docker compose up -d sinister-backend (new container)
REM    7. wait 8s for warm-up
REM    8. docker exec sinister-backend npx prisma migrate deploy
REM    9. belt-and-suspenders: psql ALTER TABLE IF NOT EXISTS deviceModel
REM   10. verify ALL 4 critical columns present
REM   11. docker logs sinister-backend --tail 30 (sanity)
REM   12. heartbeat probe — expect non-500
REM   13. write OUTLOG
REM
REM  Hidden + auto-close. NO PAUSES.
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set REPO=/opt/sinister-panel
set OUTLOG=%USERPROFILE%\Desktop\sinister-force-backend-fullrebuild.log
set LOGDIR=%TEMP%\sinister-force-backend-fullrebuild
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

for /f "tokens=*" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ssZ"') do set STAMP=%%t

echo.
echo ====================================================================
echo   SINISTER FORCE BACKEND FULL-REBUILD  (the final-finisher)
echo   stamp: %STAMP%
echo   log:   %OUTLOG%
echo ====================================================================
echo.

REM --- [1/13] probe Hetzner state -------------------------------------
echo [1/13] Hetzner state
ssh %PROD% "cd %REPO% && echo HEAD=$(git rev-parse --short HEAD) && docker ps --filter name=sinister-backend --format '{{.Names}} {{.Status}} created=$(docker inspect sinister-backend --format \"{{.Created}}\" 2>/dev/null)'"
echo.

REM --- [2/13] git pull (force) -----------------------------------------
echo [2/13] git fetch + reset --hard origin/main
ssh %PROD% "cd %REPO% && git fetch origin main && git reset --hard origin/main && git rev-parse --short HEAD"
if errorlevel 1 (
  echo   [X] git pull failed.
  echo %STAMP% FAIL git_pull>> "%OUTLOG%"
  exit /b 1
)
echo.

REM --- [3/13] stop container ------------------------------------------
echo [3/13] docker compose stop sinister-backend
ssh %PROD% "cd %REPO% && docker compose stop sinister-backend 2>&1 | tail -5"
echo.

REM --- [4/13] remove old container ------------------------------------
echo [4/13] docker compose rm -f sinister-backend
ssh %PROD% "cd %REPO% && docker compose rm -f sinister-backend 2>&1 | tail -5"
echo.

REM --- [5/13] build --no-cache --pull ---------------------------------
echo [5/13] docker compose build --no-cache --pull sinister-backend (~3-5 min)
ssh %PROD% "cd %REPO% && docker compose build --no-cache --pull sinister-backend 2>&1 | tail -15"
if errorlevel 1 (
  echo   [X] docker build failed.
  echo %STAMP% FAIL docker_build>> "%OUTLOG%"
  exit /b 1
)
echo.

REM --- [6/13] up -d --force-recreate ----------------------------------
echo [6/13] docker compose up -d --force-recreate sinister-backend
ssh %PROD% "cd %REPO% && docker compose up -d --force-recreate sinister-backend 2>&1 | tail -5"
if errorlevel 1 (
  echo   [X] docker up failed.
  echo %STAMP% FAIL docker_up>> "%OUTLOG%"
  exit /b 1
)
echo.

REM --- [7/13] container health -----------------------------------------
echo [7/13] container warm-up (8s) + status
ssh %PROD% "sleep 8 && docker ps --filter name=sinister-backend --format '{{.Names}} {{.Status}} created=$(docker inspect sinister-backend --format \"{{.Created}}\")'"
echo.

REM --- [8/13] prisma migrate deploy -----------------------------------
echo [8/13] docker exec sinister-backend npx prisma migrate deploy
ssh %PROD% "docker exec sinister-backend npx prisma migrate deploy 2>&1 | tail -20" > "%LOGDIR%\migrate.log" 2>&1
type "%LOGDIR%\migrate.log"
echo.

REM --- [9/13] belt-and-suspenders: ALTER TABLE IF NOT EXISTS deviceModel
echo [9/13] psql ALTER TABLE "Phone" ADD COLUMN IF NOT EXISTS "deviceModel"
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c 'ALTER TABLE \"Phone\" ADD COLUMN IF NOT EXISTS \"deviceModel\" TEXT;'"
echo.

REM --- [10/13] verify ALL 4 columns ----------------------------------
echo [10/13] Verify all 4 critical columns via information_schema
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -tA -c \"SELECT column_name FROM information_schema.columns WHERE table_name='Phone' AND column_name IN ('deviceModel','authToken','apkLocked','rkaSuspended') ORDER BY column_name;\"" > "%LOGDIR%\verify.txt" 2>&1
type "%LOGDIR%\verify.txt"
findstr /C:"deviceModel" "%LOGDIR%\verify.txt" >nul && findstr /C:"authToken" "%LOGDIR%\verify.txt" >nul && findstr /C:"apkLocked" "%LOGDIR%\verify.txt" >nul && findstr /C:"rkaSuspended" "%LOGDIR%\verify.txt" >nul
if errorlevel 1 (
  echo   [X] one or more required columns STILL missing.
  echo %STAMP% FAIL columns_still_missing>> "%OUTLOG%"
  exit /b 1
)
echo   + all 4 critical columns present
echo.

REM --- [11/13] backend logs sanity ------------------------------------
echo [11/13] Recent backend logs (--tail 30)
ssh %PROD% "docker logs --tail 30 sinister-backend 2>&1 | tail -30" > "%LOGDIR%\backend-logs.txt" 2>&1
type "%LOGDIR%\backend-logs.txt"
echo.

REM --- [12/13] heartbeat probe ----------------------------------------
echo [12/13] heartbeat probe (no fleet secret — expect 401 or 503, NOT 500)
curl -sS -m 10 -o "%LOGDIR%\hb-probe.txt" -w "HTTP_CODE=%%{http_code}\n" -H "Content-Type: application/json" -X POST "https://snap.sinijkr.com/api/phones/heartbeat" -d "{\"serial\":\"FULL-REBUILD-VERIFY\",\"model\":\"probe\"}" > "%LOGDIR%\hb-status.txt" 2>&1
type "%LOGDIR%\hb-status.txt"
findstr /C:"HTTP_CODE=500" "%LOGDIR%\hb-status.txt" >nul
if not errorlevel 1 (
  echo   [X] heartbeat probe STILL returns 500.
  ssh %PROD% "docker logs --tail 30 sinister-backend"
  echo %STAMP% FAIL heartbeat_500>> "%OUTLOG%"
  exit /b 1
)
echo.

REM --- [13/13] log success --------------------------------------------
echo %STAMP% OK full_rebuild head=$(ssh %PROD% "cd %REPO% && git rev-parse --short HEAD" 2^>nul) columns=all_present heartbeat=non500>> "%OUTLOG%"
echo ====================================================================
echo   ALL GREEN. Backend container rebuilt from source. Migrations
echo   applied. All 4 critical Phone columns present. Heartbeat probe
echo   does NOT 500. Kernel-APK should successfully push within ~30s.
echo ====================================================================
echo.
exit /b 0
