# PATTERNS.md Mobile Gap Audit — Sinister OS Mobile

> Author: RKOJ-ELENO :: 2026-05-24
> Audit scope: `projects/sinister-dashboard-skeleton/dashboard-skeleton/PATTERNS.md` + `components/{ui,primitives,shared,layout}/`
> Triggered by: branding-spec-2026-05-24 § 4 (EXPAND principle applied to mobile)
> Composes with: `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base + EXPAND)

## § 1 What this doc is

Per the Sanctum hard-canonical 2026-05-24 EXPAND principle: when a lane needs a primitive the skeleton lacks, the new primitive lands in the skeleton FIRST, gets a `PATTERNS.md` row SECOND, then is consumed. This audit identifies every primitive the mobile Compose theme bridge (P4 deliverable) will need, classifies each as HAVE / PARTIAL / MISSING, and for MISSING items specifies the EXPAND PR shape (where to add it in the skeleton + what tokens it needs + the Compose mapping).

## § 2 Skeleton inventory (ground-truth as of 2026-05-24)

### § 2.1 PATTERNS.md (16 documented recipes)

| # | Pattern | Pattern file |
|---|---|---|
| 1 | Buttons (lg-button / lg-pill / lg-pill-active / icon-only) | `ui/button.tsx` |
| 2 | Badges (StatusBadge + manual) | `shared/status-badge.tsx` |
| 3 | Channel pills (iM / WA / TG) | inline in PATTERNS.md |
| 4 | KPI / stat cards | `shared/stat-card.tsx`, `primitives/kpi-card.tsx` |
| 5 | Sub-tab headers | `primitives/tab-header.tsx` |
| 6 | Range / period selectors (Select) | `ui/select.tsx` |
| 7 | Search input | inline in PATTERNS.md (uses `ui/input.tsx`) |
| 8 | Advanced filter panel | `primitives/advanced-filter.tsx` |
| 9 | Variable / template chips | inline |
| 10 | Captions / hint text tier ladder | (CSS classes only) |
| 11 | Sidebar nav items | `layout/dashboard-sidebar.tsx` |
| 12 | Avatar fallback | `ui/avatar.tsx` |
| 13 | Empty / loading / error states | `shared/{empty-state,loading-state,query-error}.tsx` |
| 14 | Dialog / modal headers | `primitives/glass-dialog-header.tsx` |
| 15 | Money rendering | `shared/money.tsx` |
| 16 | Record-rail surface (rail+pane) | `layout/dashboard-layout.tsx` |

### § 2.2 `components/ui/` (23 Radix-backed primitives)

`alert-dialog · avatar · badge · button · card · checkbox · dialog · dropdown-menu · input · label · popover · scroll-area · select · separator · sheet · skeleton · sonner · switch · table · tabs · textarea · toast · tooltip`

### § 2.3 `components/primitives/` (17 surface-level primitives)

`advanced-filter · aurora-bg · calendar · chart · empty-state · error-state · filter-pill-row · geo-heat · glass-dialog-header · glow · index · kpi-card · loading-state · number-ticker · page-shell · section-header · tab-header`

### § 2.4 `components/shared/` (9 cross-feature shared)

`empty-state · folder-manager-dialog · loading-state · money · page-section · query-error · skeleton-variants · stat-card · status-badge`

### § 2.5 `components/layout/` (2 layout shells)

`dashboard-layout · dashboard-sidebar`

## § 3 Mobile-needs ↔ skeleton-inventory verdict table

For each Android surface from branding-spec § 3, classify the primitives required.

### Verdict legend

- **HAVE** — primitive exists in skeleton, maps cleanly to Compose. No EXPAND PR.
- **PARTIAL** — primitive bone exists but lacks the mobile-optimized recipe / wrapper / pattern doc. EXPAND PR adds wrapper + PATTERNS.md row.
- **MISSING** — no primitive in skeleton. EXPAND PR adds new component + new PATTERNS.md section + tokens (if any).

### § 3.1 SystemUI surfaces (lock screen, status bar, quick settings, nav bar)

| Surface need | Verdict | Skeleton match | EXPAND PR shape |
|---|---|---|---|
| Lock-screen notification chip (swipe-dismissable, actionable) | **PARTIAL** | `.lg-card` recipe exists for static cards | Add `components/primitives/notification-chip.tsx` — `lg-card` base + swipe-to-dismiss gesture + 0-3 action chips. New PATTERNS.md § 17 "Mobile notification chip". Tokens: `--swipe-threshold: 80px`, `--chip-action-width: 72px` |
| Quick-settings tile (icon + label + active state + long-press) | **PARTIAL** | `.lg-pill` / `.lg-pill-active` exists for inline pills | Add `components/primitives/qs-tile.tsx` — square 1:1 ratio, 64-72dp icon area, label below, long-press detector slot. New PATTERNS.md § 18 "Mobile quick-settings tile". Tokens: `--qs-tile-size: 84px` |
| Volume / brightness slider | **MISSING** | NO slider primitive in `ui/` (only `switch.tsx` for binary) | Add `components/ui/slider.tsx` — Radix Slider with `.lg-slider` recipe: track `bg-surface-2/60`, fill `bg-accent`, thumb `lg-card` glow on grab. New PATTERNS.md § 19 "Slider". Tokens: `--slider-track-h: 4px`, `--slider-thumb-size: 20px`, `--slider-glow: 0 0 8px 0 color-mix(in oklab, var(--accent) 50%, transparent)` |
| Status bar icon set | **HAVE** | `components/icons/` sprite system covers it | Mobile maps each glyph to `IconCompat` resource. No EXPAND. |
| Nav-bar gesture pill (EVE-busy purple state) | **PARTIAL** | No specific primitive; needs a thin animated bar | Add `components/primitives/gesture-bar.tsx` — fixed-bottom 4dp pill, white default, accent-tinted + soft glow when `busy` prop true. New PATTERNS.md § 20 "Gesture nav bar". |
| Lock glyph (animated lock/unlock) | **MISSING** | No animated glyph primitive | Add `components/icons/animated/lock.tsx` — SVG with state-driven stroke-dasharray transition (300ms `--motion-med`). New PATTERNS.md § 21 "Animated state glyphs". |
| Clock display (large face) | **MISSING** | No clock primitive | Add `components/primitives/clock-face.tsx` — tabular-nums, `text-5xl`/`text-6xl` variants, font slot. New PATTERNS.md § 22 "Clock display". |

### § 3.2 Launcher surfaces

| Surface need | Verdict | Skeleton match | EXPAND PR shape |
|---|---|---|---|
| App icon (adaptive, with optional badge) | **PARTIAL** | `ui/avatar.tsx` covers circular + rounded; no badge slot | Extend `ui/avatar.tsx` with optional `badge?: { count: number; tone: 'accent' \| 'danger' }` slot. PATTERNS.md § 12 (existing Avatar row) gets a badge sub-recipe. |
| App grid (drawer layout) | **MISSING** | No grid layout primitive (record-rail is rail+pane, not grid) | Add `components/primitives/app-grid.tsx` — CSS grid `grid-cols-4 sm:grid-cols-5 md:grid-cols-6` with `gap-3 p-4`, optional alphabetical section headers. New PATTERNS.md § 23 "App / item grid". |
| Search bar (mobile-optimized full-width) | **PARTIAL** | PATTERNS.md § 7 covers desktop search input | Add mobile variant to PATTERNS.md § 7: full-width, larger touch target (`h-12` not `h-9`), cancel button on focus, voice icon slot. No new component file — pattern doc only. |
| Widget shell (Glance-compatible) | **MISSING** | No widget primitive | Add `components/primitives/widget-shell.tsx` — fixed-aspect-ratio container (`aspect-square` / `aspect-[2/1]` / `aspect-[4/2]` for 1x1 / 2x1 / 4x2), inherits `.lg-card`, has `<WidgetSlot>` for body. New PATTERNS.md § 24 "Glance widget shell". |

### § 3.3 Modal / sheet surfaces (P4 first-party apps)

| Surface need | Verdict | Skeleton match | EXPAND PR shape |
|---|---|---|---|
| Full-screen modal | **HAVE** | `ui/dialog.tsx` + `primitives/glass-dialog-header.tsx` | Compose maps to `Dialog(properties = DialogProperties(usePlatformDefaultWidth = false))`. No EXPAND. |
| Side sheet (drawer navigation) | **HAVE** | `ui/sheet.tsx` supports `side="left" \| "right"` | Compose maps to `ModalDrawer`. No EXPAND. |
| **Bottom sheet** (the mobile primary modal) | **PARTIAL** | `ui/sheet.tsx` supports `side="bottom"` but lacks the mobile recipe | Add `components/primitives/bottom-sheet.tsx` — wraps `<Sheet side="bottom">`, adds drag-handle indicator (`.lg-pill` 36×4 px top-center), snap points (peek 30% / half 50% / full 90% via CSS custom prop), drag-to-dismiss gesture hint. New PATTERNS.md § 25 "Mobile bottom sheet". |
| Alert dialog | **HAVE** | `ui/alert-dialog.tsx` | Compose `AlertDialog`. No EXPAND. |
| Snackbar / toast | **HAVE** | `ui/sonner.tsx` + `ui/toast.tsx` | Compose `SnackbarHost`. No EXPAND. |

### § 3.4 Lists / navigation (Settings, in-app)

| Surface need | Verdict | Skeleton match | EXPAND PR shape |
|---|---|---|---|
| Settings list row (icon + label + value + chevron) | **MISSING** | Record-rail row is for record-browsing (rail+pane), not settings | Add `components/primitives/list-row.tsx` — three-slot row (leading icon · label+caption · trailing value/chevron/switch). Variants: `default` / `with-switch` / `with-value` / `destructive`. New PATTERNS.md § 26 "Settings list row". |
| Section header (grouped list) | **HAVE** | `primitives/section-header.tsx` exists | Compose maps to a styled `Text`. No EXPAND. |
| Bottom tab bar (mobile primary nav, replaces sidebar) | **MISSING** | `layout/dashboard-sidebar.tsx` is desktop-only | Add `components/primitives/tab-bar.tsx` — fixed-bottom 3-5 tab pill, each tab is icon-above-label, active tab gets accent glow + label color shift. Mirrors sidebar item recipe (PATTERNS.md § 11) but horizontal. New PATTERNS.md § 27 "Mobile bottom tab bar". |
| Top app bar (back arrow + title + actions) | **PARTIAL** | `primitives/tab-header.tsx` is closest but designed for sub-tabs not page chrome | Add `components/primitives/app-bar.tsx` — leading slot (back button or menu icon) · title (`text-base font-semibold text-white`) · trailing actions slot. Inherits `.lg-card` floor. New PATTERNS.md § 28 "Mobile app bar (top)". |
| Navigation rail (portrait tablet variant) | **MISSING** | Sidebar is full-width; no compact rail | Add `components/primitives/nav-rail.tsx` — 72dp wide, icon-only nav items with tooltip-on-hover. Tablet-portrait substitute for sidebar. New PATTERNS.md § 29 "Navigation rail (compact)". |

### § 3.5 Gesture / interaction primitives

| Surface need | Verdict | Skeleton match | EXPAND PR shape |
|---|---|---|---|
| Swipe-action row (swipe-left/right reveals actions) | **MISSING** | No gesture primitive | Add `components/primitives/swipe-action.tsx` — wraps any row child, takes `leadingActions` + `trailingActions` arrays, each action = `{ icon, label, tone, onPress }`. Tone drives background color (accent/success/warning/danger). New PATTERNS.md § 30 "Swipe-action row". |
| Pull-to-refresh indicator | **MISSING** | No PTR primitive | Add `components/primitives/pull-to-refresh.tsx` — wraps a scroll surface, shows accent-tinted spinner glyph as user pulls past `--ptr-threshold: 80px`. New PATTERNS.md § 31 "Pull to refresh". |
| Segmented control (iOS-style 2-3 way switch) | **MISSING** | PATTERNS.md § 6 says "use Select if 4+ pills"; segmented is 2-3 | Add `components/primitives/segmented-control.tsx` — pill-shaped container of 2-3 options, active option gets `.lg-pill-active` styling, animates slider between options over `--motion-fast`. New PATTERNS.md § 32 "Segmented control (2-3 options)". |
| FAB (Floating Action Button) | **MISSING** | No FAB primitive (web pattern is sidebar CTA) | Add `components/primitives/fab.tsx` — fixed-bottom-right 56dp circle, `.lg-button` recipe + accent-tinted glow, single icon slot. Variants: `regular` / `extended` (with label). New PATTERNS.md § 33 "Floating action button". |
| Long-press detector | **HAVE** (implicit) | Native to Compose via `combinedClickable(onLongClick)` | No primitive needed; document the Compose pattern in P4 bridge README. |

### § 3.6 OS-only surfaces (out-of-scope for skeleton EXPAND)

| Surface | Why out-of-scope | Handling |
|---|---|---|
| Boot animation | Pure PNG sequence + `desc.txt`; not a Compose surface | Asset pipeline in `source/bootanimation/` only |
| Bootloader unlock screen | Fastboot-rendered, no UI framework | `bootable/recovery/res-*/` images + strings |
| Fastboot chrome | Same | Same |
| Recovery (TWRP theme) | TWRP custom theme JSON, not Compose | `source/recovery-theme/` only |
| AVB unlock warning | Stock Android image swap | `frameworks/base/core/res/res/drawable/` |

## § 4 EXPAND PR rollout plan

### § 4.1 Tier 1 — Mobile-essential primitives (skeleton needs these BEFORE P4 theme bridge starts)

Order by surface-readiness criticality. Each PR is one commit to `projects/sinister-dashboard-skeleton/` master.

| # | Component | PATTERNS.md § | Estimated complexity | Blocks |
|---|---|---|---|---|
| 1 | `bottom-sheet.tsx` | new § 25 | low (wraps Sheet) | Sinister Panel mobile routes |
| 2 | `tab-bar.tsx` | new § 27 | low | Sinister Panel mobile chrome |
| 3 | `app-bar.tsx` | new § 28 | low | every first-party app top chrome |
| 4 | `ui/slider.tsx` | new § 19 | low (Radix Slider) | SystemUI volume/brightness, Vault sync-throttle |
| 5 | `list-row.tsx` | new § 26 | low | Settings, Vault peer list, Inbox |
| 6 | `segmented-control.tsx` | new § 32 | medium (animation) | Inbox filter (All/Unread/Mentions), Panel period toggle |
| 7 | `fab.tsx` | new § 33 | low | Panel new-message, Inbox compose |
| 8 | `swipe-action.tsx` | new § 30 | medium (gesture) | Notification chips, Inbox archive/delete |

**Total Tier 1: 8 PRs.** Operator-gate: each lands on skeleton's main, this lane consumes via Compose theme bridge.

### § 4.2 Tier 2 — Surface-specific (needed for SystemUI / launcher work)

| # | Component | PATTERNS.md § | Estimated complexity |
|---|---|---|---|
| 9 | `notification-chip.tsx` | new § 17 | medium (swipe + actions) |
| 10 | `qs-tile.tsx` | new § 18 | low |
| 11 | `gesture-bar.tsx` | new § 20 | low |
| 12 | `clock-face.tsx` | new § 22 | low |
| 13 | `app-grid.tsx` | new § 23 | low |
| 14 | `widget-shell.tsx` | new § 24 | medium (aspect ratios) |
| 15 | `pull-to-refresh.tsx` | new § 31 | medium |
| 16 | `nav-rail.tsx` | new § 29 | low |
| 17 | `icons/animated/lock.tsx` | new § 21 | low |

### § 4.3 Tier 3 — Augment existing

| # | Change | Where |
|---|---|---|
| 18 | Avatar badge slot | `ui/avatar.tsx` + PATTERNS.md § 12 update |
| 19 | Mobile search bar variant (touch-target sizing) | PATTERNS.md § 7 sub-recipe (no new file) |

**Total EXPAND PRs to skeleton: 19** (17 new files + 2 in-place additions). All Tier 1 lands BEFORE P4 starts. Tier 2-3 land during P4 as surface work begins.

## § 5 Cross-check against branding-spec § 4

Branding-spec § 4 originally called out 5 mobile primitives by name. This audit's coverage:

| Branding-spec call-out | Audit verdict | EXPAND PR # |
|---|---|---|
| `<BottomSheet>` | PARTIAL → wrapper | #1 |
| mobile `<TabBar>` | MISSING → new | #2 |
| `<SegmentedControl>` | MISSING → new | #6 |
| `<SwipeAction>` | MISSING → new | #8 |
| `<Sheet>` modal | HAVE (use Sheet directly) | n/a |

Plus 14 additional primitives this audit surfaced beyond the branding-spec's initial enumeration. The branding-spec § 4 paragraph should be updated to point at this audit for the full inventory (see § 7 below).

## § 6 Tokens that need to ship with the EXPAND PRs

New CSS custom properties to add to `dashboard-skeleton/tokens/globals.css` (or a new `mobile.css` partial):

```css
:root {
  /* Mobile-specific sizing */
  --tab-bar-h: 64px;
  --app-bar-h: 56px;
  --qs-tile-size: 84px;
  --fab-size: 56px;
  --fab-extended-h: 48px;
  --nav-rail-w: 72px;

  /* Sliders + gestures */
  --slider-track-h: 4px;
  --slider-thumb-size: 20px;
  --slider-glow: 0 0 8px 0 color-mix(in oklab, var(--accent) 50%, transparent);
  --swipe-threshold: 80px;
  --chip-action-width: 72px;
  --ptr-threshold: 80px;

  /* Widgets */
  --widget-1x1-min: 110px;
  --widget-2x1-min: 240px;
  --widget-4x2-min: 480px;
  --widget-radius: 24px;
}
```

These are sizing-only; colors continue to come from the existing skeleton ramp + this lane's purple override.

## § 7 Documentation deltas this audit triggers

1. **PATTERNS.md** — add § 17-§ 33 (17 new sections, see § 4 above for spec)
2. **branding-spec-2026-05-24.md § 4** (this lane) — replace "likely candidates" enumeration with pointer at this audit doc + Tier 1/2/3 PR list
3. **dashboard-skeleton CHANGELOG.md** — one row per EXPAND PR landed
4. **CLAUDE.md (Sanctum master)** — no change needed; EXPAND principle is already binding
5. **Brain `_INDEX.md`** — add row for this audit doc when committed

## § 8 No-bullshit verbs at gate

- This audit is **scaffolded** (file exists, parse-clean, inventory-cited from grep, mappings reasoned out).
- It is **NOT acceptance-tested** — no PR has been opened to the skeleton; no primitive has been built.
- Next claim-step is **scaffolded → in-flight** when the first EXPAND PR (#1 `bottom-sheet.tsx`) gets drafted on a skeleton branch.

## § 9 Composes with

- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (the EXPAND principle this audit implements)
- `branding-spec-2026-05-24` (this lane; § 4 mobile-primitives section)
- `sinister-os-mobile-doctrine-2026-05-24`
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate)
