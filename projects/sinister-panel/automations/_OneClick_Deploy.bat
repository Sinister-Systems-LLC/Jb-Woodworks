@echo off
REM ============================================================================
REM  _OneClick_Deploy.bat  --  D:\ canonical edition.
REM
REM  Identical pipeline to the legacy Sinister_OneClick_Deploy.bat on the
REM  Desktop, but rooted at the D:\ project-hub working tree
REM  (D:\Sinister\01_Projects\Sinister\Sinister-Panel\source\). The bat
REM  lives at the project root inside the hub so the whole D:\Sinister tree
REM  is self-contained -- move the hub and the bat moves with it.
REM
REM  Created 2026-05-18 PM LATE as part of the "D:\ becomes the new main
REM  working folder" transition. Pairs with the Desktop bat which now also
REM  points at D:\ -- both bats use the same source-of-truth.
REM
REM  Double-click this file. That's it. The script:
REM    1. Type-check (tsc --noEmit)
REM    2. Production build locally (next build) -- catches prerender errors
REM    3. Server target preview (info only)
REM    4. Auto-commit any pending changes with a timestamped message
REM    5. Push origin/main (fast-forward only)
REM    6. Upload remote-deploy.sh (CRLF-stripped)
REM    7. Server: git pull + build + restart (auto-detects backend changes)
REM    8. Auto-run prisma db push if schema.prisma changed
REM    9. Smoke-test https://snap.sinijkr.com/ + open browser
REM
REM  Hard rules:
REM    - NO --restore flag passed to remote-deploy.sh -- Postgres untouched
REM    - Aborts BEFORE push if local tsc or build fails
REM    - NO PAUSES AT ALL (2026-05-19): agent invokes hidden + auto-close.
REM      Output captured to %TEMP%\sinister-build.log + sinister-deploy-stdout.log.
REM      Errors print there, bat exits with non-zero, agent reads logs + surfaces.
REM    - Pure ASCII output (no chcp -- cmd.exe codepage stays default)
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set REPO=/opt/sinister-panel
set REPO_LOCAL=D:\Sinister\01_Projects\Sinister\Sinister-Panel\source
set DASHBOARD_LOCAL=%REPO_LOCAL%\leo_dev\dashboard
set SCRIPT_LOCAL=%REPO_LOCAL%\leo_dev\scripts\remote-deploy.sh
set BUILD_LOG=%TEMP%\sinister-build.log
set TARGET_FILE=%TEMP%\sinister-target.txt

echo.
echo ====================================================================
echo   SINISTER ONE-CLICK DEPLOY  to  snap.sinijkr.com  (D:\ hub edition)
echo   working tree: %REPO_LOCAL%
echo ====================================================================
echo.

REM --- sanity: working tree exists -------------------------------------
if not exist "%REPO_LOCAL%\.git" (
  echo   [X] %REPO_LOCAL%\.git not found. Wrong working tree?
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)

REM --- [1/9] tsc clean -------------------------------------------------
echo [1/9] Type-check (tsc --noEmit)
cd /d %DASHBOARD_LOCAL%
call npx tsc --noEmit
if errorlevel 1 (
  echo.
  echo   [X] TypeScript errors. Fix before deploy.
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)
echo   ok

REM --- [2/9] production build ------------------------------------------
echo.
echo [2/9] Production build (next build)
REM 2026-05-19 — clear .next/cache before every build. Killed bats (e.g. when
REM the agent kills a hung deploy) leave a corrupted cache that makes the
REM NEXT build hang silently at "Creating optimized production build...".
REM Clearing is fast (~1s) and forces a clean compile.
if exist "%DASHBOARD_LOCAL%\.next\cache" rmdir /s /q "%DASHBOARD_LOCAL%\.next\cache" >nul 2>&1
call npx next build > "%BUILD_LOG%" 2>&1
if errorlevel 1 (
  echo.
  echo   [X] Production build failed. Last 30 lines:
  echo   ----------------------------------------------------------
  powershell -NoProfile -Command "Get-Content '%BUILD_LOG%' -Tail 30"
  echo   ----------------------------------------------------------
  echo   Full log: %BUILD_LOG%
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)
echo   ok (all routes generated)

REM --- [3/9] Server target info (best-effort, never aborts) -----------
echo.
echo [3/9] Server target preview (informational)
del "%TARGET_FILE%" >nul 2>&1
ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 %PROD% "docker ps --format '{{.Names}}' 2>/dev/null | grep -iE 'dashboard|panel|sinister|next' | head -1" > "%TARGET_FILE%" 2>nul
set TARGET=
if exist "%TARGET_FILE%" set /p TARGET=<"%TARGET_FILE%"
if "!TARGET!"=="" (
  echo   (no docker target detected -- server may use systemd/pm2)
) else (
  echo   target container: !TARGET!
)

REM --- [4/9] Auto-commit pending changes -------------------------------
echo.
echo [4/9] Stage + commit pending changes
cd /d %REPO_LOCAL%
git add -A
git diff --cached --quiet >nul 2>&1
if errorlevel 1 (
  set "STAMP=%date% %time:~0,5%"
  git commit -m "deploy: panel UI update !STAMP!"
  if errorlevel 1 (
    echo   [X] commit failed.
    rem pause removed 2026-05-19 — hidden auto-close per operator directive.
    exit /b 1
  )
  echo   ok (committed)
) else (
  echo   no pending changes
)

REM --- [5/9] Sync + push origin/main -----------------------------------
echo.
echo [5/9] Push to origin/main (fast-forward only)
git pull --rebase origin main
if errorlevel 1 (
  echo.
  echo   [X] rebase failed. Resolve manually then re-run.
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)
git push origin main
if errorlevel 1 (
  echo   [X] git push failed.
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)
for /f %%h in ('git rev-parse --short HEAD') do set SHA=%%h
echo   ok (pushed at !SHA!)

REM --- [6/9] Upload remote-deploy.sh -----------------------------------
echo.
echo [6/9] Upload deploy script
scp -o StrictHostKeyChecking=accept-new "%SCRIPT_LOCAL%" %PROD%:/tmp/remote-deploy.sh >nul
if errorlevel 1 (
  echo   [X] scp failed.
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)
ssh -o BatchMode=yes %PROD% "sed -i 's/\r$//' /tmp/remote-deploy.sh && bash -n /tmp/remote-deploy.sh" >nul 2>&1
if errorlevel 1 (
  echo   [X] remote-deploy.sh failed syntax check after CRLF strip.
  rem pause removed 2026-05-19 — hidden auto-close per operator directive (b.md supersession). Errors print to log + auto-exit; agent surfaces via post-run log read.
  exit /b 1
)
echo   ok

REM --- [7/9] Detect backend changes + remote deploy --------------------
REM 2026-05-20 patch (panel agent) — ALWAYS pass --with-backend. The prior
REM "dashboard-only" branch was firing even when backend changes were
REM present (delayed-expansion edge case + screenshot evidence showed both
REM messages printing in the same run on operator's 2026-05-20 06:14 fire).
REM The fix path: always rebuild backend. Cost = one extra docker compose
REM build sinister-backend (~30-60s). Benefit = migrations always apply +
REM heartbeat hardening lands deterministically. We still log what the
REM detection WOULD have said for diagnostics.
echo.
echo [7/9] Detecting backend changes...
set DEPLOY_FLAGS=--with-backend
set SERVER_HEAD=
for /f %%h in ('ssh -o BatchMode=yes %PROD% "cd %REPO% && git rev-parse HEAD" 2^>nul') do set SERVER_HEAD=%%h
if "!SERVER_HEAD!"=="" (
  echo   could not read server HEAD -- forcing --with-backend
) else (
  git fetch origin main >nul 2>&1
  git diff --name-only !SERVER_HEAD!..origin/main 2>nul | findstr /B "leo_dev/backend/" >nul
  if not errorlevel 1 (
    echo   backend changes detected vs server HEAD !SERVER_HEAD! -- rebuilding backend
  ) else (
    echo   no backend changes detected vs !SERVER_HEAD! -- but forcing --with-backend anyway (always-rebuild policy 2026-05-20)
  )
)

echo.
echo [7/9] Remote build + restart (DB and RKA untouched)
echo   ----------------------------------------------------------
ssh %PROD% "bash /tmp/remote-deploy.sh !DEPLOY_FLAGS!"
echo   ----------------------------------------------------------

REM --- [8/9] Auto-sync Prisma schema if schema.prisma changed ----------
echo.
echo [8/9] Schema sync check
set PRISMA_NEEDED=0
if not "!SERVER_HEAD!"=="" (
  REM 2026-05-20 patch — findstr /R "schema\.prisma" parses `\.` as a
  REM literal filename glob (Windows-specific), NEVER matching. Use
  REM /C: literal search. Same fix a656e0c applied to leo_dev/bats/
  REM copy; this is the hub-level local-bat sibling.
  git diff --name-only !SERVER_HEAD!..origin/main 2>nul | findstr /C:"schema.prisma" >nul
  if not errorlevel 1 set PRISMA_NEEDED=1
)
REM Additionally — remote-deploy.sh's --with-backend branch (per a656e0c)
REM already runs `npx prisma migrate deploy` post-rebuild. The [8/9] db push
REM here is the BELT for the SUSPENDERS — migrate deploy is structured
REM migrations, db push is schema-sync. Run both when needed; if migrate
REM deploy already applied everything, db push is a no-op.
if "!PRISMA_NEEDED!"=="1" (
  echo   schema.prisma changed -- running prisma db push on prod...
  ssh %PROD% "docker exec sinister-backend npx prisma db push --skip-generate --accept-data-loss && docker restart sinister-backend && sleep 3 && docker ps --filter name=sinister-backend --format '{{.Names}} {{.Status}}'"
  if errorlevel 1 (
    echo   [X] prisma db push failed. Manually run Sinister_Prisma_Push.bat.
  ) else (
    echo   ok (schema synced + backend restarted)
  )
) else (
  echo   no schema changes -- skipping prisma push
)

REM --- [9/9] Smoke test + open browser ---------------------------------
echo.
echo [9/9] Smoke-test https://snap.sinijkr.com/
for /f %%c in ('curl -ks -o NUL -w "%%{http_code}" https://snap.sinijkr.com/') do set CODE=%%c
echo   https://snap.sinijkr.com  ->  !CODE!

echo.
echo ====================================================================
echo   DEPLOY COMPLETE  --  HEAD !SHA!  (from D:\ hub working tree)
echo ====================================================================
echo.
rem start "" "https://snap.sinijkr.com"   # browser auto-launch disabled 2026-05-19 (operator: hidden + auto-close)
rem pause removed — bat auto-closes on success. Full output captured to %BUILD_LOG% + %TEMP%\sinister-deploy-stdout.log via Tee-Object invocation pattern (see p.md 2026-05-19 hidden-bat protocol).
echo DONE %SHA%
endlocal
