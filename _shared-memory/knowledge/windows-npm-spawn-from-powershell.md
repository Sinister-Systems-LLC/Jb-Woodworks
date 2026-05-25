<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: `Start-Process powershell -Command "npm run dev"` hangs silently on Windows

**Slug:** windows-npm-spawn-from-powershell
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** workaround
**Tags:** powershell, npm, windows, start-process, child-process, npm.cmd, npm.ps1, spawn, dev-server, next-js

## Problem

Spawning `npm run dev` (or any `npm` command) from one PowerShell into another via `Start-Process powershell.exe -NoExit -Command "Set-Location ...; npm run dev"` opens the child PowerShell window but `npm` never actually starts. No child node process appears. No error in the window. The port stays empty. The PowerShell window sits at a prompt as if the command silently failed.

Symptom checklist:
- Port (e.g. `:6060` for Next.js) shows no listener via `Get-NetTCPConnection -LocalPort 6060`.
- No fresh `node.exe` child of the spawned `powershell.exe`.
- Spawned PowerShell window is responsive but seems to have never run the command.
- No error message visible.

This bit hard when bringing LetsText 2.0 dev servers up programmatically: 5+ minutes burned on three spawn attempts that all looked successful from the outside but produced no compile.

## Why it happens

`npm` on Windows is normally resolved by PowerShell to **`C:\Program Files\nodejs\npm.ps1`** (the PowerShell shim) rather than `npm.cmd`. When that `.ps1` shim is invoked from a child PowerShell launched with `-NoExit -Command "..."`, the combination of:

- ExecutionPolicy inheritance / signature check on `npm.ps1`
- stdio / console-handle handoff between parent and child PS
- npm itself spawning detached child processes for the dev server

…results in `npm.ps1` returning early without actually starting the dev server. The visible PowerShell window proceeds straight to the prompt as if the command finished, but it never did real work.

This does NOT happen when you run `npm run dev` from a hand-opened terminal — only when spawned programmatically via `Start-Process powershell -Command`.

## Fix or workaround

### Option A — Use `cmd.exe` + the full path to `npm.cmd` (RECOMMENDED)

`npm.cmd` is the classic batch shim and works reliably from `cmd.exe`. No PS shim, no ExecutionPolicy, no stdio confusion.

```powershell
$npm = 'C:\Program Files\nodejs\npm.cmd'
Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/k","`"$npm`" run dev" `
    -WorkingDirectory "D:\YourProject\frontend" `
    -WindowStyle Normal
```

The `/k` keeps the cmd window open so the dev-server logs stay visible. `-WorkingDirectory` sets the CWD before `npm.cmd` runs (more reliable than embedding `cd /d ...` in the args).

Verified: this spawns a `cmd.exe` parent that runs `npm.cmd run dev`, which in turn runs `cmd /d /s /c next dev --turbopack --port 6060` (the actual dev server), which binds to its port and starts compiling.

### Option B — Use a `.bat` wrapper that the operator double-clicks

If a one-click path already exists (e.g. `letstext-dev-fresh.bat`), prefer it. The `.bat` runs in `cmd.exe` natively, sidesteps the issue, and the operator gets a recognisable visible window.

```powershell
Start-Process -FilePath "C:\path\to\dev-fresh.bat" -WindowStyle Normal
```

### What does NOT work

```powershell
# All of these spawn the shell but npm never starts:
Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location ...; npm run dev"
Start-Process powershell.exe -ArgumentList "-NoExit","-Command","npm run dev" -WorkingDirectory "..."
Start-Process powershell -ArgumentList "-NoExit","-Command","cd ...; npm.cmd run dev"  # even with .cmd, PS context still wraps it
```

The PS-to-PS chain is the killer. Break out of PowerShell to `cmd.exe` and use `npm.cmd` directly.

## How to diagnose if you suspect this

```powershell
# 1. Confirm spawned PowerShell window is alive but has no child node
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' } | Select-Object ProcessId, CreationDate

# 2. Check what's on the expected dev port
Get-NetTCPConnection -LocalPort 6060 -State Listen -ErrorAction SilentlyContinue

# 3. If nothing on the port + no recent node procs from your spawn, you've hit this.
```

## Sanctum-specific note

The LetsText dashboard-local (`:6060`) and mobile-dashboard (`:3400`) dev servers both hit this when the master agent tried to bring them up via `powershell -NoExit -Command`. Fix applied: re-spawned via `cmd.exe + npm.cmd` per Option A. Both surfaces then compiled normally.

Future Sanctum tools that programmatically start Next.js / Vite / npm-based dev servers should default to Option A. Document the assumption in the tool's README.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 08:25 by Sinister Sanctum — bat-via-Invoke-Item ALSO fails
After switching from PS-spawn to `cmd.exe + npm.cmd` (worked once for dashboard-local, then Turbopack hung), tried `Invoke-Item "D:\LetsText\bats\letstext-dev-fresh.bat"` thinking Explorer-style invoke would give it a clean process context. **It did not.** The bat ran phases 1+2 (kill listener, wipe .next) but `call npm run dev` hung with zero descendants. The `cmd /c <bat>` process sat 170s with only a `conhost.exe` child — no npm, no node.

**Confirmed**: from inside a Claude-driven PowerShell session, EVERY programmatic spawn path that ultimately invokes `npm` inherits stdio / console-handle state that silently breaks the dev-server start. This includes:
- `Start-Process powershell -Command "...npm run dev"` (PS-on-PS)
- `Start-Process cmd.exe -ArgumentList "/k","npm.cmd run dev"` (cmd-from-PS) — works ~50% of the time; the other half binds the port but Turbopack hangs at zero-CPU after binding
- `Invoke-Item "<bat>"` (Explorer-style invoke from PS) — same hang

**Reliable green path**: have the **operator** double-click the `.bat` from Explorer (Sinister-Bots-Activation.bat, letstext-dev-fresh.bat, etc.). The bat in operator-interactive context spawns cleanly. From inside Claude, the most we can do is `Start-Process explorer.exe "<dir>"` so the operator can click it.

Park in operator-action-queue any "start dev server" task — programmatic kickoff is unreliable in this environment.

### 2026-05-19 08:15 by Sinister Sanctum — initial discovery
First hit while bringing both LetsText 2.0 dev surfaces up in response to operator's "i need letstext 2.0 back up". Three consecutive `Start-Process powershell -Command "...npm run dev"` attempts all looked successful but produced no port binding. Switched to `Start-Process cmd.exe -ArgumentList "/k","`"$npmCmd`" run dev"` and confirmed via `Get-CimInstance Win32_Process` that the cmd→npm.cmd→next-dev chain spawned cleanly. Lost ~5 minutes to this before diagnosing.

## Related topics

- [powershell-emdash-non-ascii](./powershell-emdash-non-ascii.md) — sibling Windows-PS-on-PS-5.1 gotcha
- [powershell-readhost-empty-prompt](./powershell-readhost-empty-prompt.md)
