# session-launcher

The Sinister session-start module. Boots a working session with a chosen agent, project context, and a structured opening prompt.

## What it does

Walks the operator through a guided startup:

- **R** — resume the most recent session.
- **G** — guided scaffold (pick agent, pick project, pick custom prompt).
- **N** — register a new project on the fly and persist it.
- **C** — choose a custom prompt template.

Then it emits a structured Sanctum section header into the agent transcript so every session begins with consistent context (agent name + accent color, project paths, lane, today's date, durable directives).

Defaults are deliberately quiet: `-NoNotepad` is the default, the launcher auto-closes the host window 5 seconds after handing off, and the prompt block is copy-paste ready.

## How to invoke (operator-facing)

Double-click the desktop shortcut:

```
C:\Users\Zonia\Desktop\Start-Sinister-Session.bat
```

The .bat shells into the PowerShell entry point. No arguments required for the default flow.

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\automations\start-sinister-session.ps1`
- `D:\Sinister Sanctum\automations\session-templates\projects.json`
- `D:\Sinister Sanctum\automations\session-templates\agent-prefs.json`
- `D:\Sinister Sanctum\automations\session-templates\custom-prompts.json`
- `C:\Users\Zonia\Desktop\Start-Sinister-Session.bat`

## Dependencies

- Windows PowerShell 5.1+
- Read/write access to `D:\Sinister Sanctum\automations\session-templates\` (the JSON files act as persistent state).
- No third-party PowerShell modules required.

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

shipped

## Linked-inventions

- (none yet — invention captures that evolve this tool should be linked here)

## Changelog

- **2026-05-19** — Initial registration. v4 features locked in: R / G / N / C menu, agent name + accent color injection, `-NoNotepad` default, 5-second auto-close, structured Sanctum section headers in the opening prompt.
