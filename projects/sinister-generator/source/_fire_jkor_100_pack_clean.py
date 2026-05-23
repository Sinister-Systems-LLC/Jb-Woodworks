"""Fire 100 JOKR clean-imagery variants — operator 2026-05-23T18:29Z verbatim:
'we are selling snapcaht accounts we are a service thats it. and i want
generic branding now no words and all that shit way less bright and not as
psychedilic a clean professional sleek approach'.

Total restart of the iter3/iter4 plans:
  - NO baked text / wordmarks / hero titles / pricing tiers / feature bullets
  - NO 'JOKR' lettering in the imagery (text overlays added later as SVG/CSS)
  - DARK + SLEEK + PROFESSIONAL — not bright, not loud-psychedelic
  - JOKR mascot stays the visual anchor (purple-skin grinning jester)
  - Service positioning: selling Snapchat accounts, full stop

Composition (100 imagery-only variants):
  - 25 mascot portraits (different poses + framings, square, NO text)
  - 20 wide hero banner compositions (mascot positioned for later text-overlay
    in the empty third — no baked text)
  - 15 phone/device mockups (clean snap-interface scenes, no text overlays)
  - 15 product/account-card mockups (account-card object, USA SIM pouch, etc)
  - 10 sticker / emblem designs (mascot-only forms, no wordmarks)
  - 10 background plates (dark sleek textures for text-overlay later)
  - 5 mascot+phone interaction scenes

Multi-ref via library.get_endorsed_refs. Sequential + 1s sleep.
"""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PROJECT_ROOT / "source"))
sys.path.insert(0, str(pathlib.Path(r"D:\Sinister Sanctum\tools\nano-banana")))

from nano_banana import api as nb  # noqa: E402
from sinister_generator.library import refresh_feedback, get_endorsed_refs  # noqa: E402

DESKTOP_JOKR = pathlib.Path(r"C:\Users\Zonia\Desktop\JOKR")


CHARACTER_LOCK = (
    "JOKR MASCOT (must match canonical operator-endorsed look in refs[0]):\n"
    "- Purple-skinned demon-jester with horns + small gold crown + jester hat\n"
    "  with bell-tips + royal-jester collar with central purple gem\n"
    "- Wide tooth-baring grin / mischievous expression\n"
    "- Cyan/teal eyes\n"
    "- LEFT hand: magical staff with cyan/purple heart-gem (when shown)\n"
    "- RIGHT hand: fan of magic cards with cyan card-back pattern (when shown)\n"
    "- For tight crops / icons: face + horns + crown only is sufficient\n"
    "- STYLE: bold 2D ILLUSTRATED / VECTOR — flat purple fills + cyan accents\n"
    "  + bold black outlines. NOT photorealistic, NOT painterly, NOT 3D-render\n"
)

DESIGN_DNA = (
    "DESIGN LANGUAGE — DARK SLEEK PROFESSIONAL (operator 18:26Z 'not so bright\n"
    "more subtle professional sleek' + 18:29Z 'no words and all that shit way\n"
    "less bright and not as psychedilic a clean professional sleek approach').\n"
    "\n"
    "- BACKGROUND: DEEP DARK PURPLE base (#14062E → #28104E gradient). VERY\n"
    "  SUBTLE texture — fine grain or whisper-faint paisley at <10% opacity.\n"
    "  Soft focal-point glow at most. NO loud swirls, NO mandalas dominating,\n"
    "  NO rock-poster psychedelia, NO bright washes. Apple-keynote dark-mode\n"
    "  in deep purple.\n"
    "- COLOR PALETTE: deep purple base + restrained cyan/magenta accents only\n"
    "  on key character elements (gem glow, card-back swirl, eye reflections).\n"
    "  The character is the color story; the background stays restrained.\n"
    "- NO TEXT in the imagery — NO wordmarks, NO 'JOKR' lettering, NO titles,\n"
    "  NO bullet lists, NO prices, NO product names. Pure imagery. Text\n"
    "  overlays are added later as separate typography layers.\n"
    "- Image-COMPOSITION respects negative space for the eventual text overlay\n"
    "  (banner-wide gens leave the right two-thirds clean; portrait gens are\n"
    "  square character-only).\n"
    "- Aspect: square 1:1 for portraits / 16:9 wide for banners / 9:16 vertical\n"
    "  for Story-format / 3:4 for product cards.\n"
)

REJECTION_ANTI_PATTERNS = (
    "ANTI-PATTERNS — do NOT repeat any of these:\n"
    "- NO TEXT / NO WORDMARKS / NO LETTERING / NO BAKED TITLES in the image.\n"
    "  Pure imagery only. The brand is a service; we add text overlays later.\n"
    "- NO BRIGHT / BLOWN-OUT / WASHED-OUT / OVERLIT backgrounds — DARK only.\n"
    "- NO loud psychedelic mandalas/swirls/rock-poster patterns — SUBTLE only.\n"
    "- NO 'crown king' backgrounds: royal court / throne rooms / arcane libraries\n"
    "  / cosmic starfields / casino floors / stage curtains.\n"
    "- NO porcelain-white skin on the mascot — purple skin only.\n"
    "- NO closed-mouth smirk — wide grin.\n"
    "- NO photorealistic / painterly / 3D-rendered character — 2D vector only.\n"
    "- NO replacing the JOKR mascot with the generic Sinister-Sanctum horned\n"
    "  skull — JOKR mascot is the anchor.\n"
    "- NO cheap / amateurish / cluttered layout — sleek + professional only.\n"
    "- NO loud saturated electric-neon palette — dark + restrained.\n"
)


# ----- 25 mascot portraits (square, no text, varied pose/framing/mood) -----

PORTRAIT_BRIEFS = [
    "tight head-and-shoulders crop, calm confident expression, head-on viewer",
    "tight head-and-shoulders crop, slight 3/4 turn, mischievous side-eye",
    "head only, top-down slightly tilted, wide grin direct to camera",
    "head only, slight low-angle, horns dominant in upper third",
    "shoulders-up, hand raising staff with gem glow at chest height",
    "shoulders-up, cards fanned across chest in right hand",
    "shoulders-up, both hands visible — staff left, cards right, balanced",
    "head + horns only, very tight crop, horns extending out-of-frame top",
    "head-on bust, gem on collar prominently catching highlight",
    "side profile, 3/4 turn, single horn silhouette dominant",
    "rear-3/4 over-shoulder peek toward camera, wide grin visible",
    "full bust centered, slight lean forward, cards extended toward camera",
    "head + crown + horns, head turned 30° camera-left, eyes tracking camera",
    "head tilted upward as if studying ceiling, cocky expression",
    "head looking down with knowing smirk, shadow across upper face",
    "close-up of just the eyes + horns + crown, very tight crop",
    "shoulders-up rim-lit from camera-left, dramatic edge-light on right side",
    "shoulders-up backlit silhouette with rim purple-glow tracing outline",
    "head-on with reflective sheen on collar gem + horn tips",
    "shoulders-up with subtle cyan magical particles floating around",
    "shoulders-up with one card mid-flick away from the fan in right hand",
    "head and full magical staff vertical from bottom to top of frame",
    "shoulders-up mid-laugh head-tilted-back, eyes nearly closed in joy",
    "head-on serious confident look (no laugh) closed-mouth slight smirk vari",
    "shoulders-up with horns reflecting subtle purple-and-cyan iridescence",
]


def build_portrait_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(PORTRAIT_BRIEFS, 1):
        slug = f"portrait-{i:02d}"
        prompt = (
            f"Square (1:1) imagery-only mascot portrait. {brief}. "
            f"Dark deep-purple background with subtle texture only. "
            f"NO text, NO wordmarks, NO lettering anywhere in the frame. "
            f"Clean professional illustration."
        )
        out.append((slug, prompt))
    return out


# ----- 20 wide hero banner compositions (text-overlay-later) -----

BANNER_BRIEFS = [
    "mascot anchored to the left third, head-and-shoulders crop, dark purple gradient bg leaving right two-thirds clean for later text overlay",
    "mascot anchored to the right third, slight 3/4 turn looking camera-left, left two-thirds clean negative space",
    "mascot in left third, full-body half-shown, staff and cards visible, right two-thirds dark purple negative space",
    "mascot centered, narrow vertical crop of the body, wide negative space both sides for symmetric text-overlay",
    "mascot in left quarter, very small (~15% of frame), making the right 75% all negative space",
    "mascot bottom-left corner, peeking up, top-right empty for headline overlay",
    "mascot in right quarter at a slight downward angle as if looking down at a CTA in lower-left",
    "mascot in left third, staff extending UP into the empty upper area for vertical text-alignment",
    "mascot left third, hand gesturing TOWARD the empty right area as if presenting a product",
    "mascot floating silhouette right edge, low-angle, vast dark cleanness to the left",
    "mascot only as a glowing emblem in the lower-right corner, rest is dark moody backdrop",
    "mascot left third, slight mirror-reflection or shadow shape on the right for visual rhythm",
    "mascot right third standing strong, looking forward, left two-thirds dark with slow gradient",
    "mascot centered but small (~20% frame width), even negative space around it",
    "mascot left third in a tight square inset, the rest of the banner is dark moody texture",
    "mascot top-left small, body angled downward, opening up the bottom-right for caption space",
    "mascot bottom-right small, mirror diagonal — top-left available for headline",
    "mascot left third, faint cyan radiating-energy lines fanning toward the empty right",
    "mascot just-emerging from the left edge as if behind a curtain, the right is clean dark",
    "mascot right edge, partial cropped (only ~60% of mascot visible), left two-thirds completely clean",
]


def build_banner_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(BANNER_BRIEFS, 1):
        slug = f"banner-{i:02d}"
        prompt = (
            f"Wide horizontal (16:9 aspect, ~1920×1080) imagery-only banner. {brief}. "
            f"Dark deep-purple background with subtle texture. NO baked text, "
            f"NO wordmarks, NO lettering — clean negative space for text-overlay-later workflow."
        )
        out.append((slug, prompt))
    return out


# ----- 15 phone/device mockups (clean snap interface scenes, no text) -----

PHONE_BRIEFS = [
    "single smartphone in 3/4 perspective held by an unseen hand, screen shows a blank Snapchat-yellow camera UI (no usernames or text), dark purple ambient bg",
    "smartphone face-on, screen shows a blank Snapchat-style chat thread (no readable text), mascot watermark on the back of the device",
    "smartphone tilted slightly, screen shows the Snapchat ghost icon centered on a clean yellow background, dark bg",
    "smartphone standing on edge with subtle reflection below, screen shows a blank Bitmoji avatar (no name text), dark purple bg",
    "two smartphones side-by-side comparing — both screens show blank login-style UIs (no text), dark bg",
    "smartphone slipping into a dark JOKR-purple branded pouch (no text on pouch), screen barely visible",
    "smartphone on a dark velvet surface, top-down view, screen shows the Snap camera blank, mascot face emblem subtle in corner of pouch nearby",
    "smartphone in a holographic protective sleeve, screen blank, glowing edges, dark bg",
    "stack of 3 smartphones, each face-down with subtle JOKR mascot emblem visible on back, dark moody bg",
    "smartphone in 3D-floating perspective, surrounded by abstract floating yellow Snapchat-ghost icons (no text on icons), dark bg",
    "smartphone next to a USA SIM card (no text on SIM) on a dark surface, suggesting account-creation kit",
    "smartphone screen showing a blank face-detection / unlock UI, dark purple ambient",
    "smartphone behind a faintly-glowing magical mascot-shaped silhouette, dark purple bg",
    "smartphone in side-profile, screen edge-on visible with thin yellow Snapchat color stripe, dark bg",
    "smartphone partly out of frame on bottom-left, top showing dark wallpaper with subtle JOKR mascot in upper corner",
]


def build_phone_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(PHONE_BRIEFS, 1):
        slug = f"phone-{i:02d}"
        prompt = (
            f"Imagery-only phone/device mockup. {brief}. "
            f"NO READABLE TEXT anywhere — usernames blurred, app titles absent, "
            f"timestamps absent. The phone screens are imagery-only suggestion of "
            f"Snap-interface without literal text. Dark sleek professional vibe."
        )
        out.append((slug, prompt))
    return out


# ----- 15 product/account-card mockups (objects, no text) -----

PRODUCT_BRIEFS = [
    "physical account-card object — a metallic black-purple card with subtle holographic JOKR mascot embossed (no text), floating against dark bg",
    "USA SIM card in a small protective sleeve, sleeve has subtle mascot watermark (no text), dark velvet bg",
    "small dark-purple gift-box opened to reveal a phone-card mockup inside (no text on box or card), magical glow",
    "stack of 5 metallic account-cards bound with a thin purple ribbon, mascot emblem on top card (no text), dark bg",
    "a single account-card balanced on a corner edge, mascot face only embossed, no text",
    "account-card mid-fall through dark space with motion blur, mascot embossed visible briefly",
    "account-card held by an unseen gloved hand (purple glove suggesting mascot ownership), dark bg",
    "account-card laid flat on a marble-purple surface beside a SIM card and a phone, all objects no-text",
    "premium velvet box opening to reveal a glowing account-card with mascot emblem, dark luxurious feel",
    "account-card inserted into a smartphone slot (impossible-physics — visual metaphor), dark bg",
    "account-card with a subtle holographic effect — color shifts purple → cyan as light changes",
    "stack of account-cards arranged like a deck, mascot-embossed top card, dark moody bg",
    "account-card floating with subtle aura, surrounded by 4 tiny mascot icons (no text icons)",
    "transparent acrylic display case holding a single account-card upright, dark bg, mascot on card",
    "account-card snapped in half then magically rejoining (visual concept of replacement-guarantee), no text",
]


def build_product_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(PRODUCT_BRIEFS, 1):
        slug = f"product-{i:02d}"
        prompt = (
            f"Imagery-only product mockup. {brief}. "
            f"NO PRINTED TEXT on any object. Mascot emblem/silhouette only "
            f"where branding is appropriate. Dark sleek professional product photography vibe."
        )
        out.append((slug, prompt))
    return out


# ----- 10 sticker / emblem designs (mascot-only forms) -----

EMBLEM_BRIEFS = [
    "die-cut sticker — mascot full body, white halo outline, no text",
    "die-cut sticker — mascot face + horns only (head crop), white halo, no text",
    "die-cut sticker — just the horns + crown (no face), minimal emblem, no text",
    "die-cut sticker — magical staff with heart-gem only (no character), no text",
    "die-cut sticker — fan of magic cards only, no text",
    "die-cut sticker — mascot peace-sign with grin, white halo, no text",
    "die-cut sticker — mascot winking, white halo, no text",
    "die-cut sticker — minimalist outline-only silhouette of mascot face, no fills, no text",
    "die-cut sticker — mascot tongue-out playful, white halo, no text",
    "die-cut sticker — mascot tipping the hat in a courteous bow, no text",
]


def build_emblem_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(EMBLEM_BRIEFS, 1):
        slug = f"emblem-{i:02d}"
        prompt = (
            f"Die-cut sticker/emblem design. {brief}. "
            f"Subtle dark purple background behind the sticker. NO text anywhere, "
            f"NO baked wordmarks. Clean professional illustration."
        )
        out.append((slug, prompt))
    return out


# ----- 10 dark background plates (for text-overlay later) -----

BACKDROP_BRIEFS = [
    "deep-purple gradient with subtle paisley pattern at low opacity, no character, no text — pure backdrop plate",
    "deep-purple gradient with faint cyan diagonal light leak from upper-right, no character, no text",
    "very dark purple with a single soft focal-point glow center-frame, no character, no text",
    "deep-purple with subtle hexagonal mesh pattern at low opacity, no character, no text",
    "near-black-purple with very subtle smoke / fog at the edges, no character, no text",
    "dark-purple with subtle film-grain texture across the entire frame, no character, no text",
    "deep-purple-to-black radial gradient outward from center, no character, no text",
    "deep-purple with a thin white wavy curve cutout sweeping in from the bottom-left corner, no character, no text",
    "deep-purple with two faint glowing cyan dots at lower corners as compositional anchors, no character, no text",
    "very dark purple with a barely-visible large mascot-silhouette watermark in the center (visible as a faint shape but not text), professional backdrop plate",
]


def build_backdrop_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(BACKDROP_BRIEFS, 1):
        slug = f"backdrop-{i:02d}"
        prompt = (
            f"Background plate (no character, no text). {brief}. "
            f"Designed to host text overlays added later. 16:9 wide aspect."
        )
        out.append((slug, prompt))
    return out


# ----- 5 mascot+phone interaction scenes -----

INTERACTION_BRIEFS = [
    "mascot reaching out from inside a smartphone screen — half-character is in the phone, half is emerging into the room, dark bg, no text",
    "mascot holding up a smartphone in front of itself, screen blank yellow Snapchat color, dark bg, no text",
    "mascot standing next to a giant smartphone scale-shifted larger, mascot looking up at it, dark bg, no text",
    "mascot tapping a smartphone screen with one finger, ripple emanating from contact point, dark bg, no text",
    "mascot whispering into the side of a smartphone (suggesting account-delivery), dark bg, no text",
]


def build_interaction_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(INTERACTION_BRIEFS, 1):
        slug = f"interaction-{i:02d}"
        prompt = (
            f"Mascot + phone interaction scene. {brief}. "
            f"Dark professional sleek vibe. NO TEXT anywhere — pure visual storytelling."
        )
        out.append((slug, prompt))
    return out


# ----- Build all -----

def pick_refs(kind: str) -> list[pathlib.Path]:
    return get_endorsed_refs("jkor", max_refs=4)


def build_full_prompt(kind: str, variant_prompt: str) -> str:
    return (
        f"{variant_prompt}\n\n"
        f"{CHARACTER_LOCK}\n\n"
        f"{DESIGN_DNA}\n\n"
        f"{REJECTION_ANTI_PATTERNS}"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    DESKTOP_JOKR.mkdir(parents=True, exist_ok=True)

    all_variants: list[tuple[str, str, str]] = []
    for k, builder in (
        ("portrait", build_portrait_variants),
        ("banner", build_banner_variants),
        ("phone", build_phone_variants),
        ("product", build_product_variants),
        ("emblem", build_emblem_variants),
        ("backdrop", build_backdrop_variants),
        ("interaction", build_interaction_variants),
    ):
        for slug, prompt in builder():
            all_variants.append((k, slug, prompt))

    total = len(all_variants)
    counts = {}
    for k, _, _ in all_variants:
        counts[k] = counts.get(k, 0) + 1
    print(f"[*] CLEAN-imagery iter: {total} variants")
    print(f"    breakdown: " + " / ".join(f"{counts[k]} {k}" for k in counts))

    refresh_feedback("jkor")
    sample_refs = get_endorsed_refs("jkor", max_refs=4)
    print(f"[*] Multi-refs ({len(sample_refs)}):")
    for i, r in enumerate(sample_refs):
        print(f"    refs[{i}] {r.parent.name} / {r.name}")
    print(f"[*] Est spend: ${total * 0.039:.2f}  Est time: {total * 13}s (~{total * 13 // 60} min)")

    ok_count = 0
    error_count = 0
    t_start = time.time()
    results = []

    for idx, (kind, slug, variant_prompt) in enumerate(all_variants, 1):
        if idx <= args.start:
            continue
        if args.limit and (idx - args.start) > args.limit:
            break

        full_prompt = build_full_prompt(kind, variant_prompt)
        refs = pick_refs(kind)

        utc = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
        output = DESKTOP_JOKR / f"clean-{utc}-{kind}-{slug.replace(kind+'-','')}.png"

        elapsed_total = int(time.time() - t_start)
        print(f"  [{idx:03d}/{total}] {kind}/{slug} ({len(refs)} refs, +{elapsed_total}s) ...", end=" ", flush=True)
        t0 = time.time()
        try:
            result = nb.generate(
                prompt=full_prompt,
                output_path=output,
                ref_images=refs,
                style_suffix=None,
            )
        except Exception as e:
            error_count += 1
            print(f"EXCEPTION {e}")
            results.append({"idx": idx, "kind": kind, "slug": slug, "status": "exception", "error": str(e)})
            continue
        elapsed = time.time() - t0

        if result.status == "ok":
            ok_count += 1
            print(f"ok  {elapsed:.0f}s  {result.image_bytes // 1024}KB")
        else:
            error_count += 1
            print(f"ERROR  {result.error}")

        results.append({
            "idx": idx, "kind": kind, "slug": slug, "status": result.status,
            "output_path": str(result.output_path) if result.output_path else None,
            "elapsed_s": round(elapsed, 1), "error": result.error,
        })

        if idx < total:
            time.sleep(1.0)

    total_elapsed = time.time() - t_start
    print()
    print(f"[*] clean-imagery done in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"[*] {ok_count} ok, {error_count} error / {total} total")
    print(f"[*] Spend this run: ${ok_count * 0.039:.2f}")

    log_path = HERE / f"_fire_100_clean_log_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    log_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] Full log: {log_path}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
