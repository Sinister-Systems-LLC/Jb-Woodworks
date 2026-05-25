# Sinister Designer

**Author:** RKOJ-ELENO :: 2026-05-25

The fleet's professional / clean / artistic UI authority. Every other lane that needs UI work either consumes Sinister Designer's primitives (via `sinister-dashboard-skeleton`) or escalates the task to this lane.

## Charter

Operator hard-canonical 2026-05-25:

> "i need you to check out thes skills and add them to all agents the good ones so that we create good UI's ... i needa professional clean artistic look to my uis. the let'stext dsahoard is great but we need better work."

Sinister Designer exists to:
1. Aggregate every installed UI/design Claude Code skill into a single addressable bot.
2. Defend the LetsText dashboard's quality bar across every lane.
3. Author + extend the `sinister-dashboard-skeleton` design system (EXPAND, never fork).
4. Auto-route any "make this beautiful / professional / impeccable" task to itself.

## Skills it wraps (the ui-ux-pro-max family + frontend-design)

| sub-skill | what Designer uses it for |
|-----------|---------------------------|
| `ui-ux-pro-max` | top-of-funnel planning — picks the style (one of 50+), palette (one of 161), font pairing (one of 57), and product archetype before any pixel is drawn |
| `ui-styling` | tactical CSS / Tailwind / shadcn implementation pass |
| `design` | comprehensive design action — logo (Gemini AI, 55 styles), CIP (50 deliverables), slides (Chart.js), banners (22 styles), icons (15 styles, SVG), social photos |
| `design-system` | reusable tokens + primitives consumed by `sinister-dashboard-skeleton` |
| `brand` | logo / palette / typography / identity work — anchored on the iOS-blue ramp by default |
| `banner-design` | hero / promo art / social headers |
| `slides` | presentation decks |
| `frontend-design` | production-grade frontend scaffolding (avoids generic AI aesthetic) |

The full catalog + how every fleet agent reaches them: `_shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md`. Discovery CLI: `python automations/skills_router.py --list`.

## Quality benchmark — the LetsText dashboard

Reference implementation lives at `D:\Personal\LetsText\…` (operator-private mirror) and is also encoded in `projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md`:
- iOS dark-mode system blue `#0A84FF` as the single accent
- Liquid Glass material (`.lg-card` / `.lg-button` / `.lg-pill` / `.lg-input` / `.lg-popover`)
- One primitive per role — never inline class blobs
- Three motion durations (`150/300/600ms`), one easing curve
- Hand-drawn SVG icons only (no lucide-react in new code)
- Every primitive ships EmptyState + Loading + Error slots

Sinister Designer treats the 11 Commandments as binding for every audit + proposal.

## Public surface

`src/designer.py` exposes the `Designer` class:

```python
from src.designer import Designer
d = Designer()
d.load_benchmark()              # THEME-DOCTRINE.md + palette + commandments
d.propose_palette("sanctum")    # iOS-blue anchor + brand secondary
d.propose_component("KpiCard", intent="...")   # primitive spec with skill chain
d.audit_surface("path/to/page.html")          # 11-commandment checklist
d.route_to_skills("polish this dashboard")    # chained skill recommendation
```

Smoke: `python src/designer.py` prints a sample palette + component spec + skill chain.

## Sibling lanes

- `letstext` — the quality benchmark; Designer borrows its primitives, never copies wholesale
- `sinister-panel` — Sanctum's own operator console; Designer audits it on every UI change
- `sinister-dashboard-skeleton` — the canonical UI base; Designer commits primitives HERE first
- any UI-producing lane — must read the routing doctrine before shipping new chrome

## Default modes (operator hard-canonical 2026-05-25)

- `loop=relentless` — keep iterating on quality until acceptance criterion hits
- `swarm=on` — peer with `ui-ux-pro-max` skill calls + sibling-lane reviews each turn

## Doctrine references

- `_shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md` (this lane's foundation)
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` (EXPAND, never fork)
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md`
- `_shared-memory/knowledge/loop-swarm-default-on-doctrine-2026-05-25.md`

## Status

P0 scaffold shipped 2026-05-25. Next iterations: install 21st.dev MCP server (operator-OAuth gated), publish primitive contributions to `sinister-dashboard-skeleton`, ship first audit run against `sinister-panel`.
