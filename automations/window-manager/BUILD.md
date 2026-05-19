> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# RKOJ.exe — Build Pipeline

One-click rebuild of `dist/RKOJ/RKOJ.exe`. Bash-driven for speed; PowerShell only for things that touch Windows APIs (scheduled task registration — see `AUTOSTART.md`).

## Operator entry-point

Double-click:

```
C:\Users\Zonia\Desktop\Build-Sanctum-Console.bat
```

That .bat is a thin wrapper. It locates `git-bash` and exec's the real builder:

```
D:\Sinister Sanctum\automations\window-manager\build-sanctum-console.sh
```

## Speed budget

| Path  | Target | What happens |
|---|---|---|
| Warm  | < 30 s | Steps 4-6 skipped (env + tomli hook already present). PyInstaller incremental. |
| Cold  | < 90 s | Full venv create + pip install + force-reinstall hooks-contrib + full PyInstaller. |
| Fail  | < 5 s  | Step 1 (missing src) or step 2 (no Python) detects + dies before any heavy work. |

## 10-step pipeline

| # | Phase | Notes |
|---|---|---|
| 1 | Verify source tree | desktop_app.py, server.py, RKOJ.spec, requirements.txt — all four must exist. |
| 2 | Resolve Python | `.venv/Scripts/python.exe` -> `py -3.12` -> `python` (first hit wins). |
| 3 | Warm-path probe | `import fastapi, uvicorn, webview, qrcode, PyInstaller, PyInstaller.hooks.pre_safe_import_module` AND `hook-tomli.py` on disk. Both pass = WARM, skip 4-6. |
| 4 | Ensure .venv | `python -m venv` only if missing. **Never** `pip install --upgrade pip` (see gotcha 1 below). |
| 5 | Install requirements | `pip install --disable-pip-version-check -r requirements.txt`. Also installs PyInstaller if absent. |
| 6 | Force-reinstall hooks-contrib | `pip install --force-reinstall --no-deps pyinstaller-hooks-contrib` (see gotcha 2). |
| 7 | PyInstaller | `python -m PyInstaller --noconfirm --clean RKOJ.spec`. Output tee'd to `_build-logs/build-<UTC-stamp>.log`. |
| 8 | Verify exe | `dist/RKOJ/RKOJ.exe` exists AND size > 5 MB AND mtime within 5 min. |
| 9 | Mirror to Desktop | `robocopy /MIR /R:1 /W:1` (see gotcha 3). |
| 10 | Runlog + PROGRESS + heartbeat | One python one-liner writes a `sinister-runlog/v1` JSON manifest, appends to `_shared-memory/PROGRESS/Sinister Sanctum.md`, touches `_shared-memory/heartbeats/sanctum-console-build.beat`. |

## Three baked-in gotchas (DO NOT remove)

### 1. Never `pip install --upgrade pip` in a fresh venv

The script explicitly skips this step. Self-upgrading pip on Python 3.12 in a fresh venv can corrupt `pip._vendor` (urllib3 / requests version mismatch). After that, every subsequent pip call fails with `ImportError: cannot import name 'urllib3' from 'pip._vendor'`. Knowledge entry: `D:\Sinister Sanctum\_shared-memory\knowledge\pip-self-upgrade-breaks-venv.md`.

### 2. Always force-reinstall `pyinstaller-hooks-contrib` on cold

PyInstaller 6.20 on Python 3.12 occasionally lands with a half-populated `PyInstaller/hooks/pre_safe_import_module/` directory — `hook-tomli.py` missing. The first `pyinstaller` invocation then dies with `FileNotFoundError: ... hook-tomli.py`. Force-reinstalling `pyinstaller-hooks-contrib --no-deps` fills in the missing files. Knowledge entry: `D:\Sinister Sanctum\_shared-memory\knowledge\pyinstaller-tomli-hook-missing.md`.

### 3. Robocopy `/MIR` (not `cp -ru`) for the Desktop sync

Onedir PyInstaller builds drop `_internal\python312.dll` next to the EXE. If the deploy copy is partial (locked DLL during copy, AV quarantine, mid-write interruption), the EXE bootloader cannot find its interpreter and pops a Windows MessageBox before any logging is possible. `robocopy /MIR` retries on locked files (`/R:1 /W:1`) and mirrors deletions; `cp -ru` does neither. Knowledge entry: `D:\Sinister Sanctum\_shared-memory\knowledge\exe-dll-crash-incomplete-copy.md`.

## Manual fallback commands

If the script fails at a specific step, you can run that step by hand to diagnose:

```bash
# from D:/Sinister Sanctum/automations/window-manager
cd "/d/Sinister Sanctum/automations/window-manager"

# step 4 (recreate venv from scratch)
rm -rf .venv
py -3.12 -m venv .venv

# step 5 (install requirements)
.venv/Scripts/python.exe -m pip install --disable-pip-version-check -r requirements.txt
.venv/Scripts/python.exe -m pip install --disable-pip-version-check pyinstaller

# step 6 (force-reinstall hooks)
.venv/Scripts/python.exe -m pip install --force-reinstall --no-deps pyinstaller-hooks-contrib

# step 7 (build)
.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean RKOJ.spec

# step 9 (mirror to Desktop)
robocopy "D:\Sinister Sanctum\automations\window-manager\dist\RKOJ" \
         "C:\Users\Zonia\Desktop\RKOJ" /MIR /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP
```

## Where the artifacts land

| Path | What |
|---|---|
| `dist/RKOJ/` | PyInstaller output (canonical) |
| `C:\Users\Zonia\Desktop\RKOJ\` | Robocopy mirror — what `RKOJ.bat` and old `Sanctum-Console.lnk` point at |
| `_build-logs/build-<UTC-stamp>.log` | PyInstaller stdout/stderr per run |
| `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs\build-rkoj-<UTC-stamp>.json` | `sinister-runlog/v1` manifest |
| `D:\Sinister Sanctum\_shared-memory\PROGRESS\Sinister Sanctum.md` | Append-only log entry |
| `D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj-build.beat` | Touched on each successful build |

## See also

- `AUTOSTART.md` — install the scheduled task that keeps the console always-on.
- `D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md` — full knowledge index.
