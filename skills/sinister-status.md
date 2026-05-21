---
name: sinister-status
description: Run the standard Sanctum cold-start status check (heartbeats, inbox, brain, PROGRESS)
allowed-tools: [bash, read_file, glob_search]
---
# Active Skill: sinister-status

Run the standard Sanctum cold-start status check. This is the one-shot summary
EVE produces when the operator opens a new session or asks "what's the state
of the fleet right now?"

## Steps (do all of these, then summarize)

1. **Heartbeats** — `glob` `D:/Sinister Sanctum/_shared-memory/heartbeats/*.json`.
   For each file, read mtime. Live = under 30 minutes old. Stale = over.
   Report: live count, stale count, the stalest slug.

2. **Inbox** — `glob` `D:/Sinister Sanctum/_shared-memory/inbox/*/*.json`. Group
   by project lane (the parent dir name). Report unread counts per lane and
   pull the three most-recent message titles (read each JSON's `subject` /
   `topic` field).

3. **Brain (knowledge index)** — read
   `D:/Sinister Sanctum/_shared-memory/knowledge/_INDEX.md` and summarize the
   five most recent entries (those tagged with the latest dates).

4. **PROGRESS** — for each file in
   `D:/Sinister Sanctum/_shared-memory/PROGRESS/`, read the top three lines
   under the most-recent `## ` heading. Report per-agent.

5. **Operator action queue** — read
   `D:/Sinister Sanctum/_shared-memory/OPERATOR-ACTION-QUEUE.md` and list any
   open `[ ]` items at the top of the file.

## Output format

Single concise block, four to seven bullet points total. No emojis. Use
project-display-names from PROGRESS files, not slugs, when addressing the
operator.

## Hard rules

- Never write to `_shared-memory/` from this skill — read-only audit.
- If `OPERATOR-ACTION-QUEUE.md` shows any item with `URGENT` or `BLOCKER`,
  surface it as the first line of output.
- Never invoke `git` from this skill. Use the dedicated `/git` slash-command
  if you need branch state.
