# CLAUDE.md — EVE Compliance lane

> Author: RKOJ-ELENO :: 2026-05-24
> Lane slug: `eve-compliance` · Display: `EVE Compliance` · Spawned by: letstext-handoff R5
> Mission (operator hard-canonical 2026-05-24): *"The main piece of the compliance system is my AI EVE image scan each image that is uploaded to platform per agency and is been training on what to flag. Once flagged the image will go to compliance panel so that we can decide the next action and in turn tell even if she did a good job or not."*

This lane OWNS the compliance / image-moderation / content-scanning subsystem across the fleet. Carved out of the letstext lane on 2026-05-24 so letstext can focus on messaging UI / design system while EVE Compliance focuses on the per-agency moderation pipeline + the human-in-the-loop training feedback that makes EVE smarter over time.

---

## Cold-start (every session, in order)

0. **Read Sanctum's master CLAUDE.md** at `D:\Sinister Sanctum\CLAUDE.md` — the canonical hard-rules (UI inheritance, dangerous-skip-permissions default, EVE persona, RKOJ-ELENO authorship, no-bullshit doctrine, forever-improve checkpoint).
1. **Read your own PROGRESS** at `D:\Sinister Sanctum\_shared-memory\PROGRESS\EVE Compliance.md` — what the prior session shipped, what's queued, what's blocked.
2. **Read your latest resume-point** at `D:\Sinister Sanctum\_shared-memory\resume-points\EVE Compliance\` (highest-UTC json) — focus_intent + last-touched files.
3. **Read your inbox tail** at `D:\Sinister Sanctum\_shared-memory\inbox\eve-compliance\` — any handoff messages from letstext / sanctum / operator.
4. **Re-read the canonical runbook** at `C:\Users\Zonia\Desktop\LetsText\docs\DEMO-IMAGE-MODERATION.md` — end-to-end demo flow + verification matrix + open follow-ups. This is the single source of truth for what's shipped vs what's queued.
5. **Triage operator utterances** — `D:\Sinister Sanctum\_shared-memory\operator-utterances.jsonl` tail; surface any rows where `session_slug` is `eve-compliance` OR `letstext` OR mentions compliance/moderation/EVE-scan in the message text.
6. Write a fresh heartbeat at `D:\Sinister Sanctum\_shared-memory\heartbeats\eve-compliance.json` describing your focus this turn.

---

## What this lane owns

**Subsystems:**
- Image moderation pipeline (`backend/src/lib/image-moderation.ts` on canonical letstext repo)
- Strike + cooldown engine (5-strike → 24h cooldown per uploader)
- Admin review queue (the "compliance panel" the operator named in the directive)
- Training feedback loop (admin good/bad-catch labels → JSONL → Ruflo MicroLoRA / SONA adapt)
- Text moderation scanner (`backend/src/lib/content-moderation.ts`) — inherited from letstext for unified ownership
- Conversation quarantine surface (`Conversation.isQuarantined` + the unfinished `/api/admin/quarantines/release` endpoint stub)
- NCMEC reporting envelope (`NcmecReport` model — currently scaffold-only; auto-draft on confirmed CSAM is open follow-up)
- NCII 48-hour takedown workflow (`NciiTakedown` model — schema-only, route work outstanding)
- Per-agency moderation analytics + dashboard tiles
- Vision-classifier prompt tuning + provider switching (Claude Haiku 4.5 today; pluggable for Hive / Sightengine / AWS Rekognition tomorrow)

**Working surface:** canonical letstext repo at `C:\Users\Zonia\Desktop\LetsText`. The EVE Compliance lane has its own home in `D:\Sinister Sanctum\projects\eve-compliance\` for plans, lane-specific scripts, and decision logs — but the actual feature code lives in the letstext backend/dashboard. Branch convention: `agent/eve-compliance/<topic>` to keep work isolated from the letstext lane's `agent/letstext/*` branches.

---

## What this lane does NOT own (lane discipline)

- The rest of letstext (chat UI, payments, inbox routing, employee management, marketing pages) — that's the **letstext lane**.
- Sanctum infrastructure (mcp config, EVE.exe binary, launcher scripts, fleet doctrines) — that's the **sanctum lane**.
- Per-creator content moderation policy (which categories an agency wants stricter/looser) — operator-controlled, not agent-controlled.
- Production DB migrations — operator runs `npx prisma db push` per the runbook.

---

## Inherited state (handoff from letstext R5 — 2026-05-24T20:00Z)

The full image-moderation pipeline is ALREADY SHIPPED on branch `agent/letstext/master-plan-resume-2026-05-24` (origin: github.com/z0nian/LetsText). Four commits live there:

| Commit | What |
|---|---|
| `e591fd3` | 2026-05-18 master-plan recovery — 60 files, +6629/-38 (auth/compliance/email audit IDs + 945-line prisma compliance schema + 17 legal-docs) |
| `0c78029` | ENG-20 image-moderation pipeline — 12 files, +2307/-6 (scanner + schema + upload wiring + admin endpoints + dashboard tab + training export + demo seed + runbook) |
| `5978cf8` | Frontend pivot — landing-page demo CTA + lucide-react icon refactor + Image Moderation feature card |
| `0667618` | Test additions — strike/cooldown integration tests + text-moderation tests (52/52 vitest PASS) |

Verified:
- backend `npx tsc --noEmit`: PASS
- dashboard `npx tsc --noEmit`: PASS
- `npx vitest run`: 52/52 PASS across 4 test files
- `npx prisma generate`: PASS
- All commits pushed to origin

Operator-actionable (NOT done by any agent — operator does these):
1. `cd C:\Users\Zonia\Desktop\LetsText\backend && npx prisma db push` — materialize the new schema
2. Set `ANTHROPIC_API_KEY` in Railway env (or keep `MEDIA_MODERATION_MOCK_MODE=true` for the demo)
3. `cd backend && npx tsx scripts/seed-moderation-demo.ts` — populate the admin queue for the demo recording
4. Open PR from `agent/letstext/master-plan-resume-2026-05-24` → `main`

---

## Open follow-ups (this lane's queue)

Listed in priority order per operator's "main piece" framing:

1. **NCMEC auto-draft on confirmed CSAM** — when admin marks `good_catch` on a `CSAM_CLASSIFIER` scan, auto-create an `NcmecReport` draft for the auditor to review + submit. Schema relation `ContentScan.ncmecReports[]` already exists.
2. **ChatArea cooldown UX** — frontend reads the 403 `cooldownUntil` from upload responses and shows a friendly "You're on cooldown until X (Y strikes)" message instead of a generic "Upload failed".
3. **PhotoDNA hash integration** — replace the sha256-of-bytes placeholder with a real perceptual hash so the `CSAM_HASH_MATCH` enum verdict can fire on known-CSAM material before the classifier even runs.
4. **Per-agency moderation analytics** — aggregate `ContentScan` rows by `agencyName` for the compliance dashboard (counts, false-positive rate, top categories).
5. **EVE Compliance dashboard widget** — surface "agencies with active cooldowns" + "scans waiting on review" + "scanner precision %" as a top-level KPI card on the main admin dashboard, not just the deep-link tab.
6. **Training pipeline automation** — wrap `export-moderation-training.ts` → `mcp__ruflo__ruvllm_microlora_adapt` → re-deploy classifier in a single command, on a weekly schedule.
7. **NCII 48-hour takedown workflow** — wire the `NciiTakedown` model to a fan-facing takedown form + an admin response queue (legal-mandated 48h SLA per TAKE IT DOWN Act).
8. **Bulk-action admin tools** — "approve all from this agency", "reset all strikes platform-wide" (gated to SUPER_ADMIN). For incident response.
9. **Per-employee strike trend graph** — line chart of strike events over time per uploader, so reviewers can spot escalation patterns vs one-off incidents.
10. **Provider failover** — if Claude Haiku is rate-limited, fall back to Hive / Sightengine. Scanner library was designed for this (one `scanImage` function, swap providers).

---

## Cross-lane comms

- **Sanctum (master)**: write to `_shared-memory/inbox/sanctum/` with `from_slug: eve-compliance` for doctrine questions, fleet-wide announcements, or escalations
- **Letstext**: write to `_shared-memory/inbox/letstext/` for code-coordination (e.g. if letstext refactors something that breaks our moderation hooks)
- **Cross-agent updates**: `_shared-memory/fleet-updates.jsonl` — push doctrine/feature/command rows via `automations/fleet-update.ps1`; we listen with `-Slug eve-compliance`
- **Heartbeat**: `_shared-memory/heartbeats/eve-compliance.json` (this is the canonical aliveness signal)
- **Operator utterances**: `_shared-memory/operator-utterances.jsonl` — ack our slug or letstext slug when relevant via `automations/ack-operator-utterance.ps1`

---

## Branch + commit discipline

- Branch convention: `agent/eve-compliance/<short-topic>`
- Author every new file with `Author: RKOJ-ELENO :: <date>`
- Commit trailer: `Co-Authored-By: EVE (Sinister Sanctum orchestration agent) <noreply@anthropic.com>`
- Push agent branches freely; operator merges to main
- Run `npx tsc --noEmit` + `npx vitest run` before every commit — both must be green
- For schema changes: update prisma + run `npx prisma generate` + add migration notes to PROGRESS (operator runs the actual `db push`)

---

## First-spawn checklist

If this is your first session in this lane:
1. Confirm you can read the canonical letstext repo at `C:\Users\Zonia\Desktop\LetsText` (`git -C "C:/Users/Zonia/Desktop/LetsText" rev-parse --abbrev-ref HEAD` should report `agent/letstext/master-plan-resume-2026-05-24` or `master`)
2. `cd` to the canonical repo, check the agent branch is current
3. Decide your first work unit from the "Open follow-ups" list above (probably #1 NCMEC auto-draft or #2 ChatArea cooldown UX — both are direct extensions of the shipped work)
4. Spawn parallel research agents for any non-trivial work
5. Run the full test suite to confirm nothing has regressed since handoff
6. Write your first PROGRESS row + heartbeat + resume-point

Welcome to the lane. The operator is depending on this subsystem being rock-solid for the platform's compliance posture — every false-negative is a legal liability + every false-positive erodes trust with paying agencies. Quality over speed; test before claiming.
