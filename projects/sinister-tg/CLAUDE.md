# Sinister TG :: CLAUDE.md

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-tg` :: branch `agent/sinister-tg/<topic>` :: purple
> **Source-of-truth:** `C:\Users\Zonia\Desktop\Sinister TG\` (via `source/` junction; 399 MB / 1069 files)

Sinister TG = the Telegram automation lane. Status per the original `D:\Sinister\01_Projects\Sinister\_status.md`: `⚪ unknown / not recently touched`. Slot created 2026-05-21 during the D-drive reorg to bring the lane into Sanctum's index; activation gated on operator picking a focus topic.

## Lane rules

- Branch on `agent/sinister-tg/<topic>` cut from `main`.
- Source code lives at `source/` (NTFS junction into operator's Desktop). Edit through the junction.
- Author: `RKOJ-ELENO :: <date>` on every new file.
- AGPL-3.0 headers on new source files.

## Cold-start

Inherit `automations/session-contracts.md`. Plus TG-specific:
1. Survey `source/` (`ls projects/sinister-tg/source/`) to inventory what's there.
2. Check operator's intent — TG is currently dormant; activation needs a topic.
3. Cross-lane: `projects/sinister-snap-emu/` + `projects/sinister-bumble-emu/` share emulator infrastructure if TG uses similar patterns.

## Related

- `projects/sinister-emulator-bundle/` — if TG uses the shared emu core
- `_shared-memory/inbox/sinister-tg/` — cross-agent messages once active
- `_shared-memory/PROGRESS/Sinister TG.md` — append-only progress (create on first turn)
