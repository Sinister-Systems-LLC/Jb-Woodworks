<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Cross-Lane Impact :: lane 'sanctum' touched 3 canonical file(s)

**Origin:** lane 'sanctum' on branch 'agent/sinister-os/m1-hardening-2026-05-24' / commit '30135f2'
**Subject:** 'sinister-os: parallel ramp ΓÇö themes (4 services) + eve CLI + panel-dev HMR + 4 docs + bake-panel safety'
**Timestamp:** 2026-05-24T1541Z UTC
**Range:** 'ORIG_HEAD..HEAD'

## Why every lane should care

The files below are fleet-shared. Your next 'git pull' will pull these changes
into your working tree. Read this before you 'git pull' so the diff doesn't
surprise mid-turn.

## Canonical files impacted

- '_shared-memory/DIRECTIVES.md'  _shared-memory/DIRECTIVES.md | 18 ++++++++++++++++++
- '_shared-memory/knowledge/_INDEX.md'  _shared-memory/knowledge/_INDEX.md | 2 ++
- 'automations/start-sinister-session.ps1'  automations/start-sinister-session.ps1 | 49 +++++++++++++++++++++++++---------

## Quick diff (first 40 lines)

```diff
diff --git a/_shared-memory/DIRECTIVES.md b/_shared-memory/DIRECTIVES.md
index ec8a5e6..c878fb4 100644
--- a/_shared-memory/DIRECTIVES.md
+++ b/_shared-memory/DIRECTIVES.md
@@ -4,6 +4,24 @@ Every spawned Claude session reads this on cold-start. Most-recent at top.
 
 ---
 
+## 2026-05-24 ΓÇö AGENT CONTINUITY ΓÇö no >5min self-imposed waits (HARD RULE)
+
+Operator (verbatim 2026-05-24): *"i ened all agents to work foreveer and stop having 20 minutes breaks and shit like this make sure we have all jhcode features swarm. deep audit and reviews all that shit"*.
+
+**Standing rule ΓÇö every Sanctum agent, every turn, every `/loop` iteration:**
+
+1. No agent may self-impose a `ScheduleWakeup` / `Start-Sleep` / `time.sleep` / `await asyncio.sleep` exceeding **300 seconds (5 minutes)**. Hard ceiling. The "Next wake 20 min for verification" / `delaySeconds=1200` / `+25 min fallback` pattern is **BANNED**.
+2. If verifying a build, job, boot, push, or external file: watch the output file (event-driven via Bash `run_in_background=true` + Monitor) OR re-check every 60-270 s. The 270-s sweet-spot keeps Anthropic prompt-cache warm (~90% input-token discount on resume).
+3. Verification is folded into the **next /loop iteration's natural turn-open**, NOT a separate dedicated nap. Per `no-bullshit-tested-before-claimed-doctrine-2026-05-23` Rule 4 (continuous self-audit), every iteration re-reads + re-verifies meaningful changes.
+4. Allowed values: 60 / 90 / 120 / 180 / 240 / 270 / 300 seconds. Pick the smallest that matches actual upstream latency.
+5. Banned phrasings (do not write these in PROGRESS / heartbeat / cross-agent files): `Next wake 20min`, `ScheduleWakeup armed for 1200s`, `+25 min fallback`, `Fallback wake at +25 min`, `Idle until next operator ping`.
+
+The 20-min nap costs full-rate tokens on resume (cache evicted) AND delays operator-visible work by ~15 min for no gain. Continue with the next queued master-plan / OPERATOR-ACTION-QUEUE item instead.
+
+Full doctrine: `_shared-memory/knowledge/agent-continuity-no-long-naps-2026-05-24.md`. Composes with `agent-autonomy-push-and-completion-2026-05-23` + `no-bullshit-tested-before-claimed-doctrine-2026-05-23` + `wake-on-demand-bot-dispatcher-2026-05-23`.
+
+---
+
 ## 2026-05-19 ΓÇö Plugin discipline (no marketplace cancer) ΓÇö HARD RULE
 
 Operator (verbatim): "remove all the shit we added. i want everything to be our shit that we have no asana, discord plugins or any of that slop i told you to review things not add of of this junk to the machine. you should know better."
diff --git a/_shared-memory/knowledge/_INDEX.md b/_shared-memory/knowledge/_INDEX.md
index ddb1dc2..d75a7e9 100644
--- a/_shared-memory/knowledge/_INDEX.md
+++ b/_shared-memory/knowledge/_INDEX.md
@@ -6,6 +6,8 @@ Append-only catalog of every knowledge topic. New topics added at top with `Crea
 
 | Slug | Title | Status | Tags | Created | Updated |
 |---|---|---|---|---|---|
+| sinister-chatbot-test-env-findings-2026-05-24 | Sinister Chatbot `/chatter` test-env findings ΓÇö Bucket A 6/6 shipped end-to-end this session: A1 server-persist feedback (toggle semantics, FIFO 5000-row JSON store, recent_bad sampling) + A2 left-rail aggregate badge (single round-trip `by_persona` map; green ΓëÑ60% / red Γëñ40% / yellow between) + A3 compare providers mode (multi-select pills, `compareId`-tagged Promise.all fan-out, left-accent border on siblings, localStorage-persisted set) + A4 hot-reload persona + 700ms debounced auto-save (SaveStateBadge ticks per second: Saved ┬╖ SavingΓÇª ┬╖ Unsaved ┬╖ Saved Xs ago; clarifies that edits already flow into next Send live) + A5 Γå╗ Replay (re-fires `lastUserText` with current params; works in compare mode too) + A6 local LLM connectivity probe (LocalProbeBadge dot + model dropdown from probed `/models`; auto-select first installed model on mismatch; cross-machine hint when `localhost` URL fails on production backend). Verification stack: backend tsc EXIT 0 ┬╖ dashboard tsc EXIT 0 ┬╖ doctrine-audit strict 7/7 OK ┬╖ `npm run build` SUCCESS ┬╖ `smoke-feedback.mjs` 7/7 PASS ┬╖ `smoke-local-probe.mjs` with `OLLAMA_TEST=1` 4/4 PASS (incl real-Ollama 0.5.7 happy path). 5 gotchas documented: (1) Node v24 + Windows + `AbortSignal.timeout()` libuv assertion fixed via manual `AbortController` + `getGlobalDispatcher().close()` drain; (2) cross-machine `localhost` confusion on Hetzner-served frontend solved by tri-condition hint branch (isLocalish + isConn + onProd); (3) resume-point dir-name canonicalization drift (sinister-chatbot ΓåÆ Sinister Chatbot map entry added); (4) panel backend `node_modules/iconv-lite` breakage ΓåÆ handler-direct smoke harnesses sidestep express dep; (5) `sanctum-auto-push` 30-min sweep silently commits + pushes to origin/main (intended per autonomy doctrine but surprising first-encounter). 3 architectural patterns worth carrying forward: (a) explicit state-badges beat hidden behavior (SaveStateBadge taught operator the hot-reload distinction); (b) toggle semantics for thumb verdicts (single endpoint, re-click clears, switch updates in place); (c) `by_persona` inline aggregate avoids N+1 queries from list UIs. Composes with no-bullshit-tested-before-claimed-doctrine + agent-autonomy-push-and-completion + do-not-revert-operator-canonical-protections + operator-utterance-tracking-doctrine + agent-identity-eve. Open questions for next session: compare-mode horizontal layout for NΓëÑ3 ┬╖ persona import/export JSON ┬╖ sandbox transcript persistence ┬╖ LLM-as-judge auto-rating ┬╖ A6 happy-path against LM Studio/vLLM wire-format. | shipped, lane-state | shipped, lane-state, sinister-chatbot, chatter, test-env, prompt-engineering, bucket-a-complete, a1-server-feedback, a2-left-rail-badge, a3-compare-providers, a4-hot-reload-auto-save, a5-replay-last-message, a6-local-llm-probe, ollama-happy-path-verified, node-v24-libuv-workaround, cross-machine-hint, resume-point-canonicalization, handler-direct-smoke-harness, save-state-badge, toggle-semantics, by-persona-inline-aggregate, sanctum-auto-push-30min, 2026-05-24-session | 2026-05-24 | 2026-05-24 |
+| fleet-freeze-root-cause-2026-05-24 | Fleet "10-min freeze" root cause ΓÇö measured, not speculated. **Layer 1 (primary, expected CLI behavior):** Claude Code auto-compaction fires when in-memory transcript hits ~170k-token threshold, naturally lands every 30-60 turns (~10 min for busy fleet sessions); takes 5-30 s during which CLI is unresponsive. **Layer 2 (aggravator, fixable here):** Defender real-time + behavior-monitor + Ioav all ON with NO exclusion on `~/.claude/projects/` ΓÇö 2.7 GB accumulated transcripts (1,625 MB in `C--Users-Zonia/` alone / individual jsonls hit 87 MB / active session at 19.79 MB) trigger full delta-scan on every append. Combined: compaction window stretches 5-10 s ΓåÆ 20-60 s, and parallel sessions serialize through Defender's file locks ("all agents freeze together" symptom). **What was ruled out:** sinister-term has zero periodic timers (grep returned 0 matches; status helpers are 2s-TTL cached, heartbeat writes are per-prompt); no PT10M scheduled task exists (closest PT5M ├ù 2 coincidence in APKWatchdog + fleet-monitor); auto-push is PT30M with 25-min stale-lock recovery; vault daemon not running; `_shared-memory/` append-only files all <0.32 MB (no lock contention). **Fix shipped this turn:** (1) `automations/prune-claude-transcripts.ps1` archives >14-day-old transcripts to `~/.claude/projects-archive/` (out of hot path) ΓÇö actually ran, freed 704 MB / 2712 MB ΓåÆ 2008 MB measured; (2) `automations/fleet-freeze-probe.ps1` measurement script (6 sections ΓÇö footprint / Defender state / hot transcripts / scheduled tasks / shared-memory leaderboard / summary); (3) operator queue row for one-time Administrator Defender exclusion (`Add-MpPreference -ExclusionPath ~/.claude/projects` + file-history + claude.exe process). **Doctrine:** pre-empt auto-compaction by calling `/clear` or `/compact-context` manually when turn count approaches 40 or end-of-turn summary approaches 40-line cap. Composes with `resume-point-write-ps1-fulltree-scan-hang-2026-05-21` (sibling file-IO-on-large-tree issue) + `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (every claim here has command + measured value). Operator hard-canonical 2026-05-24 verbatim: *"Every like 10 minutes all agents will like freexze for some time make sure our sinsiter term or context cleaning or whatevr the fuck it is, is efficent"*. | doctrine, shipped, fleet-wide, measured | doctrine, shipped, fleet-wide, measured, fleet-freeze, claude-code-compaction, defender-exclusion, transcript-pruning, claude-projects-2.7gb-baseline, 704mb-freed, prune-claude-transcripts-ps1, fleet-freeze-probe-ps1, operator-action-queue-row, layer-1-primary, layer-2-aggravator, sinister-term-cleared, scheduled-tasks-cleared, manual-compact-context-doctrine, operator-hard-canonical-2026-05-24 | 2026-05-24 | 2026-05-24 |
 | fleet-update-channel-doctrine-2026-05-24 | Fleet-update channel ΓÇö single append-only `_shared-memory/fleet-updates.jsonl` carrying every outbound feature/fix/tool/doctrine/operator-command broadcast, polled lazily by every lane on a randomized N=[3,8] heartbeat cadence so no single tick spikes the whole fleet. CLI at `automations/fleet-update.ps1` with 4 actions (`Push` / `List` / `Acked` / `Expire`); sibling per-slug ack ledger at `fleet-updates-acks.jsonl`; lock at `.fleet-updates.lock` mirrors operator-utterance lock pattern. Priority semantics: `high`=surface-now / `normal`=end-of-turn / `low`=silent-ack. `kind=command` rows carry an explicit `command` string + optional `target_slugs` so operator can route directives to one-or-many lanes without per-lane inbox spam. Cold-start step 10 added to CLAUDE.md (poll once on session start). Smoke-tested end-to-end 2026-05-24T14:12-14:13Z: Push (id `2026-05-24T141248Z-feat`) ΓåÆ List (visible) ΓåÆ Acked (`slug=sanctum`) ΓåÆ List filtered by `-Slug sanctum` (row hidden) ΓåÆ Push fix `-ExpiresHours 0` ΓåÆ Expire (1 row flipped) ΓåÆ List vs `-IncludeExpired` (filter honored). Seed: 2 inaugural rows pushed (channel-live + prior-broadcast-digest). Operator hard-canonical 2026-05-24 verbatim: *"jsut add to the sanctum a auto update or like communication system so that when we update things we can push to all agents and then the agents random check those updates on a time basis and use them if needed or we can give commands from here to our agents etc."* Composes with operator-utterance-tracking-doctrine-2026-05-24 (mirror inbound channel) + agent-continuity-no-long-naps-2026-05-24 (poll cadence inside heartbeat budget) + no-bullshit-tested-before-claimed-doctrine + multi-agent-git-coordination (lock pattern). Per-lane inboxes remain THE directed-work channel; fleet-update is the new polled-advisory layer ΓÇö they coexist. | doctrine, shipped, fleet-wide | doctrine, shipped, fleet-wide, fleet-update-channel, broadcast, polled, append-only-jsonl, randomized-poll-3-to-8, priority-low-normal-high, kind-command-target-slugs, ack-ledger, lock-based-append, cli-push-list-acked-expire, cold-start-step-10, claude-md-anti-revert-candidate-p12, smoke-tested-2026-05-24, 2-seed-rows, operator-hard-canonical-2026-05-24, mirror-of-utterance-channel | 2026-05-24 | 2026-05-24 |
```

## Recommended action (per lane)

- Read the diff above before next 'git pull'
- If you have un-committed work in your lane: 'git stash' then 'git pull' then 'git stash pop' to merge cleanly
- If your lane's CLAUDE.md / settings.json depend on the changed file: re-run 'automations/canonical-protections-check.ps1' after pull
- This broadcast was generated by 'automations/cross-lane-impact-diff.ps1' (C.6)
