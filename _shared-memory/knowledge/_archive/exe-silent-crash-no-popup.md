> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# EXE process alive but server never binds; no popup, no Event Log entry

**Status:** known-issue
**Tags:** pyinstaller, exe, sanctum-console, silent-crash, uvicorn, runtime, console-false
**Related:** `exe-dll-crash-incomplete-copy.md`, `pyinstaller-tomli-hook-missing.md`

## Problem

`Sanctum-Console.exe` (PyInstaller onedir build, `console=False` in spec) launches successfully:
- Process appears in `Get-Process -Name 'Sanctum-Console'` for ~5–10 s.
- No popup error (different from `exe-dll-crash-incomplete-copy` — that one raises a MessageBox before Python starts).
- No entry in `Get-WinEvent -LogName Application` matching `Sanctum-Console`.

…but the server NEVER binds `:5077`:
- `netstat -ano | grep :5077` returns nothing.
- `curl http://127.0.0.1:5077/api/health` connection-refused indefinitely.

After ~5–20 s the process exits silently. No log line, no popup, nothing in Event Viewer.

The same source run via `python desktop_app.py --no-window --port 5077` from the venv works perfectly first try (sub-2-second bind, /api/health responds). So the bug is **specific to the frozen EXE**, not the source.

## Why (suspected)

`RKOJ.spec` (formerly `Sanctum-Console.spec`) has `console=False` (no cmd window) AND `disable_windowed_traceback=False`. In PyInstaller windowed mode, uncaught child-process exceptions go to nowhere — neither stderr (no console) nor a tracedump dialog (disabled). Likely culprits:

1. **Hidden import missed** — runtime `ImportError` for a sub-dep that `collect_all('pydantic')`/etc. didn't drag in. Pydantic v2 + uvicorn + webview + qrcode + httpx + Pillow all run their own collectors; one is dropping a module.
2. **`SHARED_MEMORY_ROOT` resolution race** — the EXE bootloader spawns from a temp `_internal` cwd; `desktop_app.py`'s root-discovery loop (env var → `D:\Sinister Sanctum` → `C:\Sinister Sanctum` → home → parent-of-parent) may pick a path with no `_shared-memory/` and crash on the first inbox/auth file read.
3. **`auth.py` HWID derivation** — calls `vol C:` via subprocess; bundled python may not have the right `PATH` to find `vol.exe` in onedir mode, crashing `derive_hwid()`.

## Fix (diagnostic next steps)

To surface the actual error we need stderr from the EXE. Two paths:

### Quick: rebuild with `console=True`
Edit `RKOJ.spec` (formerly `Sanctum-Console.spec`) — find the `EXE(...)` block, flip `console=False` to `console=True`. Rebuild via `Build-Sanctum-Console.bat`. New EXE shows a cmd window with stderr — error becomes visible. Once root-cause is identified, flip back to `False`.

### Better: runtime log hook in `desktop_app.py`
Add at the top of `main()`:

```python
import logging, sys, traceback
log_path = Path(sys._MEIPASS if hasattr(sys, "_MEIPASS") else ".").parent / "_exe-runtime.log"
logging.basicConfig(filename=str(log_path), level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")
def _excepthook(exctype, value, tb):
    logging.critical("UNCAUGHT", exc_info=(exctype, value, tb))
sys.excepthook = _excepthook
```

Then on every EXE launch the file `_exe-runtime.log` next to the EXE captures the exception. Rebuild + retest + read the log.

## Workaround (for operator unblocking)

**Source-mode is the supported path while the EXE is broken.** `Start-Sanctum-Console.bat` (Desktop) calls `Start-Console.ps1 -FromSource` which runs `.venv\Scripts\python.exe desktop_app.py --no-window --port 5077`. Works first try. Operator hits `http://127.0.0.1:5077` in any browser; full UI loads.

## Discoveries

### 2026-05-19 05:10 by Sinister Sanctum
First sighting. Both the previous build (04:07) and the fresh build (05:05, with new logo) exhibit the same silent crash. Build pipeline is healthy; runtime is broken. Operator unblocked via source-mode. Defer EXE-fix to next session; add the runtime log hook FIRST so we don't repeat this guessing game.

### 2026-05-19 05:30 by Sinister Sanctum — ROOT CAUSE + FIX
Rebuilt with `console=True` in the spec; EXE booted cleanly first try (`[OK] Sanctum console up at http://127.0.0.1:5077/`, /api/health 200, all 5 sidebar tools visible). That alone is suspicious — `console=True/False` shouldn't affect runtime correctness, only stdout visibility.

**Root cause:** my own runtime-logger excepthook (added that same session — see desktop_app.py `_install_runtime_logger`) called `sys.__stderr__.write(...)`. In PyInstaller **windowed** builds (console=False) `sys.__stderr__` is None. Touching `.write` on None throws AttributeError. That cascaded into a silent process death.

**Fix:** guard the write with `if sys.__stderr__ is not None` + try/except. Patched in desktop_app.py. After patch, console=False rebuild boots clean too.

**Generalizable lesson:** when adding ANY code to desktop_app.py that touches `sys.stdout`, `sys.stderr`, `sys.__stdin__`, `sys.__stdout__`, `sys.__stderr__` — first check `is not None`. PyInstaller windowed builds null all of these. Source-mode python won't catch the bug; only the frozen EXE will.

Status: **fixed** (flipped from `known-issue`).
