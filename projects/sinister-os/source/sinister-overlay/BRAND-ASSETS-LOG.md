# BRAND-ASSETS-LOG — Sinister OS overlay branding

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Run UTC:** 2026-05-24T16:38Z
> **Generator attempted:** `D:\Sinister Sanctum\tools\nano-banana\nano_banana\api.py` (Gemini 2.5 Flash Image)
> **Outcome:** API quota exhausted (HTTP 429 `RESOURCE_EXHAUSTED` — "prepayment credits depleted") on first call. All five assets fell back to hand-authored SVG per the spec's rule 5.
> **Total estimated spend this run:** $0.00 (no successful PNG generations)
> **Driver script:** `projects/sinister-os/build/_work/gen-overlay-brand-assets.py` (kept on disk for re-run when credit is refilled)

Per the spec's conservative-balance rules + the SVG-fallback contract, every target path below carries a `.svg` instead of `.png`. The install.sh sibling consumes either extension (see `BRAND-ASSETS-NOTES.md`). Palette is locked to `source/docker-stack/config/theme/sinister-theme-tokens.css`.

| # | Asset slug | Target path | Brief (one-liner) | Cost |
|---|---|---|---|---|
| 1 | `wallpaper-primary` | `usr/share/backgrounds/sinister/wallpaper-primary.svg` | 1920x1080 deep purple-black (`#0e0a1f`) with center radial violet glow + faint embossed `SINISTER` wordmark top-right. | SVG fallback, $0 |
| 2 | `wallpaper-lockscreen` | `usr/share/backgrounds/sinister/wallpaper-lockscreen.svg` | 1920x1080 darker palette (`#08051a`) with single vertical violet light beam centered, no text — greeter overlays its own. | SVG fallback, $0 |
| 3 | `plymouth-background` | `usr/share/plymouth/themes/sinister/background.svg` | 1920x1080 boot splash, wordmark `SINISTER` rendered above center in muted violet (`#8b5cf6` @ 62% opacity); central 200x200 zone left clear for the spinner overlay. | SVG fallback, $0 |
| 4 | `calamares-show` | `usr/share/calamares/branding/sinister/show.svg` | 800x500 Liquid Glass installer card showing a stylized Panel dashboard mockup with `SINISTER OS` header. | SVG fallback, $0 |
| 5 | `sinister-logo` | `usr/share/icons/sinister/sinister-logo.svg` | 512x512 transparent-background wordmark, vertical purple gradient (`#c084fc` → `#8b5cf6`); used by app launchers, GRUB theme, os-release `LOGO`. | SVG fallback, $0 |

## Cached generation attempts

All five Gemini calls failed identically with `429 RESOURCE_EXHAUSTED`. The per-call failure summary is written to `D:\Sinister Sanctum\projects\sinister-generator\outputs\sinister-os\20260524T163847Z-summary.json`. No PNG bytes were ever returned; no cache PNGs were produced.

## Re-run instructions (when API credit is restored)

```powershell
cd "D:\Sinister Sanctum\projects\sinister-os"
python build/_work/gen-overlay-brand-assets.py
```

The driver:
1. Writes PNGs to `projects/sinister-generator/outputs/sinister-os/<UTC>-<slug>.png` (cache).
2. Copies each into the overlay target path with `.png` extension.
3. Writes a JSON summary alongside the cache PNGs.

After a successful PNG run, leave the `.svg` files in place as ultimate fallbacks (or rm them once the PNGs are committed — install.sh prefers PNG when both exist; see `BRAND-ASSETS-NOTES.md`).
