"""Generate JBW atmospheric backdrops via Nano Banana.

Author: RKOJ-ELENO :: 2026-05-23

Drops three in-theme images (no people, no fake projects, mood only):
  - banners/about-workshop.png        - About / hero atmospheric backdrop
  - banners/error-quiet-shop.png      - 404 + future error pages
  - banners/grain-texture.png         - subtle section divider texture
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
        "name": "about-workshop",
        "prompt": (
            "A wide cinematic photograph of a quiet woodworking shop at dusk. "
            "A single beam of warm light rakes across a planed walnut plank "
            "resting on a dark workbench. Fine dust motes drift in the light. "
            "Two hand planes and a row of chisels sit slightly out of focus in "
            "the shadow. No people. No text. Deep black surroundings. "
            "Aspect 16:9, depth of field, photorealistic."
        ),
    },
    {
        "name": "error-quiet-shop",
        "prompt": (
            "A lonely macro photograph of a single curled wood shaving lying on "
            "a dark-stained shop floor. A faint warm gold rim light catches one "
            "edge of the shaving; the rest of the floor falls to pure black. "
            "Quiet, contemplative, slightly melancholy. No people. No text. "
            "Aspect 16:9, photorealistic."
        ),
    },
    {
        "name": "grain-texture",
        "prompt": (
            "An extreme close-up of premium American walnut grain, raking warm "
            "gold light from the left revealing the figure of the wood. Deep "
            "shadows on the right side fade to pure black. No tools, no people, "
            "no text. Tileable texture feel. Aspect 16:9, photorealistic, "
            "macro detail."
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

summary_path = OUT / "_gen_atmospherics_2026-05-23.summary.json"
summary_path.write_text(json.dumps(results, indent=2))
print(f"\nSummary written to {summary_path}")
print(f"OK: {sum(1 for r in results if r['status'] == 'ok')} / {len(results)}")
