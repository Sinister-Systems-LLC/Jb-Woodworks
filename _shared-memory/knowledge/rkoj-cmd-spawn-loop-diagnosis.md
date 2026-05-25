<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: RKOJ console-daemon.bat cmd-spawn storm — 5 attempts/hour cap + crashing EXE = visible cmd-window flash storm

**Slug:** rkoj-cmd-spawn-loop-diagnosis
**First discovered:** 2026-05-19 14:15 by operator (visible flash storm)
**Last updated:** 2026-05-19 14:30 by Sinister Sanctum master (diagnosis + brain entry)
**Status:** fixed (root cause was crashing EXE; rebuild closed it. Logging-format quirk remains as low-priority cleanup.)
**Tags:** rkoj, console-daemon, scheduled-task, respawn, cmd-flash, exe-crash, daemon-bat, restart-loop, cmd-substring-expansion

## Problem

Operator observed: "100s of cmd consoles open and close" in rapid succession on the desktop. Frustrating + visually scary even though the underlying daemon contract worked correctly.

## Why it happens

`automations/window-manager/console-daemon.bat` is the auto-restart loop for RKOJ.exe. Behavior contract (per its header comments):

- Prefer frozen `dist/RKOJ/RKOJ.exe` (~250 ms faster boot than source mode)
- Restart loop with 3-second sleep between attempts
- Max 5 restarts per rolling hour; after cap, exit non-zero so Task Scheduler's outer cap (RestartCount=5 / Interval=1 min) takes over → effective ceiling ~25 restarts/hour, then full stop until next logon

When RKOJ.exe crashes immediately on launch (the case during the master-sweep session: first the `_shared/` underscore-collision missing-bundle bug, then the `select.pyd` missing from PyInstaller's autodetect of the multiprocessing runtime hook chain), the daemon bat:

1. spawns RKOJ.exe in a fresh cmd window (window briefly visible)
2. RKOJ crashes on DLL-load (Windows shows the "Failed to load Python DLL" popup; bat's child cmd inherits the failure)
3. cmd window exits
4. daemon sleeps 3s + spawns next attempt

5 attempts complete in ~16 + 19 + 12 + 44 = ~91 seconds (per the actual `_daemon-logs/daemon.log` trace from 2026-05-19 10:01). Then the bat exits, Task Scheduler kicks in with another wave (5 more attempts ~91s later), and the cycle repeats up to ~25 launches/hour.

Multiply that by any STALE daemon-bat instances stacked from prior sessions (this session had 4 concurrent `build-sanctum-console.sh` processes + an unknown number of console-daemon.bats), and the visible cmd-window count balloons.

### Side-finding: cmd substring-variable expansion failure in daemon.log

`daemon.log` after 2026-05-19 10:01 shows entries like:
```
[~0,4LOG_DT:~4,2LOG_DT:~6,2LOG_DT:~8,2LOG_DT:~10,2LOG_DT:~12,2] ==== console-daemon start ====
```

The bat uses `%LOG_DT:~0,4%` substring-extraction syntax in cmd, but at this call site the `%` characters got dropped (likely a missing `setlocal EnableDelayedExpansion` scope or a stray newline breaking the variable). Result: the literal string `~0,4LOG_DT:...` appears in the log instead of the year/month/day/HH/MM/SS. A side-effect file `_daemon-logs/console-~0,8LOCAL_DT` (literal name, zero bytes) gets created on every launch because the `%LOG_DT:~0,8%` in the filename position similarly fails to expand. Low priority — daemon still functions, just the log timestamps are unreadable.

## Fix or workaround

### Root cause fix (shipped)

Stop the EXE from crashing. The two underlying bugs (HR-B `_shared` bundle gap + missing `select.pyd` runtime-hook chain) were fixed in this same master-sweep:

1. `sanctum-shared-rename-pyinstaller-collision.md` — rename `_shared/` → `sanctum_shared/` + use `collect_submodules + collect_data_files`
2. `pyinstaller-distutils-exclude-collision.md` — remove `distutils` from spec excludes + add explicit hiddenimports for `select`, `_socket`, `selectors`, `multiprocessing.*`, `asyncio.*`

After both fixes, RKOJ.exe boots cleanly + the daemon-bat sees `rc=0` from the EXE on attempt 1 and the loop never enters its rapid-restart phase.

### Cleanup steps (for any operator session that hits this)

```bash
# 1. Kill all RKOJ.exe + daemon-bat instances
powershell.exe -Command "Get-CimInstance Win32_Process | Where-Object {\$_.CommandLine -match 'console-daemon|RKOJ\.exe'} | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }"

# 2. Verify ports 5077 + 5078 free
powershell.exe -Command "Get-NetTCPConnection -LocalPort 5077,5078 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess"

# 3. Remove broken-timestamp log files (no payload)
rm "D:/Sinister Sanctum/automations/window-manager/_daemon-logs/"console-~* 2>/dev/null

# 4. Rebuild + redeploy (if EXE bundle is the underlying problem)
# See `sanctum-shared-rename-pyinstaller-collision.md` + `pyinstaller-distutils-exclude-collision.md`

# 5. Click RKOJ.bat to relaunch cleanly
```

### Future hardening (deferred — operator can do later)

- Fix `console-daemon.bat` substring-variable expansion (probably needs `setlocal EnableDelayedExpansion` wrap around the timestamp call sites, plus moving `%LOG_DT:~0,8%` into a `for /f` extraction since some cmd builds parse the `:` inside `%var:~A,B%` as a label separator when the surrounding context has a `:` in it)
- Lower the daemon's 5-restart-per-hour cap to 3 so a crashing EXE causes less cmd-window noise (with the downside that a transient crash needs an operator re-click)
- Add an alert when the daemon exits-without-success — broadcast `[ALERT]` to operator's inbox so a stale crashing daemon doesn't go unnoticed

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 14:30 by Sinister Sanctum master
Verified end-to-end. Pre-fix daemon.log shows 5 attempts with `rc=-1` / `rc=1` / `rc=0` (the latter is a buggy success-then-die — RKOJ would exit clean but with no actual server lifetime). Post-fix the rebuilt RKOJ.exe boots cleanly + scheduler loop starts. The cmd-spawn storm cannot recur as long as the bundle stays intact. If future EXE rebuilds introduce a similar load-time crash, operator's diagnostic flow is: (1) check task manager for storm of `RKOJ.exe` + `cmd.exe` instances, (2) check `_daemon-logs/daemon.log` tail for `rc=-1` lines, (3) check `_exe-runtime.log` for the actual Python traceback that caused exit, (4) fix the bug + rebuild.

### 2026-05-19 14:15 by operator (verbatim trigger)
"also nothing fucking works and like 100s of cmd consoles open and close and its all shit"

## Related topics

- [sanctum-shared-rename-pyinstaller-collision](./sanctum-shared-rename-pyinstaller-collision.md) — first underlying EXE-crash cause
- [pyinstaller-distutils-exclude-collision](./pyinstaller-distutils-exclude-collision.md) — second underlying EXE-crash cause
- [exe-silent-crash-no-popup](./exe-silent-crash-no-popup.md) — different crash class (sys.__stderr__ None)
- [exe-dll-crash-incomplete-copy](./exe-dll-crash-incomplete-copy.md) — robocopy mid-build leaves partial bundle
- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md)
