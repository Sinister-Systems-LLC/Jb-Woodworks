# Author: RKOJ-ELENO :: 2026-05-23
# One-shot test fire for showmasters lane — SMPL archetype (stagehand load-in).
# Per WORKFLOW.md Lesson 3: ONE image first, get a thumb, then variants.

import sys, json
from pathlib import Path

sys.path.insert(0, r"D:\Sinister Sanctum\tools\nano-banana")
from nano_banana import smpl_image

prompt = (
    "A single stagehand crew member pushing a wheeled black road case down a "
    "dimly lit backstage corridor of a large arena. Side-lit by amber par-can "
    "spill from offstage, gold rim light catching the road case edge. "
    "Volumetric atmospheric haze. Concrete floor catches a soft gold reflection. "
    "Crew member shown as a silhouette mid-stride, in plain black work clothes, "
    "no logos. Composition: subject in the left third, corridor recedes to a "
    "vanishing point on the right, faint stage lighting glowing in the far "
    "distance. Cinematic, photographic realism, painterly atmosphere."
)

output = Path(r"D:\Sinister Sanctum\projects\sinister-generator\outputs\showmasters\blog-heroes\load-in-archetype-v1.png")

print(f"[fire] subject=load-in-archetype-v1")
print(f"[fire] output={output}")

result = smpl_image(prompt=prompt, output_path=output)

print(json.dumps({
    "status": result.status,
    "output_path": result.output_path,
    "meta_path": result.meta_path,
    "model": result.model,
    "elapsed_seconds": result.elapsed_seconds,
    "image_bytes": result.image_bytes,
    "error": result.error,
    "text_excerpt": result.text_excerpt,
}, indent=2))
