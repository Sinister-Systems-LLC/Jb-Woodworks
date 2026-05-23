# Sinister Freeze :: Master Build Plan (v1 — research-derived 2026-05-21)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Status:** PH-RESEARCH ✅ shipped → PH0 ✅ scaffold shipped → PH1 next (operator decision-gates listed below)
> **Source of truth:** `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` (529 lines, 33 sources)

## North star (verbatim operator, see README.md)

A **full-stack productivity + automation suite** for Joe at Ferrari of Winter Park (catchment of Ferrari of Central Florida, Orlando MSA per source [16]), architected from day one to scale from one salesperson to an entire dealership. Sinister-branded. Operator's "Eve" pattern → Joe's personal **"Frost"**.

## Strategic wedge (the white-space)

> "every existing auto-AI tool sells to **dealerships**, not to **salespeople**. Joe has no personal cockpit. That's the wedge."  — research agent

Every dealership-tier tool (DealerSocket, VinSolutions, Conversica, Impel, Salesforce Automotive Cloud) is configured by IT and rolled down. Salespeople get assigned seats but no agency over their own AI. Sinister Freeze is **the salesperson's personal cockpit**: Joe-owned, Joe-controlled, Joe-customized — designed for *one* Ferrari closer first, then templatized for the whole floor in V2.

## Optimization metric (single)

**How many high-intent collectors Joe is actively nurturing in a given week, and how few low-value tasks he wastes time on.** Industry baseline: BDCs waste 60–70% of time on unqualified leads [27]; AI-led qualification cuts this 45% + boosts conversion 28%. Joe's lever is even higher because Ferrari LTV per client is $1M+ over decades.

## Phase plan

### ✅ PH-RESEARCH (shipped 2026-05-21)
- Deep-research markdown: 6,606 words, 33 footnoted sources, 10 sections, 45-idea scored backlog.
- Recommendation outputs: tech-stack, MVP scope, persona ("Frost"), compliance posture.

### ✅ PH0 (shipped 2026-05-21 — Sanctum master agent)
- `projects/sinister-freeze/{README,CLAUDE,PLAN,_PARTITION-README}.md` + me/eleno/joe/source partition dirs
- `automations/session-templates/projects.json` bumped v3→v4; `sinister-freeze` registered as project 13
- `C:\Users\Zonia\Desktop\Sinister Freeze.bat` operator-side launcher
- `_shared-memory/knowledge/sinister-freeze-project-doctrine.md` brain entry
- This PLAN.md replaces the placeholder

### 📋 PH-DECIDE (operator-gated; see "Open operator questions" below)
- Resolve Q1-Q6 below; defaults proceed if no answer in 7 days
- Spawn a dedicated `freeze` agent once Q's settle

### 🚧 PH1-MVP (target: 21 days from `freeze` agent spawn)

Per research §9 MVP scope:

| Day | Feature | R/D | Notes |
|---:|---|---|---|
| 3 | **Daily 7am brief** (email + Telegram) | 10/3 | calendar + leads + weather + priorities |
| 5 | **Voice-memo intake** | 10/4 | Telegram → Whisper → Claude → CRM row |
| 8 | **DM-triage classifier** | 10/5 | IG + FB Marketplace → Hot/Tire-Kicker/Fan/Spam/Service |
| 10 | **Test-drive prep brief** | 9/4 | auto 1-pager 24h before each booked drive |
| 12 | **End-of-day wrap** (7pm) | 8/3 | shipped + stuck + tomorrow top-3 |
| 14 | **Email draft assistant** | 9/5 | Gmail thread → draft reply Joe-approve |
| 16 | **Anniversary nudge** | 9/2 | 1y/3y/5y past-purchase trade-up draft |
| 18 | **Ferrari-spec lookup chatbot** | 8/3 | Telegram or PWA → instant Ferrari brochure recall |
| 19-21 | Polish + docs + Joe-onboarding wizard + handoff | — | |

**MVP success metric** (end Week 4): Joe reports ≥2 hours/day saved + ≥1 deal closed he would have missed.

### 📋 PH2 V1 (target: month 2)

From research §5 V1 cluster (15 features). Highest priority:

- **Auto-listing copy across 5 platforms** (#11) — same VIN → 5 voices (FB casual / AutoTrader formal / IG storytelling / TikTok hook / dealer SEO)
- **Photo-snap → full listing set** (#3) — phone shot → 18-shot listing set w/ bg swap + plate blur
- **Whale-watch radar** (#15) — scrape Cars&Bids/BaT/Hagerty/FerrariChat for trade-in conquest in 250mi radius
- **Client-life dossier** (#16) — public signals + Joe's private notes per VIP
- **Cross-store Ferrari inventory cache** (#40) — daily scrape all US Ferrari dealers; spec-match instantly
- **Allocation-waitlist comms automation** (#28) — top-5-client draft emails when allocation opens
- **Lead-source attribution dashboard** (#33) — closed-loop tracking IG/TT/referral → sold deal
- **Live-inventory carousel auto-publish** (#19) — DMS arrival → IG carousel draft + human-approve
- **Reel auto-cut from showroom B-roll** (#12) — 60s record → 3 platform cuts (TT/IG/YT) w/ native captions
- **Auto-FAQ deflection** (#22) — IG DM "how much?" → bot replies w/ build link + Joe-escalate-if-serious

### 📋 PH3 V2 (target: months 3-6)

From research §5 V2 cluster (12 features). Includes:

- **Ferrari-allocation strategy notebook** (#23) — per-client purchase history → Daytona/Le-Mans-tier eligibility prediction
- **Cavalcade-style client trip planner** (#14)
- **Sound-design library** (#13) — engine notes per model auto-overlaid on Reels
- **Trade-out timing model** (#31) — predict trade-up windows from ownership + lease data
- **Sentiment-tracking on responses** (#38)
- **Vault-Boy themed avatar Joe** (#24)
- **Wallet-of-the-client signal** (#35)
- **"Sinister Showroom" client-facing microsite** (#36)

### 📋 PH4 DEALERSHIP-SCALE (target: month 6+)

- Multi-tenant pivot — Postgres on Hetzner (mirrors Sinister Panel pattern); rows by dealer_id + salesperson_id
- Onboard whole-floor at Ferrari of Winter Park
- Dealership-wide rollup surface in Sinister Panel
- SLA + DPA + SOC2-light templates for dealership IT signoff

## Tech stack (decision-of-record — see STACK.md)

- **Backend:** FastAPI on `:5079`. Async I/O (15-20k req/s vs Flask 2-3k per [19]); Pydantic validation; auto-OpenAPI.
- **Frontend:** PWA (React + Vite + Tailwind, Sanctum purple) — installs on iPhone + desktop. No Electron bloat.
- **CLI:** `sinister-freeze` (mirrors `sterm` pattern) for power use.
- **DB v0:** SQLite at `~/.sinister-freeze/freeze.db`.
- **DB v2:** Postgres on Hetzner (Panel-mirror) at dealership scale.
- **AI:** Claude API (Sonnet 4.6 for drafts, Haiku 4.5 for triage). Whisper local for voice. GPT-4o vision for photo work. Optional.
- **Comms:** Telegram bot + Gmail OAuth + IG/FB Graph API + Twilio (V2 SMS).
- **Auth:** single-user v0 → OAuth + magic-link v2.

## Persona (decision-of-record — see PERSONA-FROST.md)

**"Frost"** = Joe's personal Eve. Vault-Boy avatar, Sinister purple. Watches IG/TT/FB-Marketplace/Gmail/calendar. Drafts email/post/test-drive-brief/anniversary-nudge. Surfaces hot leads + overdue follow-ups. Asks Joe via Telegram (default) / morning email brief / Desktop notification. Tone: concise, confident, deferential — never "I think you should"; always "Here's the data, your call."

## Compliance (decision-of-record — see COMPLIANCE.md)

- TCPA: written-consent per phone number; opt-in double-confirmed
- CAN-SPAM: footer + unsubscribe; sending domain SPF/DKIM/DMARC
- Meta Graph: 24h messaging window; 200 DM/hr cap
- Ferrari brand-control: no discount language; no track-illegal imagery; no Ferrari corporate IP generated
- Florida CCPA-adjacent: customer data tagged `pii=true`; audit-log every Frost read/write/send
- Local-first storage default; cloud only with operator + Joe explicit approval (V2+)

## Open operator questions (defaults proceed if no answer)

- **Q1.** Confirm persona name **"Frost"** (vs operator alt)? — default: Frost
- **Q2.** Telegram-first companion before PWA (saves 5 dev days)? — default: yes
- **Q3.** Daily-brief delivery time **7:00am ET**? — default: yes
- **Q4.** Onboard Joe directly (Joe's personal Gmail OAuth + Joe's personal IG) vs wait for Ferrari of Winter Park IT? — default: Joe directly; dealership IT engagement deferred to PH4
- **Q5.** Confirm dealership is **Ferrari of Central Florida** (Winter Park area) per [16]? — default: yes; branding language tracks
- **Q6.** Monthly Anthropic + Twilio + Meta Graph budget ~**$50-150/mo at MVP scale**? — default: yes; cap at $200/mo until V1

## Composes with

- `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` — source of truth
- `projects/sinister-freeze/FEATURES.md` — 45-idea prioritized backlog
- `projects/sinister-freeze/STACK.md` — tech-stack decision-of-record
- `projects/sinister-freeze/PERSONA-FROST.md` — Frost persona spec
- `projects/sinister-freeze/COMPLIANCE.md` — TCPA/CAN-SPAM/Meta/Ferrari enforcement
- `tools/forge-memory-bridge/` — Joe's leads + drafts + briefs land under `namespace=freeze`
- `tools/memory-graph-render/` — Joe's customer network graph (PH3+)
- `automations/memory-consolidate.ps1` — nightly dedupe + confidence-raise
- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`
- `_shared-memory/knowledge/sinister-freeze-project-doctrine.md`
- `_shared-memory/knowledge/jcode-feature-matrix.md`
- `automations/agent-host-routing.md` — add `sinister-freeze` row (Sonnet 4.6 drafting + Haiku 4.5 triage)

## Sources

All 33 footnoted sources are in the research doc at the bottom. Key picks:
- [16] Ferrari corporate / dealership network
- [17] Ferrari Group Code of Conduct
- [22] Sales follow-up cadence data 2025
- [27] AI lead-scoring + tire-kicker triage 2025
- [28] Personal CRM productivity 2025
