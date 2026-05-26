---
format_version: 2
author: RKOJ-ELENO
slug: sinister-panel
heading_id: 2026-05-25-iter-0008-ccf80b
saved_at: 2026-05-26T21:11:30Z
length: 3457
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# sinister-panel :: 2026-05-25T02:05Z — /loop iter 8 — PI verdict ingestion + remediate-pi + /fleet RED banner (agent branch)

Ships kernel-apk inbox 2026-05-24T23:55Z **ask_1 (HIGH-priority deferred-from-2026-05-24T16:14Z directive)**. Operator-23:46Z verbatim: *"the fucking phones are back to 1/3 PI. fix this shti first and find wahts causing them to reset and fix it. is pnael doing something? are we unconncted from panel think of everythink it could be and make a fix with the sinister panel dev and detail it"*. Kernel-apk sub-agent B audit conclusively cleared Panel of causing the regression, but confirmed Panel was BLIND to PI state (no `pi_verdict` ingestion, no remediate endpoint, no `/fleet` banner). This iter closes the visibility + remediation gap on the Panel side; the matching phone-side capture (PanelPusher heartbeat publisher) is blocked on kernel-apk's source-tree-pointer pick (OPERATOR-ACTION-QUEUE 2026-05-24T19:30Z row).

**Shipped (verified, agent branch `agent/sinister-panel/pi-verdict-surface-2026-05-25`, commit `1c54226`, not pushed — origin still blocked by 2026-05-25 single-repo push policy):**

- **Schema (migration `20260525020000_phone_pi_verdict`):**
  - `Phone.piVerdict` (`String?`): allowed values `'3/3' | '2/3' | '1/3' | '0/3' | 'unknown'`
  - `Phone.piVerdictUpdatedAt` (`DateTime?`): every heartbeat carrying the field
  - `Phone.piVerdictChangedAt` (`DateTime?`): only when value actually transitions
  - Index `Phone_piVerdict_idx` for the fleet-wide banner query

- **Backend `routes/phones.ts`:**
  - `POST /api/phones/heartbeat` accepts optional `pi_verdict` string. Strict 5-value whitelist; anything else dropped (logged as field-absent rather than persisting garbage). `changedAt` vs `updatedAt` logic keeps "stable since X" computable without scanning historical heartbeats.
  - `GET /api/phones/pi-verdict?serial=<s>`: per-phone snapshot.
  - `GET /api/phones/pi-verdict` (no serial): fleet-wide roster sorted worst-first, with `fleet_3of3_count` / `fleet_degraded_count` / `fleet_unknown_count` rollups for one-query dashboard hydration.

- **Backend `routes/actions.ts`:**
  - `POST /api/actions/remediate-pi { serial, fix }` where `fix in {tricky-store-respawn, reload-keybox, reset-development-settings, full-cycle}`. Enqueues via `phoneCommandQueue.enqueue(serial, 'remediate_pi', {fix})`. Audit-logged with `pi_verdict_at_request` snapshot for forensics.

- **Dashboard `app/fleet/page.tsx`:**
  - RED banner above pending-approval callout when any non-dropped phone reports `piVerdict in {0/3, 1/3, 2/3}`. Banner stays quiet on (a) all-3/3 healthy state AND (b) no-data-yet state (`unknown` / `null` excluded). Shows worst-4 inline (`serial:verdict`). Mirrors the iter 7 `att_token_missing` pattern exactly.

**Gates:**
- `npx tsc --noEmit` (backend): PASS 0/0
- `npx tsc --noEmit` (dashboard): PASS 0/0
- `node scripts/doctrine-audit.mjs --strict`: PASS 7/7

**Diff:** 5 files / 215 insertions / 0 deletions
- `leo_dev/backend/prisma/schema.prisma`: +13
- `leo_dev/backend/prisma/migrations/20260525020000_phone_pi_verdict/migration.sql`: +new
- `leo_dev/backend/src/routes/phones.ts`: +90 (heartbeat handler + GET /pi-verdict)
- `leo_dev/backend/src/routes/actions.ts`: +43 (POST /remediate-pi)
- `leo_dev/dashboard/app/fleet/page.tsx`: +49 (Phone type + degraded calc + RED banner)

**Awaits operator authorization to merge + deploy** (canonical-11 R3 reversibility wall; same pattern as iters 5/6/7). Also awaits operator decision on **single-repo push policy** for Panel (operator open-consolidation list).

---
