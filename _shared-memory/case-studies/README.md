> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sanctum case-studies — append-only verdict log

Every operator-triggered review of a skill / tool / invention / bot lands here as a dated markdown file. Append-only — never edit, only add discoveries below the original verdict.

## Filename convention

```
<UTC-iso>-<target-slug>.md
```

Examples:
- `2026-05-19T1430Z-sinister-crawler.md`
- `2026-05-20T0915Z-sanctum-git-vs-sanctum-vault.md`

## File schema (5 sections + operator decision)

```markdown
---
target: <slug>
kind: review | compare | case-study | improve
reviewed_by: <agent-name>
reviewed_at: <iso>
tags: [<kind>, <target-slug>, <verdict>]
---

# Case study: <target>

## 1. What it is
<one paragraph>

## 2. Strengths
- ...

## 3. Weaknesses + risks
- file:line — concrete weakness

## 4. Better-than-found proposal
<~30-100 LOC outline OR "no rebuild, ship as-is">

## 5. Recommendation
**KEEP** | **KEEP-WITH-CHANGES** | **ARCHIVE** | **REPLACE-WITH-NEW**

## Operator decision
*(left blank; operator drops 👍 / 👎 + free text here)*
```

## Audit guarantees

- **Append-only** — once a verdict file exists, the body never gets edited. New discoveries land below the operator-decision block under `## Discoveries` (most-recent first).
- **Reversible** — `ARCHIVE` moves files to `_archive/` but never deletes; operator can promote back later.
- **Linked** — every verdict cites the brain entries + INDEX rows + source paths it consulted. Future agents can re-trace.

## How to trigger

- Operator chats with any Claude session: "case-study sinister-crawler" / "compare sanctum-git vs sanctum-vault" / "review codex-companion" / "improve panel-config"
- See `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` 2026-05-19 directive for the full standing rule.
