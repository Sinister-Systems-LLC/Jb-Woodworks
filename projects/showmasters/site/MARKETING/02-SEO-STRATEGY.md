<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# 02 ,  SEO Strategy (Plain English)

We want producers and venues to **find us first** when they Google for event crew. There are three things that matter:

1. **On-page SEO** ,  the words and structure on each page.
2. **Local SEO** ,  appearing in the Google Maps "local pack" for Orlando + Dallas.
3. **Technical SEO** ,  making the site fast and easy for Google to read.

Everything below is already partially built into this site. This doc explains what was done and what to add next.

---

## 1. Keywords we're targeting

These are the actual phrases people type when they're ready to book labor. Each city should rank for the same template; we just swap the city name.

### "Money keyword" pillars (every page should hint at these)

| Keyword | Buyer intent | Approx. monthly volume (US) |
|---|---|---|
| stagehand staffing | High ,  ready to book | 800-1.5k |
| event production labor | High | 500-800 |
| live event crew | High | 1k-2k |
| rigging company | High | 700 |
| trade show labor | High | 400 |
| audio visual labor | High | 600 |
| install and dismantle (i&amp;d) labor | High ,  trade-show booking | 250 |
| event production company | Medium ,  comparison phase | 5k+ |

### Local long-tail (one page per phrase)

These are gold because the searcher already named their city. Even 50 searches a month at 30% conversion = 15 leads.

- `stagehand staffing orlando`
- `stagehand staffing dallas`
- `stagehands tampa`
- `stagehands miami`
- `stagehands jacksonville`
- `stagehands dallas`
- `stagehands houston`
- `stagehands austin`
- `stagehands san antonio`
- `riggers orlando`
- `riggers dallas`
- `trade show labor orlando`
- `trade show labor dallas`
- `concert crew orlando`
- `concert crew austin`
- `forklift operator event orlando`
- `forklift operator event dallas`
- `corporate event labor orlando`
- `corporate event labor dallas`
- `convention staffing orlando`
- `convention staffing dallas`
- `house of worship av labor orlando`
- `wedding rigger orlando`
- `festival labor orlando`
- `festival labor austin`

**Action:** Each of those gets its own landing page (eventually). Start with the top 4 city pages, expand later.

---

## 2. What's already wired into this site

The build already includes the foundational SEO basics ,  nothing more to install:

### Meta tags
Every page has a unique `<title>`, `<meta description>`, canonical URL, Open Graph tags, and Twitter Card tags. Each one is hand-written to the page's intent (not boilerplate).

### Structured data (Schema.org JSON-LD)
`index.html` includes a `ProfessionalService` block with both office addresses, phone, email, founding date, service types, areas served, and social links. This is what powers the Google "knowledge panel" and rich results.

### Semantic HTML
Pages use proper `<header>`, `<nav>`, `<main>` (implicit), `<section>`, `<h1>`-`<h3>`. There's only **one `<h1>` per page**, and it carries the primary keyword for that page.

### Sitemap + robots
`sitemap.xml` and `robots.txt` are in the project root. Submit `sitemap.xml` to:
- [Google Search Console](https://search.google.com/search-console) → Sitemaps → submit `https://www.showmasters.com/sitemap.xml`
- [Bing Webmaster Tools](https://www.bing.com/webmasters) → Sitemaps → submit same URL

### Images
- Logo and PFP assets are SVG (infinitely sharp + tiny file size).
- Every `<img>` has descriptive `alt` text.
- Stock hero videos are `preload="auto"` but the rest lazy-load behind the slider.

### Internal linking
Every page in the nav points to every other page. Footer mirrors it. CTAs in body point to `contact.html#estimate`.

---

## 3. The next 10 SEO tasks (in priority order)

### Task 1 ,  Stand up the 2 location landing pages
Two new files: `orlando.html` and `dallas.html`. Each should:
- Have its city in the `<title>`, `<h1>`, first paragraph, image alt text, and URL.
- Embed the Google Map of that office.
- List service areas around that office (neighborhoods, suburbs).
- Show 3-5 testimonials from clients in that city.
- Have a clear CTA at the bottom.
- Be linked from the global nav under "Where" or a dropdown.

### Task 2 ,  Submit sitemap.xml + verify ownership
Google Search Console (5 minutes). Bing Webmaster Tools (5 minutes). Both will start indexing within 48 hours.

### Task 3 ,  Create 5 city-secondary landing pages
After Orlando and Dallas are stable, add: `tampa.html`, `miami.html`, `jacksonville.html`, `dallas.html`, `houston.html`. Same template, different city.

### Task 4 ,  Write 4 blog posts (one a month, then more)
Suggested first 4 (target = featured snippet):
1. **"How much does stagehand labor cost in 2026? A buyer's guide."** ,  pulls the search term `stagehand cost`
2. **"Stagehand vs. technician: what's the difference and why does the labor bill care?"** ,  this is literally the SMPL pitch
3. **"What worker's comp + GL insurance should you expect from your stagehand company?"**
4. **"Trade show I&D in Orlando: a producer's labor checklist for OCCC, OCC, and Gaylord Palms."**

### Task 5 ,  Add Service schema to `what.html`
Each service should have a `Service` JSON-LD block. Tells Google "we do X, Y, Z" so you can win the "services" Google panel.

### Task 6 ,  Add FAQ schema to `how.html`
The "What's baked into the rate" section already has FAQ-style content. Wrap it in `FAQPage` JSON-LD and Google will give you accordion-style rich results in search.

### Task 7 ,  Page speed audit
Run [PageSpeed Insights](https://pagespeed.web.dev/). The site should score 90+ already because there's no JS framework, but compress the hero videos with [HandBrake](https://handbrake.fr/) if mobile is &lt;90.

### Task 8 ,  Get backlinks from 5 industry sources
- ProductionHub directory listing (free)
- BizBash supplier listing
- Local Chamber of Commerce (Orlando + Dallas)
- LinkedIn company page (already exists)
- Industry guest post on Live Design Online

### Task 9 ,  Add breadcrumb schema to sub-pages
Adds the breadcrumb trail under each search result. Improves CTR by ~5%.

### Task 10 ,  Set up Google Analytics 4 + Google Tag Manager
Free. Tells you which keywords actually convert vs. just bring traffic.

---

## 4. The on-page SEO rules to never break

Every page needs:

- [ ] **Unique &lt;title&gt;** ,  under 60 characters, includes primary keyword + city + brand.
- [ ] **Unique &lt;meta description&gt;** ,  150-160 characters, includes keyword, says what's on the page, ends with a CTA.
- [ ] **One &lt;h1&gt;** ,  matches title intent.
- [ ] **Two or three &lt;h2&gt;s** ,  supporting headlines.
- [ ] **Keyword in first 100 words** ,  natural, not stuffed.
- [ ] **Internal links to 2-4 other pages.**
- [ ] **One external link to an authority** (e.g. Wikipedia, .gov, industry body) ,  signals you cite sources.
- [ ] **Image alt text on every &lt;img&gt;** ,  describes the image AND mentions the keyword once.
- [ ] **Canonical URL set** ,  prevents duplicate-content issues.
- [ ] **Word count ~600+ on landing pages, ~1200+ on blog posts.**

---

## 5. Local SEO ,  what makes a city page rank

To rank `stagehand staffing orlando` you need ALL of these:

1. **City in URL** (`/orlando` or `/orlando.html`)
2. **City in `<title>`** (`"Stagehand Staffing in Orlando, FL ,  Show Masters"`)
3. **City in `<h1>`** (`"Live event crew in Orlando"`)
4. **City in first paragraph** + 3-5 more times naturally
5. **Nearby neighborhoods named** (Winter Park, Lake Mary, Kissimmee, etc.)
6. **Map embed** of the Orlando office
7. **Local testimonials** from Orlando-area clients
8. **Local NAP** (Name, Address, Phone) consistent with GMB
9. **`LocalBusiness` JSON-LD** with the city-specific address
10. **GMB profile linked** to the page

Get 8/10 of those right and you'll outrank competitors in 60-90 days.

---

## 6. Tools to use (mostly free)

| Tool | Use | Cost |
|---|---|---|
| Google Search Console | Keyword rankings, indexing | Free |
| Google Analytics 4 | Traffic + conversion tracking | Free |
| Google Business Profile | Local pack ranking | Free |
| PageSpeed Insights | Site-speed audits | Free |
| Bing Webmaster Tools | Bing indexing | Free |
| Ubersuggest (free tier) | Keyword research | Free |
| Ahrefs Webmaster Tools | Backlinks (your own site) | Free |
| Screaming Frog (free tier) | Crawl your site for errors | Free up to 500 URLs |
| Local Falcon | GMB rank tracking by neighborhood | $24/mo |
| Whitespark Local Citation Finder | Find missing citations | $20/mo |

You don't need Ahrefs or SEMrush full subscriptions to start. The free tools cover 90% of the work.
