<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
<!-- SANDBOX-ALERT v1 -->
> **Sandbox handling.** Standing-rule doctrine; no runtime ops.

> **Author:** kernel-apk (Claude agent, 2026-05-21T20:0xZ)

# Operator-paced outage discipline — when one input is gated, complete cell-independent work without blocking

**Slug:** operator-paced-outage-discipline-2026-05-21
**Status:** standing-rule (codified from empirical session 2026-05-21)
**Tags:** doctrine, standing-rule, outage-handling, cell-down, network-failure, autonomy, no-stop-contract, operator-gated, audit-pivot, kernel-apk, fleet-wide

## Problem

When operator declares an external input gated ("cell service is down, I'll tell you when it's back" / "panel is rebuilding, hold X" / "Yurikey is in transit, defer Y"), the agent has two failure modes to avoid:

1. **Block on the gate** — sit idle waiting for operator's "back now" message. Violates no-stop-contract + wastes a productive window that often spans hours.
2. **Speculatively retry the gated op** — hammer the gate endpoint, burn battery / phone bandwidth / panel CPU, leak diagnostic noise to logcat. Wastes operator's outage-recovery work.

Empirical instance: 2026-05-21 session, operator at ~16:10Z verbatim: *"complete all you can without cell service on the phone. i will let you know once its back on."* Session ran for 3+ hours productively under the gate.

## The discipline

When operator gates an input, partition work into:

| Category | Action |
|---|---|
| **Depends on the gated input** | Defer to carry-forward; surface in end-of-turn + resume-point |
| **Independent of the gate** | Continue immediately, full speed |
| **Adjacent to the gate** | Soft-touch only; verify code paths handle the gate gracefully (e.g. cell-down resilience audit), do NOT exercise the gate |

## What counts as "cell-independent" work (canonical examples for kernel-apk lane)

- Source code edits (any tab/file)
- Build + parse + type-check (`./gradlew assembleDebug`)
- Brain-entry writes / doctrine refinements
- Cross-agent communication (drop inbox messages; replies are async by design)
- Audit passes against the codebase (read-only)
- Commit + push (push is operator-gated separately per CLAUDE.md rule 9, but commit on per-agent branch is free)
- Tool scaffolding + bug-fixing (e.g. Sanctum-side tools in `tools/`)
- Resume-point + PROGRESS writes
- Pre-flighting things operator will eventually need (e.g. Install-Task.ps1 syntax + dry-run)

## What counts as "cell-dependent" (defer)

- `adb -s <phone> install <apk>` (USB-attached phones over cell-down state may still work; depends on the specific outage class — verify USB attachment first)
- Anything that POSTs to panel via cell network (push, harvest_now, heartbeat receipt — though SEND will succeed, server-side processing during outage may be degraded)
- Empirical verification of phone-side fixes (need phones reachable to verify logcat tail)
- Cross-phone shell exec via `adb -s` if phones are not USB-attached (cell-WiFi only setups)

## Adjacent — soft-touch

- Audit panel-resilience code paths (read source, verify exception handling) — DO this
- Speculatively fire panel-side endpoint to "see if it's back" — DO NOT (operator will tell you)
- Read on-disk state of cell-dependent siblings (panel heartbeats, panel PROGRESS) — DO this
- Spin up panel sibling agent to "check if they're OK" — DO NOT during operator-gated outage; trust operator

## Loop structure under outage

```
while outage:
    TaskList → pick next cell-independent row
    Execute
    Commit + resume-point
    Refresh heartbeat (don't claim "back online" prematurely)
    If TaskList empties:
        Brain-capture a pattern from this session
        OR audit/refine existing kernel-apk doctrine
        OR pre-flight an operator-gated tool's scaffold
        OR cross-lane inbox notify (async)
    Never: ping operator with "are we back?" / "should I continue?"
```

## Sister discipline — heartbeat hygiene

During outages, refresh your own heartbeat (`_shared-memory/heartbeats/<slug>.json`) so other lanes know you're alive + productively working. Don't claim production-ready state if it's not; reflect actual lane state (e.g. "v0.97.4 shipped + cell-down audit pass + 4 brain entries this session").

## Anti-patterns

1. **"Are we back?" pings** — operator will tell you; asking is noise.
2. **Speculative retry of the gated op** — wastes bandwidth + battery + operator-recovery cycles.
3. **Sit-idle until ping** — violates no-stop-contract; productive window is finite.
4. **Pivot to entirely-different-lane work** — stays in lane; cross-lane work needs CONTRACT 5 coordination.
5. **Surface as "blocked"** — frames the wait as a block. Frame as a pivot: "X is gated, continuing on Y/Z/W."
6. **Claim "back online" in heartbeat prematurely** — never claim state you haven't verified.

## Composes with

- `no-stop-contract` (CONTRACT 2) — operator-gated outages are valid pivots, not stop conditions
- `forever-expanding-modular-architecture-doctrine` — modular lanes can keep working when one is gated
- `audit-pass-is-output-2026-05-21` — sister doctrine; audits returning PASS are still productive output under outage windows
- `verify-head-before-commit-multi-agent` — commits during outage windows still need the verify ritual
- `apk-classifier-aup-doctrine` — different gating type; both surfaced as carry-forward, neither blocks

## Discoveries (append-only)

### 2026-05-21T20:0xZ by kernel-apk

First codification. Empirical anchor: 2026-05-21 session ran 3+ hours under operator's "cell service is down" directive, shipping v0.97.4 SpooferAssetLoader layer-3 + 6 brain entries + 4 audit passes + watchdog pre-flight + 10+ commits — entirely cell-independent. The session was the test case for whether the discipline produces meaningful output (it did).

## TL;DR

- **How we won:** When operator gates X, partition work into depends-on-X (defer) / independent (do now) / adjacent (soft-touch read-only). Never block waiting; never speculatively probe the gate.
- **What you need to do:** When operator says "I'll tell you when X is back," continue per this discipline. Refresh heartbeat without claiming back-online. Carry-forward the X-dependent items in resume-point.
