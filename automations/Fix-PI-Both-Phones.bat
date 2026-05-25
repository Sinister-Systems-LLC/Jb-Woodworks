@echo off
REM Author: RKOJ-ELENO :: 2026-05-24
REM Fix-PI-Both-Phones.bat -- replay proven 14:30Z PI-restore sequence on P1 + P2
REM Sequence: per-phone reachability check + pm clear Snap + TrickyStore daemon respawn + 30s wait + PI re-tap
REM Clone-independent; no source-tree dependency. Safe to re-run any time PI degrades.
REM
REM Composes with:
REM   _shared-memory/plans/kernel-apk-andrewt407-x5-2026-05-24/master-plan.md (iter 0 owner)
REM   _shared-memory/knowledge/kernel-apk-session-2026-05-24-FULL-handoff.md (proven 14:30Z anchor)
REM   _shared-memory/inbox/sinister-panel/2026-05-24T2355Z-from-kernel-apk-PI-regression-investigation-plus-deferred-1614Z-directive-ship.json (ask_1)

setlocal

set P1=2A061JEGR09301
set P2=26031JEGR17598

echo === Fix-PI-Both-Phones :: 2026-05-24 ===
echo P1 serial: %P1%
echo P2 serial: %P2%
echo.

REM ========== PHONE 1 ==========
echo --- Phone 1 (%P1%) ---
adb -s %P1% get-state >nul 2>nul
if errorlevel 1 (
  echo [SKIP] Phone 1 not reachable. Check USB + adb devices.
  goto :phone2
)
echo [OK] Phone 1 reachable
echo [Step 1/4] pm clear com.snapchat.android (drops cached bad att_token = H1)
adb -s %P1% shell pm clear com.snapchat.android
echo [Step 2/4] TrickyStore daemon respawn (H2)
adb -s %P1% shell su -c "setsid /data/adb/modules/tricky_store/daemon </dev/null >/dev/null 2>&1 &"
echo.

:phone2
REM ========== PHONE 2 ==========
echo --- Phone 2 (%P2%) ---
adb -s %P2% get-state >nul 2>nul
if errorlevel 1 (
  echo [SKIP] Phone 2 not reachable. Check USB + adb devices.
  goto :wait
)
echo [OK] Phone 2 reachable
echo [Step 1/4] pm clear com.snapchat.android (drops cached bad att_token = H1)
adb -s %P2% shell pm clear com.snapchat.android
echo [Step 2/4] TrickyStore daemon respawn (H2)
adb -s %P2% shell su -c "setsid /data/adb/modules/tricky_store/daemon </dev/null >/dev/null 2>&1 &"
echo.

:wait
echo --- Step 3/4: wait 30s for network settle + daemon ready ---
timeout /t 30 /nobreak >nul
echo done.
echo.

REM ========== PI RE-TAP BOTH ==========
echo --- Step 4/4: re-tap Play Integrity on both phones ---
adb -s %P1% get-state >nul 2>nul
if not errorlevel 1 (
  echo Phone 1 PI verdict:
  adb -s %P1% shell "content query --uri content://com.scottyab.rootbeer.sample.provider/playintegrity"
  echo.
)
adb -s %P2% get-state >nul 2>nul
if not errorlevel 1 (
  echo Phone 2 PI verdict:
  adb -s %P2% shell "content query --uri content://com.scottyab.rootbeer.sample.provider/playintegrity"
  echo.
)

echo === Fix-PI-Both-Phones complete ===
echo Expected: DEVICE_INTEGRITY=3/3 on both. If still 1/3 -- H3 (Snap 13.93.0.51 attestation shape change)
echo confirmed; iter 1B Snap audit becomes priority-1. See master-plan.md.

endlocal
