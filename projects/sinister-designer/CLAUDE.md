# CLAUDE.md — Sinister Designer

**Author:** RKOJ-ELENO :: 2026-05-25

Per-lane CLAUDE.md for the `sinister-designer` project. Inherits sanctum-wide doctrine from `D:\Sinister Sanctum\CLAUDE.md`. This lane is the fleet's professional / clean / artistic UI authority.

## Lane scope

- **Tag:** Professional clean artistic UI/UX bot — aggregates `ui-ux-pro-max` (+7 sub-skills) + `frontend-design` and authors primitives for `sinister-dashboard-skeleton`.
- **Tier:** T2 (lane authority over UI quality; consumed by every UI-producing lane).
- **Sibling lanes:** `letstext` (benchmark), `sinister-panel` (audit target), `sinister-dashboard-skeleton` (primitive sink), every UI consumer.

## Charter (operator verbatim 2026-05-25)

> "i need you to check out thes skills and add them to all agents the good ones so that we create good UI's. start with this: taste skill / impeccable / awesome design md / skill ui / ui uo pro max / 21stdev mcp. i needa professional clean artistic look to my uis. the let'stext dsahoard is great but we need better work. make a project and bot for this ready for us called sinister designer. make sure all agetnts use skills we have and have efficent ways to get them etc"

## Skills available (canonical 2026-05-25)

Run `python automations/skills_router.py --list` at session start to see every loaded skill. Mandatory chain for ANY UI work:

```
ui-ux-pro-max -> design-system -> ui-styling -> frontend-design
```

Other useful chains:
- Branding / logo / CIP: `brand -> design`
- Slide deck: `slides`
- Banner / hero: `banner-design`
- UI audit: `ui-ux-pro-max` (review action) -> `code-review`

Full catalog + per-task chain table: `_shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md`.

## Public surface

`src/designer.py` — `Designer` class with `propose_palette()`, `propose_component()`, `audit_surface()`, `route_to_skills()`. Smoke: `python src/designer.py`.

## Quality benchmark

`projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md` is binding (11 Commandments + iOS Blue Ramp + Liquid Glass material). The LetsText dashboard (`D:\Personal\LetsText\…`) is the visual reference. NEVER ship UI that violates a commandment.

## Default modes

- `loop=relentless` (per `loop-relentless-pursuit-doctrine-2026-05-25.md`)
- `swarm=on` (per `loop-swarm-default-on-doctrine-2026-05-25.md`)
- `accent=purple` for Sanctum-tagged surfaces; `iOS-blue #0A84FF` for product-facing surfaces

## Lane-specific rules

1. **EXPAND, never fork.** Any missing primitive lands in `sinister-dashboard-skeleton/components/` FIRST, then is consumed. (Composes with `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24`.)
2. **Skill-first.** Before hand-writing CSS, call `skills_router.py --recommend "<task>"` and route through the returned chain.
3. **Inbox is authoritative.** Any cross-lane UI ask drops a JSON into `_shared-memory/inbox/sinister-designer/`; ack within one turn.
4. **Audit every PR.** When another lane ships UI, this lane runs `Designer.audit_surface()` and replies via fleet-update channel.
5. **No half-ass.** UI features ship every surface (mobile + desktop + dark + empty-state + error) together OR are not claimed shipped (per `eve-ui-uniformity-doctrine-2026-05-24`).
6. **No operator clicks.** 21st.dev MCP install is the only operator-gated action (OAuth carve-out). Everything else is automated.

## Authorship

Every new `.py`/`.md`/`.css`/`.ts` in this lane carries `Author: RKOJ-ELENO :: <date>`.

## Doctrine references

- `_shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md`
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/loop-swarm-default-on-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md`
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`
