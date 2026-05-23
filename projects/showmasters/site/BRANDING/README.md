<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# SMPL Brand Pack

The Show Masters Production Logistics asset set. Every file is a hand-built SVG — no rasters, no library icons, no AI art.

## Doctrine

**The canonical brand is what SMPL already has.** The primary identity lives in `../public/img/`:

- `logo-horizontal.svg` (the original primary lockup)
- `logo-stacked.svg`, `logo-monogram.svg`, `logo-mark.svg`, `logo-light.svg`
- `favicon.svg`, `og-card.svg`, `pfp-circle.svg`, `pfp-square.svg`

**This `BRANDING/` folder enhances and extends — it does not replace.** Every variant here either:
1. Is a straight format / color reproduction of the canonical brand (e.g. mono, outline, watermark, flat-print), or
2. Is an **exploratory direction** the operator can approve, reject, or refine. Exploratory variants are marked below.

If you only have time to read three files: **`TOKENS.md`** (color + font system), **`USAGE.md`** (when to use what), and the canonical **`../public/img/logo-horizontal.svg`** (the default).

---

## Folder map

```
BRANDING/
  logos/          12 wordmark + lockup variants (the everyday set)
  marks/           5 monogram + emblem variants (small surfaces, patches, app icons)
  social/          4 platform-sized covers (IG, LinkedIn, Facebook, YouTube)
  animated/        2 SMIL-animated SVGs (spotlight sweep + gold shimmer)
  print/           2 business-card templates (front + back, replace {{tokens}})
  README.md        you are here
  TOKENS.md        colors, fonts, spacing, motion
  USAGE.md         do / don't, clear space, min sizes
  CHANGELOG.md     version log
```

---

## logos/ — pick one of these for normal usage

Legend: `[canonical]` = same identity as the existing brand, just formatted differently · `[explore]` = exploratory direction; operator-review before public use.

| File | When to use | Status |
|---|---|---|
| `01-primary-horizontal.svg` | Default refresh of `../public/img/logo-horizontal.svg` — slightly larger, cleaner spacing | `[canonical]` |
| `02-spotlight-cone.svg` | Hero placements — adds a volumetric stage-light cone over the wordmark | `[explore]` |
| `03-truss.svg` | Industry surfaces — wordmark on a box-truss element | `[explore]` |
| `04-stacked-tagline.svg` | Footer, back-of-business-card corner, anywhere square-ish | `[canonical]` |
| `05-banner-cinematic.svg` | Email headers, presentation slides, web hero strips (16:5) | `[canonical]` |
| `06-watermark.svg` | Invoice paper, contracts, anything where the brand is present but not loud | `[canonical]` |
| `07-mono-white.svg` | Photographic backgrounds, dark videos, anywhere a single solid color reproduces best | `[canonical]` |
| `08-mono-black.svg` | Light backgrounds, fax-grade reproduction, low-color printers | `[canonical]` |
| `09-mono-gold.svg` | Foil stamping, hot-foil cards, gold-emboss merchandise | `[canonical]` |
| `10-outline.svg` | Embroidery (single-pass), laser etch, single-color screen print | `[canonical]` |
| `11-vertical-tower.svg` | Vertical sidebars, app splash, vertical banner stands | `[canonical]` |
| `12-flat-no-gradient.svg` | Old offset printers, mass production where gradients muddy | `[canonical]` |

---

## marks/ — when SMPL has to live in a small space

| File | When to use | Status |
|---|---|---|
| `01-emblem-seal.svg` | Premium contracts, anniversary collateral, tour-case engraving | `[explore]` |
| `02-mark-rounded-square.svg` | App icon refresh of `../public/img/logo-mark.svg` at 1024 | `[canonical]` |
| `03-mark-hex.svg` | Engineering / spec-sheet feel — dispatch tags, road-case stencils | `[explore]` |
| `04-mark-shield.svg` | Crew patch, embroidered shirts, dispatch jackets | `[explore]` |
| `05-mark-tour-case.svg` | Decorative element — slide kickers, marketing collateral with industrial cue | `[explore]` |

The five `[explore]` marks introduce shapes not present in the original identity (seal/hex/shield/tour-case). They are visual proposals, not in-use brand. Operator approves before any of these appear on shipped collateral.

---

## social/ — already sized for each platform

| File | Platform & spec |
|---|---|
| `instagram-pfp-1024.svg` | Instagram + any 1:1 PFP — 1024×1024 |
| `linkedin-banner-1584x396.svg` | LinkedIn company cover — 1584×396 |
| `facebook-cover-820x312.svg` | Facebook page cover — 820×312 |
| `youtube-banner-2560x1440.svg` | YouTube channel art — 2560×1440 (safe zone 1546×423 centered) |

To use any of these on a platform that needs a PNG, drop the SVG into [SVGOMG](https://svgomg.net/) → export PNG at 2× size. Or open in a browser and screenshot.

---

## animated/ — when you need motion

| File | Use |
|---|---|
| `spotlight-sweep.svg` | A pure-SVG SMIL animation — a spotlight cone sweeps across the wordmark. Drop into any `<img>` or `<object>` tag and it just plays. ~6s loop |
| `gold-shimmer.svg` | The triangle accent gets a subtle gold shimmer that sweeps every 3s |

These run with zero JS. Reduced-motion users will still see the static frame correctly.

---

## print/ — production-ready

| File | Use |
|---|---|
| `business-card-front.svg` | Front side, 3.5"×2" at 300dpi (1050×600). Trim with 3mm bleed |
| `business-card-back.svg` | Back side. Replace `{{NAME}}`, `{{ROLE}}`, `{{CELL}}`, `{{EMAIL}}` before sending to print |

---

## Asking for changes

When adding a variant, follow the existing naming convention (`NN-purpose.svg`), keep the file under 4 KB, add a one-line entry to this README, and bump `CHANGELOG.md`.

Never rasterize the source. PNG exports are downstream artifacts.
