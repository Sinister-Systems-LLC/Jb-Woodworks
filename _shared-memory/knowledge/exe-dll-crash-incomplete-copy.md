> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# EXE launches with `Failed to load Python DLL ... python312.dll`

**Status:** workaround
**Tags:** pyinstaller, exe, dll, python312, sanctum-console, onedir, robocopy
**Related:** `pyinstaller-tomli-hook-missing.md`

## Problem

Double-clicking `C:\Users\Zonia\Desktop\Sanctum-Console\Sanctum-Console.exe` (or running it via Start-Process) raises a Windows MessageBox:

```
Error: Failed to load Python DLL 'C:\Users\Zonia\Desktop\Sanctum-Console\_internal\python312.dll'.
LoadLibrary: The specified module could not be found.
```

The EXE process then exits non-zero immediately.

## Why

PyInstaller `onedir` builds put the python runtime DLL beside the EXE under `_internal/`. If the deploy step copied the build folder without **including the python DLL** (e.g. a stale partial copy, an antivirus quarantine, or the EXE was running during the copy and Windows locked the DLL), the EXE bootloader can't find its interpreter and aborts before any logging is possible. The popup is raised by the PyInstaller bootloader itself, not Python — so there's no stderr to capture in process; `Start-Process` reports `[OK] launched` because the OS spawn succeeded.

## Fix

1. Verify which side is broken — DIST (build output) vs Desktop (deploy copy):
   ```powershell
   Test-Path 'D:\Sinister Sanctum\automations\window-manager\dist\Sanctum-Console\_internal\python312.dll'
   Test-Path 'C:\Users\Zonia\Desktop\Sanctum-Console\_internal\python312.dll'
   ```
2. If DIST has it and Desktop doesn't: re-sync with `robocopy /MIR` (preserves attributes, retries locks):
   ```powershell
   robocopy 'D:\Sinister Sanctum\automations\window-manager\dist\Sanctum-Console' `
            'C:\Users\Zonia\Desktop\Sanctum-Console' /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP
   ```
   `/MIR` mirrors (adds missing, deletes extras); `/R:1 /W:1` keeps retries fast.
3. If DIST is also missing the DLL: rebuild via `Build-Sanctum-Console.bat` (Thread 3) — the `collect_all('uvicorn')` block in `RKOJ.spec` (formerly `Sanctum-Console.spec`) includes the runtime; a corrupted PyInstaller install can drop it. Workaround chain: `pip install --force-reinstall pyinstaller pyinstaller-hooks-contrib`.

## Detection (for future agents)

Don't trust `Start-Process` "success." Always:

```powershell
Start-Process $exe
Start-Sleep -Seconds 5
$p = Get-Process -Name 'Sanctum-Console' -ErrorAction SilentlyContinue
if (-not $p) {
    Get-WinEvent -LogName Application -MaxEvents 30 |
        Where-Object { $_.TimeCreated -gt (Get-Date).AddMinutes(-1) -and
                       $_.Message -like '*Sanctum-Console*' } |
        Select-Object TimeCreated, ProviderName, Message | Format-List
}
```

If process is dead within 5s, Event Viewer's Application log usually has the popup text (Provider = `Application Error` or `Windows Error Reporting`).

## Speed-prevention (Thread 3)

The new `build-sanctum-console.sh` (step 8) verifies `dist/Sanctum-Console/Sanctum-Console.exe` exists AND size > 5 MB AND mtime within 5 min before declaring success. Step 9 uses `cp -ru` (only-newer) for incremental copies; pair with `robocopy /MIR` as the fallback for full re-syncs. Future `Start-Console.ps1` wrapper bakes in the Event-Viewer popup-scan above so any rebuild artifact failure surfaces immediately rather than silently.

## Discoveries

### 2026-05-19 04:40 by Sinister Sanctum
First sighting. Both Desktop and DIST copies crashed. Desktop fixed by robocopy from DIST. DIST appears to have a separate failure (process dies ~5s after launch even with the DLL present) — likely the pywebview/Edge-WebView2 chrome init when no user is in front of the screen, OR a subprocess hook in PyInstaller onedir mode. Pivoted to source-mode launch (`python desktop_app.py --no-window --port 5077`) as the live-development path; EXE rebuild + repro pending Thread 3 build pipeline so we can iterate without manual `pyinstaller` invocations.
