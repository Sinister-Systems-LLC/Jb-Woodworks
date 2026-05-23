<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# SMPL Brand Usage

A short guide so the brand reads the same everywhere — on a hard hat, on a contract header, on a YouTube banner, on a 4-foot trade-show backwall.

---

## Clear space

Around every logo lockup, leave clear space equal to the **height of the "S" letter** in the wordmark. Nothing intrudes — no headlines, no photos, no edges of the page.

```
   ┌─────────────────────────────┐
   │                             │
   │    [ S M P L              ] │
   │                             │
   └─────────────────────────────┘
   ^                             ^
   one "S" height clear margin
```

This is the single rule that makes the logo feel premium vs. cluttered.

---

## Minimum sizes

| Use | Min width (digital) | Min width (print) |
|---|---|---|
| Primary horizontal logo (`01`) | 140 px | 1.4 in / 35 mm |
| Spotlight cone (`02`) | 220 px | 2.2 in / 56 mm |
| Truss (`03`) | 200 px | 2.0 in / 50 mm |
| Stacked (`04`) | 90 px | 0.9 in / 23 mm |
| Marks (any) | 24 px | 0.24 in / 6 mm |

Below the minimum, switch to `marks/02-mark-rounded-square.svg`.

---

## Backgrounds — picking the right variant

| Background | Use |
|---|---|
| **Dark solid** (`#0A0A0F` to `#1C1C24`) | Default. Any of the full-color logos (`01–05`, `11`) |
| **Photo / video** with dark areas | `07-mono-white.svg` |
| **Light solid** (white / cream) | `08-mono-black.svg` or `12-flat-no-gradient.svg` |
| **Gold or warm color** | `08-mono-black.svg` (never gold-on-gold) |
| **Anywhere a single foil is needed** | `09-mono-gold.svg` or `10-outline.svg` |
| **Invoice / paperwork** | `06-watermark.svg` placed faintly behind content |

When in doubt, default to dark surface + `01-primary-horizontal.svg`. The brand looks best on dark.

---

## Do

- Use the source SVGs everywhere they fit. SVGs scale, raster files don't.
- Keep the gold triangle in the upper-right corner of the L (the canonical spotlight nick).
- Use Inter 900 with tight tracking (-2) for the wordmark. Anything looser reads soft.
- Pair the SMPL wordmark with the full company name "Show Masters Production Logistics" when the audience may not recognize the abbreviation (first-time prospects, cold outreach, regulators).
- Match the gold gradient exactly — `#E8C078 → #D4A24A → #9C7126` at 135°.
- Animate the spotlight sweep on hero placements when you want extra polish (`animated/spotlight-sweep.svg`).

## Don't

- Don't rasterize the source files. Always export raster from SVG at the moment of export, never edit the raster.
- Don't change the corner triangle into a different shape (circle, star, etc.). The triangle is the spotlight cue.
- Don't swap the gold for another color. The gold is the brand. No "team Florida green" version, no "patriotic blue" version, no holiday-themed recolor.
- Don't put the logo on top of busy photography without a darkened scrim behind it. Either use a dark area of the photo or place a 40% black scrim under the logo.
- Don't use emojis next to the brand. Not in marketing copy, not in social posts. Custom SVG icons only.
- Don't stretch or skew the wordmark. The proportions are tuned.
- Don't add drop shadow under the wordmark unless using the existing gold-glow recipe in `TOKENS.md`.

---

## Naming / spelling

| Long form | "Show Masters Production Logistics" — spaces, title case |
| Abbreviation | "SMPL" — all caps, no periods |
| Possessive | "SMPL's" |
| Never | "ShowMasters" (one word), "SHOW MASTERS" in body copy, "Smpl" (mixed case) |

Company website: **showmasters.com** (always lowercased).
Primary phone: **(877) 765-2267**.
Primary email: **Orders@ShowMasters.com**.

---

## Logo on photography

If you must place a logo over a photo:

1. Find a dark area of the photo and put the logo there.
2. If no dark area exists, add a `linear-gradient(180deg, rgba(0,0,0,0.55), rgba(0,0,0,0)) ` scrim behind the logo.
3. Use `07-mono-white.svg` rather than the full-color version — it survives photo backgrounds better.

---

## When the brand might be diluted

If a client or partner asks to "co-brand" with the SMPL logo, follow these rules:

1. **SMPL always on the left** in a horizontal lockup, or **on top** in a vertical one.
2. **A vertical hairline** between SMPL and the partner mark, 1 px gold at 55% opacity.
3. **Equal optical weight** — SMPL's height should match the partner's *most distinctive feature*, not match their raw bounding box.
4. **Never inside a partner's identity boundary** — SMPL is never enclosed by a partner's container, ring, or frame.

When in doubt, decline and offer to provide a written endorsement instead.
