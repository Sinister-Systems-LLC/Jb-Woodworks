# Author: RKOJ-ELENO :: 2026-05-23
# Round 2 — the 6 missing service-card heros + reel-anticipation re-fire.

import sys, json, time
from pathlib import Path

sys.path.insert(0, r"D:\Sinister Sanctum\tools\nano-banana")
from nano_banana import smpl_image

OUT = Path(r"D:\Sinister Sanctum\projects\sinister-generator\outputs\showmasters")

JOBS = [
    {
        "out": OUT / "service-illustrations" / "camera-operator-v1.png",
        "prompt": (
            "A broadcast camera operator behind a professional multicam camera "
            "mounted on a jib arm at the side of a dark arena, viewed from a "
            "low side angle. The camera viewfinder LCD glows soft amber on the "
            "operator's face. Gold rim light catches the camera body and the "
            "jib arm extending into the frame. Subject in the left third, "
            "the jib arm reaches across the middle. Concrete venue floor "
            "below catches a faint gold reflection. Cinematic photographic realism."
        ),
    },
    {
        "out": OUT / "service-illustrations" / "spotlight-operator-v1.png",
        "prompt": (
            "A spotlight operator in a follow-spot booth high up in the back "
            "of a large dark arena, hands on the gimbal handles of a large "
            "professional follow-spot fixture. A bright cone of warm gold "
            "light shoots forward out of the spot, vanishing into atmospheric "
            "haze toward an unseen stage in the distance. View from behind "
            "the operator's silhouette, the spotlight mechanism dominating "
            "the lower right, the cone of light filling the rest of the frame."
        ),
    },
    {
        "out": OUT / "service-illustrations" / "stage-manager-v1.png",
        "prompt": (
            "A stage manager at the prompt corner of a theater wing, partially "
            "silhouetted, holding a clipboard with a small clip-on pencil light "
            "illuminating the call sheet, headset on with the boom mic positioned. "
            "Intense concentration on the face. Amber side-light spills from "
            "offstage right. Subject in the right third of the frame, dark "
            "stage flats receding to the left into shadow. Cinematic photographic realism."
        ),
    },
    {
        "out": OUT / "service-illustrations" / "tech-director-v1.png",
        "prompt": (
            "A technical director at a production village table backstage, "
            "covered in two open laptops, a small monitor showing camera feeds, "
            "a notepad and pen, and a coffee. Viewed from above-right at a "
            "three-quarter angle. The screens glow softly cool, a single "
            "amber clip-lamp arches over the table casting warm light on the "
            "hands and paperwork. Subject's hand reaches for the laptop trackpad. "
            "Deep shadow behind. Cinematic photographic realism."
        ),
    },
    {
        "out": OUT / "service-illustrations" / "show-management-v1.png",
        "prompt": (
            "A show producer with a headset at a backstage management station, "
            "viewed from behind. Three monitors in front display camera feeds "
            "of an unseen stage, glowing cool. The producer leans slightly "
            "forward toward the screens with one hand resting on a clipboard. "
            "Amber backlight spills in from offstage left, rim-lighting the "
            "shoulders and the headset cable. Deep shadow on the right side "
            "of the frame. Cinematic photographic realism."
        ),
    },
    {
        "out": OUT / "service-illustrations" / "warehouse-crew-v1.png",
        "prompt": (
            "A warehouse crew member at a large indoor loading dock, viewed "
            "from inside the warehouse looking out toward the open roll-up "
            "dock door. The crew member rolls a tall stack of black road "
            "cases on a wheeled cart toward a waiting box truck silhouetted "
            "against pre-dawn amber light pouring in through the open door. "
            "Polished concrete floor, amber tube lights overhead. Subject "
            "in left third, truck silhouette in the bright doorway right of "
            "center. Cinematic photographic realism."
        ),
    },
    {
        "out": OUT / "social" / "reel-anticipation-v1.png",
        "prompt": (
            "Vertical 9:16 deep black canvas. A single warm amber cone of "
            "stage light enters from the upper right corner and pools softly "
            "in the lower left quadrant of the frame. Subtle volumetric haze "
            "catches the light. The rest of the canvas is empty deep black "
            "negative space for typography overlay later. No subject. No "
            "people. No text. No logos. The mood is the moment of held "
            "breath before a show starts."
        ),
    },
]

print(f"[batch] firing {len(JOBS)} images")
results = []
for j in JOBS:
    j["out"].parent.mkdir(parents=True, exist_ok=True)
    r = smpl_image(prompt=j["prompt"], output_path=j["out"])
    print(f"   {j['out'].name:42s} status={r.status} sec={r.elapsed_seconds} err={r.error}")
    results.append({"name": j["out"].name, "status": r.status, "elapsed": r.elapsed_seconds, "error": r.error})

print("---SUMMARY---")
print(json.dumps({
    "total": len(results),
    "ok": sum(1 for r in results if r["status"] == "ok"),
    "errors": sum(1 for r in results if r["status"] != "ok"),
    "results": results,
}, indent=2))
