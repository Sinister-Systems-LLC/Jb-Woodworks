<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: PyInstaller 6.20 fresh install misses hook-tomli.py

**Slug:** pyinstaller-tomli-hook-missing
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** workaround
**Tags:** pyinstaller, build, hooks-contrib, python-3-12

## Problem

Fresh `pip install pyinstaller` (6.20.0) in a Python 3.12 venv, then running `pyinstaller app.py` fails immediately:

```
FileNotFoundError: [Errno 2] No such file or directory:
'...\\.venv\\Lib\\site-packages\\PyInstaller\\hooks\\pre_safe_import_module\\hook-tomli.py'
```

PyInstaller's own hooks directory is missing the `hook-tomli.py` file (and possibly others). The build aborts before producing any output.

## Why it happens

PyInstaller's hooks were split into a separate package `pyinstaller-hooks-contrib`. The main `pyinstaller` wheel declares it as a dep, but on Python 3.12 the install may complete with the dep file structure half-populated (some hook files copied, others not). Likely a race condition or a setup.py bug interacting with pip's resolver.

The missing hook files are in `pyinstaller-hooks-contrib` (the contrib package), not `pyinstaller` itself.

## Fix or workaround

Force-reinstall `pyinstaller-hooks-contrib`:

```bash
.venv/Scripts/python.exe -m pip install --force-reinstall --no-deps pyinstaller-hooks-contrib
```

After this, the missing hook file appears at:
```
.venv/Lib/site-packages/PyInstaller/hooks/pre_safe_import_module/hook-tomli.py
```

(Yes — `pyinstaller-hooks-contrib` writes into `PyInstaller/hooks/`, not its own namespace. This is by PyInstaller's design.)

Then retry `pyinstaller app.py` — the build proceeds.

## Sanctum-specific note

Hit while building `Sanctum-Console.exe` from `desktop_app.py` for the operator. The fix worked first try. Worth scripting into the Sanctum-Console build automation: always run `pip install --force-reinstall --no-deps pyinstaller-hooks-contrib` after a fresh PyInstaller install.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 03:20 by Sinister Sanctum
Reproduced cleanly. Force-reinstall of hooks-contrib added the missing hook + 100+ others. Build succeeded after.

## Related topics

- [pip-self-upgrade-breaks-venv](./pip-self-upgrade-breaks-venv.md)
