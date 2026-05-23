# JB Woodworks - Nano Banana brand memory

> **Author:** RKOJ-ELENO :: 2026-05-23

The `jbw_image()` helper auto-appends the canonical brand-lock suffix (see
`tools/nano-banana/nano_banana/api.py` :: `JBW_STYLE`). This file documents the
intent + boundaries so future agents don't drift.

## Palette (lock these into every prompt)

- Black ink: `#080808`
- Off-black panel: `#111` / `#1a1a1a`
- Warm gold: `#c9a84c`
- Gold-light: `#e2c47a`
- Gold-deep: `#9c7126`
- Cream: rgba(255,255,255,0.80)

## Typography rule

NEVER bake text or letterforms into a generated image. Typography stays in SVG
(`branding/`, wordmarks) and React components. If a card design calls for "JB
Woodworks" the layout, that title is rendered in DM Serif Display + Inter, not
generated.

## Voice rule (anti-slop)

- No fake project photos that imply real client work. JB has REAL photography in
  `D:\Sinister\old\Coding Random\JB Woodworks\Jah Images\` (~105 MB) — that is
  the source of truth for actual builds. Generated images are ONLY for
  atmosphere / mood / texture / blog headers / social backgrounds.
- No human faces unless ref-image-supplied and explicitly approved. Hands at
  work are fine (gloves, sleeves, tool grip) but not headshots.
- No plastic / faux finishes (built-in to the brand-lock suffix).
- No emojis, no logos, no UI chrome (built-in).
- Photoreal, not illustrated. Italic-emphasis comes from typography, not the
  image.

## Acceptable subjects (mood targets)

- Wood-grain close-up (walnut, oak, cherry, maple) — raking gold light reveals
  grain, deep shadows fill the rest
- Workshop atmosphere — sawdust on dark floor, a chisel resting on a planed
  edge, gold rim light from a single source
- Florida outdoor craft — silhouette of dock posts at golden hour, dark navy
  water, no boats / no people
- Pergola post detail — pressure-treated timber joinery, gold edge-light on
  end grain
- Hand at work — gloved hand pulling a hand-plane shaving, focused on the
  motion not the person

## Output layout (per inbox 2026-05-23T07:35Z)

- `projects/sinister-generator/outputs/jb-woodworks/banners/` — wide page backdrops
- `projects/sinister-generator/outputs/jb-woodworks/social/` — IG / TikTok / X post backgrounds
- `projects/sinister-generator/outputs/jb-woodworks/blog-heroes/` — future blog post headers
- `projects/sinister-generator/outputs/jb-woodworks/portfolio-teasers/` — atmospheric category teasers (NOT fake build photos)
- `projects/sinister-generator/outputs/jb-woodworks/_rejected/` — failed / off-brand attempts

When committing to the JB Woodworks site, copy the chosen PNG + its
`.meta.json` sidecar into `projects/jb-woodworks/public/img/generated/`.

## Compositional rules for in-site use

- Always render generated images at low opacity (15-25%) when placed behind
  body text. The brand reads off the typography, not the photo.
- Use a black overlay or radial vignette so the content stays legible.
- For OG / social cards, the image is the backdrop; the wordmark is overlaid
  in SVG.
