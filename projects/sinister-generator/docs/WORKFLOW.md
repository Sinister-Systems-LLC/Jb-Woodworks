# Sinister Generator — workflow audit & lessons learned

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Trigger:** Operator-requested audit during the JKOR banner session. Two over-corrections cost ~$0.24 + a frustrated "I hate all of them" before the brief finally landed.

## The pattern we landed on (after stumbling into it)

### 1. "Use this as a base" = **edit mode**, not generate mode

When the operator hands over a source image and says "use this as a base," they mean:

- Preserve 95% of the artwork
- Make only the explicitly-named changes
- Treat the prompt as an instruction to *the model that's about to edit a file*, not as a description of a scene to invent

What I did wrong on round 1: I read "make the background less loud" as "remove the runic-circle backdrop entirely," lost the cartoony jester face, lost the JOKR text, lost the staff-with-jester-topper. Result: 3 banners that looked like a totally different brand. Operator's reaction: "i said to use this as a fucking base. not change the entire look."

**Cure:**

- Prompt explicitly: "EDIT the attached source image with N minimal changes and PRESERVE EVERYTHING ELSE EXACTLY."
- Enumerate the changes literally (not interpretively): "Remove the small white download icon at bottom-right" beats "clean up the UI clutter."
- Enumerate what to KEEP — the character, the text, the composition, the palette.

### 2. Brand-lock style suffixes must be INCLUSIVE of the brand, not enforce a new look

The first `JKOR_STYLE` suffix I wrote included `NO runic symbols, NO swirls, NO sparkles, NO magical particles` — those were *part of the JKOR brand*, but I'd misread "less loud" as "remove them." The suffix turned every JKOR generation into a stripped-down sorcerer portrait.

**Cure:**

- Brand-lock suffixes describe what the brand IS, not what it isn't.
- Use the source artwork as the canonical reference for what "the brand" looks like.
- Negative directives go on the prompt for THAT specific generation, not in the brand-lock.

### 3. One banner first, then variants — never burn $0.12 on assumed direction

The first round I fired all 3 variants in one shot. All 3 missed the brief. Cost: $0.12 + an angry operator. Burning multiple variants only pays off AFTER the direction is locked.

**Cure:**

- Generate one. Show. Get a thumb (good direction / wrong direction).
- Only fire variants (2-3 more) once the direction is confirmed.
- If the first one is wrong: don't fire variants — re-think the brief, then try again with one.

### 4. For UI artifact removal (download icons, captions, watermarks), prefer PIL over re-generation

The download icon at bottom-right could have been erased with 5 lines of PIL — pixel-perfect, zero risk of the model re-imagining anything else. Re-generating with "preserve everything else" works ~70% of the time; PIL works 100%.

**Cure:**

```python
from PIL import Image
im = Image.open("source.png")
bg = im.getpixel((10, im.height - 20))
for x in range(im.width - 60, im.width - 10):
    for y in range(im.height - 50, im.height - 10):
        im.putpixel((x, y), bg)
im.save("cleaned.png")
```

For complex artifacts: `cv2.inpaint()` works without an LLM call.

### 5. References are positional — for edits, image-first beats prompt-first

Our wrapper currently passes `[prompt, ref1, ref2, ...]`. For pure style-transfer this is fine. For edits, the Gemini API responds better to `[image_to_edit, prompt, optional_extra_refs]` — it more strongly treats the first image as the canvas being edited.

**Cure (TODO in wrapper):** add an `edit_of=` parameter that puts the image first.

### 6. Aspect-ratio is NOT controllable via pixel-count in the prompt

I asked for `1620x648 (2.5:1)` and got a ~square output. Gemini picks the aspect based on the prompt's content and the reference images' aspects. To get a wide banner:

- Pass a wide reference image (the model strongly biases toward matching ref aspect)
- Describe the layout positionally ("character occupies left third, right two-thirds is empty background")
- Don't expect pixel-exact output

**Cure:** Always pass a wide reference if you want a wide output. Post-process with PIL to crop/resize to exact dimensions if needed.

### 7. Cost discipline

`gemini-2.5-flash-image` is ~$0.039/image. A 3-variant explore = ~$0.12. A 10-variant sweep = ~$0.40. The cost ceiling is rarely the budget — it's the **operator's attention budget**. Every variant they have to look at and reject is friction. Aim for: one well-aimed first shot, two locked-direction variants. Total: ~$0.12 per round.

## The new workflow (do this from now on)

```
1. Read the operator's brief literally. Underline what to KEEP and what to CHANGE.
2. Identify the artifact mode:
   - "Use this as a base" / "Edit this" / "Fix only X" → edit mode
   - "Make me a new X" / "Generate a fresh Y" → generate mode
3. EDIT MODE:
   a. If only UI artifacts (icons, captions) need removing → PIL surgical erase, no model call.
   b. Otherwise: write prompt as "EDIT the attached source with these N changes and PRESERVE EVERYTHING ELSE EXACTLY."
   c. Pass the source as the FIRST reference image.
   d. Fire ONE generation. Show. Get a thumb.
4. GENERATE MODE:
   a. Find the closest existing reference (per-project memory or canonical brand art).
   b. Apply the brand-lock suffix (--brand jkor / smpl / jbw).
   c. Fire ONE generation. Show. Get a thumb.
5. Once direction is confirmed: fire 2 variants for selection.
6. Visual review against the anti-slop checklist (docs/ANTI-SLOP.md) before saving as final.
7. Write the prompt + meta sidecar. Commit both.
```

## Per-project memory layer

Every project (JKOR / Showmasters / JB Woodworks / future) gets a folder at `projects/sinister-generator/memory/per-project/<slug>/` with:

- `BRAND.md` — visual spec (palette, character, anti-slop)
- `reference/` — canonical source images for that brand
- `_prompts/` — every prompt that worked, named by output

When a new generation succeeds, add the prompt to `_prompts/` so future agents (or future-you) can grep "what's worked for JKOR banners" instead of starting blind.

## Operator interaction protocol

- **Surface results immediately** — don't queue 5 generations and report at the end. Show the first, get a thumb, then continue.
- **Be honest about misses** — if the model hallucinated a hand, ate the text, or re-imagined the brand, say so before the operator has to spot it.
- **Don't ask permission for variants once direction is locked** — operator's auto-mode said "execute, don't ask." Variants of a confirmed direction = action, not a decision.
- **Always log the prompt** — `.meta.json` sidecar + (for winners) a copy into `memory/per-project/<slug>/_prompts/`.

## Anti-patterns codified

1. Reading "less loud" as "remove the design language."
2. Brand-lock style suffix that EXCLUDES the brand's actual visual elements.
3. Firing 3 variants of an unconfirmed direction.
4. Re-generating to remove a UI artifact when PIL would do it pixel-perfect.
5. Promising a specific pixel dimension via the prompt (Gemini ignores it).
6. Skipping the visual-review step (anti-slop) before showing the operator.
7. Leaving rejected variants in `generated/` next to the keepers (always move to `_rejected/`).

## TL;DR

- **How we won (after stumbling):** one banner at a time, edit mode for "use as base," PIL for icon removal, brand-lock describes the brand inclusively.
- **What changed in the wrapper:** `JKOR_STYLE` rewritten to be inclusive. `edit_of=` param is TODO.
- **What's now in place:** per-project memory under `memory/per-project/<slug>/`, outputs routed to `outputs/<slug>/<type>/`, Desktop satellite junction so the operator browses results without leaving the Desktop.
