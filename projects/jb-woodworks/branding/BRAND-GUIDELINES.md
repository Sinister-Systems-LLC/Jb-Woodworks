# JB Woodworks - Brand Guidelines

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Status:** Codifies the canonical v1 identity and extends it.

Single-rule version: **white-and-gold wordmark on deep black, DM Serif
Display + Inter, italic for emphasis. Nothing else.**

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
- Use `wordmark-primary.svg` for header, business cards, invoices.
- Use `wordmark-stacked.svg` for vertical placements (square stamps, social avatars).
- Use `wordmark-mono-dark.svg` on photography over a `rgba(8,8,8,0.7)` plate.
- Keep the gold-underline accent visible whenever space permits.

**Do not:**
- Add shadow, glow, bevel, outline, or any 3D effect.
- Replace Inter with a similar sans (Roboto, Helvetica) - they kern differently.
- Recolor outside the gold ramp.
- Stretch, rotate, or skew.
- Put the wordmark on busy photography without the black plate.

## Asset selection guide

| You need a logo for... | Reach for |
| --- | --- |
| Website navbar | `wordmark-primary.svg` (or inline HTML in `base.html`) |
| Footer | inline HTML wordmark |
| Social avatar (IG, FB, TT, X) | `wordmark-stacked.svg` (renders well at small sizes) |
| Invoice / letterhead | `wordmark-horizontal.svg` |
| Vehicle decal / signage | `wordmark-horizontal.svg` (or mono variant for 1-color budget) |
| Email signature | `email-signature.svg` |
| Social share / OG image | `social-card.svg` (1200x630) |
| Business card | `wordmark-stacked.svg` centered, generous clear space |
| Branded stamp / iron-on | `wordmark-mono-light.svg` (gold on white) or `wordmark-mono-dark.svg` |

## Print specs

- Business cards: 3.5 x 2in, black ground, `wordmark-stacked.svg` centered, contact set in Inter 500 8pt below.
- Letterhead: `wordmark-horizontal.svg` top-left at 1.6in wide, address bottom-right.
- Invoice: `wordmark-horizontal.svg` top-left, line items in Inter tabular-nums.
- Yard sign: `wordmark-stacked.svg` at 18in tall, with `(407) 561-1453` set in DM Serif Display 96pt italic below.

## Web specs (already wired)

- All assets ship in `/static/img/icons.svg` (UI icons) and `/branding/logos/` (brand wordmarks).
- Wordmark renders inline as text in `base.html` for sharpness at any zoom level.
- Favicon: `/static/img/favicon.svg` (also at `/branding/logos/favicon.svg`).
- OG image: `/static/img/og-image.svg` (mirrors `/branding/logos/social-card.svg`).

## Pending enhancements

- Photo presets (LUT / lightroom preset) to match the gold-on-black mood in client photography.
- Vehicle-wrap mockup at full scale.
- Yard-sign and lawn-board templates.
- Nano-banana integration (operator coordinating from another lane) - generated imagery should respect the gold/black palette and the italic-tagline voice.
