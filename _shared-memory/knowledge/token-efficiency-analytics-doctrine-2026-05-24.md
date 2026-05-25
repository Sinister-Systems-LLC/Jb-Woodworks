<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Token Efficiency Analytics Doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Operator hard-canonical:** *"in parrallel add to teh account tab a token menu so that we can track all token use and see places where we can improve our token use and make better systems to become more token efficent"* (verbatim 2026-05-24 ~23:30Z).

## Scope

Standing rule for the EVE.exe Accounts tab and any future surface that touches Claude token usage. Defines:

1. The **5-windows** philosophy for token visibility
2. The **cache hit** targets per project / fleet-wide
3. The **waste-detection** pattern set
4. The **recommendations** generation rules
5. The **data-source contract** (single source of truth = `~/.claude/projects/**/*.jsonl` via `automations/token-analytics.ps1`)

## 1. Five-windows philosophy

Token visibility ALWAYS surfaces four rolling windows + 1 lifetime aggregate:

| Window | Purpose |
|---|---|
| `1h` | Right-now spike detection (loop-mode burn, runaway sub-agents) |
| `5h` | Anthropic plan-cap window (matches `claude-usage-meter.ps1` default) |
| `24h` | Daily spend / 7-day baseline comparator |
| `7d` | Trend + recommendation reference; cost roll-up |
| lifetime | `ByProject` + `BySession` use full-history aggregates for stable rankings |

Single-window views (1h-only or 24h-only) are an anti-pattern -- they hide spikes or smooth out anomalies. Always render the 4-window strip together.

## 2. Cache hit targets

| Surface | Target | Action below target |
|---|---|---|
| Per-session | >50% | Investigate session-prompt variance; check for per-spawn timestamps |
| Per-project | >60% | Audit CLAUDE.md cold-start for cache-stable prefix |
| Fleet-wide | >60% | P0 recommendation row; review system prompt rotation |
| **Healthy** | 80-99% | Cache is working as designed |

Calculation: `cache_hit_ratio = cache_read / (cache_read + cache_creation)`. Savings vs no-cache: `0.9 * cache_read_tokens` (because cache reads cost 10% of full-input rate).

## 3. Waste-detection rules

Four named patterns flagged by `WasteReport`:

1. **abandoned-cache** (sev=med) -- session has `cache_create > 100K` AND `cache_read < 0.5 * cache_create`. Means cache was built but barely used. Common cause: short-lived sessions for one-shot tasks.
2. **context-bloat** (sev=high) -- project avg billable-eq > 200K tokens/msg over >=10 msgs. Means transcripts are loading too much context. Fix: `/compact` more often; shorter sessions; tighter sub-agent scopes.
3. **tool-loop** (sev=med) -- session with >=100 msgs AND >=0.5 tool calls per msg. Means agent is in a retry / fan-out loop. Fix: tighten task scope; cap sub-agents per loop; add early-exit heuristics.
4. **no-caching** (sev=high) -- project with >=50 msgs AND <20% cache hit ratio. Means cache is effectively broken (varying prefixes, no system prompt cache). Fix: freeze a stable prefix block at top of CLAUDE.md.

Thresholds tunable via `-ContextBloatThresholdTokens` and `-ToolLoopThresholdMsgs` parameters.

## 4. Recommendations generation

`Recommendations` action returns 5-10 prioritized rows (P0/P1/P2/P3):

- **P0** = budget burn ($200+/wk) or fleet cache <30%
- **P1** = per-project caching <25% (>=50 msgs); high-cost project; bloated sessions
- **P2** = >80% Opus mix; tool-loop count; abandoned-cache count; 24h spike vs 7d daily avg
- **P3** = always-present standing rules (cache-stable prefix; brain >150 rows)

Each recommendation includes the measurement that triggered it AND a concrete suggested action. Never emit a recommendation that an operator cannot act on.

## 5. Data-source contract

**Single source of truth:** `~/.claude/projects/**/*.jsonl` (Claude Code transcripts). Each transcript line carries `message.usage.{input_tokens,cache_creation_input_tokens,cache_read_input_tokens,output_tokens}` and `message.model`.

**Implementation:**
- Canonical sampler = `automations/token-analytics.ps1` (extends `claude-usage-meter.ps1`'s parse strategy with per-project / per-session / per-model + waste + recommendations).
- Wrapper UX = `tools/eve-picker/token_analytics.py` (Python module mirroring sub-menu for picker codepath).
- EVE.exe entry = Accounts tab option `6) Token analytics` (calls `_token_analytics_submenu()` in `automations/eve-launcher/eve.py`).

**Cost model** (Opus rate for messages where `model` matches `opus`; Sonnet rate otherwise):
- input: 1.00x ($15/M opus, $3/M sonnet)
- cache_create: 1.25x
- cache_read: 0.10x
- output: 5.00x ($75/M opus, $15/M sonnet)
- `billable_eq = input + 1.25*cc + 0.10*cr + 5.0*out` (single scalar for cross-window comparison)

## Composes with

- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (rule 2: test-before-claim — every smoke action above verified)
- `_shared-memory/knowledge/eve-exe-uniform-ui-infinite-accounts-2026-05-24.md` (sub-menu follows 3-block layout)
- `_shared-memory/knowledge/session-start-auto-update-propagation-2026-05-24.md` (eve.py edit triggers `verify-eve-features.ps1 -AutoRebuild -SyncMirror`)
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` (this is a fleet-wide doctrine, not per-project)
- `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md` (recommendations engine IS the forever-improve mechanism for token spend)
- `_shared-memory/knowledge/gradual-growth-memory-push-eve-exe-ready-2026-05-24.md` (R2: ships reachable from EVE.exe on next spawn)

## Anti-patterns (do NOT)

1. Re-implement transcript parsing from scratch — extend `token-analytics.ps1` or call its `-Action Json` and post-process.
2. Surface a single-window view without context (always show the 4-window strip).
3. Treat `raw tokens` as the comparable scalar across windows — use `billable_eq` (the weighted sum that matches actual quota burn).
4. Bury a P0 cost-burn recommendation in P3-styled prose.
5. Emit "consider X" without a measurement that triggered it.
6. Hard-code Opus pricing — model-aware switching is mandatory (Sonnet is ~5x cheaper).

## Smoke evidence (2026-05-24 first run, operator workstation)

- `Summary`: 306,480 transcript-messages scanned across 40 projects; 24h window 31,641 msgs / 8.87B raw tokens / 98.2% cache hit.
- `ByProject`: 40 projects; lifetime cost-eq $192,819 (estimated as if API-billed).
- `CacheReport`: fleet-wide 97.8% cache hit (>>60% target — healthy).
- `WasteReport`: 381 patterns flagged (370 abandoned-cache subagents + 7 tool-loops + 4 context-bloat).
- `Recommendations`: 5 emitted (1 P0 cost-burn + 2 P2 + 2 P3).
- `Json`: valid, `ConvertFrom-Json` passes.
