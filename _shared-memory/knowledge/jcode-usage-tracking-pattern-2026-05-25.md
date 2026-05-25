<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 90
-->
# jcode usage-tracking pattern (2026-05-25)

> **Author:** RKOJ-ELENO :: 2026-05-25
>
> **Decay:** `category: fact, confidence: 0.85, reinforcements: 0, half_life_days: 90`

## Why this exists

Operator hard-canonical 2026-05-25 (image #67, verbatim):
> "clean this up lnd what did i say about the cap i want everything to be clean
> and leave out wrong info. like saying its 100% its fucking not. review how
> jcode track their usaage or what we need to do and fucking do it"

EVE.exe panels were rendering a 5h spawn-count proxy as if it were measured
Anthropic-side utilization. This brain entry captures the canonical pattern
jcode uses so Sanctum can stop lying and adopt the same shape.

Sister doctrines: `anthropic-real-usage-probe-2026-05-25` (the partial port
that already exists; `automations/anthropic-usage-probe.ps1`) and
`no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 1: precise
verbs; MEASURED vs PROXY vs ESTIMATE vs STALE).

## What jcode does (source survey: `C:\Users\Zonia\Desktop\jcode-0.12.4`)

### 1. The single source of truth is the Anthropic OAuth endpoint

`src/usage.rs:29` — `const USAGE_URL: &str = "https://api.anthropic.com/api/oauth/usage";`

Auth header is the OAuth access token from `auth::claude::load_credentials()` /
`auth::claude::list_accounts()`. No transcript scraping, no spawn-count
heuristic, no msg-cap guess. The OAuth response IS the measurement.

Request shape (`fetch_anthropic_usage_data`):

```
GET /api/oauth/usage
Authorization: Bearer <oauth_access_token>
Accept: application/json
User-Agent: claude-cli/...
anthropic-beta: oauth-2025-04-20,claude-code-20250219
```

### 2. Response shape

`src/usage/model.rs:114-131` — the `UsageResponse` deserialises three windows
plus an `extra_usage` flag:

```rust
struct UsageResponse {
    five_hour:        Option<UsageWindow>,
    seven_day:        Option<UsageWindow>,
    seven_day_opus:   Option<UsageWindow>,
    extra_usage:      Option<ExtraUsageResponse>,
}
struct UsageWindow {
    utilization: Option<f32>,   // 0.0 - 1.0
    resets_at:   Option<String>,// ISO timestamp
}
```

`UsageData` (the cached normalised struct):

```
five_hour                f32    (0.0-1.0)
five_hour_resets_at      Option<String>
seven_day                f32    (0.0-1.0)
seven_day_resets_at      Option<String>
seven_day_opus           Option<f32>
extra_usage_enabled      bool
fetched_at               Option<Instant>
last_error               Option<String>
```

### 3. Cache + backoff (no per-render API hammering)

`src/usage.rs:34-44`:

| Constant | Value | Purpose |
|---|---|---|
| `CACHE_DURATION` | 300s | Default refresh interval |
| `ERROR_BACKOFF` | 300s | Wait after auth/credential failure |
| `RATE_LIMIT_BACKOFF` | 900s | Wait after 429 |
| `PROVIDER_USAGE_CACHE_TTL` | 120s | Min interval between `/usage` cmd fetches |

`UsageData::is_stale()` rolls all three windows: if any window's `resets_at`
has passed, mark stale; otherwise compare `fetched_at` elapsed against the
appropriate TTL.

### 4. Tier-aware cap computation — there is NONE on the client

jcode does NOT compute "Max 20x cap = 800K tokens / 5h" client-side. The cap
is whatever the Anthropic endpoint says it is, encoded in the `utilization`
ratio. The only client-side classification is the status bucket:

`crates/jcode-tui-usage-overlay/src/lib.rs:5-50` — `UsageOverlayStatus`:

```
Loading  Good (healthy)  Warning (watch)  Critical (high)  Error  Info
```

Cutoffs for `exhausted`: `usage_ratio >= 0.99` (both 5h AND 7d) OR
`hard_limit_reached == true`. The string format helper:

```rust
fn five_hour_percent(&self) -> String { format!("{:.0}%", self.five_hour * 100.0) }
```

### 5. Per-account attribution

`enqueue_anthropic_usage_tasks` (`src/usage.rs:271-338`) iterates
`auth::claude::list_accounts()` and spawns ONE fetch task per account into a
`JoinSet`. Each task pulls its own OAuth token and posts back a labelled
`ProviderUsage` row. The active account is marked with " ✦". `mask_email`
PII-redacts the rendered label.

So jcode achieves true per-account splits because EACH account holds its OWN
OAuth credential and the API responds per-token. Sanctum cannot do this for
api-key accounts unless those keys also have OAuth tokens — which is the
operator's open multi-OAuth migration.

### 6. Progressive UI

`fetch_all_provider_usage_progressive` (`src/usage.rs:143-239`) emits
`ProviderUsageProgress { completed, total, done, from_cache, results }`
updates as each task finishes so the TUI can show stale-cache rows
immediately and overlay fresh data as it lands. `from_cache: true` flag is
the truth-in-labelling primitive.

### 7. Account switch guidance

`AccountUsageProbe::best_available_alternative` + `switch_guidance`
(`src/usage/model.rs:343-374`) — when current account is exhausted, find the
peer account with the lowest `max(five_hour_ratio, seven_day_ratio)` and
print "Use `/account switch <label>`". Real-data driven round-robin.

## What Sanctum already has vs. what's missing

| Capability | jcode | Sanctum status |
|---|---|---|
| `/oauth/usage` GET for default OAuth slot | yes | YES — `automations/anthropic-usage-probe.ps1` |
| 5h + 7d + 7d-opus windows | yes | partial (session/weekly/sonnet/design in eve.py 4-bar) |
| Per-account OAuth iteration | yes | NO — only default slot probes; api-key slots fall back to spawn-count |
| Server-driven cap (no client-side guess) | yes | partial — eve.py default slot is server-driven; account_manager.py is client-side tier-cap guess |
| Status bucket (healthy/watch/high/critical) | yes | YES — color buckets in `_render_usage_status_bar` (60/85 cutoffs) |
| Stale badge on cached data | yes (`is_stale`) | NO — Sanctum re-uses for 60s but never tags STALE |
| MEASURED vs PROXY truth-in-labelling | implicit (no proxy exists) | NEW 2026-05-25 — eve.py + account_manager.py now emit `[MEASURED]` / `[PROXY]` |
| Per-account preference_score round-robin | yes (`best_available_alternative`) | NO — current rotation is round-robin-strict, not utilisation-aware |
| Cache + error/RL backoff (300s / 300s / 900s) | yes | partial — Sanctum uses 60s flat + per-call 3s timeout |

## Migration plan (3 phases, ship-able)

1. **Phase 1 (done 2026-05-25 evening):** Truth-in-labelling. Every
   spawn-count row carries `[PROXY]`; every OAuth-headers row carries
   `[MEASURED]`. Operator can no longer mistake spawn-count for real %.
2. **Phase 2 (queued):** Per-account `/oauth/usage` probe. Extend
   `anthropic-usage-probe.ps1` to accept `-Slot <name>` and pull the OAuth
   token from per-account credential files. Replace `[PROXY]` rows with
   `[MEASURED]` when the slot has an OAuth credential. Keep `[PROXY]` for
   api-key-only slots.
3. **Phase 3 (queued):** Stale badge + utilisation-aware rotation. Add
   `stale_at_utc` check (re-use cached payload past `CACHE_DURATION`,
   tag `[STALE]`). Add `best_available_alternative` equivalent in
   `claude-accounts.ps1` rotation logic so EVE picks the lowest-utilisation
   slot, not the next-in-list one.

## What changed in this turn (Phase 1)

`automations/eve-launcher/eve.py` (`_render_accounts_panel`):
- default OAuth slot summary changed from `live  OK` (ambiguous) to
  `[MEASURED]  headers ok` (color OK green badge)
- spawn-count fallback row changed from `<bar> 26%  (13/50 spawns 5h)`
  (read as truth) to `[PROXY] <bar> ~26%  (13/50 spawns 5h, soft cap)`
  (color WARN yellow badge + tilde)

`tools/eve-picker/account_manager.py` (`_render_usage_status_bar`):
- panel subheader changed from `(5h rolling spawn-count vs tier soft cap)`
  to `[PROXY]  (5h spawn-count vs tier soft cap -- NOT Anthropic-side %)`
- per-row tail changed from `{pct}% used (X/Y spawns this 5h)` to
  `[PROXY]  ~{pct}% of soft cap  (X/Y spawns this 5h)`
- module-level comments + `_probe_real_usage` docstring de-claimed "REAL"

`automations/claude-usage-meter.ps1` (header banner):
- renamed in-file from "REAL Claude usage probe" to "ESTIMATE Claude usage
  from local transcripts" with a pointer at the brain entry above

## References (jcode files studied)

- `src/usage.rs` (lines 1-503; main fetch + cache + multi-account)
- `src/usage/model.rs` (lines 1-375; `UsageData`, `OpenAIUsageData`,
  `AccountUsageProbe`, exhausted-detection, switch-guidance)
- `crates/jcode-usage-types/src/lib.rs` (lines 1-750; `ProviderUsage`,
  `UsageLimit`, telemetry tracker structs)
- `crates/jcode-tui-usage-overlay/src/lib.rs` (lines 1-134;
  `UsageOverlayStatus` enum + render rules)
