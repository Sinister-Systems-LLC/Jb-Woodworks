---
name: forge-build
description: Walk through the RKOJ.exe rebuild flow (PyInstaller onefile, copy to Desktop, smoke-test)
allowed-tools: [bash]
---
# Active Skill: forge-build

Walk the operator through rebuilding `RKOJ.exe` from
`D:/Sinister Sanctum/automations/build/forge-exe/` and deploying it to the
Desktop. Use only the `bash` tool.

## Pre-flight checks

1. Confirm `pyinstaller` is on PATH:
   ```bash
   pyinstaller --version
   ```
2. Confirm the entry script + spec exist:
   ```bash
   ls -la "D:/Sinister Sanctum/automations/build/forge-exe/RKOJ-entry.py"
   ls -la "D:/Sinister Sanctum/automations/build/forge-exe/RKOJ.spec"
   ```
3. Verify forge is editable-installed (so collect_submodules picks it up):
   ```bash
   python -c "import forge, forge.skills, forge.commands; print(forge.__version__)"
   ```

## Rebuild

```bash
cd "D:/Sinister Sanctum/automations/build/forge-exe/"
pyinstaller --clean --noconfirm RKOJ.spec 2>&1 | tee build.log
```

Watch for:
- `ModuleNotFoundError` during analysis — add the missing module to
  `hiddenimports` in `RKOJ.spec`.
- `WARNING: collected ... but the hook returned no datas` — usually safe.
- `WARNING: file already exists but should not` — collision. Check the
  `sanctum-shared-rename-pyinstaller-collision` brain entry.

## Smoke test

```bash
./dist/RKOJ.exe --version
./dist/RKOJ.exe --help | head -40
```

Then run the project's PowerShell smoke harness:
```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File \
    "D:/Sinister Sanctum/automations/build/forge-exe/smoke-test-rkoj.ps1"
```

## Deploy

After all checks pass:
```bash
cp "D:/Sinister Sanctum/automations/build/forge-exe/dist/RKOJ.exe" \
   "C:/Users/Zonia/Desktop/RKOJ.exe"
```

Then ask the operator to launch the Desktop shortcut and confirm a
`/version` ping shows the new build timestamp.

## Hard rules

- Never run `pyinstaller` from within the running EXE — it locks its own
  binaries. Always run from a separate shell.
- If the build fails, never push the broken EXE. Roll back to the previous
  Desktop copy (the operator keeps a backup at `Desktop/RKOJ.exe.bak`).
- Update `_shared-memory/PROGRESS/Sinister Sanctum.md` with the build
  timestamp + headline change AFTER the smoke test passes.
