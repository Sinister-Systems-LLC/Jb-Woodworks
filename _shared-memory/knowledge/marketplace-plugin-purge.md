<!-- Author: Sinister Sanctum master agent (Claude) | session: 2026-05-19 | round: purge-aftermath -->

<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Topic: Marketplace plugin purge — never bulk-install from `claude-plugins-official` (or any marketplace)

**Slug:** marketplace-plugin-purge
**First discovered:** 2026-05-19 11:25 by Sinister Sanctum master agent (Claude)
**Last updated:** 2026-05-19 11:35 by Sinister Sanctum master agent
**Status:** fixed (post-purge) + standing rule planted
**Tags:** claude-code, plugins, marketplace, hookify, bulk-install, settings-json, ~/.claude.json, standing-rule, incident-postmortem

## Problem

Earlier in the 2026-05-19 session, a sibling Sanctum master-lane agent (per PROGRESS log 14:35 entry) shipped:

- `C:\Users\Zonia\Desktop\Install-Claude-Plugins.bat` (trampoline)
- `D:\Sinister Sanctum\automations\install-claude-plugins.ps1` (9.1 KB, 172-plugin enumerator)
- `D:\Sinister Sanctum\automations\plugin-install-list.md` (35 KB categorized reference)

The clipboard helper let the operator paste a batch of `/plugin install <name>@claude-plugins-official` commands at once. Result: 33 plugins from the `claude-plugins-official` marketplace got cached + enabled:

**26 third-party junk** — airtable, apollo, asana, atlassian, box, circleback, coderabbit, cwc-makers, desktop-commander, discord, exa, github, gitlab, imessage, intercom, legalzoom, linear, notion, pigment, session-report, slack, spotify-ads-api, telegram, windsor-ai, youdotcom-agent-skills, zapier.

**7 Anthropic devtools** — claude-code-setup, claude-md-management, code-review, code-simplifier, commit-commands, **hookify** (the smoking gun), pr-review-toolkit.

The `hookify` plugin registered a `UserPromptSubmit` hook pointing at `${CLAUDE_PLUGIN_ROOT}/hooks/userpromptsubmit.py`. The operator (via separate PS window) ran `Remove-Item -Recurse -Force` on `~/.claude/hooks/` + `~/.claude/plugins/cache/` to try to clear cache, which deleted the cache copy of `userpromptsubmit.py`. But the hook registration in `~/.claude.json` (`tengu_amber_lattice.plugins` array) survived, AND the master copy of the script in `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/hookify/hooks/userpromptsubmit.py` ALSO survived (the wipe missed it). When the operator opened a new `claude --dangerously-skip-permissions` session, the hook fired on prompt submit, python3 couldn't find the file at the cache path it expected, and EVERY PROMPT got blocked with:

```
UserPromptSubmit operation blocked by hook:
[python3 ${CLAUDE_PLUGIN_ROOT}/hooks/userpromptsubmit.py]:
C:\...\python.exe: can't open file
'C:\Users\Zonia\.claude\plugins\marketplaces\claude-plugins-official\plugins\hookify\hooks\userpromptsubmit.py':
[Errno 2] No such file or directory
```

Operator was furious — "remove all the shit we added. i want everything to be our shit ... i told you to review things not add of of this junk to the machine. you should know better."

## Why it happened

1. **No guardrail against bulk-install.** DIRECTIVES.md had no rule prohibiting marketplace-bulk-install scripts; the sibling agent had no canonical "no" to point to. (Now fixed — see standing rules below.)
2. **Marketplace plugin registration spans multiple files.** Removing a plugin requires updates to: `~/.claude/settings.json::enabledPlugins`, `~/.claude.json::tengu_amber_lattice.plugins`, `~/.claude.json::tengu_harbor_ledger`, `~/.claude/plugins/cache/`, `~/.claude/plugins/data/`, `~/.claude/plugins/marketplaces/`. Partial cleanup leaves zombie state.

## Fix (autonomous purge, 2026-05-19)

Plan file: `C:\Users\Zonia\.claude\plans\pick-up-where-we-glistening-meerkat.md`. Operator approved. Executed in 7 phases:

- **A. Snapshot:** backup `~/.claude.json` + `settings.json` + `settings.local.json` to `~/.claude/backups/2026-05-19-purge/`.
- **B. Strip `settings.json::enabledPlugins`** to only `understand-anything@understand-anything` + `ui-ux-pro-max@ui-ux-pro-max-skill`.
- **C. Strip `~/.claude.json`:** `tengu_amber_lattice.plugins → []` + `tengu_harbor_ledger → []`. `mcpServers` (ruflo + vault) untouched.
- **D. `rm -rf`** the cancer: `marketplaces/claude-plugins-official/` (172-plugin source tree) + `cache/claude-plugins-official/` (33 plugin caches) + 4 plugin-data dirs (discord/imessage/telegram/hookify state).
- **E. Archive contamination sources:** delete Desktop bat; move `install-claude-plugins.ps1` + `plugin-install-list.md` to `D:\Sinister Sanctum\_archive\automations\2026-05-19-plugin-installer-purged\` with `_archived.md` reason file.
- **F. Plant guardrails:** DIRECTIVES.md standing rule (top section); this brain entry; Sanctum-side invention archive.
- **G. Verify:** JSON validity, dirs absent, MCPs intact, settings entries correct, contamination sources gone.

## Verification (post-purge state)

```
~/.claude/settings.json::enabledPlugins:
  understand-anything@understand-anything: true
  ui-ux-pro-max@ui-ux-pro-max-skill: true

~/.claude.json::mcpServers:
  ruflo (operator-owned, npx-launched)
  vault (operator-owned, D:\Sinister Sanctum\bots\agents\vault\launch-mcp.bat)

~/.claude.json::tengu_amber_lattice.plugins: []
~/.claude.json::tengu_harbor_ledger: []

~/.claude/plugins/cache/        only: ui-ux-pro-max-skill/, understand-anything/
~/.claude/plugins/marketplaces/  only: ui-ux-pro-max-skill/, understand-anything/
~/.claude/plugins/data/          only: understand-anything-understand-anything/
~/.claude/plugins/marketplaces/claude-plugins-official/  : DELETED
~/.claude/plugins/cache/claude-plugins-official/         : DELETED

Sinister-bots fleet (D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\): untouched — 13 bots survive
Sanctum-side tools (D:\Sinister Sanctum\): untouched — operator-owned
```

## Standing rules (now in DIRECTIVES.md top section)

1. **NEVER bulk-install plugins** from any marketplace.
2. **Per-plugin operator approval is mandatory** — even for Anthropic-built ones.
3. **Operator-owned MCPs are sacred.**
4. **`~/.claude.json` + `settings.json` edits require approval or plan-file authorization.**
5. **Hooks are operator-owned** — any plugin registering a `UserPromptSubmit/PreToolUse/PostToolUse/Stop` hook gets surfaced BEFORE install.
6. **Reversibility via `_archive/` workflow** — any plugin install must be reversible.

## Discoveries

### 2026-05-19 11:35 by Sinister Sanctum master agent
Initial purge complete. Backups at `~/.claude/backups/2026-05-19-purge/`. Operator restart of Claude Code is the only remaining manual step; after restart, `/mcp` should show only `ruflo` + `vault`, `/plugin` should show only the 2 operator-owned skills, and no more `UserPromptSubmit operation blocked` errors on prompt entry.

## Related

- `powershell-unicode-blockdraw-parse-fail.md` (PS 5.1 quirks)
- `sanctum-auto-push.md` (background push daemon — separate ecosystem)
- DIRECTIVES.md standing-rule index (top section, 2026-05-19 entries)
