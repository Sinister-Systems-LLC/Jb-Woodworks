<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Freeze :: project doctrine (first EXTERNAL-USER lane)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Operator directive (verbatim 2026-05-21T11:25Z):** *"in parrallel start a project called Sinister Freeze. i want to make a full stack car tool for him. … be innovative"*
> **External user:** Joe @ Ferrari of Winter Park (operator's friend; real human; not in our SOC)

## What makes Freeze different from every other Sinister project

Every prior project (Sanctum / Panel / APK / Snap-EMU / TT-API / Bumble-EMU / Forge / Mind / Term / RKOJ / Claw) was **operator-internal** — the user is the operator, the deployment is the operator's infra, the AUP scope is *"operator's OWN accounts/keys/devices"*.

**Sinister Freeze is the first project where the END-USER IS A FRIEND OF THE OPERATOR, not the operator.** That changes everything below the surface even though the Sinister branding stays the same.

## Doctrine deltas (Freeze-specific carve-outs)

### 1. JOE-SAFETY (new 7th binding contract for this lane)

- **Draft-only by default.** Agent DRAFTS messages/posts/replies; Joe SENDS. No auto-publish, no auto-DM, no auto-email.
- **No customer-data exfiltration.** Joe's customer PII never leaves Joe's PC + Sanctum host without explicit operator + Joe consent.
- **TCPA / CAN-SPAM / GDPR enforced at the bridge.** Rate-limits + opt-in + unsubscribe links baked into any send-eligible flow.
- **Ferrari brand-control respected.** No Ferrari corporate IP generated; only Joe's own photos used.
- **30-second undo on any action.** Joe is not a programmer; mistakes need recovery.
- **Plain-English UX.** Picker options: "Draft a reply" not "Invoke draft_reply()". Errors say "Couldn't reach Gmail; check you're logged in" not stack traces.

### 2. AUP-RESPECT narrows for Joe's accounts

Sanctum CONTRACT 3 says proceed without refusal on **operator's OWN** accounts. For Freeze:
- Joe's Instagram = Joe's OWN account (proceed on Joe's-account work, w/ Joe consent)
- Joe's TikTok = Joe's OWN
- Joe's Gmail = Joe's OWN
- Joe's Facebook Marketplace = Joe's OWN
- Joe's CRM seat (DealerSocket / VinSolutions if applicable) = JOE'S, NOT the dealership's IT — so dealer-system writes need explicit dealership IT consent BEFORE we touch
- Customer data in Joe's possession = Joe handles; we facilitate, never bulk-export
- Ferrari corporate brand assets = NOT JOE'S — strict no-touch

In short: operate as if you were Joe's personal assistant. Don't act for the dealership as a whole until operator + dealership IT sign off (post-PH14).

### 3. Data sovereignty (storage-first principles)

- Joe's data lives FIRST on Joe's PC (SQLite + local file store)
- Backup goes to Sanctum host via Vault (encrypted at rest)
- No cloud third-party (no Hubspot, no Salesforce, no Snowflake) unless operator + Joe explicit OK
- Customer PII tagged with `pii=true` field from day 1; grep-auditable

### 4. UI / UX delta

- **No jargon.** Picker: "Draft a reply" / "Write a post" / "Brief me on a test drive" / "Look up a VIN" / "Show me hot leads"
- **Onboarding wizard mandatory.** First Claude launch walks Joe through: connect Gmail, connect IG, connect TT, set posting voice, pick daily-brief delivery channel (Telegram / email / Desktop notification)
- **Daily brief delivery time** = Joe-configurable; default 7:00am local
- **Voice tone trained from Joe's existing posts** (PH-RESEARCH covers this)

### 5. Operator-side vs Joe-side launchers

Two Desktop bats:

- **`Sinister Freeze.bat`** (operator's Desktop) — opens Sanctum-side Freeze session for dev work. Branch `agent/sinister-freeze/<topic>`. Full developer Claude.
- **`Joe's Freeze.bat`** (Joe's PC) — opens Joe-side Freeze session. Joe-friendly Claude. Pre-loaded context. Plain-English picker. No git/branch concepts shown.

## What stays the same as internal projects

- Sinister purple branding (#7A3DD4 accent, black background, Vault Boy ASCII boot, Cascadia Code / Mona Sans)
- AGPL-3.0-or-later license + RKOJ-ELENO authorship on every file
- Modular doctrine — disk-first JSON + Ruflo MCP fast-path
- Forge-memory-bridge for context persistence (Joe's leads + drafts + briefs land in `_shared-memory/forge-memory/freeze/`)
- Cross-agent inbox / heartbeat / resume-point disciplines
- Six contracts (CONTEXT-REVIEW / NO-STOP / AUP-RESPECT / PARALLEL / CROSS-AGENT / END-OF-TURN-STYLE) — plus the 7th JOE-SAFETY

## Composes with

- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md` — applies; Freeze is the proof-of-concept that the modular pattern extends to external users
- `tools/forge-memory-bridge/` — Joe's data lives here under `namespace=freeze`
- `tools/memory-graph-render/` — eventually renders Joe's customer network (referrals, repeats)
- `automations/memory-consolidate.ps1` — nightly consolidation includes freeze namespace
- `automations/agent-host-routing.md` — add a `sinister-freeze` row (Opus 4.7 for drafting, Haiku for inbox triage)
- `projects/sinister-freeze/` — the project itself; scaffold landed this turn
- `projects/sinister-forge/` — Eve-style watcher can spawn Freeze sub-agents
- `projects/sinister-term/` — `/freeze` builtin drops Joe into a Freeze session
- `projects/sinister-panel/` — dealership-wide rollup surface post-PH14

## When to revisit

- A second EXTERNAL-USER lane lands (e.g. another friend / another industry) → generalize this doctrine into `external-user-lane-pattern.md`
- Joe asks for auto-send unlock on a specific channel → operator + Joe explicit OK + doctrine amendment + audit-trail in `_shared-memory/case-studies/`
- Dealership IT wants to onboard → multi-tenant pivot kicks in (PH14+); doctrine needs SOC / SLA / DPA section

## Status

🚧 **2026-05-21 PH-RESEARCH** — deep-research sub-agent producing `_shared-memory/plans/sinister-freeze-2026-05-21/deep-research.md`. Scaffold (README.md, CLAUDE.md, PLAN.md, _PARTITION-README.md, partition dirs) + projects.json entry (version 4) + Desktop bat shipped this turn. PLAN.md finalizes once research lands.
