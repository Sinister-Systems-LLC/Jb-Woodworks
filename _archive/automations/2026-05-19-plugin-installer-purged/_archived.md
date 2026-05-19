<!-- Author: Sinister Sanctum master agent (Claude) | session: 2026-05-19 | archived: scope plugin-cancer-purge -->

# ARCHIVED 2026-05-19 — Plugin bulk-installer scaffolding

## Why archived

A sibling Sanctum master-lane session shipped `Install-Claude-Plugins.bat` + the 9.1KB `install-claude-plugins.ps1` + a 35KB `plugin-install-list.md` enumerating 172 plugins from `claude-plugins-official` marketplace, intended as a clipboard-helper for the operator to bulk-paste `/plugin install` commands into Claude Code.

The result was scaffolding for a class of operation the operator does NOT want — 26 third-party plugins (asana, discord, github, gitlab, imessage, linear, telegram, slack, notion, airtable, atlassian, box, circleback, coderabbit, cwc-makers, desktop-commander, exa, intercom, legalzoom, pigment, session-report, spotify-ads-api, windsor-ai, youdotcom-agent-skills, zapier, apollo) + 7 Anthropic devtools (code-review, commit-commands, code-simplifier, hookify, pr-review-toolkit, claude-code-setup, claude-md-management) got cached/enabled. The broken `hookify/userpromptsubmit.py` then began blocking every prompt with `[Errno 2] No such file or directory` — confirming the install was uncoordinated + the operator was upset.

Operator (verbatim, 2026-05-19): "remove all the shit we added. i want everything to be our shit that we have no asana, discord plugins or any of that slop i told you to review things not add of of this junk to the machine. you should know better."

## What was archived here

- `install-claude-plugins.ps1` (9.1 KB) — the 172-plugin clipboard helper
- `plugin-install-list.md` (35 KB) — the categorized 172-plugin reference (database 16, deployment 5, design 3, development 78, etc.)

`C:\Users\Zonia\Desktop\Install-Claude-Plugins.bat` was DELETED entirely (not archived) since it was just a trampoline pointing at the .ps1.

## Standing rule (planted in DIRECTIVES.md 2026-05-19)

**NEVER bulk-install plugins from any marketplace.** Per-plugin operator approval is mandatory — even for Anthropic-built marketplace tools. The operator says "review this plugin" via the case-study workflow; only then install.

See `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` (top section) + brain entry `D:\Sinister Sanctum\_shared-memory\knowledge\marketplace-plugin-purge.md`.

## Reversibility

If the operator ever explicitly asks for bulk install of a curated subset:
1. Restore the relevant .ps1 + .md from this archive
2. EDIT the list to only the operator-approved subset (NOT the full 172)
3. Run only with per-plugin operator thumbs in the case-study log

Backups of the original `~/.claude.json` + `settings.json` + `settings.local.json` are at `C:\Users\Zonia\.claude\backups\2026-05-19-purge\` if rollback is ever needed.
