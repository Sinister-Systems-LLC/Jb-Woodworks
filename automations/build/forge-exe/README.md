# RKOJ.exe build pipeline

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Output:** `C:\Users\Zonia\Desktop\RKOJ.exe` (29 MB onefile PyInstaller build)

The Sinister Sanctum click-to-launch executable. Replaces the old `Sinister Forge.bat` + `Start-Sinister-Session.bat` two-step flow with one EXE that:

1. Renders the animated SINISTER ASCII boot art (purple shimmer, 4 frames @ ~100ms).
2. Greets as **EVE** and asks: pick a past project / create a new one / something else.
3. Project picker — 14 lanes from `automations/session-templates/projects.json`.
4. Mode picker — resume / expand / coaudit / smoke / security / shell.
5. Tool questions — swarm? memory? login-status? graph?
6. Delegates the actual launch to `automations/start-sinister-session.ps1` with the picked params, preserving every existing launcher feature (heartbeat write, agent-prefs persistence, focus-intent injection).

Also acts as the **sinister-CLI umbrella**: `RKOJ.exe login providers`, `RKOJ.exe usage check-all`, `RKOJ.exe swarm list`, `RKOJ.exe memory recall ...`, etc. — same dispatch as the `sinister` binary.

## Rebuild

```bash
cd "D:/Sinister Sanctum/automations/build/forge-exe"
pyinstaller --clean --noconfirm RKOJ.spec
cp dist/RKOJ.exe "C:/Users/Zonia/Desktop/RKOJ.exe"
```

Build time: ~45 sec on the operator's box. Output: `dist/RKOJ.exe` (~29 MB).

## Pre-build setup (do once per fresh Python env)

```bash
pip install pyinstaller
pip install --force-reinstall --no-deps pyinstaller-hooks-contrib   # brain doctrine: pyinstaller-tomli-hook-missing
pip install jaraco.text jaraco.functools jaraco.context              # pkg_resources runtime hook needs these
pip install -e "D:/Sinister Sanctum/tools/sinister-cli"              # umbrella
pip install -e "D:/Sinister Sanctum/tools/sinister-login"
pip install -e "D:/Sinister Sanctum/tools/sinister-usage"
pip install -e "D:/Sinister Sanctum/tools/sinister-swarm"
pip install -e "D:/Sinister Sanctum/tools/forge-memory-bridge"
pip install -e "D:/Sinister Sanctum/tools/memory-graph-render"
pip install -e "D:/Sinister Sanctum/projects/sinister-forge/source"
```

## Files

| File | What it is |
|---|---|
| `RKOJ-entry.py` | The Python entry script PyInstaller bundles. Boot art, picker, EVE persona, launcher delegate. |
| `RKOJ.spec` | PyInstaller spec — hiddenimports, datas, excludes, console=True, icon. |
| `.gitignore` | Excludes `build/`, `dist/`, `*.log` — those are ephemeral artifacts. |

## Brain doctrine honored

- `pyinstaller-distutils-exclude-collision` — `distutils` NOT in excludes
- `exe-silent-crash-no-popup` — runtime crash-log hook in entry script
- `sanctum-shared-rename-pyinstaller-collision` — `collect_submodules` + `collect_data_files` for every package
- `pyinstaller-tomli-hook-missing` — pre-build force-reinstall of hooks-contrib
- `sinister-cli-subcommand-pattern` — every shipped sinister-X tool is bundled as a hidden import

## What to test after rebuild

1. `RKOJ.exe version` → enumerates 6 sinister tools + sinister-cli umbrella version.
2. `RKOJ.exe login providers` → 11-row provider wallet table.
3. `RKOJ.exe usage list` → 11-row endpoint registry.
4. `RKOJ.exe` (no args) → animated boot → EVE greeting → picker flow → delegate to `start-sinister-session.ps1`.
5. Check `RKOJ.crash.log` next to the EXE if anything fails silently (sidecar log per `exe-silent-crash-no-popup` doctrine).
