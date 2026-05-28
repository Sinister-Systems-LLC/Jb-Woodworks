// Author: RKOJ-ELENO :: 2026-05-28
# JB Woodworks — Complete-Everything Plan (consolidated)

> **Author:** RKOJ-ELENO :: 2026-05-28
> **Lane:** jb-woodworks
> **Sources reviewed:** `_shared-memory/plans/Jb Woodworks-2026-05-23/forward-plan.md` (12-theme expansion) + `_shared-memory/plans/jb-woodworks-complete-2026-05-23T0625Z/forward-plan.md` (T#1–T#7) + `_shared-memory/resume-points/JB Woodworks/HANDOFF-2026-05-24.md` (12 operator asks) + `_shared-memory/resume-points/JB Woodworks/2026-05-27T084700Z.json` (last iter queue) + 3 brain entries (`jb-woodworks-audit-2026-05-27`, `jb-woodworks-lg-star-accent-2026-05-27`, `jb-woodworks-restore-and-audit-2026-05-27`).

## Part 1 — Past-plan audit (what's actually shipped)

### Plan A: `jb-woodworks-complete-2026-05-23T0625Z` (T#1–T#7 + brain seed)

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| T#1 | Smoke loading/legal/error/404 | ✅ | `app/loading.tsx`, `app/legal/{,privacy,terms,cookies,accessibility}`, `app/error.tsx`, `app/not-found.tsx`, `app/global-error.tsx` all present |
| T#2 | Commit v0.3.0 scaffold | ✅ | branches `agent/jb-woodworks/{scaffold-and-launch,v0.3.0-scaffold,...}` exist |
| T#4 | Image opt + lazy hero | ✅ | `next.config.mjs` `formats: ["image/avif", "image/webp"]` + `portfolio-card.tsx` uses `next/image` with `loading={eager ? undefined : "lazy"}` |
| T#5 | Sitemap mtime | ✅ | `app/sitemap.ts:11-17` `mtimeOf()` helper used for every URL |
| T#6 | Before/After slider | ✅ | `components/sections/before-after.tsx` |
| T#7 | Resend transactional contact | ⚠️ wired, env-gate | `app/api/contact/route.ts:60-87` Resend block ready; needs `RESEND_API_KEY` + `CONTACT_TO_EMAIL` on Railway |
| BRAIN | Brain entries for jbw gotchas | ✅ | 3 entries at `_shared-memory/knowledge/jb-woodworks-*.md` |

### Plan B: `Jb Woodworks-2026-05-23/forward-plan.md` (12-theme expansion)

| Theme | Done | Pending |
|-------|------|---------|
| **A. Brand** | gold/black palette, 8 wordmark SVGs, 2 patterns, MANIFEST, GUIDELINES, italic-voice | animated wordmark intro · letterpress variant · wood-grain favicon variant · cursor-follow brand glyph · README→PDF · mockups subfolder (card/sign/decal/t-shirt) |
| **B. Animations** | intro curtain · gold-line sweep · staggered rise · hero cross-fade · sticky-nav scroll-state · animated counters · scroll-progress rail · filter LayoutGroup · card hover lift · **hover-swap portfolio covers** (portfolio-card.tsx confirmed) | page-transition layer (`AnimatePresence`) · cursor light (radial gradient) · wood-grain SVG section dividers · scroll-snapped portfolio (`?layout=scroll`) · stat-counter sound · animated hero number plates |
| **C. Hero video** | 12 MP4s transcoded H.264 +faststart · poster JPGs · slide preload · next-slide warm | adaptive bitrate ladder (640/960/1280w) · AV1 + WebM variants · `<link rel="preload" as="video">` first hero · service worker cache · Lighthouse 90+ CI budget · CDN for `/media/*` |
| **D. Portfolio** | filter chips + LayoutGroup · 6+ categories · raw + optimized paths · **URL-synced filter** (`portfolio-filter.tsx:4,20,32,35,40` `useSearchParams`) · subcategory rendering · hover-swap video · `CreativeWork` JSON-LD per detail | search input · sort toggle · sticky side rail on detail · image lightbox · sticky "Get a quote" CTA on detail · per-project metadata (year/materials/location/duration) |
| **E. Editorial** | asymmetric grids · numbered services 01-06 · marquee · stats band · process timeline · alternating portfolio features · editorial portfolio header · stats strip | hero metadata gutter ext (lat/long ticker) · sticky scroll-through services · floating pull-quote section · diagonal section transitions · footer wordmark blowout (18vw bleed) |
| **F. Content depth** | 12 blog posts · 5 FAQ categories · 19 questions · about page with "how we work" 5-step | project case studies (200-400w per item) · press/awards/partners strip (placeholder OK) |
| **G. Backend** | Prisma `ContactInquiry` · POST /api/contact persist + Resend + FormSubmit fallback · /api/healthz · honeypot field | local Postgres `docker-compose.yml` · lead status admin page (`/api/admin/leads` basic-auth) · daily digest cron · rate limiting (5/hr/IP) · Turnstile CAPTCHA scaffold |
| **H. Deploy** | Off Vercel · Railway + Postgres · Vercel-proxy SSL · jb-publish.ps1 one-shot pipeline · `.railwayignore` excludes 442MB asset dump | extended DEPLOY.md (Sanctum self-host steps) · GitHub Actions CI (lint + build) · Railway PR preview deploys · domain wiring runbook · daily Postgres backup to S3-compatible |
| **I. Observability** | `/api/healthz` returns `{ok, ts}` | DB connectivity probe in healthz · structured pino-style logs · Sentry client+server · Plausible/Umami self-host |
| **J. SEO** | robots.txt · sitemap.xml (mtime-derived) · LocalBusiness JSON-LD (layout) · per-page OG + Twitter cards · canonical URLs · CreativeWork JSON-LD per project | dynamic OG image generator (`app/opengraph-image.tsx` + per-project) · Schema.org `Service` per lane · `BreadcrumbList` JSON-LD on portfolio detail · GSC + Bing sitemap submission (operator) · GBP claim (operator) |
| **K. Accessibility** | skip-link · ARIA labels · `prefers-reduced-motion` respected throughout · focus-visible gold outlines · 4.5:1 contrast | keyboard portfolio filter (arrow keys) · hero video pause/resume button · captions track on portfolio videos · axe-core CI |
| **L. Nano-banana** | 3 atmospheric backdrops shipped (about-workshop, error-quiet-shop, grain-texture) | operator-coordinated extension |

### Plan C: HANDOFF-2026-05-24.md (12 operator asks)

All 12 ✅ shipped. Open known issues:

| # | Issue | Owner | Status |
|---|-------|-------|--------|
| 1 | Railway GitHub App not on `Sinister-Systems-LLC` org | operator (1-click) | open |
| 2 | `RESEND_API_KEY` not on Railway | operator (env var) | open |
| 3 | `_legacy-flask/templates/` dead Flask copy | lane | **cleanup candidate** |
| 4 | Old `prj_xOyAeuwJHZ89KUWcqHBhq9n0Wol5` Vercel project (domains unbound) | operator (dashboard delete) | safe to delete |
| 5 | MP4 upload 1/3 timeout | mitigated by jb-publish retry | acceptable |
| 6 | Browser cache complaints | operator education | acceptable |

### Plan D: Last resume-point 2026-05-27T084700Z queue

| # | Item | Status |
|---|------|--------|
| 1 | Migrate nav/faq-tabs/portfolio-card → `.lg-*` | ✅ `app/globals.css:149-170` (`.lg-rail`/`.lg-card` added with carve-out) + components consume |
| 2 | FormSubmit OR RESEND_API_KEY | ⚠️ operator-gate (carried) |
| 3 | Lazy-load + AVIF/WebP | ✅ `next.config.mjs:17-18` + `<Image>` `loading="lazy"` |
| 4 | Sitemap lastmod auto-derived | ✅ `app/sitemap.ts:11-17` |

---

## Part 2 — Open work, prioritized for execution

### Tier 1 — ship this iter (R0/R1, code-only, high user/SEO value, low risk)

| # | Task | Effort | Why now |
|---|------|--------|---------|
| 1 | **Rate limit `/api/contact`** — in-memory token bucket, 5 POST/hr/IP, no deps | 20m | Prevent spam from a live public endpoint |
| 2 | **`/api/healthz` DB probe** — Prisma `$queryRaw\`SELECT 1\`` when `DATABASE_URL` set; degrade gracefully | 10m | Railway healthcheck reflects real liveness |
| 3 | **Hero video pause/resume button** — small absolute-positioned control in hero, respects `prefers-reduced-motion` | 25m | A11y (Theme K) + addresses "auto-cycle distracting" gripe |
| 4 | **Dynamic OG image** — `app/opengraph-image.tsx` root + `app/portfolio/[slug]/opengraph-image.tsx` per project | 40m | SEO (Theme J); rich social shares |
| 5 | **`BreadcrumbList` JSON-LD on portfolio detail** | 10m | SEO (Theme J) |
| 6 | **Schema.org `Service` block** for `/services` page | 20m | SEO (Theme J) |
| 7 | **Per-project metadata** — extend `portfolio.json` shape with optional `year/materials/location/duration`, render on detail | 30m | Theme D depth; foundation for case studies |
| 8 | **Keyboard portfolio filter** — `ArrowLeft/ArrowRight` cycle chips, `Home/End` jump to ends | 15m | A11y (Theme K) |
| 9 | **Footer wordmark blowout** — full-bleed `JB WOODWORKS` rendered at 18vw as closing signature | 15m | Theme E |
| 10 | **`_legacy-flask/` cleanup** — delete or move to `_archive/` (operator HANDOFF item 3) | 5m | Reduces "Licensed and insured" grep false positives |

### Tier 2 — next iter (R0/R1, mid effort)

| # | Task | Effort |
|---|------|--------|
| 11 | Page-transition layer (`AnimatePresence` in `app/layout.tsx`) keyed on `pathname` | 30m |
| 12 | Wood-grain SVG section dividers (`branding/patterns/grain-tile.svg` already exists) | 30m |
| 13 | Animated hero number plates ("BUILDS DELIVERED [count]") | 25m |
| 14 | Sticky scroll-through services (left rail locks, right column scrolls) | 40m |
| 15 | Floating pull-quote section between portfolio and FAQ | 20m |
| 16 | Portfolio search input above chips, debounced 200ms | 30m |
| 17 | Portfolio sort toggle (recent / category) | 20m |
| 18 | Portfolio detail sticky side rail + sticky CTA + lightbox | 90m |
| 19 | `docker-compose.yml` for local Postgres (`postgres:16` + `.env.local`) | 20m |
| 20 | `.github/workflows/ci.yml` — `npm ci && npm run build && tsc --noEmit` | 25m |
| 21 | Rate limit + Turnstile-ready scaffold (env-gated, no-op until `TURNSTILE_SITE_KEY` set) | 40m |

### Tier 3 — operator-gated or large-effort

| # | Task | Gate |
|---|------|------|
| 22 | Resend env vars on Railway | operator |
| 23 | Railway GitHub App install on `Sinister-Systems-LLC` org | operator |
| 24 | Delete old Vercel project `prj_xOyAeuwJHZ89KUWcqHBhq9n0Wol5` | operator |
| 25 | AV1 + WebM video re-encoding pipeline | requires ffmpeg AV1 build; effort 2h |
| 26 | Adaptive bitrate ladder (640/960/1280w `<source media="...">`) | 1.5h |
| 27 | `<link rel="preload" as="video">` for first hero clip | 10m (ships with #25/#26) |
| 28 | Service worker for cached hero | 1h |
| 29 | CDN (`/media/*` via Cloudflare or Bunny.net) | operator picks provider |
| 30 | Lead status admin page (`/api/admin/leads` basic-auth) | 1h (operator sets admin password) |
| 31 | Daily digest cron + Resend dispatch | 45m (after #22) |
| 32 | Sentry client+server | 30m (operator creates Sentry project) |
| 33 | Plausible/Umami analytics self-host | 1h (operator runs Plausible container on Sanctum) |
| 34 | Backups: daily Postgres → Backblaze B2 | 1h (operator B2 bucket) |
| 35 | Brand-pack mockups (business card, vehicle decal, t-shirt SVGs) | 1.5h pure design |
| 36 | Cursor-follow brand glyph + cursor light on hero | 45m |
| 37 | Project case studies (2-3 × 200-400w narrative blocks per detail page) | content gate — operator provides text or LLM drafts |
| 38 | Press / awards / partners strip | content gate |
| 39 | Captions tracks on portfolio videos | content gate (need real transcripts) |
| 40 | GSC + Bing sitemap submission, GBP claim | operator |

---

## Part 3 — Execution order (this session)

LOOP MODE relentless: ship Tier 1 in order, commit + push to `jbw-deploy` after each deliverable, write a fresh resume-point per `Tier 1` slice that closes ≥ 1 row. End-of-session: write Tier-1-done resume-point + queue Tier 2 + 3.

**Branch:** `agent/jb-woodworks/complete-everything-20260528Z` (per `branch-convention-2026-05-25`).
**Push target:** `jbw-deploy` (per `single-repo-push-policy-2026-05-25`).

---

## Part 4 — Doctrine compose

- `no-bullshit-tested-before-claimed-2026-05-23` — every shipped row carries file:line + tsc/build evidence in the iter's commit body.
- `single-repo-push-policy-2026-05-25` — JBW carve-out → `jbw-deploy` only.
- `branch-convention-2026-05-25` — `agent/jb-woodworks/<short-topic>-<utc-date>`.
- `loop-relentless-pursuit-2026-05-25` — ship Tier 1 fully this session unless blocked on external signal.
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` — gold `#c9a84c` carve-out; do not invent new chrome recipes.
- `frequent-detailed-commits-per-agent-2026-05-25` — Shipped/Smoke/Refs commit body.
- `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` — Tier 1 has 10 mostly-independent slices; consider parallel `Agent()` fanout if cache pressure rises.

---

## Part 5 — What I am NOT touching this session (lane discipline)

- `~/.claude/.mcp.json` (operator-owned)
- Other `projects/<lane>/` source trees
- `main` branch (only via `sanctum-auto-push` daemon)
- Operator-gate rows (Tier 3 items #22, #23, #24, #29, #32-34, #40)
- Content-gate rows (Tier 3 items #37-39)
