"""Fire 5 PFP iteration variants — round 2 after operator rejected all 5 PFPs in pack-v4.

Lessons from the sort:
- All 5 v4 PFPs (throwing-card, laugh-fanned-cards, side-glance, spell-cast, arms-crossed-cool)
  were rejected. So pose-exploration didn't land.
- Operator's earlier canonical (peeking-CORRECT-2026-05-23T125049Z) is the proven look.
- Strategy: stay INSIDE the canonical peeking-pose space; iterate on expression /
  lighting / framing / detail emphasis only. Treat the 5 rejected v4 poses as anti-patterns.

Uses library.generate() — auto-loads endorsed refs (📥 Refs now contains banner-CORRECT +
peeking-CORRECT), injects sort-derived anti-patterns, lands in JOKR/ for operator sort.

Sequential firing with 1s sleep to avoid AV-quarantine on parallel writes.
"""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "_unused_does_not_exist"))  # noop
sys.path.insert(0, str(HERE))  # for relative import via package root

# Make sinister_generator + nano_banana importable
sys.path.insert(0, str(HERE))
PROJECT_ROOT = HERE.parent  # projects/sinister-generator
sys.path.insert(0, str(PROJECT_ROOT / "source"))

from sinister_generator.library import generate  # noqa: E402


CHARACTER_LOCK = (
    "CHARACTER (must match the canonical operator-endorsed look in refs[0]+refs[1]):\n"
    "- PALE WHITE / porcelain mask-like face (NOT purple skin)\n"
    "- Small narrow dark eyes, mischievous half-lidded expression\n"
    "- Closed-mouth smirk (NO teeth, NO fangs, NO wide grin)\n"
    "- TWO LARGE PROMINENT dark-purple horns extending visibly beyond the jester hat outline\n"
    "- Small 4-5 point gold crown front of purple-and-silver/iridescent jester hat with bell tips\n"
    "- Purple-and-gold royal-jester collar with central round purple gem\n"
    "- WHITE GLOVES on both hands\n"
    "- LEFT hand: magical STAFF with glowing purple/cyan HEART-shaped gem on top\n"
    "- RIGHT hand: fan of magic playing cards with swirling cyan-purple MAGIC PATTERN card backs\n"
)

ITERATION_ANTI_PATTERNS = (
    "ITERATION ANTI-PATTERNS (operator rejected all 5 pose-exploration PFPs from pack-v4):\n"
    "- NO throwing-a-card mid-flight composition\n"
    "- NO laughing / wide-open-mouth / fanned cards in both hands\n"
    "- NO side-glance / 3/4 profile (face must be visible)\n"
    "- NO mid-spell-cast / hands raised / magical aura\n"
    "- NO arms-crossed-cool / no-staff-no-cards body language\n"
    "- NO showing teeth / open mouth — closed-mouth smirk ONLY\n"
    "- NO purple-skinned demon face — porcelain-white mask only\n"
    "- NO baked text / wordmarks / logos on the image — clean PFP art\n"
    "- NO weak/obscured horns — horns extend visibly above the hat\n"
)

# 5 PFP variants leaning into the canonical peeking pose — varies expression, lighting,
# framing, detail emphasis. Each ~1-2 sentence brief + reuses CHARACTER_LOCK + ANTI_PATTERNS.
VARIANTS = [
    (
        "iter1-tight-peek",
        "Tight square portrait PFP — character peeking from the bottom-left edge of frame, "
        "face nearly centered, eyes glanced toward viewer in mischievous half-lidded look, "
        "horns dominant in the upper half of frame. Composition closer than the canonical "
        "ref — face fills ~60% of the frame. Deep cyan-purple ambient backdrop, soft halo "
        "rim-light tracing the horn outline.",
    ),
    (
        "iter1-warm-lit",
        "Square PFP — character in the canonical peeking pose from the ref, but lit with "
        "warm-cyan key light from camera-left and cooler purple fill from camera-right. "
        "Subtle highlight on the heart-gem staff making it glow brighter than the canonical. "
        "Background: same deep purple as ref. Composition: same as ref.",
    ),
    (
        "iter1-cold-moonlit",
        "Square PFP — character in the canonical peeking pose from the ref, lit cold-blue / "
        "moonlit, faint silver edge-light on horn tips and collar gem. Background: deepest "
        "indigo-black gradient. Atmosphere: late-night magical heist. Same composition as ref.",
    ),
    (
        "iter1-eye-contact",
        "Square PFP — character peeking but with DIRECT eye contact to the viewer "
        "(eyes still narrow, closed-mouth smirk). More confident than the canonical's "
        "mischievous half-glance. Same horns, hat, collar, staff, cards. Composition: "
        "slightly more centered than ref; face fills ~50% of frame.",
    ),
    (
        "iter1-horn-forward",
        "Square PFP — character in the canonical peeking pose, but the camera angle is "
        "slightly LOWER (~3° tilt) so the horns appear taller and more dominant against "
        "the backdrop. Rim-light traces both horn outlines. Same expression, hat, collar, "
        "staff, cards as the ref.",
    ),
]


def main() -> int:
    print(f"[*] Firing {len(VARIANTS)} JKOR PFP iter1 variants ...")
    ok_count = 0
    error_count = 0
    t_start = time.time()

    for idx, (slug, variant_prompt) in enumerate(VARIANTS, 1):
        full_prompt = (
            f"{variant_prompt}\n\n"
            f"{CHARACTER_LOCK}\n\n"
            f"{ITERATION_ANTI_PATTERNS}"
        )
        # Prefix the prompt slug so library.generate slugifies it cleanly into the filename
        tagged_prompt = f"{slug} :: {full_prompt}"

        print(f"  [{idx}/{len(VARIANTS)}] {slug} ...", end=" ", flush=True)
        t0 = time.time()
        result = generate(
            brand="jkor",
            prompt=tagged_prompt,
            kind="pfp",
            refresh_first=(idx == 1),  # refresh once, reuse cached refs after
        )
        elapsed = time.time() - t0

        if result.status == "ok":
            ok_count += 1
            print(f"ok  {elapsed:.1f}s  {result.image_bytes // 1024}KB  refs={result.refs_used}")
        else:
            error_count += 1
            print(f"ERROR  {result.error}")

        # AV-quarantine cure: sequential + 1s gap
        if idx < len(VARIANTS):
            time.sleep(1.0)

    total_elapsed = time.time() - t_start
    print()
    print(f"[*] Done: {ok_count} ok, {error_count} error in {total_elapsed:.1f}s")
    print(f"[*] Spend this run: ${ok_count * 0.039:.3f}")
    print(f"[*] Outputs landed in C:\\Users\\Zonia\\Desktop\\JOKR\\")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
