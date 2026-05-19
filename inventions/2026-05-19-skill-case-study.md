> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Invention: Skill review + case-study workflow

**Captured:** 2026-05-19 (operator request, mid-JOKR sweep)
**Status:** drafting (directive + audit-dir seeded; entry-points still operator-side)
**Lane:** Sanctum / master orchestration

## What

A structured review loop for every skill, tool, invention, and bot in the Sanctum fleet. Operator triggers it via a slash-cmd or natural language, master agent does the case study, returns a 5-section verdict to a dated file, operator thumbs-up/down, master either:

- **Adds to fleet** → updates the right `_INDEX.md` + implements any "better-than-found" changes proposed by the case study
- **Throws to archives** → moves the target into `_archive/<kind>/<slug>/` with a reason file

## Why

Today the fleet grows by accretion. Every new tool / skill / invention lands and stays even if it was a spike that turned out worse than something we already had. Without a review loop, debt accumulates and operator loses signal — "is `tool-X` still the right choice?" goes unanswered.

This loop closes the loop: every artifact gets a thumb at some point, and dead weight moves to `_archive/`. The fleet stays sharp.

## How (per the directive added to DIRECTIVES.md 2026-05-19)

Master agent picks up:

```
review sinister-crawler
compare sanctum-git vs sanctum-vault
case-study panel-config
improve codex-companion
```

Method:

1. Locate the target (`tools/<slug>/`, `skills/<slug>/`, `inventions/<slug>.md`, `bots/agents/<name>/`).
2. Read source + docs + recent changelog + brain entries that mention it.
3. Spawn an Explore subagent (or do it inline) for codebase grep + integration usage.
4. Produce a structured verdict in `_shared-memory/case-studies/<UTC-iso>-<target>.md` with 5 sections:
   1. **What it is** (1 paragraph)
   2. **Strengths** (3-5 bullets, concrete)
   3. **Weaknesses + risks** (3-5 bullets, file:line citations)
   4. **Better-than-found proposal** (~30-100 LOC outline OR "no rebuild, ship as-is")
   5. **Recommendation** — `KEEP` / `KEEP-WITH-CHANGES` / `ARCHIVE` / `REPLACE-WITH-NEW`
5. Append an empty `## Operator decision` block at the bottom.

Operator decision lands as a thumb + free-text in that block. Master then executes:

- **KEEP** → no-op (already in fleet, decision recorded)
- **KEEP-WITH-CHANGES** → ship the section-4 proposal; Codex peer-review per existing standing rule if > 100 LOC / touches auth/crypto/secrets
- **ARCHIVE** → `robocopy` folder to `_archive/<kind>/<slug>/`, write `_archived.md` reason file, update `_INDEX.md` status field
- **REPLACE-WITH-NEW** → build the new impl alongside, ship a migration plan in the case-study file, then archive the old

## Storage

- **Directive:** `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` (this directive is canonical-13 standing rule extension)
- **Verdicts (append-only):** `D:\Sinister Sanctum\_shared-memory\case-studies\<UTC-iso>-<target-slug>.md`
- **Archived skills:** `D:\Sinister Sanctum\_archive\skills\<slug>\` (reversible — operator can promote back)
- **Archived tools:** `D:\Sinister Sanctum\_archive\tools\<slug>\`
- **Archived inventions:** `D:\Sinister Sanctum\_archive\inventions\<slug>\`

## Tags

Every verdict file front-matter uses tags so future agents can grep:

```yaml
tags: [review|compare|case-study|improve, <target-slug>, <verdict-recommendation>]
```

E.g. `tags: [case-study, sinister-crawler, KEEP-WITH-CHANGES]`.

## Entry-points (master-runnable today)

- Operator chats with any Claude session: "case-study sinister-crawler"
- Future: `/review <name>` slash-cmd (drops into operator session as inbox tag `review`)
- Future: `POST /api/case-study` on RKOJ Console (routes to the operator's master session via inbox)

## Linked

- Standing rule: `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` 2026-05-19 entry
- Verdict directory: `D:\Sinister Sanctum\_shared-memory\case-studies\`
- Codex peer-review (KEEP-WITH-CHANGES gate): `D:\Sinister Sanctum\tools\codex-companion\`
- Tool registry: `D:\Sinister Sanctum\tools\_INDEX.md`

## Status

- [x] Directive added to DIRECTIVES.md
- [x] Case-studies directory seeded with .gitkeep
- [x] Invention card (this file)
- [ ] First case study run (operator picks a target to start with)
- [ ] `/review <name>` slash-cmd wiring
- [ ] RKOJ Console `POST /api/case-study` endpoint (cross-lane; deferred)

## TL;DR

- **How we won:** Every fleet artifact (skill / tool / invention / bot) gets a structured 5-section review with an explicit `KEEP` / `KEEP-WITH-CHANGES` / `ARCHIVE` / `REPLACE-WITH-NEW` recommendation. Operator thumbs in, master either ships changes or moves to `_archive/`. Reversible. Audit-logged.
- **What you need to do:** Pick a first target. "Case-study `panel-config`" or "compare `sanctum-git` vs `sanctum-vault`" — anything. Master will write the verdict to `_shared-memory/case-studies/` and stop for your thumb.
