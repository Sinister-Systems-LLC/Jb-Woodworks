<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Non-Interactive Auth Doctrine — TTY-less spawn → env-var token fallback

> **Author:** RKOJ-ELENO :: 2026-05-23

## Symptom (what you see)

When a spawned EVE session runs a third-party CLI that wants browser-based OAuth,
the call dies with one of these stderr strings:

| CLI               | Error string                                                                |
|-------------------|-----------------------------------------------------------------------------|
| `railway login`   | `Cannot login in non-interactive mode`                                      |
| `gh auth login`   | `gh: To use GitHub CLI in automation, set the GH_TOKEN environment variable`|
| `vercel login`    | `Error: No existing credentials found. Please run "vercel login" interactively` |
| `npm login`       | `npm ERR! code EOTP` / opens browser that never returns                     |
| `supabase login`  | `Cannot prompt for input in non-interactive mode`                           |
| `firebase login`  | `Cannot run login in non-interactive mode. See login:ci`                    |
| `doctl auth init` | hangs waiting for `Enter your access token:` prompt                         |
| `fly auth login` / `flyctl auth login` | opens browser, returns nothing usable to the agent |
| `heroku login`    | `heroku: Press any key to open up the browser to login or q to exit`        |
| `eas login`       | `EAS_OFFLINE not set` then hangs waiting for password                       |
| `wrangler login`  | opens browser; CLI waits forever for the redirect                           |
| `netlify login`   | opens browser; same hang                                                    |
| `aws configure`   | hangs on first `AWS Access Key ID [None]:` prompt                           |

## Why it happens

Every fleet agent now spawns with `claude --dangerously-skip-permissions` (operator
hard-canonical 2026-05-23, see `sanctioned-bypasses-doctrine-2026-05-21.md`). That
flag in turn disables TTY allocation for the inner shell — child CLIs see
`isatty(stdin) == false`, which is the standard signal those CLIs use to refuse
interactive prompts.

The fix is **never to re-introduce a TTY**. The fix is to use the
token-based auth path every one of these CLIs ships for CI/automation use.
Tokens come from a one-time browser session the operator runs on the host
machine, are persisted to the User env-var scope, and then every spawned agent
reads them transparently.

## The fix pattern

1. **Operator** (one-time, in a normal PowerShell window) mints a token via
   the relevant dashboard, then runs:
   ```powershell
   [Environment]::SetEnvironmentVariable('RAILWAY_TOKEN','<token>','User')
   ```
2. **Restart any open EVE sessions** so they re-read User env.
3. **Agent** invokes the CLI directly — every CLI in the table below
   auto-picks up the env-var token without any `login` step.

## CLI ↔ env-var token table

| CLI               | Login command (forbidden in non-TTY)        | Env var(s) to set instead                     | Where to mint                                                       |
|-------------------|---------------------------------------------|------------------------------------------------|---------------------------------------------------------------------|
| Railway           | `railway login`                             | `RAILWAY_TOKEN` (project-scoped) or `RAILWAY_API_TOKEN` (account-wide) | <https://railway.com/account/tokens>                                |
| GitHub CLI        | `gh auth login`                             | `GH_TOKEN` (preferred) or `GITHUB_TOKEN`       | <https://github.com/settings/tokens> — needs `repo` + `workflow` scopes (see `github-auth-workflow-scope.md`) |
| Vercel            | `vercel login`                              | `VERCEL_TOKEN`                                 | <https://vercel.com/account/tokens>                                 |
| npm               | `npm login`                                 | `NPM_TOKEN` (write `//registry.npmjs.org/:_authToken=$NPM_TOKEN` into project `.npmrc` or `~/.npmrc`) | <https://www.npmjs.com/settings/~/tokens>                           |
| pnpm              | `pnpm login`                                | Same as npm — pnpm reads `~/.npmrc`            | Same                                                                |
| Supabase          | `supabase login`                            | `SUPABASE_ACCESS_TOKEN`                        | <https://supabase.com/dashboard/account/tokens>                     |
| Firebase          | `firebase login`                            | `FIREBASE_TOKEN` (mint via `firebase login:ci` ONCE on a real workstation) | n/a — `firebase login:ci` is the official CI-token minter           |
| DigitalOcean      | `doctl auth init`                           | `DIGITALOCEAN_ACCESS_TOKEN`                    | <https://cloud.digitalocean.com/account/api/tokens>                 |
| Fly.io            | `fly auth login` / `flyctl auth login`      | `FLY_API_TOKEN` (output of `flyctl auth token` on a real workstation) | n/a — mint with `flyctl auth token`                                 |
| Heroku            | `heroku login`                              | `HEROKU_API_KEY`                               | <https://dashboard.heroku.com/account> → API Key                    |
| Expo (EAS)        | `eas login` / `expo login`                  | `EXPO_TOKEN`                                   | <https://expo.dev/accounts/[user]/settings/access-tokens>           |
| Cloudflare Wrangler | `wrangler login`                          | `CLOUDFLARE_API_TOKEN` (+ `CLOUDFLARE_ACCOUNT_ID` for some commands) | <https://dash.cloudflare.com/profile/api-tokens>                    |
| Netlify           | `netlify login`                             | `NETLIFY_AUTH_TOKEN`                           | <https://app.netlify.com/user/applications#personal-access-tokens>  |
| AWS               | `aws configure`                             | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` (+ `AWS_DEFAULT_REGION`) | IAM dashboard                                                       |
| Anthropic (Claude Code itself) | `claude auth login`            | `ANTHROPIC_API_KEY` (already documented in `docs/ENV-VARIABLES.md`) | <https://console.anthropic.com/settings/keys>                       |
| OpenAI            | n/a (no login CLI) — but Codex/Anthropic compat wrappers may probe | `OPENAI_API_KEY`               | <https://platform.openai.com/api-keys>                              |
| Google Cloud      | `gcloud auth login`                         | service-account JSON via `GOOGLE_APPLICATION_CREDENTIALS=<path>` | IAM service-accounts console                                        |

## Detection + auto-switch pattern for agents

When an agent attempts `<cli> login`, wrap it in a probe that catches the
non-interactive failure and surfaces the env-var ask to the operator. **The
canonical implementation now lives in `tools/sinister-login/` v0.1.0** (shipped
2026-05-23 by rkoj-lane /loop iter 9 + 11). Two surfaces:

### Python (in-process)

```python
from sinister_login import ni_auth_probe, ProbeResult, EX_CONFIG

result = ni_auth_probe(cli="railway", cmd="railway login", envvar="RAILWAY_TOKEN")
if result.has_token:
    proceed()                          # envvar set; login skipped
elif result.needs_token:
    print(result.hint, file=sys.stderr)
    sys.exit(result.exit_code)         # 78 EX_CONFIG
```

### CLI (from bash / PowerShell / scripts)

```bash
sinister-login auth-probe railway \
    --cmd "railway login" --envvar RAILWAY_TOKEN [--timeout 30] [--json]
# exit 0    has-token / login-OK
# exit 78   needs-token (operator must mint + set env var); hint printed to stderr
# exit 127  missing binary
# exit <rc> CLI's own exit code on non-marker failure
```

### Skeleton (historical — superseded by the real impl above)

The bash sketch below was the original doctrine skeleton. The shipped Python
implementation supersedes it but pattern is identical (12 stderr markers, EOF
on stdin so prompts can't block, EX_CONFIG=78 exit, structured operator hint).

```bash
# Reusable non-interactive auth probe.
# Usage: ni_auth_probe railway "railway login" RAILWAY_TOKEN
#        ni_auth_probe gh      "gh auth status" GH_TOKEN
ni_auth_probe() {
  local cli="$1" cmd="$2" envvar="$3"
  # If the relevant token is already set, skip the login step entirely.
  if [ -n "${!envvar}" ]; then
    return 0
  fi
  # Try the login; capture stderr.
  local err
  err="$(eval "$cmd" 2>&1 >/dev/null)" || true
  case "$err" in
    *non-interactive*|*"To use"*|*"Cannot prompt"*|*"Please run"*)
      cat >&2 <<EOF
[non-interactive-auth] $cli login refused — TTY-less spawn detected.
Operator needs to mint a token and set \$${envvar} at User scope.
See docs/ENV-VARIABLES.md → "Third-party CLI auth tokens" for the URL.
After setting, restart this EVE session.
EOF
      return 78  # EX_CONFIG, the standard "config needed" exit code
      ;;
  esac
}
```

For PowerShell-host agents (RKOJ, Forge launcher) the equivalent uses
`$LASTEXITCODE` + `2>&1` capture; pattern is identical. Either way the agent
**never blocks on a browser**. It either uses the env-var token transparently
or surfaces a structured ask via `OPERATOR-ACTION-QUEUE.md`.

## Storage convention

All token env-vars live in the **User** scope (NOT Machine, NOT process), set
via `[Environment]::SetEnvironmentVariable('NAME','value','User')`. They survive
reboots, are inherited by every git-bash / PowerShell / claude spawn, and never
leak to other Windows users on the box.

Full set-command reference: `docs/ENV-VARIABLES.md` → **Third-party CLI auth
tokens** section.

## What this doctrine does NOT do

- Does NOT bypass MFA / OAuth flows that require human attestation. If a CLI
  refuses to mint long-lived tokens (rare; mostly enterprise SSO), the
  operator-action queue is the right surface — agent stops and waits.
- Does NOT enable agents to mint new tokens themselves. Token minting is an
  operator-owned, browser-based step.
- Does NOT touch `~/.claude/.mcp.json` (operator-gate per canonical-11).

## Anti-patterns

1. **Re-enabling TTY** by removing `--dangerously-skip-permissions`. This breaks
   the entire fleet's spawn pattern (canonical-21 / `do-not-revert` P1).
2. **Hardcoding tokens** in `.bat` / `.ps1` / committed files. Always env-var.
3. **`npm login` in CI** — always `NPM_TOKEN` via `.npmrc` token line.
4. **Calling `<cli> login` then ignoring the failure** — wrap in `ni_auth_probe`
   so the failure becomes a structured operator ask, not silent skip.
5. **Storing tokens in Machine scope** — User-scope is sufficient and avoids
   leaking to other Windows accounts.
6. **Editing the per-CLI config file directly** (`~/.railway/config.json`, etc.) —
   each CLI's env-var path is the documented, supported escape hatch; the
   config-file path is internal and breaks across versions.

## Empirical anchor

2026-05-23: EVE on JB Woodworks finished an autonomous railway deploy plan
through the last step where `railway login` died with `Cannot login in
non-interactive mode`. Operator surfaced the class-of-error and asked for the
doctrine. See `_shared-memory/OPERATOR-ACTION-QUEUE.md` row dated
`2026-05-23 17:00Z — JB Woodworks: Railway flip needed`.

## Composes with

- `sanctioned-bypasses-doctrine-2026-05-21` — `--dangerously-skip-permissions`
  is the upstream cause of the TTY-less state.
- `do-not-revert-operator-canonical-protections-2026-05-23` — P1 keeps the flag
  on; this doctrine handles the consequence.
- `github-auth-workflow-scope` — `gh` PAT scope quirks (need `workflow` for
  `.github/workflows/*.yml` writes).
- `headless-spawn-pattern-2026-05-23` — orthogonal; headless spawn ≠ TTY-less
  CLI auth, but both are "agent runs without a human at the keyboard".

## See also

- `docs/ENV-VARIABLES.md` — the env-var storage doc (operator-facing set
  commands)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` — open operator clicks (mint tokens)
- `tools/sinister-login/` — existing internal login abstraction (separate from
  third-party CLI auth)
