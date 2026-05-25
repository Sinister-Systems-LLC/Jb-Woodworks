# Prompts that worked

> **Author:** RKOJ-ELENO :: 2026-05-23
> Most-recent first. When a generation produces a keeper, drop the prompt here with its output path + project + UTC. Future agents grep this before starting.

---

## 2026-05-23T12:50Z — JKOR CORRECTED canonical (primary-banner-driven character lock)

**Project:** jkor
**Output:** `outputs/jkor/pfp/peeking-CORRECT-canonical-2026-05-23T125049Z.png` (1024×1024)
**Model:** `gemini-2.5-flash-image`
**Cost:** $0.039
**Refs (order matters):**
1. `memory/per-project/jkor/reference/00-PRIMARY-BANNER-canonical-*.jpg` — operator-canonical look-of-record
2. `memory/per-project/jkor/reference/01-peeking-pose-reference-*.jpg` — peeking-over-banner pose cue

**The critical correction this entry captures:** earlier 8 gens this session used `00-base-banner-original.png` + the misread BRAND.md spec as the "canonical" — that produced purple-skinned demon-jester w/ wide showing-teeth grin and mini-jester-head-bell staff. Operator pushed back ("I want these exact same look and character" — pointing at `primary-banner.jpg`). The ACTUAL canonical is very different:

| Trait | Misread (earlier 8 gens) | CORRECT (primary-banner.jpg) |
|---|---|---|
| Face | purple skin | pale white / porcelain mask |
| Mouth | wide showing-teeth grin | closed-mouth smirk |
| Eyes | large bright purple irises | small narrow dark eyes |
| Horns | small, easy to miss | LARGE prominent dark-purple |
| Staff | mini-jester-head bell | heart-shaped glowing gem |
| Cards | plain card faces w/ suits | swirl-pattern magic backs |
| Gloves | bare hands | WHITE GLOVES |
| Background | calm deep purple-navy | vibrant runic-circle + paisley |

**Key prompt moves that worked:**
1. Pass `primary-banner.jpg` as ref[0] (Gemini biases toward ref[0] for style transfer)
2. Pass `peeking-pfp.jpg` as ref[1] (POSE only — explicitly call out "look from ref[0], pose from ref[1]")
3. `style_suffix=None` — do NOT pass `JKOR_STYLE` from nano-banana. That suffix encodes the misread (purple skin, teeth grin, jester-head staff) and will fight the ref-driven look.
4. Spell out the trait deltas: skin color (white mask), mouth (closed smirk, no teeth), held items (heart-staff + magic-card backs, not jester-head + plain cards), gloves (white).

**Known weakness:** the horns came back partially obscured by the jester hat. Cure for v2: emphasize "TWO LARGE prominent dark-purple horns extending VISIBLY BEYOND the jester hat — they should be the most prominent feature above the head, NOT covered by hat prongs."

**Lesson 1:** when the LLM-suffix encodes the wrong canonical, drop it entirely (`style_suffix=None`) and let the references drive. Don't try to layer correct prompts on top of an incorrect suffix.
**Lesson 2:** verify the canonical reference by viewing it BEFORE building the prompt. I spent 8 gens × $0.039 = $0.312 because I trusted BRAND.md's text description instead of looking at the actual operator-canonical image.

---

## 2026-05-23T12:12Z — JKOR demon-jester peeking-pfp v2 (text-free PFP)

**Project:** jkor
**Output:** `outputs/jkor/pfp/peeking-jkor-regen-v2-2026-05-23T121226Z.png` (1024×1024)
**Model:** `gemini-2.5-flash-image`
**Cost:** $0.039 (v1 also $0.039 — rejected for baked text; total $0.078 for the iterated keeper)
**Refs (order matters — Gemini biases toward ref[0] for style transfer):**
1. `memory/per-project/jkor/reference/00-base-banner-original.png` — canonical look-of-record
2. `memory/per-project/jkor/reference/peeking-pfp-operator-supplied-2026-05-23T120707Z.jpg` — operator-supplied pose cue

**Why v2 worked / v1 failed:** v1 used `nano_banana.JKOR_STYLE` verbatim. That suffix contains a stale line: *"The JOKR display lettering stays where the source has it"* — outdated relative to JKOR BRAND.md's *"text NEVER baked in"* doctrine. Model honored the suffix and stamped a giant "JOKR" wordmark across the bottom. v2 overrode the suffix with a corrected `JKOR_STYLE_NO_TEXT` (drops the JOKR-lettering line, adds explicit "ABSOLUTELY NO text, NO letters, NO logos, NO wordmarks anywhere in the image") + triple-redundant no-text emphasis in the prompt body (top-priority bullet block + repeated reminders + final summary line). Model honored it cleanly.

**Proven prompt structure (reusable for any JKOR demon-jester PFP):**

1. Open with composition + pose specifics (square, peeking, head+shoulders, hands on edge, grin)
2. **TOP-PRIORITY block** repeating the no-text rule three different ways before any other instruction
3. LOCKED CHARACTER TRAITS block with hex codes for skin / eye / crown / collar / gem
4. POSE block referencing ref[1]
5. BACKGROUND block (calm purple-navy, no runes, no sparkles)
6. Style closing
7. FINAL REMINDER line reiterating no-text rule (model honors instructions at the end more reliably than the middle)

**Followup needed:** patch `tools/nano-banana/nano_banana/api.py :: JKOR_STYLE` to drop the JOKR-lettering line so future calls don't need this override. Filed as anti-pattern.

**Lesson:** if a brand style suffix says "X stays where the source has it" and the source contains baked text, the model will repeat that text every time. Audit suffixes for "stays where" / "preserve" clauses that bind to source artifacts that shouldn't propagate.

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
