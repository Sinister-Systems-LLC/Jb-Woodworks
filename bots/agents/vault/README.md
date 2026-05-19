<!-- Author: Sinister Sanctum / vault MCP agent (operator: sinistersocks5g@gmail.com) -->
# Vault agent

Tier-1 (pure Python) MCP façade over the Sinister Vault stack:

- **Vault daemon** at `http://127.0.0.1:5078` (quota, audit, snapshot)
- **Gitea** at `http://127.0.0.1:3000/api/v1` (repos, commit, push, pull)
- **Syncthing** at `http://127.0.0.1:8384/rest` (folder sync state)
- Local filesystem rooted at `D:\sinister-vault\`

One MCP namespace (`vault.*`) so any Claude session — including RKOJ-spawned
agents — has a single, predictable tool surface for "talk to the vault."

## Tools

| Tool | What |
|---|---|
| `vault.health()` | Aggregate status across daemon + Gitea + Syncthing |
| `vault.list(path="", depth=1)` | Browse `D:\sinister-vault\<path>` |
| `vault.audit(limit=50, kind=None)` | Tail vault daemon's audit log |
| `vault.commit(repo, file_path, message, account="operator")` | Add + commit + push a file to a Gitea repo |
| `vault.push(repo, branch)` | Push the working tree of a repo |
| `vault.pull(repo, branch)` | Pull a remote branch |
| `vault.search(query, limit=20)` | Substring grep across all repos + sync folder |
| `vault.sync_status()` | Per-folder Syncthing state + completion + conflicts |
| `vault.accounts()` | Enumerate `D:\sinister-vault\accounts\<name>` + HWID binding |
| `vault.snapshot(subtree="repos")` | Trigger an on-demand vault snapshot |

Every tool returns a JSON dict shaped `{ok: bool, ...}`. When a backend
(daemon, Gitea, Syncthing) is offline the tool returns `{ok: false, error: "..."}`
with a hint about which install script to run — it never raises.

## Setup

```powershell
cd "D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\vault"
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### Dependencies (out-of-band, NOT installed by this bot)

1. Vault daemon — `D:\Sinister Sanctum\tools\sinister-vault\install-vault-task.ps1`
2. Gitea — already in `D:\Sinister Sanctum\tools\sanctum-git\` (Gitea token in `.env`)
3. Syncthing — installed by operator; API key in `%LOCALAPPDATA%\Syncthing\config.xml`

## Registering with Claude Code

The fleet installer `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\install-fleet.ps1`
does NOT auto-register `vault` — its agent list does not yet include it.

### Option A — re-run the installer with the vault agent included

After the vault daemon ships:

```powershell
& "D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\install-fleet.ps1" `
    -Agents sentinel,translator,librarian,watcher,auditor,sinister-bus,`
    triage,scribe,curator,custodian,stealth-browser,researcher,vault
```

Then restart Claude Code.

### Option B — manual entry in `~/.claude/.mcp.json`

Add this block to the `mcpServers` object:

```json
"vault": {
  "command": "D:\\Sinister\\Sinister Skills\\12_LLM_ORCHESTRATION\\agents\\vault\\.venv\\Scripts\\python.exe",
  "args": ["server.py"],
  "cwd": "D:\\Sinister\\Sinister Skills\\12_LLM_ORCHESTRATION\\agents\\vault",
  "env": {
    "SINISTER_HUB_ROOT": "D:\\Sinister\\Sinister Skills",
    "VAULT_ROOT": "D:\\sinister-vault",
    "VAULT_DAEMON_URL": "http://127.0.0.1:5078",
    "GITEA_URL": "http://127.0.0.1:3000",
    "GITEA_ENV_FILE": "D:\\Sinister Sanctum\\tools\\sanctum-git\\.env",
    "SYNCTHING_URL": "http://127.0.0.1:8384",
    "SYNCTHING_CONFIG": "%LOCALAPPDATA%\\Syncthing\\config.xml"
  }
}
```

Restart Claude Code so the new MCP entry is loaded.

## Verify after registering

From any Claude session:

```
vault.health
vault.list path="" depth=1
vault.sync_status
vault.accounts
```

`vault.health` will report `vault_online`, `gitea_online`, `syncthing_online`
individually so you can tell which dependency is missing without parsing
error strings.

## Environment variables (all optional — sensible defaults)

| Var | Default |
|---|---|
| `VAULT_ROOT` | `D:\sinister-vault` |
| `VAULT_DAEMON_URL` | `http://127.0.0.1:5078` |
| `GITEA_URL` | `http://127.0.0.1:3000` |
| `GITEA_API_TOKEN` | (read from `GITEA_ENV_FILE` if unset) |
| `GITEA_ENV_FILE` | `D:\Sinister Sanctum\tools\sanctum-git\.env` |
| `SYNCTHING_URL` | `http://127.0.0.1:8384` |
| `SYNCTHING_API_KEY` | (read from `SYNCTHING_CONFIG` if unset) |
| `SYNCTHING_CONFIG` | `%LOCALAPPDATA%\Syncthing\config.xml` |
| `VAULT_GIT_DEFAULT_BRANCH` | `main` |
| `VAULT_USAGE_LOG` | `<HUB>\12_LLM_ORCHESTRATION\runtime-state\token-usage.jsonl` |

## Path note

`D:\Sinister Sanctum\bots\agents\` is a symlink to
`D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\` — so this folder is
visible at both locations with a single source of truth. No junction-creation
step is required.
