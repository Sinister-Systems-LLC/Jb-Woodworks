"""Fire 100 JKOR Snap-thread-style selling-pack variants — iter3 2026-05-23.

Operator directive 2026-05-23T17:50Z verbatim: "make the images relate to the
sinister sanctum project and snapchat and selling snapchat accounts and review
how i made threads here: C:\\Users\\Zonia\\Desktop\\ART\\Snap … as we will be
using this same idea for selling things wit this jokr company".

The Snap-thread is a 5-slide selling pack with strong brand DNA:
  - deep purple gradient backgrounds with subtle wavy liquid texture
  - WHITE wavy negative-space cutouts at slide edges (curves into the layout)
  - BOLD WHITE outlined sans-serif titles
  - 3D GLOSSY PURPLE icons + 3D lettering for prices/numbers
  - Telegram-handle pill ribbon footer on some slides
  - The original Sinister-Sanctum horned-skull mascot is the anchor → JKOR slots
    into the same role

Composition (100 variants):
  - 20 hero slides — JKOR mascot centered, "JOKR ACCOUNTS" / "SHOP JOKR" / etc title
  - 15 feature-bullet slides — 4-bullet feature callouts + 3D glossy icons
  - 15 pricing-tier slides — "PRICING" title + 3 glossy 3D-letter tier prices
  - 15 platform-reach slides — social icon constellation in dark circle
  - 15 logo-lockup slides — JKOR character + JOKR wordmark for selling pages
  - 10 full 5-slide thread layout mockups
  - 10 product-card mockups

Multi-ref via library.get_endorsed_refs (auto-pulls character refs + style refs
from 📥 Refs + 💎 Great + ✅ Good). Sequential + 1s sleep AV-quarantine cure.
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
    "JKOR MASCOT (must match the canonical operator-endorsed look — refs[0] is\n"
    "the canonical character; the snap-thread style refs in refs[3-4] are for\n"
    "DESIGN LANGUAGE only, NOT character):\n"
    "- Purple-skinned demon-jester character with horns + gold crown + jester\n"
    "  hat with bell-tip points + royal-jester collar with central purple gem\n"
    "- Wide grin / mischievous expression\n"
    "- Holds magical staff with cyan/purple heart-gem (left hand) and fan of\n"
    "  magic playing cards (right hand) when full body shown\n"
    "- For COMPACT mascot roles (corner icons, small badges): just the\n"
    "  face/bust with horns + crown is sufficient\n"
    "- STYLE: bold ILLUSTRATED / VECTOR — flat purple fills, cyan accents,\n"
    "  bold black outlines (NOT photorealistic, NOT 3D-render-character)\n"
)

DESIGN_DNA = (
    "DESIGN LANGUAGE — PSYCHEDELIC SELLING-PACK (operator hard-canonical\n"
    "2026-05-23T17:55Z: 'i want psycheldilic art not shitt crown king backgrounds').\n"
    "Snap-thread selling-pack STRUCTURE + PSYCHEDELIC art ART STYLE fused:\n"
    "\n"
    "- BACKGROUND: psychedelic — swirling fluid liquid-paint patterns, fractal\n"
    "  mandala motifs, oil-on-water iridescence, lava-lamp morph shapes, op-art\n"
    "  optical-illusion patterns. Saturated purples + electric magenta + cyan +\n"
    "  lime-green + chromatic accents. 1960s-70s rock-poster + risograph-grain\n"
    "  vibes. NOT royal court, NOT cosmic starfield, NOT arcane library, NOT\n"
    "  casino floor, NOT stage curtains — those are the rejected 'crown king'\n"
    "  scenes.\n"
    "- WHITE wavy negative-space cutouts at slide edges (kept from snap-thread\n"
    "  DNA — operator's selling-pack convention)\n"
    "- BOLD WHITE OUTLINED sans-serif titles — modern geometric sans, thick\n"
    "  white fill, subtle dark-purple drop-shadow, ALL CAPS for hero titles\n"
    "- 3D GLOSSY PURPLE/CHROMATIC icons + 3D lettering for prices and numbers\n"
    "  (chunky 3D-extruded shapes with highlight gradients, iridescent chrome\n"
    "  highlights where it fits)\n"
    "- Where shown: telegram-paper-plane icon + @handle in a pale-purple pill\n"
    "  ribbon footer at the bottom\n"
    "- 16:9 wide aspect for thread slides (target ~1500×900 or 1920×1080)\n"
)

REJECTION_ANTI_PATTERNS = (
    "ANTI-PATTERNS — do NOT repeat any of these:\n"
    "- NO 'crown king' backgrounds: royal court, throne rooms, gilded banners,\n"
    "  arcane libraries, cosmic starfields, casino floors, stage curtains\n"
    "  (operator explicitly rejected these)\n"
    "- NO porcelain-white skin on the JKOR mascot — purple skin only\n"
    "- NO closed-mouth smirk on the mascot — wide grin\n"
    "- NO photorealistic / painterly / 3D-rendered CHARACTER — character is 2D\n"
    "  illustrated / vector (3D treatment is ONLY for icons + numbers + letters)\n"
    "- NO replacing the JKOR character with the Sinister-Sanctum horned-skull\n"
    "  mascot — JKOR character is the new anchor\n"
    "- NO baked text WORDMARK inside the character art (the character is the\n"
    "  art; wordmarks/titles are separate typography layers)\n"
    "- NO tame / corporate / minimal flat backgrounds — operator wants\n"
    "  PSYCHEDELIC visual energy in every slide\n"
)


# ----- 20 hero slides -----

HERO_TITLES = [
    "JOKR ACCOUNTS", "SHOP JOKR", "JOKR PREMIUM",
    "GET JOKR", "JOKR DROP", "JOKR EXCLUSIVE",
    "JOIN JOKR", "JOKR DELUXE", "JOKR ELITE",
    "JOKR LAUNCH", "OWN JOKR", "JOKR FAM",
    "JOKR DECK", "PURE JOKR", "JOKR PASS",
    "JOKR CIRCLE", "JOKR ONLY", "JOKR HOUSE",
    "JOKR EDGE", "JOKR NIGHT",
]


def build_hero_variants() -> list[tuple[str, str]]:
    out = []
    for i, title in enumerate(HERO_TITLES, 1):
        slug = f"hero-{i:02d}-{title.replace(' ','-').lower()}"
        prompt = (
            f"Snap-thread style HERO slide. Wide horizontal 16:9 aspect. "
            f"TITLE: '{title}' in bold-white-outlined sans-serif at the top "
            f"(with subtle purple drop-shadow). "
            f"CENTER: JKOR mascot character centered, illustrated/vector style, "
            f"face/bust visible with horns + crown + jester hat clearly readable. "
            f"BACKGROUND: deep purple gradient with white wavy negative-space "
            f"cutouts at the top-left and bottom-right corners (organic curve "
            f"shapes bleeding in from the edges). "
            f"Subtle wavy liquid texture overlay on the purple. "
            f"Optionally: small Snapchat ghost icons flanking the title (yellow on white) "
            f"to evoke the original Snap-thread hero style."
        )
        out.append((slug, prompt))
    return out


# ----- 15 feature-bullet slides -----

FEATURE_BUNDLES = [
    ["Premium Curated Decks", "Daily New Drops", "Trading Card Library", "Exclusive Artwork"],
    ["Instant Delivery", "Verified Authenticity", "Lifetime Replacement", "24/7 Support"],
    ["Custom Card Backs", "Personalized Foiling", "Limited Edition", "Numbered Series"],
    ["Mystery Pack Drops", "Holo-Foil Variants", "Stamped Authenticity", "Owner Registry"],
    ["100+ Card Designs", "5 Rarity Tiers", "Themed Collections", "Digital + Physical"],
    ["MM Accepted", "Crypto Payments", "Group Discounts", "Loyalty Rewards"],
    ["High-Quality Print", "Premium Cardstock", "Foil Detailing", "Collector Sleeves"],
    ["Direct from Studio", "No Middleman", "Artist Royalties Paid", "Ethical Sourcing"],
    ["First Access Pass", "Member-Only Drops", "Pre-Launch Pricing", "Founders Circle"],
    ["Tradeable in Marketplace", "Verified Provenance", "Resale Royalties", "Authenticity NFC Chip"],
    ["Personalized Recommendations", "Curator's Pick Monthly", "Match-to-Style", "Bundle Builder"],
    ["Same-Day Shipping", "Discreet Packaging", "Insured Delivery", "Tracked Globally"],
    ["Custom Mascot Variants", "Personalized Artwork", "Name Engraved", "Wedding-Pack Option"],
    ["Limited Print Runs", "Numbered to 100", "Signed by Creator", "Certificate Included"],
    ["Beginner Friendly", "Pro Tier Available", "All Skill Levels", "Tutorial Included"],
]


def build_feature_variants() -> list[tuple[str, str]]:
    out = []
    for i, bullets in enumerate(FEATURE_BUNDLES, 1):
        slug = f"feature-{i:02d}-{bullets[0].replace(' ','-').lower()[:18]}"
        bullet_text = " / ".join(f"'{b}'" for b in bullets)
        prompt = (
            f"Snap-thread style FEATURE-BULLET slide. Wide horizontal 16:9 aspect. "
            f"LAYOUT: 4 bullet-point feature callouts stacked vertically on the LEFT side, "
            f"each preceded by a small purple-outlined circle bullet. The 4 bullets are: "
            f"{bullet_text}. "
            f"Each bullet text is bold-white-outlined sans-serif. "
            f"RIGHT SIDE: a 3D-glossy-purple icon set — a stylized 3D-rendered icon "
            f"(e.g. card deck / lock / trophy / phone) with subtle highlight gradients. "
            f"BACKGROUND: deep purple gradient + white wavy cutouts at the slide edges. "
            f"Subtle JKOR mascot face peek in one corner (small, ~10% of frame) as "
            f"the brand anchor."
        )
        out.append((slug, prompt))
    return out


# ----- 15 pricing-tier slides -----

PRICING_TIERS = [
    [("$5", "1 Card"), ("$12", "Per 5 Cards"), ("$8", "Per 10+ Cards")],
    [("$15", "Starter Deck"), ("$45", "Pro Deck"), ("$120", "Master Set")],
    [("$3", "Single"), ("$25", "Pack of 10"), ("$199", "Complete Series")],
    [("$10", "1 Print"), ("$8", "Per 5 Prints"), ("$6", "Per 20+ Prints")],
    [("$20", "Basic Pass"), ("$50", "Premium Pass"), ("$100", "Founders Pass")],
    [("$7", "Common Pack"), ("$25", "Rare Pack"), ("$99", "Legendary Pack")],
    [("$12", "1 Booster"), ("$60", "Box of 12"), ("$220", "Sealed Case")],
    [("$30", "Bronze Tier"), ("$60", "Silver Tier"), ("$120", "Gold Tier")],
    [("$9", "Card"), ("$24", "Foil Card"), ("$99", "Holo Foil")],
    [("$15", "Starter"), ("$40", "Standard"), ("$80", "Collector's")],
    [("$25", "Monthly"), ("$240", "Annual"), ("$600", "Lifetime")],
    [("$5", "Sticker"), ("$10", "Card"), ("$25", "Sticker+Card Bundle")],
    [("$50", "Bronze Drop"), ("$150", "Silver Drop"), ("$500", "Gold Drop")],
    [("$8", "Single Card"), ("$15", "Pair"), ("$40", "Trio")],
    [("$12", "Print"), ("$80", "Print Set of 8"), ("$200", "Print Set of 25")],
]


def build_pricing_variants() -> list[tuple[str, str]]:
    out = []
    for i, tiers in enumerate(PRICING_TIERS, 1):
        slug = f"pricing-{i:02d}-{tiers[0][1].replace(' ','-').lower()[:16]}"
        tier_descs = ", ".join(f"{p[0]} for '{p[1]}'" for p in tiers)
        prompt = (
            f"Snap-thread style PRICING slide. Wide horizontal 16:9 aspect. "
            f"TITLE: 'PRICING' huge bold-white-outlined sans-serif at the top. "
            f"3 TIER PRICES displayed horizontally across the middle, each in 3D "
            f"GLOSSY PURPLE LETTERING (chunky 3D-extruded, highlight gradients, "
            f"subtle white speculars): {tier_descs}. "
            f"Below each price, white sans-serif label naming the tier. "
            f"BACKGROUND: deep purple gradient with subtle wavy liquid swirl texture, "
            f"white wavy negative-space cutouts at the corners. "
            f"FOOTER: a pale-purple pill-ribbon at the bottom with a telegram-paper-plane "
            f"icon and '@jokrshop' handle. "
            f"Small JKOR mascot face peek in upper-right corner as brand anchor."
        )
        out.append((slug, prompt))
    return out


# ----- 15 platform-reach slides -----

PLATFORM_BUNDLES = [
    ("DIRECT TRAFFIC FROM ALL MAJOR PLATFORMS", "Instagram, TikTok, Hinge, Reddit, Tinder, X, Bumble"),
    ("REACH 1 MILLION+ EYES DAILY", "Instagram, TikTok, X, YouTube, Reddit, Snapchat"),
    ("CROSS-PLATFORM PRESENCE", "Instagram, TikTok, Twitter/X, Snapchat, Threads, Reddit"),
    ("BUILT FOR EVERY PLATFORM", "Instagram, TikTok, X, Telegram, Discord, Reddit, Snapchat"),
    ("ORGANIC GROWTH FROM ALL CHANNELS", "Instagram, TikTok, YouTube Shorts, Snapchat, Pinterest"),
    ("CONNECT EVERYWHERE", "Instagram, TikTok, X, Telegram, Discord, Snapchat, Reddit, Threads"),
    ("REACH YOUR TRIBE", "TikTok, Instagram, Snapchat, Discord, Telegram, X, Reddit"),
    ("SOCIAL MASTERY", "Instagram, TikTok, X, Snapchat, Threads, BeReal, Mastodon"),
    ("OMNICHANNEL", "Instagram, TikTok, X, Reddit, Snapchat, Telegram, Discord, YouTube"),
    ("EVERYWHERE YOUR CUSTOMERS ARE", "Instagram, TikTok, Hinge, Tinder, Bumble, Snapchat, Reddit, X"),
    ("BUILT FOR VIRAL GROWTH", "TikTok, Instagram Reels, YouTube Shorts, Snapchat Spotlight"),
    ("REACH GEN Z + MILLENNIALS", "TikTok, Snapchat, Instagram, X, Threads, BeReal"),
    ("LOCAL + GLOBAL REACH", "Instagram, TikTok, Facebook, X, Snapchat, Reddit, YouTube"),
    ("CONTENT TRAVELS FAR", "TikTok, Instagram, YouTube, X, Pinterest, Snapchat, Reddit"),
    ("ALWAYS-ON SOCIAL", "Instagram, TikTok, X, Snapchat, Telegram, Discord, Reddit"),
]


def build_platform_variants() -> list[tuple[str, str]]:
    out = []
    for i, (title, platforms) in enumerate(PLATFORM_BUNDLES, 1):
        slug = f"platform-{i:02d}-{title.split()[0].lower()}"
        prompt = (
            f"Snap-thread style PLATFORM-REACH slide. Wide horizontal 16:9 aspect. "
            f"TITLE: '{title}' across two lines in bold-white-outlined sans-serif at the top. "
            f"CENTER: a large dark-purple circle (~40% of frame) containing a constellation "
            f"of social-platform white icons: {platforms}. "
            f"Icons are simple white outlined symbols arranged in a balanced grid inside the circle. "
            f"BACKGROUND: deep purple gradient with subtle wavy liquid swirl texture, "
            f"white wavy negative-space cutouts at the left edge curving inward. "
            f"Small JKOR mascot in the lower-right corner as the brand anchor (~12% of frame)."
        )
        out.append((slug, prompt))
    return out


# ----- 15 logo lockup + selling-page slides -----

LOGO_LOCKUPS = [
    "JKOR character bust LEFT + 'JOKR' bold-white wordmark RIGHT, horizontal pill arrangement",
    "JKOR character TOP + 'JOKR' wordmark BOTTOM, vertical stack arrangement",
    "small JKOR mascot emblem INSIDE the 'O' of 'JOKR' wordmark",
    "JKOR character bust CENTER with the 'JOKR' wordmark wrapping in an arc above",
    "'JOKR' wordmark FRONT + character peeking from BEHIND letters with horns visible above",
    "JKOR character in a CIRCULAR purple-frame badge with 'JOKR' arched around the rim",
    "JKOR character HEAD-ONLY in a hex-shaped purple emblem with 'JOKR' below",
    "JKOR character flanking BOTH SIDES (mirror) of the 'JOKR' wordmark in middle",
    "JKOR character SILHOUETTE with 'JOKR' wordmark IN NEGATIVE-SPACE within the silhouette",
    "JKOR character emblem RIGHT + 'JOKR' wordmark LEFT + tagline below ('Magic & Cards')",
    "JKOR character + 'JOKR' wordmark + URL ribbon ('jokr.shop') in a 3-tier vertical stack",
    "stamp-style circular emblem: JKOR face center, 'JOKR ★ MAGIC ★ CARDS' arched around",
    "diagonal shoulder lockup: character upper-left + wordmark stretched lower-right",
    "wax-seal-style emblem: dark purple wax with JKOR profile pressed in + small 'JOKR' below",
    "neon-tube treatment: JKOR character outlined in cyan-neon + 'JOKR' wordmark in matching neon",
]


def build_lockup_variants() -> list[tuple[str, str]]:
    out = []
    for i, layout in enumerate(LOGO_LOCKUPS, 1):
        slug = f"lockup-{i:02d}"
        prompt = (
            f"Snap-thread style LOGO LOCKUP slide. Wide horizontal 16:9 aspect or square. "
            f"LAYOUT: {layout}. "
            f"BACKGROUND: deep purple gradient with subtle wavy liquid swirl texture, "
            f"white wavy negative-space cutouts at the slide edges. "
            f"The full lockup should read clearly even at small sizes for use as a sell-page header. "
            f"Bold white outlined sans-serif for the 'JOKR' wordmark; "
            f"illustrated/vector JKOR character."
        )
        out.append((slug, prompt))
    return out


# ----- 10 full 5-slide thread layouts -----

THREAD_LAYOUTS = [
    "5 slides arranged in a horizontal strip: hero / features / pricing / platforms / contact-CTA",
    "5 slides arranged in a 2x3 grid (last cell empty): hero / features-1 / features-2 / pricing / contact",
    "5 slides as a staircase ascending diagonally: hero top-left to contact bottom-right",
    "5 slides as 5 phone-screen mockups in a row, each showing a different slide",
    "5 slides as a fan-of-cards spread: hero centered + 4 others fanning out at angles",
    "5 slides as Instagram carousel-preview: 5 thumbnails in a horizontal scrollable strip",
    "5 slides in a hexagonal honeycomb arrangement around a central JKOR mascot",
    "5 slides stacked vertically like a magazine spread with the hero on top",
    "5 slides displayed on a tablet/phone overlay mockup — like an ad-platform preview",
    "5 slides arranged as a circular timeline with arrows pointing slide-to-slide",
]


def build_thread_variants() -> list[tuple[str, str]]:
    out = []
    for i, layout in enumerate(THREAD_LAYOUTS, 1):
        slug = f"thread-{i:02d}"
        prompt = (
            f"Multi-slide thread MOCKUP showing a complete 5-slide selling pack. "
            f"LAYOUT: {layout}. "
            f"Each individual slide carries the snap-thread design DNA: deep purple gradient + "
            f"white wavy cutouts + bold-white-outlined titles + 3D glossy purple icons/lettering. "
            f"JKOR mascot character appears on the hero slide and as a small brand-anchor on "
            f"each other slide. "
            f"Wide horizontal 16:9 aspect for the overall mockup."
        )
        out.append((slug, prompt))
    return out


# ----- 10 product-card mockups -----

PRODUCT_CARDS = [
    "1 Card Pack with hologram seal — single pack mockup, JKOR-branded wrapper, gold-foil border",
    "Booster Box of 12 packs — 3D box mockup, JKOR mascot on the lid, opened to show packs",
    "Sealed Case — large 3D shipping case, branded JKOR, gold-and-purple tape sealed",
    "Starter Deck — 60-card deck box, illustrated JKOR cover, see-through window",
    "Foil Card Showcase — single premium card displayed in protective sleeve + holder",
    "Subscription Box — monthly mystery-pack mockup, JKOR branded, opening to reveal cards",
    "Collector's Binder — premium binder with JKOR mascot on cover, open to show cards",
    "Founders Pass — metallic membership card mockup with JKOR profile + embossed serial",
    "Gift Bundle — wrapped present with JKOR ribbon + card inside, festive purple-and-gold",
    "Apparel Drop — hoodie + tee mockup pair, JKOR mascot on back, hangtag attached",
]


def build_product_variants() -> list[tuple[str, str]]:
    out = []
    for i, prod in enumerate(PRODUCT_CARDS, 1):
        slug = f"product-{i:02d}-{prod.split('—')[0].strip().replace(' ','-').lower()[:20]}"
        prompt = (
            f"Snap-thread style PRODUCT CARD MOCKUP. Wide horizontal 16:9 aspect. "
            f"PRODUCT: {prod}. "
            f"BACKGROUND: deep purple gradient with white wavy cutouts at corners. "
            f"PRODUCT CENTERED, 3D-rendered with realistic lighting + subtle reflection. "
            f"TITLE BANNER at the top in bold-white-outlined sans-serif naming the product. "
            f"PRICE TAG in the corner using 3D glossy purple lettering. "
            f"JKOR mascot small in lower-left as the brand anchor."
        )
        out.append((slug, prompt))
    return out


def pick_refs(kind: str) -> list[pathlib.Path]:
    refs = get_endorsed_refs("jkor", max_refs=4)
    return refs


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
        ("hero", build_hero_variants),
        ("feature", build_feature_variants),
        ("pricing", build_pricing_variants),
        ("platform", build_platform_variants),
        ("lockup", build_lockup_variants),
        ("thread", build_thread_variants),
        ("product", build_product_variants),
    ):
        for slug, prompt in builder():
            all_variants.append((k, slug, prompt))

    total = len(all_variants)
    counts = {k: sum(1 for x, _, _ in all_variants if x == k) for k, _ in (
        ("hero", None), ("feature", None), ("pricing", None),
        ("platform", None), ("lockup", None), ("thread", None), ("product", None)
    )}
    print(f"[*] iter3-snap: {total} variants")
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
        output = DESKTOP_JOKR / f"snap-{utc}-{kind}-{slug.replace(kind+'-','')}.png"

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
    print(f"[*] iter3-snap done in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")
    print(f"[*] {ok_count} ok, {error_count} error / {total} total")
    print(f"[*] Spend this run: ${ok_count * 0.039:.2f}")

    log_path = HERE / f"_fire_100_iter3_snap_log_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    log_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[*] Full log: {log_path}")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
