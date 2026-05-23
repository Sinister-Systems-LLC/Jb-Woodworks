<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# 04 — Booking Funnel: Stranger to Booked Show

The funnel is the steps a producer walks through, from "never heard of SMPL" to "wire transfer cleared." Every stage has a fixed shape, an expected conversion rate, and a specific thing we can do to lift it.

If you only fix one number this quarter, fix the inquiry-to-estimate-sent rate. That single step is the cheapest leverage in the whole funnel.

---

## The six stages

| # | Stage | What the producer is doing | What we're doing | Realistic conversion to next |
|---|---|---|---|---|
| 1 | Awareness | Hears "SMPL" for the first time (Google, referral, social, ad) | Show up where they search | 10–15% to site visit |
| 2 | Consideration | Visits the site, reads About + Where, scans reviews | Convince them in 90 seconds | 15–25% to inquiry |
| 3 | Inquiry | Submits the form, calls, or emails for an estimate | Respond within 4 hours | 70–85% to estimate sent |
| 4 | Estimate | Reads our quote, compares to a competitor or two | Tight quote, clear assumptions, no hidden fees | 30–50% to verbal yes |
| 5 | Verbal yes | Says "let's do it" but contract / deposit pending | Send contract + invoice same day | 90%+ to booked |
| 6 | Booked + executed | Show runs, crew shows, load-out clean | Crew Lead crushes it, invoice in 72h | 60%+ to repeat / referral |

Tour total: ~1.5% of awareness becomes a booking on the first touch. Repeat business + referrals are where the real economics live (see stage 6).

---

## Stage 1 — Awareness

**Where the first touch happens, in priority order:**

1. Google search for buyer keywords (see `02-SEO-STRATEGY.md`).
2. Google Business Profile in the local 3-pack (see `03-GMB-RANKING.md`).
3. Word-of-mouth referral from a happy client.
4. Cold outreach we initiate (see `07-OUTREACH-LIST.md`).
5. Industry directory listings (see `08-LOCAL-CITATIONS.md`).
6. Social media (see `11-SOCIAL-MEDIA-BASICS.md`).

**What to track:**
- New users per channel (Google Analytics 4 — free).
- GMB impressions per profile (GBP Insights).

**What to fix when this stage is the bottleneck:**
- Not enough impressions on either GMB profile? Add 25 more photos and post 4× weekly.
- Low organic search traffic? Add a city-specific landing page.
- No referral velocity? Read `09-REVIEWS.md` and send 30 review-request texts this week.

---

## Stage 2 — Consideration

The visitor lands on the site. They've already decided they might need crew. The site has 90 seconds to convince them we're the call.

**What they need to see in those 90 seconds:**

1. The headline — "We Make Great Days Happen, Every Day."
2. The trust strip — "Founded 2002 · 1,700+ Clients · 33 States · 130+ Crew on Payroll."
3. One concrete service preview (the six service cards).
4. One concrete testimonial.
5. The two locations (Orlando + Dallas) — so they know we're real.
6. The "Get an Estimate" CTA.

All six are above the fold by design.

**What to track:**
- Bounce rate on `/` (target <55%).
- Average session duration (target >75s).
- Time on `/contact` (target >40s — proves they're filling the form).

**What to fix when this stage is the bottleneck:**
- Bounce >65%? Hero copy or trust strip isn't landing. Test alternate headlines.
- Low time on /contact? Form is too long. Cut from 6 fields to 4.
- High `/about` traffic but low form starts? Add a clearer CTA on /about.

---

## Stage 3 — Inquiry

The producer hits "Request an Estimate." This is the most fragile stage in the funnel. A 4-hour response window separates "we won" from "we lost."

**The hard rules:**

1. **Same-day response.** Period. If the form arrives at 4pm on Friday, the reply goes out before 8pm.
2. **A real human reply.** Not "Thanks for your inquiry, someone will be in touch." The reply names a real person, references the producer's brief, and asks one clarifying question.
3. **CC the Crew Lead** who will probably run the show. They see the brief earlier and start thinking.

**What to track:**
- Time from form submit to first reply (target <4 business hours, average <90 minutes).
- % of inquiries answered same-day (target 100%).
- % of inquiries that get to a real estimate (target >75%).

**What to fix when this stage is the bottleneck:**
- Slow response? Add a Slack notification (or text alert) when the form fires.
- Inquiries dying without an estimate? The form is collecting people who aren't qualified. Add one filter question: "Approximate crew size needed?"
- Inquiries that turn into "do you have a website?" responses — they're already gone. Make sure the auto-reply confirms receipt and gives a phone number.

---

## Stage 4 — Estimate

The estimate is the document the producer compares to a competitor. Three things matter:

1. **Speed.** Send it within 24 hours of the brief. Faster = wins.
2. **Specificity.** Real numbers, real assumptions. "12 stagehands × 10 hours × $48 = $5,760" beats "approx $6k for labor."
3. **Trust signals embedded.** Show worker's comp & GL insurance numbers right on the estimate. Show that taxes + insurance are included, not extra.

**Estimate template (the basics):**

- Header: SMPL logo + estimate number + date.
- Event summary (2 sentences mirroring their brief).
- Crew table: role, count, hours, rate, line total.
- Subtotal, taxes, total.
- Assumptions: load-in/out times, holiday OT, gear separately.
- "What's baked in" callout: workers' comp, GL insurance, payroll taxes, Crew Lead, basic PPE.
- "What's not baked in" callout: equipment rental, lodging, travel, per diem.
- 7-day validity note.
- Signature block.

**What to track:**
- Estimate send → "yes" rate (target 30–50%).
- Estimate send → no-reply rate (target <20%; otherwise the estimate is leaking trust).

**What to fix when this stage is the bottleneck:**
- Lots of "we went with someone cheaper"? Sharpen the trust-signal call-outs. They're not buying labor — they're buying risk-coverage.
- Lots of "let me get back to you" → silence? Add a 72-hour follow-up email automatically.
- Producers asking lots of clarifying questions? The estimate isn't specific enough. Bake more detail into the line items.

---

## Stage 5 — Verbal Yes

They've said "let's do it" on a call or email. Don't celebrate yet — about 10% of verbal yeses still fall through.

**What to do in the next 4 hours:**

1. **Confirm in writing.** A short email: "Confirming — SMPL will crew the [Event] on [Dates] per the attached estimate. Sending the contract + deposit invoice now."
2. **Send the contract.** Simple PDF, e-signable. Two-page max.
3. **Send the deposit invoice.** 50% upfront for first-time clients, net-30 for established.
4. **Calendar block.** The Crew Lead's schedule gets locked.
5. **Hand off internally.** Project lead gets the brief, payroll gets the invoice, dispatch gets the date.

**What to track:**
- Verbal yes → signed contract rate (target >90%).
- Average days from verbal yes to first deposit cleared (target <5 days).

**What to fix when this stage is the bottleneck:**
- Contracts dragging? Use a single-button e-sign tool (Dropbox Sign, Adobe Acrobat, even just a PDF with checkboxes). Make it 30-second easy.
- Deposits dragging? Net-30 is too generous for first-timers. Insist on 50% upfront.

---

## Stage 6 — Booked + Executed

The show runs. This is where SMPL actually delivers the goods. Conversion to repeat/referral here is the single highest-margin business we can do — repeat clients cost ~$0 to acquire.

**The post-show ritual (every single time):**

1. **End-of-show check-in.** Crew Lead walks the producer through anything noteworthy before leaving site.
2. **72-hour invoice.** No exceptions. Detailed line items, photo of the load-out timesheet attached.
3. **Day-3 thank you.** A short email from the project lead: "Thank you for trusting us. Anything we should fix for next time?"
4. **Day-7 review ask.** See `09-REVIEWS.md` for the exact script.
5. **Day-30 follow-up.** "Working on anything in [their season]? Want first dibs on our calendar?"

**What to track:**
- Repeat-booking rate (target 60%+ within 12 months of first show).
- Net Promoter Score (one-question survey 7 days post-show; target 70+).
- Referrals per repeat client (target 1 in 3 sends us at least one referral within a year).

**What to fix when this stage is the bottleneck:**
- Low repeat rate? The show went fine but we didn't ask for the next one. Add the day-30 follow-up to dispatch's calendar automatically.
- No referrals? Launch the formal referral program ($250 thank-you per closed referral; see `01-MARKETING-PLAN.md` Q4).

---

## What the math looks like end-to-end

Assume Q1 numbers:

- 5,000 site visits (Google + GMB + outreach + referral).
- × 18% inquiry rate = 900 inquiries (no — too high; realistic = 4% inquiry rate from cold visits, 25% from referral; weighted = ~7% = 350 inquiries).
- × 75% to estimate = 263 estimates sent.
- × 35% to verbal yes = 92 verbal yeses.
- × 92% to contract = 85 contracts signed.
- × 100% to executed (we don't bail) = 85 booked shows.
- × 60% repeat in next 12 months = 51 repeat bookings.
- × 33% generate one referral = 28 referrals.

This is the model. If a quarter underperforms, walk down this list and find the stage where the rate dropped. Fix that one thing. Move on.
