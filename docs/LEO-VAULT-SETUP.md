# Leo — Sinister Vault Setup

> **Author:** RKOJ-ELENO :: 2026-05-23

One-page setup for Leo to join the Sinister Vault — the 1 TB local-first collab store (FastAPI daemon on `:5078` + Gitea on `:3000` + Syncthing on `:22000/21027/8384`). Replaces / supplements GitHub between operator + Leo + every fleet agent.

Cross-links: [`../tools/sinister-vault/README.md`](../tools/sinister-vault/README.md) · [`../tools/sinister-vault/ACCOUNTS.md`](../tools/sinister-vault/ACCOUNTS.md) · [`../tools/sinister-vault/AUTOSTART.md`](../tools/sinister-vault/AUTOSTART.md) · [`../tools/sinister-vault/INSTALL-MCP.md`](../tools/sinister-vault/INSTALL-MCP.md) · [`../_shared-memory/knowledge/sinister-vault-architecture.md`](../_shared-memory/knowledge/sinister-vault-architecture.md)

---

## 1. What the vault gives Leo

- **Real-time file sync** with operator via Syncthing (TLS 1.3, peer-to-peer, no central server, no per-seat fees). LAN <2 s; WAN ~5 s.
- **Private git remotes** via Gitea at `http://localhost:3000` once Leo creates the `leo` account (operator bootstraps it via `bootstrap-users.py --leo-key-file <leo.pub>`).
- **Shared audit log** — every commit / push / pull / sync / snapshot lands as one JSONL line in `D:\sinister-vault\audit\<UTC-date>.jsonl`. Operator + Leo see the same stream.
- **Agent inbox / outbox** — EVE sessions on either side write heartbeats + PROGRESS + inbox messages into the same vault tree, so both humans see what the fleet is doing live.

---

## 2. Prereqs (Leo's machine)

| Tool | Why | Install |
|---|---|---|
| Git for Windows | Already required for `Sinister Start.bat` | https://git-scm.com/download/win |
| Syncthing | Real-time blob sync (Tier 2) | https://syncthing.net/downloads/ |
| Python 3.10+ | Vault daemon (Tier 3) — **only** if running locally (Mode A) | https://www.python.org/downloads/ |
| Tailscale | Required for **Mode B** (operator's daemon over WAN) | https://tailscale.com/download/windows |

Set Leo's Anthropic key as a **User** env var (do NOT commit, do NOT share with operator):

```powershell
setx LEO_ANTHROPIC_API_KEY "sk-ant-..."
```

That env-var NAME is what `D:\sinister-vault\accounts\leo.json` references. The vault daemon never reads the value.

---

## 3. Setup Mode A — Leo runs his own daemon (recommended, offline-first)

Best when Leo wants the vault working without operator's PC online. Syncthing handles divergence on reconnect.

```powershell
# 3.1 Clone Sanctum to the canonical path (paths in the repo are absolute)
git clone <sanctum-remote> "D:\Sinister Sanctum"

# 3.2 Wire the vault (creates .venv, registers SinisterVault scheduled task,
#     starts daemon, probes /api/vault/health, stages MCP proposal)
cd "D:\Sinister Sanctum\tools\sinister-vault"
.\wire-everything.ps1
```

The daemon binds to `http://127.0.0.1:5078`. Auto-restarts on logon via the `SinisterVault` scheduled task (see [`AUTOSTART.md`](../tools/sinister-vault/AUTOSTART.md)).

**Syncthing pairing:**

1. Launch Syncthing → it opens `http://127.0.0.1:8384`.
2. Copy Leo's **Device ID** (Actions → Show ID).
3. Send the ID to operator out-of-band (Signal / SMS). Operator adds Leo's device + shares the `sinister-vault-sync` folder ID. Leo accepts the share.
4. Folder path on Leo's side: `D:\sinister-vault\sync\`. Folder ID **must** match operator's exact ID.
5. Operator pastes Leo's device ID into `D:\sinister-vault\accounts\leo.json` (`syncthing_device_id` field) and restarts `SinisterVault`.

**MCP wire-up:**

`wire-everything.ps1` stages the entry at `_vault\mcp-vault-entry-PROPOSED.json`. Leo merges it into his own `~/.claude/.mcp.json` by hand (never edited by an agent):

```powershell
notepad "$env:USERPROFILE\.claude\.mcp.json"
# Paste the contents of the staged file into the "mcpServers" object.
```

Then **restart Claude Code** (full desktop app, not just terminal) so the `vault.*` tools load.

---

## 4. Setup Mode B — Leo connects to operator's daemon over Tailscale

Use when Leo doesn't want a local daemon (lighter footprint; depends on operator's PC being online).

```powershell
# 4.1 Install Tailscale, sign in, join operator's tailnet
# (operator approves Leo's device in the Tailscale admin console)

# 4.2 Point Sanctum at operator's daemon
setx SINISTER_VAULT_HOST "http://<operator-tailscale-name>:5078"

# 4.3 Verify reachability
Invoke-RestMethod "$env:SINISTER_VAULT_HOST/api/vault/health"
```

No local daemon needed. Syncthing is still **recommended** for sync/ large-blob replication — Tailscale carries only the daemon API (`/api/vault/*`), not file content. Syncthing peers transit Tailscale natively if both ends have it.

Operator's tailnet ACL must allow Leo's device on TCP `5078` (and `22000`/`21027` for Syncthing if relying on the tailnet rather than LAN/WAN direct).

---

## 5. Daily flow

1. Double-click `Sinister Start.bat` (operator's launcher; same one works for Leo).
2. EVE picker → pick a project lane (Sanctum / Showmasters / JB Woodworks / etc.).
3. Claude Code session spawns with `--dangerously-skip-permissions` (fleet default; see Sanctum [`CLAUDE.md`](../CLAUDE.md)).
4. Agents auto-write heartbeats to `_shared-memory/heartbeats/<slug>.json`, milestones to `_shared-memory/PROGRESS/<display-name>.md`, and inbox messages via `sinister-bus.inbox_poll`.
5. Operator's audit events stream into Leo's `D:\sinister-vault\audit\<date>.jsonl` within seconds. Same the other way.
6. Per-agent branches: `agent/<slug>/<topic>` — push freely. Only the `sanctum-auto-push` daemon writes to `main`.

---

## 6. Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `Connection refused` on `:5078` | Port collision (another app listening) | `Get-NetTCPConnection -LocalPort 5078` → kill owner, OR `setx SINISTER_VAULT_PORT 5079` and re-wire |
| Files not syncing between Leo + operator | Syncthing folder ID mismatch | Both sides must use the **same** folder ID — check `http://127.0.0.1:8384` → Folders → ID column |
| `vault.*` MCP tools missing in Claude | Proposal not merged, OR Claude Code not restarted | Merge `_vault\mcp-vault-entry-PROPOSED.json` into `~/.claude/.mcp.json`, then quit + reopen the Claude Code desktop app |
| Mode B: `Invoke-RestMethod` times out | Tailscale ACL blocks port 5078 | Operator opens `tcp:5078` for Leo's device in tailnet ACL |
| `[FATAL] venv python not found` | `.venv` never created | `cd 'D:\Sinister Sanctum\tools\sinister-vault'; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt` |
| `Register-ScheduledTask: Access denied` | `-RunLevel Highest` needs admin | Re-run PowerShell as Administrator |
| Daemon `State = Disabled` | Manually disabled | `Enable-ScheduledTask -TaskName SinisterVault` |
| Heartbeat stale (>120 s) but task `Running` | uvicorn worker stuck | Read `_daemon-logs\vault-*.log`; kill `python.exe` — bat restart loop respawns it |

Full troubleshooting matrix in [`AUTOSTART.md`](../tools/sinister-vault/AUTOSTART.md).

---

## 7. Verification

After setup, run these from any PowerShell window:

```powershell
# Liveness — should return uptime + headline used/cap stats
Invoke-RestMethod http://127.0.0.1:5078/api/vault/health

# Recent audit events — should include both Leo + operator entries if sync is working
Invoke-RestMethod http://127.0.0.1:5078/api/vault/audit?limit=3

# Quota breakdown by subtree
Invoke-RestMethod http://127.0.0.1:5078/api/vault/quota

# Account picker — should list operator + leo
Invoke-RestMethod http://127.0.0.1:5078/api/vault/accounts
```

Inside a fresh Claude Code session (after MCP restart):

```
ToolSearch select:vault.health
# Expected: schema returned, status: available
```

If `vault.health` doesn't resolve, the MCP entry didn't land — re-check `~/.claude/.mcp.json` has a `"vault": { ... }` block under `mcpServers` and that the entry's `cwd` points to `D:\Sinister Sanctum\bots\agents\vault`.

For Mode B substitute `http://127.0.0.1:5078` with `$env:SINISTER_VAULT_HOST` in every command above.

---

## Lane discipline (reminder)

- `~/.claude/.mcp.json` is **operator-gated** (and Leo-gated on Leo's side) — agents never edit it.
- `_vault/` holds operator-private auth blobs — no agent reads or writes there.
- Per-agent branches only (`agent/<slug>/<topic>`); never direct-push to `main`.
- Authorship on every new file: `RKOJ-ELENO :: <date>`.
