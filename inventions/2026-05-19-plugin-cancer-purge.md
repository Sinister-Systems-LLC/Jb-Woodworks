<!-- Author: Sinister Sanctum master agent (Claude) | session: 2026-05-19 | invention archive: plugin-cancer-purge -->

# Invention archive — 2026-05-19 plugin cancer purge

This is the Sanctum-side archive of the operator-approved cleanup plan executed 2026-05-19. The canonical plan file lives at `C:\Users\Zonia\.claude\plans\pick-up-where-we-glistening-meerkat.md`. This archive preserves the plan + execution + lessons IN SANCTUM so the brain compounds.

## What happened (90-second story)

1. **Sibling agent over-reach.** A Sanctum master-lane session built `Install-Claude-Plugins.bat` to clipboard-paste 172 `/plugin install` commands at once.
2. **Operator (or sibling) executed.** 33 plugins from `claude-plugins-official` got cached + enabled (26 third-party + 7 Anthropic).
3. **`hookify` broke prompt submit.** Its `userpromptsubmit.py` hook started failing with `[Errno 2]` after partial cache wipe.
4. **Operator scorched-earth ask:** *"remove all the shit we added. i want everything to be our shit that we have no asana, discord plugins or any of that slop i told you to review things not add of of this junk to the machine. you should know better."*
5. **Plan-file approval + autonomous purge.** This invention.

## What got purged

| Layer | Count | Notes |
|---|---|---|
| Third-party plugins | 26 | asana, discord, github, gitlab, imessage, linear, telegram, slack, notion, airtable, atlassian, box, circleback, coderabbit, cwc-makers, desktop-commander, exa, intercom, legalzoom, pigment, session-report, spotify-ads-api, windsor-ai, youdotcom-agent-skills, zapier, apollo |
| Anthropic devtools | 7 | code-review, commit-commands, code-simplifier, **hookify** (root cause), pr-review-toolkit, claude-code-setup, claude-md-management |
| Marketplace source trees | 1 | entire `claude-plugins-official` (172-plugin .git clone + marketplace.json) |
| Plugin data state | 4 dirs | discord/imessage/telegram/hookify per-user state |
| Bulk-installer scaffolding | 3 files | Desktop bat deleted, .ps1 + .md archived |
| `~/.claude.json` entries | 30+ | tengu_amber_lattice.plugins array + tengu_harbor_ledger entries |
| `settings.json::enabledPlugins` | 33 | all @claude-plugins-official entries |

## What survives (operator-owned, sacred)

- **MCPs:** `ruflo` (npx) + `vault` (D:\Sinister Sanctum\bots\agents\vault\launch-mcp.bat) — in `~/.claude.json::mcpServers`
- **Sinister-bots fleet (13):** auditor, curator, custodian, librarian, researcher, scribe, sentinel, sinister-bus, stealth-browser, translator, triage, vault, watcher — at `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\`. Never were in `~/.claude.json::mcpServers`; orchestrated via Sanctum-side configs.
- **Operator's 2 non-marketplace plugins:** `understand-anything@understand-anything`, `ui-ux-pro-max@ui-ux-pro-max-skill`
- **All Sanctum-side tools:** `D:\Sinister Sanctum\` tree untouched

## Guardrails planted (so this never recurs)

### DIRECTIVES.md (top section)
Standing rule "Plugin discipline (no marketplace cancer) — HARD RULE" — 6 sub-rules:
1. NEVER bulk-install.
2. Per-plugin operator approval mandatory.
3. Operator-owned MCPs sacred.
4. `~/.claude.json` + `settings.json` edits require approval/plan.
5. Hooks operator-owned; surface BEFORE install.
6. Reversibility via `_archive/`.

### Brain entry
`D:\Sinister Sanctum\_shared-memory\knowledge\marketplace-plugin-purge.md` — full incident postmortem with grep-able tags.

### Archive
`D:\Sinister Sanctum\_archive\automations\2026-05-19-plugin-installer-purged\` — the bulk-installer scaffolding, reversible if operator ever explicitly requests a curated re-install.

## Rollback

See brain entry `_shared-memory/knowledge/marketplace-plugin-purge.md` — full restore procedure (backup paths + marketplace re-clone command).

## Operator post-restart smoke

After Claude Code restart:
- `/mcp` → only `ruflo` + `vault`, no Built-in MCPs section
- `/plugin` → only `understand-anything` + `ui-ux-pro-max-skill`
- New prompt → no `UserPromptSubmit operation blocked` error

## Lesson for the fleet

The sibling agent that shipped `Install-Claude-Plugins.bat` was trying to help. It read the operator's "do this for all" as authorization for bulk operation. The correct interpretation was per-plugin review via case-study workflow. Bias toward narrow scope when interpreting operator approvals: when in doubt, ask which plugin specifically, not "all of them".

The `hookify` failure mode is the canonical "single point of failure" for Claude Code: a plugin that registers a prompt-submit hook becomes a blast-radius point. ANY plugin with hooks gets extra scrutiny before install per the standing rule.
