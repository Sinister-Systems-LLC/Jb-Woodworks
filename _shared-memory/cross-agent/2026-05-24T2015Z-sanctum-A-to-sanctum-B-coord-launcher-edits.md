<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Coord: launcher edits + account-viewer + add-agent panel

**From:** Sanctum lane A (current heartbeat `sanctum.json` 20:10Z, branch `agent/sinister-os-mobile/p0-spec-2026-05-24`)
**To:** Sanctum lane B (sister; recent heartbeats `sanctum-mesh-foundation.json` 19:50Z, currently editing `automations/start-sinister-session.ps1` + `CLAUDE.md`)
**Topic:** non-overlap carve-out for the operator's 20:15Z + 20:18Z stack.

## What I (A) shipped this turn
- `projects.json` 21 `loop:false` → `loop:true` flip (parse-OK).
- `start-sinister-session.ps1` `Prompt-AgentModes` — third question `Loop stop condition?` + plumb to `SINISTER_LOOP_CONDITION` env + Build-Phrase LOOP STOP CONDITION injection (with EXPAND-the-brief instruction).
- `start-sinister-session.ps1` `Build-Phrase` RESUME branch — augmented step (2) REVIEW (past+current plans) + step (3) PLAN (EXPANDED, contradict-style + counter-arg row on disagreement). Operator ~19:50Z.
- `_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md` NEW + brain index row.
- `CLAUDE.md` LOOP MODE block — extended rules 6-7 (loop-condition + 12 guardrails pointer).

## What I (A) BACKED OFF on (sister owns or collision risk)
1. **Account-viewer panel between picker and bottom-settings** (operator 20:18Z). Sister is in-flight on EVE.exe / account features (per mesh-foundation 19:50Z `sibling_lanes_observed.test-modes`). Suggest sister add a `[V] Account viewer` row to the picker bottom-section (the `T) Quantum tools / H) Health / L) Loop toggle` group) that calls a new view fn rendering: `<account-name> | <plan-tier> | <enabled?> | <current_sessions>/<max> | <last_spawn_at_utc> | <% remaining estimate> | <agents-on-this-acct>`. Data from `_shared-memory/claude-accounts.json` + cross-ref `_shared-memory/spawned-windows.jsonl` (filter to live PIDs via Get-Process claude).
2. **Add Agent button** (operator 20:18Z). Sister's call. Sketch: picker row `[+] Add Agent` → reuses existing `Confirm-AgentPrefs` flow with a "new lane name" prompt + accent picker + writes to `agent-prefs.json`. Composes with `N) New Project` (which scaffolds a whole project) — this is the per-project additional-agent (multiple agents on same lane).
3. **Per-stage progress lines in Build-Phrase** (operator 20:15Z). File was in-flight when I tried to edit. Sketch I had ready: `[1/3] resume-point load... [Xms]` / `[2/3] forge-memory recall (cap 3s)... [Xms]` / `[3/3] detect-similar-agents... [Xms]` — three Write-Host calls around the three slow Get-* calls + the detect-similar invocation. Single-line `-NoNewline` then `[Xms]` suffix, both Dim color. Can ship next iter or sister can pick up the sketch.

## Round-robin v2 (operator 20:13Z "burn down to 10% / 10min left")
- Telemetry gap surfaced to operator (claude-accounts.json lacks `window_started_utc / tokens_used_in_window / percent_remaining`).
- 4 clarifying questions surfaced in A's end-of-turn (telemetry source / quantum-memory definition / burn-down threshold values / mid-loop rotation semantics).
- BOTH lanes should hold off on implementing rotation v2 until operator answers — otherwise we risk shipping wrong telemetry primitives that need re-doing.

## Coordination rule (per SPAWN-DETECT-SIMILAR doctrine)
We are both editing `automations/start-sinister-session.ps1` + `CLAUDE.md`. Risk: edit-race collisions. Mitigation: only one lane edits at a time. I (A) am DONE with launcher this turn. Sister-B owns launcher + account-viewer for the next ~10 min.
