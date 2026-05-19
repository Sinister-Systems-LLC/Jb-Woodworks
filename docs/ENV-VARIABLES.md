# Sinister Sanctum — environment variables cheat sheet

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Every env var the Sanctum fleet reads, what it unlocks, and the exact command to set it.

All vars are scoped to the **User** target on Windows — they survive reboots, are read by every PowerShell / cmd / git-bash spawn, and never leak into the system-wide context.

To set:
```powershell
[Environment]::SetEnvironmentVariable('NAME','value','User')
```

To read (verify presence, never the value):
```powershell
if ([Environment]::GetEnvironmentVariable('NAME','User')) { 'set' } else { 'unset' }
```

To unset (clear):
```powershell
[Environment]::SetEnvironmentVariable('NAME', $null, 'User')
```

**Restart any open PowerShell / Claude Code sessions** after setting; existing processes cache the env at spawn time.

---

## Critical — sets the agent capability gate

### `ANTHROPIC_API_KEY`

- **What it unlocks:** Tier-3 bots that call the Anthropic API directly: `scribe` (daily-digest writer, Haiku), `curator` (code-library scout, Haiku). Also the `sinister-chatbot` LLM path when run server-side.
- **Format:** `sk-ant-api03-...` (the standard Anthropic SDK key).
- **Without it:** Those bots fall back to "no-API-key" graceful degradation — they exist but emit `{ok:false, error:"no API key"}` for any call that needs Claude.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
  ```
- **Current state (2026-05-19):** UNSET. Blocks Scribe + Curator + Chatbot LLM paths.

### `OPENAI_API_KEY`

- **What it unlocks:** Codex Companion peer-review (`POST /api/codex/review`, `tools/codex-companion/codex.py`). Used by master agent + per-project agents to cross-check Claude's output for auth / crypto / payment / >100 LOC pushes.
- **Format:** `sk-...` (standard OpenAI key).
- **Without it:** `codex.review()` returns `{ok:false, error:"no API key"}`. Per the standing rule in `_shared-memory/DIRECTIVES.md`, that's a BLOCK for high-risk pushes (auth/crypto/payment); for low-risk it's a documented skip.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('OPENAI_API_KEY','sk-...','User')
  ```
- **Current state (2026-05-19):** SET (✓ — Codex reviews working; 5 in log).

---

## High — sets identity and isolation

### `SINISTER_VAULT_PASSPHRASE`

- **What it unlocks:** At-rest Fernet encryption for operator-private vault files via `bus.vault_lock` / `bus.vault_unlock` and the codec layer. The Sanctum Vault (storage tier at `D:\sinister-vault\`) is **orthogonal** — Vault is a quota-managed collaborative store; this passphrase is for the auth-keys / secrets blob.
- **Format:** any reasonable-length passphrase. Operator chooses.
- **Without it:** Codec works on plaintext only. Bots refuse to load `_vault/`-tagged secrets.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('SINISTER_VAULT_PASSPHRASE','<phrase>','User')
  ```
- **Current state (2026-05-19):** UNSET.

### `LEO_ANTHROPIC_API_KEY`

- **What it unlocks:** Leo's per-account Anthropic billing isolation. The multi-account schema at `D:\sinister-vault\accounts\leo.json` references this env var by name so leo's API spend is tracked separately from operator's.
- **Format:** same as `ANTHROPIC_API_KEY` (`sk-ant-api03-...`).
- **Without it:** When leo's account is the active one (per `accounts.json` rotation), the Anthropic SDK falls back to `ANTHROPIC_API_KEY` — billing leaks into operator's account.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('LEO_ANTHROPIC_API_KEY','sk-ant-...','User')
  ```
- **Current state (2026-05-19):** UNSET. Only matters once leo is actively using Sanctum.

---

## Medium — sets defaults and locations

### `SINISTER_HUB_ROOT`

- **What it unlocks:** Override of the hardcoded hub path (`D:\Sinister\Sinister Skills`). Used by every MCP bot's `server.py` to anchor its `01_MEMORY/<project>/` and `_logs/` paths.
- **Format:** absolute Windows path with no trailing backslash, e.g. `D:\Sinister\Sinister Skills` or `E:\Sinister\Sinister Skills` if the operator's drive letter shifts.
- **Without it:** Defaults to the hardcoded `D:\Sinister\Sinister Skills`. Drive-letter changes (D: → E:) break the fleet until set OR until `refresh.ps1 -RewritePaths` is run.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('SINISTER_HUB_ROOT','D:\Sinister\Sinister Skills','User')
  ```
- **Current state (2026-05-19):** UNSET (using hardcoded default).

### `SINISTER_AGENT_NAME`

- **What it unlocks:** Per-session agent identity. Read by the cold-start agent at the top of every Claude Code session; injected into heartbeat / inbox / PROGRESS file paths.
- **Format:** the display name, e.g. `Sinister Snap API`, `Sinister Sanctum`.
- **Without it:** The launcher (`start-sinister-session.ps1`) sets it inline per-spawn via the bash `export` in the generated launch script. Setting it at user-scope just makes it the default for non-launcher Claude sessions.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('SINISTER_AGENT_NAME','Sinister Sanctum','User')
  ```
- **Current state (2026-05-19):** UNSET (launcher injects per-spawn — preferred).

---

## Low — service credentials (only if running that service)

### `GITEA_ADMIN_PASSWORD`

- **What it unlocks:** Initial bootstrap of the self-hosted Gitea instance at `localhost:3000` (used by `sanctum-git` tool). Read by `tools/sanctum-git/.env` loader during install.
- **Format:** any password the operator picks for the `operator` admin account.
- **Without it:** Gitea install wizard prompts interactively. Either path works; env-var path is for scripted setup.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('GITEA_ADMIN_PASSWORD','<password>','User')
  ```
- **Current state (2026-05-19):** UNSET. Gitea is offline anyway.

---

## Tools that read these (cross-reference)

| Env var | Read by |
|---|---|
| `ANTHROPIC_API_KEY` | `bots/agents/scribe/server.py`, `bots/agents/curator/server.py`, `tools/sinister-chatbot/src/services/anthropic.ts` |
| `OPENAI_API_KEY` | `tools/codex-companion/codex.py` |
| `SINISTER_VAULT_PASSPHRASE` | `bots/agents/_shared/crypto.py`, `bots/agents/sinister-bus/server.py` (vault tools) |
| `LEO_ANTHROPIC_API_KEY` | `D:\sinister-vault\accounts\leo.json` (referenced by name) |
| `SINISTER_HUB_ROOT` | Every bot's `server.py` (path anchor) |
| `SINISTER_AGENT_NAME` | `automations/start-sinister-session.ps1`, every cold-start Claude session |
| `GITEA_ADMIN_PASSWORD` | `tools/sanctum-git/setup-vault-data-dir.ps1`, `tools/sanctum-git/bootstrap-users.py` |

## Quick-check script

To audit all of the above in one shot:

```powershell
@(
  'ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'SINISTER_VAULT_PASSPHRASE',
  'LEO_ANTHROPIC_API_KEY', 'SINISTER_HUB_ROOT', 'SINISTER_AGENT_NAME',
  'GITEA_ADMIN_PASSWORD'
) | ForEach-Object {
  $v = [Environment]::GetEnvironmentVariable($_, 'User')
  $status = if ($v) { 'set' } else { 'unset' }
  '{0,-30} {1}' -f $_, $status
}
```

## See also

- `_shared-memory/OPERATOR-ACTION-QUEUE.md` — the 🟡 Medium bucket lists the env-var set commands too
- `SESSION-START/02-OPERATOR-QUEUE.md` — cold-start sees env-var status
- `_shared-memory/knowledge/sinister-vault-architecture.md` — vault env-var details
- `_shared-memory/knowledge/codex-companion-usage.md` — OPENAI_API_KEY usage
