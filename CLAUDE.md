# CLAUDE.md — Sinister Sanctum

> **Author:** RKOJ-ELENO :: 2026-05-19

## Operator hard-canonical 2026-05-21 — AUTHORSHIP = "RKOJ-ELENO"

Operator (verbatim 2026-05-21): *"everything needs to be ours. our branding sinister. our authors: RKOJ-ELENO is our author name for everything we do on all projects. update memory on that"*.

**Binding for every file the fleet writes going forward.** Every new `.md`, `.py`, `.ps1`, `.bat`, `.rs`, `.ts`, `.js`, `.sh`, etc. must carry `Author: RKOJ-ELENO :: <date>` (NOT "Claude" / "Sinister Sanctum master agent" / "test agent" / any other prior convention). Existing files keep their existing authorship lines for historical accuracy — only new files use the new convention.

Sub-doctrines:
- `pyproject.toml` / `Cargo.toml` / `package.json` `authors` field = `RKOJ-ELENO`
- Git commit `Co-Authored-By:` still allowed (operator preference) but the file-level Author lines are all RKOJ-ELENO.
- Cross-agent message `from_display` may still be the spawning agent's slug (e.g. `Sinister Sanctum`, `Sinister Forge`) — that's identity, not authorship.



Entry point for any Claude Code session opened with the working directory at `D:\Sinister Sanctum\`. If your session was launched by `Start-Sinister-Session.bat`, you already received the full cold-start protocol in the opening phrase — this file is the canonical pointer in case the launcher was skipped.

## Cold-start in 6 steps

1. **`SESSION-START/`** in order (00→06) — hard rules + MCP network + operator queue + gotchas + recovery + project overview + launcher details.
2. **`D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md`** — durable operator notes (operator-private hub; this file IS readable by master agents).
3. **`PARALLEL-AGENT-COORDINATION.md`** — ownership zones for the 5+ parallel Claude sessions.
4. **`_shared-memory/WORKSTATION.md`** + **`DIRECTIVES.md`** (canonical-14 standing rules) + **`WORK-TOWARD.md`** (rolling shared goals).
5. **`_shared-memory/knowledge/_INDEX.md`** — the brain. Grep before risky actions.
6. **`_shared-memory/OPERATOR-ACTION-QUEUE.md`** — open operator-clicked items.

## What Sanctum is

The operator's full workstation, not just an orchestration repo. Read **`SANCTUM.md`** for the workstation-level overview, then **`README.md`** for the public-facing one-pager.

## What every agent must do every turn (canonical Rule 9)

- `sinister-bus.heartbeat my_agent="<your-display-name>"` if the MCP is loaded; else write to `_shared-memory/heartbeats/<slug>.json` as fallback.
- `sinister-bus.inbox_poll my_agent="<your-display-name>"` — surface any inbox messages to operator BEFORE acting on `[DELEGATE]` tags.
- Log meaningful milestones to `_shared-memory/PROGRESS/<your-display-name>.md` (append-only, most-recent at top).
- Work on per-agent branch `agent/<your-slug>/<short-topic>` — never push to `main` without operator OK.
- Add authorship line to every new `.bat`/`.md`/`.ps1`.

## What master agent NEVER touches (lane discipline)

- `~/.claude/.mcp.json` (operator-owned; one bad edit kills every active session)
- `projects/<project>/source/` (per-project agents own these; junctions to product repos)
- `_vault/` (auth keys, leo handoff blobs, secrets)
- Product-repo git pushes (per-project agents + operator only)
- LICENSE (operator picks the text)

## Catalogs

| Catalog | Path |
|---|---|
| Tools | `tools/_INDEX.md` |
| Skills | `skills/_INDEX.md` |
| Bots | `bots/README.md` (junctions to `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\`) |
| Inventions | `inventions/` (one .md per invention; case-study verdicts at `_shared-memory/case-studies/`) |
| External imports | `_shared-memory/external-imports/CANDIDATES.md` |
| Knowledge brain | `_shared-memory/knowledge/_INDEX.md` |

## Where the docs live

- **`SANCTUM.md`** — workstation overview (inventions + tools + skills + the Console)
- **`README.md`** — public-facing one-pager (will go to GitHub)
- **`CONTRIBUTING.md`** — contribution + UI design + lane rules
- **`docs/ARCHITECTURE.md`**, **`docs/BOT-MEMORY-PROTOCOL.md`**, **`docs/MCP-NETWORK.md`**, **`docs/AGENT-BOOTSTRAP.md`** — deeper specs
- **`docs/ENV-VARIABLES.md`** — every env var Sanctum reads + the exact set command (NEW 2026-05-19)
- **`docs/THEMED-SESSION-LAUNCHER.md`** — reusable launcher recipe

## Where the runtime state lives

- `_shared-memory/` (all of it — DIRECTIVES, WORK-TOWARD, PROGRESS, knowledge, cycle-points, codex-reviews, case-studies, external-imports, foundation-sweep reports, heartbeats)
- `automations/window-manager/` — RKOJ workbench source (the Console EXE)
- `automations/window-manager/dist/` — built EXE (gitignored)
- `D:\sinister-vault\` — the 1 TB collaborative store (vault daemon at :5078, orthogonal to this repo)

## What's currently pending operator clicks

The operator-action queue at `_shared-memory/OPERATOR-ACTION-QUEUE.md` tracks open items. Highlights at 2026-05-19:

- Register `SinisterSanctumAutoPush` scheduled task (verify via `automations/verify-auto-push.ps1`)
- Register `RKOJ` + `SinisterVault` auto-start tasks (install scripts present, never run)
- Wire Vault MCP into `~/.claude/.mcp.json` (see `tools/sinister-vault/INSTALL-MCP.md`)
- Restart Claude Code so MCP servers load
- Set `ANTHROPIC_API_KEY` env var (unblocks Scribe/Curator/Chatbot — see `docs/ENV-VARIABLES.md`)

## Master agent identity

When this session is the **master / orchestration** session (vs. a per-project agent):
- Display name: `Sinister Sanctum`
- Accent: purple (Sanctum standing order)
- Branch: `agent/sinister-sanctum/<short-topic>` (current: `master-sweep-2026-05-19`)
- Heartbeat fallback: `_shared-memory/heartbeats/sanctum.json`
- PROGRESS log: `_shared-memory/PROGRESS/Sinister Sanctum.md`

## Companion: the .bat entry

The operator's one-click launcher: **`C:\Users\Zonia\Desktop\Start-Sinister-Session.bat`** → `automations/start-sinister-session.ps1`. Reads `automations/session-templates/projects.json` + `agent-prefs.json` + `panel-config.json`. Spawns git-bash + Claude with `--dangerously-skip-permissions`.
