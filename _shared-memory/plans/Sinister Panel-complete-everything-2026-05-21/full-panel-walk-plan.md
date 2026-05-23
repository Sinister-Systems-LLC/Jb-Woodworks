# Sinister Panel — Full Panel Walk + Security Audit + Remaining Backlog Plan

> **Author:** sinister-panel agent · 2026-05-21 evening
> **Operator phrase:** *"do full panel walk grep sweep. create a plan to do this and security audit and everything else you have not done"*
> **Hetzner HEAD (LIVE):** `5112780` — 30+ commits shipped this session.
> **Doctrine-audit baseline:** `0/0/0/0/0/0` (all 6 counters clean).

Synthesized from 3 parallel Explore agents:
- **Drift agent** — full-codebase grep sweep for rounded-tile icons, iOS-blue drift, hard-coded purple hex, backdrop-blur recipe drift, subtitle leakage.
- **Security agent** — re-audit of every commit shipped this session vs the previous 9/9 PASS baseline.
- **Surface agent** — every route inventoried for Export/Filter modal coverage + StatCard sprawl + dead code.

---

## Section 1 — UI drift sweep (drift-agent finding)

**Net: 4 violations found across the entire panel.** This is remarkable cleanliness given the volume of refactoring. Doctrine-audit's 6 counters still clean.

| # | File:line | Drift pattern | Canonical fix |
|---|---|---|---|
| D1 | `components/middle-sidebar.tsx:53` | `w-7 h-7 rounded-lg bg-[var(--surface-3)]` around icon | Replace with inline-glow recipe |
| D2 | `components/middle-sidebar.tsx:105` | `w-8 h-8 rounded-lg bg-[var(--surface-3)]` around icon | Same |
| D3 | `components/middle-sidebar.tsx:139` | Same as D2 | Same |
| D4 | `components/layout/top-bar.tsx:291` | Hamburger button uses `rounded-xl`; canonical is `rounded-full` per operator's "not square" directive | One-character class swap |

**Zero violations of:**
- iOS-blue (only intentional TikTok brand mark)
- Hard-coded `#8B5CF6` (purple-500 indirection working)
- Backdrop-blur paired with `bg-surface-*` (all on `.lg-card` recipe)
- Radius override on `.lg-card`/`.lg-card-hero`/`.lg-rail`
- Subtitle leakage under headers
- Bespoke `<button>` outside allowlist

---

## Section 2 — Security audit (security-agent finding)

**Status: 7/7 PASS — zero showstoppers — DEPLOY SAFE.**

| # | Area | Verdict |
|---|---|---|
| S1 | Recent commits (path traversal, XSS, secrets) — `c3528f7` / `989a125` / `fc7fd40` / `9cfa52f` / `a62e212` / `c3fcb20` / `5112780` | ✅ PASS — username sourced from Prisma not user input; ExportModal escaping correct; sensitive defaults `defaultOn: false` verified |
| S2 | AUTH/AUTHZ baseline (middleware order, DISABLE_AUTH fail-closed) | ✅ PASS |
| S3 | Secrets exposure (apiKey once-only, ENCRYPTION_KEY not logged, timing-safe compares) | ✅ PASS |
| S4 | Postgres safety (no new migrations this session, no DROP, no --accept-data-loss) | ✅ PASS |
| S5 | CORS fail-closed in prod | ✅ PASS |
| S6 | Rate limiting (1000/min global + 5/5min auth preserved) | ✅ PASS |
| S7 | CSP allows inline styles (which the declutter recipe uses) | ✅ PASS |

**No new attack surface introduced by the session's 30+ commits.** No nice-to-fix items.

---

## Section 3 — Surface gaps (surface-agent finding)

Routes / components that escaped this session's refactor wave:

### 3A — Missing ExportModal wires

| Surface | Tables that should export | Effort |
|---|---|---|
| `/master-audit` | Audit log table | 1 commit, ~15 min |
| `/videos` | Video metadata | 1 commit, ~15 min |
| `/tiktok` | Currently uses bespoke client-side CSV — migrate to ExportModal primitive | 1 commit, ~25 min |
| `/rka` | Keybox table | 1 commit, ~15 min |

### 3B — Missing FilterModal wires (where inline filter chips still live)

| Surface | What needs consolidation | Effort |
|---|---|---|
| `/proxies` | All / Available / Assigned chip groups in /proxies + Assignments tabs | 1 commit, ~20 min |
| `/for-sale` | Status filter chips on Inventory | 1 commit, ~15 min |
| `/database` | Bans / Scraped / Imported tabs all have inline chip filters | 1 commit, ~30 min |
| `/automation` Active tab | Status chips | 1 commit, ~15 min |

### 3C — StatCard sprawl (visual overload)

| Surface | Card count | Recommendation |
|---|---|---|
| `/automation` Control Center | 18 cards | Group by phase/status into 4-6 buckets |
| `/fleet` (combined sub-tabs) | 13 cards | Group online/busy/offline tiers |
| `/progress` | 11 cards | Consolidate by phase |
| `/admin` (across folders) | 11 cards (3 folders × ~4 each) | Acceptable post-Phase-4 restructure |

**StatCard consolidation is a UX call** — not auto-mergeable without operator's per-bucket grouping intent.

### 3D — Dead code / stale tabs

**None found.** All "Coming soon" / TODO comments are legitimate technical placeholders.

---

## Section 4 — Backlog from operator's session-wide requests

Carried forward from earlier in the session:

| # | Item | Status | Reason |
|---|---|---|---|
| B1 | Editable display name + custom avatar | 🔴 NOT STARTED | Needs backend `PATCH /api/admin/me` endpoint + upload primitive |
| B2 | FilterModal text-input group support (Hair/Eye color filters) | 🔴 NOT STARTED | Extend FilterModal with `mode: "text"` group type |
| B3 | Drop plaintext `authToken` column post Wave-17 rotation | ⏳ TIME-GATED | Earliest ~2026-06-20 |
| B4 | Kernel-apk reply to my ASK (`inbox/kernel-apk/2026-05-21T2030Z-...`) | ⏳ SIBLING-LANE | Once they confirm v0.97.2 `current_snap_username` heartbeat field shipping, panel wires the skip-on-mismatch consumer |
| B5 | Account-pane / groups-tab / loops-tab / schedule-tab — pre-session components, verify not orphaned | 🟡 NEEDS-VERIFY | Surface agent flagged as untouched but couldn't confirm orphan status |

---

## Section 5 — Completion plan (operator-actionable order)

### Phase A — UI drift fixes (immediate, 1 commit, ~10 min)
- D1 / D2 / D3: middle-sidebar.tsx 3 icon containers → canonical recipe.
- D4: top-bar.tsx hamburger `rounded-xl` → `rounded-full`.

### Phase B — Export wires (4 commits, ~75 min)
- /master-audit · /videos · /rka · /tiktok migration.

### Phase C — FilterModal wires (4 commits, ~80 min)
- /proxies · /for-sale · /database · /automation Active tab.

### Phase D — KPI consolidation (UX decision, 2-3 commits, deferred to operator-confirm)
- /automation 18-card grouping
- /fleet 13-card grouping
- /progress 11-card grouping

### Phase E — Carry-forwards (deferred, larger scope)
- B1 (name+avatar): backend PATCH + upload primitive + edit modal — 1 turn
- B2 (FilterModal text inputs): extend primitive + wire Hair/Eye — 1 turn
- B5 (orphan verify): walk the 4 components, surface findings

### Phase F — Operator-gated (no agent action)
- B3 (authToken sweep) — time-gated
- B4 (kernel-apk reply) — sibling-lane

---

## Section 6 — Execution start NOW

The autonomy contract says "stop asking — complete it all". Going:
1. **NOW**: Phase A (drift fixes).
2. **Then**: Phase B (Export wires).
3. **Then**: Phase C (FilterModal wires).
4. Phase D surfaces back to operator (UX call) — won't auto-merge KPIs without their direction.

Each commit pushes + deploys in the same step so the operator sees progress at the same cadence as my work.

This file is the source of truth; updates happen as commits land. The session's progress so far is in `unfinished-review-and-plan.md` in this directory.
