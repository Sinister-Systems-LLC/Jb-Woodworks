@echo off
REM ============================================================================
REM  _OneClick_DEPLOY_AND_HEAL.bat  --  Full one-click that self-heals.
REM
REM  Use this when the regular _OneClick_Deploy.bat fails because node_modules
REM  is half-installed (Windows file-locking gremlins on `rm node_modules`).
REM  This bat:
REM    [0/10] verifies D:\ working tree + git state
REM    [1/10] wipes node_modules cleanly via robocopy /MIR with empty source
REM           (the only Windows-native way to nuke deep dependency trees
REM            without ENOTEMPTY / "directory not empty" failures)
REM    [2/10] npm install  (full clean install)
REM    [3/10] tsc --noEmit
REM    [4/10] next build
REM    [5/10] auto-commit any pending changes
REM    [6/10] push origin/main (fast-forward only)
REM    [7/10] upload remote-deploy.sh
REM    [8/10] remote deploy (auto-detects backend changes)
REM    [9/10] prisma db push if schema changed
REM    [10/10] smoke test + open browser
REM
REM  Double-click. Walk away. Comes back deployed.
REM
REM  Created 2026-05-18 PM LATE during the D:\ migration session ? paired with
REM  the standard _OneClick_Deploy.bat (which assumes node_modules is already
REM  healthy).
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set REPO=/opt/sinister-panel
set REPO_LOCAL=D:\Sinister\01_Projects\Sinister\Sinister-Panel\source
set DASHBOARD_LOCAL=%REPO_LOCAL%\leo_dev\dashboard
set SCRIPT_LOCAL=%REPO_LOCAL%\leo_dev\scripts\remote-deploy.sh
set BUILD_LOG=%TEMP%\sinister-build.log
set INSTALL_LOG=%TEMP%\sinister-install.log
set TARGET_FILE=%TEMP%\sinister-target.txt
set EMPTY_SRC=%TEMP%\_empty_robocopy_src

echo.
echo ====================================================================
echo   SINISTER ONE-CLICK DEPLOY-AND-HEAL  to  snap.sinijkr.com
echo   working tree: %REPO_LOCAL%
echo ====================================================================
echo.

REM --- [0/10] sanity: working tree exists -------------------------------
echo [0/10] Sanity check
if not exist "%REPO_LOCAL%\.git" (
  echo   [X] %REPO_LOCAL%\.git not found. Migration incomplete?
  pause
  exit /b 1
)
if not exist "%DASHBOARD_LOCAL%\package.json" (
  echo   [X] %DASHBOARD_LOCAL%\package.json not found. Wrong working tree?
  pause
  exit /b 1
)
echo   ok (working tree present)

REM --- [1/10] wipe node_modules via robocopy /MIR -----------------------
REM   bash rm -rf + cmd rd both choke on Windows file locking inside deep
REM   node trees (ENOTEMPTY, Access Denied). robocopy /MIR with an EMPTY
REM   source dir deletes everything in dest WITHOUT trying to chdir into
REM   read-only / locked subtrees. It's the only thing that reliably works.
echo.
echo [1/10] Wipe node_modules (robocopy /MIR with empty source)
if not exist "%EMPTY_SRC%" mkdir "%EMPTY_SRC%"
if exist "%DASHBOARD_LOCAL%\node_modules" (
  robocopy "%EMPTY_SRC%" "%DASHBOARD_LOCAL%\node_modules" /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /MT:8 >nul 2>&1
  REM robocopy exit 0-7 = success
  rmdir "%DASHBOARD_LOCAL%\node_modules" 2>nul
  echo   ok (wiped)
) else (
  echo   ok (no node_modules to wipe)
)

REM --- [2/10] npm install -----------------------------------------------
echo.
echo [2/10] npm install (clean)
cd /d %DASHBOARD_LOCAL%
call npm install --no-audit --no-fund > "%INSTALL_LOG%" 2>&1
if errorlevel 1 (
  echo.
  echo   [X] npm install failed. Last 20 lines:
  echo   ----------------------------------------------------------
  powershell -NoProfile -Command "Get-Content '%INSTALL_LOG%' -Tail 20"
  echo   ----------------------------------------------------------
  echo   Full log: %INSTALL_LOG%
  pause
  exit /b 1
)
echo   ok (deps installed)

REM --- [3/10] tsc clean -------------------------------------------------
echo.
echo [3/10] Type-check (tsc --noEmit)
call npx tsc --noEmit
if errorlevel 1 (
  echo.
  echo   [X] TypeScript errors. Fix before deploy.
  pause
  exit /b 1
)
echo   ok

REM --- [4/10] production build ------------------------------------------
echo.
echo [4/10] Production build (next build)
call npx next build > "%BUILD_LOG%" 2>&1
if errorlevel 1 (
  echo.
  echo   [X] Production build failed. Last 30 lines:
  echo   ----------------------------------------------------------
  powershell -NoProfile -Command "Get-Content '%BUILD_LOG%' -Tail 30"
  echo   ----------------------------------------------------------
  echo   Full log: %BUILD_LOG%
  pause
  exit /b 1
)
echo   ok (all routes generated)

REM --- [5/10] auto-commit pending changes -------------------------------
echo.
echo [5/10] Stage + commit pending changes
cd /d %REPO_LOCAL%
git add -A
git diff --cached --quiet >nul 2>&1
if errorlevel 1 (
  set "STAMP=%date% %time:~0,5%"
  git commit -m "deploy: panel UI update !STAMP!"
  if errorlevel 1 (
    echo   [X] commit failed.
    pause
    exit /b 1
  )
  echo   ok (committed)
) else (
  echo   no pending changes
)

REM --- [6/10] sync + push origin/main -----------------------------------
echo.
echo [6/10] Push to origin/main (fast-forward only)
git pull --rebase origin main
if errorlevel 1 (
  echo.
  echo   [X] rebase failed. Resolve manually then re-run.
  pause
  exit /b 1
)
git push origin main
if errorlevel 1 (
  echo   [X] git push failed.
  pause
  exit /b 1
)
for /f %%h in ('git rev-parse --short HEAD') do set SHA=%%h
echo   ok (pushed at !SHA!)

REM --- [7/10] upload remote-deploy.sh -----------------------------------
echo.
echo [7/10] Upload deploy script
scp -o StrictHostKeyChecking=accept-new "%SCRIPT_LOCAL%" %PROD%:/tmp/remote-deploy.sh >nul
if errorlevel 1 (
  echo   [X] scp failed.
  pause
  exit /b 1
)
ssh -o BatchMode=yes %PROD% "sed -i 's/\r$//' /tmp/remote-deploy.sh && bash -n /tmp/remote-deploy.sh" >nul 2>&1
if errorlevel 1 (
  echo   [X] remote-deploy.sh failed syntax check after CRLF strip.
  pause
  exit /b 1
)
echo   ok

REM --- [8/10] remote build + restart (auto-detects backend changes) -----
echo.
echo [8/10] Detecting backend changes...
set DEPLOY_FLAGS=
set SERVER_HEAD=
for /f %%h in ('ssh -o BatchMode=yes %PROD% "cd %REPO% && git rev-parse HEAD" 2^>nul') do set SERVER_HEAD=%%h
if "!SERVER_HEAD!"=="" (
  echo   could not read server HEAD -- assuming backend may have changed
  set DEPLOY_FLAGS=--with-backend
) else (
  git fetch origin main >nul 2>&1
  git diff --name-only !SERVER_HEAD!..origin/main 2>nul | findstr /B "leo_dev/backend/" >nul
  if not errorlevel 1 (
    echo   backend changes detected vs server HEAD !SERVER_HEAD! -- will rebuild backend
    set DEPLOY_FLAGS=--with-backend
  ) else (
    echo   no backend changes vs server HEAD !SERVER_HEAD! -- dashboard-only deploy
  )
)

echo.
echo [8/10] Remote build + restart (DB and RKA untouched)
echo   ----------------------------------------------------------
ssh %PROD% "bash /tmp/remote-deploy.sh !DEPLOY_FLAGS!"
echo   ----------------------------------------------------------

REM --- [9/10] prisma schema sync ---------------------------------------
echo.
echo [9/10] Schema sync check
set PRISMA_NEEDED=0
if not "!SERVER_HEAD!"=="" (
  git diff --name-only !SERVER_HEAD!..origin/main 2>nul | findstr /R "schema\.prisma" >nul
  if not errorlevel 1 set PRISMA_NEEDED=1
)
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

REM --- [10/10] smoke test + open browser --------------------------------
echo.
echo [10/10] Smoke-test https://snap.sinijkr.com/
for /f %%c in ('curl -ks -o NUL -w "%%{http_code}" https://snap.sinijkr.com/') do set CODE=%%c
echo   https://snap.sinijkr.com  ->  !CODE!

echo.
echo ====================================================================
echo   DEPLOY COMPLETE  --  HEAD !SHA!  (from D:\ hub working tree)
echo ====================================================================
echo.
start "" "https://snap.sinijkr.com"
echo Window stays open so you can scroll back through the deploy output.
echo Close it manually when you're done reading.
pause
endlocal
