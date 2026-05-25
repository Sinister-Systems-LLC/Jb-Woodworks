<!-- decay: category=routing, confidence=1.0, half_life_days=365 -->
# Skills Inventory + Routing Doctrine (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim (2026-05-25)

> "i need you to check out thes skills and add them to all agents the good ones so that we create good UI's. start with this: taste skill / impeccable / awesome design md / skill ui / ui uo pro max / 21stdev mcp. i needa professional clean artistic look to my uis. the let'stext dsahoard is great but we need better work. make a project and bot for this ready for us called sinister designer. make sure all agetnts use skills we have and have efficent ways to get them etc"

## TL;DR

Every fleet agent has access to a curated catalog of installed Claude Code skills via `~/.claude/settings.json` `enabledPlugins[]`. The **UI/design family** (ui-ux-pro-max + 7 sub-skills + frontend-design) is now MANDATORY for any UI work. The **Sinister Designer** lane (`projects/sinister-designer/`) is the fleet's design authority — any task involving UI quality, polish, branding, or "make this beautiful" routes through it. Agents discover and chain skills via `automations/skills_router.py`.

## THE inventory (every skill every agent can call)

### UI / Design (MUST-USE for any UI work)

| skill | plugin | path | trigger keywords | when to use |
|-------|--------|------|------------------|-------------|
| **ui-ux-pro-max** | ui-ux-pro-max-skill v2.5.0 | `…/skills/ui-ux-pro-max/SKILL.md` | "professional ui", "polish", "ui/ux", "design pro" | new UI surface or polish existing — 50+ styles, 161 palettes, 57 font pairings |
| **ui-styling** | ui-ux-pro-max-skill v2.5.0 | `…/skills/ui-styling/SKILL.md` | "style this", "tailwind", "css", "shadcn" | tactical CSS / Tailwind / shadcn work |
| **design** | ui-ux-pro-max-skill v2.5.0 | `…/skills/design/SKILL.md` | "design a", "logo", "CIP", "mockup", "brand identity", "deck", "banner", "icon", "social photo" | comprehensive design action — logo (55 styles, Gemini AI), CIP (50 deliverables), slides (Chart.js), banners (22 styles), icons (15 styles), social photos |
| **design-system** | ui-ux-pro-max-skill v2.5.0 | `…/skills/design-system/SKILL.md` | "design system", "tokens", "primitives", "component library" | reusable token/component library |
| **brand** | ui-ux-pro-max-skill v2.5.0 | `…/skills/brand/SKILL.md` | "brand", "palette", "typography", "impeccable" | logo / palette / typography / identity |
| **banner-design** | ui-ux-pro-max-skill v2.5.0 | `…/skills/banner-design/SKILL.md` | "banner", "hero", "promo art", "social header" | hero / promo art / social headers |
| **slides** | ui-ux-pro-max-skill v2.5.0 | `…/skills/slides/SKILL.md` | "deck", "presentation", "slides" | slide deck / presentation |
| **frontend-design** | claude-plugins-official | `…/frontend-design/skills/frontend-design/SKILL.md` | "frontend", "react", "vue", "next.js", "build a page" | new frontend scaffolding — production-grade, avoids generic AI aesthetic |

### Code / Analysis / Workflow

| skill | when |
|-------|------|
| **understand-anything** (+ understand-explain / understand-diff / understand-domain / understand-dashboard / understand-knowledge / understand-chat / understand-onboard) | cold-start step 0 — load architectural context before substantive work |
| **commit-commands** (commit / commit-push-pr / clean_gone) | git commit / PR workflow |
| **code-review:code-review** + **pr-review-toolkit:review-pr** + **security-review** | PR review / security audit |
| **simplify** | reuse / quality / efficiency sweep on changed code |
| **claude-api** | building/migrating Claude SDK apps (caching, thinking, tool use) |
| **claude-md-management** (revise-claude-md / claude-md-improver) | CLAUDE.md authoring + audits |
| **claude-code-setup:claude-automation-recommender** | auditing fleet automation surface |
| **hookify** (writing-rules / configure / hookify / help / list) | hook authoring + management |
| **update-config** | settings.json / permissions / env vars / hooks |
| **fewer-permission-prompts** | reduce permission prompts on repeated tool calls |
| **keybindings-help** | ~/.claude/keybindings.json edits |
| **session-report** | usage / token / skills audit of recent sessions |
| **schedule** + **loop** | cron / recurring routine setup |
| **init** | new CLAUDE.md bootstrap |
| **cwc-makers** (m5-onboard / cardputer-buddy) | M5Stack ESP32 device provisioning |

### Missing (TODO install — request from operator on next session)

- **21st.dev MCP server** (`@21st-dev/magic`) — the operator-named "21stdev mcp"; once Anthropic marketplace adds it, install via `npx @21st-dev/magic` and add the server stanza to `~/.claude/.mcp.json` (operator-gated). Provides 21st.dev component search + insertion. Until installed, fall back to **shadcn/ui MCP** which `ui-ux-pro-max` already integrates with.

### Operator name → skill mapping (verbatim phrase decoding)

| operator phrase | resolved skill |
|-----------------|----------------|
| "ui uo pro max" / "ui ux pro max" | `ui-ux-pro-max` |
| "skill ui" | `ui-styling` (sub-skill of ui-ux-pro-max) |
| "awesome design md" | `design` SKILL.md (sub-skill of ui-ux-pro-max) |
| "impeccable" | `brand` + `design-system` chain |
| "taste skill" | `design` SKILL.md + curated mode (manual-route until a dedicated "taste" skill appears) |
| "21stdev mcp" | 21st.dev MCP server (TODO install) |

## How every agent reaches them

1. **Skills auto-attach** via `~/.claude/settings.json` `enabledPlugins[]` — already configured. The session opener lists every loaded skill in the system-reminder block.
2. **To DISCOVER what's available in a session:** check the system message at session start; or run `python automations/skills_router.py --list`.
3. **To INVOKE:** describe the task in natural language. The Claude harness routes automatically based on the SKILL.md frontmatter `description` field. For explicit invocation, use the Skill tool with `skill="<name>"`.
4. **For complex multi-skill workflows:** call `python automations/skills_router.py --recommend "<task description>"` to get an ordered JSON chain.

## Trigger-keyword → skill-chain mapping

| operator/task pattern | recommended chain |
|-----------------------|-------------------|
| "build a beautiful dashboard" / "make this UI professional" / "polish ui" | `ui-ux-pro-max` → `design-system` → `ui-styling` → `frontend-design` |
| "make a logo" / "brand identity" / "CIP" | `brand` → `design` |
| "make a deck" / "presentation" / "slides" | `slides` |
| "make a banner" / "hero image" / "social header" | `banner-design` |
| "build a frontend page" / "next.js page" / "react component" | `frontend-design` → `ui-styling` |
| "design tokens" / "primitives" / "component library" | `design-system` → `ui-styling` |
| "audit ui" / "review ui code" | `ui-ux-pro-max` (review action) → `code-review` |
| "audit codebase" / "understand this project" | `understand-anything:understand` → `understand-anything:understand-explain` |
| "commit + push + PR" | `commit-commands:commit-push-pr` |
| "audit security" | `security-review` |

## Sinister Designer project

- **Lane:** `projects/sinister-designer/`
- **Role:** the FLEET'S design-system authority. Every other lane that needs UI work either consumes Sinister Designer's primitives (via `sinister-dashboard-skeleton`) or escalates the task to its lane.
- **Trigger phrase:** any operator request mentioning UI quality, "looks bad", "make this beautiful", "professional ui", "polish" should auto-route a copy of the task to `_shared-memory/inbox/sinister-designer/`.
- **Default modes:** `loop=relentless`, `swarm=on` (per operator hard-canonical 2026-05-25 ~06:30Z).
- **Quality benchmark:** the LetsText dashboard (`D:\Personal\LetsText\…`) + `projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md` (the 11 Commandments + iOS Blue Ramp + Liquid Glass material).
- **Public surface:** `projects/sinister-designer/src/designer.py` — `Designer` class with `propose_palette()`, `propose_component()`, `audit_surface()`, `route_to_skills()`.

## How a new fleet agent picks up skills (cold-start)

Add to every project's `CLAUDE.md` "Lane scope" block:

```
## Skills available (canonical 2026-05-25)
Run `python automations/skills_router.py --list` at session start.
Mandatory chain for UI work: ui-ux-pro-max → design-system → ui-styling → frontend-design.
Sinister Designer lane owns design-system authority — escalate UI quality concerns to its inbox.
Doctrine: _shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md
```

## Anti-patterns

1. **Hand-coding CSS / colors** when `ui-styling` or `design-system` skills are available.
2. **Re-inventing design tokens** when the LetsText dashboard already ships an iOS-blue ramp + Liquid Glass material in `sinister-dashboard-skeleton/THEME-DOCTRINE.md`.
3. **Letting agents miss `ui-ux-pro-max`** because they don't know it's auto-loaded — the inventory CLI exists so every cold-start sees the list.
4. **Forking primitives instead of expanding the skeleton** (composes with `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`).
5. **Skipping the Sinister Designer escalation** when the operator says "make this look better" — the lane exists precisely so quality concerns don't dilute across N agents.
6. **Installing 21st.dev MCP without operator OAuth/confirmation** — MCP server installs are operator-gated per `automate-everything-no-operator-admin-2026-05-25` (the OAuth carve-out).

## Composes with

- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base = dashboard-skeleton; EXPAND, never fork)
- `sanctum-scope-discipline-2026-05-24` (Sanctum stays high-level; designer lane owns UI execution)
- `automate-everything-no-operator-admin-2026-05-25` (no operator clicks; OAuth-only carve-out for 21stdev MCP install)
- `loop-relentless-pursuit-doctrine-2026-05-25` + `loop-swarm-default-on-doctrine-2026-05-25` (sinister-designer defaults)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (UI claims require same-turn smoke evidence)

## Pass criterion

- `python automations/skills_router.py --list` prints ≥ 5 skills with one-line summaries.
- `python automations/skills_router.py --recommend "build a beautiful dashboard"` returns JSON containing `ui-ux-pro-max` in `skills[]`.
- Every new UI work-unit produced by the fleet either (a) is owned by sinister-designer, or (b) cites which skills it consulted in its PROGRESS row.
- New CLAUDE.md files for UI-producing lanes carry the "Skills available" block shown above.

## Updated

2026-05-25 — initial version (RKOJ-ELENO).
