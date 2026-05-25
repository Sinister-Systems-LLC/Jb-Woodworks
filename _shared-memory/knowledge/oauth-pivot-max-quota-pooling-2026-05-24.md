<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# OAuth pivot: Max 20x quota pooling via per-slot credentials swap

Author: RKOJ-ELENO :: 2026-05-24
Status: scaffolded + smoke-tested (16/16 unit tests PASS); awaiting operator OAuth login for first real slot

## Operator hard-canonical (verbatim 2026-05-24 ~22:50Z)

*"i need you to change how the account system works so we can login accounts and not use api key approach as its not what we want we want logged in claude 20x max session and going off that usage. complete this and everything else you need to do. use all parrallel agents you need"*

## The fundamental billing fact (cap-cost honest assessment)

Anthropic's Max 20x ($200/mo) subscription quota applies ONLY to OAuth sessions used by Anthropic's first-party apps (Claude.ai web/desktop + Claude Code CLI). API keys (sk-ant-api*) hit a SEPARATE Console pay-as-you-go account that does NOT consume Max quota. Therefore:

- API-key rotation across N keys = N separate pay-as-you-go bills (no Max pooling)
- OAuth-session rotation across N logged-in accounts = N parallel Max quotas pooled

To pool Max 20x across multiple accounts, we MUST swap OAuth credentials, not API keys.

## How Claude Code stores OAuth

Single active OAuth blob at `~/.claude/.credentials.json`:

```json
{"claudeAiOauth":{"accessToken":"sk-ant-oat01-...","refreshToken":"sk-ant-ort01-...","expiresAt":1779676617708,"scopes":["user:inference","user:profile","user:sessions:claude_code",...]}}
```

The CLI does NOT natively support multi-account isolation. Our solution: keep per-slot copies at `~/.claude/credentials.<slot>.json` and atomically swap the active slot BEFORE spawn time.

## Architecture

1. **`automations/claude-oauth-accounts.ps1`** (NEW, ~600 lines, RKOJ-ELENO :: 2026-05-24) — Login / Use / Active / List / LogoutSlot / WhoAmI / RotateToNext / MarkLimited / Migrate. Eagerly loads `claude-accounts.ps1` at script-load time (lazy import dot-sources into function scope, invisible elsewhere — discovered during smoke test).
2. **`automations/test-claude-oauth-accounts.ps1`** (NEW) — 16 unit tests covering shape detection, hash determinism, atomic copy, migrate idempotency, list output schema, MarkLimited timestamps, bogus action surfacing. PASS 16/16.
3. **`_shared-memory/claude-accounts.json`** (MIGRATED) — new fields per row: `auth_mode` (`oauth`|`api_key`, default `api_key` for legacy rows), `display_name`, `oauth_email`, `quota_resets_at_utc`, `weekly_reset_at_utc`. Existing 4 rows migrated via `Invoke-OAuthMigrate`.
4. **`automations/start-sinister-session.ps1`** (PATCHED, lines 1538-1582 + 1655-1668) — when chosen slot has `auth_mode='oauth'`, runs `claude-oauth-accounts.ps1 -Action Use -Name <slot>` to swap credentials BEFORE spawn. Does NOT export `ANTHROPIC_API_KEY` for OAuth slots (that env hijacks billing to Console). New env `SINISTER_AUTH_MODE` surfaces mode to spawned bash.
5. **`tools/eve-picker/account_manager.py`** (PATCHED) — `_action_add` now offers OAuth (recommended) or API key (legacy). New `_action_oauth_login` runs the interactive Login scaffold. `_action_bulk_setup` walks operator through N accounts in one sitting. `_action_mark_limited` for "limited til monday" overrides. `_action_active_slot` shows which OAuth slot matches `~/.claude/.credentials.json`. `_action_logout` routes OAuth slots through `LogoutSlot`. Actions menu adds K (API key), M (mark limited), V (active OAuth), P (bulk setup).
6. **`automations/eve-launcher/eve.py`** `_account_onboarding_flow` (PATCHED, ~line 847-928) — mirror OAuth/API-key picker. OAuth path shells out to `claude-oauth-accounts.ps1 -Action Login` interactively.

## Operator workflow (per-account)

Per account the operator wants logged in:

1. From EVE.exe main picker → `O) Onboarding (claude accounts)` OR `M) Account Manager` → `L) Login (OAuth Max)`.
2. Pick slot name (any text; auto-slugified: "Sinister Gmail" → `sinister-gmail`).
3. Pick display name (optional; defaults to email-localpart).
4. Module preserves current `~/.claude/.credentials.json` to a sideline.
5. Module prints `claude login` instructions; operator opens a NEW window, runs `claude login`, completes OAuth in browser with the target account.
6. Operator presses Enter in the original window.
7. Module captures the freshly-written `~/.claude/.credentials.json` → `~/.claude/credentials.<slot>.json`.
8. Module restores the prior `.credentials.json` so operator's active session is undisturbed.
9. Module persists slot row with `auth_mode=oauth`, `oauth_email` (probed via Anthropic profile API), `credentials_file`.
10. Repeat for each Max 20x account.

For BULK setup: use `P) Bulk setup` in Account Manager to loop through N accounts in one sitting.

## Round-robin spawn flow (OAuth mode)

1. Picker click → `start-sinister-session.ps1` calls `Get-NextAvailableAccount` (existing logic).
2. If chosen slot has `auth_mode='oauth'`: subprocess `claude-oauth-accounts.ps1 -Action Use -Name <slot>` swaps credentials. `selectedApiKey=$null`.
3. Bash spawn script exports `SINISTER_AUTH_MODE='oauth'`; the `if [ -n '$bashApiKey' ] && [ "$SINISTER_AUTH_MODE" != "oauth" ]` guard ensures NO `ANTHROPIC_API_KEY` is set.
4. Claude CLI starts → reads `~/.claude/.credentials.json` → uses the swapped slot's OAuth session → consumes THAT account's Max plan quota.

## Cap-cost honest assessment

**Should work (intended green path):**
- If Anthropic rate-limits Max 20x per ACCOUNT (per OAuth identity / email), rotating between N logged-in accounts pools quota.

**Possible gotchas (untested):**
- If Anthropic also rate-limits by IP, all N accounts share the workstation's IP cap. Mitigation: mesh-route some spawns through Tailscale exit nodes (out-of-scope this iter).
- Anthropic may flag rapid account swapping. We do nothing obfuscatory; this is a legitimate operator-with-multiple-legit-accounts pattern.
- OAuth tokens expire (~1 hour for access, ~30 days for refresh). Claude CLI handles refresh automatically while in-session, but a long-idle slot may need re-login. Module's `WhoAmI` action surfaces expired tokens (profile probe fails).
- Concurrent spawns racing on `~/.claude/.credentials.json` swap: each spawn calls `Use` sequentially via PS1 lock-holding in claude-accounts. Within a single spawn the swap-then-launch is atomic; back-to-back spawns at <1s intervals could theoretically interleave but the launcher's lease lock serializes them.

**Definitively NOT covered:**
- Anthropic terms-of-service review of multi-account workstation pooling. Operator's responsibility.

## NEW CLI examples

```powershell
# Migrate existing claude-accounts.json schema (one-time; idempotent)
powershell -File automations\claude-oauth-accounts.ps1 -Action Migrate

# Log in a new OAuth slot (interactive; operator clicks OAuth in browser)
powershell -File automations\claude-oauth-accounts.ps1 -Action Login -Name sinister-gmail -DisplayName "Sinister Gmail"

# List all slots (OAuth + api_key) with active-marker, mode, email, limited-until
powershell -File automations\claude-oauth-accounts.ps1 -Action List

# Show which OAuth slot is currently active (hash compare against ~/.claude/.credentials.json)
powershell -File automations\claude-oauth-accounts.ps1 -Action Active

# Activate a slot (atomically copies credentials.<slot>.json -> .credentials.json)
powershell -File automations\claude-oauth-accounts.ps1 -Action Use -Name sinister-gmail

# Round-robin to next available OAuth slot
powershell -File automations\claude-oauth-accounts.ps1 -Action RotateToNext

# Operator-set "limited til monday" (rolling rate-limit)
powershell -File automations\claude-oauth-accounts.ps1 -Action MarkLimited -Name sinister-gmail -Until 2026-05-30T00:00:00Z

# Operator-set "limited til monday" (WEEKLY cap on Max plan)
powershell -File automations\claude-oauth-accounts.ps1 -Action MarkLimited -Name sinister-gmail -Until 2026-05-31T00:00:00Z -Weekly

# Probe Anthropic profile API for slot's email
powershell -File automations\claude-oauth-accounts.ps1 -Action WhoAmI -Name sinister-gmail

# Remove slot's credentials file (and clear active .credentials.json if it was the active slot)
powershell -File automations\claude-oauth-accounts.ps1 -Action LogoutSlot -Name sinister-gmail
```

## Composes with

- `claude-accounts.ps1` (legacy api-key manager — still authoritative for `auth_mode='api_key'` rows; OAuth module imports it for shared lock + config helpers)
- `claude-usage-meter.ps1` (already OAuth-compatible — sums `~/.claude/projects/**/*.jsonl` transcripts; works for OAuth out of the box)
- `start-sinister-session.ps1` (consumes Use + auth_mode hint at spawn time)
- `account_manager.py` + `eve.py` (EVE.exe surfaces — operator-facing flows)

## Backwards compatibility

- Legacy api_key path still works (any row with `auth_mode='api_key'` or missing field treated as api_key).
- `Invoke-OAuthMigrate` is idempotent — first run adds missing fields, subsequent runs no-op.
- `Get-AccountCredentials` (legacy lookup) untouched; OAuth path bypasses it.

## Smoke-test evidence

```
=== summary ===
  PASS: 16
  FAIL: 0
```

Tests cover: OAuth shape detection, file-hash determinism, atomic-copy semantics, migrate idempotency, list output schema, MarkLimited (both daily + weekly fields), bogus action handling.

## NOT smoke-tested (requires operator-interactive OAuth)

- `Invoke-OAuthLoginScaffold` end-to-end (requires browser OAuth)
- Real spawn with `auth_mode='oauth'` slot
- Multi-account round-robin under load with real Max quotas

These ship when operator runs the first real Login + spawns against the resulting slot.
