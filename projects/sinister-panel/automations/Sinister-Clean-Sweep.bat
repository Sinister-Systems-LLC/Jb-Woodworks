@echo off
REM ============================================================================
REM  Sinister-Clean-Sweep.bat  --  conservative test-data cleanup.
REM
REM  Author: Sinister Panel agent (Claude Opus 4.7 1M) :: 2026-05-20
REM  TODO: migrate to LetsText bat system per p.md 2026-05-19 directive once
REM        operator surfaces the bat-creator interface.
REM
REM  Operator directive 2026-05-20: "all data on hetzner needs to be real
REM  valid data, accounts etc. i want a clean sweep on most things. like
REM  accounts created things like that. dont delete usernanme or ban
REM  reasons or things like that."
REM
REM  Operation:
REM    1. pg_dump snapshot to /root/sinister-backups/  (ALWAYS, before any
REM       delete — restorable via psql pipe-in)
REM    2. BEFORE counts (every table)
REM    3. DRY-RUN preview (rows that WILL be deleted, sample of 20)
REM    4. DELETE accounts matching strict "test/dev" criteria + cascades
REM       (Prisma `onDelete: Cascade` handles GroupAccount/AccountTag/
REM       FriendAdd/ChatThread/ChatMessage child rows automatically)
REM    5. AFTER counts
REM    6. VERIFY KEEPERS unchanged (UsernamePool / UsernameList /
REM       UsernameListEntry / AuditLog / LicenseKey / PhoneGroup)
REM    7. Print restore command + snapshot path
REM    8. Write OUTLOG to Desktop
REM
REM  DELETE criteria for Account (intentionally strict — only kills
REM  accounts that have NO evidence of real value):
REM    - source <> 'apk_push'             (not from APK harvest)
REM    - AND "isSold" = false             (not sold — revenue history)
REM    - AND "isBanned" = false           (not banned — audit history)
REM    - AND "banFirstDetectedAt" IS NULL (never flagged — audit history)
REM    - AND "realUsername" IS NULL       (never logged in successfully)
REM    - AND "lastLoginAt" IS NULL        (never logged in successfully)
REM
REM  Accounts matching ALL six conditions are "manual/test/dev never-
REM  touched" — safe to delete. Anything with any signal of real use
REM  (apk_push, sold, banned, flagged, logged in) is KEPT.
REM
REM  Per c.md Postgres rails: --accept-data-loss requires "explicitly
REM  intentional". This bat IS that. Operator's directive authorizes.
REM ============================================================================

setlocal ENABLEDELAYEDEXPANSION

set PROD=root@95.216.240.227
set OUTLOG=%USERPROFILE%\Desktop\sinister-clean-sweep.log
set LOGDIR=%TEMP%\sinister-clean-sweep
if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

for /f "tokens=*" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ssZ"') do set STAMP=%%t
for /f "tokens=*" %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set TS=%%t
set SNAPSHOT=/root/sinister-backups/pre-cleansweep-%TS%.sql.gz

echo.
echo ====================================================================
echo   SINISTER CLEAN SWEEP  (conservative test-data cleanup)
echo   stamp: %STAMP%
echo   snapshot will land at: %SNAPSHOT%
echo   log:   %OUTLOG%
echo ====================================================================
echo.

REM --- [1/8] snapshot --------------------------------------------------
echo [1/8] pg_dump snapshot (ALWAYS, before any change)
ssh %PROD% "mkdir -p /root/sinister-backups && docker exec sinister-postgres pg_dump -U sinister -d sinister --no-owner --no-acl | gzip > %SNAPSHOT% && ls -lh %SNAPSHOT%"
if errorlevel 1 (
  echo   [X] pg_dump snapshot FAILED. Aborting — no DELETE without working backup.
  echo %STAMP% FAIL snapshot_failed>> "%OUTLOG%"
  exit /b 1
)
echo   + snapshot ok
echo.

REM --- [2/8] BEFORE counts --------------------------------------------
echo [2/8] BEFORE counts (every table)
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT 'Account' AS tbl, COUNT(*) FROM \\\"Account\\\" UNION ALL SELECT 'FriendAdd', COUNT(*) FROM \\\"FriendAdd\\\" UNION ALL SELECT 'ChatThread', COUNT(*) FROM \\\"ChatThread\\\" UNION ALL SELECT 'ChatMessage', COUNT(*) FROM \\\"ChatMessage\\\" UNION ALL SELECT 'GroupAccount', COUNT(*) FROM \\\"GroupAccount\\\" UNION ALL SELECT 'AccountTag', COUNT(*) FROM \\\"AccountTag\\\" UNION ALL SELECT 'AuditLog (KEEP)', COUNT(*) FROM \\\"AuditLog\\\" UNION ALL SELECT 'UsernamePool (KEEP)', COUNT(*) FROM \\\"UsernamePool\\\" UNION ALL SELECT 'UsernameList (KEEP)', COUNT(*) FROM \\\"UsernameList\\\" UNION ALL SELECT 'UsernameListEntry (KEEP)', COUNT(*) FROM \\\"UsernameListEntry\\\" UNION ALL SELECT 'LicenseKey (KEEP)', COUNT(*) FROM \\\"LicenseKey\\\" UNION ALL SELECT 'PhoneGroup (KEEP)', COUNT(*) FROM \\\"PhoneGroup\\\" UNION ALL SELECT 'Phone (KEEP)', COUNT(*) FROM \\\"Phone\\\";\"" > "%LOGDIR%\before-counts.txt" 2>&1
type "%LOGDIR%\before-counts.txt"
echo.

REM --- [3/8] DRY-RUN preview -------------------------------------------
echo [3/8] DRY-RUN preview — sample of 20 rows that WILL be deleted
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT username, source, \\\"loginStatus\\\", \\\"createdAt\\\" FROM \\\"Account\\\" WHERE source != 'apk_push' AND \\\"isSold\\\" = false AND \\\"isBanned\\\" = false AND \\\"banFirstDetectedAt\\\" IS NULL AND \\\"realUsername\\\" IS NULL AND \\\"lastLoginAt\\\" IS NULL ORDER BY \\\"createdAt\\\" DESC LIMIT 20;\""
echo.
echo [3/8] DRY-RUN total count
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -tA -c \"SELECT COUNT(*) AS deletable_account_count FROM \\\"Account\\\" WHERE source != 'apk_push' AND \\\"isSold\\\" = false AND \\\"isBanned\\\" = false AND \\\"banFirstDetectedAt\\\" IS NULL AND \\\"realUsername\\\" IS NULL AND \\\"lastLoginAt\\\" IS NULL;\"" > "%LOGDIR%\deletable-count.txt" 2>&1
set /p DELETABLE_COUNT=< "%LOGDIR%\deletable-count.txt"
echo   deletable Account count = !DELETABLE_COUNT!
echo.

REM --- [4/8] EXECUTE DELETE -------------------------------------------
echo [4/8] DELETE matching accounts (Prisma cascades wipe child rows)
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c \"DELETE FROM \\\"Account\\\" WHERE source != 'apk_push' AND \\\"isSold\\\" = false AND \\\"isBanned\\\" = false AND \\\"banFirstDetectedAt\\\" IS NULL AND \\\"realUsername\\\" IS NULL AND \\\"lastLoginAt\\\" IS NULL;\""
if errorlevel 1 (
  echo   [X] DELETE failed. Snapshot intact at %SNAPSHOT% — restore command at end.
  echo %STAMP% FAIL delete_failed>> "%OUTLOG%"
  exit /b 1
)
echo   + delete ok
echo.

REM --- [5/8] AFTER counts ----------------------------------------------
echo [5/8] AFTER counts (delta vs BEFORE)
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT 'Account' AS tbl, COUNT(*) FROM \\\"Account\\\" UNION ALL SELECT 'FriendAdd', COUNT(*) FROM \\\"FriendAdd\\\" UNION ALL SELECT 'ChatThread', COUNT(*) FROM \\\"ChatThread\\\" UNION ALL SELECT 'ChatMessage', COUNT(*) FROM \\\"ChatMessage\\\" UNION ALL SELECT 'GroupAccount', COUNT(*) FROM \\\"GroupAccount\\\" UNION ALL SELECT 'AccountTag', COUNT(*) FROM \\\"AccountTag\\\";\"" > "%LOGDIR%\after-counts.txt" 2>&1
type "%LOGDIR%\after-counts.txt"
echo.

REM --- [6/8] VERIFY KEEPERS unchanged -----------------------------------
echo [6/8] VERIFY KEEPERS — usernames + audit log + license keys + groups
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT 'UsernamePool' AS tbl, COUNT(*) FROM \\\"UsernamePool\\\" UNION ALL SELECT 'UsernameList', COUNT(*) FROM \\\"UsernameList\\\" UNION ALL SELECT 'UsernameListEntry', COUNT(*) FROM \\\"UsernameListEntry\\\" UNION ALL SELECT 'AuditLog', COUNT(*) FROM \\\"AuditLog\\\" UNION ALL SELECT 'LicenseKey', COUNT(*) FROM \\\"LicenseKey\\\" UNION ALL SELECT 'PhoneGroup', COUNT(*) FROM \\\"PhoneGroup\\\" UNION ALL SELECT 'Phone', COUNT(*) FROM \\\"Phone\\\";\"" > "%LOGDIR%\keepers.txt" 2>&1
type "%LOGDIR%\keepers.txt"
echo.

REM --- [7/8] sample remaining accounts (sanity) -----------------------
echo [7/8] Sample remaining Account rows (sanity check — should look real)
ssh %PROD% "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT username, source, \\\"loginStatus\\\", \\\"isSold\\\", \\\"isBanned\\\", \\\"createdAt\\\" FROM \\\"Account\\\" ORDER BY \\\"createdAt\\\" DESC LIMIT 15;\""
echo.

REM --- [8/8] restore command + log success ------------------------------
echo %STAMP% OK clean_sweep deletable_count=!DELETABLE_COUNT! snapshot=%SNAPSHOT%>> "%OUTLOG%"
echo ====================================================================
echo   CLEAN SWEEP COMPLETE.
echo   - Snapshot:  %SNAPSHOT%   (on Hetzner)
echo   - To restore:
echo       ssh %PROD% "gunzip -c %SNAPSHOT% ^| docker exec -i sinister-postgres psql -U sinister -d sinister"
echo   - Log file:  %OUTLOG%
echo ====================================================================
echo.
exit /b 0
