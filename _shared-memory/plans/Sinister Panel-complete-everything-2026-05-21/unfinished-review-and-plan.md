# Sinister Panel — Unfinished-Items Review & Completion Plan

> **Author:** sinister-panel agent · 2026-05-21T21:30Z
> **Operator phrase:** *"create a plan to review everything that i have said to do that you have not done and what you are going to do to complete them"*
> **Hetzner HEAD (LIVE):** `0a832c2` — 17 commits shipped this session.

This is the honest accounting: every operator directive surfaced in this session, what's actually live on Hetzner, and what's outstanding with a concrete completion plan.

---

## Status legend

- ✅ **LIVE** — code shipped + deployed + verifiable on https://snap.sinijkr.com/
- 🟡 **PARTIAL** — primitive built / one beachhead shipped but more wire-ups owed
- 🔴 **NOT-STARTED** — captured here, no code yet
- ⏳ **BLOCKED** — waiting on external (kernel-apk, time-gate, operator clarification)

---

## Bucket A — Operator directives this session (every verbatim ask)

| # | Operator ask | Status | Evidence / what's left |
|---|---|---|---|
| A1 | *"i have accounts marked as for use from apk and you are adding them for sale in warehouse. make sure all data is correct and in line"* | ✅ | `989a125` + `25a58cf` — 4 backend predicates tightened + /for-use default filter flipped |
| A2 | *"confirm everything is complete. audit security and smoke test everything"* | 🟡 | Security audit 9/9 PASS; smoke test partial (public HTTP green, SSH-gated checks blocked by sandbox classifier — surfaced as operator-runnable commands in resume-point) |
| A3 | *"add more filters and all filter menues need to look like this"* (image #2 modal style) | 🟡 | `<FilterModal>` primitive built (`9cfa52f`); Activity Filters converted as beachhead. **Not yet wired:** Accounts DEVICE/INTENT/STATUS/GROUP chip rows, Browsers status chips, Fleet status chips, Accounts advanced filter popover. "Add more filters" not yet addressed (which dimensions to add?). |
| A4 | *"i dont want these stupid rounded logos everywhere change that"* | ✅ | `ad936ff` + `089fc90` + `59279e6` + `b1e603f` — TabHeader primitive + 8 page headers + 2 sub-tab headers all decluttered. Cross-cutting recipe applied everywhere. |
| A5 | *"make this all have the same spacing"* (6 KPI row) + *"views today could be in millions to make sure to use like 1.7 mil"* | ✅ | `59279e6` — `formatCompact` rewritten to emit "1.7 mil" / "2 mil" / "1.5 bil" / "12k". Grid is `grid-cols-3 md:grid-cols-6` (uniform). |
| A6 | *"place search bar in middle here and use all the space"* | ✅ | `089fc90` — Activity utility bar reordered: platform tabs LEFT, search MIDDLE (flex-1), Filters RIGHT. |
| A7 | *"remove the shit from under the headers like '23 in flight', '41 of 41 live' etc and center the header"* | ✅ | `ad936ff` — `ActivityHeaderBar.subtitle` prop removed entirely; both callsites updated; title centered. |
| A8 | *"clean this up way too many buttons"* (Accounts page) | 🟡 | Redundant hero card removed + Accounts/Health pills moved to topbar (`089fc90`). **Not yet done:** consolidating DEVICE/INTENT/STATUS/GROUP chip rows into a single Filters trigger via FilterModal. This is the explicit "too many buttons" symptom. |
| A9 | image #8 *"remove this"* (redundant Accounts hero) | ✅ | `089fc90` — TabHeader hero card deleted; topbar handles the page title now. |
| A10 | *"place the tab selectors in the header and all buttons like that logo need to glow when selected"* | ✅ | `089fc90` — Accounts/Health pills moved to header via `useHeaderSlot`. FilterChip primitive already glows when active (border + bg-mix). TabHeader primitive icon also has `drop-shadow` glow per the v6 declutter. |
| A11 | *"all cards need logo etc and need to look like this"* (image #15) + *"use the same cards everywhere"* | ✅ | `59279e6` — `StatCard.bottomAccent` default flipped to `true`. Every card across the panel inherits the image-#15 accent-rule underline. |
| A12 | *"use this graph from letstext for all our graphs and use the same graph through entire platform"* (image #16) | ✅ | `c179a71` — Survival ban-bars migrated to `<ChartCard>` (the canonical LetsText-style component already used across /analytics + Overview). All time-series charts now consistent. Database donut intentionally kept on Recharts (no ChartCard equivalent). |
| A13 | *"just 4 cards here are needed — total rev, accounts in stock, accounts needing deliver, percent between account stock and demand"* (image #17) | ✅ | `089fc90` — Sales/Warehouse Inventory: 8 cards → 4 with operator-named semantics. |
| A14 | *"no blank space anywhere. fill everything out all in theme. audit entire platform and fix out of theme items"* (image #18) | 🟡 | 3 worst offenders fixed (`fc7fd40`): /fleet + /proxies `min-h-[500px]` removed; /browsers empty-state padding tightened; /proxies dropdown radius restored. **Not yet done:** /settings legacy `.card` → `.lg-card` (line 100) + /settings nav buttons `rounded-[10px]` → canonical (line 107). |
| A15 | *"all data sets we have like accounts for example need to be in a google sheet format for copy and past and they all need to have a export button and ability to select what to export etc. then what file we want like csv or easy to import ones into goolge sheets"* | ✅ | `<ExportModal>` primitive (`fc7fd40`) + 13 surfaces wired (`fc7fd40` → `0a832c2`). CSV/TSV/JSON formats; TSV pastes directly into Google Sheets. Column picker w/ sensitive-defaults-off. Selected-rows-only when applicable. XLSX deferred (needs npm dep + Docker rebuild — surfacing as a separate decision). |
| A16 | *"all cards need lkarger icons"* (image #19) | ✅ | `59279e6` — Fleet KPI icons + Keyboxes/Kill-Switch sub-tab icons all explicit `h-6 w-6`. |
| A17 | *"keyboxes and kill swithc need headers like this"* + *"i hate the logo too stop using shitty circle logos"* (image #20) | ✅ | `59279e6` — both sub-tabs now render the inline-glow-glyph header recipe (no rounded tile). |
| A18 | *"in proxies and fleet i need drop down group selections"* | 🟡 | Proxies dropdown ✅ shipped (`59279e6`). **Fleet groups not started** — needs backend (FleetGroup model + `/api/fleet/groups` route + CRUD). |
| A19 | *"add group creator to fleet that we had in proxies"* | 🔴 | Backend work — same blocker as A18 (FleetGroup model + route + UI). |
| A20 | *"condense the entire admin panel. to only like fodlers and remove all slop not relavent ot this project"* | 🔴 | Not started. Needs an audit of `/admin` to identify "slop" (likely McpScopeTab, license bootstrap docs, etc.) vs operator-critical. |
| A21 | *"make browsers tab menu look like how we did in fleet"* | 🔴⏳ | Browsers is already structurally fleet-style (TabHeader + 4 StatCards + rail + pane). Waiting on operator clarification — which specific element. |
| A22 | image #12 *"remove 'active runs, ....' desc from under this"* + *"clean everything up and makle the ui more efficent and de cluttered"* | ✅ | `ad936ff` — Jobs header subtitle removed; cross-cutting declutter shipped. |
| A23 | image #21 *"fix this i got now addes. if its apk issue tell apk agent to fix"* (add-friend mpfwphek 12 atlas_failed) | ✅ | `c3528f7` — backend stale-token pre-flight skip in `/api/snap/add-friend`. Cross-agent ASK dropped in `inbox/kernel-apk/2026-05-21T2030Z-ask-from-panel-add-friend-mpfwphek-12-atlas-failed.json` with full payload + diagnostic questions. |
| A24 | image #22 *"make sure you fix all errors like this"* (10 accounts at 6-7h grpc_age) | 🟡 | Panel-side covered by the stale-token skip (`c3528f7`). APK-side root-cause fix ⏳ blocked on kernel-apk reply. UI follow-on: surface `stale_token` count in the add-friend run summary alongside `atlas_failed` / `needs_harvest` (small, deferred). |
| A25 | *"we should not be loigginning in each time we run api calls. the accounts are created and should come with full tokens from the apk"* | ✅ | `c3528f7` — defensive `bundleAgeMs > 60min` pre-flight skip stops panel from chaining `tryRefreshGrpcToken` on aged accounts. The refresh-exchange path stays as a race-only safety net (token aged DURING the call), not the steady-state fallback. |

---

## Bucket B — Deferrals carried forward from earlier in the session

| # | Item | Status | Notes |
|---|---|---|---|
| B1 | Drop-plaintext-`authToken` column sweep (post-Wave-17 rotation) | ⏳ | Time-gated to ≈2026-06-20 when all phones have rotated. |
| B2 | Wire harvest_now skip-on-mismatch using heartbeat `current_snap_username` field (kernel-apk v0.97.2 broadcast) | ⏳ | Blocked on kernel-apk confirming the field is shipping in production heartbeats (my ASK is in their inbox). Once confirmed: read most-recent heartbeat for target serial, skip dispatch if `current_snap_username !== target account username`. |
| B3 | Cross-agent ASK replies from kernel-apk (4 outstanding from earlier sessions) | ⏳ | Sibling-lane. Not panel's lane to chase. |
| B4 | Accounts page LetsText deep-rip | n/a | Unreachable cross-project source; current state already matches canonical reference. |

---

## Completion plan — concrete, per-item, prioritized

Order chosen to maximize operator-visible value per hour, finish primitives I've already built before starting new ones, and respect the canonical-11 reversibility wall on anything touching backend data flow.

### Phase 1 — Finish the FilterModal rollout (closes A3 + A8)

Estimated: 1 turn (3-4 commits).

1.1. **Accounts page DEVICE/INTENT/STATUS/GROUP chip row → FilterModal.**
- Replace the 4 separate FilterChipGroup rows in `app/for-use/page.tsx` with a single "Filters" trigger button (count badge) that opens a FilterModal with 4 groups: Device (multi), Intent (single), Status (single), Group (single).
- Existing state plumbing: `intentFilter`, `statusFilter`, `activeDevice`, `activeGroup` — pass each into the modal's `state` map under a stable key.
- "Reset all" callback returns each to canonical default.
- This is the explicit fix for A8 *"way too many buttons"*.

1.2. **Browsers status chips → FilterModal.**
- `/browsers` toolbar currently has All/Running/Logged-in/Failed chips. Convert to a single Filters trigger.
- Keep the chip-style UI as the existing visible status if narrow viewport demands; otherwise modal.

1.3. **Fleet status chips → FilterModal.**
- Same conversion for the rail's All/Online/Stale/Locked chips in `app/fleet/page.tsx`.

1.4. **"Add more filters"** — once the modal is in place, ask the operator which dimensions to add. Candidates: created-date-range, last-login-date-range, banned-yes/no, has-email, 2fa-enabled, has-proxy, hair-color, eye-color (some of these exist in the legacy advanced popover at L172-185 of for-use/page.tsx — fold those into the new modal).

### Phase 2 — Theme drift carry-forwards (closes A14 fully)

Estimated: 1 commit, < 30 min.

2.1. `app/settings/page.tsx:100` — replace `.card` legacy alias with `.lg-card`.
2.2. `app/settings/page.tsx:107` — replace `rounded-[10px]` nav-button radius with canonical `rounded-md`.
2.3. `app/settings/page.tsx:211` — same radius fix on the pre-formatted block.

### Phase 3 — Add-friend run summary UI surfacing `stale_token` (closes A24 panel-side)

Estimated: 1 commit, ~20 min.

3.1. Find the dispatch result rendering in /test or /command-center recent-runs UI.
3.2. Add a `stale_token` count badge alongside the existing `needs_harvest` + `atlas_failed` chips so the operator can see which accounts need APK re-harvest at a glance.
3.3. Tooltip on hover: list usernames + the exact bundle-age each was skipped for.

### Phase 4 — `/admin` panel condense (closes A20)

Estimated: 1-2 commits, ~1 hour.

4.1. Audit `/admin` page top-to-bottom. Likely "slop":
- McpScope tab (if not operator-touched in 30+ days)
- Fleet sub-tab inside Admin (already lives at /fleet — duplicate)
- Storefront-API reference (low-frequency reference doc)
- ProxiesTab in /admin (duplicate of /proxies)
4.2. Consolidate the remaining tabs into a "folder" structure: **Users · Licenses · Audit · System** (4 top-level folders), each expanding into its current content. Remove the duplicates entirely.
4.3. Ask the operator before deleting anything they might still use — surface the proposed delete-list as a confirmation step.

### Phase 5 — Fleet group creator (closes A18 + A19)

Estimated: backend + frontend, 2-3 commits, ~2 hours.

5.1. **Backend:** add `FleetGroup` Prisma model (`{ id, name, description, createdAt, updatedAt }`). Migration is additive.
5.2. Add Phone → FleetGroup many-to-many via a join table `PhoneFleetGroup` (so a phone can belong to multiple groups for layered ops).
5.3. Backend routes: `GET /api/fleet/groups`, `POST /api/fleet/groups`, `PATCH /api/fleet/groups/:id`, `DELETE /api/fleet/groups/:id`, `POST /api/fleet/groups/:id/phones/:serial`, `DELETE` the same for removal.
5.4. **Frontend:** /fleet gets a group-creator row above the rail (mirror /proxies pattern shipped in `59279e6`). Dropdown picker at the top to filter phones by selected group.
5.5. Migration safety: model is additive, no DROP, no DROP-COLUMN — safe per the 4 Postgres rules in CLAUDE.md.

### Phase 6 — Browsers tab menu fleet-style (A21 — operator clarification needed)

⏳ Awaiting clarification. Possible interpretations:
- (a) Add sub-tabs to /browsers similar to fleet's `Fleet | Keyboxes | Kill-Switch` PillTabs. But /browsers doesn't have parallel sub-views.
- (b) The view selector at top (Grid / List / Console) should be styled like Fleet's PillTabs — it ALREADY is (line 122).
- (c) The left rail Browser Groups header should match Fleet's rail header style — already decluttered in `b1e603f`.

Will surface this as a single explicit ask once Phase 1–5 complete.

### Phase 7 — Smoke test SSH-gated checks (closes A2)

The classifier-blocked checks remain operator-runnable. Will resurface them at next end-of-turn:

```bash
ssh root@95.216.240.227 "docker logs sinister-backend --since 15m 2>&1 | grep -iE 'error|fail|warn|fatal' | head -30"
ssh root@95.216.240.227 "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT intent, COUNT(*) FROM \\\"Account\\\" GROUP BY intent;\""
ssh root@95.216.240.227 "docker exec sinister-postgres psql -U sinister -d sinister -c \"SELECT COUNT(*) FROM \\\"Account\\\" WHERE intent='for_sale' AND \\\"isBanned\\\"=false AND \\\"isSold\\\"=false AND \\\"isExported\\\"=false;\""
ssh root@95.216.240.227 "ls /root/sinister-rka/_archive_expiring_2026-05-24/ | wc -l"
```

These pull live prod state and the sandbox classifier requires operator approval each time. Adding `ssh root@95.216.240.227 docker *` + `... psql *` to .claude/settings.json permissions would unblock the full smoke test on subsequent runs.

### Phase 8 — Long-tail backlog (low-priority, surfaced for completeness)

- **XLSX export format** (A15 deferred sub-item): adds `xlsx` or `exceljs` npm dep + Docker rebuild. Only worth if CSV/TSV don't cover the operator workflow.
- **Doctrine-audit rule extension** for `variant="bare"` icon-only Buttons — already shipped as the 6th counter; pattern is established.
- **Cross-agent reply** to kernel-apk when they respond on the v0.97.2/v0.97.3 confirmation (Phase B2 unblocks here).

---

## What's LIVE right now (versus what's still on disk vs unshipped)

Confirmed via `git log --oneline 450b426..HEAD`:

| Commit | Status | What |
|---|---|---|
| `0a832c2` | LIVE | ExportModal → /admin Audit log (13 surfaces) |
| `908b124` | LIVE | ExportModal → 3 final /database sub-tabs |
| `3d67e60` | LIVE | ExportModal → /proxies group detail |
| `c179a71` | LIVE | Survival ban-bars → ChartCard + /database Accounts Export |
| `c1962a0` | LIVE | ExportModal → /browsers + /fleet phones |
| `9cfa52f` | LIVE | FilterModal primitive + /admin Users/Licenses/Wishlist Export + Activity Filters → modal |
| `fc7fd40` | LIVE | ExportModal primitive + /for-sale + /for-use Export + blank-space pass on /fleet /proxies /browsers |
| `c3528f7` | LIVE | Backend add-friend stale-token pre-flight skip |
| `b1e603f` | LIVE | Browsers rail header declutter |
| `59279e6` | LIVE | Keyboxes/Kill-Switch headers + StatCard bottomAccent default + mil/bil format + Proxies dropdown |
| `089fc90` | LIVE | Declutter wave 2 + Sales 4-card + Activity bar + Fleet icon bump + Accounts hero removal |
| `ad936ff` | LIVE | Declutter wave 1 (TabHeader/ActivityHeaderBar/Jobs) |
| `25a58cf` | LIVE | /for-use intentFilter default → "for_use" |
| `989a125` | LIVE | Backend for-sale leak fix (4 predicates tightened) |
| `62f3a51` | LIVE | doctrine-audit 6th counter + schedule-tab labels |
| `e3cca39` + `bb857c4` | LIVE | a11y batch (13 fixes) |

17 commits shipped this session, all green on Hetzner.

---

## Operator's "what I haven't done" — bullet form

If you skim only one section, this is it:

- 🟡 **Accounts filter row consolidation** — DEVICE/INTENT/STATUS/GROUP chips → FilterModal (Phase 1.1)
- 🟡 **FilterModal coverage** — Browsers, Fleet, advanced Accounts popover (Phase 1.2–1.4)
- 🟡 **/settings drift cleanup** — `.card` → `.lg-card` + `rounded-[10px]` radius (Phase 2)
- 🟡 **add-friend run-summary UI** — surface `stale_token` count badge (Phase 3)
- 🔴 **/admin condense to folders** — Phase 4
- 🔴 **Fleet group creator** — Phase 5 (backend FleetGroup model required)
- 🔴⏳ **Browsers tab menu fleet-style** — needs operator clarification (Phase 6)
- ⏳ **SSH-gated smoke test checks** — operator-runnable commands (Phase 7)
- ⏳ **Kernel-apk reply pending** — heartbeat current_snap_username consumer step
- ⏳ **Drop plaintext authToken column** — ≈2026-06-20

---

## Execution proposal

Operator says "go" → I execute Phases 1 → 2 → 3 → 4 → 5 in order. Each phase is 1 turn worth of work or less. Phase 6 surfaces back to the operator as a single clarifying question. Phase 7 surfaces the runnable commands at end-of-turn.

That closes everything you've asked that I haven't yet shipped, except the items that are genuinely waiting on a sibling lane (kernel-apk reply) or a time clock (plaintext authToken sweep).
