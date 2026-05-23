<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Showmasters — Master Plan

Single source of truth for everything operator has asked for + expansion roadmap. Sorted by status + impact, not chronology.

---

## ✅ DONE (live on localhost)

### Site shell
- 14 HTML pages live: `index, what, how, where, shows, about, careers, contact, order, orlando, dallas, privacy, terms` + 14 returns from `localhost:8080`
- `manifest.json` PWA wired
- Favicon stack on every page: `favicon.svg`, `mask-icon`, `apple-touch-icon`, `theme-color`
- Full OpenGraph + Twitter Card + JSON-LD per page
- `sitemap.xml` with all 11 indexable routes
- `robots.txt` disallows internal lanes

### Hero + intro
- Single looping hero video (`hero-color-spots.mp4`) — no slideshow
- Stage-cue intro animation: black veil + gold scan-bar L→R + SMPL letters ignite + tagline + rule + curtain rises
- Intro fires on EVERY page load (no sessionStorage gate)
- Hero-reveal cascade (0/120/240/360ms)
- Trust pill removed per screenshot

### Page transitions
- Every internal link click plays a 460ms curtain + scan transition before navigating
- `?intro=skip` debug bypass
- Reduced-motion respected throughout

### Brand
- BRANDING/ pack: 25 SVGs across logos / marks / social / animated / print + README + TOKENS + USAGE + CHANGELOG + NANO-BANANA spec
- 6 IG pinned-banner SVGs (3-card spanning + 3 standalone alts)
- US coverage map (real PNG from showmasters.com) at `public/img/us-coverage-map.png`
- 3 IG emoji entities killed; star → `/5`; custom SVG checkmark

### Content (matching live showmasters.com)
- Exact P.D. testimonial quote on home
- Dual hero CTAs ("Get Started" + "Get an Estimate")
- "Welcome to Show Masters" + "First-class service · 1,700+ clients" on /about
- ACA compliance + worker-classification distinction on values
- Personnel Coordinator + Sales + Regional Manager added
- jib camera / graphics / teleprompter as technician specialties

### Pages with distinct visual treatments
- `/index` — single video hero + numbered editorial process list (01-04) + interactive map + locations + estimate form
- `/what` — 12 service-role cards w/ call-sheet numbering + 8 illustrated event scenes (corporate / concert / festival / trade show / theater / worship / sports / private)
- `/how` — 4-quadrant black/gold checker with editorial illustrations (blueprint, crew briefing, deckhand+truss, signed invoice+stamp)
- `/where` — header + interactive PNG map + 6 regional city cards
- `/shows` — portfolio with 16 anonymized show cards + 8-category filter chips
- `/careers` — full apply form with 21 expertise checkboxes (matches showmasters.com)
- `/order` — production call-sheet style with 4 blocked sections + crew-roster grid
- `/orlando`, `/dallas` — SEO-targeted city landing pages with venue lists
- `/contact` — estimate form

### Interactive map
- 12 clickable state hot-zones (CA, NV, CO, TX, LA, IL, OH, TN, NC, GA, FL, NY)
- Popups with real venue/year show data per state
- Embedded on both `/` and `/where`

### Let's Chat widget
- Globally injected via script.js — bottom-right gold pill
- Click → expanding panel with quick phone/email/order links + 3-field contact form
- On every page

### Marketing playbook
- 14 MARKETING/ docs: 00-START-HERE through 13-TIKTOK-PLAYBOOK
- Cover: marketing plan, SEO strategy, GMB ranking, booking funnel, competitors, content calendar, outreach list, local citations, reviews, pricing notes, social-media basics, IG playbook, TikTok playbook

### Infrastructure
- `HOSTING.md` — anti-Vercel self-host plan (Path A workstation tunnel / Path B Hetzner VPS + Caddy)
- `SECURITY.md` — pre-launch security checklist
- `STACK.md` — LetsText-aligned target stack documented
- `app-v2/` Next.js scaffold: package.json + next.config + tsconfig + tailwind + components.json + Prisma schema (4 models) + lib (db/validations/utils) + 2 API routes + layout + globals.css + home placeholder + contact page with rhf+zod form + README
- Local server live at `http://localhost:8080/` via Python http.server

### Hub language reconciliation
- All references swept Fort Worth → Dallas across HTML, JSON-LD, manifest, branding SVGs
- "Two offices · eight operational hubs · 33 states" framing live everywhere

---

## ⏳ IN FLIGHT — finishing this loop

### A. Index branch-out hub redesign (HIGH)
Operator quote: *"Have the main page be a branch outed system that connects to all pages we want users to look at. a complete concise simple approach that is efficent and concise. like a path. not a cluttered bullshit."*

**Approach:** replace the current services-preview / how-preview / where-preview stack with a single "Navigator" section. Vertical track (sticky on desktop), 7 numbered destination nodes (What, How, Where, Shows, About, Careers, Order), each as a wayfinding tile with a 1-line pitch + arrow link. Connecting gold "stage cable" lines between nodes give the path feel. Keeps the testimonial + map + estimate but kills the redundant preview-card stacks.

### B. MARKETING/ + app-v2/ Fort Worth → Dallas sweep
14 marketing docs + 3 app-v2 files still reference Fort Worth. Replace with Dallas + drop 76135 → 75201. Then re-grep clean.

### C. Use enhanced logos on the live site
The 12 BRANDING/logos/ variants + 5 marks aren't yet referenced from any HTML page. Pick winners (probably `02-spotlight-cone` for hero placement and `03-truss` for the order page header) and integrate, OR replace the canonical `public/img/logo-horizontal.svg` with the enhanced primary lockup.

---

## 🛣 ROADMAP — next 4 loop iterations

### Iteration 5 — Phase 2 Next.js port begins
- shadcn primitives in `app-v2/components/ui/`: button, input, label, textarea, card, dialog, separator, tabs, dropdown-menu, scroll-area
- Custom SVG icon components in `app-v2/components/icons/` (already started — finish the set)
- Navbar + Footer Next.js components (already in components/site/ — verify)

### Iteration 6 — Port pages to Next.js
- `app/about/page.tsx` + `app/what/page.tsx` + `app/how/page.tsx`
- `app/where/page.tsx` with react-simple-maps replacement for the PNG (vector + state click handlers)
- `app/shows/page.tsx` reading from Prisma `Show` table

### Iteration 7 — Wire admin + Postgres
- `app/admin/page.tsx` (auth-gated, list inquiries + applications)
- Basic email notification on new inquiry via SMTP_*
- Prisma migrations applied
- One-line installer script

### Iteration 8 — Polish + launch checklist
- Caddy reverse-proxy live (per HOSTING.md Path B)
- Cloudflare DNS swap (after operator buys domain)
- Run Lighthouse audit + fix anything <90
- Submit sitemap to Google + Bing
- Claim both GMB profiles (operator step, surface in checklist)

---

## 🌱 EXPANSION IDEAS (queued for operator approval)

Each one is real client value. Pick the ones that fit; skip the rest.

### Content depth (no engineering needed)
1. **Press / Case Studies page** — 3-5 named wins with permission, deep-dive each (crew size, scope, before/after, client outcome)
2. **Meet the Crew** — anonymized profile cards (Crew Lead X, 12 years, specialty: rigging concerts at Amway). Recruits identify with real people.
3. **FAQ accordion** — 20 questions producers actually ask, optimized for featured-snippet capture
4. **Glossary of stage terms** — SEO authority + onboarding for new producers
5. **Resource library** — downloadable run-sheet templates, briefing forms (gated by email for newsletter capture)
6. **Insurance & Compliance** page — COI process, certs (OSHA, ETCP, SPRAT), training records, audit findings
7. **Newsletter signup + monthly drip** (Buttondown, self-hostable)
8. **5 more city landing pages** — Tampa, Miami, Houston, Austin, Jacksonville (per SEO doc Phase 2)
9. **Per-role recruitment pages** — `/careers/stagehand`, `/careers/rigger`, etc. Tighter SEO + targeted apply CTAs
10. **Press mentions strip** — logos of publications + awards (when operator provides logos)

### Interactive features
11. **Live crew-availability ticker** — "12 stagehands available in Orlando this weekend" pulled from Postgres
12. **Estimate calculator widget** — interactive cost estimator: pick role counts + duration → see ballpark + send-as-inquiry
13. **Show calendar (public)** — anonymized booked-show calendar showing how busy SMPL is; produces FOMO
14. **Crew profile filter** — "find a Crew Lead by city + specialty"
15. **Testimonials carousel** — beyond the single P.D. quote, build a rotating wall
16. **3D / WebGL hero** — Three.js scene of stage lights + truss, no stock footage required (replaces or supplements MP4)

### Brand + visual
17. **Animated SVG section dividers** — between major sections, stage-light themed (spotlight scan, scrim sweep, etc.)
18. **Custom 404 page** — branded "SHOW CANCELLED" with link to home
19. **Custom dark/light toggle** — for print/PDF generation needs
20. **PWA install prompt** — "Add to home screen" for mobile users who book often
21. **Skeleton loaders** — while images load, show branded shimmer (slower connections)

### Backend + ops
22. **/admin inquiry queue** with status pipeline (NEW → CONTACTED → ESTIMATED → WON/LOST)
23. **Auto-route inquiries** to the right project lead by event type + city
24. **Slack/SMS notification** to operator when new inquiry lands (Twilio or self-hosted)
25. **Daily Postgres backup** to Backblaze B2 (cheap, no Vercel)
26. **Self-hosted analytics** — Umami (privacy-respecting, GDPR-safe)
27. **Cron job framework** — for weekly review report, monthly newsletter, daily backup
28. **Per-form rate limiting** at Caddy + Postgres rolling window
29. **Webhook receivers** — Cloudflare Turnstile + GMB reviews + Google Search Console import
30. **Cookie consent banner** for EU traffic at launch

### SEO + growth
31. **Per-show landing pages** for big named shows (with client permission) — pumps long-tail SEO
32. **Annual "State of Event Labor in Florida / Texas" report** (PDF download with email capture) — links well + builds authority
33. **Industry guest-post hub** — Live Design Online, BizBash, etc. — track + republish on /press
34. **Schema.org JobPosting** on /careers — Google for Jobs free traffic
35. **Schema.org FAQPage** on /how — featured-snippet capture
36. **Schema.org Event** when shows get publicly named

### Nano banana (when wired)
37. **Real photographs** per event-type card — generated via nano banana, locked to brand palette per `BRANDING/NANO-BANANA-INTEGRATION.md`
38. **Per-city hero images** — generated skyline / venue collages for orlando.html + dallas.html
39. **Blog hero images** — one per monthly blog post (12 per year)
40. **Social-post backgrounds** — Reels covers + IG carousel slides (matches `MARKETING/06-CONTENT-CALENDAR.md`)

---

## OPERATOR-GATED — surfacing what blocks me

These need an operator decision or action I cannot take on my own:

1. **Nano banana API access** — operator said "you should have it now" but no env signal + `_vault/` correctly denied. Need: API key env var name, base URL, model name, auth header format. Spec at `BRANDING/NANO-BANANA-INTEGRATION.md`.
2. **IG canonical handle** — `@showmastersproduction` (per IG screenshot) vs `@showmastersproductionlogistics` (my docs).
3. **Dallas address** — IG shows `4501 Vineland Rd 110A, Orlando 32811`; site shows `4906 Patch Road 32822`. Dallas street + zip needs operator confirmation (currently using `Dallas, TX 75201` as placeholder).
4. **Domain + DNS** — `showmasters.com` (Cloudflare DNS swap).
5. **VPS provision** — Hetzner / DO droplet for Caddy + Next.js + Postgres (per HOSTING.md Path B).
6. **Counsel-reviewed** legal text for privacy + terms (currently noindex stubs).
7. **Real photographs** — high-resolution show photos with crew permission (until nano banana, hand-illustrated SVG scenes carry the load).
8. **Git init + push** to `Sinister-Systems-LLC/Showmasters`.
9. **Approval of `[explore]` BRANDING variants** before public use (spotlight cone, truss, emblem seal, hex, shield, tour case).
10. **GMB profile claims** — both Orlando + Dallas (per `MARKETING/03-GMB-RANKING.md`).

---

## ORDER OF EXECUTION

The loop iteration plan:
- **Now (this iter):** A (branch-out hub) + B (FW→Dallas sweep) + C (enhanced logos)
- **+20 min:** Phase 2 Next.js shadcn primitives (#35)
- **+40 min:** Phase 2 page ports begin (#38)
- **+60 min:** Add FAQ + glossary + custom 404 from expansion list
- **+80 min:** Testimonials carousel + Meet the Crew page scaffolds
- **+100 min:** Per-role recruitment landing pages
- **+120 min:** Schema.org additions (FAQPage, JobPosting, Event)
- **Beyond:** Move into expansion ideas list, top-down by ROI
