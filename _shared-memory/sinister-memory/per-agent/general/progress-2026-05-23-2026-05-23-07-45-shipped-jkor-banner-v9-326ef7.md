---
format_version: 2
author: RKOJ-ELENO
slug: general
heading_id: 2026-05-23-2026-05-23-07-45-shipped-jkor-banner-v9-326ef7
saved_at: 2026-05-26T21:11:30Z
length: 1130
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# general :: 2026-05-23 07:45 — shipped: JKOR banner v9 (PIL composite, on-spec)

Operator restated brief: "use v6 as a base" + the 4 fixes (drop whimsical text, less-loud bg, no neon edge, match panel palette).

v8 (LLM edit-mode): MISSED — model interpreted "reshape to wider aspect" as "embed v6 as a smaller inset inside a larger dark frame with a glow border." Wrong direction.

v9 (PIL composite): NAILED IT. Cropped v6 tight to character+JOKR+runic-circle (320,65,1216,665), pasted onto a 1620x648 dark-purple #1A1729 canvas at left-aligned position, feathered edges (140px right / 40px left / 30px top+bottom) for seamless blend, subtle vertical gradient on the canvas matching Command Center sidebar. Pixel-perfect brand preservation, zero LLM cost.

Codified the operation as `projects/sinister-generator/source/sinister_generator/compose.py::left_aligned_banner()` so future agents can do the same reshape on any project. Also added `erase_region()` for UI artifact removal (cleanest path for download icons / captions).

Lesson added to prompts-that-worked.md: "when the brand is already correct in a base image, finish in PIL — don't re-prompt."

Spend this session ~$0.31 of $10 (v9 was free).

---
