# Sinister Vault — MCP wire-up

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

The Vault daemon ships shipped + healthy at `127.0.0.1:5078`, but its MCP server (at `D:\Sinister Sanctum\bots\agents\vault\server.py`) is **NOT** currently registered in `~/.claude/.mcp.json`. Without that entry, no Claude session can call `vault.*` tools — the daemon is reachable, but not from inside agents.

This is the **one operator click** that bridges the gap. Lane discipline forbids master agents from hand-editing `~/.claude/.mcp.json` (a bad entry kills every active session in the fleet).

## What to run (operator, one time)

```powershell
# From any PowerShell window:
& "D:\Sinister Sanctum\tools\sinister-vault\wire-everything.ps1"
```

This script (idempotent — safe to re-run):

1. Sanity-checks the vault venv at `tools\sinister-vault\.venv\Scripts\python.exe`.
2. Registers the `SinisterVault` scheduled task (via `install-vault-task.ps1`).
3. Starts the task + waits 5 s for the daemon to bind to :5078.
4. Probes `GET http://127.0.0.1:5078/api/vault/health` (5 s timeout).
5. **Stages** the MCP entry at `D:\Sinister Sanctum\_vault\mcp-vault-entry-PROPOSED.json`.
6. Prints the merge instructions.

Then merge the staged entry into `~/.claude/.mcp.json` by hand (or use the Sanctum-side install-fleet.ps1 from the parent hub):

```powershell
# Option A — manual merge
notepad "$env:USERPROFILE\.claude\.mcp.json"
# Paste the contents of the staged file into the "mcpServers" object.

# Option B — re-run install-fleet (re-registers ALL 13 bots, vault included)
& "D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\install-fleet.ps1"
```

Then **restart Claude Code** so the new server loads. After restart, any session can call:

| Tool | Purpose |
|---|---|
| `vault.health` | Daemon liveness, uptime, quota headline |
| `vault.list` | Sandboxed recursive listing of a sub-tree |
| `vault.audit` | Tail the unified audit JSONL log |
| `vault.commit` | Record a commit-as-upload event (operator/leo identity) |
| `vault.push` / `vault.pull` | Audit-logged push/pull operations |
| `vault.search` | Search across vault sub-trees |
| `vault.sync_status` | Syncthing sync state |
| `vault.accounts` | List multi-account profiles (operator + leo) |
| `vault.snapshot` | Robocopy a sub-tree into `snapshots/` |

## Verification

After restart, in any fresh Claude session:

```
# Search for the vault tool schema
ToolSearch select:vault.health
# Expected: schema returned, status: available
```

If `vault.health` doesn't appear in search results, the registration didn't land. Check:

- `~/.claude/.mcp.json` has a `"vault": { ... }` entry under `mcpServers`.
- The entry's `cwd` points at `D:\Sinister Sanctum\bots\agents\vault`.
- The entry's `command` resolves (likely `python` with `server.py` arg, or the venv python).
- Claude Code was actually restarted (not just the terminal — the whole desktop app).

## Why this matters

Until the MCP entry lands, the entire SV-D track from the 2026-05-19 sprint is "shipped-but-disconnected." 30 KB of server code is unreachable. The vault daemon serves only RKOJ's `/api/vault/*` proxies and the operator-visible Vault drawer. Every Claude session is blind to it.

Per the runtime-readiness audit ("HR-B" + later sweeps), this is the highest-leverage operator click of the open queue:
- Cost: ~3 minutes (script run + manual merge + restart).
- Impact: unlocks vault.* tools in every Claude session, enables agent-level commit/push/audit logging into the unified vault store.

## See also

- `tools/sinister-vault/README.md` — vault daemon overview + tree + HTTP surface
- `tools/sinister-vault/AUTOSTART.md` — scheduled task lifecycle
- `bots/agents/vault/README.md` — MCP server design
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` — this is item "Register Vault MCP" in the 🟠 high bucket
- `_shared-memory/knowledge/sinister-vault-architecture.md` — full architecture brain entry
