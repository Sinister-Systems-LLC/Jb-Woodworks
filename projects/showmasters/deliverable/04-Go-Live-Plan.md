# Show Masters — Go-Live Deployment Plan

**Compiled:** 2026-05-23
**Site source:** `C:\Users\Zonia\Desktop\Showmasters Site\`

---

## TL;DR — Fastest path to live

If you want to be on `https://www.showmasters.com` in **under 90 minutes** without touching a server:

1. Sign in to **Cloudflare Pages** (or **Netlify** or **Vercel** — any of the three works; Cloudflare is recommended for cost + speed)
2. Drag the `Showmasters Site` folder into a new project (or push it to a GitHub repo and connect)
3. Point the existing showmasters.com DNS at the host's nameservers (or add a CNAME)
4. Wait 5-15 minutes for SSL to provision
5. Test the live URL
6. Submit sitemap to Google Search Console

The site is a static HTML/CSS/JS bundle with no build step required. Any modern static host handles it.

---

## What's in the source folder

```
Showmasters Site/
├── *.html              # 24 marketing pages
├── blog/               # 11 blog posts
├── style.css           # single global stylesheet
├── script.js           # single global JS
├── public/
│   ├── img/            # logos, generated photos, favicons, og cards
│   ├── video/          # hero video clips
│   └── js/             # interactive-map.js
├── BRANDING/           # source brand assets (don't deploy)
├── MARKETING/          # planning docs (don't deploy)
├── app-v2/             # future Next.js scaffold (don't deploy)
├── manifest.json       # PWA manifest
├── sitemap.xml         # XML sitemap (35 URLs)
├── robots.txt          # crawler hints
└── 404.html            # custom not-found page
```

Three folders should be excluded from deployment: `BRANDING/`, `MARKETING/`, `app-v2/`. The existing `robots.txt` already disallows them but they shouldn't ship to the live host either. Add a `.gitignore` / Netlify ignore file before deploy.

---

## Hosting options (pick one)

### Option A: Cloudflare Pages — **recommended**

**Why:** Free, fastest CDN, free SSL, auto-HTTPS, generous build minutes, the easiest path for non-engineering teams.

Steps:
1. Sign up at https://pages.cloudflare.com
2. Connect a GitHub repo OR drag-and-drop the folder
3. Build settings: **No build command**, output directory: `/`
4. Deploy
5. In Cloudflare DNS, add a CNAME for `www.showmasters.com` → the auto-generated `*.pages.dev` URL
6. Add an A or ALIAS for the apex `showmasters.com` pointing to Cloudflare's anycast IPs (provided in dash)
7. Enable "Always Use HTTPS" in SSL/TLS settings

**Cost:** Free tier covers this site comfortably (500 builds/mo, unlimited bandwidth).

### Option B: Netlify

**Why:** Has Netlify Forms built-in — useful if you want forms to email Orders@ShowMasters.com without writing backend code.

Steps:
1. Sign up at https://netlify.com
2. Drag-and-drop the site folder
3. Set custom domain to `showmasters.com`
4. Netlify provisions SSL automatically (5-15 min)
5. Enable Netlify Forms in the form HTML by adding `data-netlify="true"` to each `<form>` tag

**Cost:** Free tier handles 100 form submissions/mo. Paid tier $19/mo for 1,000.

### Option C: Vercel

Similar to Netlify, also free for static sites. Forms require third-party integration.

### Option D: Self-host on existing infrastructure

If SMPL already has a server (the previous showmasters.com is hosted somewhere), keep that and just push the new files. Lower cost predictability but more ops overhead.

---

## DNS configuration

The new site needs these records on whoever owns the `showmasters.com` domain (likely GoDaddy, Namecheap, or whoever was used for the existing site):

| Record | Type | Value |
|---|---|---|
| `@` (apex) | A or ALIAS | host's IP or alias target |
| `www` | CNAME | host's auto-URL (e.g. `showmasters.pages.dev`) |
| `mail` | MX | (leave existing) |
| `_dmarc`, `_domainkey` | TXT | (leave existing email auth records) |

**Don't touch:** Existing MX records for email. Email is independent of website hosting. Breaking those means `Orders@ShowMasters.com` stops receiving mail.

DNS propagation typically takes 5 minutes to 2 hours depending on TTL.

---

## SSL

All three recommended hosts provision Let's Encrypt SSL automatically. **You don't need to buy a certificate.** It just works once DNS resolves.

Verify by hitting `https://www.showmasters.com` after the deploy. Browser padlock = working.

---

## Forms: making the contact / order / apply forms deliver

The forms currently use `mailto:` — opens the user's email client. That works as a fallback but loses ~30% of submissions (users without a default mail client configured).

**Production setup** for actual form-to-inbox delivery:

### Option 1 (recommended): Formspree

1. Sign up at https://formspree.io (free for 50 submissions/mo, $10/mo for 1,000)
2. Create three endpoints — one for each form (estimate, order, apply)
3. Replace the `mailto:` action in each form with the Formspree URL
4. Set the destination email to `Orders@ShowMasters.com`

### Option 2: Netlify Forms

If you're hosting on Netlify, just add `data-netlify="true"` to each `<form>` tag and Netlify auto-detects and routes submissions to a configured email.

### Option 3: Self-hosted endpoint

Build a tiny serverless function (Cloudflare Worker, Vercel Function, or AWS Lambda) that accepts a POST and emails via SES/SendGrid. ~30 lines of code, $0-5/mo. Overkill unless you need custom logic.

**Either way:** Test every form end-to-end on the staging URL before flipping DNS to production.

---

## Analytics

Install before launch so you have day-one data.

### Recommended: Plausible (paid, $9/mo) or Cloudflare Web Analytics (free)

Why not Google Analytics 4: privacy-tightening regulations make GA4 increasingly cookie-banner-burdensome. Plausible and Cloudflare are cookieless and avoid that whole compliance category.

**Setup:**
1. Sign up for the analytics provider
2. Add their snippet to `style.css` adjacent code injection OR before `</body>` in every HTML file (one small script tag)
3. Verify data starts arriving in the dashboard

If you must use GA4: add the Google tag, but then the cookie banner needs to actually gate analytics consent (currently it's informational only).

---

## Google Search Console

After DNS is live + SSL works:

1. Go to https://search.google.com/search-console
2. Add `https://www.showmasters.com` as a property
3. Verify ownership via DNS TXT record OR HTML file upload
4. Submit the sitemap: `https://www.showmasters.com/sitemap.xml`
5. Set up email alerts for indexing issues

Expect first crawl within 24-48 hours. Full index in 1-2 weeks.

---

## Google Business Profile (do same day as launch)

Critical for local SEO. Two profiles needed:

1. **Show Masters Production Logistics — Fort Worth HQ**
   - Address: 6340 Lake Worth Boulevard, Fort Worth, TX 76135
   - Phone: (877) 765-2267
   - Hours: by appointment / 24-7 orders desk
   - Service area: Texas + adjacent states
   - Categories: Event production, Stagehand staffing, Audio visual equipment supplier
   - Upload 10+ photos (logos, crew at work, gear, team)

2. **Show Masters Production Logistics — Orlando Hub**
   - Address: 4906 Patch Road, Orlando, FL 32822
   - Phone: (877) 765-2267
   - Same hours, service area: Florida + adjacent states
   - Same categories
   - Upload 10+ photos

Verification: Google sends a postcard with a verification code to each address (3-5 business days).

---

## Pre-launch checklist (do every item before flipping DNS)

- [ ] All HTML pages load on the staging URL with no console errors
- [ ] All internal links work (no 404s)
- [ ] All images load (no broken image icons)
- [ ] All three forms submit successfully (to Formspree or Netlify Forms)
- [ ] Form submissions actually arrive at Orders@ShowMasters.com
- [ ] Phone link works (`tel:` opens dialer on mobile)
- [ ] Email link works (`mailto:` opens email client)
- [ ] Social links open correct social profiles
- [ ] Mobile view tested on iOS Safari + Android Chrome
- [ ] Cookie banner appears once + persists dismissal
- [ ] Cookie banner links to /cookies.html correctly
- [ ] Privacy + Terms + Cookies + Accessibility pages all render
- [ ] /sitemap.xml loads with 35 URLs
- [ ] /robots.txt loads correctly
- [ ] /404.html renders (test by visiting a bad URL)
- [ ] Open Graph cards preview correctly (test with https://opengraph.dev or https://metatags.io)
- [ ] Favicon shows in tabs
- [ ] SSL certificate valid + auto-renewing
- [ ] HTTPS redirect works (http:// → https://)
- [ ] www → apex redirect (or vice versa) consistent

---

## Launch sequence (the day-of timeline)

**T-24h:** Final pre-launch checklist run-through. Fix any failures.

**T-1h:** Cut over DNS records. Update TTL to 300 seconds if it's currently long.

**T+0:** Watch DNS propagation at https://dnschecker.org

**T+15min:** Test live URL in a fresh browser (incognito) once SSL is up.

**T+30min:** Submit sitemap to Google Search Console.

**T+1h:** Verify forms still deliver. Send a test estimate request.

**T+24h:** Check Search Console for first crawl. Check analytics for first traffic.

**T+72h:** Verify Google Business Profile postcard delivery is in progress.

**T+7d:** Site indexed in Google for branded queries ("show masters production logistics"). Local SEO begins to compound.

---

## Post-launch (first 30 days)

Week 1:
- Verify Google Business Profile listings (postcards arrive)
- Get 3-5 client reviews on GBP
- Submit to Bing Webmaster Tools

Week 2:
- Submit to industry directories (see `03-Marketing.md`)
- Start the social media cadence (see `02-Social-Media.md`)
- Publish the first scheduled blog post

Week 3:
- Run a Lighthouse audit and address top 3 performance issues
- Verify all forms still work and submissions arrive

Week 4:
- First monthly analytics review
- First SEO position check (use Ahrefs or SEMrush free trial)

---

## What's NOT included in this go-live

- **Email infrastructure** — `Orders@ShowMasters.com` and `jeremy.hutcheson@showmasters.com` are handled separately from the website. Don't touch email DNS records during the launch.
- **CRM integration** — Form submissions go to email today. If you want them in HubSpot, Salesforce, etc., add that integration after launch when there's stable traffic.
- **app-v2 / Next.js back-end** — That's a future project. The current static site does everything needed for marketing + lead capture.

---

## Estimated total cost to go live

| Item | Setup | Monthly |
|---|---|---|
| Hosting (Cloudflare Pages) | $0 | $0 |
| Domain (if not already owned) | $12-15/yr | — |
| SSL | $0 | $0 |
| Forms (Formspree starter) | $0 | $0-10 |
| Analytics (Cloudflare or Plausible) | $0 | $0-9 |
| Google Business Profile | $0 | $0 |
| **Total** | **$0-15** | **$0-19** |

Site can be live and fully functional for under $20/month. Most months it's free.

---

## Who owns what after launch

| Item | Owner |
|---|---|
| Site content + design | SMPL marketing lead |
| DNS + domain | SMPL IT or designated person |
| Hosting account | SMPL designated person |
| Forms / inbox | Orders@ShowMasters.com routes to Bill + Jeremy |
| GBP listings | SMPL local marketing |
| Social media | SMPL social lead |
| Analytics access | SMPL leadership + marketing |
| SEO monitoring | SMPL marketing or external contractor |

Document this in a shared doc on day one so nobody loses access if a person leaves.
