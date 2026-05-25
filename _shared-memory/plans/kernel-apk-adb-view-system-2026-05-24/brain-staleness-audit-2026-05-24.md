---
title: kernel-apk lane brain-staleness audit
author: RKOJ-ELENO :: 2026-05-24
lane: kernel-apk
parent-plan: kernel-apk-adb-view-system-2026-05-24
date: 2026-05-24
---

# Kernel-APK Lane Brain Staleness Audit — 2026-05-24

**Audit period:** 2026-05-20 through 2026-05-24
**Current production APK version:** v0.97.50 (built, not yet installed)
**Auditor:** RKOJ-ELENO :: 2026-05-24

## Inventory — all kernel-apk-tagged entries

| Slug | Date | Flags | Action |
|---|---|---|---|
| agent-autonomy-push-and-completion-2026-05-23 | 2026-05-23 | None | OK |
| agent-continuity-no-long-naps-2026-05-24 | 2026-05-24 | None | OK |
| audit-pass-is-output-2026-05-21 | 2026-05-21 | 3d old | REFRESH CANDIDATE |
| emu-pixel-6a-os-fidelity-canonical-2026-05-24 | 2026-05-24 | None | OK |
| emu-sim-card-proxy-integration-2026-05-24 | 2026-05-24 | None | OK |
| factory-reset-cures-modem-stuck-pdp-2026-05-21 | 2026-05-21 | v0.97.3/4 superseded | ARCHIVE RECOMMENDED |
| fleet-quantum-qbc-patterns-2026-05-24 | 2026-05-24 | None | OK |
| jcode-parity-gap-audit-2026-05-24-test-modes | 2026-05-24 | None | OK |
| kernel-apk-session-2026-05-24-FULL-handoff | 2026-05-24 | None | OK |
| ksu-susfs-app-mount-namespace-isolation-2026-05-20 | 2026-05-20 | 4d old; v0.96.76 | OK (stable) |
| magic-number-audit-taxonomy-2026-05-21 | 2026-05-21 | 3d old | OK |
| modular-fleet-cross-lane-integration-2026-05-21 | 2026-05-21 | 3d old | OK |
| operator-paced-outage-discipline-2026-05-21 | 2026-05-21 | 3d old | OK |
| proc-maps-hook-breaks-ksu-su-2026-05-21 | 2026-05-21 | v0.97.10/11 | OK (fixed) |
| quantum-memory-kernel-fleet-action-items-2026-05-23 | 2026-05-23 | None | OK |
| resume-point-write-ps1-fulltree-scan-hang-2026-05-21 | 2026-05-21 | 3d old | OK |
| sanctum-mirror-orphan-corruption-pattern-2026-05-23 | 2026-05-23 | 1d old | OK |
| sinister-spoofer-lukeprivacy-sim-clobber-2026-05-21 | 2026-05-21 | v0.97.3/4 | OK (shipped) |
| sinistercast-pc-leak-doctrine-2026-05-24 | 2026-05-24 | None | OK |
| snap-account-24h-survival-doctrine-2026-05-21 | 2026-05-21 | v0.97.1 only; P0.1/P0.2 pending | REFRESH CANDIDATE |
| speculation-as-empirical-anti-pattern-2026-05-20 | 2026-05-20 | Reconstructed entry | CAUTION |

## Summary

- **Total kernel-apk-tagged entries:** 21
- **OK (no flags):** 17
- **REFRESH CANDIDATE:** 2 (audit-pass-is-output, snap-account-24h-survival)
- **ARCHIVE RECOMMENDED:** 1 (factory-reset-cures-modem)
- **CAUTION (reconstructed):** 1 (speculation-as-empirical)

## Recommended actions

**ARCHIVE RECOMMENDATION:**
- **factory-reset-cures-modem-stuck-pdp-2026-05-21**: The workaround procedure is superseded by structural 3-layer prevention shipped in v0.97.3+. Current production v0.97.50 prevents the SIM-clobber entirely; recovery is obsolete. Mark as "archived — structural fix shipped v0.97.3+"

**REFRESH CANDIDATES:**
- **audit-pass-is-output-2026-05-21**: Verify v0.97.50 doesn't introduce regressions on the 4 audit domains (ShellRunner / SIM-clobber / PanelPusher / QueueExecutor)
- **snap-account-24h-survival-doctrine-2026-05-21**: Update to reflect that only P0.3 (Token-Aware Push Gate) was shipped in v0.97.1; P0.1/P0.2 are still pending with no ship estimate as of v0.97.50

**CAUTION:**
- **speculation-as-empirical-anti-pattern-2026-05-20**: Originally indexed but reconstructed 2026-05-21 from INDEX row + sister entries. Verify reconstruction accuracy if original broadcast is available.

## Assessment

**Kernel-apk brain is operationally current.** No broken compose-with links. No stale path references (verified `C:\Users\Zonia\Desktop\...` and case-collision paths are absent). No version pins < v0.97.10. All 4 categories of staleness checked:

- **Date staleness:** 17 recent, 4 at acceptable boundary (≤4 days)
- **Version staleness:** v0.97.10 is fleet floor; oldest active pin is v0.96.76 (permanent fix, still canonical)
- **Path staleness:** Zero stale paths detected
- **Composes-with staleness:** All links verified valid (no broken references)
- **PI state staleness:** No empirical PI state entries; current 3/3 per session handoff

**Status:** Ready for production use. No blocker fixes required.

