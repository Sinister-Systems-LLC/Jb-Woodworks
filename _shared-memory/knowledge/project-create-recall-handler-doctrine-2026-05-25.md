<!-- decay:
  category: tooling
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# Project CREATE / RECALL Canonical Handler Doctrine (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim (2026-05-25)

> *"make sure the system has a place for a project create or project recall handling that agents will find and know if i ask them to do either of them. auto add and catergories all projects to eve exe"*

## THE single place to look

**`D:\Sinister Sanctum\automations\project_manager.py`** — every fleet agent uses this CLI when the operator asks to create / recall / list / categorize a project. No more ad-hoc scaffolding scripts.

## Triggers (every Sanctum agent recognizes these)

| Operator says... | Agent runs |
|------------------|------------|
| "create a new project for X" / "scaffold a project called Y" / "spin up Z" | `python automations/project_manager.py create <key> --display "<X>" --tag "<one-liner>"` |
| "remember the project about X" / "what was that Y project" / "recall Z" | `python automations/project_manager.py recall "<X>"` |
| "list all projects" / "what projects do we have" | `python automations/project_manager.py list` |
| "categorize the projects" / "organize the picker" | `python automations/project_manager.py categorize` |
| "add X to the picker" | `python automations/project_manager.py add-to-picker <key>` |

## What `create` does (8 steps, all automatic)

1. Validates key (`^[a-z0-9][-a-z0-9]*$`)
2. Scaffolds `projects/<key>/README.md` + `CLAUDE.md` + `PROGRESS/<display>.md`
3. Appends entry to `automations/session-templates/projects.json` with:
   - `tier=3` (default; override with `--tier`)
   - `github=Sinister-Systems-LLC/Sinister-Sanctum` (single-repo policy; override with `--github`)
   - `default_modes={swarm:true, loop:"relentless"}` (per loop+swarm-default doctrine)
4. Adds key to `picker.visible_keys` so it appears in EVE.exe project picker
5. Runs `categorize` automatically — places key in correct picker.categories bucket
6. Writes heartbeat stub at `_shared-memory/heartbeats/<key>.json`
7. If `--sibling` passed, links it for cross-lane coordination (R32 sister-project doctrine)
8. Returns JSON summary with: key / display / tier / github / category / scaffolded path

## What `recall` does

Searches across **5 surfaces** in one pass:
1. `projects.json` (key / display / tag fields) — primary
2. `_shared-memory/PROGRESS/<display>.md` — recent activity context
3. `_shared-memory/heartbeats/<slug>.json` — last-active timestamp (recency boost)
4. `_shared-memory/operator-utterances.jsonl` — operator mentions
5. `_shared-memory/knowledge/` — brain doctrine for that project

Returns ranked top-N matches with score + last-active + first matching PROGRESS line.

## Auto-categorize rules

Keyword-based (case-insensitive match against `key + display + tag`):

| Keywords | Category |
|----------|----------|
| sanctum / custodian / memory / sleight / imessage | Sanctum + Core |
| api / sdk / wrapper / emulator / rkoj | Tooling + API |
| woodworks / showmasters / letstext / compliance | Client Sites |
| term / ancestral / remotion / theme | Sinister Term |
| overseer | Overseer |
| kernel / panel / chatbot / freeze / generator / snap / tiktok / bumble / jkor / quantum / jbw / os | Sinister Systems |
| (no match) | Other |

The `--categorize` action rebuilds `picker.categories[]` from these rules. Run it whenever new projects are added.

## Binding rules for every Sanctum agent

1. **Never scaffold a project by hand.** Always go through `project_manager.py create`. This guarantees the entry lands in projects.json, the picker, the categories, and the heartbeat dir simultaneously.
2. **When operator says "create"** — invoke this script immediately. Don't ask "what should I call it?"; pick a sensible kebab-case key from the operator's words.
3. **When operator says "recall" / "remember" / "find that project"** — invoke `recall` first, surface top 3 matches with last-active context.
4. **When new project is registered** — picker.categories auto-updates so EVE.exe picker sees the new entry on next render. No manual JSON edit needed.

## Composes with

- `_shared-memory/knowledge/one-terminal-per-project-no-overlap-doctrine-2026-05-25.md` (1 terminal/project — `create` ensures heartbeat stub exists)
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` (default github = Sinister-Sanctum)
- `_shared-memory/knowledge/loop-swarm-default-on-doctrine-2026-05-25.md` (default_modes preset)
- `_shared-memory/knowledge/sanctum-master-full-control-doctrine-2026-05-25.md` (no per-action confirmation needed)
