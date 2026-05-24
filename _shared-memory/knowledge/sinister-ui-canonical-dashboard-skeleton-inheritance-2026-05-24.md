<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Sinister UI Canonical — Dashboard-Skeleton Inheritance (BINDING)

> **Status:** doctrine, binding for every UI surface across the fleet (web, desktop, mobile, OS shell, kiosk).
> **Origin:** operator hard-canonical 2026-05-24, mid-loop:
> *"UPDATE in memory that everything must follow the same feel and look of our dashboards, found in the dashboard skeleton. including the mobile app"*

## What this binds

Every Sinister UI surface — Panel, OS shell kiosk, mobile app, every per-project dashboard, every embedded admin tab (filebrowser/Gitea/Rocket.Chat/Guacamole brand wrappers), every operator-facing tool — inherits from **`projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md`**.

That theme doctrine's 11 Commandments are the floor:

1. One palette, two extensions (background neutrals + accent ramp; rainbow forbidden)
2. One primitive per role (one Button always `rounded-full`, one Card, one Input, one Chart, one Icon, one TabHeader, one StatCard)
3. No stock icons (no `lucide-react`; custom SVG sprite only)
4. No emojis in UI chrome
5. No AI-slop copy (global banned-phrase list)
6. Motion = system (3 durations: 150/300/600 ms; one easing `cubic-bezier(0.22, 1, 0.36, 1)`)
7. Liquid Glass material (backdrop-filter blur + saturate + ultra-thin border + inset highlight + accent-tint outer shadow; `.lg-card` / `.lg-card-hero` / `.lg-rail` / `.lg-pill` / `.lg-button` / `.lg-input` / `.lg-popover` — never roll-your-own)
8. Numbers animate (NumberTicker on first paint; never static)
9. Per-page signature (PageShell signature class; one detail per route nobody else has)
10. Every primitive ships EmptyState + Loading + Error slots
11. Production parity TODO block in every vault note

## Where this binding diverges

Dashboard-skeleton's accent is **iOS-blue #0A84FF**. Sinister-fleet accent is **Sinister purple #c084fc** (operator's Sinister Panel screenshot is the canon).

**Per-surface accent token:**

| Surface | Accent | Rationale |
|---|---|---|
| Sinister Panel (operator + Leo) | `#c084fc` purple | Operator's canon screenshot |
| Sinister OS kiosk shell | `#c084fc` purple | Inherits Panel |
| Sinister mobile app | `#c084fc` purple | Inherits Panel |
| Per-project (JOKR, Showmasters, JB Woodworks, JKOR, Letstext) | per-brand from their brand-lock | Each project's brand-lock helper sets the surface accent |
| Dashboard-skeleton vault (operator's reference template) | iOS-blue `#0A84FF` | Preserved; this is the canonical template, NOT the consumer surface |

Every consumer surface SHIPS one accent token (`--accent: <color>`); all other colors derive (button bg = `color-mix(--accent ...)`, glow = `color-mix(--accent ...)`).

## Implementation map

| Surface | Implementation path | Status |
|---|---|---|
| Sinister Panel | `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/` (Next.js 15 + React 19 + Tailwind 4 + lucide-react) | 🟡 Has lucide; needs migration to sprite per Commandment 3 |
| Sinister OS kiosk | `projects/sinister-os/source/docker-stack/` panel placeholder + `iso-build/airootfs/srv/sinister-panel/` baked | 🟡 Placeholder uses purple but not full Liquid Glass yet |
| Sinister mobile app | `projects/sinister-kernel-apk/` (Android) | ⏳ Not yet started M6 |
| Filebrowser theme | `source/docker-stack/config/filebrowser/branding.css` (planned M2) | ⏳ |
| Gitea theme | `source/docker-stack/config/gitea/templates/sinister.css` (planned M2) | ⏳ |
| Rocket.Chat theme | Admin → Layout → Custom CSS (planned M2) | ⏳ |
| Guacamole theme | `config/guacamole/sinister-skin.jar` (planned M3) | ⏳ |

## The shared token file (single source of truth)

Ship `projects/sinister-os/source/docker-stack/config/theme/sinister-theme-tokens.css` so every embedded service can `@import` it. The token set:

```css
:root {
  --bg:            #0e0a1f;
  --bg-2:          #1a1330;
  --surface:       #251a3d;
  --border:        color-mix(in oklab, white 10%, transparent);
  --border-strong: color-mix(in oklab, white 16%, transparent);

  --accent:         #c084fc;             /* sinister purple */
  --accent-soft:    #a78bfa;
  --accent-strong:  #8b5cf6;
  --accent-tint:    color-mix(in oklab, #c084fc 18%, transparent);

  --text:           #e9d5ff;
  --text-soft:      #cbd5e1;
  --text-muted:     #94a3b8;

  --success:        #86efac;
  --warning:        #fde047;
  --danger:         #fca5a5;

  --motion-fast:    150ms;
  --motion-med:     300ms;
  --motion-slow:    600ms;
  --easing:         cubic-bezier(0.22, 1, 0.36, 1);

  --radius-sm:      6px;
  --radius:         10px;
  --radius-lg:      16px;
  --radius-full:    9999px;

  --shadow-glow:    0 8px 32px color-mix(in oklab, var(--accent) 18%, transparent);
  --shadow-card:    0 4px 12px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 0 color-mix(in oklab, white 14%, transparent);
}
```

## Lane responsibilities

| Lane | Responsibility |
|---|---|
| `sinister-panel` | Migrate lucide → custom SVG sprite; adopt `.lg-*` classes from skeleton; switch accent to `--accent: #c084fc` |
| `sinister-os` | Ship `sinister-theme-tokens.css` + apply to every embedded service in docker-stack (M2) |
| `sinister-kernel-apk` (mobile) | React Native theme bridge that maps token names; same accent |
| `sinister-dashboard-skeleton` | KEEPS iOS-blue as reference template; per-consumer forks set their own accent |
| Per-project (Showmasters / JB Woodworks / JKOR / Letstext) | Each gets a brand-lock helper that maps token names to its brand colors |

## Doctrine

When any agent writes a new UI surface:
1. Read this doctrine row + the dashboard-skeleton THEME-DOCTRINE.md
2. Reuse the canonical token set (sinister-theme-tokens.css)
3. Never roll a one-off Button / Card / Input / Chart — use the canonical primitive or fork it explicitly
4. Add a `## Production parity TODO` block in the new surface's lane note

When the operator says "this UI doesn't feel right" → check against the 11 Commandments + token usage. Most regressions = ad-hoc CSS instead of `.lg-*` classes, or stock lucide icons sneaking in.

## Brain INDEX row

Indexed in `_shared-memory/knowledge/_INDEX.md` under "UI / theme" with tag `sinister-ui-canonical`.

---

## Operator reinforcement 2026-05-24 (15:44Z) — the EXPAND principle

Operator (verbatim, second utterance reinforcing the same doctrine):

> *"update memory everything that makes a ui needs to base off our dsahboard skeleton so we have the same uniform clean look across projects and each time we make a dahsbaord and such we need to expand on that"*

This adds one new binding clause to the doctrine: **every new dashboard is an EXPANSION of the skeleton, not a fork.** When a lane needs a primitive or pattern the skeleton doesn't have yet, the lane:

1. **Adds the primitive to `projects/sinister-dashboard-skeleton/dashboard-skeleton/`** first (PR / commit there), then consumes it.
2. **Updates `THEME-DOCTRINE.md`'s 11 Commandments** if the new primitive introduces a new role (e.g., "one DataGrid" if a project needs the first virtualized table).
3. **Adds a row to `PATTERNS.md`** in the skeleton with: pattern name · use-case · which surface first needed it · before/after screenshot or token diff.
4. **NEVER rolls a one-off ad-hoc primitive** in a per-project repo when the skeleton lacks one — that path is exactly what produces the "different feel across projects" the operator is preventing.

The skeleton grows monotonically. Per-project lanes only diverge on the per-surface accent token + brand-lock palette (see "Where this binding diverges" above). All primitives, motion, layout grammar, empty/loading/error slots, and number-animation conventions remain shared.

### Audit hook (post-doctrine)

When any agent ships a UI surface, post-merge self-audit:

| Check | Pass criterion |
|---|---|
| Reuses `.lg-*` primitives | Grep new surface for `className.*lg-` → ≥1 match per Card/Button/Rail/Pill |
| Imports tokens | Surface CSS contains `@import` or inline reference to `sinister-theme-tokens.css` (or per-brand equivalent) |
| No stock lucide-react | `grep -r "from 'lucide-react'" <surface>/` → 0 matches |
| Per-page signature | New route has at least one PageShell signature class no other route uses |
| Skeleton expansion logged | If a new primitive was needed, `dashboard-skeleton/PATTERNS.md` has a fresh row |

A failing audit doesn't block the PR — it logs a row in `_shared-memory/improvement-log.jsonl` via `automations/forever-improve.ps1 -Action Review` (cold-start step 10).

### Composes with

- `forever-improve-review-doctrine-2026-05-24` — the EXPAND principle is forever-expansion applied to UI
- `github-first-sourcing-doctrine-2026-05-24` — before adding a primitive, check the skeleton AND GitHub for an existing component
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — "shipped a uniform UI" requires the audit hook above to pass, not just visual approval

