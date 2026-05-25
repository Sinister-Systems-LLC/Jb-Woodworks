# BRAND-BRIEF.md — Sinister Designer

**Author:** RKOJ-ELENO :: 2026-05-25
**Audience:** the spawned `sinister-designer` agent (and every future iteration).
**Authority this brief defers to:** `projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md` (binding) + `PATTERNS.md` + `D:\Personal\LetsText\dashboard\` (visual benchmark).

Read end-to-end BEFORE touching any UI. This is the charter.

---

## 1. BRAND BLOCK — Sinister Systems LLC

### Identity
- **Company:** Sinister Systems LLC
- **Operator:** RKOJ-ELENO (one human; multi-lane fleet of EVE agents)
- **Authorship tag (every new file):** `Author: RKOJ-ELENO :: <YYYY-MM-DD>` on every new `.py` / `.md` / `.css` / `.ts` / `.tsx` / `.js` / `.ps1` / `.bat` / `.rs` / `.sh`
- **Persona for operator-facing chrome:** EVE (never "Claude")
- **Designer mandate (operator verbatim 2026-05-25):** *"i needa professional clean artistic look to my uis. the let'stext dsahoard is great but we need better work. make a project and bot for this ready for us called sinister designer."*

### Palette — Sanctum-facing surfaces (PURPLE)
EVE.exe TUI · Sanctum control panels · agent dashboards · master tools · the snap-api-quantum dashboard. Purple is the Sanctum-master signature.

| Token   | Hex       | Role                                            |
|---------|-----------|-------------------------------------------------|
| PURPLE  | `#c084fc` | Primary accent (Sanctum-facing surfaces)        |
| BRIGHTP | `#d8b4fe` | Hover / active accent variant                   |
| DARKP   | `#6b21a8` | Header rules, dividers, deep accent backgrounds |
| PALEP   | `#e8d6ff` | Soft tint background / wash                     |
| WHITE   | `#f5f5f7` | Primary text                                    |
| SOFT    | `#98a2b3` | Secondary text                                  |
| DIM     | `#6b7280` | Tertiary text / muted                           |
| OK      | `#34c759` | Success state (sparing)                         |
| WARN    | `#ffcc00` | Warning state                                   |
| FAIL    | `#ff3b30` | Error / destructive                             |

### Palette — Product / customer-facing surfaces (iOS-BLUE)
LetsText · sinister-panel customer surfaces · any consumer Sinister Systems product. **The 11 Commandments mandate iOS-blue `#0A84FF`. NEVER ship a customer surface in purple.** Binding ramp:

| Step    | Hex       | Role                              |
|---------|-----------|-----------------------------------|
| 400     | `#3399FF` | Secondary accent / focus ring     |
| 500     | `#007AFF` | iOS light-mode reference          |
| **600** | **`#0A84FF`** | **PRIMARY (dark-mode)**       |
| 700     | `#0060CC` | Hover / pressed                   |

Alias tokens (always prefer over literal hex): `--accent` / `--accent-hover` / `--accent-pressed` / `--accent-soft` / `--accent-ring`. `--success` is aliased to `var(--accent)` — no green pixels (operator 2026-05-17). Only `--danger #E5484D` and `--warning #F5A524` are semantic survivors alongside the accent.

### Project-specific carve-outs (allowed)
- **JB Woodworks**: gold `#c9a84c` + cream + ink (`#080808`), DM Serif Display + Inter — own brand, documented in `projects/jb-woodworks/app/globals.css`.
- **Showmasters**: own carve-out (own repo, own palette per `projects/showmasters/site/BRANDING/`).

### When to use which accent
- **Purple** (`#c084fc`): EVE.exe, Sanctum control, agent-facing dashboards, fleet-update notes, internal tools, master surfaces, snap-api-quantum dashboard.
- **iOS-Blue** (`#0A84FF`): LetsText product, sinister-panel customer-facing pages, any consumer Sinister Systems product.
- **Carve-outs** (gold for JB Woodworks, etc.): EXPLICIT documented per-project carve-outs only.

### Binding doctrine
`projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md` is the law. When it conflicts with a sibling note, IT WINS. This BRAND-BRIEF defers to it.

---

## 2. DASHBOARD SKELETON BLOCK — the canon

The skeleton lives at `projects/sinister-dashboard-skeleton/dashboard-skeleton/`. Every UI we ship inherits from it. **EXPAND, never fork.** If a primitive is missing, add it to the skeleton FIRST, commit there, update `PATTERNS.md`, THEN consume it from the target surface.

### The 11 Commandments (verbatim summary from THEME-DOCTRINE.md)
1. **One palette, two extensions.** Neutrals + accent ramp. Rainbow forbidden. Semantic survivors: `--danger`, `--warning`; success/info alias to accent.
2. **One primitive per role.** `<Button>` (always `rounded-full`), `<Card>`, `<Input>`, `<Chart>`, `<Icon>`, `<TabHeader>`, `<StatCard>`. Never inline class blob. Never raw `<button>`.
3. **No stock icons.** Every glyph hand-drawn SVG at `components/icons/sprite.svg`. `lucide-react` BANNED in new code (ESLint). Eve glyph = geometric crystal (never sparkle / wand).
4. **No emojis in UI.** Vault `.md` may; runtime UI / JSX text / system prompts cannot. Emojis route through `<Icon>`.
5. **No AI-slop copy.** Global banned-phrase list: "Great question!" · "Certainly!" · "I'd be happy to" · "Feel free to" · "Let me know if" · "Don't hesitate to" · "As an AI" · "I'm here to help" · "Here's a draft:" · "Hope this helps" · em-dash recap tic · triplet tic ("clean, simple, and effective") · ", etc." / " and more" · unprovoked emoji. Enforced ESLint + `doctrine-audit.mjs`.
6. **Motion is a system.** Three durations: `--motion-fast 150ms`, `--motion-med 300ms`, `--motion-slow 600ms`. One easing: `cubic-bezier(0.22, 1, 0.36, 1)` (iOS ease-out). No bounce without spring.
7. **Liquid Glass material.** Backdrop blur (28px cards / 16px pills / 12px inputs / 36px popovers) + `saturate(180%)` + ultra-thin borders + inset white highlight + accent-tinted drop shadow. Use `.lg-*` classes only.
8. **Numbers are never static.** KPIs use `<NumberTicker>` on first paint (0 → value over `--motion-slow`). `<StatCard>` / `<KpiCard>` are canonical big-number containers.
9. **Pages have a signature.** Every route has ONE detail nobody else has (Page Signatures table in THEME-DOCTRINE.md).
10. **Every primitive ships `EmptyState` + `Loading` + `Error` slots.** No raw spinners. No "Loading…" text.
11. **Production parity is mandatory.** Every sandbox change ships with a `## Production parity TODO` block.

### Liquid Glass class taxonomy (`tokens/globals.css`)
| Class             | Recipe                                                                     | Use                                              |
|-------------------|----------------------------------------------------------------------------|--------------------------------------------------|
| `.lg-card`        | 70% surface-1 + 28px blur + 180% saturate + inset highlight + accent drop  | Default panel                                    |
| `.lg-card-hero`   | 72% surface-1 + 32px blur + 190% saturate + 18px radius + breathe anim     | Hero panel (top-of-page metric strip)            |
| `.lg-rail`        | 72% surface-1 + 28px blur + less inner highlight                           | Sidebar, right rail                              |
| `.lg-popover`     | 96% surface-1 + 36px blur                                                  | DropdownMenu / Popover / Select content          |
| `.lg-pill`        | 70% surface-2 + 16px blur + `border-radius: 999px`                         | Inactive filter chip / inactive tab pill         |
| `.lg-pill-active` | accent bloom on `.lg-pill` + accent border + outer drop + white label      | Active filter chip / active tab pill             |
| `.lg-button`      | 80% surface-1 + 18px blur + accent border + accent bloom + scale-on-press  | Primary CTA — "lit from beneath"                 |
| `.lg-input`       | 75% surface-1 + 12px blur + 6% white border (accent border on focus)       | Input / textarea (shadcn defaults inherit)       |

`.lg-card-hero` carries the ONE ambient animation (`lg-hero-breathe`, 10s cycle, imperceptible shadow shift). Silenced under `prefers-reduced-motion: reduce`.

### Surface neutrals
`--surface-0 #0A0A0F` (canvas) · `--surface-1 #13131A` (card base) · `--surface-2 #1C1C24` (elevated / hover / popover) · `--surface-3 #2A2A33` (border / separator).

### Text levels
`--text-primary #FFFFFF` · `--text-secondary #A1A1AA` · `--text-tertiary #71717A` · `--text-disabled #52525B`.

### Canonical primitives (locked)
- **`components/ui/`** — `Button` (variants: `default | glow | destructive | outline | secondary | ghost | link | subtle | bare`; every shipping variant emits `rounded-full`), `Card` (`tone="default|hero|kpi"`), `Badge`, `Input`, `Textarea`, `Select`, `DropdownMenu`, `Popover`, `Dialog` (uses `.lg-card-hero`), `Tooltip` (lightweight CSS-hover; Radix Slot loops in React 19), `Avatar`, `Switch`, `Label`, `Checkbox`, `Separator`, `Skeleton`, `ScrollArea`.
- **`components/primitives/`** — `TabHeader`, `KpiCard`, `Chart` (line / area / bar / donut / spark), `PageShell`, `GeoHeat`, `GlassDialogHeader`, `AdvancedFilter`, `FilterPillRow`, `EmptyState`, `LoadingState`, `ErrorState`, `SectionHeader`, `NumberTicker`, `Glow`, `AuroraBg`.
- **`components/shared/`** — `StatCard`, `Money` (blue `$` + white digits + font-mono tabular-nums), `EmptyState`, `LoadingState`, `QueryError`, `SkeletonVariants`.
- **`components/eve/`** — `EveObservationsCard`.

### EVE.exe TUI canonical contract (per `eve-ui-uniformity-doctrine-2026-05-24`)
Every EVE.exe sub-page is:
- **Header line:** `{DARKP}---{RESET} {WHITE}{BOLD}<title>{RESET} {DARKP}---{RESET}`
- **3-15-line body** using canonical tokens (PURPLE / BRIGHTP / OK / WARN / FAIL / DIM / WHITE / SOFT / DARKP).
- **Footer:** `B) Back  H) Home  X) Exit  (page-specific keys)`.
- B / empty-Enter → main picker; X → `sys.exit(0)`.
- Accounts panel + Health view + round-robin iterator must scale to N (no 4-slot cap).

### CI Enforcement (5 gates)
- **ESLint** — bans `lucide-react`, raw hex outside theme, banned phrases, emoji code points.
- **TypeScript** — `<Icon name="…">` literal-union enforcement.
- **`doctrine-audit.mjs --strict`** — drift detector (lucide imports / raw hex / emoji bytes / banned phrases / raw `<button>` outside `components/ui/` / pill regression).
- **`eve-prompt-safety-check.mjs`** — guardrails + banned phrases still present in Eve system prompts.
- **`probe-routes.mjs`** — HTTP smoke every route (200 or 307/308 → `/login`).

`npm run gates` chains them all. Required before any "shipped" claim.

---

## 3. ALL UIs WE'VE SHIPPED — fleet inventory

Every surface a UI/UX-pro-max-class designer needs to know about. Path → purpose → state → grade (A/B/C).

### A. Benchmark — the bar to beat

| # | Surface | Path | Purpose | State | Grade |
|---|---------|------|---------|-------|-------|
| 1 | **LetsText production dashboard** | `D:\Personal\LetsText\dashboard\` (Next.js 15 + Tailwind + Prisma) | Customer-facing creator dashboard (`/inbox`, `/smart-messenger`, `/vault`, `/templates`, `/analytics`, `/tracking-links`, `/fans`, `/calls`, `/agency`, `/admin`, `/audit`, `/compliance`, `/docs`). Cloudflare + Railway deploy. `npm run gates` gating. | Shipped, production. Operator: "let'stext dsahoard is great." iOS-blue Liquid Glass, 11 Commandments enforced. | **A** (the benchmark) |
| 2 | **LetsText 2.0 sandbox** | `D:\Personal\LetsText\2.0\dashboard-local\` | Next-gen sandbox where new primitives prove out before promotion to prod | Active iteration. Source of truth for THEME-DOCTRINE + Liquid Glass + Page Signatures. | **A** |

### B. Sinister-fleet web surfaces (Sinister Designer's territory)

| # | Surface | Path | Purpose | State | Grade |
|---|---------|------|---------|-------|-------|
| 3 | **Dashboard skeleton (canonical UI base)** | `projects/sinister-dashboard-skeleton/dashboard-skeleton/` (Next.js + Tailwind + tokens + lg-* classes + 5 gates) | The skeleton every fleet UI inherits — Liquid Glass primitives + THEME-DOCTRINE + iOS-blue ramp + Eve glyph sprite + audit scripts | Active. Contains `THEME-DOCTRINE.md` (binding), `PATTERNS.md`, `enforcement/`, `tokens/`. **EXPAND, never fork.** | **A** (the canon) |
| 4 | **Sinister Panel (production)** | `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/` — Next.js with ~20+ routes: `admin`, `analytics`, `automation`, `bitmoji`, `browsers`, `bumble`, `chatter`, `command-center`, `database`, `export`, `for-sale`, `for-use`, `groups`, `login`, `mind-graph` (w/ BrainGraph), `phones`, `providers`, etc. | Operator's mission-control panel — agency/automation/compliance hub | Active multi-route Next.js. Built without enforcing THEME-DOCTRINE; needs Liquid Glass parity pass. | **B** (functional, needs upgrade) |
| 5 | **JB Woodworks marketing site** | `projects/jb-woodworks/` (Next.js 15 + Tailwind + framer-motion + Prisma + Resend + `lucide-react` — own carve-out) | Marketing site v0.3.0 — routes: `/`, `/about`, `/portfolio`, `/services`, `/contact`, `/blog`, `/legal` + RSS + sitemap + error/loading/404 | Shipped. Gold `#c9a84c` carve-out brand. DM Serif Display + Inter. `globals.css` has its own design system (intro-curtain, shimmer, ease-out-soft). | **B+** (own carve-out brand executed cleanly) |
| 6 | **Showmasters site** | `projects/showmasters/site/` — ~25+ static HTML (`index`, `about`, `accessibility`, `blog`, `careers`, `case-studies`, `contact`, `cookies`, `crew`, `dallas`, `glossary`, `houston`, `how`, `insurance`, `order`, `orlando`, `press`, `privacy`, `shows`, …) + `app-v2/` (Next.js migration: `app/`, `components/`, `lib/`, `prisma`, `components.json`, `tailwind.config.ts`) | Marketing / operational site (carve-out brand, own repo) | Mixed: legacy static HTML + in-progress Next.js v2 migration | **C** (split static + Next; needs unification on app-v2) |
| 7 | **Sinister Quantum dashboard** | `projects/sinister-snap-api-quantum/outputs/sanctum-quantum-dashboard.html` (+ dated snapshots `dashboard-2026-05-23T*.html`) | Quantum research dashboard — one-shot self-contained HTML | Uses correct Sanctum purple `#c084fc` + dark surfaces + accent-soft tinted banners. Self-contained CSS; does NOT inherit Liquid Glass. | **C+** (canonical purple, no Liquid Glass) |
| 8 | **Snap-emu agent dashboards** | `projects/sinister-snap-emu/source/agent-dashboards/` — `AGENT-PROGRESS-PROTOCOL.md`, `AGENT-UI-SYSTEM-HANDOFF.md`, `PROGRESS.md`, `per-agent/snap-emu.md` | Spec docs for agent-progress UI system + per-agent progress log | Spec only; web implementation pending | **n/a (docs)** |
| 9 | **EVE.exe TUI launcher** | `automations/eve-launcher/eve.py` (+ `animations.py`, `build-eve-exe.py`, `garden_of_eden.py`, `smoke-animation.py`) | THE operator's session launcher (jcode-style ASCII C banner + numbered project picker + status line + spawn dispatch). Project list: Sanctum / Panel / Kernel APK / Emulator / RKOJ / Snap-API / TikTok-Emu / Bumble-Emu / Freeze / JB-Woodworks / Showmasters + G/A/N. | Active. Sanctum purple accent. TUI baseline solid; per `eve-ui-uniformity-doctrine-2026-05-24` every sub-page needs uniform header/footer + infinite-accounts iterator. | **B** |

### C. Designer's own surface
| # | Surface | Path | Purpose | State | Grade |
|---|---------|------|---------|-------|-------|
| 10 | **Sinister Designer (this lane)** | `projects/sinister-designer/` (CLAUDE.md, README.md, src/designer.py, BRAND-BRIEF.md) | UI authority bot — aggregates ui-ux-pro-max + design-system + ui-styling + frontend-design + brand + banner-design + slides | Scaffolded 2026-05-25; first iteration on initial spawn. | **scaffold** |

**UI surface count: 10** (8 product/fleet surfaces + 1 benchmark pair + 1 designer's own).

---

## 4. DESIGNER KICKOFF QUEUE — top 3 by impact-needing-polish

Ranked by `(operator-visibility × distance-from-canon)`. Each carries an inbox-style brief.

### Slot 1 — Sinister Panel Liquid Glass parity pass  **[P0]**
- **Surface:** `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/`
- **Why now:** Operator's mission-control panel = highest daily-use Sanctum surface. ~20+ routes built without enforcing THEME-DOCTRINE. Tier-1 lane authority must audit BEFORE the panel grows further.
- **Brief:** Run `Designer.audit_surface()` against every `app/*/page.tsx`. For each violation log path + commandment#. EXPAND skeleton with any missing primitive (e.g. mind-graph card variants), THEN port panel routes to consume `.lg-card` / `<KpiCard>` / `<TabHeader>` / `<StatCard>` / `<Chart>`. Replace any `lucide-react` import. Add `<PageShell signature="page-sig-{route}">` wrappers. Land `## Production parity TODO` blocks.
- **Exit criteria:** `npm run gates` (after copying script suite into panel) passes with `--strict`; pill-regression counter = 0; emoji count = 0; banned-phrase hits = 0.

### Slot 2 — EVE.exe TUI uniformity sweep  **[P0]**
- **Surface:** `automations/eve-launcher/eve.py` + every sub-page
- **Why now:** Operator hard-canonical 2026-05-24: *"allow infinite accounts and all pages on the eve exe need to have a uniform ui look ... we dont do shit half ass"*. EVE.exe is the operator's single entry point. Plus accounts panel + Health view + round-robin must scale infinitely (no 4-slot cap).
- **Brief:** Enumerate every sub-page (account picker, swarm/loop mode, project list, status, diagnose, account-status, …). Verify header line `{DARKP}---{RESET} {WHITE}{BOLD}<title>{RESET} {DARKP}---{RESET}`. Verify footer `B) Back  H) Home  X) Exit  (page-specific keys)`. Verify B/empty-Enter → main picker; X → `sys.exit(0)`. Refactor any drift into a shared `eve_picker_lib` helper.
- **Exit criteria:** `automations\verify-eve-features.ps1 -AutoRebuild -SyncMirror` passes; every sub-page uses canonical header/footer; account list scales to N without 4-slot assumptions.

### Slot 3 — Sanctum Quantum dashboard Liquid Glass upgrade  **[P1]**
- **Surface:** `projects/sinister-snap-api-quantum/outputs/sanctum-quantum-dashboard.html`
- **Why now:** Already uses Sanctum purple `#c084fc` correctly. One concentrated session converts it from "single-file HTML with custom CSS" to "single-file HTML with Liquid Glass material applied". Big quality win for low effort.
- **Brief:** Refactor the inline `:root` block to include the canonical `--surface-*` + `.lg-*` recipes (this surface must stay self-contained HTML — copy, don't `@import`). Wrap each metric strip in `.lg-card-hero`; wrap each panel in `.lg-card`; wrap pill filters in `.lg-pill` / `.lg-pill-active`; replace any custom border-radius with canonical 16px/18px. Add a vanilla-JS `NumberTicker` polyfill for KPIs.
- **Exit criteria:** Self-contained HTML still opens with no network deps; visual diff against the dashboard skeleton shows Liquid Glass material present; KPI digits animate from 0 on first paint.

---

## 5. STANDING REFERENCES (read first, every session)

- `projects/sinister-dashboard-skeleton/dashboard-skeleton/THEME-DOCTRINE.md` — the law
- `projects/sinister-dashboard-skeleton/dashboard-skeleton/PATTERNS.md` — when adding a new primitive, update this
- `projects/sinister-dashboard-skeleton/dashboard-skeleton/AGENTS.md` — what the skeleton tells consuming agents
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` — EXPAND, never fork
- `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md` — uniform EVE.exe sub-pages + infinite accounts
- `_shared-memory/knowledge/skills-inventory-and-routing-doctrine-2026-05-25.md` — `python automations/skills_router.py --recommend "<task>"` before hand-writing CSS
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` — `npm run gates` before any "shipped" claim

## 6. RUN-OF-SHOW (each Designer iteration)

1. Read this BRAND-BRIEF top-to-bottom (5 min).
2. Pick top item from `DESIGNER KICKOFF QUEUE` (or whatever's freshest in `_shared-memory/inbox/sinister-designer/`).
3. Run `python automations/skills_router.py --recommend "<task verb>"` — route through returned skill chain (`ui-ux-pro-max` → `design-system` → `ui-styling` → `frontend-design`).
4. EXPAND skeleton FIRST if a primitive is missing → commit there → `PATTERNS.md` row added.
5. Land the change on the target surface using the new primitive.
6. Run the surface's `npm run gates` (or `verify-eve-features.ps1` for EVE.exe).
7. PROGRESS append at `_shared-memory/PROGRESS/Sinister Designer.md` (most-recent at top).
8. Loop (per `loop=relentless` default).
