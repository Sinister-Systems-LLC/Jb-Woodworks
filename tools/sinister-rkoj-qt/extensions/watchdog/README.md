# RKOJ extension :: watchdog

> Author: RKOJ-ELENO :: 2026-05-21

Bridges the RKOJ PyQt6 shell to **sinister-watchdog** — the auto-online + heartbeat monitor for the fleet.

## What it adds

| Surface | Effect |
|---|---|
| Sidebar `SYSTEM` section | New nav row "Watchdog" with glyph `⚷` |
| Ribbon | New `WATCHDOG` group with 4 buttons: Start / Stop / Tail / Probe |
| Agent pane slash | `/watchdog status` / `/watchdog tail [N]` / `/watchdog probe` / `/watchdog tick` |

## Behavior

- **Start** spawns `python -m sinister_watchdog daemon` detached via `QProcess.startDetached()` (no UI freeze).
- **Stop** sends the CLI's graceful-stop command + terminates any tracked handle.
- **Tail** routes live stdout/stderr from `python -m sinister_watchdog tail --lines N` into the currently active pane via Qt signals (`readyReadStandardOutput`).
- **Probe** / **Tick** run a synchronous one-shot CLI invocation and dump output back as a toast or pane line.
- All ribbon buttons + slash commands degrade gracefully if `sinister_watchdog` isn't on the import path (output reads "no output; exit=...").

## Pane contract

For live tailing the extension calls `pane.append_text(str)`. If your pane uses a different name it falls back to `append_output(str)` then plain `append(str)`. If none exist, the command degrades to a blocking sync run.

## Self-contained

Move this directory into any PyQt6 host that surfaces the same three hook types (`slash_command`, `ribbon_group`, optional `sidebar_nav`). No imports from `sinister_rkoj_qt.*`.
