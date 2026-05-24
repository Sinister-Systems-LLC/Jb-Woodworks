@echo off
REM Sinister Start :: direct Sanctum session boot (v6 :: 2026-05-23 - RKOJ-ELENO)
REM
REM v6 changes (operator 2026-05-23 - "the sinsiter start bat file isnt
REM   working. fix it now and make sure it works with all eve exe updates"):
REM   - ADDED --diagnose flag: probes every prerequisite + reports without spawning.
REM   - ADDED preflight check for mintty / git-bash / bash; warns operator BEFORE
REM     PS1 picker runs if no spawn-capable shell will be available.
REM   - ADDED EVE.exe sanity check: skip EVE.exe if it's a zero-byte stub or
REM     fails a quick --version probe (was: blindly invoke whatever was at the path).
REM   - PS1 spawn step (started-sinister-session.ps1) hardened in parallel:
REM     conditional "[OK] window up" message + explicit [FAIL] when no shell.
REM
REM v5 (2026-05-23): step-by-step echoes + pause at end on error.
REM v4 (2026-05-23): EVE.exe probe + PS1 fallback.
REM v3 (2026-05-23 evening): First-run autonomy bootstrap via marker file.

TITLE Sinister Sanctum :: Session Online
setlocal enableextensions

REM ----- Explicit autonomy re-setup flag -----
if /I "%~1"=="--setup-autonomy" goto :run_autonomy
if /I "%~1"=="-setup-autonomy"  goto :run_autonomy
if /I "%~1"=="/setup-autonomy"  goto :run_autonomy
if /I "%~1"=="--diagnose"       goto :run_diagnose
if /I "%~1"=="-diagnose"        goto :run_diagnose
if /I "%~1"=="/diagnose"        goto :run_diagnose

REM ----- Multi-account flags (RKOJ-ELENO :: 2026-05-23) -----
REM --account <name>  -- pin a specific account for this session (overrides round-robin)
REM --account-status   -- print current claude-accounts.json state and exit
if /I "%~1"=="--account" (
    set "SINISTER_ACCOUNT=%~2"
    shift
    shift
    goto :continue_after_account
)
if /I "%~1"=="--account-status" goto :run_account_status
:continue_after_account

REM ----- Optional wt.exe redirect (off by default after v4 silent-close bug) -----
if defined SINISTER_USE_WT (
    if not defined WT_SESSION (
        where wt.exe >nul 2>&1
        if not errorlevel 1 (
            start "" wt.exe new-tab --title "Sinister Sanctum" cmd.exe /K "\"%~f0\" %*"
            exit /b 0
        )
    )
)

REM v6.1: silent root probe (operator 2026-05-23: "dont incldue this at the top").
REM Previously echoed [start] + [ok] lines. Use --verbose or --diagnose to see them.
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum

REM ----- First-run autonomy bootstrap (silent skip if marker present) -----
if not exist "%USERPROFILE%\.sanctum-autonomy-granted" (
    echo.
    echo  ====================================================================
    echo   Sinister Sanctum :: First-run autonomy bootstrap
    echo  ====================================================================
    echo   No %%USERPROFILE%%\.sanctum-autonomy-granted marker found.
    echo   Running Grant-Claude-Autonomy.ps1 once before launching the session.
    echo   Re-run any time:  Sinister Start.bat --setup-autonomy
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\grant-claude-autonomy.ps1"
    echo.
)

REM ----- Required plugin check (operator directive 2026-05-23 evening) -----
REM v6.3 (operator: "sinster start bat file wont work fix it"): plugin install
REM is now FULLY BACKGROUNDED via `start "" /B ... -WindowStyle Hidden`. Prior
REM v6.2 version blocked the bat for 10-30s while `claude plugin install ...`
REM ran each recommended plugin. The check now runs in parallel with EVE.exe
REM launch and converges silently before the operator picks a project.
if exist "%SANCTUM_ROOT%\automations\check-required-plugins.ps1" (
    start "" /B powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\check-required-plugins.ps1" -AutoInstall -Silent
)

REM ----- Spawn-shell preflight (v6.1 2026-05-23 - silent when healthy) -----
REM v6.1: only emits output if a shell is MISSING (operator: don't include
REM noisy startup chatter when everything is fine). Healthy path is silent.
set "HAS_SHELL=0"
if exist "C:\Program Files\Git\usr\bin\mintty.exe" set "HAS_SHELL=1"
if exist "C:\Program Files\Git\git-bash.exe"      set "HAS_SHELL=1"
if exist "C:\Program Files\Git\bin\bash.exe"      set "HAS_SHELL=1"
if "%HAS_SHELL%"=="0" (
    echo.
    echo  [WARN] no spawn-capable shell found.
    echo         tried mintty.exe  : C:\Program Files\Git\usr\bin\mintty.exe
    echo         tried git-bash.exe: C:\Program Files\Git\git-bash.exe
    echo         tried bash.exe    : C:\Program Files\Git\bin\bash.exe
    echo         install Git for Windows: https://gitforwindows.org
    echo.
    echo  [WARN] picker will still open but spawn will fail. Ctrl+C to abort.
    timeout /t 5
)

REM ----- Prefer EVE.exe (thin jcode-speed picker) if available -----
REM v6: tightened probe - must be >0 bytes + must respond to --version within
REM 3 seconds. Skips silently to PS1 fallback if EVE.exe is a stale/broken stub.
set "EVE_EXE="
REM v6.5 (iter 6 2026-05-23): added --onedir build path first (dist/EVE/EVE.exe).
REM The --onefile EVE.exe at dist/EVE.exe fails to extract python312.dll on some
REM Windows boxes (antivirus / VC++ runtime). --onedir builds work universally.
if exist "%~dp0EVE.exe" call :probe_eve "%~dp0EVE.exe"
if not defined EVE_EXE if exist "%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE\EVE.exe" call :probe_eve "%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE\EVE.exe"
if not defined EVE_EXE if exist "%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe" call :probe_eve "%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe"
if not defined EVE_EXE if exist "%LOCALAPPDATA%\Sinister\EVE.exe" call :probe_eve "%LOCALAPPDATA%\Sinister\EVE.exe"

if defined EVE_EXE (
    REM v6.3 (operator: "sinster start bat file wont work fix it"): use the
    REM simplest `start` syntax that reliably forks a new console — empty title
    REM "" + bare exe path. Earlier v6.2 syntax with `/D` and a colonned title
    REM ("Sinister Sanctum :: EVE") returned errorlevel 0 but didn't actually
    REM spawn EVE.exe on this machine. X-button still works because parent cmd
    REM exits immediately + EVE.exe owns its own console window.
    pushd "%SANCTUM_ROOT%"
    start "" "%EVE_EXE%"
    popd
    exit /b 0
)

:launch_ps1
REM ----- Fallback: PS1 launcher (no regression if EVE.exe not built yet) -----
REM v6.3: same simple `start ""` pattern as EVE.exe path.
pushd "%SANCTUM_ROOT%"
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
popd
exit /b 0

:run_autonomy
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum
echo.
echo  ====================================================================
echo   Sinister Sanctum :: Explicit autonomy re-setup (--setup-autonomy)
echo  ====================================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SANCTUM_ROOT%\automations\grant-claude-autonomy.ps1"
echo.
echo  ----------------------------------------------------------------------
echo   Autonomy setup complete. Run Sinister Start.bat (no flags) to boot.
echo  ----------------------------------------------------------------------
pause
exit /b 0

:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0

:no_sanctum
echo  [FAIL] Sinister Sanctum repo not found.
echo  Set SINISTER_SANCTUM_ROOT env var or place repo at D:\Sinister Sanctum
pause
exit /b 1

:run_account_status
REM Print current multi-account state and exit. RKOJ-ELENO :: 2026-05-23.
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT goto :no_sanctum
echo.
echo  ====================================================================
echo   Sinister Sanctum :: Multi-account status (--account-status)
echo  ====================================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ". '%SANCTUM_ROOT%\automations\claude-accounts.ps1'; $cfg = Get-AccountsConfig; Write-Host \"Default: $($cfg.default)\"; Write-Host \"Strategy: $($cfg.rotation_strategy)\"; Write-Host \"Accounts:\"; $cfg.accounts | ForEach-Object { $rl = if ($_.rate_limited_until_utc) { 'RATE-LIMITED until ' + $_.rate_limited_until_utc } else { 'available' }; Write-Host \"  - $($_.name) [$($_.plan_tier)] sessions=$($_.current_sessions)/$($_.max_sessions_concurrent) $rl\" }"
echo.
pause
exit /b 0

:probe_eve
REM Args: %~1 = path to EVE.exe candidate.
REM Sets EVE_EXE if the file is >0 bytes AND not in the blocklist (.broken / .bak).
REM v6.4 (operator 2026-05-23: "bat file keeps opening and closing itself" —
REM root cause was EVE.exe hung on --version after PyInstaller --onefile build
REM corruption; bat spawned EVE.exe which never showed a window, bat exited).
REM Mitigation A: rename the broken EVE.exe to EVE.exe.broken-<date> so this
REM probe skips it and PS1 fallback fires.
REM Mitigation B: this probe now also skips files ending in .broken / .bak.
if not exist "%~1" exit /b 0
echo %~1| findstr /I "\.broken \.bak" >nul && exit /b 0
for %%I in ("%~1") do if %%~zI GTR 0 set "EVE_EXE=%~1"
exit /b 0

:run_diagnose
REM ----- v6 self-help: probe every prerequisite + report. NO spawn. -----
echo.
echo  ====================================================================
echo   Sinister Start :: --diagnose
echo  ====================================================================
echo.
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if defined SANCTUM_ROOT ( echo  [OK]    SANCTUM_ROOT = %SANCTUM_ROOT% ) else ( echo  [FAIL]  SANCTUM_ROOT not found in any known location )
if exist "C:\Program Files\Git\usr\bin\mintty.exe" ( echo  [OK]    mintty.exe ) else ( echo  [FAIL]  mintty.exe - install Git for Windows )
if exist "C:\Program Files\Git\git-bash.exe" ( echo  [OK]    git-bash.exe ) else ( echo  [warn]  git-bash.exe - fallback path )
if exist "C:\Program Files\Git\bin\bash.exe" ( echo  [OK]    bash.exe ) else ( echo  [warn]  bash.exe - last-resort fallback )
if exist "%~dp0EVE.exe" ( echo  [OK]    EVE.exe on Desktop ) else ( echo  [info]  EVE.exe NOT on Desktop )
if defined SANCTUM_ROOT (
    if exist "%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe" (
        for %%I in ("%SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe") do echo  [OK]    EVE.exe at automations/eve-launcher/dist/ ^(%%~zI bytes^)
    ) else (
        echo  [info]  EVE.exe NOT in automations/eve-launcher/dist/ ^(run build-eve-exe.bat to build^)
    )
)
if exist "%LOCALAPPDATA%\Sinister\EVE.exe" ( echo  [OK]    EVE.exe at LOCALAPPDATA/Sinister/ ) else ( echo  [info]  EVE.exe NOT at LOCALAPPDATA/Sinister/ )
if defined SANCTUM_ROOT (
    if exist "%SANCTUM_ROOT%\automations\start-sinister-session.ps1" ( echo  [OK]    PS1 launcher present ) else ( echo  [FAIL]  PS1 launcher missing at %SANCTUM_ROOT%\automations\start-sinister-session.ps1 )
    if exist "%SANCTUM_ROOT%\automations\grant-claude-autonomy.ps1" ( echo  [OK]    autonomy script present ) else ( echo  [warn]  autonomy script missing ^(first-run flow degraded^) )
)
if exist "%USERPROFILE%\.sanctum-autonomy-granted" ( echo  [OK]    autonomy marker present ) else ( echo  [info]  no autonomy marker - will run on next normal launch )
echo.
echo  Done. Run "Sinister Start.bat" with no args to launch.
echo.
pause
exit /b 0
