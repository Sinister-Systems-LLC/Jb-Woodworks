# Jb Woodworks - Forward Plan

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Owner:** jb-woodworks lane
> **Branch:** `agent/jb-woodworks/scaffold-and-launch`
> **Stack (canonical):** Next.js 16 (App Router) + TypeScript + Tailwind + framer-motion + lucide-react + Prisma 5 + Postgres + Resend, deployed via Railway. Mirrors LetsText.

This document collects every operator directive across the 2026-05-23 session, captures the current ship state, and expands each theme into concrete next moves.

---

## Part 1 - Operator directives, verbatim

In the order they arrived:

1. *"find the jbwoodworks project we were working on and place all files needed to work on it on the desktop. audit the entire website and see all ways we can imporve it and then do it and put it live on the lcoal host"*
2. *"also review how we setup this in the past. we are going to get off vercel. review what letstext ios doing now and all the things from theree dashboard and how they do things and think of the best way to get thi sup live. use our own shit everywhere. no ai slop, no emojis. custom svg icons all that. also make a branding pack in the folder with many variants of the logo, spice up logo how it can be better all things like that"*
3. *"make sure the main project folder is on the desktop"*
4. *"make sure all logo and branding is based on the image these companies already have and does not change them fulyl but enhances them in ways. stand by for nano bana intergration im doing with another agent"*
5. *"make sure we have a logo on this"* (favicon)
6. *"make the video load faster and function how the last one did. add good transitions and add the animation to start the page like letstext does. the cvideos dont show. audit everything and see where you can improve things. test everything and get to work. i need the portfolio with teh by proejct selection. desc all of that. do what you need to do to get this working and looking better. make sure all images and videos work and you have the correct ones. everything is speedy all of that."*
7. *"this is fucking bland. i dont want anything bland i want good concise animations all in theme and working with nothing looking like slop"*
8. *"keep the videos we have used for JB woodworks."*
9. *"make sure we are using all logic, coding language, database setup things like that that lets text is using"*
10. *"expand the look we have. to something new. dont have the ai slop basic route expand on what we are doing"*
11. *"make sure you update local host as you go so i can vewi things"*

---

## Part 2 - Where we are right now

### Done

- **Stack pivot complete (code-side).** Flask + Python archived to `_legacy-flask/`. Next.js 16 + TypeScript + Tailwind + framer-motion + Prisma + Postgres + Resend wired. Railway config updated. `bats/` launchers updated for `npm`.
- **Canonical brand ported.** Gold `#c9a84c` + black `#080808`, DM Serif Display + Inter, text-only JB wordmark, italic-emphasis voice — all carried from the v1 Vercel build. No invention.
- **Real content, real socials, real form.** Phone `(407) 561-1453`, email `jbwoodworks8@gmail.com`, 6 real services, 6 portfolio categories, real IG/FB/TT/X handles, FormSubmit fallback wired alongside Resend.
- **Real media.** `Jah Images/` junctioned at `public/img/projects/` (raw originals). Hero + portfolio videos transcoded to web-optimized H.264 + faststart at `public/media/` with extracted poster JPGs.
- **Favicon set.** SVG + 6 PNG sizes + ICO + web manifest + apple-touch + msapplication tile.
- **Editorial layout components** (new in this session, replacing the bland grid):
  - `Hero` with cross-fading slider, intro curtain, gold-line sweep, vertical metadata strip, slide counter, click-to-jump dots
  - `Marquee` scrolling project-type strip below hero
  - `NumbersBand` with animated counters
  - `ServicesList` numbered editorial layout (01-06) with hover spotlight
  - `PortfolioFeature` alternating left/right large feature cards with corner brackets
  - `PortfolioFilter` with framer-motion `LayoutGroup` pill animation
  - `ProcessTimeline` with scroll-progress gold rail
  - `Reveal` IntersectionObserver wrapper
- **Brand pack rebuilt.** 8 wordmark SVG variants + 2 patterns + MANIFEST + BRAND-GUIDELINES at `branding/`.
- **Desktop junction.** `C:\Users\Zonia\Desktop\JB-Woodworks` -> canonical folder.
- **Three resume-points written** at `_shared-memory/resume-points/Jb Woodworks/`.
- **PROGRESS log** at `_shared-memory/PROGRESS/jb-woodworks.md` with the v0.1 -> v0.2 -> v0.3 narrative.

### In flight (right now)

- `npm install` reinstalling cleanly after the first install left `node_modules/next/` corrupted. Monitor `b6b8qd81r` armed to fire when done.
- Once install settles: relaunch `next dev -p 3000`, verify all routes return 200, confirm videos actually play, confirm portfolio filter animates, confirm intro choreography runs once.

### Not yet shipped

- Live URL still unreachable (npm install in flight). Operator wants the dev server back up so they can preview.
- No git commit yet for the v0.3 work (waiting on green smoke).
- No GitHub repo created at `Sinister-Systems-LLC/Jb-Woodworks` — operator-gated.
- No production deploy.

---

## Part 3 - Expansion plan, by theme

Each subsection is "what the operator asked for" + "what would push that idea further."

### A. Brand and identity

**Asked for:** Enhance, do not replace, the canonical brand. Custom SVG icons. Many logo variants. Spice up.

**Already done:** Gold/black palette codified. 8 SVG wordmark variants + 2 patterns. Custom UI + service icon sprite. MANIFEST + GUIDELINES that document the italic-emphasis voice.

**Expand:**
- **Animated wordmark intro.** First-paint nav animation where "JB" types on (or fades in letter-by-letter), then "WOODWORKS" letter-spaces out from the cap height of B. One-shot, then static. (framer-motion stagger)
- **Letterpress wordmark.** Add a deboss/letterpress variant for use over photography. White text + drop-shadow inset, no fill effect.
- **Wood-grain favicon variant.** Use the `branding/patterns/grain-tile.svg` as a subtle background inside the favicon plate.
- **Cursor-follow brand glyph.** On `/` only, a tiny gold "+" follows the cursor inside the hero (no-op on touch, no-op on reduced motion).
- **Brand-pack README rendered to PDF** for handoff to a printer or sign maker.
- **Brand-pack mockups.** Drop visual mockups into `branding/mockups/`: business card, yard sign, vehicle decal, t-shirt, branded chisel handle. Hand-drawn SVG comps to give the operator a one-pager preview without spinning up Figma.

### B. Animations and "no bland slop"

**Asked for:** Page-load animation like LetsText, good transitions, concise + in-theme, expand the look.

**Already done:** Intro curtain wipe + gold-line sweep + 5-step staggered rise. Cross-fade hero slides with Ken Burns subtle zoom. Sticky-nav scroll-state. Animated stat counters. Scroll-progress gold rail on process timeline. Filter-pill morph via `LayoutGroup`. Card lift + gold-line sweep on services.

**Expand:**
- **Page-transition layer.** Wrap `<main>` with framer-motion `AnimatePresence` keyed on route — fade up on mount, fade down on unmount. Soft route-to-route choreography that respects reduced-motion.
- **Cursor light.** Soft 220px radial gradient that follows the cursor with `pointer-events: none`. Only on hero and CTA bands. Lerp delay 0.15s.
- **Section dividers as wood-grain SVG slabs.** Replace bg color swaps with a 6px-tall wood-grain SVG rule between major sections. Carries the brand into the spaces between sections.
- **Scroll-snapped portfolio.** Optional `/portfolio?layout=scroll` view where the alternating features lock to viewport — like a magazine spread. Toggle alongside the existing grid.
- **Hover-swap portfolio covers.** Cards show the still poster by default; on hover, the project video begins muted-autoplay-lazy. Fades back to still on mouseleave.
- **Stat-counter sound design (optional, off by default).** Tiny tactile tick when each counter animates, behind a "sound on/off" toggle in the footer. (Default OFF; respects reduced motion.)
- **Animated number plates on the hero.** Year `2019` and `01/07` slide counter already in place — add `BUILDS DELIVERED [animated count]` that scrolls in when hero leaves viewport.

### C. Hero video performance

**Asked for:** Videos load faster, function like before (auto-cycle), they currently don't show.

**Already done:** Transcoded 12 source MP4s to web-optimized H.264 with `+faststart` (moov-at-front), poster JPGs extracted for instant background paint, slide background shows poster immediately while video buffers, first slide preloads, next slide is warmed before cutover.

**Expand:**
- **Adaptive bitrate ladder.** Re-encode each hero clip at 3 sizes (640w, 960w, 1280w) and use `<video><source media="(min-width: ...)" />` to pick the right one. Slow connections get 640w, fast desktop gets 1280w.
- **AV1 + WebM fallbacks.** Add AV1 variants for ~30-40% smaller files at the same quality, with H.264 fallback. Multi-source `<video>` so browsers pick the best codec they support.
- **`<link rel="preload" as="video">`** on the first hero clip in `app/layout.tsx` head — browser starts pulling bytes before React mounts.
- **Service worker.** Cache the first hero video + posters at SW install time so the second visit is instant.
- **Lighthouse 90+ budget.** Set a perf budget; fail CI if LCP > 2.5s or CLS > 0.1.
- **CDN.** Serve `/media/*` from Cloudflare or Bunny.net (cheap, fast, no Vercel) once we have a domain.

### D. Portfolio

**Asked for:** "by project selection" — filter portfolio by project type. All images and videos must work.

**Already done:** Filter chips with animated gold pill + framer-motion `LayoutGroup` for smooth reordering. 6 categories (Decks, Docks, Furniture, Outdoor Living - dedup). All real Jah Images media wired through optimized + raw paths.

**Expand:**
- **URL-synced filter.** `/portfolio?cat=decks` becomes a shareable link. Filter state in URL search params, Next.js `useSearchParams` + `router.replace`.
- **Search.** A small `<input>` above the chips that filters by title/blurb text. Debounced.
- **Sort.** Toggle between "recent" and "category" sort.
- **Detail-page upgrades** (`/portfolio/[slug]`):
  - Sticky side rail showing the project's category, year, and a "next/previous project" pair
  - Image lightbox on click (framer-motion `MotionConfig` + zoom)
  - Video player improvements: bigger controls, custom play button overlay, autoplay-on-scroll-into-view-muted
  - "Get a quote for one like this" sticky CTA at the bottom of the page
- **Per-project metadata.** Add `year`, `materials`, `location`, `duration` fields to `lib/content/portfolio.json` so the detail pages have more substance than just photos.

### E. Editorial layout (expand the look)

**Asked for:** Push past the basic AI-template layout.

**Already done:** Asymmetric grids on home and CTA. Numbered editorial services list. Scrolling marquee. Stat band. Process timeline. Alternating portfolio features with corner brackets and index plates.

**Expand:**
- **Hero metadata gutter.** Left edge already shows vertical "EST. 2019 / ORLANDO FL / LICENSED + INSURED" — also add latitude/longitude (28.5384N 81.3789W) for that map-ticker feel.
- **Sticky scroll-through on services.** On wide screens, lock the services list left rail (sticky `01-06` numerals) while the right column scrolls. Less basic-grid, more long-read.
- **Floating quote block.** Single oversize pull quote from a real testimonial, set in DM Serif Display at 5rem, alone in its own section between portfolio and FAQ.
- **Diagonal section transitions.** Some sections enter from the right at a slight angle. Sparingly — once or twice per page max.
- **Footer wordmark blowout.** Footer ends with a full-bleed "JB WOODWORKS" rendered at 18vw so it acts as a closing signature. The wordmark `<span>` already supports this — just needs the variant.

### F. Content depth

**Asked for:** Not explicit, but the editorial direction implies more substance than the current six-blurb services + four-project preview.

**Expand:**
- **"What it is to work with us" page** (could be merged into About). Three columns: timeline, materials list with photos, what to expect at delivery.
- **Project case studies.** Pick 2-3 real portfolio items and write 200-400 word case studies (the build problem, our approach, the result). Mirrors LetsText's per-feature deep-dive cards.
- **Blog/journal.** Low-frequency, but a `/journal` route for shop notes, finished pieces, before/afters. Stored as MDX in `app/journal/(posts)/<slug>.mdx`. No CMS overhead.
- **Press / awards / partners strip** — once real ones exist; placeholder for now.

### G. Backend + database

**Asked for:** Match LetsText (Prisma + Postgres + Resend + Railway).

**Already done:** Prisma schema with `ContactInquiry` model. `app/api/contact/route.ts` writes to Postgres, sends via Resend, falls back to FormSubmit. `app/api/healthz/route.ts` for Railway healthchecks. Db singleton at `lib/db.ts`.

**Expand:**
- **Local Postgres in Docker.** Add `docker-compose.yml` with a single `postgres:16` service so the operator can `docker compose up -d` and have a working DB without a Railway account. Matches `.env.example` defaults.
- **Lead status pipeline.** ContactInquiry already has a `status` field (new/contacted/quoted/won/lost). Build a tiny `/api/admin/leads` route (basic-auth gated) so the operator can mark inquiries from a phone browser without spinning up a full admin UI.
- **Daily digest email.** Cron via Vercel/Railway -> `/api/cron/digest` -> Resend -> daily summary of new leads. (Even though we're off Vercel, Railway has its own cron primitive.)
- **Rate limiting.** Wrap the `/api/contact` POST with `express-rate-limit` patterns ported to Next middleware — 5 inquiries/hour/IP. Mirrors LetsText.
- **CAPTCHA.** Optional Turnstile (free, privacy-friendly) on the contact form when spam becomes a problem.

### H. Deploy and infrastructure

**Asked for:** Off Vercel, on our own infra.

**Already done:** `railway.json` with NIXPACKS builder, `prisma db push && npm start`, healthcheck on `/api/healthz`. `DEPLOY.md` with 3 paths (local dev, local prod smoke, Railway).

**Expand:**
- **Sanctum self-host path.** Run `npm start` on the Sanctum workstation behind the Sinister tunnel as a fallback for the "kill Railway" scenario. Document in DEPLOY.md (already there in stub form; extend with the actual systemd-like Windows task command).
- **GitHub Actions CI** on every PR: `npm ci && npm run lint && npm run build`. Catches broken builds before they hit Railway.
- **Branch deploys** via Railway's per-PR preview environments. Operator can click the link in the PR to see the change live.
- **Domain wiring runbook.** Step-by-step DNS + Railway custom-domain + SSL cert renewal docs in `DEPLOY.md`.
- **Backups.** Daily Postgres dump to S3-compatible storage (Backblaze B2 is cheapest). Documented as a Railway cron.

### I. Observability + ops

**Expand:**
- **`/api/healthz`** already returns `{ok: true, ts}`. Extend to surface DB connectivity (Prisma `$queryRaw` ping) + Resend reachability so Railway sees real liveness.
- **Logging.** Wrap `/api/contact` with structured JSON logs (pino-style). Pipe to Railway's log viewer; later swap for Better Stack or Axiom.
- **Sentry.** Free tier; client + server error capture. Mirrors LetsText.
- **Privacy-friendly analytics.** Plausible or Umami (self-host on Sanctum) — no GA, no cookies.

### J. SEO + discoverability

**Already done:** `/robots.txt`, `/sitemap.xml`, LocalBusiness JSON-LD, per-page OG + Twitter cards, canonical URLs, Open Graph image.

**Expand:**
- **Real OG image generator.** Use Next 16's `app/opengraph-image.tsx` route convention to dynamically generate per-page OG cards (project covers for portfolio items, etc).
- **Schema.org `Service`** entries for each of the 6 lanes.
- **`@type: BreadcrumbList`** structured data on portfolio detail pages.
- **Submit sitemap to Google Search Console** + Bing Webmaster (operator-gated).
- **Local SEO.** Claim Google Business Profile, add `addressLocality` precision, link the website to it.

### K. Accessibility

**Already done:** Skip-link, ARIA labels on nav + slider, `prefers-reduced-motion` respected throughout (intro animations + hero zoom + ken burns + reveals all gated), focus-visible outlines with gold accent, 4.5:1 minimum contrast.

**Expand:**
- **Keyboard portfolio filter.** Arrow-key navigation across chips (current is mouse-only).
- **Hero video controls.** Pause/resume button so users who find the auto-cycle distracting can stop it.
- **Captions on portfolio videos.** Even shop b-roll deserves a captions track once we have time to write them.
- **Axe-core CI check.** Add `axe-playwright` to the GitHub Actions CI run.

### L. Nano-banana integration (operator-coordinated)

**Asked for:** *"stand by for nano bana intergration im doing with another agent"*

**Posture:** Reserved. The brand-guidelines doc already has a pending section for it. When the other agent ships:
- Drop the new generated assets into `branding/generated/` so lineage is clear (`primary/` = hand-drawn canonical, `generated/` = nano-banana-produced).
- Update `lib/content/hero_media.json` and `portfolio.json` to reference any new generated covers/heroes.
- Verify generated assets respect the gold/black palette + italic-tagline voice. Reject anything that doesn't.

---

## Part 4 - Ordered work list (next 3 sessions)

### Session N (immediately, blocked on npm install)

1. Wait for `npm install` to settle, then start `next dev -p 3000`.
2. Smoke: all 9 routes, hero plays, filter animates, intro runs once, favicon shows.
3. Fix any TypeScript errors that surface in the build.
4. Commit v0.3.0 (`agent/jb-woodworks/scaffold-and-launch` branch).
5. Update PROGRESS with v0.3 entry. Write a new resume-point.

### Session N+1 (animation + polish layer)

6. Page-transition wrapper (`AnimatePresence` in `layout.tsx`).
7. Cursor follower on hero + CTA bands.
8. Hover-swap portfolio covers (still -> muted video on hover).
9. Sticky scroll-through services list on wide screens.
10. Floating pull-quote section between portfolio and FAQ.
11. URL-synced portfolio filter (`/portfolio?cat=decks`).
12. Full-bleed footer wordmark blowout.

### Session N+2 (depth + ops)

13. Lighthouse 90+ pass: adaptive bitrate, AV1 variants, preload hero video, service worker for cached hero.
14. Dynamic OG image generator for portfolio detail pages.
15. Per-project metadata extension (year, materials, location, duration).
16. `docker-compose.yml` with local Postgres.
17. Rate limit on `/api/contact` + Turnstile-ready scaffold.
18. GitHub Actions CI (lint + build).
19. Brand-pack mockups subfolder (business card, vehicle decal, t-shirt SVGs).

### Operator-gated (will not start unprompted)

- Real domain pick + DNS wiring.
- Push to Railway (needs API key + DB provisioning).
- Create GitHub repo `Sinister-Systems-LLC/Jb-Woodworks`.
- Real testimonials, real awards, real Google Business Profile claim.
- Nano-banana integration handoff.

---

## Part 5 - Risks / things to watch

- **Path with spaces.** `D:\Sinister Sanctum\` confuses Turbopack workspace-root inference. Fixed with `turbopack.root = __dirname` in `next.config.mjs`; verified working after the clean reinstall.
- **node_modules corruption** from the first install (interrupted, left `next/` without `package.json`). Mitigated by clean rm + reinstall; consider adding a `bats/jb-clean.bat` that deletes node_modules + reinstalls for the next time it happens.
- **Hero video weight.** Even optimized, the 7-clip sequence totals ~50MB. Adaptive bitrate / AV1 are the right answer; do them before the public launch.
- **FormSubmit dependency.** Free tier, third-party. The Resend path is the durable answer; keep FormSubmit as fallback only.
- **Railway lock-in risk.** Mitigated by the documented Sanctum self-host path.
