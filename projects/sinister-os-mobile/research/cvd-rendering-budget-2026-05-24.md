# Cuttlefish Rendering Budget — Sinister OS Mobile

> Author: RKOJ-ELENO :: 2026-05-24
> Status: **scaffolded** — paper analysis, not validated by actual cuttlefish boot (cvd boot is P3, not started)
> Composes with: `kernel-spec-2026-05-24.md` § 5 (cuttlefish divergence), `branding-spec-2026-05-24.md` (Liquid Glass inheritance), `patterns-md-mobile-gap-audit-2026-05-24.md` (mobile primitives)

## § 1 The problem

Cuttlefish (`aosp_cf_x86_64_phone-userdebug`) is x86_64 KVM-friendly. Its GPU is **SwiftShader (software rasterizer)** by default — `lavapipe` if Vulkan-mode enabled. The Pixel 6a's GPU is **ARM Mali-G78 MP20** (Tensor G1's GPU block). These are wildly different in:

- **Fill rate** — Mali-G78 ~500 GFLOPS; SwiftShader CPU-bound, single-threaded effective ~5-30 MPixels/s on a modern build host
- **Blur perf** — Mali has dedicated 2-pass Gaussian blur via shader; SwiftShader executes the same shader on x86 cores, *no* hardware blur acceleration
- **Saturate filter** — `saturate(180%)` is CSS `color-mix` → GLSL per-pixel; Mali nails it, SwiftShader chokes at scale
- **Alpha blending** — many overlapping translucent layers stack much more cheaply on hardware

**Implication:** Liquid Glass (the dashboard-skeleton's binding material) uses 28-36px backdrop-blur + 180% saturate + ultra-thin borders + inset highlights + accent glow. On metal Pixel 6a, fine. On cuttlefish, this can drop to 5-15fps depending on layer count — making cvd UI smoke-tests misleading.

## § 2 Per-token rendering cost on SwiftShader (estimated)

Token costs scored on a 3-level scale: 🟢 fine (60fps maintained) · 🟡 degraded (30-45fps) · 🔴 likely choke (<20fps or fallback needed).

### § 2.1 Core skeleton tokens

| Token / class | Recipe | SwiftShader verdict | Notes |
|---|---|---|---|
| `.lg-card` | 28px blur + 180% sat + inset white highlight + accent shadow + 16px radius | 🟡 | Single card OK; grid of 8+ cards in viewport → 30fps |
| `.lg-card-hero` | Like `.lg-card` but larger surface + stronger shadow | 🟡 | Hero alone fine; with backdrop-blur sidebar → 25fps |
| `.lg-rail` | Backdrop blur on a wide vertical surface | 🔴 | Always-on full-height blur is the worst case on SwiftShader |
| `.lg-pill` / `.lg-pill-active` | 16px blur on small pills | 🟢 | Pills are small; perf-OK |
| `.lg-button` | 12-16px blur + glow on small button | 🟢 | Fine |
| `.lg-input` | 12px blur + ultra-thin border | 🟢 | Fine |
| `.lg-popover` | 36px blur on popover surface | 🟡 | Single popover OK; nested popovers/menus drop frames |
| Page-signature CSS (per-route blur+gradient) | Variable | 🟡-🔴 | Audit per route during P3 cvd smoke |
| Accent-tinted drop shadows | `0 4px 16px color-mix(...)` | 🟢 | Cheap on both |
| Number ticker animation | `requestAnimationFrame` over 600ms | 🟢 | CPU-only, fine |
| Aurora background (`primitives/aurora-bg.tsx`) | Animated gradient with blur | 🔴 | Will hammer cvd; need fallback |
| Glow drop-shadow | `0 0 40px color-mix(...)` | 🟢 | Cheap |

### § 2.2 Mobile-Tier-1 primitives (from gap-audit)

| Primitive | New cost | SwiftShader verdict | Mitigation |
|---|---|---|---|
| Bottom sheet | Drag handle pill + `.lg-card` recipe | 🟡 | OK in isolation |
| Tab bar (bottom) | Always-on bottom `.lg-card` strip with 5 icons | 🟡 | Always visible = always blurring background |
| App bar (top) | Always-on top `.lg-card` strip | 🟡 | Same as tab bar |
| Slider | `.lg-card` thumb + glow | 🟢 | Thumb is small |
| List row | Plain row with hover/active state | 🟢 | No heavy effect |
| Segmented control | Animated `.lg-pill-active` slider | 🟢 | Fine |
| FAB | `.lg-button` recipe + glow | 🟢 | Fine |
| Swipe action | Row reveals action chips | 🟢 | No blur required |

**Worst-case combo on cuttlefish:** tab bar + app bar + aurora-bg + a `.lg-card` grid → 4 always-on blur layers. Likely 15-20fps on SwiftShader. We need a fallback recipe.

## § 3 Fallback recipes for SwiftShader (cvd-only)

When `getprop ro.hardware` returns `cutf` or `goldfish` (emulator markers), the theme bridge applies a `data-cvd-fallback="true"` attribute on `<body>` that swaps these CSS values:

```css
/* cvd-fallback.css — applied via [data-cvd-fallback="true"] selectors */

[data-cvd-fallback="true"] .lg-card,
[data-cvd-fallback="true"] .lg-card-hero,
[data-cvd-fallback="true"] .lg-rail,
[data-cvd-fallback="true"] .lg-popover {
  /* Drop the backdrop-blur entirely; emulate with a darker semi-transparent panel */
  backdrop-filter: none;
  background-color: rgb(20 20 26 / 0.92);  /* vs the usual /0.70 with blur */
}

[data-cvd-fallback="true"] .lg-pill,
[data-cvd-fallback="true"] .lg-button,
[data-cvd-fallback="true"] .lg-input {
  /* Keep the look at smaller scale; pills are cheap enough */
  /* Only reduce if perf-audit during P3 shows real drops */
}

[data-cvd-fallback="true"] .aurora-bg {
  /* Replace animated gradient with a static SVG matte */
  background-image: url(/assets/aurora-static.svg);
  animation: none;
}

[data-cvd-fallback="true"] {
  /* Disable motion for primitives that animate position+blur together
     (the worst combo) */
  --motion-slow: 0ms;  /* was 600ms */
}
```

**Detection logic** (lives in the Compose theme bridge, P4 deliverable):

```kotlin
// inside SinisterTheme composable, P4
val ro_hardware = remember { systemProperty("ro.hardware") }
val isCvd = ro_hardware in listOf("cutf", "goldfish", "ranchu")
CompositionLocalProvider(LocalIsCvd provides isCvd) { content() }
```

Then the WebView (Sinister Panel mobile route container) reads `LocalIsCvd` and injects `data-cvd-fallback="true"` on the body.

## § 4 Verdict on cvd UI smoke-testing

**What cvd smoke-test CAN validate:**
- Layout correctness (every primitive renders in the right place)
- Color tokens applied correctly (Sinister purple shows up, no leaked iOS-blue)
- Click/touch hit targets (gesture detection, swipe-action triggering)
- Routing (tab-bar → Panel page transitions)
- Compose theme bridge mapping (skeleton tokens → Material 3 theme)
- Bottom sheet behavior (snap points, drag-to-dismiss)
- Lifecycle (BOOT_COMPLETED → EVE service announce → sticky notification)

**What cvd CANNOT validate:**
- **Real perf of Liquid Glass on Mali** — fallback recipe means cvd shows a *different* look. Need real Pixel 6a (P5 gate) to verify the actual Liquid Glass look ships at 60fps
- Aurora background true visual quality
- Multi-layer blur stack interaction
- Battery drain from always-on blur (not relevant on cvd; matters on metal)

## § 5 Lateral implication for the skeleton

This isn't only a mobile concern. The dashboard-skeleton's web surfaces ALSO chronically hit perf issues on lower-end machines (operators on cheaper laptops). The `[data-cvd-fallback="true"]` mechanism — repurposed as a `[data-low-perf="true"]` user-toggle — could give the skeleton a "reduce visual effects" accessibility setting it currently lacks.

**Recommended cross-lane handoff:** when this audit gets reviewed, message `sinister-dashboard-skeleton` lane to consider adding the fallback layer as a permanent skeleton feature, not just a mobile-cvd workaround. Operator gets accessibility win; this lane gets a no-op-on-metal fallback.

## § 6 P3 verification plan

When cuttlefish boots vanilla (master-plan § 6 P3 gate), run:

1. Boot cvd: `cvd start --report_anonymous_usage_stats=n`
2. Wait for `adb shell getprop sys.boot_completed` → 1
3. Install Sinister Panel APK (P4 deliverable, but stub for cvd-only build)
4. Open the most blur-heavy route (overview with stat-card grid + sidebar + popovers)
5. Measure: `adb shell dumpsys gfxinfo com.sinister.panel framestats` — capture 90th percentile frame time
6. Threshold: 90th percentile > 16ms (60fps target) on metal; > 33ms (30fps) on cvd-with-fallback is acceptable
7. If cvd-with-fallback < 30fps: revisit fallback recipes; drop more effects

## § 7 No-bullshit verbs at gate

- This doc is **scaffolded** (paper analysis, cited from general knowledge of SwiftShader perf characteristics + skeleton THEME-DOCTRINE.md)
- It is NOT acceptance-tested — no cvd boot has happened, no `dumpsys gfxinfo` has been read, no fallback recipe has been tested
- Next claim-step is **scaffolded → in-flight** when the fallback recipe lands on a skeleton branch (would be Tier 2 PR in patterns-md-mobile-gap-audit terms)

## § 8 Composes with

- `kernel-spec-2026-05-24.md` § 5 (cuttlefish divergence; this doc is the UI-perf-specific deepdive)
- `branding-spec-2026-05-24.md` (Liquid Glass binding — this doc identifies cvd fallback for the same material)
- `patterns-md-mobile-gap-audit-2026-05-24.md` (mobile primitives; this doc adds rendering-cost rows)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate)
- Sister: `sinister-os` PC lane shares Liquid Glass usage on desktop, but no SwiftShader concern there
