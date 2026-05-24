> **Author:** RKOJ-ELENO :: 2026-05-24

# Anthropic server-throttle vs plan-quota — distinguishing two different rate-limit errors

**Created:** 2026-05-24
**Status:** doctrine, empirical, mitigations-shipped
**Composes with:** sanctioned-bypasses-doctrine-2026-05-21 + no-bullshit-tested-before-claimed-doctrine-2026-05-23 + agent-identity-eve

## The problem

The fleet was treating ALL rate-limit signals identically: any 429 / "rate limit" / "retry after" / "too many requests" string in a session log triggered `Mark-AccountRateLimited`, which rotates to the next account in `claude-accounts.json`. That logic is correct for ONE class of error and wrong for another.

There are **two distinct rate-limit categories** that surface in the Claude Code CLI:

### Category A :: Plan-quota 429 (per-account)

- **Surface:** standard HTTP 429, "rate limit exceeded", "retry-after: Nm", "too many requests for your usage tier"
- **Cause:** the operator's account hit its plan quota (5h window / daily cap / paid-tier budget)
- **Scope:** per-account — rotating to a different account WORKS because each account has its own quota
- **Mitigation:** existing `claude-accounts.ps1` multi-account rotation via `Mark-AccountRateLimited`
- **Detection grep (tightened 2026-05-24):**
  ```
  (rate.?limit|429|too many requests|retry.?after)
  AND NOT (Server is temporarily limiting requests|not your usage limit)
  ```

### Category B :: Server-throttle (Anthropic global limiter)

- **Surface (verbatim from operator's image #16, 2026-05-24):**
  ```
  API Error: Server is temporarily limiting requests (not your usage limit) · Rate limited · Churned for 1m 5s
  ```
- **Cause:** Anthropic's server-side burst-rate limiter — independent of any account quota. Typically triggered when the fleet spawns many EVE sessions in a short window (each session opens an SSE stream + immediately begins token-streaming, which Anthropic's edge interprets as a burst).
- **Scope:** GLOBAL — every account on the same machine / IP / org sees the same throttle. **Rotating accounts does NOT help.** In fact, rotating burns the "throttle penalty" against an additional account.
- **Mitigation:** fleet-burst dampening (sleep before launching when concurrent-spawn count is high). Do NOT mark the account rate-limited.
- **Detection grep (new 2026-05-24):**
  ```
  Server is temporarily limiting requests|not your usage limit|server.?side.?(rate|throttle)|Churned for
  ```

## What we shipped (2026-05-24)

### 1. Split detection in `automations/start-sinister-session.ps1` (~line 1280-1310)

The spawn .sh trailer that grepped the recent `~/.claude/projects/*.jsonl` for rate-limit signals was branched:

- **Server-throttle match FIRST** → log a JSON line to `_shared-memory/anthropic-throttle-events.jsonl` with `{ts_utc, account, project, excerpt}`. Do NOT call `Mark-AccountRateLimited`. Print `[INFO]` (not `[WARN]`) so the operator knows the account is fine.
- **Plan-quota match SECOND** (with explicit `AND NOT server-throttle-phrase`) → existing behaviour: `Mark-AccountRateLimited` with 60s retry-after.

This ordering matters: the server-throttle phrase often CONTAINS the substring `rate limit` (Anthropic's error includes "Rate limited"), so the old single-grep would have matched plan-quota first and incorrectly marked the account.

### 2. Fleet-burst dampener (~line 1242-1278 of start-sinister-session.ps1)

New env var **`SINISTER_FLEET_BURST_LIMIT=N`** (default unset = no limit). When set, the spawn .sh:

1. Tails the last 50 lines of `_shared-memory/spawned-windows.jsonl`
2. Counts entries whose `started` ISO-8601 timestamp falls within the last 60 seconds
3. If count ≥ N, sleeps `60 - oldest_spawn_age` seconds before invoking `claude --dangerously-skip-permissions`
4. Prints `[BURST-DAMPEN]` notice with the wait duration

**Recommended values (empirical, will refine as we observe):**
- `SINISTER_FLEET_BURST_LIMIT=2` — conservative, prevents 3+ simultaneous spawns
- `SINISTER_FLEET_BURST_LIMIT=3` — moderate, allows small bursts
- unset — no limit (original behaviour, fine if the operator is solo-spawning)

### 3. Operator-facing surface :: EVE picker `H` key

New picker shortcut `H` (Health). Implementation: `tools/eve-picker/health_tools.py` (stdlib-only). Renders one-screen:

- Plan-quota events today (parsed from `_shared-memory/claude-accounts.log`)
- Server-throttle events today (read from new `anthropic-throttle-events.jsonl`)
- Average "Churned for Xs" wait time per event (regex-parsed from excerpts)
- Rolling 24h rate
- Current `SINISTER_FLEET_BURST_LIMIT` value
- **Recommendation:** if server-throttle hourly rate > 1.0 and no limit set → suggest `SINISTER_FLEET_BURST_LIMIT=2`

Picker line: `H)  Health    // Anthropic throttle status :: plan-quota vs server-throttle`

## Why account rotation actively HURTS on server-throttle

Three reasons:

1. **Doesn't fix it.** The limiter is on Anthropic's edge, not your account. Rotating just hits the same wall.
2. **Burns the rotation pool.** Once `Mark-AccountRateLimited` is called on account X, that account is unavailable for `RetryAfterSeconds` (default 60s). If server-throttle keeps firing, the spawn loop will mark every account in `claude-accounts.json` in sequence and exhaust the pool.
3. **Wrong signal to operator.** The `account-status` surface shows "RATE-LIMITED until ..." which suggests an account problem (operator might think to upgrade plan). The actual fix is burst-dampening, not account juggling.

## Forward-compatibility

If Anthropic changes the error string in the future, update the server-throttle grep pattern in `start-sinister-session.ps1` around line 1291. Keep the original verbatim string in the brain entry for grep-ability:

> `API Error: Server is temporarily limiting requests (not your usage limit) · Rate limited · Churned for 1m 5s`

## File map

| File | Role |
|---|---|
| `automations/start-sinister-session.ps1` (~L1242-1310) | Spawn .sh trailer: burst dampener + split detection |
| `_shared-memory/anthropic-throttle-events.jsonl` | Append-only JSONL of server-throttle events (NEW) |
| `_shared-memory/claude-accounts.log` | Existing plan-quota log via `Mark-AccountRateLimited` |
| `tools/eve-picker/health_tools.py` | `H` picker key — one-screen health surface (NEW) |
| `automations/eve-launcher/eve.py` | Picker UI — wires `H` shortcut |

## Acceptance criteria

- [x] Spawn .sh grep splits server-throttle from plan-quota (tested by `bash /c/Users/Zonia/test-throttle.sh` — branch hits + JSON valid)
- [x] Fleet-burst dampener no-ops when env unset (`bash -n` parses; 0-recent-spawns path returns immediately)
- [x] `H` picker key renders without error (tested via `python -c "import health_tools; health_tools.health_status()"`)
- [x] PowerShell parses with 0 errors (verified)
- [x] eve.py under 1000 lines (827 lines)
- [x] No source/ writes, no MCP edits, no third-party deps
