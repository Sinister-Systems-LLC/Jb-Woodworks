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
    "DESIGN LANGUAGE — DARK PROFESSIONAL SLEEK SELLING-PACK FOR JOKR-BRAND\n"
    "SNAPCHAT ACCOUNT SALES (operator hard-canonical 2026-05-23T18:26Z verbatim:\n"
    "'not so bright background more suttle professional sleek approach').\n"
    "\n"
    "PRODUCT: JOKR-brand Snapchat accounts (real USA SIM creation, 21-day\n"
    "proxy, 2FA delivered, Adspower wired, Bitmoji customization, 70+ adds/day).\n"
    "Powered by Sinister Panel / Sinister Snap automation. JOKR is the brand.\n"
    "\n"
    "- BACKGROUND: DEEP DARK rich PURPLE base (think #14062E → #28104E gradient).\n"
    "  SUBTLE texture only — fine paisley/swirl pattern at low opacity (~10-15%)\n"
    "  for depth, NOT loud psychedelic mandalas. Soft glow at the focal point.\n"
    "  Overall vibe: dark luxury / sleek commerce / premium tech ad. Think the\n"
    "  Apple-store-after-hours look in deep purple, not 60s rock poster.\n"
    "- WHITE wavy negative-space cutouts at slide edges — RESTRAINED versions\n"
    "  of the operator's reference Snap thread convention; thin and elegant\n"
    "  rather than thick and pillowy.\n"
    "- BOLD WHITE sans-serif titles — modern geometric sans (Inter / Plus Jakarta\n"
    "  / Manrope style), clean white fill, subtle dark-purple drop-shadow.\n"
    "  ALL CAPS for hero titles. Professional, not playful.\n"
    "- 3D GLOSSY PURPLE icons + 3D LETTERING for prices/numbers — refined chunky\n"
    "  3D-extruded with highlight gradients (Apple-keynote feel). These are the\n"
    "  one place chromatic flair is allowed; the BACKGROUND stays restrained.\n"
    "- Telegram-paper-plane icon + @handle pill-ribbon footer where appropriate\n"
    "- Snapchat ghost yellow-on-white accents ONLY where Snap-relevant\n"
    "- 16:9 wide aspect for thread slides (target ~1500×900 or 1920×1080)\n"
    "- JOKR brand wordmark MUST read clearly on every slide (operator 18:28Z:\n"
    "  'but we are called jokr')\n"
)

REJECTION_ANTI_PATTERNS = (
    "ANTI-PATTERNS — do NOT repeat any of these:\n"
    "- NO BRIGHT / BLOWN-OUT / WASHED-OUT / OVERLIT backgrounds — keep backgrounds\n"
    "  DEEP DARK PURPLE / restrained (operator 18:24Z + 18:26Z)\n"
    "- NO loud rock-poster psychedelic mandalas/swirls dominating the frame —\n"
    "  the operator wants SUBTLE PROFESSIONAL SLEEK, not chaotic-trippy\n"
    "- NO 'crown king' backgrounds: royal court / throne rooms / arcane libraries\n"
    "  / cosmic starfields / casino floors / stage curtains (operator 17:55Z)\n"
    "- NO content unrelated to JOKR-brand Snapchat-account sales — the product\n"
    "  is Snap accounts SOLD BY JOKR (operator 18:25Z + 18:28Z 'we are called jokr')\n"
    "- NO porcelain-white skin on the JOKR mascot — purple skin only\n"
    "- NO closed-mouth smirk on the mascot — wide grin\n"
    "- NO photorealistic / painterly / 3D-rendered CHARACTER — 2D vector mascot\n"
    "  (3D is ONLY for icons + numbers + lettering)\n"
    "- NO replacing the JOKR character with the Sinister-Sanctum horned-skull\n"
    "  generic mascot — JOKR mascot is the anchor\n"
    "- NO baked text wordmark inside character art\n"
    "- NO cheap / amateurish / cluttered layout — sleek + professional only\n"
    "- NO loud saturated electric-neon palette — dark purple base + restrained\n"
    "  accents only\n"
)


# ----- 20 hero slides -----

# Hero titles — JOKR is the brand selling Snapchat accounts.
HERO_TITLES = [
    "JOKR SNAPS", "JOKR SNAPCHAT", "JOKR ACCOUNTS",
    "SNAPS BY JOKR", "GET JOKR SNAPS", "JOKR SNAP VAULT",
    "PREMIUM JOKR SNAPS", "JOKR SNAP DROP", "BULK JOKR SNAPS",
    "JOKR SNAP DEALS", "JOKR USA SNAPS", "REAL SNAPS BY JOKR",
    "JOKR SNAP PACK", "JOKR SNAP SHOP", "JOKR SNAP ELITE",
    "FRESH JOKR SNAPS", "JOKR SNAP STOCK", "JOKR HUSTLE PACK",
    "JOKR SNAP CIRCLE", "JOKR PHASE I",
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

# Feature bundles — Snapchat-account selling features (operator 18:25Z).
# Mined from operator's reference Snap thread at C:\Users\Zonia\Desktop\ART\Snap.
FEATURE_BUNDLES = [
    ["Can Add 70+ People Per Day", "Comes With 21 Days Of Proxy", "Created On Real Mobile Phones", "Created On USA Sim"],
    ["Adspower Delivered", "Comes With 2FA Secret", "MM Accepted On Orders Of 10+", "Custom Bitmoji Hair + Eye Color"],
    ["Guaranteed Login", "Private Accounts", "Replacement If No Login", "Instant Delivery"],
    ["Real USA SIM-Created", "Aged 21+ Days", "Warm-Up Pattern Built In", "Discord Quality Check"],
    ["Mass-Add Capability", "Cooldown Bypass Tuned", "Friend-Add Velocity 70+/day", "Snap Score Bumped"],
    ["Bulk Pricing 10+", "Auto-Replacement Policy", "Reseller-Friendly", "MM Accepted Big Orders"],
    ["Bitmoji Pre-Configured", "Hair + Eye Color Set", "Avatar Style Matched", "Profile Picture Optional"],
    ["Adspower Profile Wired", "Cookies Pre-Loaded", "Login Sessions Active", "No Cold-Start Risk"],
    ["No-Bot Detection", "Behavioral Fingerprint Real", "Mobile-Made Not Emulator", "Carrier-Grade SIM"],
    ["Proxy Rotation 21d", "Geo-Matched USA IP", "Sticky Session Available", "Replacement If Banned <72h"],
    ["Discreet Delivery via TG", "Inbox Within 30 Min", "Encrypted Handoff", "No Login History Leaked"],
    ["Volume Tier Discounts", "10+ at $10/each", "20+ at $8/each", "100+ Custom Quote"],
    ["2FA Backup Codes Sent", "Recovery Email Pre-Set", "TOTP Secret Delivered", "Account Lifelong"],
    ["Built for Affiliate Hustle", "Built for Outreach", "Built for OnlyFans Promo", "Built for E-Comm DMs"],
    ["Refund If Login Fails", "Insurance on Bulk Orders", "Replace Within 72hr", "Reseller Tier Discounts"],
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

# Pricing tiers — Snapchat-account sales pricing (matches operator's reference
# Snap thread slide 5: $12/$10/$8 per account by volume).
PRICING_TIERS = [
    [("$12", "1 Account"), ("$10", "per 10 Accounts"), ("$8", "per 20+ Accounts")],
    [("$15", "Single Snap"), ("$12", "5+ Snaps"), ("$9", "20+ Snaps")],
    [("$20", "Premium Snap"), ("$15", "5+ Premium"), ("$11", "20+ Premium")],
    [("$10", "Basic Account"), ("$8", "Bulk 10+"), ("$6", "Bulk 50+")],
    [("$25", "Bitmoji-Custom"), ("$20", "5+ Bitmoji"), ("$15", "20+ Bitmoji")],
    [("$12", "USA Account"), ("$10", "USA Bulk 10+"), ("$8", "USA Bulk 25+")],
    [("$30", "Founders Snap"), ("$25", "5+ Founders"), ("$18", "10+ Founders")],
    [("$10", "Standard"), ("$15", "+ Adspower"), ("$22", "+ Adspower + Proxy 30d")],
    [("$12", "Snap Only"), ("$25", "Snap + Discord"), ("$40", "Snap + Discord + IG")],
    [("$15", "Login Guarantee"), ("$30", "+ Replacement"), ("$50", "+ Replacement + Insurance")],
    [("$8", "Reseller Tier"), ("$6", "100+ Resell"), ("$5", "500+ Resell")],
    [("$12", "1 Snap"), ("$60", "Pack of 5"), ("$100", "Pack of 10 + Bonus")],
    [("$10", "Cold Account"), ("$15", "Warmed Account"), ("$20", "Premium Warmed")],
    [("$12", "Basic"), ("$24", "Premium + Bitmoji"), ("$48", "Premium + Adspower")],
    [("$10", "Daily Drop"), ("$8", "Weekly Subscriber"), ("$6", "Monthly Subscriber")],
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

# Product cards — mockups of JOKR's Snapchat account product offerings.
PRODUCT_CARDS = [
    "Phone-Screen Mockup — 3D phone showing a fresh Snap account login, JOKR mascot in corner badge, 'Account Ready' overlay",
    "Bulk Snap Pack — 3D stack of 10 phone-card-style snap-account cards bound with a JOKR seal",
    "Founders Account Card — premium metallic membership card with JOKR mascot + 'FOUNDERS SNAP' embossed",
    "USA-SIM Pouch — 3D pouch / wallet mockup branded JOKR, USA SIM cards visible inside",
    "Adspower Profile Drop — laptop-screen mockup of an Adspower window with JOKR Snap profile loaded",
    "2FA Secret Capsule — 3D capsule containing TOTP secret, JOKR-branded wax seal",
    "Discord Quality-Check Card — chat-screen mockup of JOKR verifying account, mascot peeking",
    "Bitmoji Customization Kit — 3D Bitmoji avatar + customization options, JOKR mascot guiding",
    "Bulk Reseller Briefcase — 3D briefcase opening to reveal stacks of snap-account cards, JOKR brand",
    "Subscription Box — monthly snap-drop subscription, JOKR-branded box opening to reveal phone-card mockups",
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
