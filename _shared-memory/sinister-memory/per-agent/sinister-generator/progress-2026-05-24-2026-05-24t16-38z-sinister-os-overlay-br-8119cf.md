---
format_version: 2
author: RKOJ-ELENO
slug: sinister-generator
heading_id: 2026-05-24-2026-05-24t16-38z-sinister-os-overlay-br-8119cf
saved_at: 2026-05-26T21:11:30Z
length: 1372
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# sinister-generator :: 2026-05-24T16:38Z — sinister-os overlay brand pack ATTEMPTED — 0/5 PNG (API quota), 5/5 SVG fallback shipped — spend $0.00

Lane: `sinister-os` (docker-stack docket) consumed the generator. Brief: 5 brand assets for the OS overlay — `wallpaper-primary`, `wallpaper-lockscreen`, `plymouth-background`, `calamares-show`, `sinister-logo`. Driver: `projects/sinister-os/build/_work/gen-overlay-brand-assets.py` (kept on disk for re-run when credit returns).

**Outcome (verified):** every one of the 5 Gemini 2.5 Flash Image calls returned `429 RESOURCE_EXHAUSTED` — "prepayment credits depleted, manage at ai.studio". Zero PNG bytes returned. **Total estimated spend this task: $0.00.** Per-call failure summary written to `projects/sinister-generator/outputs/sinister-os/20260524T163847Z-summary.json`.

**Fallback (verified):** all 5 assets hand-authored as palette-locked SVGs at the same overlay paths (`.svg` instead of `.png`), all > 700 bytes, all referencing `--bg #0e0a1f / --accent #c084fc / --accent-strong #8b5cf6` from `sinister-theme-tokens.css`. Handoff doc for sibling install.sh: `source/sinister-overlay/BRAND-ASSETS-NOTES.md` (PNG-or-SVG resolver helper + `rsvg-convert` recipe for Plymouth). Per-asset ledger: `source/sinister-overlay/BRAND-ASSETS-LOG.md`.

**Operator-visible:** API key in env (`GEMINI_API_KEY`) is valid but the underlying Google AI Studio project is out of prepaid credit. Refill at https://ai.studio/projects then re-run the driver to upgrade SVG → PNG.

---
