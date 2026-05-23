"""Fire 100 JKOR variants — broad operator-authorized sweep 2026-05-23.

Operator directive verbatim 2026-05-23T16:38Z: "ok give me lik 100 images".
Spend: 100 × $0.039 = $3.90 — above the conservative-balance ≤ 6 soft cap;
explicit operator override, logged via PROGRESS entry after this run.

Composition based on the operator's sort verdict (8 Good, 14 Bad after 25 v4+iter1 gens):
  - PFP    (35) — heaviest exploration; 0/5 v4 + ~3/5 iter1 PFPs landed in Good/Great
  - Banner (25) — 2 of 5 v4 in Good; expand the proven "char-centric magic" direction
  - Card   (20) — 3 of 5 v4 in Good (ace/three of diamonds + MTG-style); skip joker/tarot
  - Wordmark (12) — 3 of 5 v4 in Good (hat-stacked / hat-left / char-left); skip iridescent-glow / circle-emblem
  - Logo/icon ( 8) — small-applications grab-bag

Sequential firing + 1s inter-write sleep — AV-quarantine cure from the
21:35Z lesson; parallel writes trigger Windows Defender on AI-gen PNGs.

Refs: proven canonical pair from the project library
  - banner-CORRECT-canonical-2026-05-23T125744Z.png (BANNER_REF)
  - peeking-CORRECT-canonical-2026-05-23T125049Z.png (PFP_REF)
Selected per-kind via pick_refs() — same logic as _fire_jkor_pack_all.py.
"""
# Author: RKOJ-ELENO :: 2026-05-23

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(pathlib.Path(r"D:\Sinister Sanctum\tools\nano-banana")))

from nano_banana import api as nb  # noqa: E402

DESKTOP_JOKR = pathlib.Path(r"C:\Users\Zonia\Desktop\JOKR")

# NEW canonical (operator hard-canonical 2026-05-23T16:58Z verbatim:
# "this is the guy with the correct horn skull mask only use him"):
# C:\Users\Zonia\Desktop\2026-05-23T133146Z-banner-hero-statement.png
# Copied into JOKR/📥 Refs/ as the SOLE canonical. Previous canonicals
# (peeking-CORRECT + banner-CORRECT) removed per "only use him".
CANONICAL_REF = pathlib.Path(
    r"C:\Users\Zonia\Desktop\JOKR\📥 Refs\2026-05-23T133146Z-banner-hero-statement-CANONICAL.png"
)

CHARACTER_LOCK = (
    "CHARACTER (must EXACTLY match the canonical operator-endorsed look in refs[0] — "
    "this ref is the ONE TRUE source of truth):\n"
    "- PURPLE SKIN — deep saturated purple (NOT white / NOT porcelain / NOT pale)\n"
    "- WIDE TOOTH-BARING GRIN — visible white teeth, joker-style joyful menace\n"
    "  (NOT closed-mouth smirk, NOT a frown, NOT a neutral expression)\n"
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
    "ANTI-PATTERNS — do NOT repeat any of these (operator has rejected each):\n"
    "- NO porcelain-white / pale / pink / human skin tone — character is PURPLE\n"
    "- NO closed-mouth smirk / closed lips — character has a WIDE TOOTH-BARING GRIN\n"
    "- NO narrow half-lidded eyes — eyes are WIDE OPEN cyan/teal\n"
    "- NO photorealistic rendering — ILLUSTRATED / VECTOR ART only\n"
    "- NO painterly oil-painting look — flat fills + bold outlines only\n"
    "- NO 3D-rendered / CGI character — 2D illustrated art only\n"
    "- NO weak / obscured / cropped horns — horns extend visibly above hat\n"
    "- NO baked text / wordmarks / 'JOKR' lettering inside character art\n"
    "- NO multi-pose-trio / triple-character layouts\n"
    "- NO low-angle action stance that loses face detail\n"
    "- NO tarot-card-stylized character framing\n"
    "- NO classic-bicycle-joker playing-card layout\n"
    "- NO iridescent-rainbow glow effects on text\n"
    "- NO circle-emblem framing that crops the character\n"
)


# ---------------------------------------------------------------------------
# Family 1: PFP (35 variants) — square portraits, lean into peeking canonical
# ---------------------------------------------------------------------------

PFP_EXPRESSIONS = [
    "calm mischievous half-lidded eyes, closed-mouth smirk",
    "direct eye contact (still narrow eyes), confident closed smirk",
    "one raised brow, knowing look, closed smirk",
    "slight head-tilt to character-left, eyes drift right, closed smirk",
    "eyes glanced upward (looking past camera), thoughtful, closed smirk",
    "downcast lashes, contemplative, closed smirk",
    "slight wink with the camera-left eye, the other narrow, closed smirk",
]

PFP_LIGHTING = [
    "deep purple ambient + soft cyan rim-light tracing horn outlines",
    "warm-magenta key from camera-left + cool-purple fill from camera-right + glowing staff",
    "cold blue moonlit with silver edge-light on horn tips and collar gem",
    "spotlit single warm gold key from above + deep indigo background",
    "studio softbox: even purple-grey, slight warmth, jewel-tones intact",
]

PFP_FRAMING = [
    "tight crop: face fills ~60% of frame, horns dominate upper third",
    "canonical pose, same composition as ref[1]",
    "slight low angle (~3-5° tilt) — horns appear taller against backdrop",
    "wider crop showing shoulders + collar gem, character centered",
    "peeking from lower-left corner like the canonical, more empty space camera-right",
]


def build_pfp_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    # 5 lighting × 7 expressions = 35 PFPs (more variety in expression than lighting)
    for li, lighting in enumerate(PFP_LIGHTING):
        for ei, expr in enumerate(PFP_EXPRESSIONS):
            idx += 1
            framing = PFP_FRAMING[(li + ei) % len(PFP_FRAMING)]
            slug = f"pfp-{idx:02d}-L{li+1}-E{ei+1}"
            prompt = (
                f"Square PFP portrait of the canonical JKOR character. "
                f"EXPRESSION: {expr}. "
                f"LIGHTING: {lighting}. "
                f"FRAMING: {framing}. "
                f"Character occupies the canonical peeking pose space; "
                f"clean PFP art with NO baked text / NO wordmark / NO logo."
            )
            out.append((slug, prompt))
    return out


# ---------------------------------------------------------------------------
# Family 2: Banner (25 variants) — wide aspect, lean into char-centric magic
# ---------------------------------------------------------------------------

BANNER_POSITIONS = [
    "character anchored in the left third, ~ 2/3 empty negative space camera-right for typography overlay",
    "character centered, symmetric magical aura, equal negative space on both sides",
    "character anchored in the right third, ~ 2/3 negative space camera-left",
    "character centered with a hint of secondary cards/runes flowing outward across the wide frame",
    "character left, mirrored partial reflection / shadow silhouette right for balance",
]

BANNER_ATMOSPHERES = [
    "deep purple gradient backdrop, subtle magical particles, hint of cards-in-motion",
    "stormy purple-cyan magical clouds with rim-lit character cut-through",
    "dim arcane library backdrop — bookshelves blurred — character in foreground spotlight",
    "starfield + crescent moon negative-space backdrop, character in mid-magical-channel",
    "stage-curtain purple velvet backdrop, theatrical jester reveal",
]


def build_banner_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for pi, pos in enumerate(BANNER_POSITIONS):
        for ai, atmos in enumerate(BANNER_ATMOSPHERES):
            idx += 1
            slug = f"banner-{idx:02d}-P{pi+1}-A{ai+1}"
            prompt = (
                f"Wide horizontal banner (~2.5:1 aspect target) of the canonical JKOR character. "
                f"COMPOSITION: {pos}. "
                f"ATMOSPHERE: {atmos}. "
                f"Clean character read; horns dominant; NO baked text inside the art "
                f"(typography added later as SVG overlay). NO multi-pose / NO triple-character layouts."
            )
            out.append((slug, prompt))
    return out


# ---------------------------------------------------------------------------
# Family 3: Cards (20 variants) — playing-card-style. Skip joker-classic + tarot.
# ---------------------------------------------------------------------------

CARD_DESIGNS = [
    ("ace-of-diamonds", "Ace of Diamonds playing card — large central diamond pip with the JKOR character emblem inset"),
    ("ace-of-hearts", "Ace of Hearts playing card — central heart pip with the character peeking through the gap"),
    ("ace-of-spades", "Ace of Spades playing card — bold ornate spade pip with character emblem"),
    ("ace-of-clubs", "Ace of Clubs playing card — ornate club pip with the character"),
    ("king", "King face card — full character portrait centered, ornate purple-and-gold border, K corners"),
    ("queen", "Queen face card — character in royal-jester regalia centered, Q corners"),
    ("magician-mtg", "Magic-the-Gathering-style spell card — full art frame, character mid-spell, mana cost icons in corners"),
    ("creature-mtg", "Magic-the-Gathering-style creature card — full art, character ready to attack with staff raised"),
    ("planeswalker-mtg", "MTG planeswalker card layout — character with 3 loyalty abilities, ornate frame"),
    ("trading-card", "Generic trading card — character bust-shot center, holographic foil suggestion, stat block"),
]

CARD_TREATMENTS = [
    "clean classic playing-card layout, deep purple ink on cream stock",
    "iridescent foil treatment on the border, character clean",
]


def build_card_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for di, (kind, desc) in enumerate(CARD_DESIGNS):
        for ti, treatment in enumerate(CARD_TREATMENTS):
            idx += 1
            slug = f"card-{idx:02d}-{kind}-T{ti+1}"
            prompt = (
                f"Playing-card design featuring the canonical JKOR character. "
                f"DESIGN: {desc}. TREATMENT: {treatment}. "
                f"Card aspect (~3:4) intent, clean centered composition, NO tarot stylization, "
                f"NO classic-bicycle-joker layout."
            )
            out.append((slug, prompt))
    return out


# ---------------------------------------------------------------------------
# Family 4: Wordmark (12 variants) — character + 'JOKR' text combos
# ---------------------------------------------------------------------------

WORDMARK_LAYOUTS = [
    "hat-icon stacked above the 'JOKR' wordmark, centered",
    "hat-icon to the LEFT of 'JOKR' wordmark, same baseline",
    "character bust to the LEFT of 'JOKR' wordmark, character ~ 40% width",
    "small character emblem nested INSIDE the 'O' of 'JOKR'",
    "horns growing OUT of the K + R of 'JOKR' — typographic-character fusion",
    "'JOKR' wordmark in front, character peeking up from BEHIND the letters",
]

WORDMARK_TYPOGRAPHY = [
    "bold geometric sans-serif, purple-and-gold gradient fill",
    "tall narrow serif, deep purple ink, gold hairline outline",
]


def build_wordmark_variants() -> list[tuple[str, str]]:
    out = []
    idx = 0
    for li, layout in enumerate(WORDMARK_LAYOUTS):
        for ti, typo in enumerate(WORDMARK_TYPOGRAPHY):
            idx += 1
            slug = f"wordmark-{idx:02d}-L{li+1}-T{ti+1}"
            prompt = (
                f"'JOKR' wordmark / logo lockup. "
                f"LAYOUT: {layout}. "
                f"TYPOGRAPHY: {typo}. "
                f"Clean square presentation, deep purple background. "
                f"NO iridescent-rainbow glow on text. NO circle-emblem framing of the character. "
                f"Character must read clearly even at small sizes."
            )
            out.append((slug, prompt))
    return out


# ---------------------------------------------------------------------------
# Family 5: Logo / icon (8 variants) — small applications
# ---------------------------------------------------------------------------

LOGO_VARIANTS = [
    ("favicon-hat", "Square favicon: just the JKOR jester hat + horns + crown — simplified, readable at 32px"),
    ("favicon-face", "Square favicon: simplified character face mask with horns — readable at 32px"),
    ("sticker-die-cut", "Die-cut sticker mock-up: character peeking, white outline halo around the silhouette"),
    ("merch-tee", "T-shirt graphic: character centered, deep purple shirt, gold-outlined character"),
    ("badge-circle", "Round badge / emblem (circular frame): character bust centered, JKOR initials around the rim"),
    ("seal-wax", "Wax-seal style emblem: character profile in dark purple wax with horn silhouette pressed in"),
    ("crest-shield", "Heraldic shield crest: character emblem on a purple-and-gold quartered shield"),
    ("monogram-jk", "Monogram J+K interlocked, character horns rising out of the letters, gold-on-purple"),
]


def build_logo_variants() -> list[tuple[str, str]]:
    out = []
    for i, (slug_stem, desc) in enumerate(LOGO_VARIANTS, 1):
        slug = f"logo-{i:02d}-{slug_stem}"
        prompt = (
            f"Logo/icon design featuring the canonical JKOR character or its emblem. "
            f"BRIEF: {desc}. "
            f"Clean readable form, deep purple + gold palette."
        )
        out.append((slug, prompt))
    return out


# ---------------------------------------------------------------------------

def pick_refs(kind: str) -> list[pathlib.Path]:
    # Operator hard-canonical 2026-05-23T16:58Z: "only use him" → single canonical
    # ref across every kind. The illustrated/vector style of the canonical IS the
    # signal we need to lock; no need for a second reference image.
    if CANONICAL_REF.is_file():
        return [CANONICAL_REF]
    return []


def build_full_prompt(kind: str, variant_prompt: str) -> str:
    if kind == "wordmark":
        # Wordmarks don't need full character lock — refs + minimal anti-patterns
        return f"{variant_prompt}\n\n{REJECTION_ANTI_PATTERNS}"
    return f"{variant_prompt}\n\n{CHARACTER_LOCK}\n\n{REJECTION_ANTI_PATTERNS}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0, help="0-indexed variant to start from")
    ap.add_argument("--limit", type=int, default=0, help="Stop after N gens (0 = all)")
    args = ap.parse_args()

    DESKTOP_JOKR.mkdir(parents=True, exist_ok=True)

    all_variants: list[tuple[str, str, str]] = []  # (kind, slug, prompt)
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
    print(f"[*] {total} variants prepared ({sum(1 for k,_,_ in all_variants if k=='pfp')} pfp / "
          f"{sum(1 for k,_,_ in all_variants if k=='banner')} banner / "
          f"{sum(1 for k,_,_ in all_variants if k=='card')} card / "
          f"{sum(1 for k,_,_ in all_variants if k=='wordmark')} wordmark / "
          f"{sum(1 for k,_,_ in all_variants if k=='logo')} logo)")
    print(f"[*] Canonical ref: {'OK' if CANONICAL_REF.is_file() else 'MISSING'} — {CANONICAL_REF.name}")
    print(f"[*] Est spend: ${total * 0.039:.2f}  Est time: {total * 14}s (~{total * 14 // 60} min)")

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
        output = DESKTOP_JOKR / f"pack100-{utc}-{kind}-{slug.replace(kind+'-','')}.png"

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
            "idx": idx,
            "kind": kind,
            "slug": slug,
            "status": result.status,
            "output_path": str(result.output_path) if result.output_path else None,
            "elapsed_s": round(elapsed, 1),
            "error": result.error,
        })

        if idx < total:
            time.sleep(1.0)  # AV-quarantine cure

    total_elapsed = time.time() - t_start
    print()
    print(f"[*] Done in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"[*] {ok_count} ok, {error_count} error / {total} total")
    print(f"[*] Spend this run: ${ok_count * 0.039:.2f}")

    log_path = HERE / f"_fire_100_log_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    log_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] Full log: {log_path}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
