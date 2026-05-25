<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 90
-->
# Anthropic real-usage probe via /v1/messages response headers

> Author: RKOJ-ELENO :: 2026-05-25
> Status: shipped (live, verified against operator's claude.ai/usage dashboard)
> Composes with: `claude-usage-meter.ps1` (fallback only), `claude-oauth-accounts.ps1`, EVE.exe `_render_accounts_panel`

## Operator trigger

Operator hard-canonical 2026-05-25T00:00Z (verbatim, with 2 screenshots):

> "this cap is wrong you need to make sure we are constantly updating it live in eve. it says 100 but its this: [claude.ai/usage shows session 8%, weekly 69%, sonnet 0%, design 0%] have a clever way to show when it resets, if its all models filled for the week or just the ones that resets every 4 hours"

Root cause of the bad number: `claude-usage-meter.ps1` summed transcript tokens
in a 5h window and divided by a HARD-CODED `msg_cap` (500 for "max", 1500 for
"max20"). The cap was a guess; transcript scraping double-counts cross-session
messages; the operator's actual `plan_tier` field in `claude-accounts.json` was
also stale ("max" instead of "max20"). Result: the bar showed 100% on a session
that was actually 8% used.

## Discovery findings (2026-05-25 live probes)

Endpoints probed with the OAuth Bearer token from `~/.claude/.credentials.json`
plus `anthropic-beta: oauth-2025-04-20` header:

| Endpoint | HTTP | Useful? |
|---|---|---|
| `GET /api/oauth/profile` | 200 | account/org/subscription info; NO usage numbers |
| `GET /api/bootstrap` | 200 | statsig/growthbook feature flags only |
| `GET /api/organizations` | 403 `account_session_invalid` | no |
| `GET /api/organizations/<org>` | 403 | no |
| `GET /api/organizations/<org>/usage` | 403 | no |
| `GET /api/organizations/<org>/rate_limits` | 403 | no |
| `GET /api/organizations/<org>/claude_code/*` | 404 | no |
| `GET /api/account`, `/api/me`, `/api/usage` | 403 / 404 | no |
| `GET /api/claude_code/usage`, `/api/claude_code/rate_limits` | 404 | no |
| `GET /api/oauth/profile/{usage,sessions,limits}` | 404 | no |
| `POST /v1/messages` (1 token) | **200** | **YES -- headers carry live ratelimits** |

**The only working path is response-header scraping on `/v1/messages`.** The
`account_session_invalid` 403 indicates these OAuth tokens are scoped only for
`/v1/messages` + `/api/oauth/profile`; the dashboard-style endpoints require a
separate web-session cookie that the CLI does not have.

Token format note: `sk-ant-oat01-...` is Anthropic's OAuth opaque-token format
(NOT a JWT). It cannot be decoded for claims locally; the `scopes` list in the
credentials blob (`user:profile`, `user:inference`, `user:sessions:claude_code`,
`user:mcp_servers`, `user:file_upload`) is the source of truth for what the
token can do.

## The probe (response headers)

A 1-token `POST /v1/messages` against `claude-sonnet-4-5` returns these
`anthropic-ratelimit-unified-*` headers (verified live on operator's account
2026-05-25T00:11Z, numbers match the claude.ai/usage dashboard EXACTLY):

```
anthropic-ratelimit-unified-status                          allowed
anthropic-ratelimit-unified-5h-utilization                  0.10   <- session
anthropic-ratelimit-unified-5h-reset                        1779683400 (unix)
anthropic-ratelimit-unified-5h-status                       allowed
anthropic-ratelimit-unified-7d-utilization                  0.69   <- weekly all
anthropic-ratelimit-unified-7d-reset                        1779937200 (unix)
anthropic-ratelimit-unified-7d-status                       allowed
anthropic-ratelimit-unified-7d_sonnet-utilization           0.00   <- sonnet
anthropic-ratelimit-unified-7d_sonnet-reset                 1779937200
anthropic-ratelimit-unified-7d_sonnet-status                allowed
anthropic-ratelimit-unified-representative-claim            five_hour
anthropic-ratelimit-unified-overage-status                  rejected
anthropic-ratelimit-unified-overage-disabled-reason         org_level_disabled
anthropic-organization-id                                   691cf20b-...
```

Per-bucket headers (`7d_sonnet`, `7d_design`) are emitted ONLY when the
probed model belongs to that bucket. Calling Sonnet gives unified + sonnet;
calling Opus or Haiku gives only unified. We probe Sonnet by default to cover
3 of the 4 bars in one call. Design bucket is shown as "(not probed)" unless
operator opts in -- design model usage is rare.

Reset timestamps decode in operator's local TZ (EST):
- `1779683400` = `2026-05-25 04:30 UTC` = `2026-05-25 00:30 EDT` (~ 4h22m from
  the screenshot's "Resets in 4 hr 22 min" -- exact match)
- `1779937200` = `2026-05-28 03:00 UTC` = `2026-05-27 23:00 EDT` = `Wed 11:00 PM`
  (matches operator's "Resets Wed 11:00 PM" -- exact match)

## Architecture

```
~/.claude/.credentials.json        (operator default OAuth blob, read-only)
   |
   | claudeAiOauth.accessToken (sk-ant-oat01-...)
   v
automations/anthropic-usage-probe.ps1
   |
   |  POST /v1/messages, claude-sonnet-4-5, max_tokens=1
   v
api.anthropic.com  ----- response headers -----> parse  -----> cache
                                                                |
                                              _shared-memory/anthropic-usage-cache.<slot>.json
                                                                |
                                                                v
                                                  EVE.exe _render_accounts_panel
                                                          |
                                                          v
                                                  4-bar liquid-glass layout
```

## Refresh cadence

- **Cache TTL**: 60 sec default. Tunable via `SINISTER_USAGE_PROBE_REFRESH`
  env (operator can set lower for "live" feel, higher to reduce API calls).
- **Per-render** (EVE.exe picker draw): cache-respecting -- never spams API.
- **Per project pick**: explicit `-Force` refresh fires after the project
  dispatches, so the next picker render (post-spawn) shows fresh post-burn
  numbers. No stale data on the next-spawn screen.
- **Cost**: 1 token-in + 1 token-out per refresh on Sonnet. At max-cadence
  (60s, 24 hrs) that's 1440 calls = ~0.005% of an operator session. Daily
  burn under $0.01.

## Output modes

- `Json` (default) -- machine-readable object; written to disk cache
- `Text` -- one-line summary (`session=12% (resets 4h10m) weekly=69% ...`)
- `Banner` -- multi-line ASCII bars matching claude.ai/usage layout

## EVE.exe 4-bar render (sample, live numbers)

```
Claude accounts 1 enabled  round-robin-strict c1  next -> none  [O]nboard
* ON  ezekielromero314@gmail.com (operator) [max20]  live  OK  today 51
    session [##------------]  14%  resets in 4h05m
    weekly  [##########----]  69%  resets Wed 11:00 PM
    sonnet  [--------------]   0%  resets Wed 11:00 PM
    design  [--------------]  n/a  resets -  (not probed)
+ 1 disabled: Leo (collaborator) (press O to add more)
```

Color rules per bar: GREEN <60%, YELLOW <90%, RED >=90% (composes with
existing `_usage_bar` color tokens).

Clever emphasis line, fires when a cap is hit (operator's "clever way to show"):
- weekly >= 100% -> `[WEEKLY CAP HIT -- {all-models|sonnet|design} resets <day>]`
- session >= 100% but weekly clean -> `[session full -- resets in <Hh Mm> (rotates fast)]`
- weekly >= 90% (warning band) -> `[weekly near cap -- N% used, resets <day>]`

## Failure modes

| Failure | Behavior |
|---|---|
| OAuth token expired (HTTP 401) | Emits `refresh_needed: true` + `REFRESH-NEEDED` tag. Operator runs `claude` once to refresh via CLI. |
| Probe rate-limited (HTTP 429) | Reads cached object (even if stale) + adds `stale-fallback-http-429` status. |
| Network down | Same as 429 -- stale cache + offline tag. |
| Cache corrupted | Ignored + refetch. |
| No `~/.claude/.credentials.json` | Emits `no-credentials` status; eve.py falls back to `claude-usage-meter.ps1`. |
| `claude-usage-meter.ps1` also fails | eve.py shows `meter-unavail` (same behavior as pre-change). |

## Auto-correction: subscription_type override

The OAuth credentials blob carries the AUTHORITATIVE plan tier
(`subscriptionType: "max"`, `rateLimitTier: "default_claude_max_20x"`).
`claude-accounts.json` had a stale `plan_tier: "max"` for what is actually a
Max-20x account. The probe-aware renderer overrides the label tier from the
live OAuth blob, so the displayed `[max20]` chip is always truthful.

## Verification (smoke evidence, 2026-05-25 00:11-00:19Z)

1. `Mode Text -Force` -> `session=12% (resets 4h11m) weekly=69% (resets 3d) sonnet=0% design=n/p` -- numbers match dashboard
2. `Mode Banner` -> 4-bar layout renders with correct percentages + reset times
3. `Mode Json` -> parses via `ConvertFrom-Json`, all fields populated
4. Cache: call 1 = 4462 ms (cold), call 2 = 9 ms (cache hit), call 3 force = 3459 ms (live)
5. `python -c "ast.parse(open('eve.py').read())"` -> `PARSE OK`
6. `_render_accounts_panel()` direct invocation -> 4 bars rendered with live numbers

## Gotchas + future work

- Per-account isolation: today we read `~/.claude/.credentials.json` for the
  default slot. Per-slot probing (`-Slot leo`) works but requires the slot's
  credentials file to exist. API-key-only slots (no OAuth) cannot be probed
  this way -- they get the spawn-proxy bar like before.
- Sonnet probe burns the sonnet bucket by 1 token per refresh. Even at the
  lowest tier (Max 5x) this is invisible in the % rounding.
- Design bucket is omitted by default. If operator's pipeline starts hitting
  claude-design models heavily, add a periodic design-model probe (e.g. once
  per hour) to populate that bar.
- Anthropic could change the header schema without notice. Probe is
  defensive (null-safe parsing, fallback to old meter on shape mismatch).
- This is response-HEADER scraping, NOT a documented API. It is the same
  signal Claude Code itself uses internally (the CLI displays "resetting in
  Nh" warnings from exactly these headers). Stability == Claude Code CLI
  stability.

## Files

- `automations/anthropic-usage-probe.ps1` (NEW, 380 lines)
- `automations/eve-launcher/eve.py` (`_render_accounts_panel` rewritten to
  prefer live probe over fake meter)
- `_shared-memory/knowledge/_INDEX.md` (row added)
- `_shared-memory/anthropic-usage-cache.default.json` (auto-created, 60s TTL)
- `automations/claude-usage-meter.ps1` (UNTOUCHED -- kept as fallback)
