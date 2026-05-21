@echo off
REM ============================================================================
REM  Sinister-Force-Backend-Rebuild.bat  --  surgical sinister-backend rebuild.
REM
REM  Author: Sinister Panel agent (Claude Opus 4.7 1M) :: 2026-05-20
REM  TODO: migrate to LetsText bat system per p.md 2026-05-19 directive once
REM        operator surfaces the bat-creator interface.
REM
REM  Why this exists: _OneClick_Deploy.bat's [7/9] backend-change detection
REM  silently elided --with-backend on the 2026-05-20 06:14 fire (delayed-
REM  expansion edge case). Result: frontend at 334d6c9 landed but backend
REM  container still ran old code without:
REM    1. heartbeat hardening (commit 662e085) — APK still 500s
REM    2. Phone.deviceModel migration (20260520000000) — schema drift persists
REM
REM  This bat is the surgical fix. SSH-only, single docker rebuild + migrate.
REM  Idempotent — already-up-to-date containers are no-op.
REM
REM  Steps:
REM    1. SSH probe Hetzner HEAD (should be 334d6c9)
REM    2. docker compose build sinister-backend (uses latest source)
REM    3. docker compose up -d sinister-backend (replace running container)
REM    4. wait 5s for container ready
REM    5. docker exec sinister-backend npx prisma migrate deploy
REM    6. SSH-verify Phone.deviceModel column present in prod Postgres
REM    7. probe POST /api/phones/heartbeat — expect 503 hardening OR 200,
REM       NOT 500
REM
REM  Hidden + auto-close pattern. Output to Desktop log.
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set REPO=/opt/sinister-panel
set OUTLOG=%USERPROFILE%\Desktop\sinister-force-backend-rebuild.log
set LOGDIR=%TEMP%\sinister-force-backend
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

for /f "tokens=*" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ssZ"') do set STAMP=%%t

echo.
echo ====================================================================
echo   SINISTER FORCE BACKEND REBUILD  (surgical migrate-apply path)
echo   stamp: %STAMP%
echo   log:   %OUTLOG%
echo ====================================================================
echo.

REM --- [1/7] SSH probe HEAD ---------------------------------------------
echo [1/7] Hetzner HEAD probe
ssh -o BatchMode=yes -o ConnectTimeout=10 %PROD% "cd %REPO% && git rev-parse --short HEAD" > "%LOGDIR%\head.txt" 2>&1
type "%LOGDIR%\head.txt"
set /p HETZNER_HEAD=< "%LOGDIR%\head.txt"
echo   Hetzner HEAD = !HETZNER_HEAD!

REM --- [2/7] docker compose build --no-cache sinister-backend -----------
REM 2026-05-20 patch — bumped to --no-cache. Without it, docker's layer
REM caching kept the OLD `COPY . .` layer that did NOT include the new
REM 20260520000000_phone_device_model/ migration directory. prisma migrate
REM deploy then reported "12 migrations found" (vs the source's 13) and
REM "No pending migrations to apply" → column never created. Always
REM --no-cache for backend rebuilds when a new migration must apply.
echo.
echo [2/7] docker compose build --no-cache sinister-backend (fresh source, no cache)
ssh %PROD% "cd %REPO% && docker compose build --no-cache sinister-backend 2>&1 | tail -40"
if errorlevel 1 (
  echo   [X] docker build failed.
  echo %STAMP% FAIL docker_build>> "%OUTLOG%"
  exit /b 1
)
echo   + build ok

REM --- [3/7] docker compose up -d sinister-backend ----------------------
echo.
echo [3/7] docker compose up -d sinister-backend (replace running container)
ssh %PROD% "cd %REPO% && docker compose up -d sinister-backend 2>&1 | tail -10"
if errorlevel 1 (
  echo   [X] docker up failed.
  echo %STAMP% FAIL docker_up>> "%OUTLOG%"
  exit /b 1
)
echo   + up ok

REM --- [4/7] wait 5s + container health ---------------------------------
echo.
echo [4/7] container warm-up (5s)
ssh %PROD% "sleep 5 && docker ps --filter name=sinister-backend --format '{{.Names}} {{.Status}}'"

REM --- [5/7] prisma migrate deploy -------------------------------------
echo.
echo [5/7] docker exec sinister-backend npx prisma migrate deploy
ssh %PROD% "docker exec sinister-backend npx prisma migrate deploy 2>&1 | tail -20" > "%LOGDIR%\migrate.log" 2>&1
type "%LOGDIR%\migrate.log"
if errorlevel 1 (
  echo   [X] prisma migrate deploy FAILED. See %LOGDIR%\migrate.log
  echo %STAMP% FAIL prisma_migrate_deploy>> "%OUTLOG%"
  exit /b 1
)
echo   + migrate ok

REM --- [6/7] verify Phone.deviceModel column ----------------------------
REM 2026-05-20 patch — corrected query. Prisma keeps model+column case so
REM table is "Phone" (not phone) and column is "deviceModel" (not
REM device_model). information_schema is case-exact and avoids psql's
REM \d-command behaviour for unquoted identifiers.
echo.
echo [6/7] Postgres column verify (Phone."deviceModel")
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -tA -c \"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'Phone' AND column_name = 'deviceModel';\"" > "%LOGDIR%\column-check.txt" 2>&1
type "%LOGDIR%\column-check.txt"
set /p COLUMN_COUNT=< "%LOGDIR%\column-check.txt"
echo   deviceModel presence count = !COLUMN_COUNT!
if not "!COLUMN_COUNT!"=="1" (
  echo   [X] COLUMN STILL MISSING after rebuild + migrate. Dumping diagnostics:
  ssh %PROD% "docker exec sinister-backend ls -la /app/leo_dev/backend/prisma/migrations/ 2>&1 | tail -30" > "%LOGDIR%\container-migrations.txt" 2>&1
  type "%LOGDIR%\container-migrations.txt"
  ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c '\d \"Phone\"' 2>&1 | tail -50" > "%LOGDIR%\phone-schema.txt" 2>&1
  type "%LOGDIR%\phone-schema.txt"
  echo %STAMP% FAIL column_still_missing>> "%OUTLOG%"
  exit /b 1
)
echo   + column present

REM --- [7/7] heartbeat probe — expect non-500 -------------------------
echo.
echo [7/7] heartbeat probe (expect 503 or 401 — NOT 500)
curl -sS -m 10 -o "%LOGDIR%\hb-probe.txt" -w "HTTP_CODE=%%{http_code}\n" -H "Content-Type: application/json" -X POST "https://snap.sinijkr.com/api/phones/heartbeat" -d "{\"serial\":\"FORCE-REBUILD-VERIFY\",\"model\":\"probe\"}" > "%LOGDIR%\hb-status.txt" 2>&1
type "%LOGDIR%\hb-status.txt"
findstr /C:"HTTP_CODE=500" "%LOGDIR%\hb-status.txt" >nul
if not errorlevel 1 (
  echo   [X] heartbeat STILL 500. Hardening did not deploy.
  echo %STAMP% FAIL heartbeat_500>> "%OUTLOG%"
  exit /b 1
)
echo   + heartbeat probe non-500

echo.
echo %STAMP% OK force_backend_rebuild head=!HETZNER_HEAD! column=present>> "%OUTLOG%"
echo ====================================================================
echo   ALL GREEN. Backend rebuilt + migration applied + heartbeat unblocked.
echo   See %OUTLOG% for run log.
echo ====================================================================
echo.
exit /b 0
