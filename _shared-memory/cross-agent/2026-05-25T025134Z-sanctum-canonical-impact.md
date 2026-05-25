<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Cross-Lane Impact :: lane 'sanctum' touched 3 canonical file(s)

**Origin:** lane 'sanctum' on branch 'agent/sinister-os/iter15-doctrine-adopt-2026-05-25' / commit 'be9d3ab'
**Subject:** 'sanctum: brain auto-annotate + per-agent branch push fan-out + doctrine'
**Timestamp:** 2026-05-25T0251Z UTC
**Range:** 'ORIG_HEAD..HEAD'

## Why every lane should care

The files below are fleet-shared. Your next 'git pull' will pull these changes
into your working tree. Read this before you 'git pull' so the diff doesn't
surprise mid-turn.

## Canonical files impacted

- 'CLAUDE.md'  CLAUDE.md | 208 +++++++++++++++++++++++++++++++++++++++++++++++++++++++-------
- '_shared-memory/OPERATOR-ACTION-QUEUE.md'  _shared-memory/OPERATOR-ACTION-QUEUE.md | 459 +++++++++++++++++++++++++++++---
- '_shared-memory/knowledge/_INDEX.md'  _shared-memory/knowledge/_INDEX.md | 60 ++++++++++++++++++++++++++++++++++++++

## Quick diff (first 40 lines)

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index 5a19403..60cb309 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -2,6 +2,177 @@
 
 > **Author:** RKOJ-ELENO :: 2026-05-19
 
+## Operator hard-canonical 2026-05-25 ΓÇö WE HAVE THE SOURCE; READ IT (no reverse-engineering)
+
+Operator (verbatim 2026-05-25 ~02:25Z): *"you dont need to RE his shit we have the fucking code this is the last time im going to tell you this update memory"*
+
+**Binding for every fleet agent.** When the operator references jcode, Claude Code CLI, any GitHub repo we have cloned, or any project on disk -- **READ THE SOURCE DIRECTLY** via Grep + Read + Glob. Do NOT spawn "reverse-engineering" sub-agents. Do NOT treat as black box. Do NOT probe behavior to infer architecture.
+
+Paths we have direct access to:
+- jcode: `C:\Users\Zonia\Desktop\jcode-0.12.4\`
+- Cloned GitHub repos: `_shared-memory/inbox/link-ingest/processed/<id>/download/repo/`
+- All Sinister projects: `projects/<key>/`
+
+Sub-agent prompts must phrase comparative audits as "READ source at <path>, synthesize patterns, cite FILE:LINE" -- NOT "reverse-engineer".
+
+Full doctrine: `_shared-memory/knowledge/we-have-the-source-read-it-doctrine-2026-05-25.md`. Composes with `github-first-sourcing-doctrine-2026-05-24.md` + no-bullshit doctrine rule 1.
+
+## Operator hard-canonical 2026-05-25 ΓÇö LOOP MODE = RELENTLESS (aggressive pursuit + tool-reach + watchdog)
+
+Operator (verbatim 2026-05-25T02:18Z): *"make the loop system on our agents actually work. make it agressive and make it hafve agents relentless pursue goal within our guidelines using our tools iwhen on."*
+
+**Binding for every `loop=on` spawn.** This block EXTENDS the existing LOOP MODE block below (rules 1-7) with rules 8-11. SAFE half stays binding (`safe-quality-loops-doctrine-2026-05-24` ΓÇö reversibility wall, scope freeze, quality monotonic, cost ceilings, operator interrupts). RELENTLESS half does NOT override SAFE.
+
+8. **RELENTLESS PURSUIT** ΓÇö after every shipped deliverable: (1) re-read open queue for your lane ΓåÆ (2) re-read operator-utterances tail (`status=new` for your lane addressed FIRST) ΓåÆ (3) re-poll fleet-updates ΓåÆ (4) re-check `_shared-memory/inbox/<your-slug>/*.json` for `kind=loop-poke` rows ΓåÆ (5) pick next unaddressed item (priority: operator interrupts > new high fleet-update > queue > backlog plan) ΓåÆ (6) **SHIP IT THIS TURN** ΓåÆ (7) only ScheduleWakeup cap 270s if zero actionable AND loop_condition unsatisfied. End-of-turn summaries are CHECKPOINTS, not goodbyes ΓÇö always start the next iter.
+
+9. **ANTI-STOP CHECKLIST** ΓÇö six binary checks before any end-of-turn; ANY `no` = keep going: queue empty? / utterances all addressed? / fleet-updates polled this iter? / sub-agents all returned? / loop_condition satisfied + verified? / 90%+ compaction? No "polite-stop" allowed.
+
+10. **TOOL-REACH FIRST** ΓÇö before defaulting to Read/Grep/Edit, reach for: `bot-fleet-quick-reference.md` (13 local MCP bots) / `automations/fleet-update.ps1` / `automations/mesh-coordinator.ps1` / `automations/agent-poke.ps1` / `automations/log+ack-operator-utterance.ps1` / `automations/forever-improve.ps1` / `automations/brain-decay-score.ps1` / `automations/detect-similar-agents.ps1` / `automations/quality-monotonic-loop.ps1` / `automations/sanctum-auto-push.ps1` / `Agent` subagent_type=Explore/general-purpose for parallelizable work / `ToolSearch` to discover deferred tools. Routine work routes to bots; Opus is for synthesis + decisions, not file-walking.
+
+11. **WATCHDOG POKE = OPERATOR INTENT** ΓÇö `loop-relentless-watchdog.ps1` (schtask `SinisterLoopRelentlessWatchdog`, 5min cadence) detects 3 stall signals (heartbeat >8min stale / same `focus_intent` 3 ticks / same `loop_iter` 3 ticks) and writes a `kind=loop-poke` row to your inbox. When you see a poke row: treat as operator-canonical signal ΓåÆ pick next per rule 8 ΓåÆ SHIP THIS TURN ΓåÆ mv poke to `_acked/`. Manual operator-emergency-button: `agent-poke.ps1 -Action PokeAll -Priority high` (Desktop one-click: `Poke-All-Sinister-Agents.bat`).
+
+Full doctrine: `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md` (4 sub-rules + 6 anti-patterns + pass criterion + 9 compose-with brain entries).
+
+## Operator hard-canonical 2026-05-25 ΓÇö SINGLE-REPO PUSH POLICY (3 carve-outs only)
```

## Recommended action (per lane)

- Read the diff above before next 'git pull'
- If you have un-committed work in your lane: 'git stash' then 'git pull' then 'git stash pop' to merge cleanly
- If your lane's CLAUDE.md / settings.json depend on the changed file: re-run 'automations/canonical-protections-check.ps1' after pull
- This broadcast was generated by 'automations/cross-lane-impact-diff.ps1' (C.6)
