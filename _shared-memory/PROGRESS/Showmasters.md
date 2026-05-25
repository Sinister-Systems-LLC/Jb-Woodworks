<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Agent: Showmasters

Append-only progress log. Most recent at top.

---

## 2026-05-25 00:40 — RESUME iter 1 · production re-verify · 6/6 PASS · no operator-new-work in showmasters lane

Resumed from `2026-05-24T144519Z.json` (last delivery: SESSION-SAVE-POINT at 10:15 UTC 2026-05-24).

**Production smoke (live URL `https://showmasters-web-production.up.railway.app`):**
- `/` → 200 (TTFB 205ms) ✅
- `/about.html` → 200 ✅
- `/contact.html` → 200 ✅
- `/where.html` → 200 ✅
- `/shows.html` → 200 ✅
- `/case-studies.html` → 200 ✅
- `/this-page-should-404.html` → 404 ✅ (custom 404 still routing correctly)

**Inbox triage (3 unread, all FYI/broadcast):**
1. `2026-05-24T1350Z-from-sanctum-feature-refresh.json` — 15 fleet-wide capability refresh, ack-only.
2. `2026-05-24T1555Z-from-test-modes-verify-broadcast-dashboard-skeleton-ui-base.json` — operator hard-canonical UI BASE = `dashboard-skeleton`. **Not actionable for showmasters** — this lane is a static marketing site (HTML/CSS/JS, no React/dashboard primitives). Skeleton inheritance applies to dashboard-class surfaces (panel, kiosk, admin wrappers); the marketing site retains its own brand-locked stylesheet.
3. `2026-05-24T1623Z-from-snap-api-quantum-iter103-marketing-redundancy.json` — recommended templating `deliverable/03-Marketing.md` from `site/MARKETING/*` canonical pages. Sender explicitly notes *"Lane-action only if maintaining drift is painful — current architecture is reasonable, just redundant."* Logged as backlog row D below; not firing this turn.

**Operator utterance triage (5 unread):**
- All 5 are sanctum-lane (EVE.exe redesign / infinite accounts / OAuth pivot / jcode animations / token menu) — surfaced here for visibility per canonical-10, but **not in showmasters scope**. Sanctum-lane agents handle them.

**Branch note (CAUTION):** Working tree `D:/Sinister Sanctum/projects/showmasters/site` is currently on branch `agent/sinister-os-mobile/p0-spec-2026-05-24` (sister lane). No code edits this turn — only sanctum-harness file writes (this PROGRESS line + heartbeat + resume-point), which are append-only and lane-neutral.

**Iter 2 — local-files sanity audit (free + fast):**
- 24 top-level HTML files audited (`*.html` at site root):
  - 24/24 have `<main>` landmark ✅
  - 24/24 have `class="skip-link"` ✅
  - 23/24 have `application/ld+json` schema (404.html omitted by convention) ✅
  - 0 `console.log(` leaks ✅
  - 0 `unsplash.com` refs ✅
  - 0 unsafe `target="_blank"` (zero matches even before `rel=noopener` lookahead) ✅
- No regressions since 2026-05-24 10:15 SESSION-SAVE-POINT.

**Open backlog (queued for next iter or operator direction):**
- A. PROGRESS consolidation per queue row 947 — **already trimmed** (file = 332 lines, queue note said 904). Marginal: only 1 entry at 2026-05-23 15:15 falls below the 15:50Z cutoff. Skipping.
- B. `PLAN.md` A.iv — verify intro animation on localhost:8080 (first-load full intro vs nav-click 200ms curtain). Needs visual confirmation (curl can't see animations) — operator-required.
- C. `PLAN.md` B/C — nano-banana batch (6 service heros + 2 city heros + 5 social templates + 11 blog headers, ~$0.94 cost). Operator-gated; not firing without explicit go.
- D. quantum-sweep drift fix — template `deliverable/03-Marketing.md` from `site/MARKETING/*` (cosmetic, low-urgency).

**Loop stop:** queue-empty-or-blocker reached (no `SINISTER_LOOP_CONDITION` set; falling back to default). Remaining items all require operator-input or operator-gate. Stopping cleanly.

---

## 2026-05-24 10:15 — SESSION-SAVE-POINT (Claude limit approaching) · everything captured

Operator: *"we are about to be at claude limit. save all progress and plans and everything i said so nothing is lost. make the..."* (msg cut off).

### Production state (CURRENT, LIVE, VERIFIED)

- **Public URL:** https://showmasters-web-production.up.railway.app
- **GitHub:** https://github.com/Sinister-Systems-LLC/showmasters-site
- **Railway dashboard:** https://railway.com/project/c7e6ce82-83bd-4d29-8fd7-4924f8278fbe
- **Local dev:** http://127.0.0.1:8000/ (Python http.server still running)
- **35/35 HTML pages serve 200** · `/does-not-exist` returns 404
- **Map labels live:** CA · CO · FL · GA · LA · NV · TN · TX (short-form matching reference image #7)
- **51 state paths + 8 hub markers + 53 city dots + 1 legend** on /where.html
- **34/35 valid JSON-LD schemas** (only 404 omitted by convention)
- **35/35 with `<main>` landmark + skip-to-content link**
- **6/6 security headers** (HSTS 2yr preload · CSP · X-Frame · X-Content · Referrer · Permissions)
- **22 KB brotli homepage · TTFB 140 ms · total 200 ms**
- **0 broken hrefs · 0 broken assets · 0 unlabeled inputs · 0 unsafe `target=_blank` · 0 Unsplash refs · 0 duplicate `<main>` or `<footer>` · 0 console.log leaks**

### Desktop deliverables (CURRENT)

- **`C:\Users\Zonia\Desktop\Showmasters-Deliverables\`** — 103 files · 3.1 MB
- **`C:\Users\Zonia\Desktop\Showmasters-Deliverables.zip`** — 2.4 MB · 104 entries · drag-and-drop email attach
- Folder structure:
  - `README.txt` · `EMAIL-DRAFT.txt` · `FACT-SHEET.txt` · `BOILERPLATE.txt`
  - `audits/` (4): SOCIAL-MEDIA-AUDIT · SITE-AUDIT-GUIDE · DEPLOY-CHEATSHEET · CONTENT-AUDIT
  - `marketing-playbook/` (14): 00-START → 13-TIKTOK full playbook
  - `branding-guide/` (5): README · USAGE · TOKENS · NANO-BANANA-INTEGRATION · CHANGELOG
  - `project-docs/` (4): PLAN · STACK · SECURITY · HOSTING (CLAUDE.md excluded)
  - `logos/` (8 SVGs) · `maps/` (3 SVGs) · `og-cards/` (1 SVG)
  - `qr-codes/` (5 files): production-url + showmasters-com, SVG + PNG
  - `photos/` (55 WebPs across 8 category subfolders: events, services, shows, cities, blog, process, pillars, careers)

### Every operator ask this session — DONE

| # | Ask | Status |
|---|---|---|
| 1 | Fire nano-banana batch (6 role-cards, expanded to 8 events + 8 shows + city + blog) | ✅ shipped — $1.56 total spend |
| 2 | WebP conversion (97% size reduction) | ✅ shipped — 65.79 MB saved |
| 3 | Put live on localhost | ✅ http://127.0.0.1:8000/ running |
| 4 | Open in browser | ✅ done |
| 5 | Fix the map (10+ iterations) | ✅ amCharts Albers USA, all 50 states |
| 6 | Map labels match image #7 reference | ✅ short labels (TX, FL) live |
| 7 | "Now make it have all this info" (image #4) | ✅ title + legend + city dots + hub stars |
| 8 | Bigger map size | ✅ proper Albers aspect 1.62:1 |
| 9 | Put live on Railway | ✅ https://showmasters-web-production.up.railway.app |
| 10 | Desktop deliverables for email | ✅ 103 files folder + 2.4 MB zip on Desktop |
| 11 | Add md files + social audits + deep audit guide (no black-hat) | ✅ 4 audit guides + 14 playbook + 5 branding + 4 project-docs |
| 12 | Place all on Desktop | ✅ 103 files + zip |
| 13 | Keep working / find issues | ✅ 4 CTA conversion fixes (hero buttons, city pages, branch-pills, shows→case-studies) |
| 14 | Smoke test + fix everything (image #7 + image #8 reference) | ✅ comprehensive 15-section audit · all green · short-form labels live |

### All GitHub commits this session (chronological)

```
4eacf2f  CTA: 'Take this path' as gold-pill buttons
f0ec966  shows.html → case-studies.html CTA bridge
114a987  homepage hero CTAs above the fold
9e6077d  4 city pages: header CTAs (orlando/dallas/houston/tampa)
d676dc2  serve.json: / → /index.html rewrite (404 routing fix)
1525d1d  sitemap.xml: <lastmod> on all 34 entries
d5ab413  package.json: drop serve -s (SPA fallback) to get proper 404s
6089fa9  skip-to-content link on every page + .skip-link CSS
22d3c5f  <main> landmark on 35 pages
fd95e59  order.html: aria-label on 30 unlabeled crew-request inputs
e6a4417  serve.json: 7 security headers (HSTS · CSP · X-Frame · X-Content · Referrer · Permissions)
b4621cb  humans.txt + .well-known/security.txt (RFC 9116)
efed444  4 legal-page JSON-LD schemas (accessibility · cookies · privacy · terms)
61fc751  README.md for GitHub repo
80d9204  Initial Show Masters marketing site deploy
f81ef72  Map labels: TX + FL short-form matching reference
```

### Open / operator-gated (parked for recipient's response to the email)

- DNS for **showmasters.com** → Railway (run `railway domain showmasters.com` then point CNAME)
- Counsel-reviewed privacy / terms / accessibility / cookies copy (currently scaffold)
- Instagram handle: `@showmastersproduction` vs `@showmastersproductionlogistics`
- Orlando office address: `4501 Vineland Rd` vs `4906 Patch Rd`
- Visual review of 55 brand-locked generated photos
- GitHub Actions auto-deploy (blocked: gh-cli token lacks `workflow` scope; YAML draft at `/tmp/railway-deploy.yml-snippet`)

### How to resume this session

Resume from the most recent resume-point in `_shared-memory/resume-points/Showmasters/`. To continue any polish iteration:

```powershell
# Edit files in:
D:\Sinister Sanctum\projects\showmasters\site\

# Then deploy via the one-command script:
pwsh "D:\Sinister Sanctum\projects\showmasters\site\.tmp\deploy.ps1" -Message "what changed"
```

The script syncs canonical → staging at `D:\tmp\showmasters-deploy\`, commits, pushes to GitHub, and triggers Railway redeploy.

### Tooling at `D:\Sinister Sanctum\projects\showmasters\site\.tmp\`

- `deploy.ps1` — one-command sync+commit+push+redeploy
- `site_audit.py` — broken hrefs/assets/missing-head/external-imgs/orphans audit
- `validate_jsonld.py` — every JSON-LD block parses with @context + @type
- `audit_picture_wrap.py` — every generated PNG `<img>` has a `<picture>` WebP source
- `schema_inventory.py` — which pages have schemas, which don't
- `webp_convert.py` — Pillow-based PNG → WebP at q=82
- `swap_to_picture.py` — wrap `<img>` in `<picture>` with WebP source (idempotent via picture-block stash)
- `fix_double_li.py` · `fix_double_wrap.py` · `strip_legacy_svgs.py` — historical regression-repair scripts
- `rebuild_map_v2.py` — generate the amCharts Albers map embed
- `gen_event_cards.py` · `gen_show_heros.py` — nano-banana batch image generators
- `add_main_landmark.py` · `add_main_legal.py` · `add_skip_link.py` · `add_aria_labels_order_form.py` · `add_city_header_cta.py` · `add_sitemap_lastmod.py` — surgical site-wide editors
- `swap_shows_imgs.py` — show-card Unsplash → brand-lock replacer
- `rescale_map_styles.py` · `flip_map_y.py` — historical map-fix scripts

---

## 2026-05-24 10:00 — Conversion-CTA sweep · gold pill buttons everywhere they matter

Operator: *"keep working on it all and find issues"*.

**Built this iteration (4 CTA-related issues found + fixed):**

| # | Issue | Fix | Commit |
|---|---|---|---|
| 1 | `branch-go` "Take this path" on index.html was gold-text-with-underline — read as passive link | Solid gold-gradient pill, dark text, padding 10×18, rounded 6px, drop-shadow, hover lift + arrow slide, focus-visible outline | `4eacf2f` |
| 2 | shows.html had 16 portfolio cards (display-only) + 1 "Plan Your Next Show" CTA, but NO link to `case-studies.html` where the 3 in-depth writeups live | Added "See In-Depth Case Studies" ghost button next to the primary CTA | `f0ec966` |
| 3 | Homepage hero had headline + subhead + scroll indicator but ZERO primary CTAs above the fold | Added `hero-cta-row` with "Get an Estimate" + "Place a Crew Order" below subhead, animates in with hero-reveal at 360ms, responsive (stacks at ≤540px) | `114a987` |
| 4 | 4 city pages (orlando/dallas/houston/tampa) — high-intent geo-targeted visitors — had no CTA in their page-header | Added the same hero-cta-row pattern to all 4 city headers via `.tmp/add_city_header_cta.py` | `9e6077d` |

---

## 2026-05-24 09:45 — "Take this path" CTAs upgraded to obvious gold-pill buttons
(See above for details — commit `4eacf2f`.)

---

## 2026-05-24 09:36 — Pre-send sanity pass · all green · zip refreshed · operator ready to send email

Plan executed (8 pre-send sanity checks):
1. Zip integrity (file count + structure) — 104 entries · 2.4 MB ✓
2. URLs in deliverables resolve — production · GitHub · Railway all 200 ✓
3. EMAIL-DRAFT.txt sanity — live URL · zip filename · `[name]` slot ✓
4. Phone/email consistency across 4 root docs ✓
5. Sample-read 1 audit + 1 playbook doc ✓
6. QR codes valid (SVG `<?xml` · PNG magic bytes) ✓
7. Live smoke (35/35 · 404 · short labels · 6/6 security) ✓
8. Zip refreshed ✓

---

## 2026-05-24 09:25 — Full photo set + QR codes + zip on Desktop · 103 files / 3.1 MB / 2.4 MB zipped

| Surface | Detail |
|---|---|
| Full photo set | 55 brand-locked WebPs across 8 category subfolders (events 8 · services 12 · shows 8 · cities 4 · blog 14 · process 4 · pillars 4 · careers 1) |
| QR codes | 4 files (SVG + PNG for production URL and future canonical) + README with usage notes |
| Zip on Desktop | `Showmasters-Deliverables.zip` 2.4 MB via `Compress-Archive` |
| Updated README + EMAIL-DRAFT | Reflects 103 files, 2.4 MB zip, new folder structure |

---

## 2026-05-24 09:10 — Deliverables expanded · 4 audit guides + 23 strategy docs · 51 files / 889 KB on Desktop

Operator: *"add to the deliverables all the md files i told you to make and social media audits of their account all that shi. dont reveal our black hat methods. just a general deep audit guide on things they can easily do without being super techy like me"*.

| Surface | Detail |
|---|---|
| Project docs | Copied PLAN/STACK/SECURITY/HOSTING from canonical (CLAUDE.md excluded — internal) |
| Marketing playbook | All 14 `MARKETING/*.md` docs (00-START → 13-TIKTOK) |
| Branding guide | All 5 `BRANDING/*.md` docs |
| `audits/SOCIAL-MEDIA-AUDIT.md` | Monthly IG/FB/LinkedIn checklist · profile · cadence · captions · reviews · explicit "what this audit does NOT recommend" (buy followers, fake reviews, engagement pods, scraping) |
| `audits/SITE-AUDIT-GUIDE.md` | 8 free-tools monthly walkthrough · PageSpeed · Mobile-Friendly · Schema · Search Console · GMB · WAVE · SecurityHeaders · Wayback |
| `audits/DEPLOY-CHEATSHEET.md` | One-command + manual deploy paths · rollback · add new page · DNS migration |
| `audits/CONTENT-AUDIT.md` | Quarterly stale-content check · number consistency · photo freshness · blog cadence · legal-page dates |

---

## 2026-05-24 04:00 — Map labels match reference · Desktop deliverables packaged · 404.html double-main repaired

| Surface | Detail |
|---|---|
| Map labels | `ORLANDO HUB` → `FL` · `TEXAS HQ` → `TX` · uniform 14-unit-radius solid-dark stars, no glow |
| 404.html double-main fix | Two `<main>` tags merged into one `<main id="main" class="four-oh-four">` |
| Desktop deliverables | First version: 24 files · 629 KB at `C:\Users\Zonia\Desktop\Showmasters-Deliverables\` |

---

## 2026-05-24 03:30 — Final polish · skip-link · 404 routing fix · sitemap lastmod · production audit GREEN

| Surface | Detail |
|---|---|
| `<main>` landmark | All 35 pages (depth-counted div scan + legal-page variant inserter) |
| Skip-to-content link | All 35 pages — `<a class="skip-link" href="#main">` as first focusable element, hidden until keyboard focus |
| 404 routing fix | Was: `serve -s` made 404s return 200+homepage. Now: explicit `directoryListing: false` + rewrite `/` → `/index.html` in serve.json |
| Sitemap lastmod | All 34 entries have `<lastmod>2026-05-24</lastmod>` |
| Deploy automation | `.tmp/deploy.ps1` — one-command sync+commit+push+redeploy |

---

## 2026-05-24 02:30 — A11y landmarks iteration · `<main>` + skip-to-content on 35/35 pages
(Combined with 03:30 entry.)

---

## 2026-05-23 22:10 — A11y + security iteration · 0 unlabeled inputs · 7 security headers · humans.txt + security.txt · CSP wired

| Surface | Detail |
|---|---|
| order.html a11y | 30 unlabeled crew-request inputs got `aria-label="<Role> count|hours|notes"` via `.tmp/add_aria_labels_order_form.py` |
| humans.txt | Standard credits file at `/humans.txt` |
| /.well-known/security.txt | RFC 9116 security contact |
| Security headers | 7 headers across all paths: X-Content-Type-Options nosniff · X-Frame-Options SAMEORIGIN · Referrer-Policy strict-origin-when-cross-origin · HSTS 2yr preload · Permissions-Policy locked · CSP on HTML pages · video cache 30d immutable |

---

## 2026-05-23 20:00 — Polish iteration · 4 legal-page schemas added · redeploy · README pushed to GitHub · full live audit green

| Surface | Detail |
|---|---|
| Legal-page schemas | accessibility/cookies/privacy/terms got `WebPage` JSON-LD blocks. Coverage 30/35 → 34/35 |
| README.md to GitHub | 75-line production-grade README for the GitHub mirror |
| Railway redeploy | Build completed, container `npm start` succeeded, first live GET / returned 200 in 91ms |

---

## 2026-05-23 19:30 — SHIPPED LIVE on Railway · public URL https://showmasters-web-production.up.railway.app · GitHub repo created

| Surface | Detail |
|---|---|
| Railway project | `showmasters` (`c7e6ce82-83bd-4d29-8fd7-4924f8278fbe`) in `z0nian's Projects` workspace · service `showmasters-web` (`66bee2c8-fd26-45da-a36c-beb6acb25cf7`) |
| Deployment config | `package.json` (serve@^14.2.4) · `railway.json` (NIXPACKS) · `serve.json` (cache headers) · `.dockerignore` |
| Upload bundling | Clean copy at `D:/tmp/showmasters-deploy/` — 43 MB bundle (PNG fallbacks + dev artifacts excluded). 3rd `railway up` succeeded. |
| GitHub repo | `Sinister-Systems-LLC/showmasters-site` public · first commit ships production-ready static site |
| Public domain | `railway domain` auto-assigned `https://showmasters-web-production.up.railway.app` |

Live URL smoke test (24/24 paths returned 200 · 5/5 image assets 200 · `/where.html` has 51 state-paths + 8 hub-markers · 266 ms cold response).

---

## 2026-05-23 18:30 — Map rebuilt with proper Albers projection (amCharts) · interactive-map.js polygon-star support · final close-out

| Surface | Detail |
|---|---|
| Albers US-states map | Replaced custom inline state paths with amCharts US topology (51 paths: 50 states + DC, 1.62:1 aspect). Source at `https://www.amcharts.com/lib/3/maps/svg/usaLow.svg` (32 KB), cached at `.tmp/amcharts.svg`. New viewBox `-40 -25 1140 705` |
| 53 city dots | Major US metros with `<title>` tooltips |
| 8 hub stars + labels | Polygon-based 5-point stars at hub centroids |
| Legend | Bottom-left absolute overlay with 3 rows |
| interactive-map.js polygon support | `tileCenterPct()` now handles `<polygon class="hub-star">` (averages 10 vertices for centroid) |

---

## 2026-05-23 17:15 — Visual-bug sweep · map viewBox tightened · "Eight hubs" → "Six hubs" everywhere · Fort Worth address fixed in dallas.html schema · process step images eager-load

| Surface | Detail |
|---|---|
| where.html + index.html SVG viewBox | `0 0 1100 700` → `505 35 200 130` (states were clustered 150×95 in a huge canvas; fixed) |
| index.html Florida | Moved from `state-hub` → `state-hq` (matched where.html fix) |
| "Eight hubs" stale text | 4 places: index×2 + about + press. Changed to "Six hubs" matching SVG paint |
| dallas.html schema/body mismatch | Was Dallas/75201 schema vs Fort Worth/76135 body. Fixed schema + deduplicated "Dallas, Dallas" typo |
| how.html process step images | `loading="lazy"` → `loading="eager"` so above-fold cards always render |

---

## 2026-05-23 16:30 — 8 distinct show heros · WebP conversion (-65.8 MB / -97%) · CSS image-set() for city pages · persistent localhost:8000 · full audit green

| Surface | Detail |
|---|---|
| 8 distinct show heros | nano-banana SMPL-brand for healthcare-annual · enterprise-software-keynote · automotive-reveal · country-stadium-tour · touring-comedy-theater · florida-waterfront-fest · manufacturing-expo · consumer-electronics-popup. Spend $0.31. 245s |
| WebP conversion (all generated dirs) | 71.3 MB PNGs → 2.3 MB WebPs (-65.79 MB / -97% reduction). Pillow at q=82 method 6 |
| 63 `<img>` wrapped in `<picture>` | Across 7 files. Idempotency fix after first non-idempotent run double-wrapped 101 imgs |
| 4 city CSS image-set() | CSS background-image gets WebP-first with PNG fallback |
| Persistent localhost | `python -m http.server 8000` running |

---

## 2026-05-23 15:50 — 8 brand-locked event heros generated · ZERO Unsplash anywhere · 14 new JSON-LD schemas · sitemap +6 pages · robots fixed · full audit green

| Surface | Detail |
|---|---|
| 8 event-card heros | corporate · concert · festival · trade-show · theater · worship · sports · private. $0.31 spend. 303s |
| 8 Unsplash refs swapped in what.html | All to local brand-locked PNGs |
| 16 Unsplash refs swapped in shows.html | Mapped to event-type WebPs by category (zero added gen cost) |
| 14 new JSON-LD schemas | about · contact · shows · what · where · how · order · houston · tampa · crew · press · case-studies · glossary · insurance. Coverage 16/35 → 30/35 |
| Sitemap +6 entries | crew · press · privacy · terms · cookies · accessibility |
| robots.txt fix | Removed contradictory `Disallow: /privacy.html` etc. (sitemap already lists them) |

---

## 2026-05-23 15:15 — Resume cleanup pass · where.html hub-count drift fixed · 8 legacy SVGs stripped from what.html · dead .smpl-map-marker CSS removed · full-site smoke green

| Surface | Detail |
|---|---|
| where.html Florida class fix | `state-hub` → `state-hq` matching Texas (FL is the FL office, not just a hub state) |
| where.html copy | "Eight states are operational hubs" → "Six states are operational hubs" matching SVG paint |
| what.html legacy SVG strip | Removed 8 `<svg style="display:none">` blocks (-406 lines, -26 KB) |
| style.css dead-code | Removed `.smpl-map-marker` + `.marker-dot` + keyframes (~70 lines) |
