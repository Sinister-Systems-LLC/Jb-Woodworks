> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: PyInstaller hook-distutils.py fails when `distutils` is in spec excludes — also: missing `select`/`_socket` causes EXE bootloader to crash with "Failed to load Python DLL"

**Slug:** pyinstaller-distutils-exclude-collision
**First discovered:** 2026-05-19 14:00 by Sinister Sanctum master (RKOJ rebuild close-out)
**Last updated:** 2026-05-19 14:05 by Sinister Sanctum master
**Status:** fixed
**Tags:** pyinstaller, distutils, exclude, hook-distutils, alias_module, select, _socket, multiprocessing, asyncio, hiddenimports, exe, dll-load-failed, bootloader, runtime-hook

## Problem — two distinct PyInstaller build/runtime failures

### Failure 1 — Build-time `ValueError: Target module "distutils" already imported as "ExcludedModule"`

`automations/window-manager/RKOJ.spec` had `distutils` in its `excludes` list (carried over from the original Sanctum-Console.spec). On a clean `PyInstaller --noconfirm --clean RKOJ.spec` run, PyInstaller would explode with:

```
File ".../PyInstaller/hooks/pre_safe_import_module/hook-distutils.py", line 23, in pre_safe_import_module
    api.add_alias_module(real_vendored_name, aliased_name)
  ...
ValueError: Target module "distutils" already imported as "ExcludedModule('distutils',)".
```

Confusing because earlier builds with the same spec SUCCEEDED. The difference: `--clean` forces a fresh cache, which is when the pre_safe_import_module hook actually runs against the real exclude list.

### Failure 2 — Runtime "Failed to load Python DLL python312.dll" / `ModuleNotFoundError: No module named 'select'`

After fixing Failure 1, the rebuilt RKOJ.exe ran on the operator's Desktop and immediately crashed with a Windows MessageBox:

> Failed to load Python DLL 'D:\Sinister Sanctum\automations\window-manager\dist\RKOJ\_internal\python312.dll'.
> LoadLibrary: The specified module could not be found.

`python312.dll` IS in the bundle, fully intact (6.9MB). The error message is misleading — the actual root cause is a Python `ModuleNotFoundError` raised inside `pyi_rth_multiprocessing.py` (PyInstaller's multiprocessing runtime hook) when `selectors.py` line 12 tries `import select`. PyInstaller's autodetect missed the `select` stdlib chain on this build (the imports are buried inside asyncio's internal selector dispatch, not directly referenced by `server.py`). The Windows bootloader catches the Python-level exception and shows the generic DLL-not-found popup.

## Why it happens

### Failure 1 root cause

PyInstaller's `hook-distutils.py` (in newer 6.x versions) calls `add_alias_module(real_vendored_name, "distutils")` during the pre_safe_import_module phase. This is needed because Python 3.12 vendored `distutils` differently. But `add_alias_module` strictly refuses to alias to a name that was already registered as `ExcludedModule` — and excludes are processed BEFORE the alias hook runs. Net effect: `distutils` is in excludes → registered as `ExcludedModule` → hook tries to alias it → ValueError → build dies.

Confirmed with PyInstaller 6.20.0. Older 6.x may not have the strict alias check.

### Failure 2 root cause

`pyi_rth_multiprocessing.py` is a runtime hook that PyInstaller automatically includes whenever `multiprocessing` is on the import graph (and `multiprocessing` is on RKOJ's graph because uvicorn imports it transitively). On import, this hook runs `import selectors`, which imports `select`. The `select` stdlib module is a C-extension (`select.pyd`) and PyInstaller's analyzer only follows EXPLICIT imports — it doesn't introspect through asyncio's selector_events.py or selectors.py transitive chain reliably. So `select.pyd` got omitted from `_internal/`.

Same story for `_socket.pyd`, `multiprocessing.context`, `multiprocessing.reduction`, `asyncio.windows_events`, etc.

## Fix or workaround

Two-part fix shipped in `RKOJ.spec` 2026-05-19 14:00-14:05:

### Part 1 — distutils exclude removal

Comment out `'distutils'` from the `excludes=[...]` list. Annotate with the brain-entry slug:

```python
excludes=[
    ...
    'setuptools',     # no runtime install
    'pip',            # no runtime install
    # 'distutils' INTENTIONALLY NOT EXCLUDED here -- PyInstaller's own
    # hook-distutils.py aliases distutils to a vendored name during the
    # pre_safe_import_module phase. If we exclude distutils first, that
    # alias fails with "Target module 'distutils' already imported as
    # 'ExcludedModule'". Brain entry: pyinstaller-distutils-exclude-collision.md.
    # The actual cost of including distutils is tiny (~50KB), not worth
    # the build failure. Reproduced 2026-05-19 with PyInstaller 6.20.0.
    'pydoc',          # no in-EXE doc browser
    ...
]
```

### Part 2 — explicit hiddenimports for the stdlib network/select/asyncio chain

Add to the `hiddenimports` list:

```python
hiddenimports = [
    'uvicorn.logging',
    ...
    'multiprocessing',
    # 2026-05-19 master sweep: bootloader crash repro showed
    # `ModuleNotFoundError: No module named 'select'` during
    # pyi_rth_multiprocessing -> selectors.py:12. PyInstaller's autodetect
    # missed it on this build; declare the stdlib network/select chain
    # explicitly so it ships in _internal/.
    'select',
    '_socket',
    'socket',
    'selectors',
    'multiprocessing.context',
    'multiprocessing.reduction',
    'multiprocessing.popen_spawn_win32',
    'multiprocessing.queues',
    'multiprocessing.synchronize',
    'multiprocessing.connection',
    'multiprocessing.shared_memory',
    'multiprocessing.heap',
    'asyncio',
    'asyncio.selector_events',
    'asyncio.windows_events',
    'asyncio.proactor_events',
]
```

After both fixes, the rebuilt EXE smoke-test passes:

```bash
"D:/Sinister Sanctum/automations/window-manager/dist/RKOJ/RKOJ.exe" --port 5099 --no-window
# -> [OK] Sinister Sanctum found at: D:\Sinister Sanctum
# -> [OK] Sanctum console up at http://127.0.0.1:5099/

curl http://127.0.0.1:5099/api/health
# -> {"ok":true,"version":"8aj.1","port":5099,"shared_ok":true,"auth_available":true,...}
```

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 14:05 by Sinister Sanctum master
Verified BOTH failures resolved with the patched spec. Build now takes ~2:15 (vs the old ~5min). `python312.dll`, `select.pyd`, `_socket.pyd`, `sanctum_shared/`, `base_library.zip` all present in `_internal/`. Source-mode python NEVER reproduces this — only the frozen EXE — so the bug is exclusively a PyInstaller analysis-pass-vs-runtime-hook gap. The operator can no longer ignore this if they see "Failed to load Python DLL" in the future — the diagnostic flow is: (1) check `_internal/python312.dll` exists, (2) if yes, the error is masking a Python ModuleNotFoundError in a runtime hook — likely missing stdlib import, add to hiddenimports.

### 2026-05-19 14:00 by Sinister Sanctum master (rebuild close-out)
Hit Failure 1 first (distutils ValueError) — fixed by commenting out the exclude. Then hit Failure 2 (DLL load popup) — diagnosed via PyInstaller xref + warning logs in `build/RKOJ/warn-RKOJ.txt`; reproduced by reading `warn-RKOJ.txt` showed "hidden import 'select' not found". Fixed via explicit hiddenimports list.

## Related topics

- [exe-silent-crash-no-popup](./exe-silent-crash-no-popup.md) — different EXE crash class (sys.__stderr__ None in windowed builds)
- [exe-dll-crash-incomplete-copy](./exe-dll-crash-incomplete-copy.md) — incomplete robocopy leaves DLL chain broken
- [sanctum-shared-rename-pyinstaller-collision](./sanctum-shared-rename-pyinstaller-collision.md) — the bundle-gap bug fixed in the same rebuild
- [pyinstaller-tomli-hook-missing](./pyinstaller-tomli-hook-missing.md) — PyInstaller 6.20 hooks-contrib quirk
