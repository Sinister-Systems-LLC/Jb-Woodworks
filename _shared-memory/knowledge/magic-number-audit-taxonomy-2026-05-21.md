# Magic-Number Audit Taxonomy (Kernel APK doctrine, 2026-05-21)

> **Author:** kernel-apk (Claude agent, 2026-05-21)
> **Status:** doctrine — added after v0.97.4 magic-number sweep returned 4-of-4 false positives
> **Composes with:** speculation-as-empirical-anti-pattern, real-data-fallback-pattern (QueueTab.kt:109 + CreatorTab.kt:147 reference impls)

## Problem

Magic-number audits that grep numeric literals without semantic distinction over-flag legitimate UX/system calibration values as if they were display-ETA candidates needing real-data fallback. The v0.97.4 audit (Explore-track-C output from 2026-05-21T15:25Z session) carry-forwarded 4 candidates: Step02_SignUp Y%/8s, QueueExecutor 540s, RootTab 15s, ConnectionTab 1.5s. On per-file inspection ALL FOUR turned out to be non-replaceable categories. Doctrine captures the categorization so future audits self-classify.

## Taxonomy

Every numeric literal in app source falls into one of:

| Category | Real-data-fallback applies? | Example | Reasoning |
|---|---|---|---|
| **Display ETA** | ✅ YES | QueueTab.kt "75s/iter" pre-v0.97.3 → `livePlannedSec = currentSpoofSteps.sumOf{expectedSeconds}` | Operator sees the value; reality should drive the display |
| **Polling interval** | ❌ NO | RootTab.kt `delay(15_000L)` for RootInfoProbe refresh | Cadence is operator-tuned trade-off (too-fast wastes resources, too-slow misses drift) |
| **Circuit-breaker timeout** | ❌ NO | QueueExecutor.kt `PER_ACCOUNT_TIMEOUT_MS = 540_000L` | Must cover worst-case slow-tail; observed-avg underestimates and risks premature abort |
| **UI debounce** | ❌ NO | ConnectionTab.kt `delay(1500)` after PING button | Prevents user double-click; ergonomic constant |
| **Touch coordinate** | ❌ NO | Step02_SignUp.kt `(sh * 0.73).toInt()` Y-fallback | Screen-relative calibration; observed-avg doesn't apply to spatial coords |
| **DOM-wait deadline** | ❌ NO | Step02_SignUp.kt `8000` ms bottommost-button poll budget | Give-up-and-fall-back-to-X budget; not a display value |
| **Typography** | ❌ NO | `letterSpacing = 1.5.sp` | Style; numeric coincidence |
| **Algorithm tuning constant** | ❌ NO | Hash table size, retry exponent, etc. | Empirical correctness threshold |
| **Protocol field** | ❌ NO | HTTP timeout, packet size, MTU | External-system contract |

## Audit checklist (use this BEFORE flagging)

For each numeric literal candidate, answer:

1. **Is the value rendered to UI as a number/duration the operator reads?** If NO → not a display-ETA candidate. Skip.
2. **Is there per-iter telemetry that would produce a meaningful average?** If NO (e.g. polling cadence has no "observed" counterpart) → skip.
3. **Would observed-avg underestimate the safe value?** Timeouts must cover slow-tail; if YES → skip.
4. **Is it a UX ergonomic constant?** (debounce / button-cooldown / animation) → skip.
5. **Is it a touch coord / screen-relative ratio?** → skip.
6. **Is it typography / spacing?** → skip.

Only candidates surviving all 6 are real-data-fallback eligible. The QueueTab.kt:109 (75s/iter) + CreatorTab.kt:147 (300s) reference impls are the canonical replacement pattern: **observed-avg → live-planned-sum → last-resort-hardcoded → hide-when-unknown**.

## Anti-patterns

1. **Grep `[0-9]+L` and pipe to "fix"** — produces 4/4 false positives like this session
2. **Apply real-data-fallback to a timeout** — narrows safety margin; risks production aborts
3. **Apply real-data-fallback to a poll interval** — meaningless (no telemetry to average)
4. **Replace touch coords with averages** — averages don't apply to spatial positions
5. **Wrap typography in observed-avg fallback** — categorically wrong
6. **Audit numeric literals without reading surrounding context** — the comment 5 lines up usually explains why the value was chosen

## Empirical instance this turn

Session 2026-05-21T16:1xZ tasks 3-6 (Step02_SignUp, QueueExecutor, RootTab, ConnectionTab) all skipped on inspection. Task status updates document the per-file finding. The audit-track-C output that surfaced these was generated WITHOUT semantic classification; this doctrine entry codifies the missing classification step so future Explore-track-N "magic number" passes self-filter.

## TL;DR

- **How we won:** Surfaced 4-of-4 false positives in carry-forward magic-number audit; codified taxonomy distinguishing display-ETA (real-data-fallback OK) from 8 other non-replaceable categories.
- **What you need to do:** Future audits read this taxonomy first; only flag display-ETA candidates surviving the 6-question checklist.
