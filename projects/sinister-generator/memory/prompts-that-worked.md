# Prompts that worked

> **Author:** RKOJ-ELENO :: 2026-05-23
> Most-recent first. When a generation produces a keeper, drop the prompt here with its output path + project + UTC. Future agents grep this before starting.

---

## 2026-05-23T07:45Z — JKOR banner-v9 (PIL composite — pixel-perfect)

**Project:** jkor
**Output:** `outputs/jkor/banners/banner-v9.png`
**Model:** `PIL/local` (no LLM call)
**Cost:** $0
**Operation:** `source.sinister_generator.compose.left_aligned_banner(source=v6.png, output=v9.png, canvas_size=(1620,648), canvas_color=(0x1A,0x17,0x29), crop_box=(320,65,1216,665), paste_x=30, feather_right=140)`
**Why it worked:** v6 was already brand-correct (cartoony jester + runic circle + JOKR text + download icon already removed). The only remaining edits were: drop the whimsical caption, kill the neon edge, reshape to 1620x648 wide, deepen the bg palette to match the Command Center sidebar. ALL of those are pure pixel ops — crop + composite + feather. No LLM hallucination risk, no cost. v8 (LLM edit-mode attempt) had inverted the brief (placed v6 as a small inset in a bigger frame); v9 (PIL) nailed it.
**Lesson:** when the brand is already correct in a base image, finish in PIL — don't re-prompt.

---

## 2026-05-23T07:38Z — JKOR banner-v8 (REJECTED — LLM misinterpretation)

**Project:** jkor
**Output:** `outputs/jkor/banners/banner-v8.png` (left in place for now; could move to _rejected/)
**Why it missed:** The LLM treated the "reshape v6 to a wider aspect with character on left + empty right field" instruction as "embed v6 as a smaller inset inside a larger dark frame, with a glowing border around the inset." Lost the layout reshape goal. The character + JOKR + runic circle are intact but contained inside a small rectangle in the top-left of the canvas, framed by a purple aura — exactly the neon edge we were trying to kill.
**Lesson:** for "reshape this canvas" instructions, the LLM often interprets it as "place this on a larger background." For pure aspect-ratio + layout changes, PIL is faster + free + reliable.

---

## 2026-05-23T07:25Z — JKOR banner-v7 (preservation + layout pivot)

**Project:** jkor
**Output:** `outputs/jkor/banners/banner-v7.png`
**Model:** `gemini-2.5-flash-image`
**References:** JKOR source banner + `C:\Users\Zonia\Desktop\ART\banner.png` + Command Center sidebar screenshot
**Why it worked:** prompt was edit-mode AND layout-explicit. Operator's "use ART/banner.png as size+layout template" plus "preserve character from JKOR source" plus "drop whimsical caption + neon edge" got the model to combine the right elements.

```
Generate a wide horizontal banner at 1620x648 pixels (2.5:1 aspect ratio). LAYOUT
(match the second reference image): the character occupies the LEFT third of the
frame, with the remaining right two-thirds being a plain calm purple background
field. Crisp rectangular edges — NO rounded neon glowing border, NO outline
glow, NO decorative frame. CHARACTER (preserve from the first reference image):
the JKOR purple-skinned cartoon demon-jester with cheeky teeth-showing grin,
small horns, gold crown, jester staff with a mini-jester-head bell topper held
in one hand, fan of 4 playing cards in the other hand, purple-and-gold
royal-jester collar with a central gem. Character three-quarter body, facing
camera. BACKGROUND: deep dark sanctum-purple matching a Sinister Command Center
sidebar — base color around #1A1729 to #221944, with very subtle vertical purple
gradient and barely-there cloud-like texture (no swirls, no runes, no sparkles,
no magical particles). The right side stays mostly empty plain dark purple.
TEXT: the JOKR display lettering stays in clean white sans-serif, positioned
centered along the BOTTOM of the canvas under the character. NO other text in
the image. NO whimsical caption at the top. NO download icon anywhere. NO UI
artifacts. Style: clean cinematic digital painting, premium video-game
character-art quality, calm and minimal, the deep purple Sinister Command
Center aesthetic.
```

**Caveats / for next iteration:**
- Aspect came out ~square (Gemini doesn't honor pixel-size). To force wider, pass a wider reference as the FIRST ref.
- Background read slightly more medium-purple than the deep-dark sidebar target. Increase weight on "match the panel sidebar palette" or pass the sidebar screenshot FIRST.

---

## 2026-05-23T07:18Z — JKOR banner-v4/v5/v6 (preservation edits of source)

**Project:** jkor
**Outputs:** `outputs/jkor/banners/banner-v{4,5,6}.png`
**Why they worked (partially):** the "EDIT the attached source banner with TWO minimal changes and PRESERVE EVERYTHING ELSE EXACTLY" pattern produced near-clones of the source with the download icon removed.
**Why they were superseded:** the operator wanted a new layout/size (per ART/banner.png), not just a dim+icon-removal of the original. These remain as a known-good preservation-mode pattern for future "just clean this up" requests.

---

## 2026-05-23T07:13Z — JKOR banner-v1/v2/v3 (REJECTED — over-correction)

**Project:** jkor
**Outputs:** `outputs/jkor/_rejected/banner-v{1,2,3}.png`
**Why they failed:** the brand-lock style suffix said `NO runic symbols, NO swirls, NO sparkles` — which deleted core JKOR brand elements. The output was a "sorcerer prince" instead of a "cartoon demon-jester." Operator: "i hate all of them."
**Lesson codified:** see `docs/WORKFLOW.md` § Lesson 2 (brand-lock describes the brand inclusively).
