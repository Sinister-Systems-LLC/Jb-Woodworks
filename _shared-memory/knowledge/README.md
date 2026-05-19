> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# _shared-memory/knowledge/ — the Sanctum brain

This folder is the **shared, growing knowledge base** for every Claude session in the Sinister fleet. When ANY agent (master, snap-emu, tiktok-emu, panel, kernel-apk, ephemeral) discovers a gotcha, a bug, a workaround, or ships a fix — they append it here. Every agent reads from here on cold-start. The brain accumulates across sessions; nothing useful is ever lost.

## Why this exists

In a single Claude session, you spend 15 minutes solving a problem. Maybe you find that GitHub Actions silently fails when you push without the `workflow` OAuth scope. Or that scrcpy creates a VirtualDisplay Snapchat detects. Or that PowerShell's `Read-Host ""` (empty prompt) crashes with "name cannot be null".

The next agent that hits the same wall — different project, different week, maybe Leo's machine — should NOT have to rediscover it. The fix should be in their cold-start context, ready to apply.

That's what this folder is. **A growing brain.** One .md file per topic. Append-only. Every entry timestamped + authored.

## How it works

```
_shared-memory/knowledge/
├── README.md                         (this file)
├── _INDEX.md                         (catalog of all topics, auto-maintained)
├── _TEMPLATE.md                      (copy this for a new topic)
├── github-auth-workflow-scope.md     (example: how to grant the workflow scope)
├── scrcpy-virtual-display.md         (why Snapchat detects scrcpy mirroring)
├── powershell-readhost-empty.md      (Read-Host '' crashes; use Read-Host ' ' or 'prompt')
├── adb-containerization.md           (per-phone container model)
└── ...                               (more topics appended forever)
```

Each topic file has a standard skeleton (see `_TEMPLATE.md`):

```markdown
# Topic: <one-line title>

**Slug:** <kebab-case-slug-matching-filename>
**First discovered:** YYYY-MM-DD HH:MM by <agent-name>
**Last updated:** YYYY-MM-DD HH:MM by <agent-name>
**Status:** open | known-issue | workaround | fixed | superseded
**Tags:** comma, separated, tags

## Problem

What goes wrong, in plain English. Include error messages verbatim.

## Why it happens

Root cause. Reference docs / source code paths.

## Fix or workaround

Concrete steps. Code / commands. Tested or untested.

## Discoveries (append-only log, most-recent at top)

### YYYY-MM-DD HH:MM by <agent-name>
What you found. New evidence. Edge case. Better fix.

### YYYY-MM-DD HH:MM by <agent-name>
Earlier discovery.
```

## How agents write here

On cold-start, every Claude session reads `DIRECTIVES.md` which says:

> When you discover a bug / gotcha / workaround / better-fix during your work,
> append it to `D:\Sinister Sanctum\_shared-memory\knowledge\<slug>.md`. If the
> topic doesn't exist yet, copy `_TEMPLATE.md` to create it. Most-recent
> discoveries at the top. Always sign with `SINISTER_AGENT_NAME` + timestamp.

Three ways an agent can write:

1. **Direct file write** — `_TEMPLATE.md` → copy → fill → save. Markdown.
2. **POST `/api/knowledge/append`** — if the Sanctum Console is up:
   ```json
   {
     "slug": "github-auth-workflow-scope",
     "agent": "Sinister Sanctum",
     "kind": "discovery",
     "title": "gh auth refresh -s workflow expands scope without rotating token",
     "body": "Running `gh auth refresh -h github.com -s workflow` adds the workflow scope to an existing token. Confirmed on operator's machine 2026-05-19. Token UUID unchanged afterward — no need to re-bind anything."
   }
   ```
3. **`C:\Users\Zonia\Desktop\Log-Knowledge.bat`** — operator-side one-click append.

## How agents read here

On every cold-start, the launcher's phrase tells the spawned Claude:

> "Before doing real work, scan `D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md` for topics relevant to your scope. If you're about to attempt something where the brain says 'known issue + workaround', apply the workaround."

Agents may also `GET /api/knowledge/{slug}` from the Sanctum Console at any time.

## Topic naming convention

- Lowercase, dash-separated, ≤ 50 chars
- Topic = what + where: `github-auth-workflow-scope` (what: workflow scope, where: github auth)
- NOT date-prefixed (this is knowledge, not a journal entry — date lives inside the file)
- Avoid project-specific naming unless the topic only applies to that project: prefer `kameleo-fingerprint-screen-min-1280` over `panel-kameleo-screen-bug`.

## Status lifecycle

- **open** — discovered but no fix yet
- **known-issue** — confirmed, documented, but not yet fixed (workaround exists)
- **workaround** — there's a workaround but not a real fix
- **fixed** — the fix shipped; agents should apply this fix automatically
- **superseded** — a newer topic supersedes this one (link to it)

## Anti-patterns

- ❌ Don't put time-sensitive operator instructions here — those go in DIRECTIVES.md
- ❌ Don't put per-agent progress notes here — those go in PROGRESS/<agent>.md
- ❌ Don't delete old discoveries — append, mark superseded if needed
- ❌ Don't duplicate topics — if uncertain, grep first (see "Discovery" section below)
- ❌ Don't write meta-knowledge here ("we use git" / "Python is good") — only actionable, fix-shaped knowledge

## Discovery (avoiding duplicates)

Before creating a new topic file, check if one already exists:

```bash
# from any agent's shell
grep -l "<your-keyword>" "D:\Sinister Sanctum\_shared-memory\knowledge\"*.md
```

Or `GET /api/knowledge?search=<query>` from the Sanctum Console.

If a topic exists, **append a new discovery to its log** rather than creating a duplicate.

## TL;DR

- One folder. Per-topic .md files. Append-only.
- Every Claude session writes new discoveries here + reads existing ones on cold-start.
- The brain grows forever. Nothing useful is lost.
- Operator + agents share this. Leo's keys also unlock it.
