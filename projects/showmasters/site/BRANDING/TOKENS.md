<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# SMPL Brand Tokens

These are the values that make every asset feel like the same brand. Mirror them into any new file. Most of these are already wired into `style.css` as CSS custom properties — this doc is the canonical source.

---

## Color

### Surface ramp (dark)

| Token | Hex | Used for |
|---|---|---|
| `--bg`   | `#0A0A0F` | Page canvas |
| `--bg-1` | `#13131A` | Card / glass surface base |
| `--bg-2` | `#1C1C24` | Elevated surface |
| `--bg-3` | `#2A2A33` | Hover / pressed |

### Brand accent (gold)

| Token | Hex | Used for |
|---|---|---|
| `--gold-50`  | `#FBF1DC` | Soft tint — backgrounds, tag pills |
| `--gold-100` | `#F4DFB1` | Subtle highlight |
| `--gold-300` | `#E8C078` | Gradient start, glow |
| `--gold`     | `#D4A24A` | **Primary brand** — links, CTAs, accents |
| `--gold-700` | `#B88736` | Pressed state |
| `--gold-900` | `#5C4319` | Glow base, deep accent |

Gradient (the SMPL gold gradient as it appears in every logo):

```
linear-gradient(135deg,
  #E8C078 0%,
  #D4A24A 55%,
  #9C7126 100%
)
```

### Text levels

| Token | Hex | Use |
|---|---|---|
| `--text`   | `#FFFFFF` | Headings, key UI |
| `--text-2` | `#C7C7CF` | Body copy |
| `--text-3` | `#8E8E98` | Captions, meta |
| `--text-4` | `#5C5C66` | Disabled, hint |

### Borders & overlays

| Token | Value |
|---|---|
| `--border`   | `rgba(255,255,255,0.07)` |
| `--border-2` | `rgba(255,255,255,0.12)` |
| `--gold-soft` | `rgba(212,162,74,0.12)` (gold tint behind glass) |
| `--gold-ring` | `rgba(232,192,120,0.55)` (focus ring) |

### Semantic

| Token | Hex | Use |
|---|---|---|
| `--danger`  | `#E5484D` | Form errors, destructive actions |
| `--success` | `#34C759` | Form success, confirmations |

---

## Typography

### Families

| Family | Use | Weights |
|---|---|---|
| **Inter** | UI, body, tagline, monogram | 400 / 500 / 600 / 700 / 800 / 900 |
| **DM Serif Display** | Display headings (H1–H3), pull quotes | 400 / 400 italic |

Inter for everything functional. DM Serif Display for the things that should feel cinematic.

### Scale

```
H1   clamp(2.6rem,  6vw, 5.0rem)
H2   clamp(2.0rem, 4.2vw, 3.4rem)
H3   clamp(1.05rem, 2vw, 1.35rem)
Body 1rem (16px)  line-height 1.7
Caps tracking 3.2–6.4 letter-spacing on small uppercase labels
```

### Wordmark spec

- Family: Inter
- Weight: 900
- Letter-spacing: −2 (tight)
- Triangle accent: 14×14 (small), 24×24 (med), 240×240 (large). Always upper-right of the L.
- Triangle gradient: 135° (see above)

---

## Spacing & radius

| Token | Value |
|---|---|
| `--r-sm` | `8px`  |
| `--r`    | `14px` |
| `--r-lg` | `20px` |
| Card padding (mobile) | `24px` |
| Card padding (desktop) | `40px` |
| Section padding (desktop) | `110px` vertical |
| Container max width | `1200px` |
| Container side padding | `28px` |

---

## Motion

Three durations, one curve. Never more.

| Token | Value | Use |
|---|---|---|
| `--motion-fast` | `150ms` | Hover state, focus, micro-interactions |
| `--motion-med`  | `300ms` | Card lift, modal open, accordion toggle |
| `--motion-slow` | `600ms` | Hero fades, page transitions |
| `--ease` | `cubic-bezier(0.22, 1, 0.36, 1)` | All easing |

If you reach for a different easing curve, stop and use this one instead.

---

## Effects

### Liquid Glass (the surface)

```css
background: color-mix(in oklab, var(--bg-1) 72%, transparent);
backdrop-filter: blur(24px) saturate(170%);
border: 1px solid color-mix(in oklab, white 10%, transparent);
box-shadow:
  inset 0 1px 0 0 color-mix(in oklab, white 14%, transparent),
  inset 0 0 50px -30px color-mix(in oklab, var(--gold) 10%, transparent),
  0 10px 32px -12px color-mix(in oklab, var(--gold) 18%, rgba(0,0,0,0.55));
border-radius: var(--r);
```

This is the surface every card uses. Adapted from the LetsText dashboard recipe.

### Gold glow (hover, focus)

```css
box-shadow: 0 0 40px 0 color-mix(in oklab, var(--gold) 35%, transparent);
```

### Spotlight bloom (hero)

A radial gradient from the upper-right corner, `#FFE8B8` at ~35% opacity fading to transparent. Used as the lamp source in the cinematic banner and IG profile.
