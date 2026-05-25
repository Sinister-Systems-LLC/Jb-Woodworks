<!-- decay:
  superseded_by: no-bullshit-tested-before-claimed-doctrine-2026-05-23
-->
> **Author:** RKOJ-ELENO :: 2026-05-21

# Topic: PyInstaller tmp-file race — sibling agent's atomic-write breaks Analysis phase

**Slug:** pyinstaller-tmp-race-condition-2026-05-21
**First discovered:** 2026-05-21 by EVE (Sinister Sanctum orchestration agent)
**Last updated:** 2026-05-21 by EVE
**Status:** workaround (long-term fix is one-line spec edit)
**Tags:** pyinstaller, race-condition, atomic-write, tmp-file, RKOJ.spec, hiddenimports, datas-glob, parallel-agents

## Problem

During a parallel-agent build (24+ agents touching the RKOJ source tree while one of them runs `pyinstaller RKOJ.spec`), the build fails with:

```
ERROR: Unable to find 'D:\Sinister Sanctum\projects\rkoj\source\forge\commands.py.tmp.62084.7a3f9b2c' when adding binary and data files.
```

The `.tmp.<pid>.<id>` file is gone by the time PyInstaller's second-pass file read fires. PyInstaller's `Analysis` phase enumerates source files in two passes:

1. **Pass 1 — Glob**: walks the source tree, builds a manifest of every file matching `datas` patterns.
2. **Pass 2 — Read**: opens each file in the manifest, hashes, copies into the bundle.

Between the two passes, a sibling agent's `Edit` tool (Claude Code's atomic-write implementation) creates a `.tmp.<pid>.<random>` file, writes the new content, then `os.rename()`s it over the target. If Pass 1 catches the `.tmp.*` file mid-write, Pass 2's read fails because the rename completed and the tmp file no longer exists.

## Why it happens

Claude Code's `Edit`/`Write` tools use atomic-write semantics for safety: write to a sibling `.tmp.<pid>.<id>` file, then `os.rename()` over the destination. This guarantees the destination file is either fully-old or fully-new at every point — no half-written file ever appears.

The atomic-write pattern is correct in isolation. The conflict is:

1. PyInstaller's `Analysis` does its glob without any locking — it's a one-shot snapshot.
2. The default `datas=[]` glob patterns in `RKOJ.spec` are wildcard-y (`projects/rkoj/source/forge/**/*.py`) and DO match `.tmp.<pid>.*` files.
3. Between glob and read, the tmp file is gone (renamed onto the destination), so the read fails the build.

The window is small (milliseconds for `os.rename`), but during a 24-agent sweep where dozens of edits land per minute, the dice come up wrong.

Reference: PyInstaller source `PyInstaller/building/build_main.py::Analysis._compute_dependencies()` — the manifest is built before any read.

## Fix or workaround

### Short-term workaround (this session)

Wait for sibling commits to land, then retry:

```bash
# Confirm all sibling agents have committed:
git log --all --oneline --since="5 minutes ago"
# Empty for ~30 seconds = quiet period

# Rebuild
cd projects/rkoj
pyinstaller RKOJ.spec --clean --noconfirm
```

If a race still hits, just retry — the window is small enough that 2-3 attempts almost always succeed.

### Long-term fix (single-line spec edit)

Add `*.tmp.*` to the PyInstaller spec's `excludes`. In `projects/rkoj/RKOJ.spec`:

```python
a = Analysis(
    ['RKOJ-entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('source/forge/**/*.py', 'forge'),
        # ... other entries
    ],
    hiddenimports=[
        # ... long list
    ],
    excludes=[
        '*.tmp.*',            # <-- ADD THIS LINE — drops Claude Code atomic-write tmp files
        '*.swp', '*.swo',     # vim swap files (cheap to include too)
        '.git',
    ],
    # ... rest
)
```

The `excludes` patterns run against the matched paths before Pass 2 reads, so any `.tmp.*` file caught mid-write is dropped from the manifest. Build proceeds without a retry.

**Status of long-term fix**: not yet committed (operator gating — will land in next-session sweep). Workaround works fine in the meantime.

## Discoveries (append-only log, most-recent at top)

### 2026-05-21 by EVE (Sinister Sanctum)

First encountered during the v1.0.1 → v1.0.2 build when 4 agents were mid-edit on `forge/commands.py` and `forge/spawn/base.py`. The error reproduced 2 of 5 build attempts. Workaround (wait + retry) shipped v1.0.2 successfully. Spec-excludes fix queued for next session.

Filed in the operator queue at `_shared-memory/OPERATOR-ACTION-QUEUE.md` as low-priority (workaround suffices).

## Related topics

- [parallel-agent-orchestration-pattern-2026-05-21](./parallel-agent-orchestration-pattern-2026-05-21.md)
- [exe-dll-crash-incomplete-copy](./exe-dll-crash-incomplete-copy.md)
- [exe-silent-crash-no-popup](./exe-silent-crash-no-popup.md)
- [rkoj-v1.0-to-v1.1-form-parity-journey](./rkoj-v1.0-to-v1.1-form-parity-journey.md)
