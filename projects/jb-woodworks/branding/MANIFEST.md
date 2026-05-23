# JB Woodworks - Brand Asset Pack

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Status:** Enhanced from canonical v1 (the prior Vercel build).

The original JB Woodworks identity was already established: text-based
"JB WOODWORKS" wordmark in Inter Black with a gold underline, on a
deep-black ground. This pack preserves that identity verbatim and
extends it across new surfaces (social cards, email signatures, print
lockups) so the brand can scale beyond the website without losing
recognition.

All assets are hand-authored SVGs. Edit in a text editor; do not
re-export through a binary tool that may flatten font metrics.

## Color tokens (carried verbatim from v1 style.css)

| Token | Hex | Use |
| --- | --- | --- |
| `--black` | `#080808` | Page ground, primary surface |
| `--black-2` | `#0f0f0f` | Section alternation |
| `--black-3` | `#141414` | Card surface |
| `--black-4` | `#1a1a1a` | Hover lift |
| `--black-5` | `#222222` | Highest elevation |
| `--gold` | `#c9a84c` | Primary accent, brand mark gold-underline, CTAs |
| `--gold-light` | `#e2c47a` | Hover state, highlights |
| `--gold-dim` | `rgba(201, 168, 76, 0.10)` | Tinted backgrounds (nav badge, icon plates) |
| `--white` | `#ffffff` | Body text, headlines |
| `--white-80/50/30` | rgba | Tiered text contrast |
| `--border` | `rgba(255,255,255,0.07)` | Hairlines |

## Typography (carried verbatim from v1)

- **Display:** DM Serif Display (regular + italic). Italic is the brand voice for em-phasized words ("Built to *Last*", "Our Custom *Services*").
- **Body + wordmark:** Inter (300 / 400 / 500 / 600 / 700 / 800 / 900). The wordmark uses Inter 900 with 0.16em letter-spacing.
- Loaded from Google Fonts with `display=swap`.

## Files

| File | Dimensions | Tone | Intended surface |
| --- | --- | --- | --- |
| `logos/wordmark-primary.svg`        | 320x140  | dark-bg  | Header lockup, business cards, invoice header |
| `logos/wordmark-horizontal.svg`     | 420x80   | dark-bg  | Email signatures, footer, sign painting |
| `logos/wordmark-stacked.svg`        | 360x280  | dark-bg  | Square placements: stamps, packaging, social avatar surround |
| `logos/wordmark-mono-dark.svg`      | 320x140  | mono     | Light-on-dark monochrome (etched signage, dark print) |
| `logos/wordmark-mono-light.svg`     | 320x140  | mono     | Dark-on-light monochrome (paper print, embroidery) |
| `logos/favicon.svg`                 | 64x64    | dark-bg  | Browser tab, app-icon source |
| `logos/social-card.svg`             | 1200x630 | dark-bg  | OG / Twitter card, share preview |
| `logos/email-signature.svg`         | 420x110  | dark-bg  | Email signature footer |
| `patterns/grain-tile.svg`           | 64x32    | dark-bg  | CSS `background-image` repeating tile |
| `patterns/ring-pattern.svg`         | 240x240  | dark-bg  | Hero overlay, page-mount backdrop |

Total: 8 logo variants + 2 patterns.

## Wordmark construction

The mark is two text layers, not a font subset:
1. `JB` in Inter 900, 58pt, 9px letter-spacing, white.
2. `WOODWORKS` in Inter 700, 11pt, 11px letter-spacing, gold (`#c9a84c`), centered under the JB.

A thin gold hairline (1-2px) optionally sits between the two layers
(`wordmark-stacked.svg`) to anchor them on larger placements.

## Usage rules

1. Minimum clear space around the wordmark = the cap height of the "J".
2. Minimum size for the primary wordmark = 80px wide on screen, 0.7in in print.
3. Never recolor outside the token list. Gold is the only brand accent.
4. Never apply shadow, glow, or bevel effects to the wordmark.
5. On photography, use `wordmark-mono-dark.svg` placed on a black-tinted plate (rgba(8,8,8,0.7)) rather than directly on the image.

## License

These assets are proprietary to JB Woodworks. Authored by RKOJ-ELENO
on behalf of the Sinister Sanctum agency lane.
