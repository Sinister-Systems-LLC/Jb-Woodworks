# Sinister Branding Spec — Sinister OS Mobile (Pixel 6a)

> Author: RKOJ-ELENO :: 2026-05-24
> Originating operator utterance: 2026-05-24T16:09:10Z — *"take note this needs the sinister branding and look"*
> Composes with: `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base + EXPAND principle, Sanctum CLAUDE.md hard-canonical)

## § 1 Why this doc exists

The Sanctum master CLAUDE.md hard-canonical 2026-05-24 binds every UI surface in the fleet — including OS-level surfaces — to inherit from `projects/sinister-dashboard-skeleton/dashboard-skeleton/`. The operator reinforced specifically for this lane on 2026-05-24T16:09:10Z: the Pixel 6a OS must carry the Sinister branding and look, not vanilla Android styling.

This doc enumerates every surface in an Android OS that touches the user's eye, declares what the Sinister branding is on each, and pins the inheritance path back to the skeleton. **No surface gets a one-off** — if a primitive isn't in the skeleton yet, EXPAND there first then consume.

## § 2 The Sinister look — non-negotiables (inherited from skeleton)

| Spec | Value | Source of truth |
|---|---|---|
| **Accent** | Sinister purple `#c084fc` (Tailwind `purple-400`) | per Sanctum CLAUDE.md hard-canonical 2026-05-24 (the ONLY allowed divergence from the skeleton's iOS-blue reference) |
| **Material** | Liquid Glass — 28px blur, 180% saturate, ultra-thin borders, inset white highlight, accent-tinted drop shadow | `dashboard-skeleton/THEME-DOCTRINE.md` § Liquid Glass Surfaces (binding) |
| **Mode** | Dark mode only (no light-mode toggle in v1) | THEME-DOCTRINE.md § Commandment 1 (one palette) |
| **Iconography** | Hand-drawn SVG sprite. NO `lucide-react`, NO emojis in UI chrome | THEME-DOCTRINE.md § Commandment 3 + 4 |
| **Motion** | Three durations only — `--motion-fast 150ms` / `--motion-med 300ms` / `--motion-slow 600ms`. One easing curve `cubic-bezier(0.22, 1, 0.36, 1)` | THEME-DOCTRINE.md § Commandment 6 |
| **Buttons** | Always `rounded-full`. ONE button primitive, no inline class blobs | THEME-DOCTRINE.md § Commandment 2 |
| **Numbers** | Always animate 0→value over `--motion-slow` first paint via `<NumberTicker>` (Compose equivalent on mobile) | THEME-DOCTRINE.md § Commandment 8 |
| **Copy** | No AI-slop phrases. No "I plan to…" / "I'll also…" / banned-phrase list applies to system strings | THEME-DOCTRINE.md § Commandment 5 |
| **Glow** | Primary CTAs + hero tiles get accent-tinted glow: `0 0 40px 0 color-mix(in oklab, var(--accent) 35%, transparent)` | THEME-DOCTRINE.md § iOS Blue Ramp footnote (re-tinted for our purple) |

### § 2.1 Sinister purple ramp (lane override of skeleton's blue ramp)

| Step | Hex | Role |
|------|------|------|
| 50  | `#F5EBFE` | High-contrast text on deep dark surfaces |
| 100 | `#EBD5FD` | Inline link text |
| 200 | `#DDB7FB` | Selected pill text |
| 300 | `#CC97F9` | Hover affordance text |
| **400** | **`#C084FC`** | **PRIMARY accent — `--accent` lane override** |
| 500 | `#A855F7` | Hover/pressed for primary |
| 600 | `#9333EA` | Strong accent backgrounds |
| 700 | `#7E22CE` | Pressed deep |
| 800 | `#6B21A8` | Glow shadow base |
| 900 | `#581C87` | Ambient haze on hero surfaces |
| 950 | `#3B0764` | Deepest accent — boot animation midpoint |

Tokens land in `tokens/sinister-mobile-purple.ts` (Compose) and `tokens/sinister-mobile-purple.xml` (Android resources) when P4 starts. Same step-keys as skeleton's blue ramp — drop-in replacement.

## § 3 Per-surface branding map (every place the user sees pixels)

Android OS exposes ~14 chrome surfaces between cold boot and the home screen. Each must look Sinister; none may show vanilla AOSP styling.

### § 3.1 Pre-OS (bootloader)

| Surface | Vanilla AOSP behavior | Sinister behavior | Implementation hook |
|---|---|---|---|
| Bootloader unlock warning | Orange / yellow Android warning | Replaced with: black background, Sinister crystal glyph (geometric, per skeleton commandment 3), purple-400 accent text *"Sinister-locked bootloader. Authorized via custom AVB key."* | `bootloader/img/warning.img` rebuild — only possible when AVB unlocked path, then re-locked with our key (operator Q3) |
| Fastboot mode chrome | White text on black | Hand-drawn Sinister wordmark + purple accent device-state line | `fastboot/font` + custom strings in `bootable/recovery/res-*/strings.xml` |

### § 3.2 Boot animation

| Surface | Vanilla AOSP | Sinister | Hook |
|---|---|---|---|
| `bootanimation.zip` | Google "G" or stock LineageOS spinner | Sinister crystal logo drawing-in stroke-by-stroke against the purple-950 ambient haze, scaling out into purple-400 glow at boot-completed. Frame rate 60fps, ~3s loop, fades to home on `BOOT_COMPLETED` | `frameworks/base/cmds/bootanimation/` consumes `/system/media/bootanimation.zip` — pure PNG sequence + `desc.txt` |
| Optional shutdown animation | None (instant black) | Reverse boot — crystal contracts back into purple-950 then black | Vendor-specific extension; defer to P4 |

### § 3.3 Lock screen

| Element | Vanilla | Sinister | Hook |
|---|---|---|---|
| Wallpaper | User photo | Default Sinister wallpaper pack (3 wallpapers from `sinister-generator` outputs cache, brand-locked) | `WallpaperManager` defaults in `frameworks/base/core/res/res/drawable-nodpi/default_wallpaper.png` |
| Clock font | Roboto | Hand-paired font (TBD P4 — candidates: SF Pro Display fork, Inter v4, JetBrains Mono Display) — picked once and stays | `framework-res` font config |
| Lock icon | Material padlock | Hand-drawn Sinister crystal-with-pin glyph | `frameworks/base/packages/SystemUI/res/drawable/ic_lock.xml` |
| Notification chips | Material 3 rounded rects | `.lg-card` Liquid Glass recipe via SystemUI Compose theme bridge | SystemUI `NotificationShelf` Compose port |

### § 3.4 SystemUI (status bar, quick settings, nav bar)

| Element | Vanilla | Sinister | Hook |
|---|---|---|---|
| Status bar icons | Filled Material | Hand-drawn glyph set matching skeleton's icon sprite | `SystemUI/res/drawable/stat_sys_*.xml` |
| Quick settings tiles | Material 3 chips | `.lg-pill` recipe — Liquid Glass blur pill, purple-400 accent when active | `SystemUI/src/.../qs/QSTileView.kt` Compose port |
| Nav bar | Material gesture pill / 3-button | Same gesture pill BUT colored purple-400 when system-busy (EVE thinking) | `SystemUI/src/.../navigationbar/` |
| Volume / brightness sliders | Material | Skeleton's `<Slider>` primitive — purple track, glow on grab | SystemUI Compose port |

### § 3.5 Launcher (home screen + app drawer)

Approach: fork Trebuchet (Lineage's launcher) → strip Material → Compose-rewrite using skeleton primitives. Alternative: ship a Sinister-Launcher APK in `/system/priv-app/` set as default home via `RoleManager`.

| Element | Vanilla | Sinister | Hook |
|---|---|---|---|
| App icons | Adaptive icons via `IconCompat` | Adaptive icons with purple-400 accent layer for first-party Sinister apps; AOSP / third-party app icons monochromed to skeleton's icon style via `IconCompat.createWithMonochromeAdaptiveBitmap` | `Launcher3` icon pipeline |
| App drawer | Vertical grid | `.lg-rail`-style grid with backdrop blur showing wallpaper through | Custom Compose launcher |
| Search bar | Material chip | `.lg-input` recipe + skeleton's `<SearchBar>` primitive (EXPAND to skeleton if not yet there) | Launcher Compose port |
| Widgets | Material RemoteViews | Compose widgets via Glance API for Sinister Panel widget, vault status widget, EVE voice-state widget | Glance widget package `com.sinister.widgets` |

### § 3.6 Settings app

| Element | Vanilla | Sinister | Hook |
|---|---|---|---|
| List rows | Material `Preference` | Skeleton's `<ListRow>` primitive (EXPAND if not yet there) | `packages/apps/Settings` Compose port — big lift; consider deferring to P4.5 |
| Headers | Material toolbar | `.lg-card` hero header with purple glow | Settings activity Compose theme |
| Sub-screens | Material navigation | Skeleton's `<PageShell>` pattern with per-screen signature CSS class | Settings navigation port |

Pragmatic compromise: keep AOSP Settings list rows BUT swap the theme to Sinister tokens (dark + purple) via `framework-res/res/values-night/colors.xml`. Full Compose port is a P5.5 polish item.

### § 3.7 Recovery (TWRP / stock recovery)

| Element | Vanilla | Sinister | Hook |
|---|---|---|---|
| Recovery splash | LineageOS / TWRP teal | Sinister crystal + purple-400 | `bootable/recovery/res-*/images/icon_*.png` |
| Recovery menu | Material list | TWRP custom theme JSON — purple accent + Liquid Glass-inspired stripes (true blur impossible at recovery, fake with semi-transparent panels) | `bootable/recovery/gui/` |

### § 3.8 Sinister-first-party apps (P4 deliverables)

Every Sinister app inherits via Jetpack Compose theme bridge. Bridge maps skeleton tokens (CSS variables) → Compose `MaterialTheme`:

- `--accent` → `colorScheme.primary` (purple-400)
- `--accent-soft` → `colorScheme.primaryContainer`
- `--surface-1` → `colorScheme.surface`
- `.lg-card` → `Surface(modifier = Modifier.lgCard())` extension
- Motion tokens → `tween(durationMillis, easing)` defaults

Apps to ship Sinister-styled:

1. **Sinister Panel** (`com.sinister.panel`) — mobile companion view; routes per master-plan § 7.2
2. **Sinister Vault** (`com.sinister.vault`) — Syncthing fork with Sinister chrome over the WebUI
3. **Sinister EVE** (`com.sinister.eve`) — privileged system service + thin foreground UI (sticky notification + voice-state full-screen)
4. **Sinister Inbox** (`com.sinister.inbox`) — cross-agent message reader
5. **Sinister Mind** (`com.sinister.mind`) — brain entry browser

### § 3.9 Per-app glyph design

Each first-party app needs a custom icon (no Material defaults). Generated via `sinister-generator` with brand-lock helper. Conservative-balance cap from CLAUDE.md applies: 1 variant per app, evaluate, iterate only if brief unmet. Total ≤ 6 images per session.

Brief shape (passed to `nano_banana.generate`): *"Adaptive icon, 432x432 px, geometric crystal silhouette in Sinister purple `#c084fc` over deep black-purple `#3B0764` background, ultra-thin 1px white highlight on top edge, subtle accent-tinted outer glow, no text, no Material design language, hand-drawn vector aesthetic."*

## § 4 The EXPAND principle applied to mobile

This section's full per-primitive inventory + EXPAND PR rollout lives in **`patterns-md-mobile-gap-audit-2026-05-24.md`** (Turn 2 deliverable, sibling research doc). That audit enumerates 19 EXPAND PRs across 3 tiers: **Tier 1** (8 PRs, must-land-before-P4 Compose theme bridge) · **Tier 2** (9 surface-specific PRs that land during P4 cuttlefish work) · **Tier 3** (2 augments to existing primitives). Tier 1 was handed off to the `sinister-dashboard-skeleton` lane via `_shared-memory/inbox/sinister-dashboard-skeleton/2026-05-24T1645Z-...-tier1-expand-prs.json` (Turn 3).

The EXPAND principle order (hard rule, per Sanctum CLAUDE.md hard-canonical 2026-05-24 15:44Z) is:

1. **First commit** lands in `projects/sinister-dashboard-skeleton/dashboard-skeleton/components/` with the new primitive in CSS/HTML reference form
2. **Second commit** lands in `dashboard-skeleton/PATTERNS.md` documenting the new row + its token recipe
3. **Third commit** lands in this lane's `source/compose-theme-bridge/` mapping the new primitive to Compose
4. Then — and only then — this lane consumes it

NEVER write the primitive only in Compose. NEVER ship a one-off Compose component without the skeleton having authored it first. That's what produces the "different feel across projects" the operator is preventing.

### § 4.1 Tier 1 quick-reference (8 mobile-essential primitives blocking P4)

| # | Component | Audit-doc § 4.1 verdict |
|---|---|---|
| 1 | `bottom-sheet.tsx` | PARTIAL (wraps existing `ui/sheet.tsx side='bottom'`) |
| 2 | `tab-bar.tsx` | MISSING (sidebar is desktop-only) |
| 3 | `app-bar.tsx` | PARTIAL (tab-header is for sub-tabs, not page chrome) |
| 4 | `ui/slider.tsx` | MISSING (only `ui/switch.tsx` exists — most-surprising gap) |
| 5 | `list-row.tsx` | MISSING (record-rail is rail+pane, not settings-list) |
| 6 | `segmented-control.tsx` | MISSING |
| 7 | `fab.tsx` | MISSING |
| 8 | `swipe-action.tsx` | MISSING (no gesture primitive in skeleton) |

See `patterns-md-mobile-gap-audit-2026-05-24.md` § 4 for per-PR shape, tokens, complexity, and consumed-by-mobile mappings.

## § 5 What the operator's branding utterance forecloses

The utterance "take note this needs the sinister branding and look" rules out:

- Shipping a LineageOS-skinned ROM with stock teal accent (rejected — must look Sinister)
- Shipping AOSP Material You with user-pickable accent (rejected — purple-400 is the brand, not a preference)
- Skipping the launcher rewrite "for now" (rejected — the launcher is the most-seen surface; it must be Sinister day-one)
- Shipping Material 3 SystemUI temporarily (allowed ONLY if recolored to Sinister tokens; full Compose port can defer to P4.5 polish)

## § 6 P0 → P1 branding deliverables (gated on operator Q1-Q10 answers)

When P0 unlocks (operator answers Q1-Q10 + clicks lock):

1. `source/compose-theme-bridge/` skeleton (empty package, README, gradle build file)
2. `tokens/sinister-mobile-purple.xml` (Android color resources) — derived from skeleton `globals.css` purple ramp
3. `tokens/sinister-mobile-purple.ts` (Compose tokens) — derived from skeleton `tokens/globals.css`
4. 3 wallpaper variants generated via `sinister-generator` brand-lock helper (cap: 3 images, well under 6-per-task balance)
5. Default bootanimation.zip prototype (frame sequence rendered from a single seed image + programmatic stroke-in)
6. App-icon set: 5 first-party glyphs (Panel, Vault, EVE, Inbox, Mind) — 5 generated images
7. Sample `framework-res/res/values-night/colors.xml` patch swapping AOSP defaults to Sinister tokens

Total P1-handoff image budget: 8 images (3 wallpapers + 5 icons) — within the conservative-balance rules.

## § 7 Composes with

- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base + EXPAND)
- `sinister-os-mobile-doctrine-2026-05-24` (this lane's canonical doctrine)
- `sinister-os-doctrine-2026-05-24` (PC sister; share branding tokens)
- `agent-identity-eve` (the persona inside the ROM)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate)

## § 8 Verbs at gate (no-bullshit)

This doc is **scaffolded** (file exists + parse-clean). It is NOT acceptance-tested — no actual Compose theme bridge built, no actual bootanimation prototyped, no actual icons rendered. The next claim-step is **scaffolded → shipped** when items § 6.1-§ 6.7 land in `source/` with verifiable evidence (file paths + cuttlefish boot screenshot showing purple accent).
