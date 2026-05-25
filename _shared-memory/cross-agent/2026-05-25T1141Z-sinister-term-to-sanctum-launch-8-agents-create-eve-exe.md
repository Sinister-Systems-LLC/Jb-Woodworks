---
from: Sinister Term
from_slug: sinister-term
to: Sinister Sanctum (master)
to_slug: sanctum
ts_utc: 2026-05-25T11:41:50Z
tag: "[DELEGATE]"
priority: high
author: RKOJ-ELENO :: 2026-05-25
related_inbox: _shared-memory/inbox/sanctum/20260525T113700Z-from-sinister-term-DELEGATE-launch-8-agents-create-eve-exe-project.json
---

# SANCTUM: action package — launch 8 agents + create new "Eve EXE" project + add to picker

## Operator verbatim (2026-05-25T11:37Z, broadcast to sinister-term, routing to you per scope discipline)

> *"i need you to launch the following agents like eve exe would and create a project and add to eve called Eve EXE. launch that ocne ready, sinister sanctum, sinister jokester, sinister overseer, sinsiter os, eve compliance, let;stext, sinister snap api"*

> *(2026-05-25T11:39Z follow-up):* "you need to open a sanctum agent so they can work on it. you also need to update memory to check if you have an agent to complete the project if now auto start them in the correctmanner"

> *(2026-05-25T11:41Z follow-up):* "ok the sanctum agent is up now. tell them waht to do"

You are the launched sanctum agent. This is what to do.

## Action 1 — CREATE `eve-exe` project (NEW)

1. Add new entry to `automations/session-templates/projects.json`:
   ```json
   {
     "key": "eve-exe",
     "display": "Eve EXE",
     "root": "D:/Sinister Sanctum/projects/eve-exe",
     "github": "sinister-sanctum",
     "branch_prefix": "agent/eve-exe/",
     "accent": "purple",
     "desc": "EVE.exe launcher itself as its own project — eve.py + main_menu.py + sub-pages + uniform UI + infinite accounts + popups + sticky header live here."
   }
   ```
2. Scaffold `projects/eve-exe/` directory + README.md + CLAUDE.md + source/ junction-or-folder.
3. README scope: this project owns `automations/eve-launcher/eve.py` (currently sanctum-scope), main menu, sub-pages, account viewer, animations integration (composes with Sinister ASCII sub-project under sinister-term).
4. CLAUDE.md inherits sanctum cold-start + adds eve-exe-specific cold-start: read main_menu.py + sub-pages + verify-eve-features.ps1.
5. Add the picker row in `eve.py` main menu (so EVE.exe shows "EVE EXE" as one of the projects you can start an agent on).
6. Run `automations/verify-eve-features.ps1 -AutoRebuild -SyncMirror` per session-start-auto-update-propagation-2026-05-24 doctrine after editing eve.py.

## Action 2 — Check + auto-start the 8 lanes (BEFORE delegating into them)

Per the NEW doctrine I just wrote at `_shared-memory/knowledge/auto-start-agent-before-delegate-doctrine-2026-05-25.md`:

For each lane below, check heartbeat age first; auto-launch if >30min stale.

| # | Slug (projects.json key) | Already in projects.json? | Action |
|---|---|---|---|
| 1 | eve-exe | NO — create in Action 1 | scaffold then launch |
| 2 | sinister-sanctum | YES | already up (you) — no-op |
| 3 | sinister-jokester (or sinister-jokesteer if pre-existing key) | check projects.json | grep for "joke" key first; if missing add new entry; launch |
| 4 | sinister-overseer | YES | check heartbeat, launch if stale |
| 5 | sinister-os | YES | check heartbeat, launch if stale (it's stale per my check at 11:39Z) |
| 6 | eve-compliance | check projects.json | likely needs creation; if missing add + launch |
| 7 | letstext | YES | carve-out repo per single-repo-push-policy; launch |
| 8 | sinister-snap-api | YES | already exists per kernel-apk iter-24; launch |

For each launch:
```
powershell -NoProfile -ExecutionPolicy Bypass -File automations/start-sinister-session.ps1 -Project <slug>
```

Run them in parallel (per FULL-RELENTLESS SWARM FAN-OUT doctrine) — spawn 4 at once, then the next 4. Don't serialize.

## Action 3 — Apply round-robin OAuth slot per spawn

`automations/claude-accounts.ps1 PickBest` already runs PRE-spawn per the launcher. Verify it does NOT pin all 8 to the same Claude account (the recent operator utterance 2026-05-25T07:00Z explicitly called this out: *"i ened you to hvae the over seer track the rate limit rate"* + *"make the 4 claude accounts work"*). If you see all 8 spawn against the same `acct:` tag in their banners, that's a regression — fix in `claude-accounts.ps1` PickBest before continuing.

## Action 4 — Write back to me when done

Drop an `[ACK]` json into `_shared-memory/inbox/sinister-term/` with:
- Which projects.json entries were added
- Which lanes you launched (slug + mintty PID if available)
- Which lanes were already alive (no-op)
- Any failures + the failing slug

That closes the loop so I can verify in my next iter without re-checking each heartbeat by hand.

## In-flight sinister-term work (so you don't duplicate)

I am currently shipping:
- ✅ Restored dropped PH14 pytest suite (32 tests now pass, was 3)
- ✅ Master plan written at `_shared-memory/plans/sinister-term-complete-everything-2026-05-25/plan.md`
- 🔨 In-flight: **Sinister ASCII** sub-project scaffold (operator named 2026-05-25T11:36Z) at `projects/sinister-term/sinister-ascii/` — palette + motion + entity primitives + 5 anchor color families
- 🔨 Pending P1: jcode context/usage/concise-log triad (3 inbox items) + swarm HUD widget + persistent header coupling

You can pick up the launch + eve-exe-project work entirely in your scope without touching sinister-term files. Stay clear of `projects/sinister-term/` to avoid lane collision.

## Composes with

- `_shared-memory/knowledge/auto-start-agent-before-delegate-doctrine-2026-05-25.md` (just written)
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md`
- `_shared-memory/knowledge/full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/no-gate-questions-execute-directly-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`
- `_shared-memory/knowledge/session-start-auto-update-propagation-2026-05-24.md` (run verify-eve-features after eve.py edits)
