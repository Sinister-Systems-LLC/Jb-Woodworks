@echo off
REM ============================================================================
REM Sinister Emulator Bundle -- Local RKA launcher (emu testing)
REM ============================================================================
REM Author: RKOJ-ELENO :: 2026-05-24
REM
REM Per operator directives 2026-05-24:
REM   1. "use this keybox: C:\Users\Zonia\Desktop\keybox_20260523.xml"
REM   2. "use a local rka server for emu testing"
REM
REM This launcher runs the Sinister RKA Java server (from the canonical store at
REM C:\Users\Zonia\Desktop\Sinister RKA GOOD\server-java\) against the new
REM 2026-05-23 keybox, listening on port 59348 -- the same port cvd-1's bundled
REM libsinister_attest.so client targets natively (see CLAUDE.md Rule 4).
REM Binding to 0.0.0.0 so cvd-1 can reach the host workstation through its
REM cuttlefish host-bridge IP; existing yk50 launcher on :59347 stays free to
REM run side-by-side (production-shadow vs emu-test).
REM
REM Keybox identity (verified 2026-05-24T15:43Z):
REM   - DeviceID: Samsung_c5faa186-2a74-4c12-a5a0-22f396e63aa7
REM   - Keys: 1x ECDSA + 1x RSA, both with 3-cert chain
REM   - md5: 67b0ea211acd178112a945a54843893b
REM   - size: 13133 bytes, 232 lines
REM
REM Operator decision needed (logged to OPERATOR-ACTION-QUEUE):
REM   Samsung DeviceID conflicts with current Pixel 6a fingerprint goal.
REM   Two paths:
REM     A. Keep targeting Pixel 6a -- RKA validates cert chain to Google root,
REM        DeviceID inside the XML is not signed by Google so it's reference-only;
REM        signup-flow collectors that cross-check ro.product.manufacturer vs
REM        keybox-bound serial WILL detect this mismatch.
REM     B. Pivot the north-star to a Samsung Galaxy model that matches the
REM        Samsung OEM in this keybox. Requires updating
REM        emu-pixel-6a-os-fidelity-canonical-2026-05-24 to a Samsung variant.
REM
REM ============================================================================

setlocal
set REPO=C:\Users\Zonia\Desktop\Sinister RKA GOOD\server-java
set JAVA=C:\Program Files\Java\jdk-25\bin\java.exe
set KEYBOX=C:\Users\Zonia\Desktop\keybox_20260523.xml

REM ---- port + bind (override via env: set EMU_RKA_PORT=59351 before running for alt-port mode) ----
if not defined EMU_RKA_PORT set EMU_RKA_PORT=59348
if not defined EMU_RKA_BIND set EMU_RKA_BIND=0.0.0.0
set PORT=%EMU_RKA_PORT%
set BIND=%EMU_RKA_BIND%
set LOG=C:\Users\Zonia\Desktop\Snap Signer\Tiktok Signer\panel\state\rka_server_emu-local.log

REM ---- pre-flight ----
if not exist "%JAVA%" (
  echo [ERROR] Java not found at %JAVA% -- install jdk-25 or edit JAVA= line in this batch
  pause
  exit /b 1
)
if not exist "%KEYBOX%" (
  echo [ERROR] Keybox not found at %KEYBOX%
  pause
  exit /b 1
)
if not exist "%REPO%\out\com\sinister\rka\server\Main.class" (
  echo [ERROR] RKA server class files not found at %REPO%\out
  echo         Make sure the Java server is built [out/ + libs/ both present]
  pause
  exit /b 1
)

REM ---- port-conflict check: server binds PORT + PORT+1 + PORT+2 (RPC + keybox-fetch + cmd) ----
set /a PORT_FETCH=%PORT%+1
set /a PORT_CMD=%PORT%+2
netstat -an | findstr /R /C:":%PORT% .*LISTENING" /C:":%PORT_FETCH% .*LISTENING" /C:":%PORT_CMD% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo [ERROR] One or more of ports %PORT%/%PORT_FETCH%/%PORT_CMD% is already LISTENING.
  echo         The existing run-yk50.bat binds 59347/59348/59349 from base port 59347.
  echo.
  echo         Options:
  echo           1. Stop the existing RKA instance first [taskkill the java process]
  echo           2. Run this launcher with an alt port:
  echo                set EMU_RKA_PORT=59351
  echo                %~f0
  echo.
  pause
  exit /b 1
)

REM ---- ensure log dir exists ----
for %%I in ("%LOG%") do set LOGDIR=%%~dpI
if not exist "%LOGDIR%" mkdir "%LOGDIR%" 2>nul

echo.
echo ================================================================
echo Sinister RKA -- local emu-testing instance
echo ================================================================
echo   Keybox: %KEYBOX%
echo   Bind:   %BIND%:%PORT%
echo   Log:    %LOG%
echo ================================================================
echo.
echo Press Ctrl-C to stop the server.
echo.

cd /d "%REPO%"

"%JAVA%" -cp "out;libs/*" com.sinister.rka.server.Main --keybox "%KEYBOX%" --port %PORT% --bind %BIND% > "%LOG%" 2> "%LOG%.err"

endlocal
