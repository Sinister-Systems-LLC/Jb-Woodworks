<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Multi-account burn-first :: capacity-blocker visibility doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24 (test-modes lane, /loop iter 5 sub-area capacity-UX)
> **Closes:** `test-modes-5x-parallel-consolidated-status-2026-05-24.md` §4 row #1 — operator-action item *"enable Leo/slot3/slot4"*
> **Composes with:** `no-bullshit-tested-before-claimed-doctrine-2026-05-23` · sub-area B ship · `jcode-parity-gap-audit-2026-05-24-test-modes.md` §9.1

## Why this exists

Sub-area B shipped `rotation_strategy: burn-first` in `_shared-memory/claude-accounts.json` and `Get-NextAvailableAccount v4` in `automations/claude-accounts.ps1`. The implementation is verified-live. However, **only `operator` account is `enabled: true`** in claude-accounts.json — Leo + slot3 + slot4 are all `enabled: false`.

**Net effect:** burn-first ≡ load-balance functionally when `enabled_count=1`. The 100% plan utilization the operator asked for in image #1 is **logic-shipped but capacity-blocked**. Operator may not realize this from reading the consolidated status (it's in §4 row #1, but easy to miss).

## The one-command unblock

```powershell
# from anywhere in Sanctum:
.\automations\claude-accounts.ps1 -Action SetKey -Name leo
# (or -Name slot3 / -Name slot4 — accepts ANTHROPIC_API_KEY via secure prompt)
```

This:
1. Prompts operator for the Anthropic API key (secure read, never echoed to log).
2. Writes to `C:\Users\Zonia\.claude\credentials.<slot>.json` (operator-private, not in repo).
3. Flips `enabled: false → true` for that slot in `claude-accounts.json`.
4. Optionally sets `plan_tier` (defaults to "max").

**After ANY ONE additional slot is enabled**, burn-first auto-failover kicks in immediately — no further config, no restart, no agent-side change.

## Verification when operator runs it

After enabling a second slot, this command confirms the failover capacity is live:

```powershell
. .\automations\claude-accounts.ps1
$cfg = Get-AccountsConfig
$enabled = @($cfg.accounts | Where-Object { $_.enabled -ne $false })
Write-Host "enabled_count=$($enabled.Count) names=$(($enabled.name) -join ',') strategy=$($cfg.rotation_strategy)"
# expected after enabling leo: enabled_count=2 names=operator,leo strategy=burn-first
```

## Why this is operator-action only

This file documents the unblock but does NOT auto-execute it:

1. **Credentials are operator-private** — Anthropic API keys are not in any repo; operator's secret store is the only source.
2. **Account-enablement is policy** — operator decides whether Leo's account is in the rotation pool right now (Leo is a collaborator, not a backup; permission may be context-dependent).
3. **Plan-tier is operator knowledge** — only operator knows which slots have which Anthropic plan tiers.

Per sanctioned-bypasses-doctrine-2026-05-21: master EVE has standing authorization to spawn children with `--dangerously-skip-permissions`, but operator-private credential surfaces stay operator-owned.

## Signal-surface plan (optional UX additions, deferred)

Future siblings (NOT this iter — outside scope per rule 1) could add:

- **Launcher startup warning** when `enabled_count=1` AND `rotation_strategy=burn-first`: 1-line yellow `[hint] burn-first active but only 1 account enabled — failover is no-op. Run claude-accounts.ps1 -Action SetKey -Name leo to enable.`
- **Sentinel rule** that fires every 12h reminding the operator-action queue.
- **EVE.exe status panel** row showing `accounts: 1/4 enabled (strategy=burn-first)`.

None of these ship this iter — outside sub-area scope. Listed for future iter-N to claim.

## No-bullshit ledger

- This doc is operator-facing pointer + verification recipe. **Does NOT claim** capacity is unlocked.
- The implementation in claude-accounts.ps1 + claude-accounts.json IS shipped (verified live this turn: smoke test `Get-NextAvailableAccount → strategy=burn-first` returned anchor account; file read confirmed value).
- Operator-action gap is real and explicit; rule 1 precise verb = `code-shipped, capacity-blocked-on-operator-credential-enablement`.

## Composes-with

- `_shared-memory/knowledge/jcode-parity-gap-audit-2026-05-24-test-modes.md` §9.1
- `_shared-memory/knowledge/test-modes-5x-parallel-consolidated-status-2026-05-24.md` §4 row #1
- `automations/claude-accounts.ps1` (the unblock tool)
- `_shared-memory/claude-accounts.json` (the data this guards)
