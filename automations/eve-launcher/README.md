<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# eve-launcher :: EVE.exe (thin fast picker for Sinister Sanctum)

Operator (verbatim 2026-05-23): *"can we make bat file start a exe file start like jcode does that has our starting features to spawn agents and such. make sure we have all speed settings and performacnce increase from jcode"* + *"i want this as eve.exe not the rkoj exe"*.

## What this is

`EVE.exe` is a single-file Windows binary built from `eve.py` via PyInstaller. It is the **fast cold-start picker** for spawning Sinister Sanctum project agents. Target: jcode-class boot time (jcode is ~48 ms time-to-first-input, ~167 MB RAM; PowerShell launcher's host bootstrap alone is ~600-800 ms).

EVE.exe handles the common path (numeric pick / G / multi-select) entirely in Python (stdlib only, no module cascade), then dispatches to the canonical PS1 launcher in headless mode (`start-sinister-session.ps1 -Project <key>`) for the actual spawn. For sub-flows that need PS1's interactive UX (A/N/R/K/S), EVE.exe transparently hands off to the full PS1 picker.

## Why thin

- The PS1 launcher (`automations/start-sinister-session.ps1`) is ~53 KB. Every spawn reparses it.
- PowerShell host startup is ~600 ms even with `-NoProfile`. EVE.exe has zero PowerShell on the hot path.
- PyInstaller `--onefile` adds ~15-20 MB to the binary but cold-starts in ~150-300 ms.
- All the heavy lifting (trust-pre-acceptance, mintty spawn, status pills, sterm handoff, resume-point auto-write) stays in PS1 — single source of truth.

## How it composes with the existing launcher

```
Sinister Start.bat  ->  EVE.exe        (if present, fast path)
                    \-> start-sinister-session.ps1  (fallback / full picker)

EVE.exe  ->  start-sinister-session.ps1 -Project <key>    (numeric / G)
        \->  start-sinister-session.ps1                   (A/N/R/K/S/F)
```

## Build

```cmd
cd "D:\Sinister Sanctum\automations\eve-launcher"
build-eve-exe.bat
```

Requires Python 3.10+ on PATH. PyInstaller is installed automatically if missing. Output: `dist\EVE.exe` (~15-20 MB).

## Install (optional)

Copy `dist\EVE.exe` somewhere `Sinister Start.bat` can find it. The bat probes:

1. `%~dp0EVE.exe` (Desktop next to the bat)
2. `%SINISTER_SANCTUM_ROOT%\automations\eve-launcher\dist\EVE.exe`
3. `%LOCALAPPDATA%\Sinister\EVE.exe`

If none found, the bat falls back to the PS1 launcher (no regression).

## Speed measurement

`eve.py` self-reports boot-to-first-input in milliseconds in the banner. Compare against:

| Tool                 | Time to first input |
|----------------------|---------------------|
| jcode (baseline)     | 48.7 ms             |
| Antigravity CLI      | 383.7 ms            |
| Codex CLI            | 905.8 ms            |
| Claude Code          | 3512.8 ms           |
| EVE.exe (target)     | < 300 ms            |
| PS1 launcher (today) | ~800-1200 ms        |

## Doctrine

Brain entries:
- `_shared-memory/knowledge/eve-exe-launcher-jcode-speed-parity-2026-05-23.md`
- `_shared-memory/knowledge/jcode-feature-matrix.md` (row for EVE.exe to be added)

Composes with `agent-identity-eve.md` (EVE persona) — the binary name reflects the persona.

## What EVE.exe does NOT do

- No mintty spawn (PS1 owns that).
- No claude trust-pre-acceptance (PS1 owns that).
- No sterm post-claude handoff (PS1 owns that — runs inside the spawned shell).
- No resume-point write logic (delegated to `resume-point-write.ps1`).
- No interactive sub-flows (A/N/R/K/S) — those dispatch into PS1.

Single responsibility: the fast picker UI. Everything else stays in the PS1, which keeps the launcher behavior 1:1 with what's documented + reduces drift between EVE.exe and the script.
