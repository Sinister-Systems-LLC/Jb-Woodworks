# Plan: Multi-Claude Account Rotation System

> **Author:** RKOJ-ELENO :: 2026-05-23 evening
> **Goal:** Run multiple Claude accounts in parallel, auto-rotate on rate-limit, auto-recover when limit clears.

## Operator directive (verbatim)

> "i ned you to add multi claude support with rotation features wehere i can spread out agents between accounts. if a plan rate limits it auto switches to other plan and comes back once limit is done etc. we need a complex system for this make it and test it and add it to the eve exe and bat file to login different accounts etc."
>
> "if they hit a limnit on all plans they need to start back up once limit is over"

## Architecture

### Storage

`_shared-memory/claude-accounts.json` — operator-curated list of accounts. Schema:

```json
{
  "version": 1,
  "default": "operator",
  "rotation_strategy": "round-robin",
  "accounts": [
    {
      "name": "operator",
      "label": "Sinister Sanctum (Zonia)",
      "env_key": "ANTHROPIC_API_KEY",
      "credentials_file": "C:\\Users\\Zonia\\.claude\\credentials.operator.json",
      "plan_tier": "max",
      "max_sessions_concurrent": 5,
      "current_sessions": 0,
      "rate_limited_until_utc": null,
      "last_429_at_utc": null,
      "successful_spawns_today": 0,
      "fleet_share": 0.6
    },
    {
      "name": "leo",
      "label": "Leo (collaborator)",
      "env_key": "ANTHROPIC_API_KEY",
      "credentials_file": "C:\\Users\\Zonia\\.claude\\credentials.leo.json",
      "plan_tier": "max",
      "max_sessions_concurrent": 5,
      "current_sessions": 0,
      "rate_limited_until_utc": null,
      "last_429_at_utc": null,
      "successful_spawns_today": 0,
      "fleet_share": 0.4
    }
  ]
}
```

### Components

1. **`automations/claude-accounts.ps1`** — library with:
   - `Get-NextAvailableAccount` — returns name of next account by rotation strategy, respecting rate-limits + concurrent caps
   - `Mark-AccountSpawned <name>` — increments `current_sessions`, increments `successful_spawns_today`
   - `Mark-AccountRateLimited <name> <retry_after_seconds>` — sets `rate_limited_until_utc`
   - `Get-WaitUntilAnyAvailable` — returns earliest `rate_limited_until_utc` across all accounts
   - All operations use a `.lock` file for concurrent safety

2. **`automations/claude-account-watchdog.ps1`** — scheduled task (every 5 min) that:
   - Decrements `current_sessions` for stale entries (no recent heartbeat → assume session ended)
   - Resets `rate_limited_until_utc` when wall clock > stored value
   - If all accounts WERE rate-limited and at least one is now available, fires `Sinister Start.bat --auto-resume` to bring agents back up

3. **`automations/start-sinister-session.ps1` integration:**
   - At top of `Launch-Session`, call `Get-NextAvailableAccount`
   - Set `$env:ANTHROPIC_API_KEY` (or whichever env_key the account uses) in the spawn .sh
   - Call `Mark-AccountSpawned` after successful spawn
   - On claude exit (in the .sh trailer), check exit code/log for 429 markers and call `Mark-AccountRateLimited` if detected

4. **`tools/session-launcher/Sinister Start.bat` integration:**
   - Honor `SINISTER_ACCOUNT=<name>` env to pin a specific account
   - Add `--account <name>` flag → sets SINISTER_ACCOUNT before invoking PS1/EVE.exe
   - Add `--account-status` flag → prints current account state and exits

5. **`automations/eve-launcher/eve.py` integration (longer-term):**
   - Add account picker in EVE.exe UI (key `K` already used for Clear-ctx; use `U` for "user/account picker")
   - Show current account in the status bar
   - Auto-rotate when picker hits "spawn" if current account is throttled

### Rate-limit detection

Two paths:

a) **Sync detection** (preferred): on claude exit in the spawn .sh, check the run-log for known 429 patterns:
   - `"rate limit exceeded"`
   - `"too many requests"`
   - `"retry-after"`
   - `"429"`

b) **Async heartbeat-based**: every heartbeat write includes `last_api_response_code`. Watchdog reads heartbeats; if 429 detected, marks account.

We do path (a) first (simpler, no schema change).

### Recovery loop

Three layers:
1. **Spawn-time fallback**: `Get-NextAvailableAccount` returns next non-rate-limited account; if all limited, returns `null` + the `Get-WaitUntilAnyAvailable` timestamp.
2. **Bat-time wait**: if `Get-NextAvailableAccount` returned null, bat sleeps until `Get-WaitUntilAnyAvailable`, then retries (max 3 wait cycles before giving up).
3. **Watchdog-time wake**: scheduled-task watchdog (every 5 min) detects when a rate-limited account becomes available; if no claude is running, fires `Sinister Start.bat --auto-resume`.

### Security

- Per-account credentials files live at `C:\Users\<op>\.claude\credentials.<name>.json` (operator-private, NOT in repo).
- `claude-accounts.json` in repo has NO secrets — just account names + paths to credentials.
- Each spawn sets `ANTHROPIC_API_KEY` from the credentials file's `api_key` field (or whatever the operator chose).

## Phased delivery

- **Phase 1 (this turn):** Storage schema + manager library + bat/PS1 wiring (Agent M1).
- **Phase 2:** Rate-limit detection in spawn .sh + Mark-AccountRateLimited call (Agent M2).
- **Phase 3:** Watchdog scheduled task + auto-resume logic (Agent M3).
- **Phase 4 (future):** EVE.exe picker UI integration.

## Test plan

- Smoke: create `claude-accounts.json` with 2 fake accounts → spawn picks first → mark rate-limited → spawn picks second → mark both rate-limited → spawn returns null → bat waits → wall clock advances → spawn picks first again.
- E2E: real spawn with real keys (operator + Leo), verify env_key is set correctly in spawned claude.
