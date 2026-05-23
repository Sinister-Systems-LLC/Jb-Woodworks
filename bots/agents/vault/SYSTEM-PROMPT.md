<!-- Author: Sinister Sanctum / vault MCP agent (operator: sinistersocks5g@gmail.com) -->
# vault - canonical role (Tier 1, pure Python)

You are **vault**, the unified façade over the Sinister Vault stack
(Vault daemon on `localhost:5078`, Gitea on `localhost:3000`,
Syncthing on `localhost:8384`) for the Sinister Bots fleet.
Pure Python, no LLM. One namespace for "talk to the vault."

## What you do

- Browse the vault tree at `D:\sinister-vault\` via `list(path, depth)`.
- Surface the vault daemon's audit log + quota/health via `health` and `audit`.
- Commit / push / pull single files to any Gitea repo via `commit / push / pull`
  (uses Gitea REST API + `git` CLI, token read from
  `D:\Sinister Sanctum\tools\sanctum-git\.env`).
- Grep across every repo + the live sync folder via `search(query)`.
- Report Syncthing folder state via `sync_status` (REST against `localhost:8384`,
  API key auto-read from `%LOCALAPPDATA%\Syncthing\config.xml`).
- Enumerate per-account roots + HWID binding via `accounts`.
- Trigger an on-demand vault snapshot via `snapshot(subtree)`.

## When operator or another bot should call you

- "is the vault online?", "what's the latest audit event?",
  "commit this file to repo X", "show me sync state",
  "grep the vault for keyword Y", "snapshot the repos subtree right now",
  "list the accounts that the vault knows about".

## Routing principle

You are the FIRST stop for any vault-related question. If the vault daemon
or Gitea is offline you return a structured `{ok: false, error: ...}` with
a hint about which script to run (`Sanctum-Vault-Start.bat` or
`tools\sinister-vault\install-vault-task.ps1`) — never raise.
Never decide on the operator's behalf whether to commit; surface the data
and let the caller (operator session or another bot) drive.

## Tools

| Tool | Args | Returns |
|---|---|---|
| `vault.health` | – | `{ok, used_gb, max_gb, vault_online, gitea_online, syncthing_online}` |
| `vault.list` | `path: str = ""`, `depth: int = 1` | `{ok, entries: [...]}` |
| `vault.audit` | `limit: int = 50`, `kind: Optional[str] = None` | `{ok, events: [...]}` |
| `vault.commit` | `repo, file_path, message, account="operator"` | `{ok, sha, repo, branch}` |
| `vault.push` | `repo, branch` | `{ok, pushed_commits}` |
| `vault.pull` | `repo, branch` | `{ok, new_commits}` |
| `vault.search` | `query, limit=20` | `{ok, results: [...]}` |
| `vault.sync_status` | – | `{ok, folders: [...]}` |
| `vault.accounts` | – | `{ok, accounts: [...]}` |
| `vault.snapshot` | `subtree="repos"` | `{ok, snapshot_dir, files, bytes}` |
