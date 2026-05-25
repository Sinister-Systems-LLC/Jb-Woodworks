<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->
<!-- SANDBOX-ALERT v1 -->
> **Sandbox handling.** Standing-rule doctrine; no runtime ops.

> **Author:** kernel-apk (Claude agent, 2026-05-21T20:0xZ)

# Audit-pass IS output — counter to "audits must find bugs to be productive"

**Slug:** audit-pass-is-output-2026-05-21
**Status:** standing-rule (codified from empirical session 2026-05-21)
**Tags:** doctrine, standing-rule, audit, brain-hygiene, anti-pattern, false-positive-prevention, speculation-as-empirical-sibling, audit-output, no-fix-required, productivity-bias

## Problem

When an agent runs an audit and finds no bugs, there's a productivity bias to either:

1. Manufacture a "finding" to feel productive (introduces real risk via speculative changes)
2. Skip the audit-pass-confirmation step and move on without documenting (loses the verification value)
3. Re-audit the same surface looking harder (wastes cycles + may produce false positives)

Empirical instance: 2026-05-21 session ran 4 audits in lane (ShellRunner API-split, 3-layer SIM-clobber wire-up, PanelPusher offline-resilience, QueueExecutor failure-cap). ALL 4 returned PASS with no source fix needed. The instinct to "find SOMETHING to ship" was present but resisted; instead each PASS was documented in PROGRESS + task description.

The doctrine: a verified-correct audit IS output. The verification has fleet value even when no source edit follows.

## What an audit-pass produces

| Output | Value |
|---|---|
| **Verified-correct status** | Future agents can read PROGRESS + skip re-auditing the same surface |
| **Codified invariants** | The audit task description names what was verified, so the invariant is searchable |
| **Brain entry refinement** | If the audit uncovered subtler nuances (e.g. v0.96.77 runSu/runSuFresh split), the brain entry gets corrected — net output |
| **Anti-regression baseline** | Next time someone touches the surface, the audit-pass record is the regression-detector |
| **Operator confidence** | "I checked X and Y — they're solid" is a real session deliverable |

## When to declare audit-PASS vs continue digging

PASS when:
- Every audit question has an answered "verified-correct" outcome
- Edge cases are accounted for (foreign-app reads, cell-down resilience, failure-streaks, etc.)
- Empirical evidence supports correctness (e.g. 38 populated stash dirs verified the inotify+cp pattern)
- Speculation-as-empirical isn't tempting (per the sibling brain entry)

KEEP DIGGING when:
- The audit only touched one path and the surface has multiple paths
- Empirical evidence is missing (you read the code but didn't trace data through it)
- The surface had a known prior bug class and you didn't check for regression

DON'T MANUFACTURE FINDINGS when:
- You can't find anything but feel pressure to ship a fix
- The surface looks "too clean to be real" (often is, especially after recent refactor)
- The audit is the FIFTH on the same surface (move on)

## The 4-audit example this session (anchors)

1. **ShellRunner runSu/runSuFresh API split** — PASS. Documented in `ksu-susfs-app-mount-namespace-isolation-2026-05-20.md` correction. Brain entry's prior advice (over-broad `grep "runSu" | grep -v "-M"`) was the actual finding — corrected, not new code.

2. **3-layer SIM-clobber prevention wire-up** — PASS. Verified profile.h:33 → main.c:169 → telephony_hook.c:175 → SpooferConfigPoller.kt:73-81 → SpooferAssetLoader.kt steps 5+6. All 4 ctl0 keys map to dispatcher entries. No fix needed; the wire-up is correct.

3. **PanelPusher offline-resilience** — PASS. DNS-fail 60s backoff + drainPendingPushes + 429 handling + UnknownHostException explicit handling all present. Cell-down → quiet queue → drain on recovery.

4. **QueueExecutor failure-streak cap** — PASS. No built-in auto-cap by deliberate design (operator-paced manual pause). Adding auto-cap would regress transient-blip scenarios.

Each PASS is captured in PROGRESS + task descriptions. Next agent auditing the same surface can read the PASS record and skip re-doing work.

## Anti-patterns

1. **Manufacture a finding to feel productive** — introduces regressions
2. **Skip the PASS documentation** — wastes the audit's downstream value
3. **Re-audit the same surface** without new evidence — burns cycles
4. **Hedge PASS with "probably fine"** — either it's verified or it's not; if hedge, dig more
5. **Claim PASS without paste-evidence** — per speculation-as-empirical doctrine, evidence must be inline
6. **Audit-shame** ("I should have found something") — productive sessions can be entirely audit-PASS

## Sister entries

- `speculation-as-empirical-anti-pattern-2026-05-20` — the discipline that lets audit-PASS be honest output (don't manufacture findings)
- `magic-number-audit-taxonomy-2026-05-21` — sister kernel-apk audit pattern; the 4-of-4 false positives there were ANOTHER instance of audit-output-without-code-change (the brain entry IS the output)
- `operator-paced-outage-discipline-2026-05-21` — audit-PASS is canonical productive work during outage windows when source ships are gated

## Composes with

- No-stop contract (audit-PASS counts as "I worked on it")
- Brain-hygiene (the documented PASS is what compounds in `_INDEX.md`)
- Canonical-19 KEEP-WORKING-UNTIL-DONE — audit-PASS is a legitimate "done" state

## Discoveries (append-only)

### 2026-05-21T20:0xZ by kernel-apk

First codification. Empirical anchor: 4 audit passes this session all returned PASS; documented in PROGRESS 19:15Z entry + per-task descriptions. The temptation to manufacture a "finding" was felt and resisted (especially when reading runSu callers — easy to flag plain-runSu as "missing -M" but the API split makes that wrong). The brain entry correction itself (over-broad audit query → correct API-level discipline) WAS the output.

## TL;DR

- **How we won:** 4 audits PASS, 0 code edits, brain entries refined for net knowledge gain. Documented each PASS in PROGRESS + task description so next agent can skip re-audit.
- **What you need to do:** When your audit returns "looks correct," document the PASS + the verification points. Don't manufacture findings. The audit-PASS IS the output.

### 2026-05-24T20:04Z by kernel-apk (refresh — v0.97.50 verification)

Re-verified all 4 audit domains hold at v0.97.50 (production tip per brain staleness audit 2026-05-24): ShellRunner API split unchanged; 3-layer SIM-clobber prevention still wired (v0.97.3-v0.97.4 ship intact); PanelPusher offline-resilience intact (no v0.97.x ship has touched it); QueueExecutor failure-cap stable. No regressions across the 4 PASS surfaces. Doctrine remains operationally current.

This refresh entry IS itself an instance of audit-pass-is-output: 0 source edits, 4 domains re-verified, the recorded PASS is the artifact. Composes with kernel-apk brain staleness audit (`_shared-memory/plans/kernel-apk-adb-view-system-2026-05-24/brain-staleness-audit-2026-05-24.md`) which flagged this entry as REFRESH CANDIDATE; the refresh discharges that flag.
