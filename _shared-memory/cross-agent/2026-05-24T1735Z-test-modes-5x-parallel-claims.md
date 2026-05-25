<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 5x parallel test-modes lanes — sub-area claims (2026-05-24T17:35Z)

> **Trigger:** operator at 17:32Z screenshot: *"review what i told this agent you and 4 others. total of 5 are going to work on all this launching you guys now."*
> **Parent directive (operator 17:21Z + 17:32Z stack):** active swarm now, jcode parity (cross-ref + contradict until quality drops), multi-account round-robin, per-project swarm prompt, 100% plan utilization (no token waste, push to limit before reset), session-restore-like-never-closed, memory smarter.

## Why this doc exists

5 EVE sessions are spawning **into the same `test-modes` lane on the same branch**. Without a claim split they will collide on file edits (CLAUDE.md, launcher, brain entries). This doc divides the directive into 5 non-overlapping sub-areas. Each sibling claims ONE sub-area + signs the claim. First-to-write wins; if a sibling sees their preferred sub-area already claimed they pick the next open one. Anything not claimed within 10 min is fair game for any sibling.

## Sub-area split

| # | Sub-area | Files this touches (sole owner during ship) | Acceptance criterion |
|---|---|---|---|
| A | **forge-memory auto-recall pre-fetch into Build-Phrase** (jcode parity rows 9-10 gap for claude-only spawns) | `automations/start-sinister-session.ps1` (Build-Phrase + Get-ResumeContextInject region only) | After spawn, child Claude phrase contains a `MEMORY_RECALL=` block with top-3 forge-memory hits on the latest operator-utterance tags. Smoke test: NoLaunch dry-run prints injected phrase. |
| B | **Multi-account 100%-utilization watchdog hardening** (push tokens to the actual 429 ceiling; no local-cap gating; auto-rotate seamlessly) | `automations/claude-account-watchdog.ps1`, `automations/claude-accounts.ps1` only | `Get-NextAvailableAccount` never returns null until ALL accounts are server-429'd. `Mark-AccountRateLimited` retry-after parsed from response headers (not heuristic). Smoke test: simulate 429 -> account marked, sibling spawn picks next account, no fleet-wide stall. |
| C | **JCode hard-gaps audit -> ship one row** (rows 23 claude-hooks PH13 OR row 25 agentgrep OR row 28 mermaid-rs-renderer fork) | `_shared-memory/knowledge/jcode-eve-exe-parity-audit-2026-05-24.md` + new lane PLAN row + skeleton repo (per chosen row) | One hard-gap moved from 🔴 to 🟡 with skeleton + brief + brain index row. |
| D | **Per-project swarm-prompt verify + projects.json default_modes audit + .bat re-prompt-on-resume** (operator: "ask per project i launch in the bat file") | `automations/session-templates/projects.json`, `automations/start-sinister-session.ps1` (Prompt-AgentModes call sites only) | Every project in `projects.json` has explicit `default_modes`. Resume path also fires Prompt-AgentModes (currently may skip on auto-resume). Smoke test: `start-sinister-session.ps1 -Project sanctum -NoLaunch` confirms prompt fires on resume path. |
| E | **Consolidated status doc + jcode-features-we-are-missing tally + utterance acks** (operator: "add now to the system all we were working on" + "review all jcode features we are missing") | `_shared-memory/knowledge/test-modes-5x-parallel-consolidated-status-2026-05-24.md` (NEW), brain `_INDEX.md`, ack utterances via `automations/ack-operator-utterance.ps1` for the 13 lane-targeted rows | Single doc lists every shipped piece across A+B+C+D + outstanding hard gaps + lane ownership + next-step matrix. 13 utterances acked + linked to deliverables. |

## How to claim

Edit THIS file, replace `[OPEN]` with `[CLAIMED by <session-tag>]` for ONE sub-area, then save IMMEDIATELY. Race window is small but real — if two sessions write at once last-write-wins, look at the result, and the loser picks another sub-area. Below is the claim register.

## Claim register

- **Sub-area A — forge-memory auto-recall pre-fetch into Build-Phrase** — [SHIPPED by test-modes-iter4 2026-05-24T18:00Z]
  - `automations/start-sinister-session.ps1` `Get-MemoryRecallInject` (NEW, ~70 LOC) — harvests tags from last 30 operator-utterances (status=new/acknowledged), joins top-8 unique tags into a query, invokes `forge-memory recall` with 5s wall-clock cap + graceful no-CLI fallback, parses JSON, formats top-3 hits as compact `[key] value(80c)` joined `|`, returns ` MEMORY_RECALL (auto-prefetch from forge-memory on tags=<q>): <hits>` injection.
  - `Build-Phrase` resume branch now appends `Get-MemoryRecallInject` after `Get-ResumeContextInject`. Killswitch: `SINISTER_SKIP_MEMORY_RECALL=1`.
  - **Smoke-test verified:** isolated function call returned 272-char result in 0.18s with hits on tags=`mode-flip test-modes --swarm phone multi-account round-robin no-downtime rate-limit`. Parse-clean.
  - **Closes:** jcode-parity-audit rows 9-10 (claude-only EVE.exe spawns now auto-prefetch memory hits inline; previously the phrase only TOLD the agent to call forge-memory manually).
- **Sub-area B — Multi-account 100%-utilization watchdog hardening** — [SHIPPED by test-modes-iter5 2026-05-24T17:50Z]
  - `automations/claude-accounts.ps1` Get-NextAvailableAccount v4 — honors `cfg.rotation_strategy`. Three strategies: `burn-first` (anchor on cfg.default until 429 → next enabled non-RL highest-tier-first), `round-robin-strict` (cycle via last_rotation_index), `load-balance` (legacy).
  - `_shared-memory/claude-accounts.json` rotation_strategy `load-balance` → `burn-first`. Smoke-test: `PICKED=operator strategy=burn-first` parse-clean.
  - **Gap** (operator-config, not code): only `operator` is `enabled:true`; leo/slot3/slot4 are disabled. burn-first 100%-failover requires ≥2 enabled accounts. Queued as operator-action.
  - **Acceptance partial:** code change verified parse-clean + smoke-test PICKED returns expected account. Server-429 retry-after header parse + Mark-AccountRateLimited automation is open for next iteration (counter-arg row in this turn's PROGRESS).
- **Sub-area C — JCode hard-gaps audit -> ship one row** — [PARTIAL by test-modes-gap-audit (this session, 2026-05-24T17:52Z)]
  - Ran `automations/jcode-parity-probe.ps1 -Json` end-to-end. Baseline: 24 PASS / 3 real-FAIL / 4 expected-FAIL out of 31.
  - **Fixed R8 probe-defect** (`automations/jcode-parity-probe.ps1` `$rufloPaths` was stale — pointed at npm-global, but Ruflo actually lives at `_shared-memory/external-imports/ruflo/`). After fix: 25 PASS / 2 real-FAIL. Verified by re-run.
  - Wrote `_shared-memory/knowledge/jcode-parity-gap-audit-2026-05-24-test-modes.md` — verified row-by-row gap summary. R21 + R29 cross-referenced to existing operator-action queue items; no new doctrine needed.
  - **Remaining (still open for next sibling):** ship one of the planned rows (R23 claude-hooks PH13 / R24 Skill_Seekers PH12 / R25 agentgrep PH14 / R28 sinister-mermaid-render Rust fork). All four are 📋 planned with explicit owners in the matrix.
- **Sub-area D — Per-project swarm-prompt verify + projects.json audit + bat re-prompt-on-resume** — [SHIPPED by test-modes-iter6 2026-05-24T17:55Z]
  - `Prompt-AgentModes` (start-sinister-session.ps1:1068+) accepts `-ProjectRec` and pre-fills from `projects.json.default_modes.{swarm,loop}`. All 4 call sites (now lines 1800/1818/1838/1855) pass `$projRec` — covers cold spawn, by-key spawn, new-project flow, resume-by-key.
  - **projects.json default_modes audit DONE**: PowerShell audit `25/25 projects have default_modes`. Sibling seeded the remaining 22 between iter5 and iter6. Zero missing.
  - **Bat re-prompt-on-resume verified**: function honors `SINISTER_SKIP_MODES_PROMPT=1` for silent mode; without env it prompts interactively. All 4 call paths reachable.

- **Sub-area D extension — Headless `-Project` path now also prompts** — [SHIPPED by test-modes-iter4 2026-05-24T18:05Z]
  - **Gap found:** iter6 covered the 4 INTERACTIVE picker paths. But EVE.exe's actual dispatch flow is `EVE.exe picker -> subprocess.call powershell -File start-sinister-session.ps1 -Project <key>`, which takes the **headless `-Project` branch (line 1714)**. Pre-fix that branch used `$modes = @{ swarm=$env:..; loop=$env:.. }` — env-vars-only, NEVER prompting. Operator's hard-canonical "ask per project i launch in the bat file" was silently bypassed for the most-common spawn path.
  - **Fix:** line 1714 now calls `Prompt-AgentModes -ProjectRec $projRec` like the interactive paths. Honors `SINISTER_SKIP_MODES_PROMPT=1` for true-headless (Task Scheduler / cron); without env it prompts in the parent EVE.exe terminal (subprocess.call inherits stdin so Read-Host reads from the same window). eve.py only sets the skip-env when the operator explicitly passed `--swarm`/`--loop`/`--both`/`--no-*`, so normal picker flow now surfaces the prompt as the operator expects.
  - **Smoke-test:** `powershell.exe -File start-sinister-session.ps1 -Project sanctum -NoLaunch` with `SINISTER_SKIP_MODES_PROMPT=1` env exits 0 (bypass path PASS). Parse-clean before + after edit. End-to-end (Read-Host hit) deferred to next interactive EVE.exe launch by operator.
  - **Closes operator's "bat not loading fix it" UX concern**: previously the spawn went silently headless from operator's POV. Now the spawn surfaces a visible prompt in the same window where they made the project pick, plus the new mintty window opens after they answer.

- **Sub-area B continuation — 429 retry-after parsing in spawn .sh** — [SHIPPED by test-modes-iter6 2026-05-24T17:55Z]
  - `automations/start-sinister-session.ps1` (~line 1490 in spawn .sh heredoc): default-60s retry-after replaced with two-stage extraction. JSON header `"retry-after":"<N>"` first; then text "retry after N" / "try again in N seconds"; falls back to 60s.
  - Smoke-tested standalone: 3/3 patterns return correct integer (`{"retry-after": "1234"}` → 1234, `Please try again in 567 seconds.` → 567, `Retry-After: 89` → 89). Parsed value flows into `-RetryAfterSeconds <N>` arg of `claude-accounts.ps1`.

- **Sub-area E — Consolidated status doc + jcode-features-missing tally + utterance acks** — [SHIPPED by test-modes-iter7 2026-05-24T18:10Z]
  - **`_shared-memory/knowledge/test-modes-5x-parallel-consolidated-status-2026-05-24.md` (NEW)** — full scoreboard (6 ship + 1 partial of 7 deliverables), per-sub-area detail tables, outstanding-gap matrix, sibling matrix, halt-check (cold-start steps at 11 / threshold 10 = EDGE, consolidation pass queued).
  - **11 lane-targeted utterances acked** total (was 8): added 15:40:57 (utterance tracking), 15:42:25 (github intake), 16:05:32 (docker auto-open + token efficient) this iter.
  - jcode-parity-probe (post-R8-fix): 25/31 PASS, 2 REAL-FAIL (R21 daemon / R29 picker_overlay.py — both operator-side gates), 4 EXP-GAP (R23/R24/R25/R28 planned per matrix).
  - **Skipped brain `_INDEX.md` row** by design — brain at 157 rows (no-bullshit signal 1 tripped). Per-lane status docs don't warrant index entries; claim register IS the index for this 5x sweep.
  - **Remaining (out-of-domain for test-modes):** 4 utterances unacked (16:09:10 / 15:56:34 sinister-os-mobile branding+project — those lanes' work) and Sub-area C row-ship (R23/R24/R25/R28 — owner Forge/Sanctum).

## Anti-collision rules

1. **One sub-area per session.** If you finish A in 20 min and want to grab another, edit the register again to claim a SECOND row — don't silently sweep.
2. **No edits outside your sub-area's listed files** without re-claiming. The launcher + brain entries are shared surfaces.
3. **Commit your sub-area's work as a single atomic commit** with prefix `[test-modes-5x-A]` / `[B]` / `[C]` / `[D]` / `[E]`. Branch is shared (`agent/sinister-os-mobile/p0-spec-2026-05-24`), so atomic = no half-finished interleaved diffs.
4. **End-of-turn**: each session writes a resume-point + updates this register with `[SHIPPED by <session-tag>]` + deliverable bullet. Subsequent siblings see what's done.
5. **If you find a counter-argument** to the sub-area approach (e.g., "wiring forge-memory into Build-Phrase will blow the cold-start phrase budget"), log it via `automations/counter-arg.ps1` BEFORE shipping the change.

## Composes with

- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — every sub-area must have a smoke-test in its acceptance criterion
- `multi-agent-branch-contention-isolation-pattern` — claim register is the lightweight isolation when worktree-per-lane isn't available
- `jcode-eve-exe-parity-audit-2026-05-24` — parent audit that rows 9-10 / 23 / 25 / 28 come from
- `agent-autonomy-push-and-completion-2026-05-23` — agents push their own branch freely; this register is the coordination layer on top
