<!-- decay:
  category: preference
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# One-Terminal-Per-Project + No-Overlap-Sub-Agents Doctrine (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25

## Operator verbatim (2026-05-25)

> *"ok condense down to 1 agent like i said and make sure you work from one window and have all info here and make sure of this moving foward. 1 window per project but can have parrallel mcp bots of cousr."*
>
> *"ok stop you idiots better not be fucking with each other and making 3 copies. this has to stop. clean this up and enure this shit dont happen again."*
>
> *"make sure we take note of that 1 termnal per project so taht no toes are stepped on. we need ot be concise for this and add failsafes for all thigns like this."*
>
> **CLARIFICATION (Image #16, 2026-05-25)**: *"you can use parrallel agents and full swarm . just 1 view like this per project but you can use all bots mcps servers, parralkle agents as you need."*

## Authoritative rule (post-clarification)

- **1 Claude WINDOW per project lane.** Don't open a second terminal for the same project slug.
- **WITHIN that window, full swarm is ENCOURAGED**: spawn parallel `Agent` sub-agents, call MCP bots, run MCP servers concurrently, fan out across non-overlapping file slices.
- "No overlap" applies to **file sets**: two parallel sub-agents must touch DISJOINT files. If they could touch the same file → serialize the work or split the slice.

## Binding rules (every Sanctum master agent)

1. **ONE TERMINAL PER PROJECT.** Each project lane (sanctum / sinister-os / letstext / showmasters / jb-woodworks / kernel-apk / overseer / panel / memory / chatbot / freeze / rkoj / sleight / jkor / etc.) gets EXACTLY ONE running Claude session at a time. Never spawn a second window for the same project.

2. **NO OVERLAPPING SUB-AGENTS ON SHARED FILES.** When using the `Agent` tool, sub-agents must work on NON-OVERLAPPING file sets (different directories, different files). If two sub-agents could touch the same file → DO NOT SPAWN them in parallel; do the work serially in the master window instead.

3. **MCP BOTS ARE FINE IN PARALLEL.** Small, single-purpose MCP tool calls (semantic search, memory recall, browser sessions, etc.) can run concurrently because they're read-mostly and don't fork the working tree.

4. **MASTER WORKS IN ONE WINDOW.** All Sanctum-master work happens in the master's own Claude window — not in spawned worktree forks. The `isolation: "worktree"` flag is BANNED for Sanctum sub-agents on this repo (it caused 5149-file worktree creates that timed out and left stuck locked worktrees).

5. **FAILSAFE — before spawning a project session via `start-sinister-session.ps1`:**
   - Check `_shared-memory/heartbeats/<slug>.json` for a heartbeat newer than 5 min → if present, ABORT (project already has a live session).
   - Check `tasklist /FI "WINDOWTITLE eq Sinister <project>*"` → if a window exists, ABORT.

6. **FAILSAFE — before spawning a sub-agent via `Agent` tool:**
   - Map out the EXACT files the sub-agent will touch.
   - If another sub-agent in this turn touches ANY of those files → fold the work serially into the master, OR pick a non-overlapping slice.
   - Worktree isolation is OFF by default; only use when you're sure no overlap exists AND the worktree create won't timeout (small repo or shallow checkout).

7. **MASTER ORCHESTRATES, DOESN'T CO-EDIT.** Per-project files (under `projects/<key>/`) are owned by that project's session. Sanctum master only touches them for:
   - Initial scaffolding (new project setup, picker entry add)
   - Cross-lane refactors explicitly requested by operator
   - When the project session has been dead >24h and a P0 fix is needed

8. **EVE.exe PICKER ENFORCES THIS.** The picker should refuse to start a second session for a project that already has a live heartbeat. (Future iter: add this check in `project_picker_multiselect.launch_selected()`.)

## Pass criterion

- `git worktree list` shows only 1 entry for `D:\Sinister Sanctum` (plus any operator-managed long-running ones in `C:\tmp` or `D:\tmp`).
- No two heartbeat files for the same project slug have timestamps within 5 min of each other.
- Sanctum master commits land sequentially (no concurrent commits to same branch from forked workers).

## Anti-patterns (NEVER do these)

1. **Spawn 5 worktree-isolated sub-agents** on the same repo simultaneously. (Caused 9 stuck worktrees + 5 minute file-update freezes in iter-27.)
2. **Spawn a sub-agent to edit `eve.py` while master is also editing it.** Concurrent index races + lost commits.
3. **Launch sinister-os twice** because the first one looks idle. Check heartbeat first.
4. **Make a sub-agent do 14 unrelated tasks** in one prompt. Scope it down.
5. **Sleep + poll for sub-agent completion** when the parent could just do the work directly faster.

## Composes with

- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` (master = high-level orchestration only)
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md` (relentless = keep going, NOT spawn copies)
- `_shared-memory/knowledge/safe-quality-loops-doctrine-2026-05-24.md` (quality > parallelism)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (verified > parallel-claimed)
