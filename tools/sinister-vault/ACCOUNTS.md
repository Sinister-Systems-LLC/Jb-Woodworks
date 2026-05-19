# Sinister Vault - Multi-Account System

> **Author:** Sinister Sanctum SV-E agent (Claude) :: 2026-05-19

Each Sanctum user (operator, Leo, anyone else added later) gets their own
account profile under `D:\sinister-vault\accounts\<name>.json`. The Vault
daemon picks them up on startup; RKOJ surfaces an account picker; each
user's Claude API usage bills to their own Anthropic account.

## Why multi-account

- **Separate Anthropic billing.** Operator's prompts go on operator's API
  key. Leo's prompts go on Leo's. Neither sees the other's invoices.
- **Separate HWID binding.** Each account binds to the machine that first
  logged in with that profile, so the operator profile cannot be lifted
  from Leo's laptop (or vice versa) without re-binding.
- **Separate identity.** The Sanctum addresses operator as "Sinister
  Sanctum" (purple accent); Leo is "Sinister Leo" (magenta accent). The
  identity strings flow through prompts, log lines, and UI chrome.
- **Separate Gitea + Syncthing pairing.** Same person on multiple devices
  reuses one profile; different people get different profiles.

## File layout

```
D:\sinister-vault\accounts\
├── _INDEX.md          ← human catalog of who is registered
├── _TEMPLATE.json     ← copy this when adding a new account
├── operator.json      ← operator profile
└── leo.json           ← Leo profile
```

## Schema (vault/account/v1)

```json
{
  "schema": "vault/account/v1",
  "name": "operator",
  "display": "Operator",
  "anthropic_api_key_env": "ANTHROPIC_API_KEY",
  "anthropic_api_key_ref": "user-env",
  "default_agent_identity": "Sinister Sanctum",
  "default_accent_color": "purple",
  "default_model": "claude-opus-4-7",
  "gitea_user": "operator",
  "syncthing_device_id": "<paste-after-syncthing-install>",
  "hwid_bound": null,
  "bound_at": null,
  "created_at": "2026-05-19T00:00:00Z",
  "notes": "free-form"
}
```

| Field                    | Meaning                                                                  |
| ------------------------ | ------------------------------------------------------------------------ |
| `schema`                 | Always `vault/account/v1`. Version bump on breaking changes.             |
| `name`                   | Short slug used in URLs / file names. Lowercase, no spaces.              |
| `display`                | Human display name in the account picker.                                |
| `anthropic_api_key_env`  | Name of the env var holding this user's Anthropic API key.               |
| `anthropic_api_key_ref`  | Always `user-env` for v1. Reserved for future ref types (vault, kms).    |
| `default_agent_identity` | The Sanctum's name when this user is active (e.g. "Sinister Leo").       |
| `default_accent_color`   | Token from the RKOJ palette (`purple`, `magenta`, `cyan`, etc.).         |
| `default_model`          | Claude model ID this user defaults to.                                   |
| `gitea_user`             | Username in `sanctum-git` (Gitea); must already exist there.             |
| `syncthing_device_id`    | Filled in after the user's machine is paired in Syncthing.               |
| `hwid_bound`             | First HWID this profile was used on. `null` until first login.           |
| `bound_at`               | UTC ISO timestamp of the binding event. `null` until first login.        |
| `created_at`             | UTC ISO timestamp the profile file was created.                          |
| `notes`                  | Free-form. Anything memorable about this account.                        |

## Add a new account

```powershell
# 1. copy the template
Copy-Item D:\sinister-vault\accounts\_TEMPLATE.json `
          D:\sinister-vault\accounts\alice.json

# 2. edit alice.json — set name=alice, display=Alice, agent_identity=Sinister Alice,
#    accent_color=cyan, anthropic_api_key_env=ALICE_ANTHROPIC_API_KEY

# 3. set Alice's Anthropic key as a User env var
setx ALICE_ANTHROPIC_API_KEY "sk-ant-..."

# 4. append a row to D:\sinister-vault\accounts\_INDEX.md

# 5. restart the vault daemon so it re-scans the accounts dir
Stop-ScheduledTask  -TaskName SinisterVault
Start-ScheduledTask -TaskName SinisterVault
```

## Env-var binding pattern

| Account  | Env var name                | Where it lives             |
| -------- | --------------------------- | -------------------------- |
| operator | `ANTHROPIC_API_KEY`         | User env vars (operator)   |
| leo      | `LEO_ANTHROPIC_API_KEY`     | User env vars (Leo)        |
| alice    | `ALICE_ANTHROPIC_API_KEY`   | User env vars (Alice)      |

The Vault daemon NEVER reads or stores the actual key. It hands the env-var
NAME to the calling RKOJ session, which then reads `os.environ[...]` at
prompt-build time. If the env var is unset, the session refuses to start
and prompts the user to set it.

## How RKOJ surfaces the account picker

The RKOJ UI (IR-A) reads the accounts list from
`GET http://127.0.0.1:5078/api/vault/accounts` (proxied through RKOJ at
`/api/vault/accounts` on port 5077) and renders a picker chip in the
ribbon. Switching account swaps the active identity, accent color, and
env-var lookup. See IR-A's `RKOJ-VAULT-DRAWER.md` for the UI contract.

## Security

- Account profile files (`accounts/*.json`) contain METADATA only - no
  secrets. The actual Anthropic API key is the user's responsibility to
  set as an env var; the vault never sees it.
- HWID-auth keys live in `D:\sinister-vault\_vault\auth-keys.json` (see
  SV-A). That file is separate and more sensitive; the accounts dir is
  not.
- Account profiles are intentionally diff-friendly so they can be
  committed to a private Sanctum repo if the operator wants. Just keep
  env-var values OUT of the JSON.
- A leaked profile file leaks only: who the user is, which env var name
  to look for, what their preferred identity/accent is. None of that is
  enough to call the API on their behalf.

## See also

- `D:\sinister-vault\accounts\_INDEX.md` - human-readable catalog.
- `D:\sinister-vault\accounts\_TEMPLATE.json` - copy-paste starter.
- `AUTOSTART.md` (this dir) - the scheduled task that runs the daemon.
- `README.md` (this dir) - SV-A's vault daemon overview.
