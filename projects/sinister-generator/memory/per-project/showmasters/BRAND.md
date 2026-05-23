<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Showmasters (SMPL) — brand spec for image generation

> Pulled from `C:\Users\Zonia\Desktop\Showmasters Site\BRANDING\NANO-BANANA-INTEGRATION.md` + `BRANDING/TOKENS.md`. Future agents read this BEFORE firing.

## One-line brand
Show Masters Production Logistics — the people backstage who make great-day events happen. Stagehands, riggers, technicians, lift operators, crew leads, logistics. Quiet competence under stage lighting.

## Palette (binding)

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0A0A0F` | deep black background (almost never pure black) |
| `--gold-light` | `#E8C078` | top of gold gradient (highlights, key light) |
| `--gold` | `#D4A24A` | canonical accent (logo gold, lighting accent) |
| `--gold-dark` | `#9C7126` | bottom of gradient (shadow gold, amber depth) |
| `--fg` | `#FFFFFF` | foreground / subject highlight |

The dark-and-gold split is the brand. Reject any output that drifts into cool blue, magenta, or daylight white-balance.

## Visual mood (what the brand IS — inclusive, per WORKFLOW Lesson 2)

- **Stage-lit, never daylight.** Volumetric par-can light, backlight haze, atmospheric fog used like an instrument.
- **Crew as silhouette / half-shadow.** People backstage are skilled professionals, NOT the focal point — the SHOW is. So crew are most often rim-lit, in motion, mid-task. Faces seldom centered.
- **Industrial premium.** Black road cases, anodized aluminum trusses, neatly run cables, immaculate stage tape. Things look new, organized, capable.
- **Big rooms.** Arenas, theaters, ballrooms, festival fields at dusk. Negative space matters — empty seats lit by stage glow, cathedral-tall ceilings, sweeping camera height.
- **In motion / in progress.** Load-in, focus call, last sound-check, intermission turnaround. Never empty / static.

## Subjects we'll generate

Anchored on the day-one work-list:

1. **6× service-card heroes** — stagehand, rigger, technician, lift operator, crew lead, logistics. Each is a brand-archetype shot (one person mid-task, dark venue, gold lighting). Aspect: 4:3 or 16:10.
2. **12× blog header heroes** — one per content-calendar month. Topics include: load-in checklist, ACA compliance, the road-case lifecycle, what a focus call looks like, hub vs office, etc. Aspect: 21:9 (wide hero strip).
3. **2× city hero strips** — Orlando + Fort Worth. Stylized skyline at dusk with a faint stage-light glow from the venue district. Aspect: 21:9.
4. **5× social templates** — Reels covers (9:16), IG carousel slides (1:1), one quote-card layout. Solid background = `#0A0A0F` with a single gold highlight; layout-empty for typography overlay later in the DOM (text NEVER baked in per anti-slop rule).

## Anti-slop overrides (merge with `docs/ANTI-SLOP.md`)

In addition to the fleet checklist, reject SMPL generations that:

- Read as "concert photographer" stock photo — too clean / too generic / over-saturated reds and purples.
- Show daylight or natural sun on the subject (kills the brand).
- Render hands holding cables in unnatural grips (very common Gemini fail).
- Center the artist / performer rather than the crew. The brand is BACKSTAGE.
- Include any text, signage, or banded "press" labels in-frame.
- Include any logo (no SMPL wordmark in image; that's overlaid later in SVG).

## Reference image set

Located at `reference/` next to this file:

- `og-card.svg` — canonical OG card, palette anchor
- `pfp-square.svg` — IG-style square brand mark
- `logo-horizontal.svg` — wordmark (for palette only — DO NOT generate near a logo)
- `us-coverage-map.svg` — stylized US silhouette in brand colors (palette anchor)

When firing a generation, default to `og-card.svg` as the first reference for style transfer on most subjects. For city heros, also pass `us-coverage-map.svg` so the dark-gold map aesthetic carries through.

## Prompt cookbook (starter templates)

### Service-card hero — stagehand
```
A single stagehand crew member pushing a wheeled black road case down a dimly lit
backstage corridor of a large arena. Side-lit by amber par-can spill from offstage,
gold rim light on the road case edge. Volumetric atmospheric haze. Concrete floor
catches a soft gold reflection. Crew member shown as a silhouette mid-stride, in
black work clothes, no logo. Composition: subject in left third, corridor recedes
to a vanishing point on the right, faint stage lighting glowing in the distance.
Cinematic, photographic realism.
```

### Service-card hero — rigger
```
A rigger high in the truss above a darkened arena, securing a chain motor to a
beam, viewed from a low upward angle. Gold key light from a follow-spot below
catches the worker and the truss geometry. Deep black void behind. Composition:
rigger occupies the upper third, truss diagonals frame the shot, empty venue
seats barely visible far below.
```

### Blog header — load-in checklist
```
Wide horizontal shot of a half-loaded arena stage at the start of load-in.
Several stagehands moving cases, one technician focused on a console at front
of stage, scattered amber work lights, the venue mostly dark with one cool
white house light still on far stage right. Camera at audience-level height,
slightly off-center. Aspect 21:9, deep negative space top and right for
typography overlay.
```

### City hero — Orlando
```
Cinematic dusk skyline of Orlando, Florida, viewed across Lake Eola or from
a low rooftop. Tall buildings as black silhouettes against a deep gradient sky
that fades from dark navy at top to warm gold at the horizon. A faint pinpoint
of amber stage-light glow concentrated in the lower right (suggesting the
production / entertainment district). No people, no text, no logos. Painterly
photoreal, 21:9 wide.
```

### Social template — Reels cover (9:16)
```
Vertical 9:16 deep black canvas with a single offset cone of warm gold stage
light entering from upper right and pooling in the lower left third. No subject,
no text. Composition deliberately empty for typography overlay in the DOM later.
The canvas should feel like the moment before a show starts — anticipation,
not a scene.
```

## Cost ceiling

Soft budget: $25 / month per ops doc. At $0.039/image that's ~640 images, so we have far more headroom than needed for the day-one list. Goal: one well-aimed first shot, two locked-direction variants = ~$0.12/round.

## Operator interaction protocol (per WORKFLOW.md)

1. Fire ONE image. Save with meta sidecar. Surface the path + a one-line description.
2. Operator drops 👍 / 👎.
3. On 👍: fire 2 variants for selection, then move to next subject.
4. On 👎: don't fire variants — re-think the brief, then try ONE again.
5. Winners → drop the prompt into `_prompts/<output-name>.md` here so the next agent doesn't start blind.

## See also
- `D:\Sinister Sanctum\_shared-memory\knowledge\nano-banana-gemini-image.md` — fleet brain entry
- `D:\Sinister Sanctum\projects\sinister-generator\docs\WORKFLOW.md` — workflow doctrine
- `D:\Sinister Sanctum\projects\sinister-generator\docs\ANTI-SLOP.md` — base anti-slop checklist
- `C:\Users\Zonia\Desktop\Showmasters Site\BRANDING\NANO-BANANA-INTEGRATION.md` — Showmasters-side contract
