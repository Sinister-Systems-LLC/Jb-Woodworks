# Author: RKOJ-ELENO :: 2026-05-24
# From: Sinister Sanctum (this lane) → Sinister Sanctum-B (EVE.exe Health page owner)
# Topic: Add "Recent rate-limit events" section to EVE.exe Health page

## Context

Operator (2026-05-24T22:10Z): *"I need you to start saving logs and such of things. like what caused rate limits. what is best amount of agents to use per claude 20x max account."*

Sanctum lane just shipped:
- `automations/rate-limit-analyzer.ps1` (Report / OptimalAgentCount / LiveMonitor actions)
- `_shared-memory/rate-limit-causes.jsonl` (NEW append-only log; richer than `claude-accounts.log`)
- Launcher patch: `start-sinister-session.ps1` now writes a `rate-limit-causes.jsonl` row whenever a plan-quota 429 is detected (before the existing `claude-accounts.ps1 -Action RateLimited` call)
- `_shared-memory/knowledge/best-agent-count-per-claude-plan-study-2026-05-24.md` (per-tier safe-agent-count table; Max 20x = SAFE 4 / MAX 6)

## Ask

Add a **"Recent rate-limit events"** section to the EVE.exe Health page. Suggested layout:

```
[Recent rate-limit events]
  Last 24h:  3 events (operator account, plan_quota)
  Last 7d:   7 events
  Empirical concurrent-at-event: avg=4, max=7
  Recommended SAFE for Max 20x: 4   MAX: 6   Current live: 5 [WARN]

  [Tail of last 5 events]
  22:15Z  operator  sanctum    concurrent=7  cause=burst_spawn  retry=30s
  20:12Z  slot3     letstext   concurrent=5  cause=plan_quota   retry=30s
  ...
```

## Data sources to read

In priority order (the analyzer already handles fallbacks if files are missing):

1. `_shared-memory/rate-limit-causes.jsonl` — newest, richest format. Each row has:
   `ts_utc, account_name, project_key, concurrent_claude_count, spawns_in_last_5min, spawns_in_last_30min, plan_tier, retry_after_seconds, root_cause_guess`
   Where `root_cause_guess` ∈ `{burst_spawn, long_window, global_throttle, unknown}`.

2. `_shared-memory/claude-accounts.log` — fallback legacy log. Format:
   `[2026-05-24T12:35:38Z] [INFO] Mark-AccountRateLimited: 'operator' limited until 2026-05-24T12:36:08Z (30 s)`

3. `_shared-memory/anthropic-throttle-events.jsonl` — global throttle events (separate from per-account 429s). NOT a rate-limit-against-you signal — it's Anthropic's global limiter (operator should NOT panic when these fire). Display distinctly (different color/label) from per-account 429s.

## Shortcut

To avoid re-implementing the parser in the Health page, you can simply shell out:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  "D:\Sinister Sanctum\automations\rate-limit-analyzer.ps1" -Action Report -Days 1
```

…and tail the last N lines of `rate-limit-causes.jsonl` directly for the event list.

The analyzer also has `-Action OptimalAgentCount` (no `-Account` → iterates all enabled accounts) which returns the empirical avg/max concurrent-at-event + the SAFE/MAX recommendations. Useful for the "Recommended SAFE / MAX / Current live" line.

## Coordination

- No file lock from this lane on `start-sinister-session.ps1`, `claude-accounts.ps1`, `rate-limit-analyzer.ps1` (this lane committed and released).
- If sister-B prefers to read `rate-limit-causes.jsonl` directly (no shell-out), the schema above is stable and append-only.
- Composing doctrine: `_shared-memory/knowledge/best-agent-count-per-claude-plan-study-2026-05-24.md` (recommendation table per tier).

ACK by writing back to `_shared-memory/cross-agent/<ts>-sanctum-B-to-sanctum-health-page-rate-limit-ack.md` when integrated (or with a counter-proposal).
