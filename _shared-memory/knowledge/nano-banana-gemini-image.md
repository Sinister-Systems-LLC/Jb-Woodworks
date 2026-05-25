<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# nano-banana — Gemini 2.5 Flash Image (fleet-wide image generation)

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Status:** workaround (key not yet set; tool ready)
> **Tags:** image-generation, gemini, nano-banana, google-genai, showmasters, jb-woodworks, fleet-wide, standing-rule, gemini-2.5-flash-image

## Problem

The fleet had no first-party way to generate images. Showmasters had drafted a contract doc (`BRANDING/NANO-BANANA-INTEGRATION.md`) listing the shape it wanted, but nothing was wired. JB Woodworks was about to hit the same wall on hero / portfolio / blog imagery. Operator owns a Gemini Pro account with the Nano Banana feature (Gemini 2.5 Flash Image) and wanted it installed so every agent can call it.

## Why

- **Gemini 2.5 Flash Image** ("Nano Banana") is Google's multimodal image generation model. Accepts text prompts plus optional reference images for style transfer. Returns inline image bytes (no URL fetch).
- The official SDK is `google-genai` (Python 3.10+). The older `google-generativeai` is being retired.
- Default model id: `gemini-2.5-flash-image`. Subject to change as the feature graduates to GA.
- Costs are per-image, billed to operator's Gemini Pro account. No per-key tiering at the SDK layer — quota is account-wide.

## Fix

`tools/nano-banana/` is the fleet-wide wrapper. Every agent (sanctum master, showmasters, jb-woodworks, future lanes) imports the same module:

```python
from nano_banana import generate, smpl_image, jbw_image
```

- `generate(prompt, output_path, ref_images=None, style_suffix=None, model=DEFAULT_MODEL)` — base generation.
- `smpl_image(prompt, output_path, ref_images=None)` — Showmasters brand-lock (dark + gold gradient stage-light style).
- `jbw_image(prompt, output_path, ref_images=None)` — JB Woodworks brand-lock (premium wood close-up, gold-on-black, photoreal).

CLI: `python -m nano_banana --prompt "..." --output out.png [--brand smpl|jbw] [--ref ref1.png]`.

Every successful call writes the PNG AND a `<output>.png.meta.json` sidecar (prompt, model, UTC, elapsed, ref count, image byte size, text excerpt). Commit both together when saving into a project repo.

### Env var resolution order

1. `GEMINI_API_KEY` (canonical — what the SDK reads by default)
2. `NANO_BANANA_API_KEY` (alias kept for Showmasters' contract doc)
3. `GOOGLE_API_KEY` (additional fallback)

The wrapper raises `RuntimeError` with the setx command if none are set.

### Install steps (operator-side, one-time)

1. `pip install google-genai` (master `general` lane ran this 2026-05-23 — pre-installed for the fleet)
2. `[Environment]::SetEnvironmentVariable('GEMINI_API_KEY','<key>','User')` (operator must do this — see OPERATOR-ACTION-QUEUE 🟠 High)
3. Restart any open Claude Code / PowerShell sessions

### Brand-lock style suffixes

| helper | appended style |
|---|---|
| `smpl_image()` | cinematic volumetric stage lighting, deep black bg `#0A0A0F`, gold gradient `#E8C078 -> #D4A24A -> #9C7126`, high-contrast subject, no text, no emojis, no logos |
| `jbw_image()` | premium craftsmanship, hand-finished wood close-up, warm gold `#c9a84c` on `#080808`, soft directional light, photoreal, no text, no emojis, no plastic / faux finishes |

Future lanes should add their own brand-lock helper next to `smpl_image` / `jbw_image` rather than hand-rolling the suffix in callers.

## Discoveries

### 2026-05-23 07:35 by general (EVE) — promoted to a project (sinister-generator)

- `tools/nano-banana/` stays as the SDK wrapper.
- `projects/sinister-generator/` is now the application layer: per-project routing, memory, audit, docs, output organization.
- Operator satellite: `C:\Users\Zonia\Desktop\Sinister Generator\` (NTFS junction → `projects/sinister-generator/outputs/`). Operator browses every project's outputs from the desktop.
- Per-project memory at `projects/sinister-generator/memory/per-project/<slug>/` carries the brand spec + reference images + winning prompts.
- 3 projects registered: jkor, showmasters, jb-woodworks. Adding a new project: see `projects/sinister-generator/docs/BRAND-PACK-SPEC.md`.
- Workflow audit doc at `projects/sinister-generator/docs/WORKFLOW.md` — 7 lessons codified from the JKOR over-correction incident this session.
- Visual review checklist at `docs/ANTI-SLOP.md`.
- Anti-pattern added: #11 — brand-lock style suffix that excludes the brand's own visual elements. (See JKOR v1/v2/v3 rejected for the empirical anchor.)

### 2026-05-23 07:10 by general (EVE) — model name correction + billing-tier discovery

- DEFAULT_MODEL corrected from `gemini-2.5-flash-image-preview` (404 NOT_FOUND) to `gemini-2.5-flash-image` (GA). Verified via `client.models.list()` — the `-preview` name has been retired since GA shipped.
- Available image-capable models on the operator's key today: `gemini-2.5-flash-image` (canonical Nano Banana GA), `gemini-3-pro-image-preview` (Nano Banana Pro newer / more capable), `nano-banana-pro-preview` (alias), `gemini-3.1-flash-image-preview`, `imagen-4.0-{generate,ultra-generate,fast-generate}-001` (Imagen models — different endpoint: `predict` not `generateContent`; our wrapper only supports `generateContent`, would need a separate adapter for Imagen).
- **Free tier == zero for image generation.** Even with a valid `AIza...` key, the linked Cloud project must have billing enabled OR every image-model `generateContent` call returns `429 RESOURCE_EXHAUSTED` with `limit: 0`. Operator-action: enable billing on the project at `https://console.cloud.google.com/billing` (operator's project shown in the AI Studio key-details modal — project number is the canonical identifier).
- Anti-pattern added below (#9 — never assume free-tier covers image gen; always surface the billing gate as the first diagnosis on `RESOURCE_EXHAUSTED`).

### 2026-05-23 06:55 by general (EVE)

Initial ship.

- `tools/nano-banana/` populated with package + CLI + README + smoke bat + .env.example + AUTHOR + pyproject.
- `google-genai` installed at the system Python (3.12.10).
- Showmasters' integration contract (`BRANDING/NANO-BANANA-INTEGRATION.md`) honored: dark+gold brand-lock helper, on-disk meta sidecar, fallback-to-local-file pattern (commit generated assets, never live-fetch on page render).
- Inbox messages dropped to `showmasters` + `jb-woodworks` announcing availability.
- OPERATOR-ACTION-QUEUE updated: 🟠 set `GEMINI_API_KEY` env var (one-line setx command included).
- `docs/ENV-VARIABLES.md` extended with `GEMINI_API_KEY` section.

Not tested yet — needs the key. Tool is wired correctly per the SDK docs but only a live key proves the response-parsing path (inline_data → bytes). First live generation will confirm.

### Anti-patterns to avoid

1. **Don't accept the API key as a function parameter.** Always read from env. Keys leak when callers persist their kwargs in resume-points or logs.
2. **Don't live-fetch on page render.** Generate once, save to `<project>/public/img/generated/<topic>-<datestamp>.png`, commit the file, reference the file in HTML. Otherwise every page load hits the API.
3. **Don't bake text into images.** Nano Banana hallucinates words. Typography stays in SVG / DOM. Brand-lock suffixes enforce `no text in image`.
4. **Don't skip the meta sidecar.** Future agents need to reproduce or refine without re-deriving the prompt.
5. **Don't roll a per-lane wrapper.** Add a brand-lock helper into `nano_banana/api.py` and import it. Keeps the env-var resolution + response parsing + sidecar logic in one place.
6. **Don't commit `.env`.** Only `.env.example`. Operator sets the user env var; nothing per-project.
7. **Don't assume `inline_data.data` is bytes.** The SDK sometimes returns base64-encoded `str`. The wrapper's `_normalize_refs` + response loop handles both — keep that branch.
8. **Don't push generated images you haven't visually reviewed.** Showmasters' anti-slop rules (reject hallucinated text / uncanny faces / daylight stock-photo feel) apply fleet-wide.
9. **Don't assume the free tier covers image generation.** It doesn't. `gemini-2.5-flash-image` (and every other image-gen model) requires billing enabled on the linked Cloud project. A valid `AIza...` key + free-tier billing = `429 RESOURCE_EXHAUSTED` with `limit: 0`. First diagnosis on 429: send the operator to `https://console.cloud.google.com/billing` to attach a payment method to the project number from the AI Studio key-details modal. Don't waste a turn trying a different model id — every image model has the same gate.
10. **Don't use the `-preview` model id after a model goes GA.** `gemini-2.5-flash-image-preview` 404s today; `gemini-2.5-flash-image` is the correct GA name. Same pattern likely for the rest as they graduate. Verify the current name via `client.models.list()` if a 404 fires.
11. **Don't put brand-killing NO-lists in the brand-lock style suffix.** Negative directives belong in the per-call prompt. The brand-lock suffix is durable — it lives in `api.py` and applies to EVERY generation for that brand. If the suffix says "NO runes" but the brand HAS runes, every future generation is broken. Empirical anchor: JKOR v1/v2/v3 (rejected) — initial `JKOR_STYLE` had `NO runic symbols, NO swirls, NO sparkles` which stripped the cartoony brand entirely. Cure: suffix describes what the brand IS (inclusive), not what it isn't.
12. **Don't fire 3 variants of an unconfirmed direction.** One image first, get a thumb, then variants. Empirical anchor: $0.12 burned on 3 wrong-direction JKOR banners before realizing the brief was wrong. The model's cost isn't the bottleneck — the operator's attention is.
13. **Don't trust pixel-dimension instructions in the prompt.** `gemini-2.5-flash-image` ignores `1620x648` and picks aspect from reference-image content and prompt semantics. To force a wide aspect: pass a wide reference image as the FIRST ref. Post-process with PIL for exact pixel dimensions.

## Composes with

- `agent-identity-eve` (every lane caller identifies as EVE-on-<lane>)
- `operator-hard-canonical-authorship-RKOJ-ELENO` (file authorship)
- `forever-expanding-modular-architecture-doctrine` (one disk surface, brand-lock helpers as extension points)
- Showmasters' `BRANDING/NANO-BANANA-INTEGRATION.md` (per-lane contract honored)
- `docs/ENV-VARIABLES.md` (new `GEMINI_API_KEY` section)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` (env-var gate)
