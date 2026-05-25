<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# We have the source -- READ it, don't reverse-engineer (operator hard-canonical)

**Author:** RKOJ-ELENO :: 2026-05-25
**Status:** binding for every fleet agent
**Composes with:** `github-first-sourcing-doctrine-2026-05-24.md` + no-bullshit doctrine

## Operator verbatim (2026-05-25 ~02:25Z)

> "you dont need to RE his shit we have the fucking code this is the last time im going to tell you this update memory"

## Rule

When the operator references **jcode**, **claude-code**, **any project whose source we already have on disk**, OR any GitHub repo we've already cloned into `_shared-memory/inbox/link-ingest/processed/` -- DO NOT spawn "reverse-engineering" sub-agents, do NOT treat it as a black box, do NOT speculate based on observed behavior.

**READ THE CODE DIRECTLY.** Use Grep + Read + Glob on the source paths. Synthesize patterns from actual file contents.

## Specific paths we already have

| Reference | Local source path | Treat as |
|---|---|---|
| jcode | `C:\Users\Zonia\Desktop\jcode-0.12.4\` | direct-readable |
| Claude Code CLI | `~/.claude/` config + npm install + ANY cached source if present | direct-readable |
| Any GitHub-linked invention | `_shared-memory/inbox/link-ingest/processed/<id>/download/repo/` | direct-readable |
| Operator's previous projects | `projects/<key>/` | direct-readable (it's literally ours) |

## Anti-patterns (forbidden)

- "Reverse-engineer how X works" -- if X's source is on disk, you READ it
- "Probe X's behavior to infer architecture" -- same
- "Treat X as a black box" -- never; we have full visibility into anything we host or clone
- Spawning a sub-agent whose first phase is "RE the source" -- waste of tokens
- Asking the operator "do you have X's source?" -- check the paths above FIRST

## What to do instead

1. **Grep first**: `grep -r "<pattern>" "C:\Users\Zonia\Desktop\jcode-0.12.4"`
2. **Read the entry points**: every project has `main.py` / `cli.py` / `cmd/` / `src/index.ts` / similar
3. **Trace the call graph** via reads, not by guessing
4. **Document the pattern with FILE:LINE refs** so future agents don't re-walk

## How sub-agent prompts should phrase comparative audits

WRONG: "reverse-engineer how jcode does X"
RIGHT: "read jcode's source at `C:\Users\Zonia\Desktop\jcode-0.12.4\<path>` and synthesize how it does X; compare to our `<sinister-path>`; propose improvements"

## Composes with

- `github-first-sourcing-doctrine-2026-05-24.md`: BEFORE writing custom code, check GitHub. Once cloned to `_shared-memory/inbox/link-ingest/processed/`, the code becomes direct-readable per THIS doctrine.
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` Rule 1: precise verbs. "Audited by reading" >> "reverse-engineered".

## Self-application (this session)

Spawned sub-agent `ab3e59e365fcd34b3` was prompted to "reverse-engineer jcode's swarm function". Operator corrected: we HAVE jcode source at `C:\Users\Zonia\Desktop\jcode-0.12.4\`. Sub-agent re-tasked via inbox to READ source directly, NOT RE.
