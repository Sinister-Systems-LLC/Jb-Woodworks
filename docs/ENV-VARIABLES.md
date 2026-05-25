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

- **What it unlocks:**
  1. **RKOJ.exe Anthropic SDK direct path** (v0.6.0+, `forge/spawn/anthropic_direct.py`) — in-process `anthropic.Anthropic.messages.stream` loop with visible `thinking_delta` + batched `tool_use` rendering. When the key is absent, RKOJ falls back to the `claude -p` subprocess path (slower, less observable).
  2. **Tier-3 bots that call the Anthropic API directly:** `scribe` (daily-digest writer, Haiku), `curator` (code-library scout, Haiku). Also the `sinister-chatbot` LLM path when run server-side.
- **Format:** `sk-ant-api03-...` (the standard Anthropic SDK key).
- **Without it:** RKOJ.exe still works (claude -p fallback). Tier-3 bots emit `{ok:false, error:"no API key"}` for any call that needs Claude.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
  ```
- **Current state (2026-05-19):** UNSET. Blocks Scribe + Curator + Chatbot LLM paths AND forces RKOJ.exe into the `claude -p` fallback path (functional but slower).

### `GEMINI_API_KEY`

- **What it unlocks:** Fleet-wide image generation via the `nano-banana` tool (`tools/nano-banana/`). Wraps Gemini 2.5 Flash Image ("Nano Banana") via the `google-genai` SDK. Used by Showmasters (dark+gold stage-light brand-lock helper `smpl_image`), JB Woodworks (gold/black wood photoreal `jbw_image`), and any future lane that needs image generation.
- **Format:** standard Google AI Studio key (no fixed prefix; operator copies it out of the Gemini Pro dashboard).
- **Without it:** `nano_banana.generate()` raises `RuntimeError("No API key. Set GEMINI_API_KEY ...")`. The wrapper also accepts `NANO_BANANA_API_KEY` and `GOOGLE_API_KEY` as aliases (precedence: `GEMINI_API_KEY` → `NANO_BANANA_API_KEY` → `GOOGLE_API_KEY`).
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('GEMINI_API_KEY','<your-key>','User')
  ```
- **Current state (2026-05-23):** UNSET. `google-genai` Python SDK 2.6.0 is installed system-wide; just needs the key.

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

### `SINISTER_EVE_SWARM` / `SINISTER_EVE_LOOP` / `SINISTER_EVE_LOOP_INTERVAL_S`

- **What they unlock:** Per-project EVE autonomy mode for a spawned agent. Picker-overlay's S verb (AutonomyToggleDialog) writes the per-project preset into `automations/session-templates/agent-prefs.json::autonomy_preset.<key>`; RKOJ's `_make_child_env(sess)` exports them at spawn time. `SWARM=1` means swarm mode; `LOOP=1` means auto-loop the agent; `LOOP_INTERVAL_S=<n>` sets the loop cadence in seconds.
- **Read by:** EVE.exe + RKOJ.exe via `eve_picker_lib.prompt_agent_modes_from_env()` and the spawned child claude (via `agents_tab._make_child_env`); SWARM/LOOP visibility chips on `AgentCard` mirror them.
- **Format:** `SINISTER_EVE_SWARM=1` (truthy) / `SINISTER_EVE_LOOP=1` / `SINISTER_EVE_LOOP_INTERVAL_S=300`.
- **Without them:** The spawned agent runs in normal (non-swarm, non-loop) mode. This is the default.
- **Set (preferred path):** Don't set them at User scope — use the picker overlay's `S` verb → AutonomyToggleDialog → save. The preset persists per-project; spawn-time export is automatic. User-scope setting works too but applies to every spawn until unset.
- **Doctrine:** `_shared-memory/knowledge/eve-into-rkoj-integration-2026-05-23.md`; `_shared-memory/plans/_archive/eve-into-rkoj-integration-2026-05-23T1330Z/plan.md` §5.

### `SINISTER_BROWSER_HOST` / `SINISTER_BROWSER_PORT` / `SINISTER_BROWSER_TIMEOUT`

- **What they unlock:** Connection target for the firefox-agent-bridge WebSocket that `tools/sinister-browser/api.py` connects to. Default `127.0.0.1:8766` with 30-second timeout.
- **Read by:** `tools/sinister-browser/sinister_browser/api.py::Browser` (Layer B); also picked up by `skills/sinister-browser.md` operator hint when probing.
- **Format:** Host as string, port as integer, timeout as seconds (float OK).
- **Without them:** Defaults are used (`127.0.0.1:8766`, 30 s). Override only when running Firefox on a different machine (e.g. Leo's host via Tailscale) or when the bridge moved off its default port.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('SINISTER_BROWSER_HOST','127.0.0.1','User')
  [Environment]::SetEnvironmentVariable('SINISTER_BROWSER_PORT','8766','User')
  [Environment]::SetEnvironmentVariable('SINISTER_BROWSER_TIMEOUT','30','User')
  ```
- **Doctrine:** `_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md`; matrix row 26.

### `SINISTER_SANCTUM_ROOT`

- **What it unlocks:** Path anchor for the Sanctum tree on Leo's machine (or any installation that puts the repo somewhere other than `D:\Sinister Sanctum`). Used by `eve_picker_lib`, `sinister-mind/server.py`, `sinister-vault/daemon.py`, `tools/sinister-utils/io.py`, and most tools that read fleet-shared JSON.
- **Format:** Absolute path string. Example: `D:\Sinister Sanctum` (operator default) or `C:\Sanctum` (Leo example).
- **Without it:** Tools default to `D:\Sinister Sanctum` (operator's canonical). Leo MUST set it if his clone lives elsewhere.
- **Set:**
  ```powershell
  [Environment]::SetEnvironmentVariable('SINISTER_SANCTUM_ROOT','D:\Sinister Sanctum','User')
  ```
- **Doctrine:** referenced by every tool that reads `automations/session-templates/projects.json` (which the BOM-defense doctrine catalogues fleet-wide).

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

## Third-party CLI auth tokens — TTY-less spawn fix

Every fleet agent now spawns with `claude --dangerously-skip-permissions`, which
disables TTY allocation. Any CLI whose `login` opens a browser (`railway login`,
`gh auth login`, `vercel login`, etc.) dies with **`Cannot login in
non-interactive mode`** or an equivalent string. The fix: mint a token via the
service dashboard once, store it as a User-scope env var, and the CLI will
auto-pick it up on every subsequent call — no `login` step needed.

Full doctrine: `_shared-memory/knowledge/non-interactive-auth-doctrine-2026-05-23.md`.

### Token env-var table

| CLI                  | Env var(s)                                                         | Mint location                                                       |
|----------------------|---------------------------------------------------------------------|---------------------------------------------------------------------|
| Railway              | `RAILWAY_TOKEN` (project) or `RAILWAY_API_TOKEN` (account)         | <https://railway.com/account/tokens>                                |
| GitHub CLI           | `GH_TOKEN` (preferred) or `GITHUB_TOKEN`                            | <https://github.com/settings/tokens> (`repo` + `workflow` scopes)   |
| Vercel               | `VERCEL_TOKEN`                                                      | <https://vercel.com/account/tokens>                                 |
| npm / pnpm           | `NPM_TOKEN` (write `//registry.npmjs.org/:_authToken=$NPM_TOKEN` into `~/.npmrc`) | <https://www.npmjs.com/settings/~/tokens>                |
| Supabase             | `SUPABASE_ACCESS_TOKEN`                                             | <https://supabase.com/dashboard/account/tokens>                     |
| Firebase             | `FIREBASE_TOKEN` (run `firebase login:ci` once on a real workstation) | n/a — `firebase login:ci` mints it                                |
| DigitalOcean (doctl) | `DIGITALOCEAN_ACCESS_TOKEN`                                         | <https://cloud.digitalocean.com/account/api/tokens>                 |
| Fly.io (flyctl)      | `FLY_API_TOKEN` (output of `flyctl auth token`)                     | n/a — mint with `flyctl auth token`                                 |
| Heroku               | `HEROKU_API_KEY`                                                    | <https://dashboard.heroku.com/account> → API Key                    |
| Expo / EAS           | `EXPO_TOKEN`                                                        | <https://expo.dev/accounts/[user]/settings/access-tokens>           |
| Cloudflare Wrangler  | `CLOUDFLARE_API_TOKEN` (+ `CLOUDFLARE_ACCOUNT_ID` for some commands) | <https://dash.cloudflare.com/profile/api-tokens>                    |
| Netlify              | `NETLIFY_AUTH_TOKEN`                                                | <https://app.netlify.com/user/applications#personal-access-tokens>  |
| AWS                  | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` (+ `AWS_DEFAULT_REGION`) | IAM console                                                      |
| Google Cloud         | `GOOGLE_APPLICATION_CREDENTIALS=<path-to-service-account.json>`      | IAM service-accounts console                                       |

> **Operator must set these.** Tokens are minted via the operator's browser
> session in a normal (non-Claude) window. Agents will never mint these
> themselves.

### Set commands (per-user, survives reboot)

```powershell
[Environment]::SetEnvironmentVariable('RAILWAY_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('GH_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('VERCEL_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('NPM_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('SUPABASE_ACCESS_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('FIREBASE_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('DIGITALOCEAN_ACCESS_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('FLY_API_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('HEROKU_API_KEY','<token>','User')
[Environment]::SetEnvironmentVariable('EXPO_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('CLOUDFLARE_API_TOKEN','<token>','User')
[Environment]::SetEnvironmentVariable('NETLIFY_AUTH_TOKEN','<token>','User')
```

### Per-session (current PowerShell only — does NOT persist)

```powershell
$env:RAILWAY_TOKEN = '<token>'
$env:GH_TOKEN      = '<token>'
# etc.
```

Use per-session for one-off tests; use the User-scope `setx`-equivalent above
for the durable path.

### Verify a token is set (without printing the value)

```powershell
if ([Environment]::GetEnvironmentVariable('RAILWAY_TOKEN','User')) { 'set' } else { 'unset' }
```

### npm note

`npm` reads `NPM_TOKEN` via a project- or user-scope `.npmrc` file, NOT directly
from env. Put this single line in `~/.npmrc` (one-time):

```
//registry.npmjs.org/:_authToken=${NPM_TOKEN}
```

`pnpm` and `yarn` v1 read the same file.

### Restart open sessions after setting

Existing PowerShell / Claude Code / git-bash sessions cache the env at spawn
time. Setting a new User-scope env var requires closing and reopening any
session that needs to see it.

---

## Tools that read these (cross-reference)

| Env var | Read by |
|---|---|
| `ANTHROPIC_API_KEY` | `bots/agents/scribe/server.py`, `bots/agents/curator/server.py`, `tools/sinister-chatbot/src/services/anthropic.ts` |
| `GEMINI_API_KEY` | `tools/nano-banana/nano_banana/api.py` (via `google-genai` SDK) |
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
  'ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'SINISTER_VAULT_PASSPHRASE',
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
