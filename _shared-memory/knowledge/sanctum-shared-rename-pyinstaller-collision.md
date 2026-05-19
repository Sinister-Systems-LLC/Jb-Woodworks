> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: `_shared/` package name collides with PyInstaller bundling — rename to `sanctum_shared/`

**Slug:** sanctum-shared-rename-pyinstaller-collision
**First discovered:** 2026-05-19 11:17 by Sinister Sanctum master (HR-B audit)
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master (agent A wave 1)
**Status:** fixed
**Tags:** pyinstaller, _shared, sanctum_shared, bundling, collect_submodules, collect_data_files, rkoj, exe, spec, underscore-prefix

## Problem

RKOJ's PyInstaller spec declared `('_shared', '_shared')` in `datas` — meant to copy the local `automations/window-manager/_shared/` directory into the frozen bundle as `_internal/_shared/`. The bundle as built was missing that directory, so the runtime EXE's `from _shared import cycle_points` and `from _shared import scheduler` would fail. Cycle-points + scheduler features were silently broken in the EXE while working in source mode.

## Why it happens

Two independent factors:

1. **Hybrid package merging in source mode.** The local `_shared/__init__.py` extended `__path__` to include the HUB `_shared/` directory at `D:/Sinister/Sinister Skills/12_LLM_ORCHESTRATION/agents/_shared/` so `from _shared import inbox / runlog / codec` resolved through the hub. The local package was acting as both a real package (cycle_points / scheduler) AND a path-bridge to the hub. PyInstaller's static analyzer can introspect the imports but doesn't follow runtime `__path__.append()`, so its hidden-import map for `_shared` was incomplete / inconsistent.

2. **Underscore-prefix naming.** PyInstaller uses `_pyi_*` and other underscore-prefixed namespaces internally. A user package starting with `_` doesn't directly collide with `_pyi_` but DOES interact badly with PyInstaller's data-vs-module heuristics in some hook versions. The `('_shared', '_shared')` data-tuple form is non-recursive (it copies top-level files) and skips `.py` files when there's a competing module-import path. Net result: `_shared/` got partially or completely omitted.

The PROGRESS log at `_shared-memory/PROGRESS/Sinister Sanctum.md` (2026-05-19 11:17 audit, "Critical failures" section) flagged this as bug #1.

## Fix or workaround

Three-part fix shipped in Wave 1 agent A (2026-05-19 13:30):

1. **Rename the LOCAL package** `automations/window-manager/_shared/` → `automations/window-manager/sanctum_shared/`. The name no longer collides with PyInstaller's underscore-prefix heuristics OR with the hub `_shared` package.

2. **Drop the `__path__` hack** in `sanctum_shared/__init__.py`. The local package is now a clean Python package with just `cycle_points.py` + `scheduler.py`. Update `server.py` imports:
   - `from _shared import cycle_points` → `from sanctum_shared import cycle_points`
   - `from _shared import scheduler` → `from sanctum_shared import scheduler`
   - Keep `from _shared import inbox / runlog / codec` UNCHANGED — these resolve via the hub. The existing `sys.path.insert` at server.py:78-79 was already in place to make the hub `_shared/` importable as the bare name `_shared`. No new path injection needed.

3. **Update the spec** (renamed to `RKOJ.spec`) to use proper module collection:
   ```python
   from PyInstaller.utils.hooks import collect_submodules, collect_data_files
   hiddenimports += collect_submodules('sanctum_shared')
   datas += collect_data_files('sanctum_shared', include_py_files=True)
   ```
   These hooks walk the package via Python's import machinery — guaranteed to find every submodule + every .py file. The old non-recursive `('_shared', '_shared')` data-tuple is gone.

```bash
# Smoke verify (tested OK):
cd "D:/Sinister Sanctum/automations/window-manager"
./.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, '.'); from sanctum_shared import cycle_points, scheduler; from _shared import inbox, runlog; print('OK')"
# -> OK
```

The build script (`build-sanctum-console.sh`) + `BUILD.md` + `docs/WORKBENCH.md` + `docs/RKOJ-OPERATOR-GUIDE.md` all reference `RKOJ.spec` now (the prior `Sanctum-Console.spec` was renamed but left a confusing artifact for anyone grepping for the spec name).

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master (agent A wave 1)
Shipped the rename. `python -c "from sanctum_shared import cycle_points, scheduler; from _shared import inbox, runlog"` returns OK in source mode. EXE rebuild + bundle verification pending (task G — running now). The original spec `('_shared', '_shared')` line is REMOVED entirely; spec datas no longer references the old name. If a future PyInstaller version changes its underscore-prefix handling, the rename approach still stands — it's not just a workaround for the current PyInstaller, it's a hygiene fix.

### 2026-05-19 11:17 by Sinister Sanctum master (HR-B audit)
Audit found `dist/RKOJ/_internal/_shared/` MISSING from the bundle despite the spec declaring `('_shared', '_shared')`. Same problem in `C:/Users/Zonia/Desktop/RKOJ/_internal/`. Hypothesized the underscore-prefix conflict. Recommended rename to `sanctum_shared/`. Tracked in PROGRESS log "Critical failures" section.

## Related topics

- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md)
- [exe-silent-crash-no-popup](./exe-silent-crash-no-popup.md)
- [exe-dll-crash-incomplete-copy](./exe-dll-crash-incomplete-copy.md)
- [pyinstaller-tomli-hook-missing](./pyinstaller-tomli-hook-missing.md)
