# EVE Crash Detector :: CLI Reference

Author: RKOJ-ELENO :: 2026-05-25

Auto-detects when EVE.exe crashes / hangs and runs the operator-blessed
`C:\Users\Zonia\Desktop\Kill-Stuck-EVE.bat` rescue script. Also blocks
EVE.exe rebuilds while the binary is running.

## Why this exists

Operator (verbatim 2026-05-25 ~06:14Z): *"I need you to detect eve crashes
and run this especially if they crash before you compile an exe. but take
note you can still update while exe is running, we should have made this a
feature."* → fix shipped: rebuilds now auto-kill the running EVE.exe first
via the `--pre-compile` hook in `verify-eve-features.ps1`.

## Five crash signals

| ID | Name | Fires when |
|----|------|------------|
| A | Zombie process | EVE.exe PID alive, 0% CPU two samples, status stopped/zombie OR alive >5min idle |
| B | No main window | EVE.exe alive >15s but `EnumWindows` finds zero visible window owned by its PID |
| C | mintty exit 126 | Recent `eve-incidents.jsonl` rows contain `exit 126` / `mintty.*126` (last 5 min) |
| D | Orphan conhost | `conhost.exe` whose parent PID is dead (EVE.exe died, conhost stayed) |
| E | Stale lock file | `~/.eve/eve.lock` or `_shared-memory/.eve-running.lock` older than 30 min with no matching live EVE.exe |

Any single signal triggers crash state. Signal B is the one most likely to
fire on the operator's machine — historically EVE has hung during init
(spinner with no window paint) more often than zombie / file-lock scenarios.

## Commands

### Scan (detect only)
```
python automations/eve_crash_detector.py --scan
```
Exit 0 healthy, 1 crashed. Use `--json` for machine-readable output.

### Scan + auto-rescue
```
python automations/eve_crash_detector.py --scan --auto-kill
```
On detection: runs `Kill-Stuck-EVE.bat` and appends to
`_shared-memory/eve-crash-log.jsonl`.

### Pre-compile guard (always-kill before rebuild)
```
python automations/eve_crash_detector.py --pre-compile
```
Graceful SIGTERM 5s -> force kill via Kill-Stuck-EVE.bat. Exit 0 cleared,
exit 2 still alive (rebuild should abort). Add `--dry-run` to preview.

`verify-eve-features.ps1` invokes this automatically at the top of every
rebuild attempt, so the operator never sees "EXE in use" PyInstaller errors.

### Status / recent events
```
python automations/eve_crash_detector.py --status
```
Prints current EVE.exe processes + last 5 events from the crash log. Safe
to run when log is absent.

## Install the 5-minute watchdog schtask

```
python automations/install_eve_crash_detector.py
```
Creates `SinisterEveCrashWatchdog`, runs every 5 min:
```
python "D:\Sinister Sanctum\automations\eve_crash_detector.py" --scan --auto-kill
```

Uninstall: `python automations/install_eve_crash_detector.py --uninstall`
Preview only: add `--dry-run` to either invocation.

## Logs

- `_shared-memory/eve-crash-log.jsonl` — every auto-kill, pre-compile clear,
  pre-compile fail, and scan-detected event (one JSON object per line).
- `_shared-memory/eve-incidents.jsonl` — source of signal C input
  (mintty exit-126 detection).

## Disabling

- Stop schtask: `schtasks /End /TN SinisterEveCrashWatchdog`
- Remove schtask: `python automations/install_eve_crash_detector.py --uninstall`
- Bypass pre-compile guard: comment out the single-line invocation at the
  top of `automations/verify-eve-features.ps1`.

## Safety guarantees

- ONLY invokes `Kill-Stuck-EVE.bat` (title-targeted: `Select EVE*`,
  `EVE ::*`, `Sinister Start*` + image `EVE.exe`). Never broad-kills
  `claude.exe`, `mintty.exe`, or any operator session.
- Idempotent install (`schtasks /F` recreates without orphans).
- Dry-run flags on both detector + installer for safe preview.
