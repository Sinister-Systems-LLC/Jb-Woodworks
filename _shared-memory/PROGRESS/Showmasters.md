<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Agent: Showmasters

Append-only progress log. Most recent at top.

---

## 2026-05-23 08:20 — Video lazy-load + entrance cascade + shows portfolio + STACK doc + Next.js app-v2 scaffold (LetsText-aligned)

Continued same session. Operator dropped three more directives mirrored from JB Woodworks pane:
1. *"make the video load faster... add good transitions... animation to start the page like letstext does... videos dont show... portfolio with by-project selection... not bland... no slop."*
2. *"make sure we are using all logic, coding language, database setup things like that that lets text is using."*

**Built this turn (still in `C:\Users\Zonia\Desktop\Showmasters Site\`):**

| Surface | Detail |
|---|---|
| Hero video lazy-load | EDIT `index.html` + `script.js`. Was: all 6 MP4s `preload="auto"` = 40 MB on page load (why "videos don't show" — first one not ready). Now: slide 1 `preload="auto"`, slide 2 `preload="metadata"`, slides 3-6 `preload="none"` + poster fallback. JS lookahead bumps next slide to `preload="auto"` when current goes active. Initial payload ~12 MB instead of 40 |
| Hero reveal cascade | EDIT `index.html` + `script.js`. Hero tag / headline / subheadline / CTA group each tagged `.hero-reveal` with `--reveal-delay` 0/120/240/360 ms. JS reveals sequentially after the Digital Loom intro (lifted from LetsText) fades out. Also added fallback path: when intro is skipped (sessionStorage memo or prefers-reduced-motion), `smplRevealHero()` still runs so hero copy doesn't sit at opacity:0 |
| `shows.html` NEW | Full portfolio page with 16 anonymized show cards across 8 categories (Corporate × 4, Concert × 3, Festival × 2, Trade Show × 3, Sports × 1, Theater × 1, Worship × 1, Private × 1). Filter chips bar with live counts. Pure client-side filter via JS (`#filterBar` click → toggles `.is-hidden` on cards by `data-category`). Footer + nav + full SEO stack matching the rest of the site |
| `.filter-chip` + `.show-card` + `.shows-grid` CSS | EDIT `style.css`. Glass-style chips with active gold gradient. Cards with category-themed thumbnail gradients (one per show category) + hover lift + gold glow. Stagger-in helper for sectioned containers. Mobile horizontal-scroll filter bar |
| Stagger-in IntersectionObserver | EDIT `script.js`. Containers tagged `.stagger-in` get `.is-staggered` when scrolled into view; their direct children fade in with 80ms cascading delays via CSS |
| Shows nav link added to every page | EDIT all 9 existing HTML pages (index/about/what/how/where/careers/contact/privacy/terms). Nav order: What · How · Where · **Shows** · About · Careers · Contact |
| `STACK.md` NEW | Documents the LetsText-aligned target stack (Next.js 15.5 + React 19.2 + TS5 + Tailwind 4.1 + shadcn new-york + Radix + react-hook-form + zod + react-query + framer-motion + react-simple-maps + Prisma + Postgres). Migration phases 1-5. Why we're moving past the static site |
| `app-v2/` Next.js scaffold NEW (16 files) | Side-by-side Next.js app, static site stays live until parity. Files: `package.json` (deps version-matched to LetsText dashboard-local), `next.config.mjs` (Radix tree-shake + security headers + image config), `tsconfig.json` (strict, paths `@/*`), `tailwind.config.ts` (SMPL brand tokens), `postcss.config.mjs`, `components.json` (shadcn new-york), `.env.example` (DATABASE_URL + Turnstile + nano-banana placeholders), `.gitignore`, `prisma/schema.prisma` (4 models: Inquiry / Application / NewsletterSub / Show + 4 enums), `lib/db.ts` (Prisma singleton), `lib/validations.ts` (zod schemas for inquiry/application/newsletter), `lib/utils.ts` (cn + hashIp), `app/layout.tsx` (Inter + DM Serif via next/font, manifest, theme-color), `app/globals.css` (Tailwind 4 entry + brand vars), `app/page.tsx` (home placeholder), `app/contact/page.tsx` + `app/contact/contact-form.tsx` (rhf + zod client form, POSTs to /api/inquiry), `app/api/inquiry/route.ts` (zod-validate, Turnstile-verify, Prisma-write), `app/api/application/route.ts`, `README.md` (full setup instructions including Docker Postgres + Caddy reverse-proxy config for HOSTING.md Path B) |

**Files touched this turn:**
- NEW: `shows.html`, `STACK.md`, `app-v2/` (16 files), `public/img/us-coverage-map.svg` was from prior turn
- EDIT: `index.html` (video preload + hero-reveal + Shows nav + already-applied where-preview lang fixes), `script.js` (hero-reveal helper + lookahead video preload + shows filter logic + stagger observer), `style.css` (filter-chip + show-card + shows-grid + stagger-in classes), `about.html`, `what.html`, `how.html`, `where.html`, `careers.html`, `contact.html`, `privacy.html`, `terms.html` (all gained Shows nav link)

**Stack handoff for next session:**
- `cd app-v2 && pnpm install` to materialize the deps
- Local Postgres needed for `pnpm db:push` (Docker one-liner is in `app-v2/README.md`)
- `pnpm dev` runs on port 5050 (avoids LetsText's 6060 + JB Woodworks)

**Still operator-gated:**
- Nano banana API access (other agent)
- IG handle canonical pick
- Orlando address canonical pick (4501 Vineland vs 4906 Patch Rd)
- Git init + push to `Sinister-Systems-LLC/Showmasters`
- Domain/DNS for showmasters.com
- Counsel-reviewed legal pages
- VPS provisioning for Postgres + Next.js
- Approval of `[explore]` BRANDING variants before public use

---

## 2026-05-23 07:10 — SEO + favicon hardening + IG pinned-banner set + US coverage map + cross-page language reconciliation

Continued same session past 06:15. Operator added four further directives in rapid order: (1) "make sure we have a logo on this and good seo," (2) "for IG make some branding things — replace this shitty 3 banner here," (3) "make sure the main project folder is on the desktop" (already canonical), (4) "audit all pages on the current site and ensure we include all info needed... entire site is one complete concise piece... all info needed visually displayed in a great manner."

**Built this turn:**

| Surface | Detail |
|---|---|
| `manifest.json` | NEW. PWA manifest at site root — SMPL name + short_name, theme + background `#0A0A0F`, 3 icons (favicon.svg + pfp-square.svg + pfp-circle.svg) |
| Favicon stack on all 9 HTML pages | NEW. Added `mask-icon` (Safari pinned-tab, gold `#D4A24A`), `apple-touch-icon` (was only on index), `manifest` link, `theme-color` meta. Index also gets `msapplication-TileColor` for Windows tile |
| Open Graph + Twitter Card on 6 secondary indexable pages | NEW. Added `og:url`, `og:type`, `og:site_name`, `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image` to about/what/how/where/careers/contact. Each tuned per page |
| Open Graph on 2 stub pages | NEW. privacy + terms got og:title/description/image so social shares render properly (still `noindex,follow`) |
| IG pinned-banner replacement set (6 SVGs + README) | NEW in `BRANDING/social/`. Option A: 3-card spanning composition (`ig-pinned-01-we-make-great`, `02-happen`, `03-every-day`) — reads as one headline across the IG profile, replaces the broken "LABOOGISTICS" trio. Option B: 3 standalone alternates (`ig-alt-stats`, `ig-alt-services`, `ig-alt-promise`). Each 1080×1080, full brand language, plus `ig-pinned-README.md` explaining when to use what |
| US coverage map | NEW `public/img/us-coverage-map.svg`. Stylized US silhouette in brand gold + dark canvas. 2 large gold-star primary offices (Orlando + Fort Worth) + 6 operational-hub stars (CA, NV, CO, TN, GA, LA) + ~70 city-served dots placed roughly geographically + legend + stat panel. Total file ~7 KB |
| `where.html` augmented | NEW visual section between header + locations grid. Headline pivoted from "Two hubs / Nationwide team" → "Two offices / Nationwide footprint" with subheadline that names the 8-hub layer explicitly. The 6 regional city cards below kept intact |
| Cross-page hub-language reconciliation | EDIT. index.html hero subhead + where-preview headline + about.html "today we run from" paragraph all pivoted from "two operational hubs" (which collided with the OLD-site map's 8-hub usage) to "two offices · eight operational hubs · 33 states." Trust strip crew count unified: 130+ (was 131+ on index) |

**Discrepancies surfaced for operator (will NOT auto-resolve):**

1. **IG handle:** The actual IG profile in operator's screenshot is `@showmastersproduction` (no "logistics"). My `MARKETING/12-INSTAGRAM-PLAYBOOK.md` and the JSON-LD `sameAs` block assumed `@showmastersproductionlogistics`. Operator picks one canonical handle and we update the other reference.
2. **Orlando address:** IG bio shows `4501 Vineland Rd Suite 110A, Orlando, FL 32811`. Site / JSON-LD / GMB doc all show `4906 Patch Road, Orlando, FL 32822`. Two different Orlando addresses live on the same brand right now. Which is current.
3. **Operational hubs definition:** Old SMPL site (per operator screenshot) listed 8 starred states as "Operational Hubs" (CA, NV, CO, TN, GA, TX, LA, FL). My docs called Orlando + Fort Worth "hubs." Reconciled language to "two offices · eight operational hubs." Map renders 6 hub stars (CA, NV, CO, TN, GA, LA) plus the 2 office stars (Orlando-FL, Fort Worth-TX) — TX + FL state stars folded into the office stars to avoid double-marking. If operator wants the original 8-star aesthetic restored, can split.

**Standing by on nano banana** — `BRANDING/NANO-BANANA-INTEGRATION.md` already lists everything we need from the other-agent setup.

**Files touched this turn:**
- NEW: `manifest.json`, `public/img/us-coverage-map.svg`
- NEW: `BRANDING/social/ig-pinned-01-we-make-great.svg`, `02-happen.svg`, `03-every-day.svg`, `ig-alt-stats.svg`, `ig-alt-services.svg`, `ig-alt-promise.svg`, `ig-pinned-README.md`
- EDIT: `index.html` (favicon stack expanded, hero subhead, where-preview headline, trust-strip count fix), `about.html` (favicon stack + og:url/type/twitter:card + "two offices" language), `contact.html` (favicon stack + og:url/etc), `what.html` (favicon stack + og:url/etc), `how.html` (favicon stack + og:url/etc), `where.html` (favicon stack + og:url/etc + US map insert + headline rewrite), `careers.html` (favicon stack + og:url/etc), `privacy.html` (favicon stack + og:* tags added), `terms.html` (favicon stack + og:* tags added)

Final SEO+social tag count per page: index 13 · about/what/how/where/careers/contact 14 each · privacy/terms 7 each (appropriate for noindex stubs).

---

## 2026-05-23 06:15 — BRANDING pack + 10 new MARKETING docs + HOSTING plan + bespoke service icons + nano-banana request

Picked up mid-session after the privacy/terms stubs landed. Operator gave two pivots:
1. **(1st)** "Pickup where we left off — review what jb-woodworks agent is working on; include FULL marketing plans + simpler things like how to manage IG/TikTok accounts; nothing from Sinister branding on the public site."
2. **(2nd)** "Get off Vercel; use our own shit everywhere; no AI slop, no emojis; custom SVG icons everywhere; spice up logo with many variants."
3. **(3rd)** "All logo/branding based on what the company already has — enhance, don't replace. Stand by for nano banana — will set up via other agent."

**Built this session (all at `C:\Users\Zonia\Desktop\Showmasters Site\`):**

| Surface | Detail |
|---|---|
| BRANDING/ pack | NEW folder. 25 SVGs across logos/, marks/, social/, animated/, print/. 4 docs (README, TOKENS, USAGE, CHANGELOG) + NANO-BANANA-INTEGRATION.md |
| MARKETING/ docs | 7 NEW playbook docs added (04-BOOKING-FUNNEL through 10-PRICING-NOTES) + 3 social-media docs (11-SOCIAL-MEDIA-BASICS, 12-INSTAGRAM-PLAYBOOK, 13-TIKTOK-PLAYBOOK). Updated 00-START-HERE to reference 04-13 |
| HOSTING.md | NEW. Self-host plan — 3 paths (workstation+Cloudflare tunnel / VPS+Caddy / R2+Worker), recommendation = Path A now → Path B by Q+90, anti-Vercel checklist, Caddyfile drop-in, deploy commands |
| Bespoke service icons | 6 inline SVG icons in `index.html` replaced. Old library-style icons (house/clock/cube/hex) swapped for custom event-industry glyphs: figure-pushing-road-case (stagehand), carabiner+rope (rigger), mixing-console faders (technician), scissor lift raised (lift op), comm headset+boom mic (crew lead), clipboard with checklist (logistics) |
| Emoji removal | 3 entities killed: 2× `&#10003;` checkmark → custom SVG check; `4.8★` → `4.8/5` in MARKETING/03-GMB-RANKING |

**Branding doctrine honored:** the canonical brand at `public/img/*.svg` (logo-horizontal/stacked/monogram/mark, favicon, og-card, pfp) is UNCHANGED. BRANDING/ contains either (a) canonical reproductions in different formats (mono white/black/gold, outline, watermark, vertical, flat, social-sized, animated SMIL) or (b) **explicitly tagged `[explore]` proposals** (spotlight-cone, truss, emblem-seal, hex, shield, tour-case) marked operator-review-before-public-use in BRANDING/README.

**Nano banana standing by:** wrote `BRANDING/NANO-BANANA-INTEGRATION.md` listing what showmasters lane needs from the other-agent setup (API key env var name, model id, auth header format, request/response shapes, budget cap suggestion $25/mo, local fallback storage to `public/img/generated/`, anti-slop visual review rules).

**Operator-gated (unchanged from prior session):**
- Git init + push to `Sinister-Systems-LLC/Showmasters`
- Domain/DNS for showmasters.com
- Real counsel-reviewed privacy + terms text
- Nano banana API access (in progress via other agent)
- Approval/rejection of `[explore]` BRANDING variants before any public use

**Branch:** `agent/showmasters/scaffold-and-launch` (still on this branch, no commits this session — operator hasn't OK'd a push yet)

**Files touched this session:**
- NEW: `BRANDING/` (entire folder) — 30 files
- NEW: `MARKETING/04-BOOKING-FUNNEL.md`, `05-COMPETITORS.md`, `06-CONTENT-CALENDAR.md`, `07-OUTREACH-LIST.md`, `08-LOCAL-CITATIONS.md`, `09-REVIEWS.md`, `10-PRICING-NOTES.md`, `11-SOCIAL-MEDIA-BASICS.md`, `12-INSTAGRAM-PLAYBOOK.md`, `13-TIKTOK-PLAYBOOK.md`
- NEW: `HOSTING.md`
- EDIT: `index.html` (6 service icons + 1 checkmark), `contact.html` (1 checkmark), `MARKETING/00-START-HERE.md` (added 11-13 to read order), `MARKETING/03-GMB-RANKING.md` (star → /5)
- EDIT (Sanctum side): `D:\Sinister Sanctum\projects\showmasters\_SCAFFOLD-BRIEF.md` — added canonical-location pointer so future sessions don't fragment work between Sanctum projects/ and Desktop

---

## 2026-05-23 02:25 — scaffold completed + privacy/terms stubs landed

Picked up on branch `agent/showmasters/scaffold-and-launch` mid-session. Prior session had landed the bulk of the scaffold at `C:\Users\Zonia\Desktop\Showmasters Site\` per operator decision (canonical location: Desktop, NOT `D:\Sinister Sanctum\projects\showmasters\`).

**Current state of `C:\Users\Zonia\Desktop\Showmasters Site\`:**

| Surface | Count | Status |
|---|---:|---|
| HTML pages | 9 | index, about, careers, contact, how, what, where, privacy (new), terms (new) |
| Stylesheets | 1 | `style.css` (18.5 KB) |
| Scripts | 1 | `script.js` (7 KB) |
| Branding SVGs | 24 | 12 logos, 5 marks, 2 print, 4 social, 2 animated, + README |
| Public images | 9 | favicon, og-card, 5 logo variants, 2 pfp variants |
| Hero videos | 6 | crowd, drummer, color spots, flashing, music stage, stage light |
| MARKETING docs | 4 | 00-START-HERE through 03-GMB-RANKING |
| SEO | 3 | sitemap.xml, robots.txt, JSON-LD on index |

**This session's deliverables:**

1. **Asset-path audit** — grepped every `(href|src)=` in all 7 original HTML pages; cross-checked against on-disk files. All local refs resolve EXCEPT two: `/privacy.html` + `/terms.html` referenced from every page's footer.
2. **Stub pages landed** — `privacy.html` + `terms.html` with full nav + page-header + 4-6 placeholder sections each + footer. `<meta name="robots" content="noindex,follow">` so they don't index pre-launch. Each closes with a yellow "Scaffold note" box telling the operator + future counsel to replace with counsel-reviewed language before going live.

**Operator-gated items (surfaced, not acted):**

- Whether the Site folder should be its own git repo (currently NOT initialized as git)
- Push to `Sinister-Systems-LLC/Showmasters` GitHub repo (needs auth + operator OK)
- Domain/DNS for `showmasters.com` (self-hosted per brief, not Vercel)
- Real counsel-reviewed privacy + terms text

**Branch:** `agent/showmasters/scaffold-and-launch` (already on origin)
**Scaffold brief:** `D:\Sinister Sanctum\projects\showmasters\_SCAFFOLD-BRIEF.md` (acceptance summary appended this session)

---
