# Author: RKOJ-ELENO :: 2026-05-23
# Fire 6 SMPL service-card heros. Direction locked by load-in-archetype-v1.
# Per WORKFLOW.md "operator interaction protocol": don't ask permission for
# variants once direction is locked. These are different SUBJECTS (not variants
# of one subject) — same brand-lock applies.

import sys, json, time
from pathlib import Path

sys.path.insert(0, r"D:\Sinister Sanctum\tools\nano-banana")
from nano_banana import smpl_image

OUT_ROOT = Path(r"D:\Sinister Sanctum\projects\sinister-generator\outputs\showmasters\service-illustrations")
OUT_ROOT.mkdir(parents=True, exist_ok=True)

SUBJECTS = [
    {
        "slug": "stagehand",
        "prompt": (
            "A single stagehand crew member pushing a wheeled black road case "
            "across a backstage corridor of an arena. Amber par-can side-light "
            "from offstage left, gold rim light catching the case edge. "
            "Volumetric atmospheric haze. Concrete floor with soft gold "
            "reflection. Crew shown as a silhouette mid-stride, plain black "
            "work clothes, no logos. Subject in left third, corridor recedes "
            "to vanishing point on the right. Cinematic photographic realism."
        ),
    },
    {
        "slug": "rigger",
        "prompt": (
            "A rigger high up in the truss above a darkened arena, securing a "
            "chain motor to a steel beam. Low upward camera angle. Gold key "
            "light from a follow-spot below catches the rigger's silhouette "
            "and the geometric lines of the truss. Deep black void surrounds, "
            "with faint hints of empty venue seats far below. Subject occupies "
            "the upper third of the frame, truss diagonals frame the shot. "
            "Cinematic photographic realism."
        ),
    },
    {
        "slug": "technician",
        "prompt": (
            "An audio technician at a large lighting + sound console at the "
            "front-of-house position in a dark theater. Gold backlight from "
            "the stage in the distance, the console's small LEDs glowing in "
            "amber and warm white in the foreground. Technician shown from "
            "behind, headphones on, hands on faders, focused. Composition: "
            "console occupies lower third, stage glow on the horizon, "
            "technician's silhouette frames the right side. Cinematic, "
            "photographic, painterly atmosphere."
        ),
    },
    {
        "slug": "lift-operator",
        "prompt": (
            "A boom-lift operator raising a scissor lift platform high inside "
            "a dark arena, viewed from a low angle. Amber stage lighting "
            "catches the painted yellow lift mast and the operator's safety "
            "harness silhouette. Background is deep black void with subtle "
            "truss geometry visible far above. Subject centered slightly "
            "right of middle, lift extending upward into the frame. "
            "Cinematic photographic realism."
        ),
    },
    {
        "slug": "crew-lead",
        "prompt": (
            "A crew lead in a dark venue holding a clipboard, communicating "
            "on a headset with a hand pressed to the earpiece, scanning the "
            "load-in floor. Amber working light catches their face from one "
            "side, the rest of the figure receding into shadow. Behind them, "
            "out-of-focus stagehands move cases. Composition: subject in left "
            "third, soft bokeh activity behind. Cinematic photographic "
            "realism, painterly atmosphere."
        ),
    },
    {
        "slug": "logistics",
        "prompt": (
            "A logistics coordinator at a backstage staging area surrounded "
            "by neatly stacked black road cases and equipment carts. They are "
            "writing on a clipboard, partially silhouetted by an amber par-can "
            "glow from above and behind. Concrete floor with case-strap "
            "shadows. Subject in left third of frame, cases stacked into the "
            "right two-thirds with depth. Cinematic photographic realism."
        ),
    },
]

results = []
for s in SUBJECTS:
    out = OUT_ROOT / f"{s['slug']}-v1.png"
    print(f"[fire] {s['slug']} -> {out.name}")
    t0 = time.time()
    r = smpl_image(prompt=s["prompt"], output_path=out)
    el = round(time.time() - t0, 2)
    results.append({
        "slug": s["slug"],
        "status": r.status,
        "output_path": r.output_path,
        "elapsed_seconds": r.elapsed_seconds,
        "image_bytes": r.image_bytes,
        "error": r.error,
        "wall_seconds": el,
    })
    print(f"   status={r.status} bytes={r.image_bytes} sec={r.elapsed_seconds} err={r.error}")

print("---SUMMARY---")
print(json.dumps(results, indent=2))
