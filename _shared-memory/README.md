# _shared-memory/ — cross-agent shared directives

Every Claude session spawned by `Start-Sinister-Session.bat` (master, snap-emu, tiktok-emu, panel, kernel-apk, etc.) reads this folder during cold-start. It's the operator's persistent sticky-note that ALL agents see.

## What lives here

| File | Purpose |
|---|---|
| `DIRECTIVES.md` | Standing operator directives. Appended via `Update-Sanctum-Memory.bat`. Every entry is dated. NEVER deleted — superseded entries are marked `[superseded YYYY-MM-DD]`. |
| `WORK-TOWARD.md` | Current shared goals across the Sinister LLC suite. What agents should be moving towards together. |
| `notes/` | Ad-hoc cross-agent notes. Free-form. Append-only. |

## How agents consume this

The launcher's cold-start phrase (every mode except `scaffold`) includes:

> "ALWAYS read `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` + `WORK-TOWARD.md` at session start. These are operator's standing instructions for ALL agents."

So each spawned Claude reads these on its first turn and incorporates them.

## How the operator updates this

**Easiest:** double-click `C:\Users\Zonia\Desktop\Update-Sanctum-Memory.bat`. Asks:

1. Which file? (1=DIRECTIVES.md, 2=WORK-TOWARD.md, 3=new note)
2. Title / one-liner
3. Body (multi-line; finish with Ctrl+Z)

The bat prepends a timestamped entry. Other agents see it on their next cold-start.

**From the Sanctum Console UI:** the right pane has a "Shared Memory" card with a text box + "Append to DIRECTIVES" button. POSTs `/api/shared-memory/append`.

**Manually:** open the .md file in any editor. New entries go at the TOP (most recent first).

## Lane discipline

- This folder is shared across ALL agents — every agent has read access.
- Only master / orchestration / operator should EDIT these files.
- Per-agent notes belong in the agent's own `01_MEMORY/<agent>/` folder, NOT here.

## TL;DR

- **How we won:** One folder. Every agent reads it. Operator writes once → everyone sees it next time they spawn.
- **What you need to do:** Use `Update-Sanctum-Memory.bat` whenever you want a directive to propagate to every future Claude session.
