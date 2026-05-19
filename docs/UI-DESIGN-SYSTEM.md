# UI Design System — Sinister Sanctum

> **Authority:** binding. When this note conflicts with any other UI guidance inside Sanctum, this note wins. Defers upstream to the source-of-truth `THEME-DOCTRINE.md` inside `dashboard-skeleton/`.

---

## Operator directive (verbatim, 2026-05-19)

> use `C:\Users\Zonia\Desktop\dashboard-skeleton\` ONLY for all new UIs. Update all md files about this. Make sure we do it moving forward.

Master lane interpretation: **every new UI surface in the Sinister LLC universe consumes the `dashboard-skeleton` token set, primitives, and Liquid Glass classes verbatim.** No bespoke material recipes. No parallel design systems. Skeleton is the canonical source; Sanctum-consuming repos copy or import — they do not fork.

---

## Canonical UI source

| Layer | Path | Role |
|---|---|---|
| Canonical real folder | `C:\Users\Zonia\Desktop\dashboard-skeleton\` | The single source of truth for tokens, primitives, Liquid Glass classes, motion vars, doctrine, audit scripts, page-signature CSS. Operator owns updates. |
| Intended junction (read-only from Sanctum) | `D:\Sinister Sanctum\skills\dashboard-skeleton\` | Virtual mount so Sanctum agents can reach the skeleton without a Desktop path leak. Created with `cmd /c mklink /J "D:\Sinister Sanctum\skills\dashboard-skeleton" "C:\Users\Zonia\Desktop\dashboard-skeleton"`. |
| Authority doc inside skeleton | `C:\Users\Zonia\Desktop\dashboard-skeleton\THEME-DOCTRINE.md` | The 11 commandments + ramps + lg-class recipes + motion vars + page-signature catalog. This Sanctum note paraphrases it. Read upstream first when in doubt. |

Working in either path is equivalent. New UI work — whether panel-side, Sanctum-side, or in a product-repo — **starts by importing/copying from the skeleton path above**.

---

## Sanctum branding override

The dashboard-skeleton ships an iOS-blue accent because the panel side wears panel branding. **Sanctum's own surfaces (master console, EXE chrome, launchers, orchestration UIs) wear Sanctum branding on top of the skeleton material.**

**Sanctum logo (binding):**

- File: `C:\Users\Zonia\Desktop\INPO\Things\ART\Img.png`
- Subject: a purple crowned horned demon skull (the "Sinister Sanctum master/orchestration mark").
- Use everywhere Sanctum branding appears: console splash, EXE icon, launcher header art, master agent identity card, Sanctum-side dialog headers, bot-fleet activator chrome.
- Never substitute a stock skull. Never recolor it (the purple is part of the mark).

**Sanctum purple ramp (back-compat — Sanctum-specific accent):**

The original purple ramp is preserved as the Sanctum accent for surfaces that wear Sanctum branding. It is **never the default for new panel-side UIs**.

| Token | Hex | Use |
|---|---|---|
| `--sanctum-primary` | `#7A3DD4` | Sanctum primary accent — console CTAs, launcher chrome, master-agent identity |
| `--sanctum-soft` | `#A06EFF` | Hover lift, secondary Sanctum accent, ambient glow base |
| `--sanctum-deep` | `#4A1F8E` | Pressed states, deep ambient haze on Sanctum heroes |
| `--sanctum-card` | `#15151E` | Sanctum-side card surface (replaces `--surface-1` for Sanctum chrome) |
| `--sanctum-bg` | `#0E0E12` | Sanctum-side canvas (replaces `--surface-0` for Sanctum chrome) |

**Decision rule:**

| Surface | Accent | Logo |
|---|---|---|
| Panel-side (dashboard, inbox, agency, admin, compliance, audit, vault, fans, calls, analytics, templates, tracking-links, docs, smart-messenger) | **iOS blue `#0A84FF`** (binding) | none / panel mark |
| Sanctum-side (Sanctum Console, EXE, launchers, master orchestration UI, bot-fleet activator, agent identity) | **Sanctum purple `#7A3DD4`** | `Img.png` (purple crowned horned demon skull) |
| Product-repo UIs (Snap-EMU, TikTok-EMU, Kernel-APK that don't have their own brand) | **iOS blue** (default) — override only with operator sign-off | per-product, never Sanctum mark |

---

## The 11 commandments (paraphrased from skeleton)

Source: `C:\Users\Zonia\Desktop\dashboard-skeleton\THEME-DOCTRINE.md` §"The 11 Commandments". Read upstream for the binding wording.

1. **One palette, two extensions.** Background neutrals + iOS-blue accent ramp. Rainbow is forbidden. The only non-blue tokens permitted are `--danger`, `--warning`; `--success` and `--info` are aliases for `--accent`.
2. **One primitive per role.** `<Button>` always emits `rounded-full`. One `<Card>`, one `<Input>`, one `<Chart>`, one `<Icon>`, one `<TabHeader>`, one `<StatCard>`. New shapes fork the canonical primitive — never inline a class blob, never use raw `<button>`.
3. **No stock icons.** Every glyph is a hand-drawn SVG in `components/icons/sprite.svg`. `lucide-react` is forbidden in new code. The Eve glyph is a geometric crystal — never a sparkle, never a magic wand.
4. **No emojis in UI.** Runtime UI strings, JSX text, system prompts cannot use them. Emojis flow through `<Icon>`. Vault `.md` files and fan-message data files are exempt.
5. **No AI-slop copy.** Banned-phrase list is global — Eve drafts, UI copy, error toasts, empty states, every human-read string.
6. **Motion is a system, not a sprinkle.** Three durations: `--motion-fast 150ms`, `--motion-med 300ms`, `--motion-slow 600ms`. One easing curve: `cubic-bezier(0.22, 1, 0.36, 1)`. iOS 26 ease-out, not Material.
7. **Liquid Glass material.** Backdrop blur + saturate + ultra-thin border + inset white highlight + accent-tinted outer drop. Use `.lg-card` / `.lg-card-hero` / `.lg-rail` / `.lg-pill` / `.lg-pill-active` / `.lg-button` / `.lg-input` / `.lg-popover`. Never roll your own.
8. **Numbers are never static.** KPI tiles use `<NumberTicker>` on first paint. `<StatCard>` / `<KpiCard>` are the canonical containers — no bespoke big-number displays.
9. **Pages have a signature.** One detail per page that nobody else has. `<PageShell signature="...">` attaches the per-route `page-sig-*` class.
10. **Every primitive ships `EmptyState` + `LoadingState` + `ErrorState`.** No raw spinners. No "Loading…" text. Empty states have a hand-drawn SVG, a headline, and one CTA.
11. **Production parity is mandatory.** Every skeleton change gets a `## Production parity TODO` in its vault note listing the prod files to mirror later.

**Most important for Sanctum agents:** rounded-full buttons always, `.lg-card` material everywhere, no purple as default for new panel UIs, no `lucide-react`, geometric crystal Eve glyph not sparkle.

---

## Token tables

### iOS Blue ramp (binding for panel-side accent)

| Step | Hex | Role |
|---|---|---|
| 50 | `#E5F2FF` | Highest-contrast text on dark, rare |
| 100 | `#CCE5FF` | Inline link text |
| 200 | `#99CCFF` | Selected pill text |
| 300 | `#66B2FF` | Hover affordance text |
| 400 | `#3399FF` | Secondary accent — borders, focus rings |
| **500** | **`#007AFF`** | **iOS light-mode system blue** (reference) |
| **600** | **`#0A84FF`** | **iOS dark-mode system blue — PRIMARY accent** |
| 700 | `#0060CC` | Hover/pressed state for primary |
| 800 | `#004899` | Strong accent backgrounds |
| 900 | `#003066` | Deep accent — glow shadow base |
| 950 | `#001833` | Ambient blue haze on heroes |

**Aliases:**
- `--accent` = `--blue-600` = `#0A84FF`
- `--accent-hover` = `--blue-500` = `#007AFF`
- `--accent-pressed` = `--blue-700` = `#0060CC`
- `--accent-soft` = `color-mix(in oklab, var(--blue-600) 15%, transparent)`
- `--accent-ring` = `color-mix(in oklab, var(--blue-400) 60%, transparent)`

### Surface neutrals

| Token | Hex | Use |
|---|---|---|
| `--surface-0` | `#0A0A0F` | Page canvas — deepest background |
| `--surface-1` | `#13131A` | Card background — default panel base (lg-* recipes start here) |
| `--surface-2` | `#1C1C24` | Elevated card, hover state, popover base, inactive pill |
| `--surface-3` | `#2A2A33` | Border, separator, input chrome |

### Text levels

| Token | Hex | Use |
|---|---|---|
| `--text-primary` | `#FFFFFF` | Headings, primary body, KPI digits |
| `--text-secondary` | `#A1A1AA` | Helper text, table sub-cells |
| `--text-tertiary` | `#71717A` | Captions, axis labels, timestamps |
| `--text-disabled` | `#52525B` | Disabled inputs, placeholder |

### Semantic survivors

| Token | Value | Use ONLY for |
|---|---|---|
| `--danger` | `#E5484D` | P0 compliance flag, destructive confirm, error state |
| `--warning` | `#F5A524` | P1/P2 flag, soft policy hit |
| `--success` | `var(--accent)` | "Saved" / "completed" / "active" / "sent" (operator: remove all the green) |
| `--info` | `var(--accent)` | Default informational |

### Sanctum purple ramp (back-compat — Sanctum surfaces only)

| Token | Hex | Use |
|---|---|---|
| `--sanctum-primary` | `#7A3DD4` | Sanctum primary accent |
| `--sanctum-soft` | `#A06EFF` | Sanctum hover / secondary accent |
| `--sanctum-deep` | `#4A1F8E` | Sanctum pressed / deep ambient |
| `--sanctum-card` | `#15151E` | Sanctum card surface |
| `--sanctum-bg` | `#0E0E12` | Sanctum canvas |

The skeleton still exports `--purple-50` through `--purple-950` and `bg-purple-*` Tailwind classes for back-compat with old assets and page-signature CSS that references them directly. **New panel-side code uses `bg-accent` or `bg-blue-*`.** New Sanctum-side code uses `bg-sanctum-primary` / `--sanctum-*` tokens above.

---

## Liquid Glass catalog

All chrome surfaces use one of these recipes. Defined in `dashboard-skeleton/tokens/globals.css`. Never roll your own.

| Class | Material rule | Use |
|---|---|---|
| `.lg-card` | 70% surface-1 + 28px blur + 180% saturate + inset white highlight + accent-tinted drop shadow + 16px radius | Default panel — every standalone card |
| `.lg-card-hero` | 72% surface-1 + 32px blur + 190% saturate + bigger inset highlight + 18px radius + slow ambient `lg-hero-breathe` (10s) | Hero panel — top-of-page metric strip, primary modules |
| `.lg-rail` | 72% surface-1 + 28px blur + less inner highlight | Sidebar, right rail |
| `.lg-popover` | 96% surface-1 + 36px blur (more opaque because floating over arbitrary content) | DropdownMenuContent, PopoverContent, SelectContent |
| `.lg-pill` | 70% surface-2 + 16px blur + `border-radius: 999px` | Inactive filter chip, inactive tab pill |
| `.lg-pill-active` | accent bloom on top of `.lg-pill` + accent border + small directional outer drop + white label | Active filter chip, active tab pill |
| `.lg-button` | 80% surface-1 + 18px blur + accent border + larger accent bloom + accent-tinted drop + white label + press-scale | Primary CTA — the "lit-from-beneath" feel |
| `.lg-input` | 75% surface-1 + 12px blur + 6% white border (accent border on focus) | Input / textarea — shadcn `<Input>` and `<Textarea>` already apply this |

`.lg-card-hero` carries the one ambient repeating animation (`lg-hero-breathe`, 10s). All recipes honor `prefers-reduced-motion: reduce`.

---

## Motion

```css
--motion-fast:   150ms;   /* chip toggle, focus ring, hover lift */
--motion-med:    300ms;   /* page fade, modal open, tab swap */
--motion-slow:   600ms;   /* number ticker, hero KPI reveal */
--motion-ease:   cubic-bezier(0.22, 1, 0.36, 1);  /* iOS 26 ease-out */
```

**Hard rules:**
- No animation longer than `--motion-slow` (600ms). Two named exceptions: `.lg-card-hero` breathe (10s, imperceptible) and compliance `breathing-pulse` (2.4s, intentional until human-acked). Both honor `prefers-reduced-motion`.
- Springs use `framer-motion` `{ type: "spring", stiffness: 380, damping: 30 }`.
- iOS 26 + Liquid Glass vibe. Not Material Design. No translate-Y-jumping cards.
- Page mount = fade in + 8px lift → 0 over `--motion-med` (via `<PageShell>`).

---

## Component primitives (16 doctrine + shadcn ui + shared + icons)

**Doctrine primitives — `dashboard-skeleton/components/primitives/`:**

| Primitive | File | Purpose |
|---|---|---|
| `TabHeader` | `tab-header.tsx` | Canonical sub-tab header — accent tile + title + count + right-slot |
| `KpiCard` | `kpi-card.tsx` | KPI tile with `<NumberTicker>` — bare white digits + blue corner glyph + accent rule |
| `Chart` | `chart.tsx` | Single `recharts` wrapper — `line | area | bar | donut | spark` |
| `PageShell` | `page-shell.tsx` | Standard layout — page-fade + `page-sig-*` signature slot |
| `GeoHeat` | `geo-heat.tsx` | Multi-layer world heatmap on iOS-blue ramp |
| `AdvancedFilter` | `advanced-filter.tsx` | Schema-driven filter panel (pill / hours-window / days-window / money-range) |
| `FilterPillRow` | `filter-pill-row.tsx` | Gear + pill cluster on `.lg-pill` / `.lg-pill-active` |
| `NumberTicker` | `number-ticker.tsx` | 0 → value over `--motion-slow` on first paint |
| `EmptyState` | `empty-state.tsx` | Hand-drawn SVG + headline + one CTA |
| `LoadingState` | `loading-state.tsx` | Skeleton replacement for raw spinners |
| `ErrorState` | `error-state.tsx` | Error display with retry affordance |
| `SectionHeader` | `section-header.tsx` | In-page section header with accent rule |
| `Glow` | `glow.tsx` | Accent-tinted ambient glow wrapper |
| `AuroraBg` | `aurora-bg.tsx` | Aurora background (fans memory card signature) |
| `Calendar` | `calendar.tsx` | Date picker / scheduled-call grid |
| `GlassDialogHeader` | `glass-dialog-header.tsx` | Centered title + divider bar (auto-applied by `DialogHeader`) |

**shadcn locked primitives — `dashboard-skeleton/components/ui/`:**
- `Button` — variants: `default | glow | destructive | outline | secondary | ghost | link | subtle | bare`. Every shipping variant emits `rounded-full`.
- `Card` — `tone="default|hero|kpi"`.
- `Badge` — locked to accent + four semantic survivors.
- `Input`, `Textarea` — inherit `.lg-input`.
- `Select`, `DropdownMenu`, `Popover` — content uses `.lg-popover`.
- `Dialog` — content uses `.lg-card-hero`, header centered with divider bar.
- `Tooltip` — lightweight CSS-hover replacement (Radix Slot ref-loop on React 19).
- `Avatar`, `Switch`, `Label`, `Checkbox`, `Separator`, `Skeleton`, `ScrollArea`.

**Shared primitives — `dashboard-skeleton/components/shared/`:**
- `StatCard` — non-animated KPI sibling of `<KpiCard>`. Bare white digits + blue corner glyph + accent rule.
- `Money` — blue `$` (`text-accent`) + white digits (`font-mono tabular-nums`).
- `EmptyState`, `LoadingState`, `QueryError`, `SkeletonVariants`, `PageSection`, `StatusBadge`, `FolderManagerDialog`.

**Icons — `dashboard-skeleton/components/icons/`:**
- `sprite.svg` — single artist-reference SVG sprite.
- `sprite-root.tsx` — runtime sprite (must stay in sync with `sprite.svg`).
- `icon.tsx` — `<Icon name="..." />` with TypeScript literal-union autocomplete.
- The Eve glyph (`i-eve`) is a geometric crystal — never sparkle, never magic wand.

**Eve primitive — `dashboard-skeleton/components/eve/`:**
- `EveObservationsCard` — read-only "Eve thinks…" card for inbox right rail.

---

## Type scale

**Font stack (SF-first):**

```css
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
             "Segoe UI", system-ui, sans-serif;
```

**Base size:** `15px` (panel-side default — slightly under web 16px to match iOS density).

**Canonical big-number recipe:**

```tsx
<span className="text-3xl font-bold tabular-nums text-white">
  {value}
</span>
```

Variations live inside `<KpiCard>` / `<StatCard>` / `<Money>` — do not roll your own big-number block.

---

## When to consume what

| Intent | Files to copy / import from skeleton |
|---|---|
| Building a KPI tile | `components/primitives/kpi-card.tsx` (animated) or `components/shared/stat-card.tsx` (non-animated) |
| Building a chart | `components/primitives/chart.tsx` (all chart types route through this) |
| Building a sub-tab header | `components/primitives/tab-header.tsx` |
| Wrapping a route | `components/primitives/page-shell.tsx` (attaches signature CSS) |
| Money display | `components/shared/money.tsx` |
| Empty / loading / error states | `components/primitives/{empty-state,loading-state,error-state}.tsx` |
| Filter UI | `components/primitives/{advanced-filter,filter-pill-row}.tsx` |
| World map / heatmap | `components/primitives/geo-heat.tsx` |
| Modal / dialog | `components/ui/dialog.tsx` + `components/primitives/glass-dialog-header.tsx` |
| Any glyph | `components/icons/icon.tsx` + add to `sprite.svg` if missing |
| Tokens (colors, motion, surfaces) | `tokens/globals.css` + `lib/theme.ts` |
| Tailwind config | `tailwind.config.ts` |
| ESLint enforcement | `enforcement/eslint.config.mjs` |
| Doctrine audit | `scripts/doctrine-audit.mjs` (run with `--strict` in CI) |

---

## Forbidden

- **Purple as the default for new panel UIs.** Purple is reserved for Sanctum-specific surfaces (Sanctum Console / launchers / EXE chrome / master agent identity). Panel-side defaults to iOS blue.
- **Custom material recipes outside `.lg-*`.** No bespoke `background-color: rgba(...)` + `backdrop-filter` blobs. Use the eight Liquid Glass classes.
- **`lucide-react`.** ESLint blocks new imports. Existing imports are tracked for removal.
- **Magic-wand / sparkle Eve icon.** The Eve glyph is a geometric crystal. The shape is operator-final.
- **Rainbow accent.** Pick from the iOS blue ramp (panel-side) or Sanctum purple ramp (Sanctum-side). No other accent colors.
- **Raw `<button>` / `<div className="rounded-xl border ...">`.** Use the canonical primitives.
- **Emojis in runtime UI.** Use `<Icon>` instead. Vault `.md` and fan-message data files are exempt.
- **AI-slop copy.** See the banned-phrase list in `dashboard-skeleton/THEME-DOCTRINE.md` §"Banned Phrases".

---

## Process for keeping in sync

1. **Canonical path is `C:\Users\Zonia\Desktop\dashboard-skeleton\`.** Operator owns updates to the skeleton — tokens, primitives, doctrine, audit scripts, page-signature CSS.
2. **Sanctum mounts a junction read-only** at `D:\Sinister Sanctum\skills\dashboard-skeleton\`. Create with:
   ```powershell
   cmd /c mklink /J "D:\Sinister Sanctum\skills\dashboard-skeleton" "C:\Users\Zonia\Desktop\dashboard-skeleton"
   ```
   Junction means edits in either path appear in both — but **Sanctum agents treat the mount as read-only.** Master never writes through this junction.
3. **Sanctum consumes** by copying / importing from the junction (or the Desktop canonical) into the consuming repo. Skeleton is the upstream; Sanctum is downstream.
4. **When the skeleton changes**, the operator updates `THEME-DOCTRINE.md` upstream. Master updates this Sanctum doc to mirror any new sections (token additions, new primitives, new commandments).
5. **Product repos** (Snap-EMU, TikTok-EMU, Panel, Kernel-APK) consume the skeleton the same way — by path on the operator's machine, by GitHub URL for Leo's machine. No vendoring.

---

## Related

- Upstream authority: `C:\Users\Zonia\Desktop\dashboard-skeleton\THEME-DOCTRINE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Panel integration: `docs/PANEL-INTEGRATION.md`
- Operator directives (master lane): `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md`
- Contributor rules: `CONTRIBUTING.md` §"UI design — canonical source"
- Repo overview: `SANCTUM.md` §"UI design lineage"
