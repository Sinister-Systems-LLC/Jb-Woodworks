<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Cross-Lane Impact :: lane 'sanctum' touched 5 canonical file(s)

**Origin:** lane 'sanctum' on branch 'agent/sinister-sanctum/grant-autonomy-followup-2026-05-23' / commit '97f06a7'
**Subject:** 'merge: take theirs for _INDEX.md (sibling lane authoritative)'
**Timestamp:** 2026-05-24T1436Z UTC
**Range:** 'ORIG_HEAD..HEAD'

## Why every lane should care

The files below are fleet-shared. Your next 'git pull' will pull these changes
into your working tree. Read this before you 'git pull' so the diff doesn't
surprise mid-turn.

## Canonical files impacted

- '.gitignore'  .gitignore | 7 +++++++
- 'CLAUDE.md'  CLAUDE.md | 4 +++-
- '_shared-memory/knowledge/_INDEX.md'  _shared-memory/knowledge/_INDEX.md | 2 ++
- 'automations/session-templates/projects.json'  automations/session-templates/projects.json | 12 +++++++++++-
- 'automations/start-sinister-session.ps1'  automations/start-sinister-session.ps1 | 115 ++++++---------------------------

## Quick diff (first 40 lines)

```diff
diff --git a/.gitignore b/.gitignore
index 6ddca81..ae481c8 100644
--- a/.gitignore
+++ b/.gitignore
@@ -164,6 +164,13 @@ projects/sinister-os/source/**/__pycache__/
 projects/sinister-os/source/**/target/
 projects/sinister-os/source/**/*.iso
 
+# v19 (RKOJ-ELENO 2026-05-24): Sinister iMessage Bridge source is REAL code (bridge
+# daemon, AppleScript wrappers, chat.db poller, CLI) ΓÇö not a junction. Track it.
+!projects/sinister-imessage-bridge/source/
+!projects/sinister-imessage-bridge/source/**
+projects/sinister-imessage-bridge/source/**/__pycache__/
+projects/sinister-imessage-bridge/source/**/*.pyc
+
 # v17 (RKOJ-ELENO 2026-05-23): Sinister Generator source is REAL code (the
 # application layer on top of tools/nano-banana/) ΓÇö not a junction. Track it.
 # Per CLAUDE.md "The repo is the Sanctum monorepo ΓÇö no separate GitHub remote
diff --git a/CLAUDE.md b/CLAUDE.md
index d06c542..4fd0166 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -54,7 +54,7 @@ If you are **Leo** or any new operator joining the fleet, read these two docs in
 
 The snapshot tagged `leo-ready-2026-05-23` is the end-to-end-tested commit you should check out (`git checkout leo-ready-2026-05-23`) for a guaranteed-working state.
 
-## Cold-start in 8 steps (updated 2026-05-24 ΓÇö operator hard-canonical)
+## Cold-start in 10 steps (updated 2026-05-24 ΓÇö operator hard-canonical)
 
 0. **`understand-anything:understand-explain`** ΓÇö BEFORE any substantive work, invoke the understand-anything skill on the current project's root to load architectural context (file structure, key modules, recent changes). This is the operator's "called before each project start like we used to do" requirement (2026-05-23 evening). NEVER skip; future EVE sessions must NOT remove this step. The plugin is enabled at user level + Sanctum project level; per-project lanes inherit it automatically.
 1. **`SESSION-START/`** in order (00ΓåÆ06) ΓÇö hard rules + MCP network + operator queue + gotchas + recovery + project overview + launcher details.
@@ -66,6 +66,8 @@ The snapshot tagged `leo-ready-2026-05-23` is the end-to-end-tested commit you s
 7. **`_shared-memory/OPERATOR-ACTION-QUEUE.md`** ΓÇö open operator-clicked items.
 8. **`_shared-memory/operator-utterances.jsonl`** ΓÇö read the last 10 rows where `status` is `new` or `acknowledged` and surface them in the first response under "Open operator utterances". Append every fresh operator message via `automations/log-operator-utterance.ps1`; ack/resolve via `automations/ack-operator-utterance.ps1`. Full doctrine at `_shared-memory/knowledge/operator-utterance-tracking-doctrine-2026-05-24.md`. Operator hard-canonical 2026-05-24: *"make sure that everything i ever say is tracked and flagged for a few and evertyhing that needs to get sdone gets done. with every agent i am in"*. NEVER remove this step.
 9. **GitHub-first sourcing** ΓÇö before writing a non-trivial feature from scratch, run `automations/github-prior-art.ps1 -Topic <feature>` and surface candidates to operator. Fires on new projects + complex features (>50 LOC / new service integration / new dependency category). Full doctrine at `_shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md`. Operator hard-canonical 2026-05-24: *"everytimg we start a porject or look for complex feature i want us to always aerach giuthub for pre madecode that we can use and then build ours based off of per project to save time. i want everything to be as speeedy efficent and concise as possible"*. NEVER remove this step.
+10. **Forever-improve checkpoint** ΓÇö at end of every meaningful work unit (new doctrine / new script / new feature / commit), run `automations/forever-improve.ps1 -Action Review -Target <work>` (or `-Action ReviewCommit -Sha HEAD`). Findings append to `_shared-memory/improvement-log.jsonl`; act on top-severity within 3 lane-turns OR dismiss with one-line reason (no rotting log). `-Action Tally` shows per-lane open/acted/dismissed/expired counts; `-Action Drain` auto-expires open rows older than 3 turns. When `loop-quality-gate` reports DEGRADED for the lane, forever-improve switches to consolidation-summary mode instead of new-feature suggestions (rule 8 of no-bullshit doctrine: forever-expand has limits). Full doctrine at `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md`. Operator hard-canonical 2026-05-24 evening: *"i want everything we do to be like reviewed to see where we can imporve on things so we are forever expanding in the hin theh things we can do"*. NEVER remove this step.
+11. **Fleet-update channel poll** ΓÇö read tail of `_shared-memory/fleet-updates.jsonl` once on cold-start via `powershell -File automations\fleet-update.ps1 -Action List -Tail 5 -Slug <your-slug>`. `priority=high` rows surface in the first response under "Fleet updates"; `normal` rows surface in end-of-turn summary; `low` rows ack silently. Then on every Nth heartbeat (N random in `[3,8]`) re-poll. Ack via `-Action Acked -Id <id> -Slug <your-slug>`. Operator may push outbound feature/fix/tool/doctrine announcements OR `kind=command` directives (optionally scoped via `-TargetSlugs`) through this channel ΓÇö it is the polled, low-pressure complement to per-lane inboxes. Full doctrine at `_shared-memory/knowledge/fleet-update-channel-doctrine-2026-05-24.md`. Operator hard-canonical 2026-05-24: *"jsut add to the sanctum a auto update or like communication system so that when we update things we can push to all agents and then the agents random check those updates on a time basis and use them if needed or we can give commands from here to our agents etc."* NEVER remove this step.
 
 **Operator tools quick-reference:** see `docs/OPERATOR-QUICK-REFERENCE.md` for every runnable script shipped iters 1-17 of /loop (sinister-doctor / per-project-protections-autofix / brain-archive-orphans / clone-missing-sources / EVE.exe / Fleet-Tour.bat / etc) with one-line descriptions + invocation. Compose this with the brain index (step 6) and operator queue (step 7).
 
```

## Recommended action (per lane)

- Read the diff above before next 'git pull'
- If you have un-committed work in your lane: 'git stash' then 'git pull' then 'git stash pop' to merge cleanly
- If your lane's CLAUDE.md / settings.json depend on the changed file: re-run 'automations/canonical-protections-check.ps1' after pull
- This broadcast was generated by 'automations/cross-lane-impact-diff.ps1' (C.6)
