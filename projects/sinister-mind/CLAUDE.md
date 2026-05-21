# Sinister Mind :: CLAUDE.md

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-mind` :: branch `agent/sinister-mind/<topic>` :: purple

## What you're working on

Sinister Mind = the visual mind-graph for the Sanctum brain. Flask + D3.js force-directed graph w/ Sinister theme (dark + purple primary, neural-architecture cluster aesthetic). Sidebar: project filter, complex search, tag chips, shortest-path-between-concepts. Live-streams brain entries / cross-agent / plans / heartbeats / resume-points. Optional Ruflo agentdb wiring for semantic-similarity edges (graceful fallback to tag overlap).

Read `projects/sinister-mind/README.md` for the full scope + 10-phase plan.

## Cold-start

Inherit standard contracts from `automations/session-contracts.md`. Plus Mind-specific:

1. Read `projects/sinister-mind/README.md` for current phase.
2. Read `projects/sinister-mind/source/PLAN.md` for forward-plan rows.
3. Read recent PROGRESS/Mind entries.
4. Check `projects/sinister-mind/source/mind/static/index.html` if working on frontend.
5. Check `projects/sinister-mind/source/mind/server.py` if working on backend.

## Lane rules

- Branch on `agent/sinister-mind/<topic>` cut from `main`.
- All Mind source goes in `projects/sinister-mind/source/`.
- Frontend is **vanilla HTML + D3.js** — no React/Node build step. Drop new .js files in `mind/static/`; the Flask server serves them.
- Backend is **Flask** — keep endpoints under `mind/server.py` until they need their own modules.
- AGPL-3.0 headers on every file: `Author: RKOJ-ELENO :: <date>`.

## What stays out of Mind

- Brain entry CREATION — Mind only READS. Brain entries are written by other agents during their work.
- Cross-agent message creation — same, read-only here.
- The RKOJ workbench iteself — Mind embeds as iframe, doesn't fork.
- Forge — sibling project, not a fork target. Mind links INTO Forge panes via PH9; doesn't replace.

## Operator directive

> *"in the graph we make i need it to look like this in theme with a side bar to tell me where things are complex searching etc. and i can see the by project breakdown in here and essentially be a more powerful obsidan mind graph using jcode and all other skills."*

## Related

- `projects/sinister-mind/README.md` — full scope
- `projects/sinister-mind/source/PLAN.md` — phase plan
- `projects/sinister-forge/source/PLAN.md` — sibling
- `automations/session-contracts.md` — 6 binding contracts
