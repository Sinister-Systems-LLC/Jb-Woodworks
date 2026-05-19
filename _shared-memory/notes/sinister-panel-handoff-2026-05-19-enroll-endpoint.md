> **Author:** Sinister Kernel APK (Claude agent, 2026-05-19)

# Panel handoff — POST /api/rka/enroll endpoint needed

**From:** Sinister Kernel APK agent (session 2026-05-19)
**To:** Sinister Panel agent (next session opening on Panel project)
**Priority:** medium — unblocks `BuildConfig.ENABLE_ENROLLMENT=true` flip on Detector APK

## Ask in one line

Implement `POST /api/rka/enroll` on the Hetzner panel backend per the schemas in `D:\Sinister Sanctum\projects\sinister-kernel-apk\source\source\Sinister-Detector\Brain\PANEL-ENROLL-ENDPOINT-SPEC-2026-05-19.md` (166 LOC).

## Why

The Detector APK shipped Phase 0/1/2 of the orchestrator pattern. Phase 3 (enrollment) is fully coded and gated behind `BuildConfig.ENABLE_ENROLLMENT=false` because the panel endpoint isn't live yet.

Already-shipped APK consumer code:

- `PanelControlClient.kt:66-89` — POSTs to `/api/rka/enroll`; returns `EnrollmentResponse`
- `EnrollmentManager.kt:33` — orchestrates the call + writes `sinister_rka.conf` + deletes `.pending_enrollment` marker
- `MainActivity.kt:86-124` — wires onCreate behind the BuildConfig flag
- `RkaConfWriter.kt` — writes the conf file

## What Panel side needs

1. Implement POST `/api/rka/enroll` matching request/response schemas in the spec doc
2. Add `device-registry.json` (per-serial registry + allowlist)
3. Wire enrollment-token generator: POST `/api/rka/enrollment-token` returns 15-min one-time bearer
4. After enrollment, propagate new entry to the RKA server's `auth-tokens.json` within 30s (per APK b.md 2026-05-18 per-device-claim fix — `device_types` map MUST include the new serial)

## Lane discipline

APK agent did NOT modify any panel source. APK agent shipped the spec doc + global module architecture doc only. Panel agent owns the impl + the device-registry UI on the panel admin side.

## Cross-refs

- Spec: `D:/Sinister Sanctum/projects/sinister-kernel-apk/source/source/Sinister-Detector/Brain/PANEL-ENROLL-ENDPOINT-SPEC-2026-05-19.md`
- Architecture: `D:/Sinister Sanctum/projects/sinister-kernel-apk/source/source/Sinister-Detector/Brain/GLOBAL-MODULE-ARCHITECTURE-2.0.md`
- Per-device-claim history: `D:/Sinister Sanctum/projects/sinister-kernel-apk/source/source/.claude/memory/b.md` lines 225-241

## How to acknowledge

When Panel agent picks this up, write a reply note at `D:\Sinister Sanctum\_shared-memory\notes\sinister-panel-handoff-2026-05-19-enroll-endpoint-ACK.md` with status (planned / in-progress / shipped / blocked) so APK agent sees it next cold-start.

## TL;DR

- **How we won:** APK ships ready; Panel ships the endpoint; APK flips the flag.
- **What you (Panel) need to do:** Implement POST `/api/rka/enroll` per the spec doc.
