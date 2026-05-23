# Plan: Leo-launcher-ready (2026-05-23 evening)

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Goal:** Leo can `git clone` Sinister-Sanctum, double-click `Sinister Start.bat`, and have a working EVE session with no manual fixes. Everything tested + on GitHub.

## What's already done (verified)

- ✅ HEAD `80d4f7a` pushed to `origin/agent/sinister-sanctum/grant-autonomy-followup-2026-05-23`
- ✅ Sinister Start.bat v6.3 — simple `start "" "%EXE%"` syntax + async plugin install + portable banner path
- ✅ sinister-banner.sh — animated 256-color ASCII C from image #3
- ✅ check-required-plugins.ps1 — `-Silent` + `-AutoInstall` (covers required + recommended)
- ✅ Zombie EVE.exe instances killed
- ✅ Cold-start prompt verified delivering to claude (image #8)

## Open items

### Phase A — EVE.exe rebuild (parallel agent)

Current EVE.exe at `automations/eve-launcher/dist/EVE.exe` (8.4 MB) was built earlier. Needs verification:

1. Rebuild via `automations/eve-launcher/build-eve-exe.bat`
2. Confirm new build picks up latest `eve.py` (the version that dispatches to PS1)
3. Smoke-test: `EVE.exe` alone shows picker; selecting `1` dispatches to PS1; PS1 spawns claude

### Phase B — End-to-end bat test (parallel agent)

Run the full launch flow from a clean state:

1. Kill all existing EVE / claude / cmd / mintty processes
2. Double-click `C:\Users\Zonia\Desktop\Sinister Start.bat`
3. Verify: no plugin-check output on screen (`-Silent` works)
4. Verify: EVE.exe picker window appears (own console)
5. Verify: parent bat window closed (X button works on picker)
6. Pick `1` (Sanctum), confirm: mintty spawns, banner animates, claude UI loads, cold-start phrase visible as first user message
7. Close mintty via X → confirm clean shutdown + resume-point write

### Phase C — Leo prerequisites doc (parallel agent)

Audit + write `docs/LEO-SETUP.md` (or update existing) covering:

1. What Leo needs to install (Git for Windows, Claude Code CLI, Python optional)
2. Where to clone the repo (`D:\Sinister Sanctum` OR set `SINISTER_SANCTUM_ROOT`)
3. Env vars needed (`ANTHROPIC_API_KEY` for Scribe/Curator/Chatbot — see `docs/ENV-VARIABLES.md`)
4. First-run flow (autonomy bootstrap → plugin install → launcher)
5. Common pitfalls (zombie processes, lock contention, missing plugins)
6. How to verify the install worked (`Sinister Start.bat --diagnose`)

### Phase D — Final sweep + push (this agent)

1. Commit remaining ~461 unstaged files (per-lane PROGRESS, inbox, resume-points)
2. Verify `local HEAD == remote HEAD`
3. Tag the commit `leo-ready-2026-05-23` for easy reference

## Acceptance criteria

- [ ] EVE.exe rebuilt, verified, committed to dist/
- [ ] End-to-end bat test passes
- [ ] docs/LEO-SETUP.md exists + accurate
- [ ] All commits pushed to origin
- [ ] Tag pushed: `leo-ready-2026-05-23`

## Loop completion signal

When all four checkboxes above are ✅, post final confirmation to operator and stop the /loop wakeup cycle.
