<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# CLAUDE.md — Showmasters Site

> Project root: `C:\Users\Zonia\Desktop\Showmasters Site\` (the actual marketing-site working tree)
> Sanctum harness root: `D:\Sinister Sanctum\` (where all _shared-memory/, knowledge/, automations/ live)
> Agent slug: `showmasters`
> Display name: `Showmasters`
> Persona: EVE (per `_shared-memory/knowledge/agent-identity-eve.md`)

## Why this file exists

The Showmasters marketing site lives on the **Desktop** (`C:\Users\Zonia\Desktop\Showmasters Site\`) so the operator can drag-and-drop assets / open `index.html` directly. But the **Sinister Sanctum harness** (PROGRESS, heartbeats, resume-points, brain, automations, knowledge, etc.) lives at `D:\Sinister Sanctum\`. The prior CLAUDE.md here incorrectly assumed a parallel harness at `C:\Users\Zonia\Desktop\_shared-memory\` and `C:\Users\Zonia\Desktop\automations\` — neither directory exists. That's the bug the operator screenshot caught (the agent spawned, looked for the local harness, found nothing, asked which path to use).

**The single harness is at `D:\Sinister Sanctum\`. This file pins it.**

## What this project is

Show Masters Production Logistics — marketing site for the live-events / production-logistics company. Static-site stack (`index.html` + `style.css` + `script.js` + ~25 sub-pages). No build step. Brand pack at `BRANDING/`. Marketing copy at `MARKETING/`. V2 staging at `app-v2/`.

Working-tree files (this directory):
- Project briefs: `PLAN.md`, `STACK.md`, `SECURITY.md`, `HOSTING.md`
- Site root: `index.html`, `style.css`, `script.js`, `manifest.json`, `sitemap.xml`, `robots.txt`, `404.html`
- City pages: `orlando.html`, `houston.html`, `dallas.html`
- About / how / press: `about.html`, `crew.html`, `shows.html`, `how.html`, `insurance.html`, `case-studies.html`, `careers.html`, `contact.html`, `order.html`, `press.html`, `faq.html`, `glossary.html`
- Legal: `privacy.html`, `cookies.html`, `accessibility.html`
- Sub-trees: `BRANDING/`, `MARKETING/`, `app-v2/`, `public/`, `.claude/`

## Cold-start (every spawn — read these BEFORE substantive work)

1. **Read `D:\Sinister Sanctum\CLAUDE.md`** — fleet-wide doctrine (EVE persona, RKOJ-ELENO authorship, --dangerously-skip-permissions default, lane discipline).
2. **Read `D:\Sinister Sanctum\SESSION-START\`** (`00-RULES.md` → `06-LAUNCHER-DETAILS.md`, in order).
3. **Read `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md`** + **`WORK-TOWARD.md`** + **`OPERATOR-ACTION-QUEUE.md`** rows tagged `showmasters`.
4. **Grep `D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md`** for `showmasters` tags before risky actions.
5. **Read the latest resume-point** at `D:\Sinister Sanctum\_shared-memory\resume-points\Showmasters\<HIGHEST-UTC>.json`. If none, fall back to top of `D:\Sinister Sanctum\_shared-memory\PROGRESS\Showmasters.md`.

## Standard fleet I/O paths

| What | Where |
|---|---|
| Heartbeat | `D:\Sinister Sanctum\_shared-memory\heartbeats\showmasters.json` |
| PROGRESS log (append-only, newest at top) | `D:\Sinister Sanctum\_shared-memory\PROGRESS\Showmasters.md` |
| Resume-points (display-name dir per `resume-point-dir-name-convention`) | `D:\Sinister Sanctum\_shared-memory\resume-points\Showmasters\<UTC>.json` |
| Inbox | `D:\Sinister Sanctum\_shared-memory\inbox\showmasters\` |
| Plans | `D:\Sinister Sanctum\_shared-memory\plans\showmasters-*/` |

Write a new resume-point at end of every meaningful deliverable:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\resume-point-write.ps1" -SanctumRoot "D:\Sinister Sanctum" -ProjectKey showmasters -AgentName showmasters -Mode resume
```

## Per-agent branch

Work on `agent/showmasters/<short-topic>` cut off the latest doctrine HEAD. Push freely per `_shared-memory/knowledge/agent-autonomy-push-and-completion-2026-05-23.md`.

## Image generation

Use `D:\Sinister Sanctum\projects\sinister-generator\` (per-project brand-lock helpers in `nano_banana`). Showmasters brand-pack docs at `D:\Sinister Sanctum\projects\sinister-generator\memory\per-project\showmasters\`. Generation cost ~$0.039 per image. Operator-gated: requires Google Cloud billing on project `492031902572` enabled.

## What this project NEVER touches

- `D:\Sinister Sanctum\_vault\` (operator secrets)
- `~/.claude/.mcp.json` (operator-owned)
- Other projects' sources under `D:\Sinister Sanctum\projects\<other>/`
- LICENSE (operator chooses)

## Launcher env vars (exported by `start-sinister-session.ps1`)

The launcher exports these into the spawn shell — use them to locate things if the hard-coded paths above ever move:

- `SINISTER_SANCTUM_ROOT` = `D:\Sinister Sanctum` (override with env var)
- `SINISTER_PROJECT_KEY` = `showmasters`
- `SINISTER_PROJECT_DISPLAY` = `Showmasters`
- `SINISTER_AGENT_NAME` = `showmasters` (or whatever R) Rename + Color set)
- `SINISTER_ACCENT_COLOR` = `purple` (or whatever R) Rename + Color set)
- `SINISTER_MODE` = `resume`

## Conventions

- **No build step** — edit HTML/CSS/JS directly. If you introduce one, document it here first.
- **Single stylesheet, single script** — keep `style.css` and `script.js` as the only globals unless splitting is justified in PROGRESS.
- **Don't invent infrastructure** — if a Sanctum path doesn't resolve, surface it; don't fake parallel harness paths (that's the bug this file fixes).
- **PROGRESS is append-only** — never rewrite history; add corrective entries instead.
