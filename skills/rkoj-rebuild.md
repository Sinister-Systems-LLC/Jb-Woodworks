---
name: rkoj-rebuild
description: Build RKOJ.exe via pyinstaller
allowed-tools: [bash]
---
# Active Skill: rkoj-rebuild

Quick one-shot rebuild of `RKOJ.exe`. This is the minimal-ceremony variant
of `/forge-build` — run it when you just need a fresh EXE on the Desktop
without the full walkthrough. For the diagnostic-heavy version see
`/forge-build`.

## Steps

1. **Move to the build dir**:
   ```bash
   cd "D:/Sinister Sanctum/automations/build/forge-exe/"
   ```

2. **Run PyInstaller** (clean + noconfirm so it never prompts):
   ```bash
   pyinstaller --clean --noconfirm RKOJ.spec
   ```

3. **Copy the fresh EXE to the Desktop**:
   ```bash
   cp dist/RKOJ.exe "C:/Users/Zonia/Desktop/RKOJ.exe"
   ```

4. **Smoke-test the new binary**:
   ```bash
   "C:/Users/Zonia/Desktop/RKOJ.exe" --version
   ```

5. **Report** the printed version string + build timestamp back to the
   operator. Done.

## Output format

Three lines, no decoration:

```
build: <ok|FAILED>
version: <output of --version>
deployed: C:/Users/Zonia/Desktop/RKOJ.exe (<size> bytes)
```

## Hard rules

- Never run from inside the running EXE — it locks its own binaries.
  Always invoke from a separate shell.
- If `pyinstaller` exits non-zero, STOP. Do not copy a broken EXE to the
  Desktop. Surface the last 20 lines of stderr to the operator.
- The full diagnostic build flow (hidden-imports debugging, hook
  collisions, PROGRESS update) lives in `/forge-build`. Switch to that
  if this minimal flow fails.
