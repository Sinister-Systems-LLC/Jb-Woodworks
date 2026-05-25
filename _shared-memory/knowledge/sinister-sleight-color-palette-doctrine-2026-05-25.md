<!-- decay: category=design, confidence=1.0, half_life_days=730 -->
# Sinister Sleight Color Palette Doctrine (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim

"based the cmd color ascii art and animations off this logo: C:\Users\Zonia\Desktop\2026-05-23T133146Z-banner-hero-statement.png. i want transparent consoles as well and in theme, branded, context and usage popups all jcode features."

## The reference

`C:\Users\Zonia\Desktop\2026-05-23T133146Z-banner-hero-statement.png` --
purple jester w/ crown + horned mask + scepter + tarot cards, magenta-pink
neon ring with runes, deep purple-black background.

## Canonical 8-color palette

| token | 256-color | hex approx | use |
|-------|-----------|------------|-----|
| SLEIGHT_DEEP_PURPLE | 55 | #5f00af | backgrounds, deep accents |
| SLEIGHT_PURPLE | 99 | #875fff | mid-tier UI elements |
| SLEIGHT_JESTER | 141 | #af87ff | primary foreground (== existing PURPLE) |
| SLEIGHT_NEON_MAG | 201 | #ff00ff | neon glow, active state |
| SLEIGHT_NEON_PINK | 205 | #ff5fd7 | highlights |
| SLEIGHT_RUNE_VIO | 177 | #d787ff | borders + decorations (== existing BRIGHTP) |
| SLEIGHT_TAROT_CYAN | 87 | #5fd7ff | rare contrast / "card flip" accent |
| SLEIGHT_CROWN_GOLD | 220 | #ffd700 | use SPARINGLY -- premium accent |

## Where applied (rolling out across iter-28+)

- eve_ui.py + main_menu.py -- glow palette updated this iter
- projects/sinister-term-themes/src/theme.py -- full palette inheritance (sinister-term lane owns the rollout)
- All NEW UI work uses these tokens; existing tokens (PURPLE, BRIGHTP, etc.) kept as aliases

## Anti-patterns

1. Inventing new purple shades. Use the 8 above.
2. Using CROWN_GOLD on >1 element per screen -- it loses meaning.
3. Mixing Sleight with default-terminal-magenta. Always reach for SLEIGHT_NEON_MAG instead.

## Composes with

- eve-ui-uniformity-doctrine-2026-05-24 (header/footer + canonical tokens)
- sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24 (skeleton inherits accent)
