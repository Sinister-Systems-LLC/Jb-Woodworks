# Sinister Freeze

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-freeze` :: branch `agent/sinister-freeze/<topic>` :: purple accent
> **License:** AGPL-3.0-or-later
> **Status:** PH-RESEARCH (deep research in flight; project NOT started per operator)
> **Operator directive (verbatim 2026-05-21):** *"in parrallel start a project called Sinister Freeze. i want to make a full stack car tool for him. … be innovative"*

## What this is (north star)

Sinister Freeze is a **full-stack productivity + automation suite for luxury-car salespeople**, built first for **Joe at Ferrari of Winter Park** (a friend of the operator) and architected from day one to scale to an entire dealership.

It's the operator's "Eve" pattern applied to a car salesperson:
- watches every channel Joe runs (IG DMs, TikTok comments, Facebook Marketplace, Gmail, calendar)
- drafts every text he sends (DMs, follow-up emails, social posts, test-drive prep briefs)
- surfaces what needs his attention (hot leads, overdue follow-ups, posts that crushed, posts that flopped)
- asks him how he wants to handle it via the channel he prefers (Desktop / Telegram / morning email brief)

Joe gets his time back; the dealership gets a 10x salesperson; Sinister gets a real-world product.

## Operator goals (full prompt, verbatim 2026-05-21)

> "in parrallel start a project called Sinister Freeze. i want to make a full stack car tool for him. I want you to do this in parralle. With our main ui that we use with a good color schem,e layout etc. i want you to think about all the features we can make and add for him. Here is info about him:
>
> He is a good friend of mine that works at ferrari of winterpark and sells cars. he is trying to post on socials. runs instagram account, tiktok etc. manages emaisl facebook marketplace etc etc. THink on everything we can do for him and increase everything he does to power his bussiness and one day his entire dealership like how eve does for us. i want to have claude support for him as well with bat files so we have run it and pickup work on his system. make it all very easy for him to use launch claude talk to it etc. draft emails, anything he needs to do. creaete a full project strcutre, plan, everything we need to do this in parrallel but dont start the porject yet just preapre and plan and deep research evrything we can do that will actually help him sell more cars. be innovative"

## Status (as of 2026-05-21T11:30Z)

| Phase | What | Status |
|---|---|---|
| **PH-RESEARCH** | Background deep-research sub-agent producing `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` covering: (a) car-salesperson day-in-the-life, (b) existing tools landscape (DealerSocket / VinSolutions / Hammr.ai / Impel / Conversica), (c) social-for-cars playbook, (d) email + DM best practices, (e) 30+ innovation gaps with ROI / difficulty / novelty / release scoring, (f) tech-stack recommendation, (g) Eve-pattern for Joe, (h) risk / compliance, (i) MVP scope, (j) sources | 🚧 in flight |
| **PH0** | Project scaffold (this README + CLAUDE.md + PLAN.md placeholder + _PARTITION-README.md + Desktop bat + projects.json entry) | 🚧 this commit |
| **PH1+** | Will be defined by PLAN.md once research lands | 📋 awaits research |

## Branding (locked)

- **Primary accent:** purple `#7A3DD4` (Sinister canonical)
- **Background:** black / very-dark grey
- **Secondary:** dim cyan
- **Boot art:** Vault Boy ASCII spinner (same as Forge / Term / RKOJ)
- **Typography:** Cascadia Code (TUI / CLI surfaces) + Mona Sans / Inter (web surfaces)
- **Voice:** concierge, never pushy — matches Ferrari's brand-control posture

## One-click for Joe (planned)

Two Desktop bats land here once PLAN.md crystallizes:

- **`Sinister Freeze.bat`** — operator-side: opens a Claude session at `D:\Sinister Sanctum\projects\sinister-freeze\source\` for fleet-internal dev work.
- **`Joe's Freeze.bat`** — Joe-side: opens a Joe-friendly Claude session that auto-loads his context (recent leads, today's calendar, draft queue) and asks "what do you want to do today?" — picker has plain-English options: "Draft a reply", "Write a post", "Brief me on a test drive", "Look up a VIN", "Show me hot leads".

## Lane rules

- Branch on `agent/sinister-freeze/<topic>` cut from main
- All code AGPL-3.0-or-later + `Author: RKOJ-ELENO :: <date>`
- Joe's data sovereignty: NOTHING leaves his PC / our infra without explicit operator OK
- Ferrari brand-control respected: NO unauthorized Ferrari-corporate imagery; Joe's own photos only
- TCPA / CAN-SPAM compliance baked in (rate-limits + double-opt-in for any SMS/email automation)

## Composes with

- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md` — every Freeze module is disk-first, MCP-fast-path-optional
- `tools/forge-memory-bridge/` — Joe's lead notes + post drafts + test-drive briefs all land in forge-memory under `namespace=freeze`; Eve-pattern reads them for daily brief
- `tools/memory-graph-render/` — eventually renders Joe's customer network (leads + referrals + repeats)
- `automations/memory-consolidate.ps1` — nightly dedupe + confidence-raise on Joe's lead notes
- `automations/agent-host-routing.md` — adds a `sinister-freeze` row (likely Opus 4.7 for drafting, Haiku for triage)
- `automations/session-contracts.md` — 6 binding contracts inherit; Freeze adds a 7th "JOE-SAFETY" carve-out (no automated send without his click)
- `projects/sinister-panel/` — Panel surfaces Freeze's dealership-wide metrics once scaled
- `projects/sinister-forge/` — Eve-style watcher can spawn Freeze sub-agents for specific Joe tasks
- `projects/sinister-term/` — `sterm` CLI gets `/freeze` builtin that drops Joe into a Freeze session

## What this project will deliberately NOT do

- No replacement for DealerSocket / VinSolutions CRMs (we integrate via API; the dealership IT picks the system-of-record)
- No payment processing (DocuPad / RouteOne handle that; we surface signals)
- No raw automation of Ferrari-corporate IP (per brand-control)
- No social-media account password-storage (OAuth or operator's vault — never plaintext)

## Cross-references

- `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md` — research output (in flight)
- `_shared-memory/plans/sinister-freeze-2026-05-21/plan.md` — phase plan (drafted once research lands)
- `automations/session-templates/projects.json` — picker registry entry
- `C:\Users\Zonia\Desktop\Sinister Freeze.bat` — one-click launcher (post-research)
- `C:\Users\Zonia\Desktop\Joe's Freeze.bat` — Joe-side one-click launcher (post-research)
