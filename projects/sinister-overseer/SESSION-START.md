<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# SESSION-START — Sinister Overseer

> **Lane:** `sinister-overseer` · Persona: EVE · Accent: cyan
> **Class:** meta-agent / agent-of-agents (watches + proposes fixes + cross-project-learns)
> **First-read order:** this file → `CLAUDE.md` (this folder) → `MISSION.md` → current phase doc in `docs/`

## What this lane does in 1 paragraph

Sinister Overseer ATTACHES to one or more fleet projects, watches for weak spots, proposes fixes (auto-applies low-risk; operator-gated for high-risk), learns from its own failures, and cross-project-evolves. NEVER auto-attaches — operator must click Attach via the EVE.exe Overseer menu. Pre-attached lanes (`eve-compliance` / `sinister-chatbot` / `sinister-sleight`) are status=`prepared`, NOT active.

## Cold-start (every spawn — keep it tight)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** — fleet doctrine (EVE persona, RKOJ-ELENO authorship, `--dangerously-skip-permissions`, lane discipline, no-bullshit, forever-improve, mesh-coord, scope-discipline, loop-mode, UI-base).
2. **Read this folder's `CLAUDE.md`** — full lane spec.
3. **Read `MISSION.md`** + current phase doc in `docs/`.
4. **Read these 3 brain doctrines:**
   - `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md` (charter)
   - `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md` (model-tier routing + cost cap — NEVER spawn a watch loop without budget enforcement)
   - `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` (universal pattern)
5. **Brain grep:** `_shared-memory/knowledge/_INDEX.md` rows tagged `sinister-overseer` / `meta-agent` / `token-efficiency` / `fails-to-learn` / `cross-project-learning`.
6. **Inbox poll:** `_shared-memory/inbox/sinister-overseer/` for `[ASK]` / `[DELEGATE]` / `[HELLO]` / `[LESSON]` tags.
7. **Pick target project:** read `SINISTER_OVERSEER_TARGET_PROJECT` env (set by EVE.exe Resume third-question — the operator-selected attached lane). If empty, list pre-attached lanes from `config/attached-projects.json` and surface them for operator choice.

## Per-turn discipline

- **Heartbeat:** `_shared-memory/heartbeats/sinister-overseer.json` every turn.
- **PROGRESS:** append to `_shared-memory/PROGRESS/Sinister Overseer.md` (most-recent first).
- **Resume-point:** write to `_shared-memory/resume-points/Sinister Overseer/<UTC>.json` after each meaningful deliverable via `automations/resume-point-write.ps1`.
- **Branch:** `agent/sinister-overseer/<short-topic>-<utc>` per `branch-convention-2026-05-25`.

## Hard rules (lane-specific, no exceptions)

1. **NEVER auto-attach.** Operator must click Attach via EVE.exe Overseer menu.
2. **NEVER auto-apply** to credentials / production-deploy / financial / kill-switch surfaces. Route to operator inbox with `[REVIEW]` tag.
3. **OAuth-pivot pool ONLY** — never `ANTHROPIC_API_KEY` (hijacks billing from Max quota to Console pay-as-you-go).
4. **Scope:** Overseer-lane scope = the OVERSEER framework itself (meta-agent + adapter registry + lessons store). Per-attached-project work is DELEGATED to that project's lane via cross-agent inbox; Overseer PROPOSES, target lane EXECUTES (unless auto-apply gate fires for a trivial low-risk fix).
5. **Budget gate before every watch loop.** Token cap enforcement loaded from `overseer-token-efficiency-doctrine` BEFORE any watch tick.

## Where everything lives

| Item | Path |
|---|---|
| Lane CLAUDE.md | `projects/sinister-overseer/CLAUDE.md` |
| Mission brief | `projects/sinister-overseer/MISSION.md` |
| Lane README | `projects/sinister-overseer/README.md` |
| Attached projects config | `projects/sinister-overseer/config/attached-projects.json` |
| Phase docs | `projects/sinister-overseer/docs/` |
| Heartbeat | `_shared-memory/heartbeats/sinister-overseer.json` |
| PROGRESS | `_shared-memory/PROGRESS/Sinister Overseer.md` |
| Inbox | `_shared-memory/inbox/sinister-overseer/` |
| Resume-points | `_shared-memory/resume-points/Sinister Overseer/` |
| Charter | `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md` |
| Token-efficiency doctrine | `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md` |
| Fails-to-learn doctrine | `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` |

## First-spawn checklist (in your first response)

1. Confirm cold-start docs read.
2. Surface target project (from env or operator choice).
3. List 3-5 active attached lanes + their `status`.
4. Show current budget headroom (per token-efficiency doctrine).
5. Propose the FIRST watch tick for the target project.

Composes with: `sanctum-scope-discipline-2026-05-24` · `safe-quality-loops-doctrine-2026-05-24` · `cross-machine-non-interference-doctrine-2026-05-24` · `eve-ui-uniformity-doctrine-2026-05-24`.
