"""Generate JBW page-hero atmospheric backdrops via Nano Banana.

Author: RKOJ-ELENO :: 2026-05-23

Drops three in-theme images for the remaining underused page heros:
  - banners/contact-shop.png      - Contact page hero backdrop
  - banners/services-tools.png    - Services page hero backdrop
  - banners/portfolio-finish.png  - Portfolio listing hero backdrop
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\Sinister Sanctum\tools\nano-banana")
from nano_banana import jbw_image  # type: ignore

OUT = Path(r"D:\Sinister Sanctum\projects\sinister-generator\outputs\jb-woodworks\banners")
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    {
        "name": "contact-shop",
        "prompt": (
            "A warm cinematic photograph of a quiet woodworking shop in the late "
            "afternoon. A wide pine workbench takes the foreground; a single warm "
            "tungsten work light spills gold onto a half-finished board. A "
            "clipboard with a folded tape measure rests off to one side. No "
            "people, no text. Deep black surroundings, soft glow on the right "
            "side. Aspect 16:9, photorealistic, slight depth of field."
        ),
    },
    {
        "name": "services-tools",
        "prompt": (
            "A top-down photograph of a curated row of hand tools laid out on "
            "dark stained planks: a block plane, three chisels of different "
            "widths, a marking gauge, a pencil. Warm gold rim light comes from "
            "the top edge, the rest falls to deep black. Clean, deliberate, "
            "no people, no text. Aspect 16:9, photorealistic, macro detail."
        ),
    },
    {
        "name": "portfolio-finish",
        "prompt": (
            "An extreme low-angle photograph along a freshly oiled walnut "
            "tabletop, the surface glossy enough to reflect a single warm gold "
            "highlight that races down the length of the wood. The far end fades "
            "into pure black. No people, no text, no objects on the table. "
            "Aspect 16:9, photorealistic, dramatic raking light, calm and "
            "premium."
        ),
    },
]

results = []
for job in JOBS:
    out_path = OUT / f"{job['name']}.png"
    print(f"[gen] {job['name']} -> {out_path}")
    r = jbw_image(prompt=job["prompt"], output_path=str(out_path))
    results.append({
        "name": job["name"],
        "status": r.status,
        "elapsed_seconds": r.elapsed_seconds,
        "image_bytes": r.image_bytes,
        "error": r.error,
    })
    print(f"  -> {r.status} | {r.elapsed_seconds}s | {r.image_bytes}B")
    if r.error:
        print(f"  ERR: {r.error}")

summary_path = OUT / "_gen_page_heros_2026-05-23.summary.json"
summary_path.write_text(json.dumps(results, indent=2))
print(f"\nSummary written to {summary_path}")
print(f"OK: {sum(1 for r in results if r['status'] == 'ok')} / {len(results)}")
