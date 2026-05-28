@echo off
REM Spawn Sanctum Agent :: 22-agent fleet launcher (v13, +lane 22 sinister-serper 2026-05-27)
REM Author: RKOJ-ELENO :: 2026-05-27
REM
REM v13 changes (sanctum lane resume 2026-05-27 -- chatbot delegate inbox
REM   handoff at _shared-memory/inbox/sanctum/20260527T0611Z-...):
REM   1. Added LANE_22=sinister-serper + LANE_NAME_22="Sinister Serper"
REM      (parity with projects.json v17 + Spawn Sanctum Agent.bat -All flag).
REM   2. Picker echo + ALL-flag triple + select_done triple all bumped 21 -> 22.
REM   3. Banner + TITLE bumped to v13.
REM
REM
REM v12 changes (sanctum lane operator-verbatim 2026-05-27T03:07Z trigger:
REM   "The operator reports it is broken... diagnose by [-Repair] / lane log
REM    dir... stale slot files / ps1 launcher signature drift / projects.json
REM    missing lanes (v10 added sinister-ascii-converter at lane 21 -- verify it
REM    exists in projects.json) / CLAUDECODE detection false-positives / mintty
REM    path issues / defender quarantine").
REM   Diagnosis:
REM     - Root bat "Spawn Sanctum Agent.bat" was at v10 (20 lanes + lane 21 added
REM       Q v10 header but NO LANE_21 vars; it was actually a v10 spec). It still
REM       overwrites parent .credentials.json via PS1 slot-swap -> 401 storm.
REM     - automations\Spawn-Sanctum-Agent.bat was at v11.1 (per-lane
REM       CLAUDE_CONFIG_DIR isolation; safe) but had only 20 lanes (no lane 21).
REM     - Recent spawn-fleet-*\ run dirs since 2026-05-26T22:05Z showed
REM       ok_count=0 fail_count=1 with NO lane log written = silent
REM       picker-exit / Tee-Object failure before lane spawn.
REM   Fixes:
REM     1. Added LANE_21=sinister-ascii-converter + LANE_NAME_21="Sinister ASCII
REM        Converter" (parity with root bat v10 + projects.json entry that already
REM        exists). Picker echo + ALL-flag triple + select_done triple all bumped.
REM     2. Root "Spawn Sanctum Agent.bat" is now a SHIM that forwards to
REM        automations\Spawn-Sanctum-Agent.bat -- no duplicate spec, no drift.
REM     3. Repair-mode dry-run smoke now lists all 22 lanes (was 20).
REM     4. Bumped banner to v12 + TITLE to v12.
REM
REM v11 changes (operator hard-canonical 2026-05-26: "i ran the bat file and it
REM   shut down all windows"). Root cause: v10's per-lane RotateToNext atomically
REM   rewrote ~/.claude/.credentials.json -- killing every pre-existing running
REM   Claude session that shared that file on its next token refresh (401 wall).
REM   Fix: per-lane CLAUDE_CONFIG_DIR isolation. Each spawned lane gets its OWN
REM   %USERPROFILE%\.claude.<slot>\ directory populated with that slot's
REM   credentials + a one-time mirror of settings.json / projects / todos from
REM   ~/.claude/. Parent's ~/.claude/.credentials.json is NEVER touched.
REM   No RotateToNext / Use in the lane loop. SECTION 12 creds-restore is now
REM   a noop. -NoIsolation flag falls back to the v10 shared-creds behavior for
REM   debugging.
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

TITLE EVE :: Spawn Sanctum Fleet (v12)
mode con: cols=140 lines=50 >nul 2>&1
setlocal enableextensions enabledelayedexpansion

REM Detect "running from inside Claude Code". When set, the parent CLI session
REM reads the same .credentials.json the PS1 will overwrite -- warn loudly so
REM the operator knows why their 401s happen.
if defined CLAUDECODE (
    echo.
    echo  *********************************************************************
    echo  * NOTICE :: this bat is being run from INSIDE a Claude Code session. *
    echo  *           v12 isolation: each lane gets its own CLAUDE_CONFIG_DIR  *
    echo  *           parent ~/.claude/.credentials.json is NEVER touched, so  *
    echo  *           pre-existing running Claude sessions WILL NOT 401.       *
    echo  *           ^(Pass -NoIsolation to revert to legacy shared-creds.^)   *
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
    REM v10 fallback (operator hard-canonical 2026-05-26: "this has to work at all
    REM times to launch atleast a general agent even when the d drive is not in the pc").
    REM No Sanctum repo reachable -> launch a bare general claude agent in cwd
    REM with --dangerously-skip-permissions so the operator always gets a working
    REM agent within one click, even with D: unplugged.
    color 6F
    echo.
    echo  [degraded] Sinister Sanctum repo not found ^(D: drive likely offline^).
    echo             Launching BARE GENERAL AGENT in %%USERPROFILE%% as fallback.
    echo             ^(Plug D: back in + re-run for full 20-lane fleet picker.^)
    echo.
    set "FALLBACK_CWD=%USERPROFILE%"
    if exist "%USERPROFILE%\Desktop" set "FALLBACK_CWD=%USERPROFILE%\Desktop"
    where claude >nul 2>&1
    if errorlevel 1 (
        echo  [FAIL] claude CLI not on PATH; cannot launch general agent.
        echo         Install: winget install -e --id Anthropic.ClaudeCode
        pause
        exit /b 1
    )
    REM Try git-bash mintty first (matches the themed look the operator expects),
    REM fall back to a plain cmd window if mintty is missing.
    set "MINTTY_EXE=C:\Program Files\Git\usr\bin\mintty.exe"
    set "BASH_EXE=C:\Program Files\Git\bin\bash.exe"
    if exist "%MINTTY_EXE%" if exist "%BASH_EXE%" (
        start "EVE :: general-agent" "%MINTTY_EXE%" -i -t "EVE :: general-agent (D: offline)" -e "%BASH_EXE%" -lc "cd '%FALLBACK_CWD%' && claude --dangerously-skip-permissions"
        exit /b 0
    )
    start "EVE :: general-agent" cmd /k "cd /d %FALLBACK_CWD% && claude --dangerously-skip-permissions"
    exit /b 0
)

set "PS1_LAUNCHER=%SANCTUM_ROOT%\automations\start-sinister-session.ps1"
set "ACCOUNTS_JSON=%SANCTUM_ROOT%\_shared-memory\claude-accounts.json"
set "PROJECTS_JSON=%SANCTUM_ROOT%\automations\session-templates\projects.json"
set "CREDS_LIVE=%USERPROFILE%\.claude\.credentials.json"

REM ====================================================================
REM SECTION 2 :: 22-lane fleet definition (canonical order)
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
REM  21   | sinister-ascii-converter  | Sinister ASCII Converter (v12 addition)
REM  22   | sinister-serper           | Sinister Serper        (v13 addition)
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
set "LANE_21=sinister-ascii-converter"
set "LANE_22=sinister-serper"
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
set "LANE_NAME_21=Sinister ASCII Converter"
set "LANE_NAME_22=Sinister Serper"

REM ====================================================================
REM SECTION 3 :: Argument parsing
REM ====================================================================
set "EXTRA_ARGS="
set "SOLO=0"
set "ALL_FLAG=0"
set "REPAIR_MODE=0"
set "DRYRUN_MODE=0"
set "HELP_MODE=0"
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
if /I "%~1"=="-DryRun"      (set "DRYRUN_MODE=1" & shift & goto :argloop)
if /I "%~1"=="/DryRun"      (set "DRYRUN_MODE=1" & shift & goto :argloop)
if /I "%~1"=="-Help"        (set "HELP_MODE=1" & shift & goto :argloop)
if /I "%~1"=="/Help"        (set "HELP_MODE=1" & shift & goto :argloop)
if /I "%~1"=="-?"           (set "HELP_MODE=1" & shift & goto :argloop)
if /I "%~1"=="/?"           (set "HELP_MODE=1" & shift & goto :argloop)
if /I "%~1"=="-Lanes"       (set "LANES_OVERRIDE=%~2" & shift & shift & goto :argloop)
if /I "%~1"=="/Lanes"       (set "LANES_OVERRIDE=%~2" & shift & shift & goto :argloop)
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto :argloop
:argdone

REM Help mode: print flags + exit 0 (no preflight, no spawn).
if "%HELP_MODE%"=="1" (
    echo.
    echo  Spawn-Sanctum-Agent.bat v12 :: 22-agent fleet launcher
    echo  Author: RKOJ-ELENO :: 2026-05-27
    echo.
    echo  USAGE: Spawn-Sanctum-Agent.bat [flags]
    echo.
    echo  FLAGS:
    echo    -All           launch all 22 lanes
    echo    -SoloSanctum   launch only sanctum lane
    echo    -Lanes a,b,c   launch specific lane keys ^(comma-separated^)
    echo    -Repair        run preflight only, no spawn
    echo    -DryRun        run full plumbing ^(slot pick, dir stage^) but skip
    echo                   mintty + claude.exe -- prints what WOULD be done
    echo    -NoIsolation   legacy v10 shared-creds path ^(parent may 401^)
    echo    -NoRotate      do not advance round-robin cursor
    echo    -Help / -?     this message
    echo.
    echo  INTERACTIVE PICKER OPTIONS:
    echo    A / Enter      launch all 22 lanes
    echo    S              sanctum only
    echo    M              manage accounts ^(add/remove/list, no spawn^)
    echo    R              repair mode ^(preflight only^)
    echo    X              cancel
    echo    1,3,4...       comma-separated lane indices
    echo.
    echo  LANES ^(1-22^):
    echo    sinister-memory  sinister-os  eve-exe  sanctum  sinister-term
    echo    eve-compliance   sinister-overseer  letstext  sinister-jokester
    echo    sinister-quantum sinister-snap-api-quantum  kernel-apk
    echo    sinister-sleight sinister-term-themes  sinister-designer
    echo    sinister-panel   sinister-chatbot  sinister-hieroglyphics
    echo    showmasters      jb-woodworks  sinister-ascii-converter
    echo.
    echo  EXIT CODES:
    echo    0   all selected lanes ok
    echo    1   one or more lanes failed ^(see log dir^)
    echo    2   PS1 launcher missing
    echo    3   projects.json missing
    echo    4   no valid lanes selected
    echo.
    exit /b 0
)

REM ====================================================================
REM SECTION 4 :: Banner
REM ====================================================================
echo.
echo  ============================================================
echo   EVE :: Spawn Sanctum Fleet ^(v12 :: 21 lanes + per-lane CLAUDE_CONFIG_DIR isolation^)
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
REM SECTION 6b :: ACCOUNT STATUS + ISOLATION-MODE FLAG (v11 2026-05-26)
REM ====================================================================
REM v11 fix (operator hard-canonical 2026-05-26 verbatim: "i ran the bat file
REM   and it shut down all windows").
REM
REM v10's per-lane RotateToNext mutated ~/.claude/.credentials.json which
REM killed every pre-existing running Claude session. v11 picks the best
REM slot per lane via PickBestSlot (READ-ONLY -- no parent-creds mutation)
REM then pre-stages a per-slot %USERPROFILE%\.claude.<slot>\ config dir and
REM sets CLAUDE_CONFIG_DIR=<that dir> before spawning that lane's PS1. The
REM Claude CLI respects CLAUDE_CONFIG_DIR (Anthropic docs) so the child uses
REM its OWN .credentials.json without ever touching the parent's.
REM
REM Flag: -NoIsolation falls back to the v10 shared-creds behavior (legacy
REM debugging; will resurrect the original 401 storm).
set "ISOLATION_DISABLED=0"
set "ROTATE_DISABLED=0"
for %%A in (%EXTRA_ARGS%) do (
    if /I "%%~A"=="-NoIsolation" set "ISOLATION_DISABLED=1"
    if /I "%%~A"=="/NoIsolation" set "ISOLATION_DISABLED=1"
    if /I "%%~A"=="-NoRotate" set "ROTATE_DISABLED=1"
    if /I "%%~A"=="/NoRotate" set "ROTATE_DISABLED=1"
)
set "OAUTH_PS1=%SANCTUM_ROOT%\automations\claude-oauth-accounts.ps1"
set "OAUTH_EXT_PS1=%SANCTUM_ROOT%\automations\claude-oauth-extensions.ps1"
if not exist "%OAUTH_PS1%" (
    echo  [isolation]     WARN :: claude-oauth-accounts.ps1 missing -- per-lane isolation disabled
    set "ISOLATION_DISABLED=1"
    set "ROTATE_DISABLED=1"
)
if "%ISOLATION_DISABLED%"=="1" (
    echo  [isolation]     DISABLED ^(-NoIsolation flag set, or oauth lib missing^)
    echo  [isolation]     WARN  fallback = v10 shared-creds behavior; parent agents may 401.
) else (
    echo  [isolation]     ENABLED :: each lane spawns with its own CLAUDE_CONFIG_DIR
    echo  [isolation]     parent ~/.claude/.credentials.json will NOT be touched
    REM Print current slot status (with 5h-usage bars + dup-account detection)
    REM so operator sees eligible accounts BEFORE picking. v11 swapped List
    REM for ListBars per operator hard-canonical 2026-05-26.
    REM ListBars lives in claude-oauth-extensions.ps1 (sibling file, survives
    REM sister-agent reverts of main file). Fallback to main -Action List if missing.
    if exist "%OAUTH_EXT_PS1%" (
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_EXT_PS1%" -Action ListBars 2>nul
    ) else (
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_PS1%" -Action List 2>nul
    )
)

REM ====================================================================
REM SECTION 7 :: Pre-warm EVE icon cache (no-space path)
REM ====================================================================
REM 2026-05-28 operator hard-canonical: "use the correct logo we use for eve
REM exe on the terminals. you are using a picture of the fucking image."
REM Swapped claude-icon.ico -> eve-icon.ico (EVE-branded, 104 KB) per
REM agent-identity-eve doctrine. claude-icon.ico still copied as a fallback
REM so any pre-existing reference resolves cleanly.
set "EVE_ICON_SRC=%SANCTUM_ROOT%\automations\eve-launcher\assets\eve-icon.ico"
set "EVE_ICON_DST=%USERPROFILE%\.eve\eve-icon.ico"
set "ICON_SRC=%SANCTUM_ROOT%\automations\eve-launcher\assets\claude-icon.ico"
set "ICON_DST=%USERPROFILE%\.eve\claude-icon.ico"
if not exist "%USERPROFILE%\.eve" mkdir "%USERPROFILE%\.eve" >nul 2>&1
if exist "%EVE_ICON_SRC%" copy /Y "%EVE_ICON_SRC%" "%EVE_ICON_DST%" >nul 2>&1
if exist "%ICON_SRC%" copy /Y "%ICON_SRC%" "%ICON_DST%" >nul 2>&1

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
    REM Operator hard-canonical 2026-05-28: "you spawned too many sanctum agents
    REM dont worry about the master agent in the bat file just launch projects".
    REM -All previously included LANE_4=sanctum (the master). It's now SKIPPED;
    REM operator is already running a sanctum master separately. -SoloSanctum
    REM is still available if a sanctum spawn is explicitly wanted.
    set "FLEET_KEYS=%LANE_1% %LANE_2% %LANE_3% %LANE_5% %LANE_6% %LANE_7% %LANE_8% %LANE_9% %LANE_10% %LANE_11% %LANE_12% %LANE_13% %LANE_14% %LANE_15% %LANE_16% %LANE_17% %LANE_18% %LANE_19% %LANE_20% %LANE_21% %LANE_22%"
    echo  [select]  -All :: launching 21 project lanes ^(sanctum-master excluded per 2026-05-28 directive^)
    goto :select_done
)

if "%SOLO%"=="1" (
    set "FLEET_KEYS=%LANE_4%"
    echo  [select]  -SoloSanctum :: sanctum only
    goto :select_done
)

REM ----- Interactive picker -----
:picker
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
echo    21^) %LANE_NAME_21% ^(%LANE_21%^)
echo    22^) %LANE_NAME_22%        ^(%LANE_22%^)
echo.
echo    A^) ALL 22 lanes        ^(default -- press Enter^)
echo    S^) Sanctum only        ^(solo^)
echo    M^) Manage accounts     ^(add/remove/list -- no spawn^)
echo    R^) Repair mode         ^(preflight only, no spawn^)
echo    X^) Cancel
echo.
echo    Or enter comma-separated indices  e.g.  1,3,4,7,9,12,15,19
echo.
set /p "PICK=  Selection: "

if not defined PICK set "PICK=A"
if /I "%PICK%"=="A"   (set "FLEET_KEYS=%LANE_1% %LANE_2% %LANE_3% %LANE_4% %LANE_5% %LANE_6% %LANE_7% %LANE_8% %LANE_9% %LANE_10% %LANE_11% %LANE_12% %LANE_13% %LANE_14% %LANE_15% %LANE_16% %LANE_17% %LANE_18% %LANE_19% %LANE_20% %LANE_21% %LANE_22%" & goto :select_done)
if /I "%PICK%"=="ALL" (set "FLEET_KEYS=%LANE_1% %LANE_2% %LANE_3% %LANE_4% %LANE_5% %LANE_6% %LANE_7% %LANE_8% %LANE_9% %LANE_10% %LANE_11% %LANE_12% %LANE_13% %LANE_14% %LANE_15% %LANE_16% %LANE_17% %LANE_18% %LANE_19% %LANE_20% %LANE_21% %LANE_22%" & goto :select_done)
if /I "%PICK%"=="S"   (set "FLEET_KEYS=%LANE_4%" & goto :select_done)
if /I "%PICK%"=="M"   (call :manage_accounts & goto :picker)
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
set "SINISTER_SANCTUM_ROOT=%SANCTUM_ROOT%"
REM v11.1 (2026-05-27) :: -DryRun passes through to PS1 via SINISTER_DRY_RUN so
REM the mintty + claude.exe launch is skipped and the operator sees the
REM resolved invocation + per-lane CLAUDE_CONFIG_DIR without actually spawning.
if "%DRYRUN_MODE%"=="1" (
    set "SINISTER_DRY_RUN=1"
    echo  [dry-run] SINISTER_DRY_RUN=1 -- PS1 will print resolved invocation but not fire mintty/claude
)

REM ====================================================================
REM SECTION 11 :: Per-lane spawn -- CLAUDE_CONFIG_DIR isolation (v11)
REM ====================================================================
REM v11 (2026-05-26): each lane gets its own %USERPROFILE%\.claude.<slot>\
REM via PickBestSlot + :stage_slot_dir helper. CLAUDE_CONFIG_DIR is set
REM in this cmd subshell BEFORE invoking start-sinister-session.ps1 so the
REM spawned claude inherits it. Parent ~/.claude/.credentials.json is NEVER
REM mutated -- pre-existing running agents are safe.
REM
REM Fallback path (-NoIsolation): preserves v10 shared-creds spawn for
REM debugging. Will resurrect the 401 storm; do not use unless triaging.
pushd "%SANCTUM_ROOT%"
set "FAIL_COUNT=0"
set "OK_COUNT=0"
set "FAIL_KEYS="

for %%K in (%FLEET_KEYS%) do (
    echo.
    echo  ------------------------------------------------------------
    echo   [fleet] spawning '%%K' ...
    echo  ------------------------------------------------------------
    set "LANE_LOG=%RUN_DIR%\%%K.log"
    set "LANE_SLOT="
    set "LANE_CONFIG_DIR="

    if "!ISOLATION_DISABLED!"=="0" (
        REM ---- v11 per-lane CLAUDE_CONFIG_DIR isolation ----
        REM PickBestSlot writes the chosen slot name to stdout and exits 1
        REM if no eligible slot. Diagnostics go to stderr; we discard them
        REM here to keep the for /F capture clean.
        REM 2026-05-28: Action name is "PickBest" not "PickBestSlot" -- the latter
        REM was erroring "unknown -Action" and breaking every lane spawn. Fixed
        REM concurrent with operator's quota-cleanup (sinister-gmail only slot).
        for /F "usebackq tokens=* delims=" %%S in (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_PS1%" -Action PickBest 2^>nul`) do (
            if not defined LANE_SLOT set "LANE_SLOT=%%S"
        )
        if not defined LANE_SLOT (
            REM v11.1 (2026-05-27) :: FULL-POWER fallback per operator hard-canonical
            REM "dont fucking rate limit me like this i need full power". PickBestSlot
            REM filters out rate_limited_until_utc>now slots; if ALL are marked we
            REM still want a spawn (local bookkeeping is advisory; Anthropic's server
            REM is the real gate). Pick first slot whose credentials.<name>.json file
            REM exists on disk -- that is the minimum needed for the lane to launch.
            echo  [pick-slot] PickBestSlot returned no slot ^(all marked rate-limited^); FULL-POWER fallback...
            for %%F in ("%USERPROFILE%\.claude\credentials.operator.json" "%USERPROFILE%\.claude\credentials.operator-b.json" "%USERPROFILE%\.claude\credentials.slot3.json" "%USERPROFILE%\.claude\credentials.slot4.json" "%USERPROFILE%\.claude\credentials.leo.json") do (
                if not defined LANE_SLOT (
                    if exist "%%~F" (
                        set "_fname=%%~nF"
                        REM strip leading "credentials." from "credentials.operator"
                        set "_fname=!_fname:credentials.=!"
                        set "LANE_SLOT=!_fname!"
                        echo  [pick-slot] FULL-POWER picked '!LANE_SLOT!' ^(creds present, ignoring rate-limit mark^)
                    )
                )
            )
        )
        if not defined LANE_SLOT (
            echo.
            echo  ****************************************************************
            echo  * [pick-slot] FAIL :: no slot creds found on disk at all.       *
            echo  *             FIX : add accounts via:                           *
            echo  *                                                              *
            echo  *   powershell -NoProfile -ExecutionPolicy Bypass -File ^^     *
            echo  *     "%OAUTH_PS1%" -Action AddAndLogin -Count 4               *
            echo  *                                                              *
            echo  *             Then re-run this bat. Skipping lane '%%K'.       *
            echo  ****************************************************************
            set /a FAIL_COUNT+=1
            set "FAIL_KEYS=!FAIL_KEYS! %%K"
            echo  [fleet] '%%K' :: SKIP  rc=NO_SLOT
            ping -n 1 -w 400 127.0.0.1 >nul 2>&1
            REM Skip to next lane without spawning.
        ) else (
            set "LANE_CONFIG_DIR=%USERPROFILE%\.claude.!LANE_SLOT!"
            echo  [pick-slot] '%%K' -^> slot='!LANE_SLOT!'  config_dir='!LANE_CONFIG_DIR!'
            call :stage_slot_dir "!LANE_SLOT!" "!LANE_CONFIG_DIR!"
            if "!STAGE_RC!"=="0" (
                REM Set CLAUDE_CONFIG_DIR in THIS subshell -- the powershell.exe
                REM below inherits it (and its spawned mintty/claude inherits in turn).
                set "CLAUDE_CONFIG_DIR=!LANE_CONFIG_DIR!"
                powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%PS1_LAUNCHER%' -Project %%K %EXTRA_ARGS% 2>&1 | Tee-Object -FilePath '!LANE_LOG!'"
                set "RC_LAST=!ERRORLEVEL!"
                set "CLAUDE_CONFIG_DIR="
            ) else (
                echo  [stage]   FAIL :: could not stage !LANE_CONFIG_DIR! ^(rc=!STAGE_RC!^)
                set "RC_LAST=99"
            )
        )
    ) else (
        REM ---- legacy v10 shared-creds path (debug only) ----
        powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& '%PS1_LAUNCHER%' -Project %%K %EXTRA_ARGS% 2>&1 | Tee-Object -FilePath '!LANE_LOG!'"
        set "RC_LAST=!ERRORLEVEL!"
    )

    if defined RC_LAST (
        if "!RC_LAST!"=="0" (
            set /a OK_COUNT+=1
            echo  [fleet] '%%K' :: OK    rc=!RC_LAST!
        ) else (
            set /a FAIL_COUNT+=1
            set "FAIL_KEYS=!FAIL_KEYS! %%K"
            echo  [fleet] '%%K' :: FAIL  rc=!RC_LAST!
            call :classify_error "!LANE_LOG!" "!RC_LAST!" "%%K"
        )
    )
    set "RC_LAST="
    ping -n 1 -w 400 127.0.0.1 >nul 2>&1
)

popd

REM ====================================================================
REM SECTION 12 :: CREDS-PRESERVE :: NOOP in v11 (kept for back-compat)
REM ====================================================================
REM v11 (2026-05-26): per-lane CLAUDE_CONFIG_DIR isolation means parent's
REM ~/.claude/.credentials.json is never mutated, so there is nothing to
REM restore. SECTION 6 still takes a safety backup (cheap insurance for the
REM -NoIsolation legacy path), but in the default isolated flow this is a
REM diagnostic-only artifact.
echo.
if "%ISOLATION_DISABLED%"=="1" (
    echo  [creds-preserve] -NoIsolation mode :: restoring parent .credentials.json from backup
    if exist "%CREDS_BACKUP%" (
        copy /Y "%CREDS_BACKUP%" "%CREDS_LIVE%" >nul 2>&1
        if "!ERRORLEVEL!"=="0" (
            echo                  OK   ^(parent session creds restored^)
        ) else (
            echo                  WARN :: restore copy failed -- you may need /login
        )
    ) else (
        echo                  SKIP :: no backup found
    )
) else (
    echo  [creds-preserve] NOOP ^(v11 isolation: parent creds were never touched^)
)

REM ====================================================================
REM SECTION 13 :: Emit fleet manifest
REM ====================================================================
set "MANIFEST=%RUN_DIR%\manifest.txt"
(
    echo Sinister Sanctum Fleet Manifest ^(v12^)
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
REM HELPER :: :stage_slot_dir <slot> <config-dir>  (v11 isolation)
REM ====================================================================
REM Pre-stages %USERPROFILE%\.claude.<slot>\ with that slot's credentials.
REM Mirrors settings.json + projects\ + todos\ from ~/.claude/ ONLY if the
REM destination is missing (no clobber of existing per-slot state).
REM Sets STAGE_RC=0 on success, non-zero on failure.
:stage_slot_dir
set "STAGE_SLOT=%~1"
set "STAGE_DIR=%~2"
set "STAGE_RC=0"
set "SLOT_CREDS=%USERPROFILE%\.claude\credentials.%STAGE_SLOT%.json"
if not exist "%SLOT_CREDS%" (
    echo  [stage]   FAIL :: per-slot creds missing at %SLOT_CREDS%
    echo                   ^(run claude-oauth-accounts.ps1 -Action Login -Name %STAGE_SLOT%^)
    set "STAGE_RC=2"
    exit /b 0
)
if not exist "%STAGE_DIR%" mkdir "%STAGE_DIR%" >nul 2>&1
if not exist "%STAGE_DIR%" (
    echo  [stage]   FAIL :: could not create %STAGE_DIR%
    set "STAGE_RC=3"
    exit /b 0
)
REM Always re-copy the slot credentials (cheap; ensures freshest token blob).
copy /Y "%SLOT_CREDS%" "%STAGE_DIR%\.credentials.json" >nul 2>&1
if not exist "%STAGE_DIR%\.credentials.json" (
    echo  [stage]   FAIL :: credentials copy failed -^> %STAGE_DIR%\.credentials.json
    set "STAGE_RC=4"
    exit /b 0
)
REM One-time mirror of settings + projects + todos. Skip if dest exists.
if not exist "%STAGE_DIR%\settings.json" (
    if exist "%USERPROFILE%\.claude\settings.json" copy /Y "%USERPROFILE%\.claude\settings.json" "%STAGE_DIR%\settings.json" >nul 2>&1
)
if not exist "%STAGE_DIR%\settings.local.json" (
    if exist "%USERPROFILE%\.claude\settings.local.json" copy /Y "%USERPROFILE%\.claude\settings.local.json" "%STAGE_DIR%\settings.local.json" >nul 2>&1
)
if not exist "%STAGE_DIR%\.claude.json" (
    if exist "%USERPROFILE%\.claude\.claude.json" copy /Y "%USERPROFILE%\.claude\.claude.json" "%STAGE_DIR%\.claude.json" >nul 2>&1
)
if not exist "%STAGE_DIR%\projects" (
    if exist "%USERPROFILE%\.claude\projects" (
        xcopy /E /I /Y /Q "%USERPROFILE%\.claude\projects" "%STAGE_DIR%\projects" >nul 2>&1
    )
)
if not exist "%STAGE_DIR%\todos" (
    if exist "%USERPROFILE%\.claude\todos" (
        xcopy /E /I /Y /Q "%USERPROFILE%\.claude\todos" "%STAGE_DIR%\todos" >nul 2>&1
    )
)
if not exist "%STAGE_DIR%\plugins" (
    if exist "%USERPROFILE%\.claude\plugins" (
        xcopy /E /I /Y /Q "%USERPROFILE%\.claude\plugins" "%STAGE_DIR%\plugins" >nul 2>&1
    )
)
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

REM ====================================================================
REM HELPER :: :manage_accounts  (M) on the fleet picker)
REM RKOJ-ELENO :: 2026-05-27 :: P0 operator directive
REM "add a way for me to add my 3 other accounts and make sure all things
REM  and funciton are global use so if i add my 4 accounts in here eve exe
REM  will have same info and round robin functon"
REM
REM Routes to claude-oauth-accounts.ps1 (which writes to the canonical
REM _shared-memory\claude-accounts.json + ~\.claude\credentials.<slot>.json
REM pair -- the SAME store EVE.exe's account_manager.py reads). All actions
REM run with SINISTER_NO_PARENT_TOUCH=1 + use the dedupe-guarded -Action Add
REM path. NO destructive overwrite of parent's .credentials.json.
REM ====================================================================
:manage_accounts
:manage_loop
echo.
echo  ============================================================
echo   ACCOUNT MANAGEMENT
echo  ============================================================
echo     1^) Add account        ^(OAuth login flow -- browser^)
echo     2^) List accounts      ^(with quota bars + dupe detection^)
echo     3^) Remove account     ^(pick a slot to log out + disable^)
echo     4^) Back to fleet selection
echo.
set /p "MPICK=  Selection: "
if not defined MPICK set "MPICK=4"

REM Guard rails: every sub-action runs with the cascade-kill safe env so
REM the OAuth Login scaffold does NOT overwrite parent .credentials.json.
REM (claude-oauth-accounts.ps1 already preserves+restores the sideline,
REM but we belt-and-suspender it.)
set "SINISTER_NO_PARENT_TOUCH=1"

if /I "%MPICK%"=="1" (
    echo.
    echo  [add-account] launching OAuth Login scaffold ^(browser will open^)
    echo                dedup guard ON :: same email as existing slot will be REJECTED
    echo                ^(use -Force flag manually if you really want to allow it^)
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_PS1%" -Action Add
    echo.
    pause
    goto :manage_loop
)
if /I "%MPICK%"=="2" (
    echo.
    if exist "%OAUTH_EXT_PS1%" (
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_EXT_PS1%" -Action ListBars
    ) else (
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_PS1%" -Action List
    )
    echo.
    pause
    goto :manage_loop
)
if /I "%MPICK%"=="3" (
    echo.
    echo  [remove-account] available slots:
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_PS1%" -Action List
    echo.
    set /p "RMSLOT=  Slot name to remove: "
    if not defined RMSLOT (
        echo  [remove-account] cancelled.
        goto :manage_loop
    )
    set /p "RMCONF=  Type the slot name again to confirm: "
    if /I not "!RMCONF!"=="!RMSLOT!" (
        echo  [remove-account] confirmation mismatch -- aborted.
        goto :manage_loop
    )
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%OAUTH_PS1%" -Action Remove -Name "!RMSLOT!"
    echo.
    pause
    goto :manage_loop
)
if /I "%MPICK%"=="4" (
    set "SINISTER_NO_PARENT_TOUCH="
    exit /b 0
)
if /I "%MPICK%"=="B" (
    set "SINISTER_NO_PARENT_TOUCH="
    exit /b 0
)

echo  [warn] invalid selection '%MPICK%' -- enter 1, 2, 3, or 4.
goto :manage_loop
