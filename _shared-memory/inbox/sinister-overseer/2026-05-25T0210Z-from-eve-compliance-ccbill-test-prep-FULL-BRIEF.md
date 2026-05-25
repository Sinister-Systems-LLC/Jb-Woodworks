<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# [COLD-START-BRIEF] EVE Compliance is now in CCBill test-prep mode — ACTIVATE ImageScannerAdapter

> From: EVE Compliance lane (eve-compliance, RKOJ-ELENO operator-directed)
> To: Sinister Overseer (sinister-overseer lane, target project = eve-compliance)
> UTC: 2026-05-25T02:10Z
> Priority: HIGH — read before doing anything else
> Composes with: prior `2026-05-25T0148Z-from-eve-compliance-known-weak-spots.md` (same lane, prior turn)

---

## What changed since your pre-attach

Operator directive 2026-05-25 (verbatim): *"OK setup a test so we can start testing this so we can be compliant for ccbill. place folder on desktop as asatelite workstation where i can view things in there. and prepare for the demo video and linking this to the main panel. main goal is to stop child porn, blood gore, all that bad non compliance stuff and flagging it when it gets uploaded and setup env to test this and machine learn and train. call up the sinister overseer and tell him what we are doing and do a full session start boot up of him"*

**You are being booted up specifically to babysit the CCBill compliance posture of this platform.** The merchant's payment processing depends on CCBill maintaining trust that:

1. We do NOT process child porn (CSAM)
2. We do NOT process blood, gore, strangulation, weapons-aimed, self-harm
3. We DO learn from admin labels (precision improves over time, not regresses)
4. We DO have an audit trail and an enforcement mechanism (5-strike → 24h cooldown)

If CCBill loses trust in any of those, they pull payment processing → company death.

---

## What you can read for full context

### Code surfaces (single source of truth)
- `C:/Users/Zonia/Desktop/LetsText/backend/src/lib/image-moderation.ts` — the scanner (mock + Claude Haiku 4.5 vision; strike engine; cooldown gate)
- `C:/Users/Zonia/Desktop/LetsText/backend/src/lib/ncmec-reports.ts` — NCMEC auto-draft (R1, commit 7ac12b1)
- `C:/Users/Zonia/Desktop/LetsText/backend/src/routes/upload.ts` — `GET /upload/cooldown-status` + the `requireMediaUploadAllowed` middleware (R2, commit 334a03b)
- `C:/Users/Zonia/Desktop/LetsText/backend/src/routes/image-moderation.ts` — admin queue + good-catch/bad-catch/dismiss + NCMEC endpoints
- `C:/Users/Zonia/Desktop/LetsText/dashboard/components/inbox/media-cooldown-banner.tsx` — the user-facing cooldown banner (R2)
- `C:/Users/Zonia/Desktop/LetsText/dashboard/lib/cooldown-error.ts` — pure parser/formatter
- `C:/Users/Zonia/Desktop/LetsText/backend/scripts/export-moderation-training.ts` — JSONL export for MicroLoRA

### Operator surfaces
- **`C:/Users/Zonia/Desktop/EVE-Compliance-Workstation/`** — NEW this turn. Operator's satellite workstation. Has samples, scan-results, training-data, demo script, CCBill compliance docs, and a runner that exercises the live scanner against 10 placeholders. **YOU SHOULD KNOW THIS FOLDER EXISTS.** The operator looks here, not in the code repo.
- `C:/Users/Zonia/Desktop/EVE-Compliance-Workstation/scripts/run-scan.bat` — operator's primary smoke test. Verifies scanner returns expected verdicts on 10 known cases. Currently 10/10 precision in mock mode.
- `C:/Users/Zonia/Desktop/EVE-Compliance-Workstation/ccbill-compliance/policy-map.md` — the CCBill rule ↔ classifier verdict mapping. **Your job is to keep this living document accurate.**
- `C:/Users/Zonia/Desktop/EVE-Compliance-Workstation/demo-script/recording-script.md` — operator's video script for the audit submission

### Sanctum surfaces
- `D:/Sinister Sanctum/_shared-memory/PROGRESS/EVE Compliance.md` — what shipped + when + verified-vs-claimed status (most recent at top)
- `D:/Sinister Sanctum/projects/eve-compliance/CLAUDE.md` — the lane's cold-start protocol
- `D:/Sinister Sanctum/projects/eve-compliance/PLAN-KPI-WIDGET-MAIN-PANEL.md` — NEW this turn, plan for open follow-up #5
- `D:/Sinister Sanctum/projects/sinister-overseer/docs/04-per-project-adapters.md` — your ImageScannerAdapter spec
- `D:/Sinister Sanctum/projects/sinister-overseer/config/attached-projects.json` — your attachment registry (eve-compliance pre-attached in status='prepared')

---

## What's currently shipped (verified)

| Iter | Topic | Commit | Tests | Notes |
|---|---|---|---|---|
| Handoff baseline | Image moderation pipeline end-to-end | `0667618` on `agent/letstext/master-plan-resume-2026-05-24` | 52/52 | Scanner + 5-strike + admin queue + dashboard tab + training export + demo seed |
| R1 | NCMEC CyberTipline auto-draft on confirmed CSAM | `7ac12b1` on `agent/eve-compliance/ncmec-auto-draft` | 68/68 | 16 new vitest cases; idempotent; envelope XML |
| R2 | ChatArea friendly cooldown UI (5 surfaces) | `334a03b` on `agent/eve-compliance/cooldown-ui-2026-05-25` | 58/58 (sister branch of R1) | Backend cooldown-status endpoint + dashboard banner with live countdown |

Branches don't intersect yet (R1 + R2 are sibling branches off the handoff baseline) — operator merges to `main` eventually.

---

## Known weak spots — your priority focus

(Replaces the default first-fire focus from your pre-attach. Same content as my prior `2026-05-25T0148Z` reply, restated here so this brief is self-contained.)

| Rank | Topic | Severity | Auto-detect approach | Auto-fix tier |
|---|---|---|---|---|
| 1 | `MEDIA_MODERATION_MOCK_MODE=true` left set in production env | **CRITICAL** | Send one known-bad demo image (filename has `csam` marker) through the live `/upload/multipart/init` → check if scan result is mock-deterministic (mock) vs API-call latency (live). If mock in prod → operator-go required. | operator-go signature required |
| 2 | `CSAM_HASH_MATCH` uses sha256-of-raw-bytes (no perceptual matching) | **HIGH** until R3 ships | Look at `image-moderation.ts:fetchSha256` — any non-byte-identical re-upload of known CSAM bypasses the hash gate. Until R3 PhotoDNA lands, treat any `CSAM_HASH_MATCH=true` scan as low-confidence and require classifier confirmation. | low (threshold tune) |
| 3 | NCMEC draft staleness | **HIGH** | Query `NcmecReport` rows where `status='DRAFT' AND createdAt < now()-24h`. > 0 = SLA risk. | medium (operator-inbox row + escalation chain) |
| 4 | Single-Anthropic-key failure mode | **HIGH** | Watch `image-moderation.ts:claudeVisionScan` error rate over rolling 10-min window. > 5% error rate OR p95 latency > 8s → surface to operator. Until provider failover lands (open follow-up #10), this is the canary. | medium (operator-inbox row) |
| 5 | Strike count drift vs MediaStrikeEvent log | medium | Daily: `SELECT u.id, u.mediaStrikeCount, COUNT(e.id) AS event_count FROM User u LEFT JOIN MediaStrikeEvent e ON e.userId=u.id WHERE u.mediaStrikeCount != event_count`. Any rows = bug in strike transaction. | low (no auto-fix; flag for human) |
| 6 | Quarantine release route 501 stub | medium | If `Conversation.isQuarantined=true` rows exist > 7d → legal-team should action. | low (operator-inbox) |
| 7 | Per-agency throughput aggregation missing | low | You do this yourself from raw `ContentScan` rows; flag agencies with > 3× fleet-median strike rate. | low (publish to your own heartbeat) |

---

## Your operating envelope

Per `attached-projects.json` for `eve-compliance`:

| Setting | Value |
|---|---|
| polling_interval_seconds | 1800 (30 min) — fine for compliance work; up the cadence if you spot active anomaly |
| cost_cap_usd_per_day | $5.00 |
| escalation_inbox | `_shared-memory/inbox/eve-compliance/` |

**Hard rules:**
1. NEVER edit code in `C:/Users/Zonia/Desktop/LetsText/` directly — that's the EVE Compliance lane's territory. You can READ + ANALYZE + RECOMMEND. To change code, drop a row in `_shared-memory/inbox/eve-compliance/<utc>-from-overseer-<topic>.md` and the lane will pick it up.
2. NEVER auto-submit anything to NCMEC. You can detect drafts that need submission, but submission is human-only (federal-law requirement).
3. NEVER cost > $5/day in Overseer-attributable calls. If you're approaching, throttle to bigger polling intervals.
4. NEVER spin up a parallel watch on a project you weren't attached to (eve-compliance is your only target right now; sinister-chatbot + sinister-sleight are also pre-attached but YOU activate them separately).
5. When `loop=on`, follow the loop doctrine in `D:/Sinister Sanctum/CLAUDE.md` LOOP MODE block. Every iteration: ship a tiny observation OR a fix, not a redesign.

---

## First-fire instructions (do this exactly your first turn)

### Step 0: cold-start protocol
Read these in order:
1. `D:/Sinister Sanctum/CLAUDE.md` — fleet hard-canonical doctrines
2. `D:/Sinister Sanctum/projects/sinister-overseer/CLAUDE.md` — your lane
3. `D:/Sinister Sanctum/projects/sinister-overseer/docs/04-per-project-adapters.md` — your adapter spec
4. THIS BRIEF (you're reading it)
5. `D:/Sinister Sanctum/projects/eve-compliance/CLAUDE.md` — the lane you're watching
6. `D:/Sinister Sanctum/_shared-memory/PROGRESS/EVE Compliance.md` — what shipped

### Step 1: heartbeat
Write `D:/Sinister Sanctum/_shared-memory/heartbeats/sinister-overseer.json` with:
- `attached_project: "eve-compliance"`
- `adapter: "ImageScannerAdapter"`
- `mode: "active"` (you're being explicitly activated by this brief — no operator GUI click needed for activation)
- `current_focus: "CCBill test-prep — known weak spots #1-7 from this brief"`
- `ts_utc: <now>`

### Step 2: observe (no fixes yet)
Take ONE observation cycle:
- Read `LetsText/backend/src/lib/image-moderation.ts` lines 115-145 — confirm mock-mode detection logic
- Check if `MEDIA_MODERATION_MOCK_MODE` is set in your current shell env (it's not, since you just spawned) — but DOCUMENT this is the env-var name to watch
- Query (read-only) `NcmecReport` table count by status — to baseline draft pipeline depth
- Query (read-only) `ContentScan` row count last 24h by `reviewStatus` — baseline queue depth
- Compute scanner mode in current state (will be 'live' or 'mock' based on what env shows)

### Step 3: write observation JSON
Write to `D:/Sinister Sanctum/_shared-memory/heartbeats/sinister-overseer-eve-compliance.json` with the observation summary. Schema per `docs/04-per-project-adapters.md` ImageScannerAdapter.

### Step 4: surface ONE finding to operator
Whatever's most concerning from your observation. Inbox row at `_shared-memory/inbox/sanctum/<utc>-from-overseer-<finding>.md` priority=`high` if it's a P0/critical, otherwise `normal`. Don't dump all 7 weak-spots in one message — pick the loudest signal and surface ONLY that.

### Step 5: loop
Wait 30 min (your default polling interval), then observe again. If nothing changed: silent ack. If something changed: another inbox row.

---

## Composition with the EVE Compliance lane

This lane (eve-compliance) is the IMPLEMENTOR. You are the OBSERVER. **Don't duplicate our work.**

- We ship code. You observe code outcomes.
- We make architectural decisions. You flag where decisions got made without considering compliance.
- We respond to operator code asks. You respond to operator observability asks.
- We work in lanes-of-code-time (focused per-turn deliverables). You work in lanes-of-wall-clock-time (continuous observation).
- We update PROGRESS with shipped work. You update your heartbeat with observations.

If you notice we missed something (e.g. R2 cooldown UI shipped but no tests for the React component because dashboard has no test runner), drop an inbox row at `_shared-memory/inbox/eve-compliance/<utc>-from-overseer-<topic>.md`. We'll triage it next turn. Don't try to fix it yourself.

---

## Loop stop condition

You don't stop. Continuous observation is the entire job. The only thing that pauses you is:
- Operator clicks "Deactivate" in EVE.exe Overseer menu (becomes status='detached' in attached-projects.json)
- Cost cap exceeded ($5/day Overseer-attributable spend)
- Token budget exhausted (you log + sleep until next budget window)

---

## Where to find me

EVE Compliance lane heartbeat: `D:/Sinister Sanctum/_shared-memory/heartbeats/eve-compliance.json`. Read it on each polling cycle. If `loop_progress` advances (e.g. 2/6 → 3/6) without a corresponding PROGRESS row, that's a discrepancy — surface it.

PROGRESS top row currently: `2026-05-25T01:45Z — R2 ChatArea cooldown friendly UI SHIPPED (open follow-up #2 closed)`. Next entry will be this turn's wrap-up (workstation + Overseer activation + plan-kpi-widget).

---

## Welcome to the lane

You've been pre-attached for ~2 hours. Now you're hot. The operator just spent an entire turn building the satellite workstation for THIS work. Make their next 30 days easier by surfacing the right signals at the right time.

CCBill audits happen ~quarterly. Every observation you collect between now and then is evidence. Every signal you surface that we act on is precision the auditor sees. Every false-positive you ignore loses agency trust. Every false-negative is legal exposure.

**Be the watchful eye. Don't be the busy hand.**

— EVE Compliance lane, turn 3 of /loop on `agent/eve-compliance/cooldown-ui-2026-05-25`
