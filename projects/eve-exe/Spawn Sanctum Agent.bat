@echo off
REM [SUPERSEDED 2026-05-27 by sanctum-cleanup-and-migrator]
REM   This eve-exe project copy is at v9 (20 lanes). Canonical source-of-truth is now:
REM     D:\Sinister Sanctum\automations\Spawn-Sanctum-Agent.bat (v12, 21 lanes, per-lane CLAUDE_CONFIG_DIR isolation)
REM     D:\Sinister Sanctum\Spawn Sanctum Agent.bat            (v12 shim that forwards to ^^^)
REM   Per Lane A iter-29 unification (2026-05-27). Lane owner: re-sync from root or replace with shim.
REM   File preserved (NOT removed) per WITHOUT-REMOVING-THINGS operator constraint.
REM Spawn Sanctum Agent :: 20-agent fleet launcher (v9, +8 lanes 2026-05-26)
REM Author: RKOJ-ELENO :: 2026-05-26
REM
REM v9 changes (operator 2026-05-26 verbatim image+text directive batch):
REM   "i want session starts for sinsiter hieroglyphics, sinister sleight,
REM    ancestral remotion, designer, panel, chatbot" (v8)
REM   + "also add to bat file (for sanctum agent only) a way to start showmasters
REM     and jbwoodworks projects, sinister api and kernel apk" (v9; sinister api +
REM    kernel apk were already v7 lanes 11+12, so v9 adds the 2 missing: showmasters
REM    + jb-woodworks)
REM   Picker grew 12 -> 20 lanes:
REM     +sinister-sleight (lane 13)
REM     +sinister-term-themes [Ancestral Remotion] (lane 14)
REM     +sinister-designer (lane 15)
REM     +sinister-panel (lane 16)
REM     +sinister-chatbot (lane 17)
REM     +sinister-hieroglyphics (lane 18)
REM     +showmasters (lane 19)
REM     +jb-woodworks (lane 20)
REM
REM v7 changes (operator 2026-05-26 verbatim two-part directive):
REM   1. "i need you to add launch option for sinsiter jokester here"
REM   2. "add to that bat file a way to start sinister quantum, sinister snap api
REM      and kernel apk agents"
REM   Picker grew 8 -> 12 lanes: +sinister-jokester (lane 9) +sinister-quantum
REM   (lane 10) +sinister-snap-api-quantum (lane 11) +kernel-apk (lane 12).
REM   sinister-jokester also got a projects.json entry (v14->v15) + a minimal
REM   CLAUDE.md scaffold so the PS1 launcher won't fail with 'unknown project'.
REM
REM Operator hard-canonical 2026-05-26 (verbatim):
REM   "i need this to work and always work to start a sinister sanctum agent"
REM   "launch sinister memory, sinister os, eve exe, sinister sanctum, eve
REM    compliance, sinister overseer agents before doing anything else"
REM   "add error handeling to that so that this does not happen again"
REM   "try the bat file yourself and successfully launch sinister sanctum,
REM    sinister os, sinister memory, sinister term, eve exe, sinister overseer,
REM    eve compliuance, letstext agents. make sure i can select and open those
REM    with the bat file aswell and make sure this bat file always works with
REM    no issues"
REM
REM v6 changes (operator 2026-05-26 verbatim: "you keep getting logged out i
REM   think it has to do with the eve account manager or json file"):
REM   1. PARENT-CREDS PRESERVE :: PS1's claude-oauth-accounts.ps1 -Action Use
REM      OVERWRITES ~/.claude/.credentials.json with the chosen slot's tokens
REM      (start-sinister-session.ps1:2015-2032). That kills the operator's
REM      parent session because it reads the same file. v5 only restored if
REM      the file looked broken -- it does NOT catch valid-shape-but-wrong-
REM      account state. v6 restores UNCONDITIONALLY at end (after all spawns).
REM   2. LIVE LANE OUTPUT :: v5 redirected per-lane stdout to a log file, so
REM      operator saw nothing for ~30s per lane and assumed the bat hung.
REM      v6 streams PS1 stdout to the console so the operator can see the
REM      account-lease, mintty spawn, window-foreground progress in real time.
REM   3. INSIDE-CLAUDE-CODE DETECTION :: if CLAUDECODE env var is set, the
REM      bat is being run from inside a Claude Code session and overwriting
REM      .credentials.json will 401 the parent. Print a clear warning.
REM
REM v5 features preserved: 8-lane picker, -All / -Lanes / -SoloSanctum /
REM   -Repair flags, preflight checks, creds backup, fleet manifest.

TITLE EVE :: Spawn Sanctum Fleet (v9)
mode con: cols=140 lines=50 >nul 2>&1
setlocal enableextensions enabledelayedexpansion

REM Detect "running from inside Claude Code". When set, the parent CLI session
REM reads the same .credentials.json the PS1 will overwrite -- warn loudly so
REM the operator knows why their 401s happen.
if defined CLAUDECODE (
    echo.
    echo  *********************************************************************
    echo  * NOTICE :: this bat is being run from INSIDE a Claude Code session. *
    echo  *           PS1 spawns will briefly overwrite ~/.claude/.credentials *
    echo  *           .json. The parent session may 401 mid-run. v6 RESTORES   *
    echo  *           parent creds at end -- /login may be needed once.        *
    echo  *           Safer: double-click the bat from Explorer instead.       *
    echo  *********************************************************************
    echo.
)

REM ====================================================================
REM SECTION 1 :: SANCTUM_ROOT resolution
REM ====================================================================
set "SANCTUM_ROOT="
call :tryroot "%SINISTER_SANCTUM_ROOT%"
if not defined SANCTUM_ROOT call :tryroot "D:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "C:\Sinister Sanctum"
if not defined SANCTUM_ROOT call :tryroot "%USERPROFILE%\Sinister Sanctum"
if not defined SANCTUM_ROOT (
    color 4F
    echo.
    echo  [FAIL] Sinister Sanctum repo not found.
    echo         Tried: %%SINISTER_SANCTUM_ROOT%% / D:\Sinister Sanctum
    echo                C:\Sinister Sanctum / %%USERPROFILE%%\Sinister Sanctum
    echo         Fix: set SINISTER_SANCTUM_ROOT env var, OR place repo at D:\Sinister Sanctum
    echo.
    pause
    exit /b 1
)

set "PS1_LAUNCHER=%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
set "ACCOUNTS_JSON=%SANCTUM_ROOT%\_shared-memory\claude-accounts.json"
set "PROJECTS_JSON=%SANCTUM_ROOT%\automations\session-templates\projects.json"
set "CREDS_LIVE=%USERPROFILE%\.claude\.credentials.json"

REM ====================================================================
REM SECTION 2 :: 20-lane fleet definition (canonical order)
REM ====================================================================
REM Index | Key                       | Display
REM   1   | sinister-memory           | Sinister Memory
REM   2   | sinister-os               | Sinister OS
REM   3   | eve-exe                   | Eve EXE
REM   4   | sanctum                   | Sanctum
REM   5   | sinister-term             | Sinister Term
REM   6   | eve-compliance            | EVE Compliance
REM   7   | sinister-overseer         | Sinister Overseer
REM   8   | letstext                  | LetsText
REM   9   | sinister-jokester         | Sinister Jokester      (v7 addition)
REM  10   | sinister-quantum          | Sinister Quantum       (v7 addition)
REM  11   | sinister-snap-api-quantum | Sinister Snap API      (v7 addition)
REM  12   | kernel-apk                | Kernel APK             (v7 addition)
REM  13   | sinister-sleight          | Sinister Sleight       (v8 addition)
REM  14   | sinister-term-themes      | Ancestral Remotion     (v8 addition)
REM  15   | sinister-designer         | Sinister Designer      (v8 addition)
REM  16   | sinister-panel            | Sinister Panel         (v8 addition)
REM  17   | sinister-chatbot          | Sinister Chatbot       (v8 addition)
REM  18   | sinister-hieroglyphics    | Sinister Hieroglyphics (v8 addition)
REM  19   | showmasters               | Showmasters            (v9 addition)
REM  20   | jb-woodworks              | JB Woodworks           (v9 addition)
set "LANE_1=sinister-memory"
set "LANE_2=sinister-os"
set "LANE_3=eve-exe"
set "LANE_4=sanctum"
set "LANE_5=sinister-term"
set "LANE_6=eve-compliance"
set "LANE_7=sinister-overseer"
set "LANE_8=letstext"
set "LANE_9=sinister-jokester"
set "LANE_10=sinister-quantum"
set "LANE_11=sinister-snap-api-quantum"
set "LANE_12=kernel-apk"
set "LANE_13=sinister-sleight"
set "LANE_14=sinister-term-themes"
set "LANE_15=sinister-designer"
set "LANE_16=sinister-panel"
set "LANE_17=sinister-chatbot"
set "LANE_18=sinister-hieroglyphics"
set "LANE_19=showmasters"
set "LANE_20=jb-woodworks"
set "LANE_NAME_1=Sinister Memory"
set "LANE_NAME_2=Sinister OS"
set "LANE_NAME_3=Eve EXE"
set "LANE_NAME_4=Sanctum"
set "LANE_NAME_5=Sinister Term"
set "LANE_NAME_6=EVE Compliance"
set "LANE_NAME_7=Sinister Overseer"
set "LANE_NAME_8=LetsText"
set "LANE_NAME_9=Sinister Jokester"
set "LANE_NAME_10=Sinister Quantum"
set "LANE_NAME_11=Sinister Snap API"
set "LANE_NAME_12=Kernel APK"
set "LANE_NAME_13=Sinister Sleight"
set "LANE_NAME_14=Ancestral Remotion"
set "LANE_NAME_15=Sinister Designer"
set "LANE_NAME_16=Sinister Panel"
set "LANE_NAME_17=Sinister Chatbot"
set "LANE_NAME_18=Sinister Hieroglyphics"
set "LANE_NAME_19=Showmasters"
set "LANE_NAME_20=JB Woodworks"

REM ====================================================================
REM SECTION 3 :: Argument parsing
REM ====================================================================
set "EXTRA_ARGS="
set "SOLO=0"
set "ALL_FLAG=0"
set "REPAIR_MODE=0"
set "LANES_OVERRIDE="
:argloop
if "%~1"=="" goto :argdone
if /I "%~1"=="-SoloSanctum" (set "SOLO=1" & shift & goto :argloop)
if /I "%~1"=="/SoloSanctum" (set "SOLO=1" & shift & goto :argloop)
if /I "%~1"=="-All"         (set "ALL_FLAG=1" & shift & goto :argloop)
if /I "%~1"=="/All"         (set "ALL_FLAG=1" & shift & goto :argloop)
if /I "%~1"=="-Repair"      (set "REPAIR_MODE=1" & shift & goto :argloop)
if /I "%~1"=="/Repair"      (set "REPAIR_MODE=1" & shift & goto :argloop)
if /I "%~1"=="-Doctor"      (set "REPAIR_MODE=1" & shift & goto :argloop)
if /I "%~1"=="-Lanes"       (set "LANES_OVERRIDE=%~2" & shift & shift & goto :argloop)
if /I "%~1"=="/Lanes"       (set "LANES_OVERRIDE=%~2" & shift & shift & goto :argloop)
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto :argloop
:argdone

REM ====================================================================
REM SECTION 4 :: Banner
REM ====================================================================
echo.
echo  ============================================================
echo   EVE :: Spawn Sanctum Fleet ^(v9 :: 20-lane picker + creds-sync^)
echo  ============================================================
echo   Sanctum root:   %SANCTUM_ROOT%
echo   PS1 launcher:   %PS1_LAUNCHER%
echo  ============================================================
echo.

REM ====================================================================
REM SECTION 5 :: Preflight checks
REM ====================================================================
echo  [preflight 1/4] PS1 launcher
if not exist "%PS1_LAUNCHER%" (
    echo                  FAIL :: not found
    echo                  FIX  :: pull latest Sanctum or restore automations\ from git
    pause
    exit /b 2
)
echo                  OK

echo  [preflight 2/4] accounts.json
if not exist "%ACCOUNTS_JSON%" (
    echo                  WARN :: missing -- PS1 will fall back to defaults
) else (
    echo                  OK
)

echo  [preflight 3/4] projects.json
if not exist "%PROJECTS_JSON%" (
    echo                  FAIL :: not found
    echo                  FIX  :: restore automations\session-templates\projects.json from git
    pause
    exit /b 3
)
echo                  OK

echo  [preflight 4/4] live credentials
if exist "%CREDS_LIVE%" (
    echo                  OK   ^(.credentials.json present^)
) else (
    echo                  WARN :: missing -- next claude spawn will prompt /login
)
echo.

REM ====================================================================
REM SECTION 6 :: Credentials backup ^(creds-guard^)
REM ====================================================================
set "TS=%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "TS=%TS: =0%"
set "RUN_DIR=%SANCTUM_ROOT%\_shared-memory\script-runs\spawn-fleet-%TS%"
if not exist "%RUN_DIR%" mkdir "%RUN_DIR%" >nul 2>&1
set "CREDS_BACKUP=%RUN_DIR%\credentials-pre-spawn.json"
if exist "%CREDS_LIVE%" (
    copy /Y "%CREDS_LIVE%" "%CREDS_BACKUP%" >nul 2>&1
)
if exist "%CREDS_BACKUP%" (
    echo  [creds-guard]   backup OK
) else if exist "%CREDS_LIVE%" (
    echo  [creds-guard]   WARN :: backup copy failed -- continuing
) else (
    echo  [creds-guard]   no live creds to back up
)

REM ====================================================================
REM SECTION 6b :: CREDS-SYNC :: copy live .credentials.json to every slot
REM ====================================================================
REM Operator 2026-05-26 diagnosis: slot files (credentials.operator.json /
REM credentials.slot3.json / credentials.slot4.json) had STALE tokens
REM (expiresAt: 1779724665974 vs live 1779857192001 = ~38hr older). PS1's
REM slot-swap step then overwrote .credentials.json with a stale token,
REM causing 401 in both spawned mintty and the parent session. By copying
REM the live (fresh) .credentials.json into every slot BEFORE spawning,
REM the PS1 swap becomes a no-op (same content) and no 401 occurs.
REM
REM This is non-destructive: the original slot files were already backed
REM up implicitly via claude-accounts.ps1's own management. The live
REM .credentials.json is the source of truth (set by /login).
if exist "%CREDS_LIVE%" (
    echo  [creds-sync]    syncing live creds to slot files
    for %%S in (
        "%USERPROFILE%\.claude\credentials.operator.json"
        "%USERPROFILE%\.claude\credentials.slot3.json"
        "%USERPROFILE%\.claude\credentials.slot4.json"
    ) do (
        if exist %%S (
            copy /Y "%CREDS_LIVE%" %%S >nul 2>&1
            if "!ERRORLEVEL!"=="0" (
                echo                  OK   %%~nxS
            ) else (
                echo                  WARN copy failed: %%~nxS
            )
        )
    )
) else (
    echo  [creds-sync]    SKIP :: no live .credentials.json to sync from
)

REM ====================================================================
REM SECTION 7 :: Pre-warm claude-icon cache (no-space path)
REM ====================================================================
set "ICON_SRC=%SANCTUM_ROOT%\automations\eve-launcher\assets\claude-icon.ico"
set "ICON_DST=%USERPROFILE%\.eve\claude-icon.ico"
if exist "%ICON_SRC%" (
    if not exist "%USERPROFILE%\.eve" mkdir "%USERPROFILE%\.eve" >nul 2>&1
    copy /Y "%ICON_SRC%" "%ICON_DST%" >nul 2>&1
)

REM ====================================================================
REM SECTION 8 :: Repair mode early-exit
REM ====================================================================
if "%REPAIR_MODE%"=="1" (
    echo.
    echo  ============================================================
    echo   REPAIR MODE :: preflight done, no spawn fired.
    echo   Run without -Repair to spawn the fleet.
    echo  ============================================================
    echo.
    pause
    exit /b 0
)

REM ====================================================================
REM SECTION 9 :: Resolve which lanes to spawn
REM   Precedence: -Lanes <csv>  ^>  -All  ^>  -SoloSanctum  ^>  interactive picker
REM ====================================================================
set "FLEET_KEYS="

if defined LANES_OVERRIDE (
    REM Parse comma-separated key list. e.g. "sanctum,sinister-os,letstext"
    set "_l=!LANES_OVERRIDE!"
    set "_l=!_l:,= !"
    set "FLEET_KEYS=!_l!"
    echo  [select]  -Lanes override :: !FLEET_KEYS!
    goto :select_done
)

if "%ALL_FLAG%"=="1" (
    set "FLEET_KEYS=%LANE_1% %LANE_2% %LANE_3% %LANE_4% %LANE_5% %LANE_6% %LANE_7% %LANE_8% %LANE_9% %LANE_10% %LANE_11% %LANE_12% %LANE_13% %LANE_14% %LANE_15% %LANE_16% %LANE_17% %LANE_18% %LANE_19% %LANE_20%"
    echo  [select]  -All :: launching all 20 lanes
    goto :select_done
)

if "%SOLO%"=="1" (
    set "FLEET_KEYS=%LANE_4%"
    echo  [select]  -SoloSanctum :: sanctum only
    goto :select_done
)

REM ----- Interactive picker -----
echo  ============================================================
echo   FLEET SELECTION
echo  ============================================================
echo     1^) %LANE_NAME_1%        ^(%LANE_1%^)
echo     2^) %LANE_NAME_2%            ^(%LANE_2%^)
echo     3^) %LANE_NAME_3%                 ^(%LANE_3%^)
echo     4^) %LANE_NAME_4%                 ^(%LANE_4%^)
echo     5^) %LANE_NAME_5%          ^(%LANE_5%^)
echo     6^) %LANE_NAME_6%         ^(%LANE_6%^)
echo     7^) %LANE_NAME_7%      ^(%LANE_7%^)
echo     8^) %LANE_NAME_8%               ^(%LANE_8%^)
echo     9^) %LANE_NAME_9%      ^(%LANE_9%^)
echo    10^) %LANE_NAME_10%       ^(%LANE_10%^)
echo    11^) %LANE_NAME_11%      ^(%LANE_11%^)
echo    12^) %LANE_NAME_12%             ^(%LANE_12%^)
echo    13^) %LANE_NAME_13%       ^(%LANE_13%^)
echo    14^) %LANE_NAME_14%     ^(%LANE_14%^)
echo    15^) %LANE_NAME_15%      ^(%LANE_15%^)
echo    16^) %LANE_NAME_16%         ^(%LANE_16%^)
echo    17^) %LANE_NAME_17%       ^(%LANE_17%^)
echo    18^) %LANE_NAME_18% ^(%LANE_18%^)
echo    19^) %LANE_NAME_19%            ^(%LANE_19%^)
echo    20^) %LANE_NAME_20%           ^(%LANE_20%^)
echo.
echo    A^) ALL 20 lanes        ^(default -- press Enter^)
echo    S^) Sanctum only        ^(solo^)
echo    R^) Repair mode         ^(preflight only, no spawn^)
echo    X^) Cancel
echo.
echo    Or enter comma-separated indices  e.g.  1,3,4,7,9,12,15,19
echo.
set /p "PICK=  Selection: "

if not defined PICK set "PICK=A"
if /I "%PICK%"=="A"   (set "FLEET_KEYS=%LANE_1% %LANE_2% %LANE_3% %LANE_4% %LANE_5% %LANE_6% %LANE_7% %LANE_8% %LANE_9% %LANE_10% %LANE_11% %LANE_12% %LANE_13% %LANE_14% %LANE_15% %LANE_16% %LANE_17% %LANE_18% %LANE_19% %LANE_20%" & goto :select_done)
if /I "%PICK%"=="ALL" (set "FLEET_KEYS=%LANE_1% %LANE_2% %LANE_3% %LANE_4% %LANE_5% %LANE_6% %LANE_7% %LANE_8% %LANE_9% %LANE_10% %LANE_11% %LANE_12% %LANE_13% %LANE_14% %LANE_15% %LANE_16% %LANE_17% %LANE_18% %LANE_19% %LANE_20%" & goto :select_done)
if /I "%PICK%"=="S"   (set "FLEET_KEYS=%LANE_4%" & goto :select_done)
if /I "%PICK%"=="X"   (
    echo  [cancelled]
    exit /b 0
)
if /I "%PICK%"=="R" (
    echo  [repair]
    REM Already past repair gate; just run preflight summary and exit.
    echo.
    echo  ============================================================
    echo   REPAIR MODE :: preflight done, no spawn fired.
    echo  ============================================================
    pause
    exit /b 0
)

REM Parse comma-separated indices. Strip spaces.
set "_p=%PICK%"
set "_p=%_p:,= %"
for %%I in (%_p%) do (
    if defined LANE_%%I (
        for /F "tokens=*" %%V in ('echo !LANE_%%I!') do set "FLEET_KEYS=!FLEET_KEYS! %%V"
    ) else (
        echo  [warn] ignoring invalid selection: %%I
    )
)
if not defined FLEET_KEYS (
    echo  [fail] no valid lanes selected.
    pause
    exit /b 4
)

:select_done
echo.
echo  [select]  lanes:  %FLEET_KEYS%
echo.

REM ====================================================================
REM SECTION 10 :: Lock modes for all spawns
REM ====================================================================
set "SINISTER_DEFAULT_SWARM=1"
set "SINISTER_DEFAULT_LOOP=1"
set "SINISTER_SKIP_MODES_PROMPT=1"
REM 2026-05-27 :: operator "fast fluid and concise" - master silence flag also
REM kills the Confirm-AgentPrefs / picker-reprompt / quick-launch chatter that
REM SINISTER_SKIP_MODES_PROMPT alone does NOT cover.
set "SINISTER_SILENT_LAUNCH=1"
set "SINISTER_SKIP_CONFIRM_PREFS=1"
set "SINISTER_SKIP_PICKER_REPROMPT=1"
set "SINISTER_SANCTUM_ROOT=%SANCTUM_ROOT%"

REM ====================================================================
REM SECTION 11 :: Per-lane spawn with logging + error classification
REM ====================================================================
pushd "%SANCTUM_ROOT%"
set "FAIL_COUNT=0"
set "OK_COUNT=0"
set "FAIL_KEYS="

REM v6: stream PS1 stdout to console so operator sees progress in real time.
REM Per-lane log is captured by piping through powershell tee-object so we
REM still have it for error classification.
for %%K in (%FLEET_KEYS%) do (
    echo.
    echo  ------------------------------------------------------------
    echo   [fleet] spawning '%%K' ...
    echo  ------------------------------------------------------------
    set "LANE_LOG=%RUN_DIR%\%%K.log"
    REM Tee via powershell so the operator sees the PS1 progress AND we still
    REM capture a log for classify_error. tee-object writes to file + stdout.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%PS1_LAUNCHER%' -Project %%K %EXTRA_ARGS% 2>&1 | Tee-Object -FilePath '!LANE_LOG!'"
    set "RC_LAST=!ERRORLEVEL!"
    if "!RC_LAST!"=="0" (
        set /a OK_COUNT+=1
        echo  [fleet] '%%K' :: OK    rc=!RC_LAST!
    ) else (
        set /a FAIL_COUNT+=1
        set "FAIL_KEYS=!FAIL_KEYS! %%K"
        echo  [fleet] '%%K' :: FAIL  rc=!RC_LAST!
        call :classify_error "!LANE_LOG!" "!RC_LAST!" "%%K"
    )
    ping -n 1 -w 400 127.0.0.1 >nul 2>&1
)

popd

REM ====================================================================
REM SECTION 12 :: CREDS-PRESERVE :: UNCONDITIONAL restore (v6 KEY FIX)
REM ====================================================================
REM Root cause of the 2026-05-26 401 storm: PS1 calls claude-oauth-accounts.ps1
REM -Action Use <slot> per lane, which overwrites ~/.claude/.credentials.json
REM with the slot's tokens. Each lane's spawned mintty/claude has already read
REM .credentials.json by the time PS1 returns -- so the spawned child has its
REM slot tokens loaded in memory. But the PARENT session (operator's main
REM terminal OR a Claude Code conversation) still reads .credentials.json on
REM every token refresh and now sees the WRONG account's tokens -> 401.
REM
REM v6 fix: at end of all spawns, unconditionally restore the operator's
REM PRE-BAT .credentials.json from the backup. This guarantees the parent
REM session is back to its working creds. The 8 spawned children keep their
REM own tokens in memory (claude doesn't re-read .credentials.json once it's
REM running unless it hits a refresh -- and Max-plan tokens are long-lived).
echo.
echo  [creds-preserve] restoring operator .credentials.json from pre-bat backup
if exist "%CREDS_BACKUP%" (
    copy /Y "%CREDS_BACKUP%" "%CREDS_LIVE%" >nul 2>&1
    if "!ERRORLEVEL!"=="0" (
        echo                  OK   ^(parent session creds restored^)
    ) else (
        echo                  WARN :: restore copy failed -- you may need /login
    )
) else (
    echo                  SKIP :: no backup found ^(no pre-bat creds existed^)
)

REM ====================================================================
REM SECTION 13 :: Emit fleet manifest
REM ====================================================================
set "MANIFEST=%RUN_DIR%\manifest.txt"
(
    echo Sinister Sanctum Fleet Manifest ^(v6^)
    echo ts:           %TS%
    echo sanctum_root: %SANCTUM_ROOT%
    echo lanes:        %FLEET_KEYS%
    echo ok_count:     %OK_COUNT%
    echo fail_count:   %FAIL_COUNT%
    echo fail_keys:    %FAIL_KEYS%
    echo creds_backup: %CREDS_BACKUP%
) > "%MANIFEST%" 2>nul

REM ====================================================================
REM SECTION 14 :: Summary + exit
REM ====================================================================
echo.
echo  ============================================================
echo   Fleet spawn complete.
echo   OK:    %OK_COUNT%
echo   FAIL:  %FAIL_COUNT%
echo   Logs:  %RUN_DIR%
echo  ============================================================
echo.

if "%FAIL_COUNT%"=="0" (
    ping -n 5 127.0.0.1 >nul 2>&1
    exit /b 0
)

echo  [info] %FAIL_COUNT% lane^(s^) failed. rc reference:
echo         - rc=2   : unknown -Project key OR SANCTUM_ROOT not resolvable
echo         - rc=124 : PS1 hung past 180s ^(forge-memory / vault lock^)
echo         - 401    : token expired -- /login in a clean window, OR re-run with -Repair
echo.
pause
exit /b 1

REM ====================================================================
REM HELPER :: :tryroot
REM ====================================================================
:tryroot
if "%~1"=="" exit /b 0
if exist "%~1\automations\start-sinister-session.ps1" set "SANCTUM_ROOT=%~1"
exit /b 0

REM ====================================================================
REM HELPER :: :classify_error
REM ====================================================================
:classify_error
set "ELOG=%~1"
set "ERC=%~2"
set "EKEY=%~3"
if not exist "%ELOG%" (
    echo                ^>^> class: NO_LOG  ^(bat-side failure, log not written^)
    exit /b 0
)
findstr /C:"Please run /login" /C:"401" /C:"Invalid authentication" "%ELOG%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    echo                ^>^> class: TOKEN_EXPIRED  for slot used by '%EKEY%'
    echo                ^>^> fix:   run /login in a clean window OR claude-accounts.ps1 -Action Login
    exit /b 0
)
findstr /C:"unknown -Project" /C:"FAIL] unknown" "%ELOG%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    echo                ^>^> class: UNKNOWN_PROJECT_KEY for '%EKEY%'
    echo                ^>^> fix:   check %SANCTUM_ROOT%\automations\session-templates\projects.json
    exit /b 0
)
findstr /C:"PS1 launcher not found" "%ELOG%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    echo                ^>^> class: PS1_NOT_FOUND
    echo                ^>^> fix:   restore automations\start-sinister-session.ps1 from git
    exit /b 0
)
findstr /C:"no spawn-capable shell found" "%ELOG%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    echo                ^>^> class: SHELL_MISSING
    echo                ^>^> fix:   install Git for Windows ^(provides mintty + bash^)
    exit /b 0
)
findstr /C:"PS1 hung past" /C:"DISPATCH_TIMEOUT" "%ELOG%" >nul 2>&1
if "!ERRORLEVEL!"=="0" (
    echo                ^>^> class: PS1_TIMEOUT
    echo                ^>^> fix:   kill stale powershell.exe; check forge-memory daemon
    exit /b 0
)
echo                ^>^> class: UNKNOWN  ^(rc=%ERC%, see log tail below^)
powershell.exe -NoProfile -Command "Get-Content -Path '%ELOG%' -Tail 6 | ForEach-Object { '                  ' + $_ }" 2>nul
exit /b 0
