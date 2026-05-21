---
name: sinister-sweep
description: Full Sanctum fleet status sweep
allowed-tools: [bash, read_file, glob_search]
---
# Active Skill: sinister-sweep

Full fleet status sweep — the deep version of `/sinister-status`. Where
`/sinister-status` gives a 4-7 bullet cold-start summary, `/sinister-sweep`
walks every active surface and produces a structured report.

Run this when the operator asks "give me the full sweep" or before a major
context switch (e.g. start of a new working block).

## Steps

1. **Heartbeats** — `glob` `D:/Sinister Sanctum/_shared-memory/heartbeats/*.json`.
   For each file: read `agent_display`, `last_heartbeat_iso`, `agent_identity`.
   Categorize: live (< 30 min), stale (30 min – 2 h), dead (> 2 h).
   Report per-lane counts + the stalest slug per category.

2. **Inbox** — `glob`
   `D:/Sinister Sanctum/_shared-memory/inbox/*/*.json`. Group by project
   lane (parent dir name). Report:
   - Unread count per lane
   - Three most-recent message subjects/topics per lane (newest first)
   - Any message tagged `URGENT` or `BLOCKER` — surface first

3. **PROGRESS top-3** — for each file in
   `D:/Sinister Sanctum/_shared-memory/PROGRESS/`, read the three most-recent
   `## ` entries (top of file = newest). Report headline + date per lane.

4. **Recent commits** — run `git log -5 --oneline` from
   `D:/Sinister Sanctum/`. Report the five most-recent commit subjects.

5. **EXE version** — run
   `"C:/Users/Zonia/Desktop/RKOJ.exe" --version` and capture output.
   If the EXE is missing or fails, note it. Cross-check with the build
   timestamp in `dist/RKOJ.exe` under `automations/build/forge-exe/`.

6. **Action queue** — read
   `D:/Sinister Sanctum/_shared-memory/OPERATOR-ACTION-QUEUE.md`. Report:
   - Total open `[ ]` items
   - Any `URGENT`/`BLOCKER` items verbatim
   - Three most-recently added items

## Output format

Markdown report with six numbered sections matching the steps above. Each
section is 2-6 lines. End with a one-line headline:

> Fleet status: `<healthy|degraded|critical>` — `<one-line reason>`.

`critical` if any heartbeat is dead OR any URGENT/BLOCKER is open.
`degraded` if any heartbeat is stale OR EXE smoke fails.
`healthy` otherwise.

## Hard rules

- READ-ONLY across the entire sweep. Never modify shared memory, inbox,
  PROGRESS, or commit anything.
- If RKOJ.exe is missing from the Desktop, note it but do NOT auto-rebuild
  — that's `/forge-build` or `/rkoj-rebuild`.
- Never enumerate `_vault/` (secret material).
- Surface URGENT/BLOCKER items at the TOP of the report, before the
  numbered sections, prefixed with `>>> `.
