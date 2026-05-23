<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Instagram Pinned-Banner Set

A replacement for the existing 3 pinned cards on `@showmastersproduction` (the ones with the broken "LABOOGISTICS" word). Designed for 1080×1080 IG feed posts that, when pinned in order, read as a 3-card narrative left-to-right on the profile.

## Option A — The 3-card spanning set (recommended)

Pin these three in this order. They form the SMPL signature headline across the profile:

| Position | File | Card reads |
|---|---|---|
| Pin 1 (leftmost) | `ig-pinned-01-we-make-great.svg` | "We Make / Great Days" + locality strip |
| Pin 2 (middle) | `ig-pinned-02-happen.svg` | "Happen" oversized + stats row |
| Pin 3 (rightmost) | `ig-pinned-03-every-day.svg` | "Every Day." + the 3-line trust block + CTA |

The 3 cards share a continuous gold hairline at y=220 + y=940 so the profile feels intentional, not a random set.

When pinning on Instagram, remember IG shows the most-recent pin on the LEFT. So upload + pin in REVERSE order (pin 03 first, then 02, then 01) — that way they read 01 → 02 → 03 left-to-right.

## Option B — Standalone alternatives

Use any single one of these on its own if a spanning set is too rigid:

| File | Purpose |
|---|---|
| `ig-alt-stats.svg` | The "by the numbers" card — 22+ years, 1,700+ clients, 33 states, 130+ crew |
| `ig-alt-services.svg` | A 6-tile services overview — fits the entire "what we do" on one card |
| `ig-alt-promise.svg` | The trust promise — W-4, insurance baked in, same Crew Lead |

These can be mixed with Option A (e.g. pin `ig-alt-promise` + 2 of the spanning set).

## Exporting for Instagram

IG requires raster (PNG / JPEG) on upload. Convert any of these SVGs by:

1. Open in a browser at native 1080×1080 size.
2. Screenshot OR use `rsvg-convert -w 1080 -h 1080 file.svg -o file.png` if rsvg is installed.
3. Or drop into [SVGOMG](https://svgomg.net/) → "Export as PNG."

When nano banana integration is wired, this manual export step goes away — we can render the SVG → PNG via the model's image API directly.

## Why these replace the originals

Looking at the existing 3 pinned cards (screenshot 2026-05-23):

- Card 1 ("WE'RE NATIONWIDE" with US map) is decent but standalone.
- Card 2 reads "LABOOGISTICS" — appears to be a broken word from a spanning composition (intended "LABOR LOGISTICS" maybe) that didn't render right.
- Card 3 reads partial "WE HAVE / COVERED" continuing the broken composition.

The new set fixes that by:
- Making each card complete on its own (so if IG re-orders, they still read).
- Adding a visual continuity (shared gold rule + spotlight bloom) so the spanning set feels intentional.
- Using the canonical SMPL wordmark + gold corner triangle on every card.
- Including the CTA + handle on the trailing card.

## What we did NOT do

- We did NOT introduce new brand elements. Every card uses the existing SMPL identity (wordmark + gold triangle + Inter 900 + the gold gradient) per operator's 2026-05-23 doctrine: "enhance, don't replace."
- We did NOT generate any AI imagery. All assets are hand-built SVG.
- We did NOT use emojis. The yellow squares ("Since 2002") emoji visible in the IG bio should be replaced with plain text when the bio is updated.

## Brief for operator

Please verify before publishing:

1. The IG handle for this brand is `@showmastersproduction` (per the screenshot) — confirm vs. `@showmastersproductionlogistics` (what was in our marketing playbook). Pick one canonical handle and update everywhere.
2. The Orlando address shown in IG bio (`4501 Vineland Rd Suite 110A, Orlando, Florida 32811`) does NOT match the website / JSON-LD / our docs (`4906 Patch Road, Orlando, FL 32822`). Which is current?
3. Pick Option A (spanning set) or Option B (one standalone) before uploading.
