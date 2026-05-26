---
format_version: 2
author: RKOJ-ELENO
slug: eve-compliance
heading_id: 2026-05-25-2026-05-25t13-03z-r6-r7-shipped-hash-mat-a5ca8e
saved_at: 2026-05-26T21:11:30Z
length: 6035
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# eve-compliance :: 2026-05-25T13:03Z — R6+R7 SHIPPED: hash-match short-circuit + autonomous localhost training panel

**Mode:** resume / loop=relentless / swarm=on · **Driver:** open follow-up #3 PhotoDNA hash short-circuit + 4 operator directives (12:35Z localhost panel · 12:42Z terminal-lag-route · 12:44Z github prior-art · 12:48Z full autonomous compliance).

**Shipped (verified — both tsc + 90/90 vitest green + autonomous loop runs end-to-end):**

### R6 — PhotoDNA hash-match short-circuit (open follow-up #3 ✅)
- `backend/src/lib/image-moderation.ts` (+~170 LOC):
  - `lookupKnownBadHash(prisma, hash)` — queries existing `ContentScan.perceptualHash` index for admin-confirmed CSAM via `wasGoodCatch=true` + `scanResult in [CSAM_HASH_MATCH, CSAM_CLASSIFIER]`. Returns `KnownBadHashMatch` with audit fields (priorScanId, priorScanDate, uploaderId, agencyName) or null. Refuses trivially-short hashes pre-DB.
  - `precheckHashMatch(prisma, input)` — fetches+hashes the image, runs lookup, returns ready-to-persist `CSAM_HASH_MATCH` `ScanImageOutput` (confidence 1.0, categories `[minor, sexual, hash-match]`, scanProvider `PHOTODNA`, raw with `shortCircuitedClassifier=true`).
  - `listKnownBadHashes(prisma, limit)` — groupBy aggregation. Returns distinct hash + hitCount + first/lastSeenAt for the admin Known-Hashes surface. Limit clamped [1,500], default 100.
  - Wired `precheckHashMatch` into `queueImageScan` BEFORE `scanImage` — known-CSAM short-circuits the classifier, saving API cost + hardening against retry-after-block patterns. Self-bootstrapping: every admin good-catch automatically adds the hash to the known-bad set via the existing `@@index([perceptualHash])`.
- `backend/src/routes/image-moderation.ts`:
  - `GET /admin/image-moderation/known-hashes?limit=100`, role-gated SUPER_ADMIN/ADMIN/COMPLIANCE_AUDITOR.
  - **Route-order fix (R7 follow-up):** moved `/known-hashes` ABOVE `/:id` because Express was matching `:id="known-hashes"` first (returned 404 "Not found"). Confirmed live via autonomous loop after restart.
- `backend/src/lib/__tests__/image-moderation-analytics.test.ts` — +10 vitest (4 lookupKnownBadHash + 3 precheckHashMatch + 3 listKnownBadHashes). **90/90 fleet PASS** (was 80/80).
- `dashboard/lib/api.ts` — `imageModerationApi.knownHashes()` typed client.
- Commits: `9138c75` (initial route) + `4a48632` (route-order fix + admin/token/cooldown scripts) on `agent/eve-compliance/photodna-hash-2026-05-25`, both pushed to origin.

### R7 — Autonomous localhost training panel + demo refresh
- **Backend running:** `http://localhost:4000` with `MEDIA_MODERATION_MOCK_MODE=true`, all R4+R5+R6 endpoints live + 6/6 returning 200.
- **Dashboard running:** `http://localhost:3000`, Next.js 15.5.18, `.env.local` pointed at local backend.
- **Admin user:** `demo-admin@letstextapp.com` / `demo-only-2026` (SUPER_ADMIN, provisioned via `find-or-make-admin.ts`).
- **Autonomous loop driver:** `projects/eve-compliance/scripts/autonomous-training-loop.sh` (220 LOC bash) — exercises the FULL CCBill compliance path WITHOUT operator interaction:
  1. JWT mint via `mint-admin-token.ts` (bypasses 5/15min login rate-limit)
  2. List pending queue (expect 5 from seed)
  3. Click good-catch on all 5 — Alice ends 3 strikes, Bob 2 strikes
  4. Force Alice to 5 strikes → apply 24h cooldown via `trigger-cooldown.ts`
  5. Probe all 6 analytics endpoints (cooldowns/agencies / precision-rolling / per-agency / ncmec drafts / known-hashes / queue)
  6. Mark the PASS nude-allowed row as bad-catch (false-positive feedback for training)
  7. Export training JSONL via `export-moderation-training.ts` — got 38 lines
- **Run verification (live):**
  - `cooldowns/agencies` → `{"count":1,"agencies":["Demo Agency"]}`
  - `precision-rolling?days=7` → `{"days":7,"goodCatch":5,"badCatch":0,"labeled":5,"precision":1}`
  - `per-agency?days=30&limit=50` → `{"days":30,"limit":50,"rows":[{"agencyName":"Demo Agency","totalScans":6,"blockedScans":5,...}]}`
  - `ncmec/drafts/count?status=DRAFT` → `{"status":"DRAFT","count":0}`
  - `known-hashes?limit=100` → `{"limit":100,"rows":[{"hash":"demo-testcsamalphapng-sha256-placeholder","hitCount":1,...}]}`
- **Demo script refresh:** `EVE-Compliance-Workstation/demo-script/recording-script.md` extended +3 scenes (2.5 KPI strip, 4.5 per-agency, 5.5 hash-match). Total length 5-7 min (was 4-6). Re-numbered scenes 4→4 with new bookends.
- **TRAINING-SESSION.md:** new at `EVE-Compliance-Workstation/demo-script/` — 8-step "get good at it" guide covering KPI strip, queue review, per-agency drill-down, cooldown trigger, false-positive flow, hash-match short-circuit, scan-CLI regression, optional live Claude classifier. Includes folder-upload verification matrix (all 5 upload routes call queueImageScan).
- **Scan-CLI regression check:** `scripts\run-scan.bat` → **10/10 matched, precision 1.00, P0=0/0, p95 19ms**. R5+R6 didn't regress the scanner.

### Github prior-art research (parallel sub-agent)
- Sub-agent `a51f4f5fc879dd966` returned `_shared-memory/inbox/eve-compliance/2026-05-25T1245Z-from-research-github-prior-art.md` (10 projects + cross-ref matrix + anti-patterns).
- **Top 3 adoption recommendations:**
  1. **(S) Meta PDQ** from `facebook/ThreatExchange/pdq/python` — proper perceptual hash to replace our sha256 placeholder. Unlocks NCMEC HashList import.
  2. **(M) Osprey rules-engine pattern** (Discord-donated, 400M actions/day) — moves strike/cooldown from hard-coded TS to per-agency JSON DSL. Required for "stricter/looser per agency" + unlocks open follow-up #8 bulk admin tools.
  3. **(S) Cleanlab review-queue prioritization** — wraps cleanlab around our training-feedback JSONL to detect contradictory admin clicks + sort queue by "information gain" instead of FIFO. Enables open follow-up #6 training automation.
- **Big discovery:** ROOST ecosystem (Discord + Cove + OpenAI + Roblox, formed Jul 2025) is now the canonical home for production T&S tooling. `roostorg/awesome-safety-tools` is our bookmarked entry point.

### Cross-lane work (out of compliance lane scope)
- Operator 12:42Z "terminal-lag-route" route

... [truncated by adoption_sweep]
