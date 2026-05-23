# Completion Plan — what's left to finish

**Compiled:** 2026-05-23
**Site state:** Static HTML/CSS/JS site at `C:\Users\Zonia\Desktop\Showmasters Site\` serving on `localhost:8080`. 33 HTML pages, 0 broken refs, all HQ/Hub terminology accurate, real social handles, real Fort Worth address.

---

## Section A — code/content work I can finish unattended

### A1. Visual verification pass on the new realmap (priority: high)

The new US map (`public/img/us-realmap.svg`) renders 56 state geometries projected via Albers USA. I have not yet visually confirmed the projection looks geographically correct at the rendered scale. The viewBox is large (2993×3199) so it may need scaling adjustments or a tighter clamp on the projection multiplier.

**Action:** Open `/where.html` and `/index.html` in browser, screenshot, fix any aspect-ratio or zoom issues. Tune the `* 1000` projection multiplier in `.tmp/render_real_map.py` if states render too large.

**Estimated time:** 20-30 min

---

### A2. Differentiate the remaining section headings (priority: medium)

Pillars + flow now have unique heading treatments. Three more sections on the homepage still use the standard `eyebrow + section-headline + section-subheadline` pattern:

- Testimonials section
- FAQ section
- Where preview (above the map)

**Action:** Give each one a distinct visual personality (magazine pull-quote / Q&A label / coordinates-grid).

**Estimated time:** 45 min

---

### A3. Wire real nano-banana brand photography on the shows portfolio (priority: low)

The `/shows.html` portfolio shows 16 event cards with Unsplash stock photos. Brand-locked nano-banana renders would be more consistent with the rest of the site.

**Action:** Fire a 16-image nano-banana batch (~$0.64) keyed to the existing card categories (corporate, concert, festival, trade show, sports, theater, worship, private).

**Estimated time:** 45 min including generation + wiring

---

### A4. Decide and apply "Dallas" vs "Fort Worth" copy treatment everywhere (priority: low)

The street address is Fort Worth, TX 76135 (correct). But many pages still say "Dallas" or "DFW" as the metro reference (correct colloquially since Dallas-Fort Worth is the same metro). `dallas.html` exists as the Dallas-metro city page.

**Decision needed (operator):** Keep "Dallas" as the metro reference everywhere it appears in body copy, OR change to "Fort Worth" / "DFW" everywhere.

**Action:** Once decided, one Python pass to update across all files.

**Estimated time:** 15 min once decided

---

### A5. Add the 12th content-calendar blog post (priority: low)

11 blog posts published. Three calendar slots still open: Aug (1099 vs W-2), Oct (multi-day convention crewing), Dec (year-in-review).

**Action:** Write one more producer-facing post (Aug 1099 vs W-2 is the highest-SEO-value remaining slot). Wire into blog.html and sitemap.

**Estimated time:** 30-45 min per article

---

### A6. Final QA + cleanup pass (priority: high)

- Lighthouse audit on homepage + 2-3 key pages
- Image-size audit (PNG → WebP conversion for the nano-banana photos to halve page weight)
- Verify hero video carousel cycles correctly
- Verify homepage intro animation plays on every refresh (and only the homepage)
- Verify path floater resets on homepage landing
- Verify cookie banner shows once + persists across pages
- Verify mailto: forms build correct subject + body
- Click every nav link on every page
- Click every footer link on every page
- Visual check on mobile breakpoint (320px / 414px / 768px)

**Estimated time:** 90 min

---

### A7. Trim `app-v2/` scaffold from the deploy bundle (priority: medium)

`app-v2/` contains a Next.js scaffold for a future backend. It should not deploy with the static marketing site.

**Action:** Confirm `robots.txt` disallows `/app-v2/` (already done), and add deploy-time exclusion to whichever host is chosen. Or move `app-v2/` outside the site root entirely.

**Estimated time:** 5 min

---

### A8. Tighten any remaining "wordy" copy (priority: low)

Operator flagged that the site reads verbose in places. The site has already had one trim pass. Targets for a second pass:

- About page story paragraphs
- The "How we work" 4-step blurbs
- Several blog-post ledes

**Action:** Read through with a red pen mindset. Cut 15-25% of word count without losing meaning.

**Estimated time:** 90 min

---

## Section B — operator-gated work (can't do without you)

### B1. Pick a hosting platform and deploy

Three recommended options (full detail in `04-Go-Live-Plan.md`):

- **Cloudflare Pages** — free, fastest, easiest
- **Netlify** — has Forms built-in
- **Vercel** — also free, polished UX

**Why it's blocking:** Hosting accounts require your email + payment method. Domain DNS access requires your domain-registrar credentials.

**What I need from you:** Pick one. Sign up. Either drag-and-drop the folder OR give me github push access so I can push to a repo connected to the host.

---

### B2. DNS cutover for showmasters.com

The current showmasters.com is hosted somewhere. To launch the new site you need to either:

- Point the same domain at the new host (DNS edit at the registrar — usually GoDaddy or Namecheap)
- Or use a staging subdomain (`new.showmasters.com`) first, test, then flip the apex

**What I need from you:** Domain-registrar credentials (or you do the DNS edit yourself with my guidance). The TTL should be lowered to 300 seconds 24h before cutover.

---

### B3. Forms backend (Formspree or Netlify Forms)

Forms currently use `mailto:` — opens user's email client. ~30% of users have no default mail client configured and the submission silently fails.

**For production:** Sign up at https://formspree.io (free 50/mo, $10/mo for 1,000), create 3 endpoints (estimate / order / apply), give me the endpoint URLs, and I'll wire them into the forms in ~10 min.

**What I need from you:** A Formspree account + the three endpoint URLs, OR confirm we host on Netlify and I'll wire Netlify Forms directly.

---

### B4. Google Business Profile claims (×2)

GBP is the single biggest local-SEO ranking factor. Two profiles needed:

- **Show Masters Production Logistics — Fort Worth HQ** (6340 Lake Worth Boulevard, Fort Worth, TX 76135)
- **Show Masters Production Logistics — Orlando Hub** (4906 Patch Road, Orlando, FL 32822)

**What I need from you:** A Google account at SMPL. I'll write the listings + recommend service areas + draft the Q&A seed content; you click through verification + receive the postcards (3-5 business days each).

---

### B5. Analytics installation

Recommended: **Plausible** ($9/mo, cookieless, privacy-respecting) OR **Cloudflare Web Analytics** (free, also cookieless).

**What I need from you:** Sign up for one. Give me the embed snippet. I'll add it to the site in ~5 min.

---

### B6. Social account confirmation

The site now links to the real social handles pulled from showmasters.com:

- Instagram: @showmastersproduction
- Facebook: ShowMastersPL
- LinkedIn: show-masters-production

**What I need from you:** Confirm these are the right active accounts. If any of them changed since the live site was last updated, give me the new URLs.

---

### B7. Email infrastructure verification

Forms route to `Orders@ShowMasters.com`. Need to confirm:

- That inbox is actively monitored
- Spam filtering doesn't bury new estimate requests
- Auto-reply (if any) is on-brand

**What I need from you:** Either confirm the inbox is fine as-is, or set up an auto-responder. Optional: add `jeremy.hutcheson@showmasters.com` as a BCC on estimate-form submissions (we'd need to wire that into the form router).

---

### B8. Google Search Console + Bing Webmaster Tools

After the site is live + DNS resolves, I submit the sitemap. Requires a verified property in each.

**What I need from you:** Add `https://www.showmasters.com` as a property in each tool (or give me access to SMPL's existing properties).

---

## Section C — nice-to-haves / future work

### C1. Convert PNG → WebP for the nano-banana photos

The site uses ~30 nano-banana PNG files at ~150-250KB each. WebP conversion typically halves the file size with no visible quality loss. Saves ~3-5MB of total page weight.

**Estimated time:** 30 min (single script + replace references)

### C2. Replace Unsplash stock photos with brand-locked nano-banana

The 16 show portfolio cards + the 6 role-card replacements use Unsplash stock. These could all be replaced with brand-locked imagery.

**Estimated cost:** ~$1.00 in nano-banana generation
**Estimated time:** 60 min

### C3. Build an actual newsletter capture

The "Want these in your inbox" form on blog.html is interim — posts to /contact#estimate. Real newsletter capture would use Mailchimp / Beehiiv / ConvertKit free tier.

**What I need from you:** Pick a newsletter platform, give me the API key or signup-form URL.

### C4. CRM integration

If form submissions should land in HubSpot/Salesforce/Pipedrive/Airtable, add an integration via Zapier or directly through the forms backend.

**What I need from you:** Confirm whether SMPL has a CRM today + which one.

### C5. The `dallas.html` page rename

Should the Dallas city page become `fort-worth.html` since the actual office is in Fort Worth? Or keep `dallas.html` since "Dallas" is the wider-known metro and SEO target?

**My recommendation:** Keep `dallas.html` for SEO ("stagehand crew Dallas" has more search volume than Fort Worth), but update the page hero to reference both cities ("Stagehands & crew in Dallas-Fort Worth").

---

## Section D — recommended order of operations to go live in 7 days

| Day | What | Owner |
|---|---|---|
| Day 0 | Pick hosting (B1). Sign up for Formspree (B3) and Plausible (B5). | Operator |
| Day 1 | I deploy to staging URL via host. Wire forms backend. Verify everything works on the staging URL. | EVE + operator |
| Day 2 | Visual + content review on staging. Operator edits / requests. | Operator |
| Day 3 | I apply edits. Run Lighthouse, fix top issues. Confirm performance is acceptable. | EVE |
| Day 4 | DNS lower TTL to 300s in registrar (B2). Final review on staging. | Operator |
| Day 5 | DNS cutover. SSL provisions. Test live URL. Submit sitemap to GSC (B8). Claim GBP profiles (B4). | Operator + EVE |
| Day 6 | Watch for 24h. Verify form submissions land in Orders@. Monitor analytics for traffic. | Operator + EVE |
| Day 7 | Post-launch QA. Polish anything that landed weird. Plan first 30 days of content + reviews. | EVE + operator |

---

## What's already done (so you know what you don't need to ask about)

- Site structure: 33 HTML pages built, 11 blog posts, 6 marketing playbook MD files, sitemap, robots.txt, 404
- Brand visual system: dark + gold, serif italic accents, monospace mono labels, atmospheric heros
- Real US map: state-outline SVG with hub beacons (verification pending)
- Forms: estimate, order, apply — all wired to `Orders@ShowMasters.com` via mailto (production wiring blocked on B3)
- Single-open accordion FAQ + open-state header bar
- Path-tracker floater that resets on homepage landing
- Cookie banner that shows once and persists dismissal
- Scroll-to-top floating button
- Smooth page transitions with intro skip when going home
- Site-wide HQ swap to Texas HQ + Florida Hub
- Real Fort Worth, TX 76135 address everywhere
- Real social handles from live showmasters.com
- Roman-numeral chapter mark on pillars + technical-doc heading on flow
- Order-page "Not sure what to order?" disclaimer + free-estimate CTA
- Show Masters Deliverable package on Desktop: 6 markdown playbooks (README, SEO, Social, Marketing, Go-Live, Gear+Apparel) + 11 blog post HTMLs
- All sensitive / internal references scrubbed from deliverables

---

## How to use this plan

1. Skim **Section B** first — those are the items blocking launch
2. Tell me which **Section A** items you want me to finish now
3. **Section D** is the calendar; ignore if you want to go faster or slower
4. **Section C** is purely optional polish — skip until after launch unless something jumps out
