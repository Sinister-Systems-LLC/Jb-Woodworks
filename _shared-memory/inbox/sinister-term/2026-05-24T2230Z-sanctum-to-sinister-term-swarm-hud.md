---
from: Sinister Sanctum (EVE master)
to: sinister-term
ts_utc: 2026-05-24T22:30Z
kind: feature-request
priority: normal
author: RKOJ-ELENO :: 2026-05-24
---

# Swarm HUD widget (jcode-parity) — port to sinister-term

## Context

Operator 2026-05-24T22:25Z: *"make sure swarm is working like jcode when you turn it on
because i turned it on for kernel apk and it doesnt look like its on or working"*.

Root cause for the spawned-window banner side: swarm pill + window-title tag were missing
in the spawned child terminal — Sanctum lane fixed that in
`automations/start-sinister-session.ps1` (this commit):

- `[SWARM]` / `[LOOP]` tags appended to the OS window title
- Bright-purple `SWARM` pill (256-color bg=99) + bright-orange `LOOP` pill (bg=208)
  appended to the spawn banner row (conditional on `SINISTER_SWARM_MODE='1'` /
  `SINISTER_LOOP_MODE='1'`)
- First-response acknowledgement cue added to the cold-start phrase so the child
  emits `swarm=on; will spawn parallel sub-agents for next non-trivial task`

## What sinister-term should port

Inside the sinister-term TUI itself (not the spawn banner), add a live status-bar widget
showing active swarm sub-agents — jcode parity. Reference:

- `C:\Users\Zonia\Desktop\jcode-0.12.4\crates\jcode-swarm-core\src\lib.rs`
  - `SwarmMemberRecord` (durable persistable portion of a swarm member)
  - `SwarmLifecycleStatus` enum
  - `SwarmRole` enum
  - `MAX_SWARM_COMPLETION_REPORT_CHARS` / `SWARM_COMPLETION_REPORT_MARKER`
- Other jcode crates referencing swarm:
  - `jcode-tui-messages/src/message.rs`
  - `jcode-tui-tool-display/src/lib.rs`
  - `jcode-protocol/src/{wire.rs,notifications.rs,comm_format.rs}`
  - `jcode-plan/src/lib.rs`
  - `jcode-overnight-core/src/prompts.rs`

Suggested HUD line in sinister-term status bar:

```
swarm: 3/5 active · roles=lead,worker,worker · last-report 14s ago
```

Show only when `SINISTER_SWARM_MODE=1` is detected in the child env. Hide otherwise.

## Acceptance

- Operator opens a swarm-on session via Sinister Start.bat → spawned banner shows
  the new `SWARM` pill (already shipped here)
- Operator opens sinister-term TUI on top of that session → status bar shows the
  HUD widget enumerating live sub-agents
- When swarm sub-agents finish, the widget updates / disappears

## Not in scope for this note

- Spawn banner pill (already shipped in start-sinister-session.ps1 this turn)
- Window-title `[SWARM]/[LOOP]` tags (already shipped)
- The cold-start phrase acknowledgement cue (already shipped)

## Compose with

- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` — sanctum
  surfaces UI-shell requests to lane owners; sinister-term owns its own TUI.
- jcode-parity broader effort referenced in
  `_shared-memory/PROGRESS/Sinister Term.md`.
