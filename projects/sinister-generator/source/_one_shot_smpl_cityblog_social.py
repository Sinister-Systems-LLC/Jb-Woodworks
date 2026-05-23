# Author: RKOJ-ELENO :: 2026-05-23
# Fire remaining day-one batch: 2 city + 5 social + 11 blog headers.
# Direction locked from load-in-archetype-v1 + service-card batch.

import sys, json, time
from pathlib import Path

sys.path.insert(0, r"D:\Sinister Sanctum\tools\nano-banana")
from nano_banana import smpl_image

OUTPUTS = Path(r"D:\Sinister Sanctum\projects\sinister-generator\outputs\showmasters")

JOBS = []

# 2 city heros
for slug, city, where in [
    ("orlando-hero", "Orlando, Florida", "across Lake Eola at dusk with downtown buildings as silhouettes"),
    ("dallas-hero",  "Dallas, Texas",    "from a low rooftop at dusk with Reunion Tower silhouetted"),
]:
    JOBS.append({
        "out": OUTPUTS / "blog-heroes" / f"{slug}-v1.png",
        "prompt": (
            f"Cinematic dusk view of {city} {where}. Tall buildings as black "
            "silhouettes against a deep gradient sky fading from dark navy at "
            "the top to warm amber-gold at the horizon. A faint pinpoint of "
            "warm gold stage-light glow concentrated in the lower right of the "
            "frame, suggesting a venue district. No people, no text, no logos. "
            "Painterly photoreal, wide cinematic framing."
        ),
    })

# 5 social templates — empty / negative-space layouts for typography overlay
SOCIAL = [
    ("reel-anticipation",   "Vertical 9:16 deep black canvas with a single cone of warm gold stage light entering from upper right and pooling in the lower left third. No subject. No text. Composition deliberately empty for typography overlay later. The canvas feels like the moment before a show starts."),
    ("reel-loadin",         "Vertical 9:16 deep black canvas with the silhouettes of stacked road cases occupying only the lower 25 percent of the frame, lit from above by a single amber spotlight casting long shadows up the cases. The upper three-quarters is empty deep-black negative space for typography overlay. No people. No text."),
    ("reel-truss",          "Vertical 9:16 deep black canvas viewed straight up from the deck toward a truss grid high above. The truss steel forms a geometric grid pattern at the very top of the frame, lit gold from below. The lower three-quarters is empty deep black void for typography overlay. No people. No text."),
    ("ig-square-haze",      "Square 1:1 canvas. Deep black background with a horizontal band of golden volumetric stage-light haze across the middle third. The upper and lower thirds are empty deep black for typography overlay later. No subject. No text. No logos. Minimal."),
    ("ig-square-cone",      "Square 1:1 canvas. A single off-center cone of warm gold stage light entering from upper-right corner, pooling in the lower-left quadrant. Rest of frame is empty deep black. No subject. No text. Composition deliberately empty for typography overlay later."),
]
for slug, prompt in SOCIAL:
    JOBS.append({"out": OUTPUTS / "social" / f"{slug}-v1.png", "prompt": prompt})

# 11 blog headers per MARKETING/06-CONTENT-CALENDAR.md
BLOG = [
    ("blog-load-in-checklist",    "Wide horizontal shot of a half-loaded arena stage at the start of load-in. Several stagehands moving cases, one technician focused on a console at front of stage, scattered amber work lights, the venue mostly dark with one cool white house light still on far stage right. Camera at audience-level height, slightly off-center. Deep negative space top and right for typography overlay."),
    ("blog-focus-call",           "Wide horizontal shot of a darkened theater during a focus call. A single par-can light from a high front-of-house position is on, casting a sharp amber cone onto an empty stage. A lighting designer's silhouette stands far back at the FOH mixing position. Deep black void elsewhere. Cinematic widescreen."),
    ("blog-road-case-lifecycle",  "Wide horizontal shot of a row of black road cases lined up backstage, viewed from a low side angle. Cases are open and partially packed, equipment inside visible in shadows. Amber par-can light rakes across the row from offstage left. Concrete floor. No people. Cinematic widescreen."),
    ("blog-hub-vs-office",        "Wide horizontal shot of a half-lit warehouse interior with a few stagehand silhouettes loading a truck through a roll-up door at the far end. The truck's tail-lights cast a faint red glow. Most of the warehouse is in deep shadow with one amber utility light bracketed on the left wall. Cinematic widescreen, painterly."),
    ("blog-aca-compliance",       "Wide horizontal shot of a backstage clipboard rest area: a road case is being used as a writing surface, a folded paperwork stack and a pen lie on top, lit by a small clip-on amber work-lamp clamped to the case. Deep shadow surrounds. No people, no text on the papers, no logos. Cinematic widescreen."),
    ("blog-w4-vs-1099",           "Wide horizontal shot of a crew briefing scene: 6-8 stagehands standing in a loose semicircle around a crew lead with a clipboard, viewed from behind the crew lead. Single amber work-light overhead illuminates the group from above. Deep shadow background. Cinematic widescreen."),
    ("blog-72-hour-invoice",      "Wide horizontal shot of an empty venue after a show has loaded out: black marley floor, scattered cables being coiled, two stagehands rolling a long extension cable far in the background, one amber par-can still glowing on the truss. Mood: 4am wrap-up. Cinematic widescreen."),
    ("blog-rigger-day",           "Wide horizontal shot of a rigger high up in the truss above an arena, viewed from far back so the rigger is a small silhouette and the truss geometry dominates the frame. Gold key light below catches the truss diagonals. Deep black void behind. Cinematic widescreen."),
    ("blog-trade-show",           "Wide horizontal shot of a half-built trade-show booth: aluminum truss towers, pipe-and-drape sections being unrolled, a stagehand on a ladder. Amber par-can spill from offstage, vast empty exhibit hall floor stretching to a vanishing point. Cinematic widescreen."),
    ("blog-festival-load-in",     "Wide horizontal shot of an outdoor festival mainstage at dusk, mid-load-in. Stage scaffolding silhouetted against a deep dark-orange sky, a single follow-spot tower lit up amber against the gathering darkness. Crew silhouettes moving cases at stage level. Cinematic widescreen."),
    ("blog-corporate-keynote",    "Wide horizontal shot of an empty conference ballroom ready for a corporate keynote: rows of empty chairs, dark velvet stage drapes, an unlit lectern center-stage, a single amber wash light from above casting a soft pool on the lectern. Deep shadows fill the rest. Cinematic widescreen."),
]
for slug, prompt in BLOG:
    JOBS.append({"out": OUTPUTS / "blog-heroes" / f"{slug}-v1.png", "prompt": prompt})

print(f"[batch] firing {len(JOBS)} images")
results = []
for j in JOBS:
    j["out"].parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    r = smpl_image(prompt=j["prompt"], output_path=j["out"])
    el = round(time.time() - t0, 2)
    print(f"   {j['out'].name:48s} status={r.status} sec={r.elapsed_seconds} bytes={r.image_bytes} err={r.error}")
    results.append({
        "out": str(j["out"]),
        "status": r.status,
        "elapsed_seconds": r.elapsed_seconds,
        "image_bytes": r.image_bytes,
        "error": r.error,
    })

print("---SUMMARY---")
print(json.dumps({
    "total": len(results),
    "ok": sum(1 for r in results if r["status"] == "ok"),
    "errors": sum(1 for r in results if r["status"] != "ok"),
    "wall_total_seconds": sum(r["elapsed_seconds"] for r in results),
    "results": results,
}, indent=2))
