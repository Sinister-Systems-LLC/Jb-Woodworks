<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# load-in-archetype-v1 — first SMPL win

**Output:** `outputs/showmasters/blog-heroes/load-in-archetype-v1.png`
**Model:** `gemini-2.5-flash-image`
**Cost:** ~$0.039
**Elapsed:** 7.53 s
**TS UTC:** 2026-05-23T08:56:04Z
**References passed:** none (pure prompt + SMPL brand-lock suffix)

## Prompt (verbatim)

```
A single stagehand crew member pushing a wheeled black road case down a dimly lit
backstage corridor of a large arena. Side-lit by amber par-can spill from offstage,
gold rim light catching the road case edge. Volumetric atmospheric haze. Concrete
floor catches a soft gold reflection. Crew member shown as a silhouette mid-stride,
in plain black work clothes, no logos. Composition: subject in the left third,
corridor recedes to a vanishing point on the right, faint stage lighting glowing
in the far distance. Cinematic, photographic realism, painterly atmosphere.
```

(The `smpl_image()` helper auto-appends `SMPL_STYLE` from `nano_banana/api.py`.)

## Why it worked

- Brand-lock suffix delivered exactly what the brand spec asks for: deep-black room, amber/gold pool on subject, no text/logos/daylight.
- Prompt gave Gemini a clear single subject (crew member), a verb (pushing), a location (corridor), a light direction (offstage left amber), a composition rule (left third + vanishing-point right), and a register (cinematic, photographic, painterly).
- Zero reference images — proves the brand-lock suffix alone is strong enough for the SMPL archetype. Reference images become important when we need exact aspect ratio (e.g. 21:9 wide hero strip) or palette anchoring on subjects further from the archetype.

## Aspect note

Output: 1024×1024 (square). For wide blog heros at 21:9 we'll need to pass a wide reference image as the FIRST ref (per WORKFLOW Lesson 6). PIL crop on this image to a wide strip is an option too — though the composition was built for square; cropping wide would lose the floor reflection.

## Lessons confirmed

- "One image first, get a thumb" workflow held — no $0.12 wasted on assumed variants.
- Brand-lock suffix is INCLUSIVE (per WORKFLOW Lesson 2) — describes the SMPL look, doesn't strip elements.
- Operator-visible path on the satellite junction: `C:\Users\Zonia\Desktop\Sinister Generator\showmasters\blog-heroes\load-in-archetype-v1.png`.

## Direction lock proposal (pending operator 👍 / 👎)

If approved:
1. Fire 2 variants of this archetype (different subject pose / different corridor depth) at 21:9 aspect using `og-card.svg` as first ref + a wide reference image.
2. Move on to the second day-one subject — rigger-in-truss service-card hero.

If rejected: re-brief, single re-fire, no variants.

## 2026-05-23T09:00Z update — direction confirmed by use

Operator did not 👎; instead asked for "complete everything" + "spice up the hero." Treating that as direction-lock. Subsequent batch (6 service-cards + 2 city + 5 social + 11 blog headers = 24 more images, all status=ok, ~$0.94 total) all use the same SMPL_STYLE brand-lock. Same dark+gold archetype across the line.

Winning patterns:
- Single subject (or empty scene), left-third composition
- "Volumetric stage lighting" / "amber par-can spill" / "gold rim light" → reliable brand-lock
- Subject as silhouette / rim-lit not portrait — preserves the "crew not artist" doctrine
- Wide horizontal hero strips can be described with "wide horizontal shot of..." even though Gemini delivers ~square output; PIL crop or `object-fit: cover` finishes the aspect
- For empty-canvas social templates: describe the LIGHT, not the SUBJECT — Gemini delivers clean negative-space layouts for typography overlay
