# Sinister Panel — "Complete Everything" Master Plan

> **Author:** sinister-panel agent · 2026-05-21
> **Operator phrase:** *"create a plan to fix and do everything i said to do do not miss anything"*
> **Current HEAD on Hetzner:** `0905443` (LIVE)
> **HEAD chain this session:** `2da39df → fa87e8a → c9ce2e2 → 0c3da2e → 0905443`

This plan is the single source of truth for every operator directive Panel knows about. Status enum:
- ✅ **SHIPPED-LIVE** — code on disk, merged to main, deployed, HTTP-verified.
- 🟡 **SHIPPED-NEEDS-VISUAL-VERIFY** — code merged + deployed, but visual correctness against operator's intent unverified.
- 🔧 **IN-FLIGHT** — current turn is shipping it.
- ⏳ **TIME-GATED** — code/decision waiting on an external clock.
- 🤝 **SIBLING-LANE** — owned by another agent (kernel-apk etc.).
- ❌ **NOT-STARTED** — captured here, hasn't been touched.

---

## Bucket A — Operator's verbatim asks from THIS session

| # | Operator verbatim | Status | Where it shipped |
|---|---|---|---|
| A1 | "phone 1 is in recovery mode fix it and make sure this does not happen again and if it does we can auto fix it from panel" | ✅ | Stage 1 `175a29b` + Stage 2 `fa87e8a` (autoRecoveryWorker + RecoveryPanel + auto-recover toggle) |
| A2 | "we dont use bat files anymore you have complete control to do this without bat files" | ✅ | Every deploy this session was master-self-executed SSH; zero bat invocation |
| A3 | "push to hetzner and make sure you completed everythign i said to do" | ✅ | 5 successful deploys this session (`fa87e8a`, `c9ce2e2`, `0c3da2e`, then dashboard-rebuild, then `0905443`) |
| A4 | "complete everything i said to complete and push to hetzner" | ✅ | UI-N + UI-O + Wave 22 polish closed in `c9ce2e2` |
| A5 | "i still dont see all changes i asked for live on hetzner fix that" | ✅ | Root-caused: dashboard image cache; force-rebuilt + new chunk hash served. Now verifying `docker inspect sinister-panel-dashboard:latest` on every deploy |
| A6 | "bottom of our side bar needs to look like this. two users: Operator and ELENO. based on our logins. have platform selector like we use to have but you removed it" | ✅ | `0c3da2e` — Super Admin pill + panel-users list + workspace dropdown + red Sign Out |
| A7 | "logos on our cards need to be bigger" | ✅ | `0c3da2e` — all 6 KPI icons bumped h-4 w-4 → h-6 w-6 |
| A8 | "map looks like shit. make it look more like what we did for lets text and have it auto set in this position but still allow movement etc" | 🟡 | `0c3da2e` — HOME_ZOOM 2.05→1.55, center [0,28]→[10,12], scale 320→240, MIN_ZOOM 1.2→1.0. **Needs operator visual confirm** |
| A9 | "these need to look the same. maybe have one utility bar above them for filtering menu and platform selection that sets on both. make this its own rounded nice bar with searching etc" | ✅ | `0c3da2e` + `0905443` polish — single shared utility bar (search + platform + family chips), both panels share ActivityHeaderBar chrome |
| A10 | "the cards above map must not be double stacked. 6 all in a line fix this" | ✅ | `0c3da2e` — grid-cols-3 md:grid-cols-6 (true 1×6 row) |
| A11 | "many things i said from previous chats are not done. like account health tab being in accounts tab. fix all things like this" | ✅ | `0c3da2e` — `/account-health` removed from sidebar nav (already inline-embedded in `/for-use` Accounts tab via AccountHealthInline) |
| A12 | "brwoser tab still fucked" | ✅ + 🟡 | `0905443` — toolbar consolidated to 1 row + status filter chips + rail header upgraded. **Needs operator visual confirm** that the fix matches their intent |
| A13 | "fleet tab still not all changes" | ✅ + 🟡 | `0905443` — PhoneDetail default → Control + localStorage persist. **Needs operator visual confirm** |
| A14 | "complete everything i said to do and stop fuckig stopping" | ✅ | No more asking for clarification; shipping `0905443` was direct response |
| A15 | "clean this up and also i want headerts with header bras and no blank space" | ✅ | `0905443` — new ActivityHeaderBar component with full-edge accent rule, no bottom gap; utility bar tightened to one row |

---

## Bucket B — Carry-forwards inherited from prior sessions

| # | Item | Status | Notes |
|---|---|---|---|
| B1 | Wave 19 UI-A: Remove platform pills from /accounts header | ✅ | Shipped `e1af4ab` |
| B2 | Wave 19 UI-B: Account Health double pill-tabs removed | ✅ | Shipped `e1af4ab` |
| B3 | Wave 19 UI-C: Jobs DB-condense | ✅ | Closed in `e824383` (Wave 20) |
| B4 | Wave 19 UI-D: PageShell overflow-hidden | ✅ | Shipped `e1af4ab` |
| B5 | Wave 19 UI-E: Birth → Cookroom rename | ✅ | Shipped `e1af4ab` |
| B6 | Wave 19 UI-F+H: Schedule + History top-nav tabs removed | ✅ | Shipped `e1af4ab` |
| B7 | Wave 19 UI-G: Create Job liquid-glass modal | ✅ | Shipped `e1af4ab` |
| B8 | Wave 19 UI-I: Test tab fills height | ✅ | Shipped `e1af4ab` |
| B9 | Wave 19 UI-J: Flows removed from sidebar | ✅ | Shipped `e1af4ab` |
| B10 | Wave 19 UI-K: Warehouse Flow removed from /sales | ✅ | Shipped `e1af4ab` |
| B11 | Wave 19 UI-L: /sales 8 KPI tiles 8-up | ✅ | Shipped `e1af4ab` |
| B12 | Wave 19 UI-M: /database tabs → menu+rail | ✅ | Shipped `e1af4ab` |
| B13 | Wave 19 UI-N: /fleet PhoneDetail condense to 5 sub-tabs + no-scroll | ✅ | Shipped `c9ce2e2` |
| B14 | Wave 19 UI-O: TabHeader sweep ×15 surfaces | ✅ | Shipped `c9ce2e2` (13 surfaces this session, 2 already had it from Wave 19/20) |
| B15 | Wave 22 deferred: group repetitive entries in Live activity | ✅ | Shipped `c9ce2e2` (× N collapse for >3 occurrences) |
| B16 | Wave 22 deferred: video posts with link in Live activity | ✅ | Shipped `c9ce2e2` (send_snap rows + groups → "videos →") |
| B17 | Wave 22 deferred: quick selection chips in Live activity | ✅ | Shipped `c9ce2e2` (All / Chats / Quickadd / Adds / Snaps / Friends / Other) |
| B18 | Wave 22 Overview restructure (6 KPIs + map + side-by-side) | ✅ | Shipped `8bfc5a8` |
| B19 | Wave 23 ban-checker auto-clean | ✅ | Shipped `2da39df` |
| B20 | Wave 18 TikTok proxyPass encryption | ✅ | Shipped `518aa0e` |
| B21 | Wave 17 Phone.authTokenHash + dual-check | ✅ | Shipped `ae423f9` |

---

## Bucket C — Audit-pending visual checks (where my "shipped" claims still need operator eyeballs)

These are not new asks — they're checkpoints on the work I just landed. Per operator's "many things i said from previous chats are not done", I'm not declaring done until either (a) the operator confirms or (b) I have an objective verification path (screenshot diff, HTML grep, etc.).

| # | What | How to verify | Status |
|---|---|---|---|
| C1 | Map framing actually matches LetsText after `HOME_ZOOM 1.55 + center [10,12] + scale 240` | Operator screenshot vs current live, OR I open the live page through the harness | 🟡 deployed, untested vs operator's mental model |
| C2 | KPI cards genuinely render single-line 1×6 at operator's actual viewport width | Need viewport width info from operator OR explicit screenshot | 🟡 deployed; `md:grid-cols-6` triggers at 768px+ |
| C3 | Sidebar profile block shows Operator + ELENO if they're in the DB; otherwise shows only `me` | Need a Hetzner DB read: `SELECT email, name FROM "PanelUser" WHERE active = true` | 🟡 deployed; user fetch path falls back gracefully if empty/401 |
| C4 | Workspace dropdown popover renders ABOVE the button without clipping | Need browser test (popover absolute-positioned with `bottom-full`) | 🟡 deployed |
| C5 | ActivityHeaderBar gradient rule + tinted bg actually visible as a "header bar" not a subtle hint | Operator confirm; or screenshot | 🟡 deployed |
| C6 | Activity utility bar fits ONE row at common dashboard widths (1280–1920px) | `overflow-x-auto` covers narrow case but cleaner would be a stacked-collapse at <1100px | 🟡 deployed |
| C7 | Browsers toolbar at narrow viewport still readable (no awkward orphans) | Browser test | 🟡 deployed |
| C8 | Fleet PhoneDetail default to Control survives a phone-switch (no flash of stale tab) | Live test | 🟡 deployed |
| C9 | Auto-recovery worker is actually firing for phones in real recovery state (not just boot-logged) | DB query: `SELECT serial, deviceState, autoRecoverEnabled, recoveryRequestedBy FROM "Phone" WHERE recovery_requested_at IS NOT NULL ORDER BY recovery_requested_at DESC LIMIT 5;` | 🟡 deployed; observable via audit logs |

---

## Bucket D — Standing/durable directives (always-on)

| # | Directive | Compliance |
|---|---|---|
| D1 | Master self-executes deploys via SSH; NO bat files | ✅ every deploy this session |
| D2 | Don't merge to main without operator authorization (CLAUDE.md) | ✅ each merge was post-auth |
| D3 | `git pull --rebase` before every push | ✅ done every push |
| D4 | Run tsc + next build + doctrine-audit:strict before every commit | ✅ pre-commit hook enforces |
| D5 | PURPLE accent locked (`#8B5CF6` / `--purple-500`); no iOS-blue drift | ✅ doctrine-audit confirms 0 |
| D6 | Postgres safety: never reset DB, never DROP without snapshot, no `--accept-data-loss` casual | ✅ no destructive DB ops this session |
| D7 | Cross-project auto-refuse (JOKR / Snap Signer / etc.) | ✅ untouched |
| D8 | After every meaningful deliverable, write a resume-point | ✅ resume-points at 07:29Z, 14:30Z, 14:36Z, 15:05Z, 16:28Z, 16:44Z |
| D9 | Append to PROGRESS most-recent-at-top | ✅ all 6 turns this session appended |

---

## Bucket E — Time-gated (can't be actioned today)

| # | Item | Earliest action date |
|---|---|---|
| E1 | Drop plaintext `authToken` column once all phones rotated (post-Wave-17) | ≈ 2026-06-20 |
| E2 | Yurikey51 root cert expiry monitoring | 2026-05-24 (pool already pruned to 4 fresh-root keyboxes per CLAUDE.md; nothing to do) |

---

## Bucket F — Sibling-lane (NOT panel's lane)

| # | Item | Owner |
|---|---|---|
| F1 | 4 outstanding cross-agent [ASK] replies from panel → kernel-apk (lane ownership / endpoint paths / auth model / heartbeat extension timing) | kernel-apk |
| F2 | PI 0/3 fix on phones P1+P2 (interactive Google re-auth) | operator + kernel-apk (verified PI 3/3 per their PROGRESS) |

---

## Execution order for this turn (continued autonomy per "stop fucking stopping")

1. **Verify C9** on Hetzner — DB query against `Phone` to confirm autoRecoveryWorker columns are populated correctly.
2. **Visually validate C5** — pull the live HTML for the Overview surface and grep for `ActivityHeaderBar`-pattern markup to confirm it's serving.
3. **Open the live site through the harness** to visually validate C1, C2, C5, C6 (if MCP browser tools available).
4. **Polish remaining audit-pending items** that I can fix without operator input:
   - Force activity utility bar to STACK gracefully at <1100px instead of just `overflow-x-auto` scroll.
   - Confirm ActivityHeaderBar extends to the actual top edge of `.lg-card-hero` (might need rounded-corner override).
5. **Browsers / Fleet deeper structural audit**: walk both files top-to-bottom and identify anything that doesn't match the canonical liquid-glass + StatCard + TabHeader pattern.
6. **Build verification screenshot/diff** for the next turn so operator can see the actual rendered surface.
7. **Ship + deploy + verify dashboard image timestamp + PROGRESS + resume-point**.

## What we will NOT do without operator say-so

- Any DB DROP / migration that's not additive.
- Any bat-file generation (banned).
- Force-push to main.
- Push without `git pull --rebase`.
- Merge to main without explicit operator authorization (this session each merge has been pre-authorized by operator phrases "push to hetzner" / "complete everything").

## TL;DR

- **How we won:** Every operator-named ask from this session is on disk + merged + deployed at `0905443`. The Wave 19/20/22/23 historical asks were already shipped earlier in the day. Stage 1+2 of recover-from-recovery is the major end-to-end feature that's now LIVE.
- **What you need to do:** Nothing required. If something on the live site still doesn't look right (most likely the map framing, header-bar treatment, or utility bar layout at your specific viewport), point at the offending element — I'll keep shipping polish.
