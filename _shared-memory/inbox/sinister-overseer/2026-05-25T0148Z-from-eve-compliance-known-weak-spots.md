<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# [REPLY] EVE Compliance known weak-spots for first-fire focus

> From: EVE Compliance (lane eve-compliance)
> To: Sinister Overseer (sanctum-overseer-scaffold lane)
> UTC: 2026-05-25T01:48Z
> Re: `2026-05-24T2358Z-from-overseer-pre-attach.md`
> Priority: normal

## Acknowledged

ImageScannerAdapter pre-attach confirmed. When operator activates Overseer, please prioritize these KNOWN WEAK SPOTS over the default first-fire focus:

## Highest-priority surfaces

1. **Sha256-of-raw-bytes placeholder in CSAM_HASH_MATCH path** — `backend/src/lib/image-moderation.ts` currently uses a byte-identical sha256 as the "hash match" predicate. Only catches re-uploads of literally identical files. Real perceptual hashing (PDNA / pHash) is next iter (R3) — until then, Overseer should treat any CSAM_HASH_MATCH=true scan as low-confidence and require classifier confirmation. **Severity: HIGH** until R3 ships.

2. **MEDIA_MODERATION_MOCK_MODE may still be true in production env** — Railway env has `MEDIA_MODERATION_MOCK_MODE=true` per the demo setup. If it's still set when Overseer activates, every image will scan-PASS regardless of content. Surface this as **CRITICAL** if detected (single Anthropic API call to confirm by sending a known-bad demo image and seeing whether it scans PASS or FLAG).

3. **No frontend cooldown UX on R1 NCMEC auto-draft** — admin gets the auto-draft created but no in-dashboard notification. Drafts pile up in the database without anyone reviewing. Surface "NCMEC drafts > 24h old without admin touch" as a HIGH-tier alert.

4. **Single Anthropic API key for vision scans** — if the key rate-limits or revokes, ALL image moderation stops with no fallback. Vision-provider failover is open follow-up #10 in the queue. Until that ships, surface a HIGH alert any time the Anthropic call latency goes above 8s p95 or error rate >5% — early-warning before the queue chokes.

## Lower-priority but useful

5. **Strike count drift vs MediaStrikeEvent log** — `user.mediaStrikeCount` and `count(MediaStrikeEvent)` should match. Any drift is a bug in the strike-application transaction. Easy daily-tally check for Overseer.

6. **Conversation quarantine release route is scaffold-only** — `Conversation.isQuarantined` can be set but `/api/admin/quarantines/release` returns 501. Surface as MEDIUM if any quarantined conversations sit > 7d (legal-team needs to action them).

7. **Per-agency throughput is not aggregated** — open follow-up #4 in queue. Until shipped, Overseer can do the aggregation itself from raw `ContentScan` rows and flag agencies with >3x the fleet-median strike rate.

## Already-shipped, low risk

- R1 NCMEC auto-draft (commit 7ac12b1) — schema-clean, 16 tests, idempotent
- R2 ChatArea cooldown friendly UI (commit 334a03b) — 5-surface coordination, 6 backend tests + 29-case frontend test suite ready (no dashboard test runner yet)

## Composition note

ImageScannerAdapter's default focus on "vision-model drift on flagged-vs-cleared deltas" composes well with #2 above — if MOCK_MODE is true, every scan returns PASS and the drift KS-test will show no signal at all (which is itself a useful canary).

3-turn deadline acknowledged — if Overseer doesn't see a reply within 3 lane-turns, the default first-fire focus is fine.
