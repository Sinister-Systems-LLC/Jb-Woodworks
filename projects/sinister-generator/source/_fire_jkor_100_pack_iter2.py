"""Fire 100 JKOR variants — iter2 sweep 2026-05-23, operator-authorized.

Operator directive 2026-05-23T17:11Z: "ok do another set of 100".

Same canonical ref + lock as iter1 (purple-grin character per 2026-05-23T16:58Z
hard-canonical). Different prompt axes to maximize variety:

  iter1 axes (already explored):
    PFP: lighting × expression (5 × 7)
    Banner: char-position × atmosphere (5 × 5)
    Card: design × treatment (10 × 2 — mostly aces + face + MTG)
    Wordmark: layout × typography (6 × 2)
    Logo: 8 grab-bag emblems

  iter2 axes (this pack):
    PFP: pose × scene-backdrop (7 × 5) — character DOING things, varied backdrops
    Banner: scene × char-position (5 × 5) — themed environments (casino/library/etc)
    Card: numbered × suit (5 numbered × 4 suits = 20) — fewer face cards
    Wordmark: typography-treatment × layout (6 × 2) — etched/neon/smoke/etc
    Logo: 8 application contexts — app icons, merch, ads

Sequential firing + 1s sleep. Sole canonical ref via JOKR/📥 Refs/.
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

# Per operator 2026-05-23T17:32Z: use the purple-skull photos sorted into
# 💎 Great + ✅ Good (not just one canonical). The library's feedback loop
# scans those tiers and returns ranked refs — Refs → Great → Good.
# A multi-ref Gemini call locks character far harder than a single-ref call.
CANONICAL_REF = pathlib.Path(
    r"C:\Users\Zonia\Desktop\JOKR\📥 Refs\2026-05-23T133146Z-banner-hero-statement-CANONICAL.png"
)

CHARACTER_LOCK = (
    "CHARACTER (must EXACTLY match the canonical operator-endorsed look in refs[0] — "
    "this ref is the ONE TRUE source of truth):\n"
    "- PURPLE SKIN — deep saturated purple (NOT white / NOT porcelain / NOT pale)\n"
    "- WIDE TOOTH-BARING GRIN — visible white teeth, joker-style joyful menace\n"
    "  (NOT closed-mouth smirk, NOT a frown, NOT neutral)\n"
    "- CYAN/TEAL EYES — wide open, mischievous glee (NOT narrow, NOT half-lidded)\n"
    "- TWO LARGE PROMINENT dark-purple horns curving up + back, extending visibly\n"
    "  above the jester hat outline\n"
    "- Small gold 4-5 point crown at the front of the purple-and-gold jester hat\n"
    "  with bell-tip points\n"
    "- Purple-and-gold royal-jester collar with central round purple gem at the throat\n"
    "- LEFT hand: magical STAFF with glowing cyan/purple gem on top\n"
    "- RIGHT hand: fan of magic playing cards (visible card backs with cyan pattern)\n"
    "- STYLE: bold ILLUSTRATED / VECTOR — flat purple fills, cyan accents,\n"
    "  bold black outlines, slight neon/glow on staff gem + collar gem\n"
    "  (NOT photorealistic, NOT painterly, NOT 3D-render — clean illustrated art)\n"
)

REJECTION_ANTI_PATTERNS = (
    "ANTI-PATTERNS — do NOT repeat any of these:\n"
    "- NO porcelain-white / pale / pink / human skin tone — character is PURPLE\n"
    "- NO closed-mouth smirk / closed lips — character has a WIDE TOOTH-BARING GRIN\n"
    "- NO narrow half-lidded eyes — eyes are WIDE OPEN cyan/teal\n"
    "- NO photorealistic rendering — ILLUSTRATED / VECTOR ART only\n"
    "- NO painterly oil-painting look — flat fills + bold outlines only\n"
    "- NO 3D-rendered / CGI character — 2D illustrated art only\n"
    "- NO weak / obscured / cropped horns — horns extend visibly above hat\n"
    "- NO baked text / wordmarks / 'JOKR' lettering inside character art (unless logo/wordmark family)\n"
    "- NO multi-pose-trio / triple-character layouts\n"
    "- NO low-angle action stance that loses face detail\n"
    "- NO tarot-card-stylized character framing\n"
    "- NO classic-bicycle-joker playing-card layout\n"
)


# ----- PFP: 7 poses × 5 backdrops = 35 -----

PFP_POSES = [
    "standing confidently centered, staff in left hand pointed up, cards fanned in right hand at hip",
    "mid-laugh, head thrown slightly back, both arms wide showing staff and full card fan",
    "leaning forward toward viewer, staff angled across chest, cards held close to face",
    "casting a spell — staff raised high with bright cyan/purple gem glow, cards forgotten momentarily, grin wide",
    "dealing a card mid-flick from the fan, staff held loose, eyes locked on the falling card",
    "arms crossed proudly with staff resting on shoulder, cards tucked under arm, grin full of confidence",
    "kneeling on one knee like a court jester taking a bow, staff planted, cards fanned outward toward viewer",
]

PFP_BACKDROPS = [
    "rich royal-purple background with subtle runic patterns + cyan magical particles",
    "deep velvet stage curtain backdrop with golden footlights glowing from below",
    "cosmic starfield + crescent moon, swirling magenta nebulae in distance",
    "arcane library interior — towering purple bookshelves blurred behind, dust motes catching cyan magical light",
    "casino floor abstraction — soft bokeh of suit-color spotlights (clubs/diamonds/hearts/spades) in purple+teal palette",
]


def build_pfp_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for pi, pose in enumerate(PFP_POSES):
        for bi, backdrop in enumerate(PFP_BACKDROPS):
            idx += 1
            slug = f"pfp-{idx:02d}-P{pi+1}-B{bi+1}"
            prompt = (
                f"Square portrait of the canonical JKOR character (illustrated / vector art). "
                f"POSE: {pose}. "
                f"BACKDROP: {backdrop}. "
                f"Clean character read; horns dominant; NO baked text / NO wordmark / NO logo. "
                f"Character should fill ~55-70% of the frame depending on pose."
            )
            out.append((slug, prompt))
    return out


# ----- Banner: 5 scenes × 5 char positions = 25 -----

BANNER_SCENES = [
    "casino floor scene — soft bokeh of chip stacks + suit icons in background, character mid-deal",
    "arcane library interior — towering bookshelves, glowing tomes, character mid-spell-channel",
    "festival stage scene — purple velvet curtain backdrop, golden footlights, character at center taking a bow",
    "cosmic void scene — swirling galaxies, runic glyphs floating around character",
    "royal court scene — gilded throne dimly visible behind character, purple banners hung",
]

BANNER_CHAR_POSITIONS = [
    "character anchored in the left third, action flows outward to the right",
    "character centered, scene framing radiates symmetrically",
    "character anchored in the right third, action flows outward to the left",
    "character centered, slight low-angle hero shot, scene framing tall behind",
    "character left, character partial-mirror reflection or shadow silhouette right",
]


def build_banner_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for si, scene in enumerate(BANNER_SCENES):
        for pi, pos in enumerate(BANNER_CHAR_POSITIONS):
            idx += 1
            slug = f"banner-{idx:02d}-S{si+1}-P{pi+1}"
            prompt = (
                f"Wide horizontal banner (~2.5:1 aspect target) of the canonical JKOR character. "
                f"SCENE: {scene}. "
                f"CHAR POSITION: {pos}. "
                f"Illustrated / vector art style. Clean character read; horns dominant. "
                f"NO baked text inside the art (typography added later as SVG overlay)."
            )
            out.append((slug, prompt))
    return out


# ----- Card: 5 numbered × 4 suits = 20 -----

CARD_NUMBERS = ["2 (Two)", "5 (Five)", "7 (Seven)", "9 (Nine)", "10 (Ten)"]
CARD_SUITS = ["Diamonds (red/magenta on cream)", "Hearts (red/magenta on cream)",
              "Spades (deep purple on cream)", "Clubs (deep purple on cream)"]


def build_card_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for ni, num in enumerate(CARD_NUMBERS):
        for si, suit in enumerate(CARD_SUITS):
            idx += 1
            num_slug = num.split()[0].lower()
            suit_slug = suit.split()[0].lower()
            slug = f"card-{idx:02d}-{num_slug}-of-{suit_slug}"
            prompt = (
                f"Playing card design: the {num} of {suit}. "
                f"Layout: classic playing-card with the {num.split()[0]} pip arrangement of "
                f"{suit.split()[0].lower()} symbols, but each pip stylized with a tiny embedded JKOR character "
                f"emblem (horns + crown silhouette). The full JKOR character peeks out from one corner of the card. "
                f"Card aspect (~3:4), clean centered, illustrated/vector style, purple-and-gold border ornament. "
                f"NO joker-classic layout, NO tarot stylization, NO face-card layout."
            )
            out.append((slug, prompt))
    return out


# ----- Wordmark: 6 typography-treatments × 2 layouts = 12 -----

WORDMARK_TYPO_TREATMENTS = [
    "etched-metal: deep purple metal plate with the 'JOKR' letters etched and gold-inlaid",
    "neon-tube: 'JOKR' as cyan + magenta neon-tube lettering with glow halos",
    "smoke-text: 'JOKR' letters formed from swirling purple smoke and arcane vapor",
    "glass-translucent: 'JOKR' in faceted purple-glass letters with cyan refractions",
    "stitched-fabric: 'JOKR' embroidered on purple velvet, gold thread, slight shadow",
    "iridescent-pixel: 'JOKR' built from chunky pixel/voxel blocks shifting purple→cyan",
]

WORDMARK_CHAR_LAYOUTS = [
    "small character emblem peeking from BEHIND the wordmark",
    "character bust to the LEFT of the wordmark (character ~ 35% width)",
]


def build_wordmark_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for ti, treatment in enumerate(WORDMARK_TYPO_TREATMENTS):
        for li, layout in enumerate(WORDMARK_CHAR_LAYOUTS):
            idx += 1
            slug = f"wordmark-{idx:02d}-T{ti+1}-L{li+1}"
            prompt = (
                f"'JOKR' wordmark / logo lockup. "
                f"TYPOGRAPHY TREATMENT: {treatment}. "
                f"CHARACTER LAYOUT: {layout}. "
                f"Clean square presentation, deep purple background. "
                f"Character must read clearly; wordmark must read clearly. "
                f"NO iridescent-rainbow glow on text. NO circle-emblem framing of the character."
            )
            out.append((slug, prompt))
    return out


# ----- Logo / icon (8 application contexts) -----

LOGO_VARIANTS = [
    ("appicon-rounded-square", "Mobile app icon (rounded-square iOS-style): character face only (horns + grin + crown) centered on deep purple gradient, readable at 60×60px"),
    ("appicon-circle", "Mobile app icon (circular): character face centered, purple-and-gold ring border, readable at 60×60px"),
    ("favicon-monogram", "Favicon: a single 'J' letter with horns growing out of its top, gold-on-purple, readable at 16×16"),
    ("business-card-front", "Business-card front face mock-up: 3.5×2 aspect, character emblem top-right, 'JOKR' wordmark center-left, gold-on-purple"),
    ("merch-cap-embroidery", "Embroidery-style mock-up for a baseball cap front panel: small character emblem (horns + face only) on purple cap, gold-thread look"),
    ("merch-hoodie-back", "Large back-print mock-up for a purple hoodie: full character centered, decorative runic frame surrounding"),
    ("social-banner-square", "Square social banner (Instagram post 1:1): character on left, 'JOKR' wordmark right, decorative purple frame"),
    ("ad-banner-mobile", "Mobile ad banner (320×100 ratio): character on left, 'JOKR — magical card game' tagline on right, gold-on-purple"),
]


def build_logo_variants() -> list[tuple[str, str]]:
    out = []
    for i, (slug_stem, desc) in enumerate(LOGO_VARIANTS, 1):
        slug = f"logo-{i:02d}-{slug_stem}"
        prompt = (
            f"Logo/icon application featuring the canonical JKOR character or its emblem. "
            f"BRIEF: {desc}. "
            f"Illustrated / vector art style. Deep purple + gold palette + cyan accents."
        )
        out.append((slug, prompt))
    return out


def pick_refs(kind: str) -> list[pathlib.Path]:
    """Return up to 4 character-locked refs ranked Refs > Great > Good.

    Operator's 💎 Great + ✅ Good + 📥 Refs all contain the purple-skull
    canonical character; loading multiple of them as refs gives Gemini
    a much stronger character lock than a single-ref call.
    """
    refs = get_endorsed_refs("jkor", max_refs=4)
    if not refs and CANONICAL_REF.is_file():
        refs = [CANONICAL_REF]
    return refs


def build_full_prompt(kind: str, variant_prompt: str) -> str:
    if kind == "wordmark":
        return f"{variant_prompt}\n\n{REJECTION_ANTI_PATTERNS}"
    return f"{variant_prompt}\n\n{CHARACTER_LOCK}\n\n{REJECTION_ANTI_PATTERNS}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    DESKTOP_JOKR.mkdir(parents=True, exist_ok=True)

    all_variants: list[tuple[str, str, str]] = []
    for k, builder in (
        ("pfp", build_pfp_variants),
        ("banner", build_banner_variants),
        ("card", build_card_variants),
        ("wordmark", build_wordmark_variants),
        ("logo", build_logo_variants),
    ):
        for slug, prompt in builder():
            all_variants.append((k, slug, prompt))

    total = len(all_variants)
    counts = {k: sum(1 for x, _, _ in all_variants if x == k) for k in ("pfp", "banner", "card", "wordmark", "logo")}
    print(f"[*] iter2: {total} variants ({counts['pfp']} pfp / {counts['banner']} banner / "
          f"{counts['card']} card / {counts['wordmark']} wordmark / {counts['logo']} logo)")
    print(f"[*] Canonical ref: {'OK' if CANONICAL_REF.is_file() else 'MISSING'} — {CANONICAL_REF.name}")
    print(f"[*] Est spend: ${total * 0.039:.2f}  Est time: {total * 12}s (~{total * 12 // 60} min)")

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
        output = DESKTOP_JOKR / f"pack100b-{utc}-{kind}-{slug.replace(kind+'-','')}.png"

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
    print(f"[*] iter2 done in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"[*] {ok_count} ok, {error_count} error / {total} total")
    print(f"[*] Spend this run: ${ok_count * 0.039:.2f}")

    log_path = HERE / f"_fire_100_iter2_log_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    log_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] Full log: {log_path}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
