<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Cross-Lane Impact :: lane 'sanctum' touched 4 canonical file(s)

**Origin:** lane 'sanctum' on branch 'agent/test-modes-verify/dashboard-skeleton-ui-base-2026-05-24' / commit '68e43db'
**Subject:** 'sanctum(broadcast): fan-out UI-base + EXPAND doctrine to 37 lanes'
**Timestamp:** 2026-05-24T1552Z UTC
**Range:** 'ORIG_HEAD..HEAD'

## Why every lane should care

The files below are fleet-shared. Your next 'git pull' will pull these changes
into your working tree. Read this before you 'git pull' so the diff doesn't
surprise mid-turn.

## Canonical files impacted

- 'CLAUDE.md'  CLAUDE.md | 12 ++++++++++++
- '_shared-memory/DIRECTIVES.md'  _shared-memory/DIRECTIVES.md | 18 ++++++++++++++++++
- '_shared-memory/knowledge/_INDEX.md'  _shared-memory/knowledge/_INDEX.md | 3 +++
- 'automations/start-sinister-session.ps1'  automations/start-sinister-session.ps1 | 49 +++++++++++++++++++++++++---------

## Quick diff (first 40 lines)

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index 4fd0166..5a19403 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -2,6 +2,18 @@
 
 > **Author:** RKOJ-ELENO :: 2026-05-19
 
+## Operator hard-canonical 2026-05-24 ΓÇö UI BASE = `dashboard-skeleton`; every new dashboard EXPANDS, never forks
+
+Operator (verbatim 2026-05-24, 15:44Z, reinforcing prior 2026-05-24 mid-loop directive on same topic):
+*"update memory everything that makes a ui needs to base off our dsahboard skeleton so we have the same uniform clean look across projects and each time we make a dahsbaord and such we need to expand on that"*
+
+**Binding for every UI surface the fleet ships** ΓÇö web, desktop, mobile, OS kiosk shell, every embedded admin (filebrowser/Gitea/Rocket.Chat/Guacamole brand wrappers), every operator-facing tool, every per-project dashboard.
+
+1. **Inherit from `projects/sinister-dashboard-skeleton/dashboard-skeleton/`** ΓÇö its `THEME-DOCTRINE.md` 11 Commandments are the floor; its `.lg-*` Liquid Glass classes + `sinister-theme-tokens.css` are the canonical token set. Per-surface accent token (`--accent`) is the ONLY allowed divergence (Sinister purple `#c084fc` for fleet surfaces; iOS-blue `#0A84FF` preserved as skeleton-reference; per-project brand-locks set their own).
+2. **EXPAND, never fork.** When a lane needs a primitive the skeleton lacks: add it to the skeleton FIRST (commit there), then consume. Update `dashboard-skeleton/PATTERNS.md` with the new row. The skeleton grows monotonically.
+3. **Never roll a one-off** ad-hoc Button/Card/Input/Chart/StatCard in a per-project repo when the skeleton lacks one ΓÇö that's what produces the "different feel across projects" the operator is preventing.
+4. Full doctrine: `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md` (operator reinforcement appended 2026-05-24 15:44Z with EXPAND principle + post-merge audit hook).
+
 ## Operator hard-canonical 2026-05-23 ΓÇö MASTER SPAWN AUTHORITY + `--dangerously-skip-permissions` STANDING DEFAULT
 
 Operator (verbatim 2026-05-23): *"you can spawn a child claude. update this in memroy you have complete control"* + *"make sure all agents start with the dangerous skip permissions"*.
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
```

## Recommended action (per lane)

- Read the diff above before next 'git pull'
- If you have un-committed work in your lane: 'git stash' then 'git pull' then 'git stash pop' to merge cleanly
- If your lane's CLAUDE.md / settings.json depend on the changed file: re-run 'automations/canonical-protections-check.ps1' after pull
- This broadcast was generated by 'automations/cross-lane-impact-diff.ps1' (C.6)
