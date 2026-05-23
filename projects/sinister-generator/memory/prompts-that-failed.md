# Prompts that failed

> **Author:** RKOJ-ELENO :: 2026-05-23
> Most-recent first. Every prompt that produced a rejected output. Cite WHY it missed so future prompts skip the trap.

---

## 2026-05-23T07:13Z — JKOR banners v1/v2/v3 (over-correction)

**Outputs:** `outputs/jkor/_rejected/banner-v{1,2,3}.png`
**Prompt theme:** "clean cinematic digital painting, deep near-black background, subtle Sanctum-purple glow, minimal, calm, premium video-game UI art quality... NO busy patterns, NO runic symbols, NO swirls, NO sparkles, NO magical particles"
**Why it missed:** The "NO" list stripped out the brand's core visual elements. The runic circle, the swirls, the sparkles — those ARE the JKOR brand. Reading "less loud" as "remove them" was wrong.
**Operator reaction:** "i said to use this as a fucking base. not change the entire look. i hate all of them"
**Lesson:** Brand-lock suffixes must describe what the brand IS, not enforce a contradictory aesthetic. See `docs/WORKFLOW.md` § Lesson 2.

---

## Patterns to avoid

1. **Aggressive NO-lists in the brand-lock suffix.** Negative directives belong in the per-call prompt, not in the durable brand-lock.
2. **Promising pixel dimensions in the prompt.** Gemini 2.5 Flash Image ignores them — it picks aspect based on reference images and content. To force aspect, pass a reference image of the target aspect.
3. **Reading the brief interpretively.** "Less loud" can mean "dim by 20%" OR "remove half the elements" — always default to the minimal interpretation when the brief is ambiguous.
4. **Generating multiple variants before confirming direction.** One first, get a thumb, THEN variants.
5. **Skipping reference images.** Gemini drifts toward training-data analogs without anchors.
