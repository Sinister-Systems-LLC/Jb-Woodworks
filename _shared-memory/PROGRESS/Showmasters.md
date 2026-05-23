<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Agent: Showmasters

Append-only progress log. Most recent at top.

---

## 2026-05-23 10:30 — Pills killed · path floater · marquee · nav-active · legal pack · 5-video hero · 25 images

Operator screen-shared a flurry: kill the AI-slop pills, build a path-tracker floater, footer needs Florida/Texas + "we work everywhere" + cookie/privacy/legal protection, JB-Woodworks-style services marquee, header should show what page you're on, hero video must be insane crowd / LED-walls / lights (not the dance-floor squares), and the home intro should play on every refresh.

**Built this turn:**

| Surface | Detail |
|---|---|
| **Pills + branch-tag stripped** | PowerShell pass killed 19 `.lg-pill is-gold` instances across every HTML file + the 1 `.branch-tag` ("WHERE TO START") on the homepage. Operator pointed at the dark "WHAT WE DO" pill in image #2 as the slop tell |
| **Path-tracker floater** (`#smplPath`) | Fixed bottom-right card on the 5 path pages (what/how/where/shows/order). 5 mini-dots show visited (✓ gold), current (gold ring), next-unvisited (pulsing gold border). Three buttons: ← Start, Next: <name> →, Quote. Visited persists via sessionStorage. Dismissible via the × — stays dismissed for the session. Mobile-responsive |
| **Services marquee** (`.smpl-marquee`) | Vanilla CSS port of JB Woodworks' `components/sections/marquee.tsx` — flex track of 36 items (12 crew categories × 3 cycles), DM Serif italic at clamp(1.6rem, 4vw, 2.8rem) in dimmed cream, gold "+" separators in Inter 900, edge-gradient masks, 56s linear infinite loop, hover-pauses, prefers-reduced-motion respected. Sits on the homepage between hero/trust-strip and the branch section |
| **Nav active state** (`is-active` + `is-visited`) | JS detects current pathname + matches `.nav-links a` and `.mob-link` href. Adds `.is-active` (gold text + gold gradient underline 2px below the nav) or `.is-visited` (small gold dot after the label for the 5 paths). Sources visited list from the path floater's sessionStorage so the two systems share state |
| **Hero video carousel** | Now 5 clips (dropped `hero-color-spots.mp4` per operator screenshot #1): crowd-hands → flashing-lights → music-stage → drummer → stage-light. `.hero-overlay-strong` + `.hero-vignette` overlays plus CSS `filter: contrast(1.08) saturate(1.14) brightness(0.92)` on the video itself — pushes warmth + depth |
| **Homepage intro gate rewired** | Full stage-cue animation now fires on EVERY load + refresh of the homepage (no sessionStorage gate). All other pages skip the full intro entirely and just reveal hero copy. Between-page navigation always plays the new SMPL flash (~340ms: veil drop + SMPL wordmark fade + gold scan-bar pass) |
| **Footer unified across 22 pages** | New "Locations" column on the right with phone + email + Florida HQ address (4906 Patch Road, Orlando, FL 32822) + Texas Hub (6340 Lake Worth Blvd, Dallas, TX 75201) + the "we crew shows everywhere on the map" tag. Brand column gained social icons (IG/FB/LI as circle-bordered SVGs in gold). Bottom legal row now: Privacy · Terms · Cookies · Accessibility · Contact |
| **Legal pack written** | `privacy.html` rebuilt with a 13-section policy (plain-summary callout, who we are, what we collect by visitor / form / applicant / client / employee, how we use it, who we share it with, cookies cross-link, retention timelines, CCPA/GDPR-aware rights, security, children, international transfers, third-party links, change-log, contact). New `cookies.html` with a table of every cookie we use + browser opt-out paths + DNT/GPC respect. New `accessibility.html` with WCAG 2.1 AA target + prefers-reduced-motion honored + contact-for-accessibility. `terms.html` rebuilt with 12-section TOS (agreement, site-vs-services distinction, acceptable use, submissions, IP, third-party links, warranty disclaimer, liability cap $100, indemnification, FL governing law, changes, contact). All three flagged for counsel review in callout boxes |
| **Order page enhancements** | Added a 4-card trust strip above the form (24/7 orders desk · same-day response · 72hr invoice · W-4 employees) and a 3-step "what happens next" timeline (drop the brief → same-day response → estimate then crew). `.order-trust` + `.order-next` CSS appended |
| **Quick copy clean-up** | More em-dashes killed in how.html body copy. `where.html` traveling-crew section tightened |

**Generated images now live (from prior batches):**
- 6 service-card heros wired into what.html role-cards
- 2 city heros wired into orlando.html + dallas.html page-headers
- 12 blog heros staged in `public/img/generated/blog/` (await blog template)
- 4 social templates staged in `BRANDING/social/templates/` (reel-anticipation still needs re-fire)

**Doctrine honored:**
- Pills removal followed the same "kill the AI section-tag pattern" pass from the 09:15 turn
- Marquee ported from a sibling-lane sister tool (JB Woodworks) — cross-agent code-reuse via on-disk read, no inbox round-trip needed
- Cookies banner sets `smpl_cookies_v1` in localStorage; path tracker uses `smpl_paths_visited` in sessionStorage; intro uses no storage now (homepage refresh always plays)
- Per-agent branch discipline still honored (no git ops this turn; operator hasn't OK'd a push yet)

**Still operator-gated:**
- Counsel review on privacy / terms / cookies / accessibility (callout boxes flag specifics)
- Direction lock on new hero carousel + service-card photos + city-page heros + marquee + path floater + nav active states
- Same 8 unchanged from prior entries: IG handle, Orlando address, git init + push, domain/DNS, VPS for app-v2, `[explore]` BRANDING approval, reel-anticipation re-fire, blog template build to consume the staged blog heros

---

## 2026-05-23 09:25 — 25 brand images shipped · hero carousel · faster page transitions · operator-voice copy pass

Operator drops several asks back to back: (1) complete the standing work-list, (2) faster between-page animations, keep the full intro for the home, (3) wording must be operator voice not AI-slop (professional, concise, intelligent, direct), (4) intro plays on every refresh of the home page, (5) hero video should be a complex crowd / LED-wall / lights showcase, (6) "don't use this one" (pointed at the color-spots dance-floor video).

**Built this turn:**

| Surface | Detail |
|---|---|
| **Nano-banana batch 2** | 6 service-card heros (stagehand, rigger, technician, lift-operator, crew-lead, logistics). All status=ok, ~7s each, $0.24. All PASS anti-slop on visual review |
| **Nano-banana batch 3** | 2 city heros (orlando-hero, dallas-hero) + 4 social templates (reel-loadin, reel-truss, ig-square-haze, ig-square-cone) + 11 blog heros (load-in-checklist, focus-call, road-case-lifecycle, hub-vs-office, aca-compliance, w4-vs-1099, 72-hour-invoice, rigger-day, trade-show, festival-load-in, corporate-keynote). 17 of 18 status=ok ($0.66 + reel-anticipation didn't land, can re-fire). Meta sidecars next to every PNG |
| **What.html service cards wired** | 6 of 12 role-cards now have generated hero photos (cards 01/02/03/06/07/12). Added `.role-hero` CSS with full-bleed top strip, drops the SVG icon when present. Other 6 cards keep the SVG-icon look |
| **Orlando + Dallas pages wired** | New `.page-header-city` CSS treats the header as a cinematic photo backdrop with dual-gradient + brand overlay. Orlando uses orlando.png (dusk skyline across Lake Eola), Dallas uses dallas.png (skyline with Reunion Tower). Headline + subtitle stay readable on top |
| **Hero video carousel — restored + de-slopped** | Replaced single-video hero with 5-video carousel: hero-crowd-hands (8s, the insane crowd shot operator asked for) → hero-flashing-lights (6s) → hero-music-stage (7s) → hero-drummer (6s) → hero-stage-light (6s). Cycle ~33s. KILLED hero-color-spots.mp4 from the rotation per operator screenshot ("don't use this one"). Added beefier `.hero-overlay-strong` + `.hero-vignette` overlays + CSS `filter: contrast(1.08) saturate(1.14) brightness(0.92)` grade on the video itself — pushes warmth + depth so the clips read brand-on-brand instead of generic stock |
| **Page-transition redesign** | `#smplTx` now renders a brief SMPL wordmark + gold scan-bar sweep (~340ms total) on every internal nav click. Was previously just a black veil + bar — now a true "simple SMPL animation" per operator ask |
| **Homepage intro gate rewired** | Full stage-cue intro now fires on EVERY load + refresh of the homepage (not sessionStorage-gated). All other pages skip the full intro and just reveal their hero text. `?intro=force` overrides for any page; `?intro=skip` suppresses for debug |
| **Copy audit + operator-voice rewrite** | 10 " ,  " find-replace typos fixed across 5 HTML files via batched PowerShell pass. Major hand-edits on index.html (hero sub + branch nodes + where-preview + CTA body + form-success + footer brand), what.html (12-card subtitle + 6 role-card descriptions), about.html (subtitle + intro paragraphs + "Three divisions" line + values list em-dashes), how.html (subtitle + 8 body em-dashes replaced with periods), where.html (traveling-crew section), orlando.html (subtitle tighten), dallas.html (subtitle tighten). Removed: "biggest moments in live entertainment", "boring in the best possible way", "the kind you can trust on day one", "shape of the show shows you the route", "live events of every shape", "we believe / we pride / passionate about" never-existed-here-but-watched-for, " — " em-dashes interrupting prose. Kept: brand line "We Make Great Days Happen, Every Day", testimonial verbatim quotes, UI-label em-dashes ("Stagehand — Audio"), domain language like "Crew Lead" / "load-in" / "ACA compliance" |
| **Brand memory at sinister-generator** | NEW `projects/sinister-generator/memory/per-project/showmasters/BRAND.md` — palette, voice, anti-slop overrides, prompt cookbook for 4 archetypes. Canonical brand SVGs copied to `reference/` (og-card, pfp-square, logo-horizontal, us-coverage-map). `_prompts/load-in-archetype-v1.md` captured + extended with the direction-lock note |
| **Inbox triage** | Two `[BROADCAST]` / `[UPDATE]` messages from general (EVE) ACK'd via cross-agent `2026-05-23T0855Z-showmasters-to-general-ack-nano-banana.md`. Source JSONs archived to `inbox/showmasters/_archive/`. Heartbeat marker written |
| **Plan file** | NEW `_shared-memory/plans/showmasters-2026-05-23-finish-everything/PLAN.md` — full work-list + doctrine alignment + execution order + reversibility notes |
| **One-shot fire scripts (reusable)** | `projects/sinister-generator/source/_one_shot_smpl_v1.py` (load-in archetype), `_one_shot_smpl_service_cards.py` (6 service heros), `_one_shot_smpl_cityblog_social.py` (18-image batch). Future agents copy + edit subjects |

**Cost this turn:** ~$0.94 across 25 generated images (gemini-2.5-flash-image @ $0.039 each). Well under the $25/mo soft budget.

**Generated image inventory** (all PASS anti-slop unless noted):
- `outputs/showmasters/blog-heroes/`: load-in-archetype-v1, orlando-hero-v1, dallas-hero-v1, blog-load-in-checklist-v1, blog-focus-call-v1, blog-road-case-lifecycle-v1, blog-hub-vs-office-v1, blog-aca-compliance-v1, blog-w4-vs-1099-v1, blog-72-hour-invoice-v1, blog-rigger-day-v1, blog-trade-show-v1, blog-festival-load-in-v1, blog-corporate-keynote-v1
- `outputs/showmasters/service-illustrations/`: stagehand-v1, rigger-v1, technician-v1, lift-operator-v1, crew-lead-v1, logistics-v1
- `outputs/showmasters/social/`: reel-loadin-v1, reel-truss-v1, ig-square-haze-v1, ig-square-cone-v1 (reel-anticipation MISSING — re-fire next turn)

**Site wiring (where generated images now live):**
- 6 service heros → `public/img/generated/services/<slug>.png` → wired into what.html role-cards 01/02/03/06/07/12
- 2 city heros → `public/img/generated/cities/{orlando,dallas}.png` → wired into orlando.html + dallas.html page-headers as cover background with overlay
- 12 blog heros → `public/img/generated/blog/<slug>.png` → staged (no blog index yet to consume them)
- 4 social templates → `BRANDING/social/templates/<slug>.png` → staged (operator drops typography on top in IG/Reels editor)

**Open / next-turn:**
- Re-fire `reel-anticipation` social template (the one that didn't land)
- Visual review by operator: new hero carousel (5 videos), service-card photos, city-page heros, page transition feel — direction lock or call out specific images to swap
- Copy audit on remaining lower-priority pages (faq, glossary, press, crew, case-studies, insurance, houston, tampa, shows, order)
- Bring `reel-anticipation` back in
- Build the actual blog index/template so blog-heros can land

**Still operator-gated (unchanged):**
- IG handle canonical pick (`@showmastersproduction` vs `@showmastersproductionlogistics`)
- Orlando address canonical pick (4501 Vineland vs 4906 Patch Rd)
- Git init + push to `Sinister-Systems-LLC/Showmasters`
- Domain/DNS for showmasters.com
- Counsel-reviewed legal text (privacy + terms)
- VPS provisioning for app-v2 Postgres + Next.js
- Approval of `[explore]` BRANDING variants before public use
- Direction lock on the new image batch

---

## 2026-05-23 08:56 — Nano-banana FIRST FIRE shipped · SMPL archetype lands clean · brand memory seeded

Resume from prior 09:15 entry. Two inbox broadcasts landed since last session: (a) `tools/nano-banana/` wired by general/EVE, (b) image-gen promoted to `projects/sinister-generator/` with showmasters output routing. Operator set `GEMINI_API_KEY` + enabled Cloud billing — fully unblocked.

**Built this turn:**

| Surface | Detail |
|---|---|
| Brand memory at sinister-generator | NEW `projects/sinister-generator/memory/per-project/showmasters/BRAND.md` — full palette, voice, anti-slop overrides (no daylight, no centered performer, no in-frame logos), prompt cookbook for the 4 archetypes (service-card / blog-header / city-hero / social-template). Reference dir populated with canonical brand SVGs (og-card, pfp-square, logo-horizontal, us-coverage-map). `_prompts/` subdir seeded |
| Inbox triage | Two broadcast messages ACK'd via `_shared-memory/cross-agent/2026-05-23T0855Z-showmasters-to-general-ack-nano-banana.md`; source JSONs archived to `inbox/showmasters/_archive/` |
| Heartbeat | `_shared-memory/heartbeats/showmasters.last` written (Rule 9, file-based since sinister-bus MCP isn't loaded in this session) |
| **FIRST GENERATION** | `outputs/showmasters/blog-heroes/load-in-archetype-v1.png` — 1024×1024, 1.1 MB, 7.5 s, $0.039. SMPL archetype: silhouetted stagehand pushing road case down dim backstage corridor, amber par-can side-light, gold floor reflection, faint magenta/blue wash deep in the right vanishing-point (reads as moving-head bleed, on-brand). Meta sidecar saved next to PNG. Winning prompt captured at `memory/per-project/showmasters/_prompts/load-in-archetype-v1.md` |
| One-shot fire script | `projects/sinister-generator/source/_one_shot_smpl_v1.py` (the script that fired it — reusable template for v2/v3 variants) |

**Anti-slop verdict (pre-promotion):** PASS. No text, no UI cruft, no daylight, palette holds (`#0A0A0F` bg + amber gold pool), subject in left third per brief, vanishing point right per brief, crew as silhouette not portrait per brand-rule.

**Operator review path:**
- Direct: `D:\Sinister Sanctum\projects\sinister-generator\outputs\showmasters\blog-heroes\load-in-archetype-v1.png`
- Satellite junction: `C:\Users\Zonia\Desktop\Sinister Generator\showmasters\blog-heroes\load-in-archetype-v1.png`

**Workflow doctrine honored:**
- One image first (per WORKFLOW Lesson 3) — no $0.12 burned on assumed variants
- Brand-lock suffix INCLUSIVE (per Lesson 2) — `SMPL_STYLE` describes the brand, doesn't strip it
- Meta sidecar written (per anti-pattern #4 — never skip)
- Winning prompt copied to `_prompts/` so future agents grep instead of starting blind

**Standing by on operator 👍 / 👎 for direction lock.**

If 👍 → fire 2 variants at 21:9 wide aspect (pass `og-card.svg` + a wide reference as first ref per Lesson 6), then move to subject #2 in the day-one list (rigger service-card hero).

If 👎 → no variants. Re-brief, single re-fire.

**Day-one work list (still on-deck, all unblocked):**
- 12 blog headers (load-in checklist, ACA compliance, road-case lifecycle, focus call, hub vs office, etc.)
- 2 city hero strips (Orlando, Fort Worth) at 21:9
- 5 social templates (Reels covers 9:16, IG carousel 1:1)
- 6 service-card hero illustrations (stagehand, rigger, tech, lift, lead, logistics)

**Cost so far this turn:** $0.039 (1 image at `gemini-2.5-flash-image`). Soft budget $25/mo = ~640 images headroom.

**Still operator-gated:**
- Direction thumb on `load-in-archetype-v1.png`
- Same 8 unchanged from prior entry: nano-banana set (now ✅ DONE — Gemini key + billing live), IG handle canonical pick, Orlando address canonical pick, git init + push, domain/DNS, counsel-reviewed legal text, VPS for Postgres, `[explore]` BRANDING variants approval

---

## 2026-05-23 09:15 — Local server live · stage-cue intro replaced Digital-Loom · home de-slop · live-site content sync

Operator drops in rapid order: "open the website on local host" + "this entire website looks like ai slop... change the start animation, it looks shitty" + "add the elements from showmasters they have... audit all tabs they have... where, what, how, about, careers."

**Built this turn:**

| Surface | Detail |
|---|---|
| **Local dev server** | `python -m http.server 8080` running in background from `C:\Users\Zonia\Desktop\Showmasters Site\`. All 9 HTML routes verified 200. Browser launch fired |
| **NEW intro animation** | Killed the 90-thread "Digital Loom" particle canvas (generic AI-template look — same pattern LetsText uses). Replaced with stage-cue scan: dark veil + horizontal gold scan-bar sweeps L→R, SMPL letters ignite in its wake (S→M→P→L at 34/46/58/70% of scan), tagline + gold rule fade in after scan completes, veil rises like a stage curtain. Pure CSS keyframes — no canvas, no RAF. ~2.0s total. Brand-specific not generic. sessionStorage key bumped `smpl_intro_seen` → `smpl_intro_v2_seen` so anyone who saw the old intro gets the new one on next visit |
| **Live-site content sync** | Fetched showmasters.com/ + /what + /how + /where + /about + /careers via WebFetch. Patched missing pieces: testimonial updated to exact P.D. quote ("...Dion was absolutely wonderful to work with..."), dual hero CTAs ("Get Started" + "Get an Estimate" — matches live), "Welcome to Show Masters" about-page tag, "First-class service, 1,700+ clients served" headline, ACA-compliance + proper-worker-classification lines added to /about values, Personnel Coordinator + Sales + Regional Manager added as careers roles, jib camera / graphics / teleprompter added as technician specialties, General Floor Crew / Production Assistant added to stagehand roles, application-process paragraph with PDF-resume guidance |
| **"Order Online" nav button on all 9 pages** | Live site has a secondary CTA next to "Get an Estimate" — replicated as ghost-style button. Now nav shows two CTAs: Order Online + Get an Estimate |
| **Home de-slop pass** | Killed the generic SaaS `section-tag` pills from 4 sections (Services / How we work / Where we work / Plan your next great day) — they were screaming AI-template. Replaced the 4-card process grid with a proper numbered editorial list (`process-numbered`): big DM-Serif italic gold numerals 01-04 sticky on the left, full editorial paragraph on the right, hairline dividers. Tightened the services-section subhead. Section now reads as confident long-form, not template-card-grid |

**Files touched this turn:**
- EDIT: `script.js` (intro replaced wholesale, sessionStorage v2 key), `style.css` (intro CSS rewritten, NEW `process-numbered` editorial list styles), `index.html` (4 section-tag removals + numbered process + dual CTA + exact testimonial), `about.html` (header rewrite + 2 new values), `careers.html` (10 role cards + apply-by-email paragraph + jib/graphics/teleprompter additions), `what.html` (Order Online nav), `how.html` (Order Online nav), `where.html` (Order Online nav), `shows.html` (Order Online nav), `contact.html` (Order Online nav)

**Local URL for operator review:** http://localhost:8080/ (and any of the 9 routes — /index.html, /what.html, /how.html, /where.html, /shows.html, /about.html, /careers.html, /contact.html, /privacy.html, /terms.html).

**Still operator-gated:**
- Same 8 items from prior entry — nano banana access, IG handle pick, Orlando address pick, git init + push, domain/DNS, counsel-reviewed legal text, VPS provision for app-v2 Postgres, approval of `[explore]` branding variants
- New: confirm the new intro feels right (refresh once to see it; sessionStorage memoizes after first view)

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
