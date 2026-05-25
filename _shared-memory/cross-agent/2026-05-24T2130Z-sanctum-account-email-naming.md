# Author: RKOJ-ELENO :: 2026-05-24

# Sanctum doctrine note — Claude account email auto-naming

**Trigger:** operator verbatim 2026-05-24T21:25Z: *"name the claude accounmt based on their email."*

**Scope:** `_shared-memory/claude-accounts.json` slot labels are now derived from the Anthropic account email instead of hand-written placeholders ("Sinister Sanctum (Zonia)", "(unconfigured)"). Label format: `email@host (slug)`, e.g. `ezekielromero314@gmail.com (operator)`. Affects every UI surface that renders `account.label` (claude-accounts.ps1 List/Status, EVE picker, fleet-tour, etc.).

**Resolution chain** (`Get-AnthropicEmailFromKey` in `automations/claude-accounts.ps1`, tries in order, first hit wins):

1. **Strategy A — JWT decode.** Splits the key on `.`, base64url-decodes the payload, looks for `email` / `account_email`. `sk-ant-oat01-*` OAuth tokens are opaque so this almost always misses, but it's cheap-first and costs nothing on a hit.
2. **Strategy B — file-cached email.** `_Try-ReadCredentialsField` reads the credentials JSON; if it carries `account_email` (we write this back on first resolution), we skip the HTTP probe entirely on future runs. Idempotent + offline-friendly.
3. **Strategy C — Anthropic OAuth profile HTTP probe.** `GET https://api.anthropic.com/api/oauth/profile` with `Authorization: Bearer <key>` + `anthropic-version: 2023-06-01`. Smoke-tested 2026-05-24T21:30Z with the operator's live `sk-ant-oat01-*` token → HTTP 200, returned `{account:{email:"ezekielromero314@gmail.com",full_name:"Ezekiel",...}, organization:{...}, application:{name:"Claude Code",...}}`. This is the realistic winner for Claude Code OAuth tokens.

**Schema support.** The helper reads BOTH credentials shapes: `{api_key:"..."}` (Sanctum-written, via `Invoke-AccountSetKey`) AND `{claudeAiOauth:{accessToken:"..."}}` (the Claude Code CLI's `~/.claude/.credentials.json`). For the `operator` slot specifically, if its declared `credentials_file` is missing the resolver falls back to the CLI default `$env:USERPROFILE\.claude\.credentials.json`.

**CLI surface.** New action `powershell -File automations\claude-accounts.ps1 -Action ResolveEmails` walks every slot, resolves email, updates label, caches email back into Sanctum-format creds (NEVER touches CLI-schema files), idempotent on re-run. Atomic write via existing `_Acquire-AccountsLock` pattern. `Invoke-AccountSetKey` now also auto-resolves immediately after writing the key so newly-added slots get email-named without a follow-up command.

**Operator override.** Edit `_shared-memory/claude-accounts.json` `label` field directly. `ResolveEmails` overwrites whenever the resolved email differs from the current label; to pin a custom label, pass `-Label "Custom"` to `SetKey` (explicit `-Label` wins over auto-resolved email).

**Smoke-test result (2026-05-24T21:30Z, this lane):**
- `operator` → `ezekielromero314@gmail.com` (source=profile-api, status=updated → idempotent on 2nd run)
- `leo`, `slot3`, `slot4` → unresolved (credentials files don't exist yet on this workstation; will resolve on first SetKey)

**Files touched:** `automations/claude-accounts.ps1` (added `Get-AnthropicEmailFromKey`, `Resolve-AccountEmail`, `Invoke-AccountResolveEmails`, `_Try-ReadCredentialsField`; modified `Invoke-AccountSetKey`); `_shared-memory/claude-accounts.json` (operator label updated); `~/.claude/.credentials.json` NOT modified (CLI-schema preserved); Sanctum-format creds files (when present) get an `account_email` cache field added on first resolve.

**Out-of-scope.** `automations/eve-launcher/eve.py` is sister-B's file; not touched by this iter (UI consumer of `account.label` will pick up the new format on next render without changes).
