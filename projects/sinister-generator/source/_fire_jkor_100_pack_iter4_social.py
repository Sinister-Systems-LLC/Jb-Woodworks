"""Fire 100 JKOR social-commerce variants — iter4 2026-05-23.

Operator directive 2026-05-23T18:11Z verbatim: "keep going do 100 more"
(third 100-pack after iter2 100-pack + iter3-snap selling-pack).

Selling-content formats for the highest-leverage social platforms + commerce
extensions, all in psychedelic JKOR brand aesthetic (per 17:55Z hard-canonical:
"i want psycheldilic art not shitt crown king backgrounds").

Composition (100):
  - 20 Instagram square posts (1:1) — product showcase + quote graphics + brand
  - 15 IG/Snap Story templates (9:16) — vertical with CTA bar
  - 15 TikTok/Reel cover thumbnails (9:16) — eye-catching, swipe-stop
  - 15 Facebook/Twitter/X ad creatives (1.91:1) — paid-social hero
  - 10 Email header banners (3:1) — newsletter / promo top-banner
  - 10 Sticker designs — die-cut illustrated stickers
  - 10 Tarot/Oracle card designs — alternative card style to iter2 playing cards
  - 5 Apparel print mockups — T-shirt back / hoodie front

Multi-ref via library.get_endorsed_refs (auto-pulls character refs + style refs
from 📥 Refs + 💎 Great + ✅ Good). Sequential + 1s sleep AV-quarantine cure.

Anti-patterns drop "crown king" backgrounds (royal court / arcane library /
cosmic starfield / casino floor / stage curtains) per 17:55Z directive.
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
    "JKOR MASCOT (must match the canonical operator-endorsed look in refs[0]):\n"
    "- Purple-skinned demon-jester character with horns + gold crown + jester\n"
    "  hat with bell-tip points + royal-jester collar with central purple gem\n"
    "- Wide grin / mischievous expression\n"
    "- Holds magical staff with cyan/purple heart-gem (left hand) + fan of\n"
    "  magic playing cards (right hand) when full body shown\n"
    "- For compact mascot roles: just the face/bust with horns + crown\n"
    "- STYLE: bold ILLUSTRATED / VECTOR — flat purple fills, cyan accents,\n"
    "  bold black outlines (NOT photorealistic, NOT 3D-render-character)\n"
)

DESIGN_DNA = (
    "DESIGN LANGUAGE — PSYCHEDELIC + SOCIAL/COMMERCE:\n"
    "- BACKGROUND: psychedelic — swirling fluid liquid-paint patterns, fractal\n"
    "  mandala motifs, oil-on-water iridescence, lava-lamp morph shapes, op-art\n"
    "  optical-illusion patterns. Saturated purples + electric magenta + cyan +\n"
    "  lime-green + chromatic accents. 60s-70s rock-poster + risograph-grain.\n"
    "- WHITE wavy negative-space cutouts at edges (operator's selling-pack convention)\n"
    "- BOLD WHITE OUTLINED sans-serif titles — geometric sans, thick white\n"
    "  fill, subtle dark-purple drop-shadow, ALL CAPS for hero\n"
    "- 3D GLOSSY PURPLE/CHROMATIC lettering for prices and numbers (chunky\n"
    "  3D-extruded with iridescent chrome highlights)\n"
    "- Telegram-paper-plane icon + @handle pill-ribbon footer where appropriate\n"
    "- ASPECT: matches the platform native size (1:1 / 9:16 / 1.91:1 / 3:1)\n"
)

REJECTION_ANTI_PATTERNS = (
    "ANTI-PATTERNS — do NOT repeat:\n"
    "- NO 'crown king' backgrounds: royal court / throne rooms / gilded banners\n"
    "  / arcane libraries / cosmic starfields / casino floors / stage curtains\n"
    "- NO porcelain-white skin on the JKOR mascot — purple only\n"
    "- NO closed-mouth smirk — wide grin\n"
    "- NO photorealistic / painterly / 3D-rendered CHARACTER — 2D vector\n"
    "- NO Sinister-Sanctum horned-skull replacing JKOR — JKOR is the anchor\n"
    "- NO baked text wordmark inside character art\n"
    "- NO tame / corporate / minimal flat backgrounds — PSYCHEDELIC energy\n"
)


# ----- 20 Instagram square posts (1:1) -----

IG_POST_BRIEFS = [
    "Hero product launch — JKOR mascot centered, large 'NEW DROP' bold title, psychedelic swirl bg",
    "Quote card — short punchy quote ('LUCK IS RIGGED.') with mascot small in corner",
    "Carousel slide 1 — title 'SWIPE TO REVEAL' with mascot peeking from the right edge",
    "Behind-the-scenes — mascot 'sneak peek' with frame edge curtain-pull effect",
    "Restock alert — 'BACK IN STOCK' big bold + mascot pointing toward title",
    "Numbered drop — '24/100 LIMITED' with mascot holding the number card",
    "Founder's circle — 'JOIN THE CIRCLE' mascot in a fractal mandala frame",
    "Magic of the day — 'TODAY'S CARD' mascot with single card highlighted",
    "Customer love — '⭐⭐⭐⭐⭐' rating + mascot reacting with grin + glowing cards",
    "Brand origin — 'BORN IN 2026' mascot in 70s-rock-poster style frame",
    "Buy now CTA — 'SHOP NOW' giant button + mascot pointing down at it",
    "Bundle deal — '3-PACK SAVES 30%' mascot juggling 3 floating cards",
    "Membership perk — 'MEMBERS ONLY' mascot with gold key chained around horns",
    "Sold out — 'SOLD OUT — NEXT DROP SOON' mascot peeking through stamp",
    "Sticker pack tease — 'STICKERS DROP FRI' multiple mini-mascots scattered",
    "Drop countdown — '24 HRS' large countdown numbers + mascot waiting",
    "Win a deck — 'TAG 3 FRIENDS TO WIN' mascot holding winning deck",
    "Founders thank you — 'YOU MADE THIS HAPPEN' mascot bowing courteously",
    "Phase II reveal — 'PHASE II UNLOCKED' mascot through cracked-glass effect",
    "Brand mantra — 'WE BEND THE DECK' bold title + mascot bending cards",
]


def build_ig_post_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(IG_POST_BRIEFS, 1):
        slug = f"igpost-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Instagram square post (1:1 aspect, ~1080×1080). "
            f"BRIEF: {brief}. "
            f"Wavy white negative-space cutouts at corners. JKOR mascot styled per "
            f"refs[0]. PSYCHEDELIC swirling background. Bold-white-outlined typography "
            f"where called for."
        )
        out.append((slug, prompt))
    return out


# ----- 15 IG/Snap Story templates (9:16) -----

STORY_BRIEFS = [
    "Today's drop — title at top, mascot center, 'SWIPE UP' CTA at bottom",
    "Poll sticker template — 'WHICH ONE?' top, 2 product options side-by-side, mascot peeking center",
    "Countdown sticker template — '00:23:59' large center numbers, mascot below",
    "Behind-the-scenes peek — mascot with finger-to-lips 'shhh' gesture, 'TOMORROW' below",
    "Quote story — vertical poem-style text 'THE DECK / IS / NEVER / FAIR.' + mascot bottom",
    "DM CTA — 'DM 'JOKR' TO ORDER' bold + mascot pointing at user",
    "Link CTA — 'TAP THE LINK' arrow pointing up, mascot below grinning",
    "Tutorial step 1 — '1 / 5' top-corner indicator, mascot demoing a shuffle",
    "Reaction template — large reaction-face mascot grin, 'WHEN THE NEW PACK ARRIVES'",
    "Pricing snap — '$12 each' big 3D price, mascot smaller showing the product",
    "Loop GIF idea — 'NEW MERCH ↻' loop arrows around mascot",
    "Pre-order CTA — 'PRE-ORDER OPEN' header, mascot with stopwatch, footer @handle",
    "Live now — 'LIVE NOW' red badge, mascot waving, 'JOIN' button center",
    "Restock — 'BACK IN STOCK!' burst-shape header, mascot with shopping bag",
    "Founder's pass tease — 'FOUNDER'S PASS' vertical wordmark + mascot below",
]


def build_story_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(STORY_BRIEFS, 1):
        slug = f"story-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Vertical Story template (9:16 aspect, ~1080×1920). "
            f"BRIEF: {brief}. "
            f"PSYCHEDELIC bg, wavy cutouts, bold-white-outlined headlines. "
            f"Vertical composition optimised for Instagram + Snapchat Stories. "
            f"JKOR mascot styled per refs[0]."
        )
        out.append((slug, prompt))
    return out


# ----- 15 TikTok/Reel cover thumbnails (9:16) -----

TIKTOK_BRIEFS = [
    "Watch til the end — face-of-mascot mid-grin, 'WATCH TIL THE END' across top",
    "POV — 'POV: YOU JUST BOUGHT JKOR' style title + mascot reaction face",
    "ASMR-card-shuffle — 'CARD SHUFFLE ASMR' header, mascot mid-shuffle",
    "Day in the life — 'DAY IN THE LIFE OF A CARD HUSTLER' + mascot",
    "Tier list — 'JOKR DECK TIER LIST' + S-tier card glowing",
    "Unboxing — 'I UNBOXED $1000 OF JKOR' mascot mid-reveal",
    "Tutorial — 'HOW I MAKE $X SELLING CARDS' mascot at desk",
    "Quick magic — '3 SECOND CARD MAGIC' mascot mid-trick",
    "Don't blink — 'BLINK AND YOU MISSED IT' mascot fast-pose blur",
    "Reaction — 'MY REACTION TO PHASE II' mascot wide-eyed grin",
    "Storytime — 'STORYTIME: HOW JKOR STARTED' mascot at fireplace stylized",
    "Vs duel — 'JKOR vs OTHER DECKS' split-screen mascot vs generic",
    "Top 5 — 'TOP 5 JKOR CARDS' countdown style with stacked cards",
    "Drop alert — '⚠️ NEW DROP TONIGHT' siren-style mascot wide-eyed",
    "Behind-the-design — 'HOW THIS CARD WAS MADE' mascot at drafting table",
]


def build_tiktok_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(TIKTOK_BRIEFS, 1):
        slug = f"tiktok-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"TikTok/Reel cover thumbnail (9:16 aspect, ~1080×1920). "
            f"BRIEF: {brief}. "
            f"EYE-CATCHING swipe-stop composition with very bold title text in "
            f"the upper third and dynamic mascot positioning in the middle/lower "
            f"two-thirds. PSYCHEDELIC bg. JKOR mascot styled per refs[0]."
        )
        out.append((slug, prompt))
    return out


# ----- 15 Facebook/Twitter/X ad creatives (1.91:1) -----

AD_BRIEFS = [
    "Cold-traffic intro — 'EVER BOUGHT A CARD THAT FELT LIKE MAGIC?' + mascot",
    "Direct sale — '$12 / 1 CARD · $10 / 5+ · $8 / 10+' price tiers + mascot",
    "Limited time — 'LAUNCH WEEK 30% OFF — ENDS FRIDAY' + mascot with clock",
    "Trust signal — '10,000+ CARDS SHIPPED · ⭐4.9 RATING' + mascot trophy",
    "Founders CTA — 'BECOME A FOUNDING MEMBER — 100 SPOTS LEFT' + mascot key",
    "Use-case angle — 'GIFT THAT TURNS HEADS' + mascot wrapping a deck",
    "Curiosity hook — 'WHAT EVEN IS A JKOR DECK?' question-mark mascot",
    "Social proof — 'CREATORS YOU FOLLOW ARE COLLECTING' + mascot with creator silhouettes",
    "Scarcity — 'ONLY 24 LEFT — NEXT DROP IN 30 DAYS' + countdown mascot",
    "Re-engagement — 'YOU LEFT THIS IN YOUR CART…' mascot reminding",
    "Lookbook tease — 'SEE THE FULL LOOKBOOK →' + mascot pointing right",
    "Brand promise — 'BUILT BY ARTISTS · OWNED BY YOU' + mascot with paint brush",
    "Comparison — 'WHY JKOR > OTHER DECKS' table + mascot pointing checkmarks",
    "Testimonial style — '\"BEST CARDS I'VE OWNED.\" — @collector_jane' + mascot",
    "Bundle CTA — 'BUILD YOUR BUNDLE — SAVE UP TO 40%' + mascot juggling cards",
]


def build_ad_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(AD_BRIEFS, 1):
        slug = f"ad-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Paid-social ad creative (1.91:1 aspect, ~1200×628). "
            f"BRIEF: {brief}. "
            f"CONVERSION-FOCUSED layout: headline left + visual right OR centered "
            f"with CTA button. PSYCHEDELIC bg, JKOR mascot styled per refs[0]. "
            f"Wavy cutouts + bold-white-outlined headline. Small @jokr handle "
            f"footer-right."
        )
        out.append((slug, prompt))
    return out


# ----- 10 Email header banners (3:1) -----

EMAIL_BRIEFS = [
    "Welcome email — 'WELCOME TO JKOR' mascot tipping hat",
    "Order confirmation — 'YOUR DECK IS ON ITS WAY' mascot with shipping box",
    "Shipped email — 'JUST SHIPPED!' mascot waving deck-shaped envelope",
    "Drop announcement — 'NEW DROP INSIDE' mascot mid-magic-reveal",
    "Reactivation — 'WE MISS YOU' mascot pleading-grin",
    "Birthday email — 'HAPPY BIRTHDAY' mascot with party-hat + cards",
    "Cart abandoned — 'YOU FORGOT SOMETHING' mascot dangling a cart",
    "Members-only — 'MEMBERS-ONLY DROP' mascot with secret-vault door",
    "Survey — 'TELL US WHAT YOU THINK' mascot with clipboard",
    "Thank-you — 'THANK YOU FOR YOUR ORDER' mascot bowing",
]


def build_email_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(EMAIL_BRIEFS, 1):
        slug = f"email-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Email header banner (3:1 aspect, ~1200×400). "
            f"BRIEF: {brief}. "
            f"PSYCHEDELIC bg, wavy cutouts, bold-white-outlined headline horizontal "
            f"centered. JKOR mascot styled per refs[0]."
        )
        out.append((slug, prompt))
    return out


# ----- 10 Sticker designs -----

STICKER_BRIEFS = [
    "Mascot face only — die-cut sticker outline, white halo around silhouette",
    "Mascot full body — die-cut, white halo, holding-cards-and-staff pose",
    "Horns-only icon — minimalist die-cut, just the horns + crown",
    "Tongue-out mascot — sticker variation with playful tongue-stuck-out face",
    "Heart-staff icon — die-cut just the staff with heart-gem",
    "Card-fan icon — die-cut just the card fan",
    "'JOKR' wordmark sticker — typographic die-cut with mascot horns growing out of letters",
    "Peace-sign mascot — mascot with one hand peace-sign + grin, die-cut",
    "Winking mascot — die-cut with closed-eye wink",
    "Skull-style mascot — psychedelic skull-emblem variation of mascot face",
]


def build_sticker_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(STICKER_BRIEFS, 1):
        slug = f"sticker-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Die-cut sticker design (square aspect with the actual sticker shape "
            f"cut out from the artwork area). "
            f"BRIEF: {brief}. "
            f"Visible white printed-paper halo border around the sticker outline. "
            f"Subtle psychedelic background outside the sticker (showing the "
            f"sticker as if photographed on a colorful surface). JKOR mascot per refs[0]."
        )
        out.append((slug, prompt))
    return out


# ----- 10 Tarot/Oracle card designs -----

TAROT_BRIEFS = [
    "THE TRICKSTER — major arcana style, mascot juggling cards, roman numeral 0",
    "THE MAGICIAN — mascot mid-spell with staff raised, roman numeral I",
    "THE FOOL — mascot stepping confidently off a card edge, roman numeral I",
    "WHEEL OF FORTUNE — mascot spinning a roulette of card suits, roman numeral X",
    "THE LOVERS — twin mascots facing each other, roman numeral VI",
    "THE STAR — mascot with star-burst around horns, roman numeral XVII",
    "THE MOON — mascot under crescent moon with cards, roman numeral XVIII",
    "THE SUN — mascot under radiant psychedelic sun, roman numeral XIX",
    "THE TOWER — mascot mid-leap from a falling tower of cards, roman numeral XVI",
    "THE WORLD — mascot encircled by all four suits, roman numeral XXI",
]


def build_tarot_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(TAROT_BRIEFS, 1):
        slug = f"tarot-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Tarot/Oracle card design featuring the JKOR mascot. ~3:5 vertical "
            f"aspect target. "
            f"BRIEF: {brief}. "
            f"Ornate purple-and-gold tarot-style border. Full art frame (not the "
            f"traditional small-illustration tarot — psychedelic FULL-art treatment). "
            f"Card title centered at bottom in bold-white-outlined text. JKOR mascot "
            f"styled per refs[0]. PSYCHEDELIC swirling backgrounds."
        )
        out.append((slug, prompt))
    return out


# ----- 5 Apparel print mockups -----

APPAREL_BRIEFS = [
    "T-shirt back print — large mascot full-body centered, runic frame around, purple shirt",
    "Hoodie front print — small chest emblem mascot face only, black hoodie",
    "Cap front embroidery — tiny mascot face + horns on a purple cap front panel",
    "Crewneck back graphic — large 'JOKR' wordmark + small mascot, gold-on-purple",
    "Tote bag print — mascot with cards fanned out, runic mandala behind, purple tote",
]


def build_apparel_variants() -> list[tuple[str, str]]:
    out = []
    for i, brief in enumerate(APPAREL_BRIEFS, 1):
        slug = f"apparel-{i:02d}-{brief.split('—')[0].strip().replace(' ','-').lower()[:18]}"
        prompt = (
            f"Apparel/merch print mockup. "
            f"BRIEF: {brief}. "
            f"Photoreal apparel mockup with the JKOR illustrated print clearly visible. "
            f"Print itself is psychedelic + JKOR mascot per refs[0]. "
            f"Subtle hangtag / sticker label visible."
        )
        out.append((slug, prompt))
    return out


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
        ("igpost", build_ig_post_variants),
        ("story", build_story_variants),
        ("tiktok", build_tiktok_variants),
        ("ad", build_ad_variants),
        ("email", build_email_variants),
        ("sticker", build_sticker_variants),
        ("tarot", build_tarot_variants),
        ("apparel", build_apparel_variants),
    ):
        for slug, prompt in builder():
            all_variants.append((k, slug, prompt))

    total = len(all_variants)
    counts = {}
    for k, _, _ in all_variants:
        counts[k] = counts.get(k, 0) + 1
    print(f"[*] iter4-social: {total} variants")
    print(f"    breakdown: " + " / ".join(f"{counts[k]} {k}" for k in counts))

    refresh_feedback("jkor")
    sample_refs = get_endorsed_refs("jkor", max_refs=4)
    print(f"[*] Multi-refs ({len(sample_refs)}):")
    for i, r in enumerate(sample_refs):
        print(f"    refs[{i}] {r.parent.name} / {r.name}")
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
        output = DESKTOP_JOKR / f"social-{utc}-{kind}-{slug.replace(kind+'-','')}.png"

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
    print(f"[*] iter4-social done in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"[*] {ok_count} ok, {error_count} error / {total} total")
    print(f"[*] Spend this run: ${ok_count * 0.039:.2f}")

    log_path = HERE / f"_fire_100_iter4_social_log_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    log_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] Full log: {log_path}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
