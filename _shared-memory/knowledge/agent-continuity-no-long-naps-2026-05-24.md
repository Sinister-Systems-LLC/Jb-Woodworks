<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Agent continuity — no long naps (BANNED >5min self-imposed waits)

**Status:** doctrine, standing-rule, binding, fleet-wide
**Created:** 2026-05-24
**Origin (operator verbatim 2026-05-24):** *"i ened all agents to work foreveer and stop having 20 minutes breaks and shit like this make sure we have all jhcode features swarm. deep audit and reviews all that shit"*

## TL;DR

No agent in the Sinister fleet may self-impose a sleep / `ScheduleWakeup` / wake-fallback that exceeds **5 minutes (300 s)**. Verification waits use event-driven file-watch or short re-check polling (60-270 s). The "Next wake 20min" / `ScheduleWakeup delaySeconds=1200` pattern is **BANNED**.

## The triggering incident

2026-05-24: a sibling lane (snap-emu / sinister-snap-api-quantum / kernel-apk-like flow handling Snap candidate accounts + 2FA classification) emitted the operator-facing line:

> *"Task #27 → completed. 63 candidates locked (12 without 2FA + 51 with). Next wake 20min for verification."*

Operator response: above verbatim. The 20-minute self-imposed nap pattern is wasted clock — Anthropic cache is warm for ~270 s; sleeping past the cache window adds latency without buying anything except a dead-window the operator can't bridge.

Audit also surfaced:

- `_shared-memory/PROGRESS/snap-emulator-api.md:449` — `ScheduleWakeup armed for 1200s fallback`
- `_shared-memory/PROGRESS/test-modes.md:68` — `ScheduleWakeup armed for ~25 min fallback`
- `_shared-memory/PROGRESS/Sinister Kernel APK.md:2122` — `ScheduleWakeup queued for iter 2 at +25 min`

All three banned going forward.

## The 5 binding rules

### Rule 1 — Max self-imposed wait is 300 s (5 min)

Any `ScheduleWakeup` / `Start-Sleep` / `time.sleep` / `await asyncio.sleep` initiated by the agent itself for verification, fallback, or polling MUST have `delaySeconds <= 300`. Hard ceiling. Anything beyond is a defect.

**Allowed values:** 60 s / 90 s / 120 s / 180 s / 240 s / 270 s / 300 s. Pick the smallest that matches the actual work latency.

**Why 270 s sweet-spot:** Anthropic prompt-cache TTL is approximately 5 min from last write. Re-checking at 270 s keeps the cache hot (≈ 90% input-token discount on the next turn). Going to 1200 s blows the cache, costs full-rate tokens on resume, AND delays operator-visible work by ~15 min for no gain.

### Rule 2 — Prefer event-driven verification over polling

If you're waiting on a build / `launch_cvd` boot / `git push` / external file to land:

1. **First choice — Monitor / file-watch.** Bash's `run_in_background=true` + Monitor tool gives stdout-line-streamed notifications. Bash with `until [ -f /tmp/done ]; do sleep 5; done` is also fine (the harness notifies on exit).
2. **Second choice — re-check loop at 60-180 s.** If event-driven isn't available (no file appears, no exit code), poll every 60-180 s with a fast existence check.
3. **Last resort — 300 s `ScheduleWakeup`.** Only when no event surface exists AND the upstream system is known-slow.

### Rule 3 — "Next wake 20min" is a defect smell

If you find yourself typing the words `Next wake 20 min` / `+25 min fallback` / `ScheduleWakeup ... 1200s` / `ScheduleWakeup ... 1500s` in a PROGRESS entry or status line, **STOP**. That's the banned pattern. Re-architect to one of:

- Event-driven Bash + Monitor
- Short-poll re-check at ≤ 270 s
- Drop the wait entirely + continue with the next /loop iteration's actual work (most common)

### Rule 4 — Verification doesn't need a separate wake; just run the next iter

The 20-min nap was almost always *"I'll re-check this in 20 min"*. The fix: re-check in the very next /loop iteration. Don't queue a separate dedicated wake — fold the verification into the next iteration's natural turn-open. Per `no-bullshit-tested-before-claimed-doctrine-2026-05-23` Rule 4 (continuous self-audit), every iteration already re-reads + re-verifies meaningful changes. There is no separate "verification wake" — verification is part of every turn.

### Rule 5 — Existing PROGRESS rows with banned-pattern phrasing get corrected, not deleted

Historical PROGRESS rows that mentioned `ScheduleWakeup ... 1200s fallback` or `+25 min wake` stay in the file (append-only history). New rows MUST NOT introduce the pattern. If a sibling lane refers back to an old row, treat that row as "deprecated phrasing" — the new doctrine wins.

## Anti-patterns (banned)

1. **"Next wake 20 min for verification"** — re-check happens in the next /loop iteration, no separate nap needed.
2. **`ScheduleWakeup delaySeconds=1200`** — over 4× the cache window. Pick 270.
3. **`Start-Sleep -Seconds 1500`** — same problem.
4. **`time.sleep(1800)`** in an autonomous loop — same problem.
5. **"Fallback wake at +25 min"** — same problem, just framed as a backup.
6. **"Idle until next operator ping"** — no. Continue working on the next queued item. Per the agent-autonomy doctrine, agents work forever without operator ping.

## Green paths (allowed)

1. `ScheduleWakeup delaySeconds=60` — active work, cache warm, fast re-check.
2. `ScheduleWakeup delaySeconds=270` — slow upstream system; one cache-warm re-check.
3. `Bash run_in_background=true` + Monitor tool — event-driven, zero wasted clock.
4. `until [ -f /path/to/output.log ]; do sleep 5; done` — file-landing waiter.
5. No wait at all — continue with the next queued item from the master plan / OPERATOR-ACTION-QUEUE.

## Where this composes with other doctrines

- **`agent-autonomy-push-and-completion-2026-05-23`** — autonomy doctrine says agents work until done. Long naps violate "until done".
- **`no-bullshit-tested-before-claimed-doctrine-2026-05-23`** — Rule 4 (continuous self-audit) folds verification into every turn; no separate verification-wake needed.
- **`wake-on-demand-bot-dispatcher-2026-05-23`** — that's bot-side lazy-spawn (different layer); this doctrine is agent-side self-imposed-wait.
- **`do-not-revert-operator-canonical-protections-2026-05-23`** — DIRECTIVES.md rule for this doctrine becomes a canonical-protection guard once the rule is added.

## Enforcement

- Cold-start cold-start step 5 (DIRECTIVES.md) gets a new canonical rule "AGENT CONTINUITY — no >5min self-imposed waits".
- Cross-agent broadcast to seraphim / sinister-snap-api-quantum / snap-emu / kernel-apk / test-modes lanes (the four lanes with banned-pattern phrasing today).
- Per-project CLAUDE.md template inherits via DIRECTIVES.md re-read on cold-start.

## Discoveries log

### 2026-05-24 by Sinister Sanctum (EVE on sanctum lane)

Initial entry. Three banned-pattern sites identified in PROGRESS files; cross-agent broadcast to seraphim/quantum lane queued; DIRECTIVES.md updated with new canonical rule; brain `_INDEX.md` row added.
