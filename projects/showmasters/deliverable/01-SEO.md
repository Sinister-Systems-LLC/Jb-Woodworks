# SEO Playbook — Show Masters Production Logistics

**Site:** https://www.showmasters.com
**Compiled:** 2026-05-23

---

## Quick wins (do this month)

These take less than an hour each, in priority order:

1. **Claim and verify Google Business Profile** for both Orlando HQ (4906 Patch Road, Orlando, FL 32822) and Dallas Hub (6340 Lake Worth Boulevard, Dallas, TX 75201). This single step does more for local search than the next ten tasks combined.
2. **Submit the sitemap** at https://www.showmasters.com/sitemap.xml to Google Search Console and Bing Webmaster Tools. The site already has the sitemap built; it just needs to be registered.
3. **Add the LocalBusiness schema** that already exists in `index.html` to all city pages (orlando.html, dallas.html, houston.html, tampa.html) with city-specific JSON-LD blocks. Most are already done; verify with the Rich Results Test tool.
4. **Get 5 reviews** on Google Business Profile from past clients. Direct ask via email; offer a follow-up call as gratitude. Reviews are the single biggest local-SEO ranking factor for service businesses.
5. **Build out citations** on the 30 most relevant industry directories (full list in `03-Marketing.md` → `08-LOCAL-CITATIONS`).

## The keyword strategy

SMPL's search strategy is built around three keyword categories:

### Category 1: Local + service (highest commercial intent)

These are the keywords producers actually type when they need crew **now**. They should be the canonical-link target on the city pages.

| Keyword | Monthly searches (est.) | Difficulty | Current ranking |
|---|---|---|---|
| stagehand staffing orlando | 110 | Medium | Top 10 (verify) |
| stagehands dallas tx | 90 | Medium | Top 10 (verify) |
| event crew orlando | 880 | Medium-High | Aim for top 5 |
| event crew dallas | 720 | Medium-High | Aim for top 5 |
| stagehand companies near me | 1,300 | High (local) | Local pack target |
| rigging crew orlando | 70 | Low | Easy win, currently mid-page |
| trade show labor orlando | 480 | Medium | Aim for top 3 |
| trade show labor dallas | 320 | Medium | Aim for top 5 |

### Category 2: Educational long-tail (authority building, slow burn)

These are the keywords producers type when they're researching, not buying. The blog posts in `blog-posts/` target these.

- "how much does stagehand labor cost"
- "stagehand vs technician difference"
- "what does a rigger do at concert"
- "12 hour load in process"
- "workers comp insurance live events"
- "1099 vs w2 stagehands"

These each have low monthly volume (40–500/mo) but compound over time as authority articles. Once a producer reads your stagehand-cost article and you're #1 on Google for the term, they remember you when they have a show to book.

### Category 3: Branded + competitor

Make sure these always return SMPL first:

- "show masters production logistics"
- "show masters orlando"
- "show masters dallas"
- "smpl crew"
- "show masters reviews"

Set up Google Search Console alerts for any branded-keyword position drop.

## On-page SEO best practices

Every page on the site should have:

1. **A unique `<title>` tag** — 50-60 chars, keyword + brand + location
2. **A unique `<meta name="description">`** — 140-160 chars, value proposition + CTA verb
3. **A canonical URL** (`<link rel="canonical">`) — prevents duplicate-content issues
4. **Open Graph + Twitter Card meta** — for social sharing previews
5. **One H1 only**, descriptive, with primary keyword
6. **H2/H3 hierarchy** that mirrors search intent
7. **Internal links** to 3+ related pages
8. **Image alt text** — every image, descriptive, includes keyword where natural
9. **JSON-LD schema** — Organization, LocalBusiness, Service, Article (blog posts), FAQ (where applicable)

Spot-check: the current site does about 80% of this correctly. The 20% gaps are:
- Some pages have generic alt text ("Show Masters" instead of "stagehand crew at Orange County Convention Center")
- Article schema is partial on some blog posts
- The FAQ page used FAQPage schema correctly — but the page has been removed; if you bring it back, restore that schema

## Local SEO priorities

For a service business with two physical offices, local SEO **is** SEO. The three things that move the needle:

### 1. Google Business Profile (formerly Google My Business)

For each office:
- Verified address, phone, hours
- Service area definition (FL + nearby states for Orlando; TX + nearby states for Dallas)
- 8+ photos (exterior, interior, crew at work, gear, team)
- Weekly posts (events, behind-the-scenes, client wins)
- Q&A section with seed questions (we provide GL insurance, COI on request, etc.)
- Review responses (every review, within 48 hours)

### 2. NAP consistency

Name, Address, Phone must be **identical** across:
- Google Business Profile
- Website footer + contact page
- Yelp, Bing Places, Apple Maps
- Industry directories (EventCrowd, ProductionHub, Stagehand.com, etc.)
- Social media profiles

Inconsistent NAP is the #1 reason local rankings suffer. Set this up once correctly and audit quarterly.

### 3. Local content

City pages already exist for Orlando, Dallas, Houston, Tampa. Each should have:
- A clear local-keyword target in title + H1
- Venue list with internal links to relevant case studies
- Service-area definition (neighborhoods/counties)
- Phone + email + map embed (or address card)
- A local-flavored testimonial if available

Consider adding pages for: Miami, Tampa Bay regional, Fort Worth, Austin, San Antonio, Houston suburbs.

## Technical SEO checklist

- [ ] **Sitemap.xml** — exists at /sitemap.xml. Submit to GSC + Bing.
- [ ] **Robots.txt** — exists. Disallows /BRANDING, /MARKETING, /app-v2.
- [ ] **Mobile-friendly** — verify on PageSpeed Insights. Currently looks good but verify all pages.
- [ ] **Core Web Vitals** — LCP under 2.5s, CLS under 0.1, INP under 200ms. Hero video may be the bottleneck; lazy-load + poster image.
- [ ] **HTTPS** — required once on live domain.
- [ ] **404 page** — exists, on-brand.
- [ ] **Canonical tags** — every page has one. Verify no accidental cross-canonicals.
- [ ] **Image optimization** — convert PNG → WebP for photos. Lazy-load via `loading="lazy"` (mostly done).
- [ ] **Structured data** — Organization, LocalBusiness, Service, Article schemas. Validate with Rich Results Test.
- [ ] **Hreflang** — not needed (English-only US site).

## Link-building strategy

Backlinks remain the strongest off-page ranking factor. Three tracks:

### Track 1: Industry directories (one-time, do once)

Submit to:
- ProductionHub
- EventCrowd
- Stagehand.com
- Industry-specific local directories (Orlando event guides, Dallas event guides, etc.)
- IATSE-adjacent directories where appropriate (non-union but related)
- Trade publication digital directories (Pollstar, Event Marketer, BizBash)

Expected outcome: 30-50 high-quality links over 60 days.

### Track 2: Earned media (ongoing)

- Pitch industry publications (Pollstar, BizBash, Event Marketer, Special Events Magazine, Live Design Online) with story ideas:
  - Annual "How much does live event labor cost" report (use the blog post as a pitch)
  - Behind-the-scenes case studies from major shows (with client permission)
  - Op-eds from leadership on industry trends (W-4 vs 1099, ETCP certification, etc.)
- Local business journals (Orlando Business Journal, Dallas Business Journal) for company milestones, expansion, hiring announcements
- Industry podcasts (StageDirections, LiveDesign podcasts) — pitch leadership for guest spots

Expected outcome: 6-12 earned-media links per year, each at high domain authority.

### Track 3: Resource-page link-building

- Universities with theater/event-tech programs (UCF, UT-Austin, NCSU, Full Sail) — offer to be a recruiting resource on their career pages
- Industry-association resource lists (USITT, IATSE local chapters where non-jurisdictional, ESTA)
- Local convention/visitors bureaus (Orlando CVB, VisitDallas) — get listed as a vendor partner

Expected outcome: 12-24 high-trust links per year.

## Tooling stack

The minimum SEO stack to actually execute the above:

- **Google Search Console** (free) — indexing, click data, technical issues
- **Google Business Profile** (free) — local SEO foundation
- **Google Analytics 4** (free) — traffic + conversion tracking
- **Ahrefs or SEMrush** (paid, $99-$129/mo) — keyword tracking, backlink monitoring, competitor analysis
- **Screaming Frog** (free up to 500 URLs, paid for more) — technical SEO audits
- **PageSpeed Insights** (free) — Core Web Vitals
- **Rich Results Test** (free) — structured-data validation

Total minimum spend: $99-$129/mo for one paid tool. Without that tool you're flying blind on keyword tracking but can still execute everything else.

## Reporting cadence

A monthly one-page SEO report should answer four questions:

1. How many organic visitors did we get this month vs last month?
2. Which 10 keywords drove the most traffic? Which 10 are climbing?
3. Did we add any backlinks this month? From whom?
4. What's the next action item (one specific thing)?

If you can't answer those four in five minutes from a monthly report, the report is too long.

## What NOT to do

- **Don't buy backlinks.** Cheap PBN links will tank rankings within 6-12 months.
- **Don't run an SEO contractor on commission.** SEO is incremental; commission incentivizes black-hat tactics.
- **Don't keyword-stuff.** Modern Google is fluent; stuffing reads as low-quality and ranks worse than natural writing.
- **Don't redesign the site without an SEO migration plan.** The current URL structure is fine; preserve it.
- **Don't pay for inclusion in "best of" listicles.** Earned coverage > paid coverage for SEO purposes (and usually trust purposes too).
