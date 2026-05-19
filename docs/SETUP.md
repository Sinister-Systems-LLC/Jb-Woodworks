# Sinister LLC â€” setup (fresh machine)

## Prerequisites

- Windows 10/11
- Python 3.10+ (`python --version`)
- Docker Desktop (for Ollama; optional but recommended)
- Node.js 18+ (only if working on `projects/sinister-panel/` or `projects/library-of-alexandria/` UI)
- Git
- The Sinister external drive mounted as `D:\`

## One-shot bootstrap

```powershell
# Clone the LLC monorepo (one of these, operator decides)
git clone <REPO_URL> 'D:\Sinister Sanctum'
# OR if junctioned: it's already there.

cd 'D:\Sinister Sanctum'

# Junction the 8 Sinister projects from C:\Desktop into projects/
.\automations\migrate-projects.ps1

# Activate the 12-bot fleet (registers in ~/.claude/.mcp.json)
.\automations\activate-everything.ps1

# Secret-scrub (CONFIRM no secrets snuck in)
.\automations\secret-scrub.ps1
```

Restart Claude Code. Verify with `sinister-bus.list_network` -> expect **19 endpoints**.

## Tier-2 bots (Ollama)

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\docker'
.\setup.bat                    # docker compose up + initial pulls
docker exec -it ollama ollama pull nomic-embed-text qwen2.5:1.5b qwen2.5-coder:7b
```

After this: librarian, triage, researcher run in vector / synthesis mode (else degraded fallback).

## Tier-3 bots (Anthropic Haiku)

```powershell
[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
```

Restart Claude Code. Scribe + Curator unlock.

## Custodian 24/7 backup

```powershell
cd 'D:\Sinister Sanctum\bots\agents\custodian'  # junction back to hub
.\install-task.ps1
```

Two Windows scheduled tasks register (logon trigger + daily 03:00 restart). Verify:

```powershell
schtasks /Query /TN SinisterCustodian /V /FO LIST
```

Logs: `D:\_backups\_logs\custodian-<today>.log`.

## Smoke test

```
sinister-bus.health         -> total_endpoints: 19
sinister-bus.list_network   -> bots + base_mcps lists
custodian.health            -> snapshot_count > 0
sentinel.list_alarms        -> 3 default alarms
researcher.health           -> stealth_available + ollama_healthy
```

## TL;DR

- **How we won:** One command (`migrate-projects.ps1` + `activate-everything.ps1`) gets a fresh machine to a working 19-server MCP network.
- **What you need to do:**
  - Run the two scripts above.
  - Set `ANTHROPIC_API_KEY` if you want Scribe + Curator.
  - Run `install-task.ps1` for the 24/7 backup daemon.
