# JB Woodworks - Brand Guidelines

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** v2 - owner-supplied JBW logo system (monogram + horizontal + stacked wordmarks) now canonical. Replaces the v1 hand-drawn text wordmark.

Single-rule version: **gold-on-ink JBW monogram + wordmarks, DM Serif Display + Inter, italic for emphasis. Nothing else.**

## The three canonical marks (owner spec 2026-05-24)

| Mark | File | Use for |
| --- | --- | --- |
| **Primary Monogram** | `public/img/branding/jbw-monogram.png` | Social profile pictures, favicon, watermarks, mobile/small branding, minimal placements |
| **Horizontal Wordmark** | `public/img/branding/jbw-wordmark-horizontal.png` | Website header / top-left corner, email signatures, invoices, business documents |
| **Stacked Wordmark** | `public/img/branding/jbw-wordmark-stacked.png` | Website footer, presentation graphics, portfolio section branding, signage, larger branded placements |

All three are recolored from the owner's source PNGs to brand gold `#c9a84c` on **transparent** backgrounds (so the same files drop cleanly over any surface in the ink palette).

### Pipeline

`scripts/recolor-logos.py` re-derives every output from sources in `scripts/_logo-src/jbw-{monogram,horizontal,stacked}-src.png`. If the owner ships an updated source mark, replace the matching file in `_logo-src/` and re-run:

```bash
python scripts/recolor-logos.py
```

Outputs (auto-replace in place):
- `public/img/branding/jbw-monogram.png` - icon only, gold/transparent
- `public/img/branding/jbw-wordmark-horizontal.png` - icon + name, gold/transparent
- `public/img/branding/jbw-wordmark-stacked.png` - icon over name + tagline
- `public/img/branding/jbw-monogram-on-ink.png` - mark centered on #080808 (square, social use)
- `public/img/favicon-{16,32,48,180,192,512}.png` + `favicon.ico`
- `public/img/og-image.png` (1200x630 social card)
- `branding/logos/email-signature.png` (560x160 email block)

## Voice and tone

- **Confident, plain.** A craftsman talks like a craftsman.
- **Concrete.** Name the wood. Name the project type. Name the city.
- **Direct on price.** "Free estimates." Above the fold on the contact page.
- **The italic move.** Display-serif italic on the second half of a headline ("Premium Craftsmanship. Built to *Last*."). That is the brand signature. Use it on every page head.

Phrases to avoid (slip-ups from prior drafts):
- "Heirloom-grade", "artisan", "bespoke", "curated"
- "Passion for the craft" (we let the work say it)
- Star ratings, vague claims, invented stat lines

## Color usage

| Surface | Ground | Body text | Accent |
| --- | --- | --- | --- |
| Default (site, app) | `--black` `#080808` | `--white-80` | `--gold` `#c9a84c` |
| Section alt | `--black-2` `#0f0f0f` | `--white-80` | `--gold` |
| Card on black | `--black-3` `#141414` | `--white-50` | `--gold` |
| CTA band | `--gold` (gradient) | `--black` | `--black` button on gold |
| Light print | `--white` | `--black` | `--gold` (only if 2-color budget) |
| Embroidery / single-color | gold thread on black, OR black ink on white | n/a | n/a |

The gold ramp is the **only** accent. Never mix in a second brand color.
Greens, blues, etc. - not in scope.

## Typography rules

- Headings: DM Serif Display, regular for the first phrase, italic in gold for the punchline.
- Body: Inter 400-500, line-height 1.7-1.8 on dark.
- Eyebrow labels (section-tag): Inter 700, 0.22em tracking, ALL CAPS, gold, 0.68rem.
- The wordmark: Inter 900 for "JB", Inter 700 for "WOODWORKS" (tighter weight than you would expect).

## Wordmark do / do not

**Do:**
- Use `jbw-wordmark-horizontal.png` for header, business cards, invoices, email sigs.
- Use `jbw-wordmark-stacked.png` for footer, presentation graphics, signage, larger placements.
- Use `jbw-monogram.png` for favicon, social profile pics, watermarks, mobile.
- Use `jbw-monogram-on-ink.png` when you need the mark already on a black plate (social cards).

**Do not:**
- Add shadow, glow, bevel, outline, or any 3D effect (subtle drop-shadow over busy photography is the one exception - see hero).
- Recolor outside brand gold `#c9a84c`. Don't tint it warmer/cooler.
- Stretch, rotate, or skew.
- Combine multiple marks in one placement (pick one).
- Re-add the old text-only "JB / WOODWORKS" lockup anywhere - the owner's monogram is canonical now.

## Asset selection guide

| You need a logo for... | Reach for |
| --- | --- |
| Website navbar | `/img/branding/jbw-wordmark-horizontal.png` (wired in `components/sections/nav.tsx`) |
| Website footer | `/img/branding/jbw-wordmark-stacked.png` (wired in `components/sections/footer.tsx`) |
| Splash / loading screens | `/img/branding/jbw-monogram.png` (wired in `splash.tsx` + `loading.tsx`) |
| Favicon / browser tab | `/img/favicon-*.png` + `favicon.ico` (all regenerated from monogram) |
| Apple touch icon | `/img/favicon-180.png` |
| Android home screen | `/img/favicon-192.png` + `/img/favicon-512.png` via `site.webmanifest` |
| Social avatar (IG, FB, TT, X) | `/img/branding/jbw-monogram-on-ink.png` (square, ready to upload) |
| Social share / OG card | `/img/og-image.png` (1200x630, wired in `app/layout.tsx`) |
| Email signature | `/branding/logos/email-signature.png` (560x160 PNG, renders consistently in Gmail/Outlook) |
| Invoice / letterhead | `jbw-wordmark-horizontal.png` top-left, 1.6in wide |
| Business card | `jbw-wordmark-stacked.png` centered on black, generous clear space |
| Vehicle decal / signage | `jbw-wordmark-stacked.png` or `jbw-wordmark-horizontal.png` |
| Yard sign | `jbw-wordmark-stacked.png` at 18in tall, contact set in DM Serif Display below |

## Clear space + minimum sizes

- **Monogram:** clear space = 0.25× icon width on all sides. Minimum display size: 24px (favicon-16 is hand-tuned).
- **Horizontal wordmark:** clear space = height of the JBW icon on each side. Minimum: 120px wide on screen.
- **Stacked wordmark:** clear space = height of the icon on top + sides. Minimum: 96px tall on screen.

## Pending enhancements

- Photo presets (LUT / lightroom preset) to match the gold-on-black mood in client photography.
- Vehicle-wrap mockup at full scale.
- Yard-sign and lawn-board templates.
- Nano-banana integration (operator coordinating from another lane) - generated imagery should respect the gold/black palette and the italic-tagline voice.
