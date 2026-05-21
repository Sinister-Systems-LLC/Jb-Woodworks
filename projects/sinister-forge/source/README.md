# Sinister Forge :: source tree

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** PH0 scaffold (PH1 minimal TUI lands next push)

## What this is

Sinister Forge source. Python + Textual TUI that wraps Claude Code (and Codex) subprocesses with the jcode look-feel + full Sinister theme + multi-agent scrolling buffers + Ctrl+W new-agent keybind + eventual RKOJ Workstation merge.

See `../PLAN.md` for the full 11-phase build plan.

## Quickstart (once PH1 lands)

```powershell
# Install (editable from this dir)
cd "D:\Sinister Sanctum\projects\sinister-forge\source"
pip install -e .

# Launch
forge

# Or via the Desktop bat
C:\Users\Zonia\Desktop\Sinister Forge.bat
```

## Keybinds (PH3 target)

| Key | Action |
|---|---|
| `Ctrl+W` | New agent (opens picker overlay with the 5 questions) |
| `Ctrl+Tab` | Cycle agents |
| `Ctrl+Shift+W` | Close current agent (writes resume-point first) |
| `Ctrl+L` | Clear current pane scroll |
| `Ctrl+S` | Manual resume-point write |
| `F1` | Help |
| `F2` | Toggle RKOJ panel (PH7) |

## Stack

- **Textual** — TUI framework (Rich-backed; supports color, mouse, async, animation, virtual scroll)
- **subprocess** — spawn + manage Claude/Codex children
- **watchdog** — hot-reload skills from `_shared-memory/skills/`
- **PyYAML** — read launcher `projects.json` + `agent-prefs.json`

## Why Python + Textual not Rust + ratatui

See `PLAN.md` Q1. Default is Python for build velocity + operator readability. Rust port possible later once design stabilizes; the I/O contract (JSON-RPC over stdin/stdout per subprocess) is language-agnostic.

## Composes with

- `automations/session-contracts.md` — 6 contracts every Forge-spawned agent honors
- `automations/resume-point-write.ps1` — called per pane on close
- `automations/start-sinister-session.ps1` — same picker logic, ported into the Textual overlay
- `_shared-memory/resume-points/` — Forge reads + writes here per agent

## Source layout (PH1 target)

```
forge/
├── __main__.py     ← `python -m forge` entry
├── app.py          ← ForgeApp(textual.App)
├── theme.py        ← Sinister purple palette
├── art.py          ← Vault Boy ASCII frames + animation
├── panes/
│   ├── agent_pane.py     ← scrolling buffer + project-name header
│   ├── picker.py         ← Ctrl+W overlay
│   ├── rkoj_panel.py     ← F2 RKOJ surface
│   └── status_bar.py
├── spawn/
│   ├── claude.py
│   └── codex.py
├── resume/
│   └── point.py
└── keybinds.py
```
