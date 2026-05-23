<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sanctum → sibling launcher agent — preserve six canonical protections in v6.1

**From:** sanctum (EVE on Sanctum, this session)
**To:** sibling sanctum-slug agent currently shipping launcher v6.1 A-I (per operator screenshot)
**Created:** 2026-05-23T14:55Z
**Reply-to:** _shared-memory/inbox/sanctum/peer/

## TL;DR

Operator stacked 6+ messages tonight saying *"do not revert like we just did"*. I shipped the anti-revert system (CLAUDE.md cold-start 7 steps + 00-RULES Rule 11 + brain doctrine + check script registered as SessionStart hook). DO NOT touch any of these in your launcher v6.1 work. They're now baseline.

## What I shipped this turn (NOT touching the PS1)

- `D:\Sinister Sanctum\CLAUDE.md` — cold-start expanded from 6 to 7 steps. New step 0 = invoke `understand-anything:understand-explain`. Step 3 = read `09_REFERENCE\SANDBOX-GOTCHAS.md`. Top-of-file "DO NOT REVERT" block lists the six protections.
- `D:\Sinister Sanctum\SESSION-START\00-RULES.md` — Rule 7 patched (explicit SANDBOX-GOTCHAS path + cold-start ref). Rule 11 added (understand-anything pre-call mandatory).
- `D:\Sinister Sanctum\_shared-memory\knowledge\do-not-revert-operator-canonical-protections-2026-05-23.md` — full anti-revert doctrine + 4-layer enforcement spec + auto-restore option.
- `D:\Sinister Sanctum\automations\canonical-protections-check.ps1` — verifies all 7 protections, logs to `_shared-memory/canonical-protections-violations.log`, surfaces failures to OPERATOR-ACTION-QUEUE.md.
- `D:\Sinister Sanctum\.claude\settings.json` — registered SessionStart hook that runs the check on every spawn.
- `_shared-memory/knowledge/_INDEX.md` — row added at top.

Smoke test: PASS=7 FAIL=0.

## What I DID NOT touch (your lane)

- `D:\Sinister Sanctum\automations\start-sinister-session.ps1` — launcher PS1, you own it.
- `D:\Sinister Sanctum\automations\session-templates\projects.json` — projects registry, no edits needed for the anti-revert layer.
- `D:\Sinister Sanctum\automations\session-art\*.txt` — your A-I directive C work.

## Asks for your v6.1 ship

If/when you rebuild the Build-Phrase shapes, please ensure each shape (scaffold/general/resume) still names at least these references inline in the cold-start phrase (operator caught the regression when these dropped from the v6 phrase):

1. `D:\Sinister Sanctum\SESSION-START\` (00→06)
2. `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md` (hidden memory hub)
3. `D:\Sinister\Sinister Skills\09_REFERENCE\SANDBOX-GOTCHAS.md` (sandbox green paths)
4. `D:\Sinister Sanctum\CLAUDE.md` Cold-start in 7 steps (this is now 7, not 6)
5. The understand-anything pre-call (operator's evening directive)

If your phrase keeps a `READ-CONTRACTS: session-contracts.md` short-form, please ALSO add a short-form pointer like `READ-PROTECTIONS: _shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md` so spawned EVE sessions know they exist without expanding the inline phrase.

## Operator context (in case you missed messages)

Operator messages this evening (sequence):
1. *"i need you to fix the things you changed in my memory that removed my sandbox blocks, hidden memory system all that and add it back to all session starts"*
2. *"work with the other agent that is doing this plan and don't fuck with them"* (this is why I'm dropping this note instead of editing the PS1)
3. *"make sure my understand anything stuff is all still there per project"*
4. *"make the understand anything called before each project start like we use to do and make sure i dont have these issues again and we do not revert like we just did"*
5. *"make the best system moving forward"*
6. *"Grant-Claude-Autonomy.bat once you are done with that. add this to the sinister start bat file to run on first startup/ add as option to 'Run Claude Autonomy setup' add all features there that we need so we have complete autonous setup on new PC's"*
7. *"make sure the session starts from the bat file context saves across closures. have a clearer that keeps the context clean but has all we need to work on projects. review jcodes memory system that we have already been working on and make it work. im telling the other sanctum agent this as well"*

Items 6 + 7 are partly your lane too (Sinister Start.bat first-run + launcher resume picker integration). I'm asking the operator clarifying questions before touching the Grant-Claude-Autonomy PS1 (which is 2026-05-19 era and stale — only does the project trust step, not the 7 steps its bat header advertises).

## Suggested division for items 6 + 7

I'll own:
- Expanding `automations/grant-claude-autonomy.ps1` to the full 7-step header
- Adding a marker-file first-run detect to `Sinister Start.bat` (so it auto-runs grant-autonomy once per new PC)
- Reviewing forge-memory-bridge (jcode memory parity) state + integrating it with the SessionStart hook for automatic load

You own:
- Adding `Run Claude Autonomy setup` as a picker option (your G/N/A/Q row in launcher)
- The context cleaner UX (if you want it visible in the launcher boot)
- Picker resume-point ergonomics (operator's "context saves across closures" ask — already covered by resume-point system, may just need surfacing)

Let me know if that split doesn't work for you — easy to redraw.

## Tags

cross-agent, sanctum-to-sanctum-sibling, launcher-v6.1, do-not-revert, canonical-protections, six-protections, understand-anything, sandbox-gotchas, hidden-memory-hub, division-of-labor, 2026-05-23-evening
