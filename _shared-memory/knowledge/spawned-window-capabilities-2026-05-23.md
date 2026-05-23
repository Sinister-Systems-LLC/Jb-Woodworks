<!-- Author: RKOJ-ELENO :: 2026-05-23 -->

# Spawned-window capabilities — 2026-05-23 read-only audit

> Status: doctrine, standing-rule, binding
> Tags: doctrine, standing-rule, binding, spawned-window-capabilities, mcp-fleet, agent-tool, parallel-subagents, local-bots, sinister-bus, 2026-05-23, audit

## Operator directive (verbatim 2026-05-23)

*"allow all windows to use parrallel agents and local agents. make sure our local agents and all features like that work"*

Binding for every EVE session spawned via `Sinister Start.bat` → `D:\Sinister Sanctum\automations\start-sinister-session.ps1` → `claude --dangerously-skip-permissions <phrase>`.

## What every spawned EVE has access to

| Capability | Surface | How it loads | Status |
|---|---|---|---|
| **Parallel sub-agents** | Claude Code built-in `Agent` tool (Explore, Plan, code-review, general-purpose) | Built into the `claude` CLI itself; available in every session that ran `claude --dangerously-skip-permissions` (which the launcher always uses) | OK — class-level, no per-spawn enablement |
| **Local bot fleet (MCP)** | `~/.claude/.mcp.json` mcpServers (12 Sinister bots + 11 third-party MCPs) | Claude reads `~/.claude/.mcp.json` on cold-start, spawns each MCP subprocess with its declared `cwd` + `env`, surfaces tools as `mcp__<server>__<tool>` | OK for 12/13 Sinister bots — see reachability matrix below |
| **Sanctum knowledge brain** | `D:\Sinister Sanctum\_shared-memory\knowledge\` (regular dir + `_INDEX.md` table) | Filesystem read/write; any session can grep/read/append | OK universally |
| **Cross-agent inbox** | `D:\Sinister Sanctum\_shared-memory\inbox\<slug>\*.json` + `sinister-bus.inbox_poll` MCP tool | Filesystem + MCP both reach the same dir | OK universally |
| **Heartbeats** | `D:\Sinister Sanctum\_shared-memory\heartbeats\<slug>.json` + `sinister-bus.heartbeat` MCP tool | Filesystem + MCP both reach the same dir | OK universally |
| **Resume-points** | `D:\Sinister Sanctum\_shared-memory\resume-points\<Slug>\<ts>.json` + close-hook `automations/resume-point-write.ps1` | Launcher v6.1 close-hook fires when claude exits; manual write any time | OK universally |
| **PROGRESS logs** | `D:\Sinister Sanctum\_shared-memory\PROGRESS\<Display>.md` (append-only, most-recent at top) | Plain markdown; any session edits | OK universally |
| **Skills (plugins)** | `understand-anything@understand-anything` + 30+ others (frontend-design, code-review, hookify, ui-ux-pro-max, claude-md-management, commit-commands, etc.) | `~/.claude/settings.json` `enabledPlugins[]` + Sanctum-level `.claude/settings.json` mirror | OK — protected by P2 in `do-not-revert-operator-canonical-protections-2026-05-23.md` |
| **Sandboxed Bash + PowerShell tools** | Built-in CLI; `--dangerously-skip-permissions` standing default | Launcher always passes the flag | OK |
| **Sanctum env vars in spawn shell** | `SINISTER_AGENT_NAME`, `SINISTER_ACCENT_COLOR`, `SINISTER_PROJECT_KEY`, `SINISTER_PROJECT_DISPLAY`, `SINISTER_MODE` | Exported by `Launch-Session` before `claude` invocation (lines 873-877 of `start-sinister-session.ps1`) | OK |

## Reachability matrix — `.mcp.json` audit 2026-05-23

23 MCP servers total registered in `~/.claude/.mcp.json` (sorted): `auditor, context7, curator, custodian, eve, letstext, letstext-admin, librarian, memory, playwright, researcher, scribe, sentinel, sequential-thinking, sinister-apk, sinister-bus, sinister-panel, sinister-snap, sinister-tiktok, stealth-browser, translator, triage, watcher`.

### Sinister bot fleet (12 entries verified loadable)

| Bot | Key | cwd exists | server.py present | Status |
|---|---|---|---|---|
| sentinel | `sentinel` | OK | OK (`D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\sentinel\server.py`) | loadable |
| librarian | `librarian` | OK | OK | loadable |
| translator | `translator` | OK | OK | loadable |
| watcher | `watcher` | OK | OK | loadable |
| auditor | `auditor` | OK | OK | loadable |
| sinister-bus | `sinister-bus` | OK | OK (`D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\sinister-bus\server.py` — verified 2026-05-23) | loadable |
| triage | `triage` | OK | OK | loadable |
| scribe | `scribe` | OK | OK | loadable |
| curator | `curator` | OK | OK | loadable |
| custodian | `custodian` | OK | OK | loadable |
| stealth-browser | `stealth-browser` | OK | OK | loadable |
| researcher | `researcher` | OK | OK | loadable |
| vault | (none in `.mcp.json` as `vault`/`sinister-vault`) | n/a | n/a | **GAP** — operator-queue item to wire it; tracked in `tools/sinister-vault/INSTALL-MCP.md` |

### Non-Sinister MCPs reachable in the same load (informational, third-party)

`context7, eve, letstext, letstext-admin, memory, playwright, sequential-thinking, sinister-apk, sinister-panel, sinister-snap, sinister-tiktok` — all currently registered. (`eve` points at `C:\Users\Zonia\Desktop\Sinister Library Of Alexandria\eve mcp\eve-server` — separate from the `EVE` persona; this is the eve-memory MCP server.)

### Disk hub + junction

- Hub: `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\` contains 14 entries (12 bots + `vault` folder + `_shared`).
- Junction: `D:\Sinister Sanctum\bots\agents` is a Windows Junction (`fsutil reparsepoint` confirms Mount Point tag `0xa0000003`) targeting `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents` — resolves correctly.

## Launcher spawn-flow audit (`start-sinister-session.ps1` Launch-Session)

Verified 2026-05-23 in `D:\Sinister Sanctum\automations\start-sinister-session.ps1` line 790 onward:

1. Line 871: `claude --dangerously-skip-permissions '$bashPhrase'` — required for MCPs to load without per-prompt approval. OK.
2. No `--no-mcp` / `--disable-mcp` / `--exclude-mcp` flags anywhere in the file (verified via grep). OK.
3. Lines 873-877 export the SINISTER_* env vars into the spawn shell before `claude` invocation. OK.
4. Pre-trusts the project folder in `~/.claude.json` (lines 800-826) so MCPs load without first-run trust dialog. OK.
5. No `.claude/settings.json` `disabledMcpServers` block — verified empty (settings.json has no `disabledMcpServers` / `enabledMcpServers` keys; defaults to "all enabled").

## The one-liner to restart Claude Code so newly-junction-resolved MCPs come online

Close every active Claude Code window then double-click `C:\Users\Zonia\Desktop\Start-Sinister-Session.bat` (or run from PowerShell):

```powershell
Get-Process -Name claude,mintty -ErrorAction SilentlyContinue | Stop-Process -Force; Start-Process "C:\Users\Zonia\Desktop\Start-Sinister-Session.bat"
```

Then in the picker, pick any lane (or `S` for Sanctum). New spawn will re-read `~/.claude/.mcp.json` and `~/.claude/settings.json` from scratch — any junctions resolved during the previous session take effect immediately.

## Anti-patterns

1. **Don't edit `~/.claude/.mcp.json` from a spawned agent** — operator-owned file; one bad edit kills every active session. Use `mklink /J` junctions to route around stale paths instead (`mcp-junction-fix-pattern-2026-05-23.md`).
2. **Don't assume `Agent` tool is an MCP** — it's a Claude Code built-in. No setup needed; never blocked.
3. **Don't manually start bot subprocesses** — Claude Code spawns them on cold-start. Pre-launching racing the harness's spawn = port collision + duplicate processes.
4. **Don't add a bot to `~/.claude/.mcp.json` without verifying the cwd + entry-point exist** — silent load failure with no surfaced error.
5. **Don't disable MCPs in `.claude/settings.json` `disabledMcpServers[]` "temporarily"** — gets forgotten, next operator session loses bots silently.

## Composes with

- `do-not-revert-operator-canonical-protections-2026-05-23.md` (P1, P2 protect the `--dangerously-skip-permissions` + plugin enablement that this audit depends on)
- `mcp-junction-fix-pattern-2026-05-23.md` (how 13 stale cwds were resolved without touching the operator-gated file)
- `sanctioned-bypasses-doctrine-2026-05-21.md` (`--dangerously-skip-permissions` is a sanctioned bypass, not a flag to avoid)
- `spawn-validation-end-to-end-2026-05-23.md` (the 4 spawn artifacts + 5 spawn surfaces this audit pre-supposes)
- `wake-on-demand-bot-dispatcher-2026-05-23.md` (proposed lazy-spawn pattern for the 12 always-on bots audited here)
- `agent-identity-eve.md` (EVE is the persona; MCP keys are lane identifiers)

## Empirical anchor

Audit performed 2026-05-23 from this Sanctum session at HEAD `73c628b` on branch `agent/sinister-sanctum/anti-revert-doctrine-2026-05-23`. All 12 Sinister bot folders enumerated via `Get-ChildItem`; junction confirmed via `Get-Item ... .LinkType` + `fsutil reparsepoint`; `.mcp.json` parsed via `ConvertFrom-Json`; `Launch-Session` function read at lines 790-880 of `automations/start-sinister-session.ps1`. Vault MCP gap matches the open item in `_shared-memory/OPERATOR-ACTION-QUEUE.md` ("Wire Vault MCP into `~/.claude/.mcp.json`").
