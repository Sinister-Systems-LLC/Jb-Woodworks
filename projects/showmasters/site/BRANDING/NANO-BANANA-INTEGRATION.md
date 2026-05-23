<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Nano Banana — Integration Request

Operator (2026-05-23) is wiring up "nano banana" image generation via another agent. This doc lists what the showmasters agent needs to start using it for image generation moving forward.

## What we need

### 1. Auth / access

- **API key** (the secret). Stored as an env var, NOT in any file in this repo. Suggested name: `NANO_BANANA_API_KEY` or whatever convention the master fleet picks.
- **API base URL** (the endpoint host).
- **Org / project ID** if the service is scoped per project.
- **Quota / rate-limit awareness**: any per-minute or per-day request cap we should respect, and what the error response looks like when we exceed it.

### 2. Model / endpoint specifics

- **Which model name** are we calling? (Gemini 2.5 Flash Image? Gemini 2.0 Flash exp? Imagen 4?)
- **Auth header format**: `x-goog-api-key: KEY` vs `Authorization: Bearer KEY` vs query parameter.
- **Request shape**: JSON schema for `prompt`, optional reference-image bytes, aspect-ratio, output count, safety settings.
- **Response shape**: where the image bytes live in the response (base64 inline? URL? streamed chunks?).
- **Supported formats**: PNG / WEBP / JPEG / AVIF? Any preference?
- **Supported sizes**: which dimensions does the API accept (1024×1024, 1024×1792, etc.)?

### 3. Use cases for showmasters specifically

When the integration is live, we'd use nano banana for:

| Use case | Frequency | Notes |
|---|---|---|
| Show photography placeholders | as needed | Dark-canvas event shots — stage lighting, crew silhouettes, behind-the-scenes load-in |
| Service-card hero illustrations | one-time | A custom illustration per service (stagehand / rigger / tech / lift / lead / logistics) in the SMPL gold-on-dark style |
| Blog post header images | 1× per month | One generated hero per monthly blog post (see `MARKETING/06-CONTENT-CALENDAR.md`) |
| Social-post backgrounds | 2× per week | Reels covers + IG carousel slides |
| Location-page hero (orlando.html / fort-worth.html) | one-time | Per-city skyline / venue collage in the brand palette |
| Equipment / gear visualization | as needed | "What's in a road case?" content, "anatomy of a stage rig" diagrams |

### 4. Brand-consistency prompts (the template library)

Once we know the model can accept reference images for style transfer, we'll build a prompt library that always enforces:

- **Color palette**: deep black `#0A0A0F` background, gold gradient `#E8C078 → #D4A24A → #9C7126` accent, white `#FFFFFF` foreground.
- **Lighting**: backlit / volumetric / stage-light feel. Never daylight.
- **Composition**: low contrast in shadows, high contrast on the subject. Cinematic.
- **No emojis, no text in generated images** (typography is done in SVG, not by the model).
- **Always cite the canonical brand** when generating for SMPL: pass `og-card.svg` or `pfp-square.svg` as a reference image for style.

Suggested wrapper helper in code:

```python
def smpl_image(prompt: str, ref_images: list[bytes] = None, size: str = "1024x1024") -> bytes:
    """Generate an SMPL-brand image via nano banana.

    Auto-prepends the brand prompt suffix. Always uses dark/gold palette.
    Returns raw PNG bytes.
    """
    style_suffix = (
        " — cinematic, volumetric stage lighting, deep black background, "
        "gold gradient accent, no text, no emojis, high-contrast subject"
    )
    # ... call nano banana with prompt + style_suffix + ref_images ...
```

### 5. Local fallback when nano banana is unavailable

When nano banana is down or rate-limited, the site must keep working. So:

- All generated images are saved into `public/img/generated/<topic>-<datestamp>.png` on creation.
- The site always references the saved file, NOT a live API call.
- If a fresh generation fails, we use the most recent saved version of that asset.

### 6. Cost expectations

What is the per-image cost? At what volume does it start to matter?

If pricing is metered, give us a monthly budget cap. Suggested initial cap: **$25/month** for the showmasters lane — enough for ~250–1,000 images depending on tier.

### 7. Storage of generated assets

- Local on the workstation, in `public/img/generated/`.
- Each image's prompt + model + timestamp captured in a sibling `*.meta.json` (so we can reproduce / refine later).
- Generated assets are committed to git, NOT regenerated on every build. Determinism matters.

### 8. Anti-slop checks

Before any generated image goes on the site, the showmasters agent visually reviews. Filter rules:

- Reject if any text appears in the image (model hallucinates words).
- Reject if hands / faces look uncanny.
- Reject if lighting reads as "daytime stock photo" rather than stage.
- Reject if there's an emoji or logo-like glyph in the generated content.

When in doubt, regenerate or fall back to a real photograph.

## What we'd do day-one with the integration

When the API key + endpoint land:

1. Generate one hero image per blog post (12 for the year — preload all of them).
2. Generate the per-city skyline hero for orlando.html + fort-worth.html.
3. Build 5 social-post template backgrounds (Reels covers).
4. Add the wrapper helper to `tools/` so any future agent in the lane uses the same brand-locked path.

That's the standby work. Pinging operator when access is provisioned.
