<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: fact
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# Brain-Decay Implementation Schema (Tier 2 of memory-backbone-3-tier-hybrid)

**Created:** 2026-05-24T22:10Z
**Authority:** memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24 (Tier 2) + sub-agent recommendation 2026-05-24T22:07Z ("pin frontmatter schema + decay formula + EffConf column contract before opportunistic backfill drifts").

Pins the canonical contract so 174 brain entries can be opportunistically annotated by ANY lane without schema drift.

---

## 1. Frontmatter schema (canonical)

```
<!-- decay:
  category: correction | preference | fact | entity
  confidence: 0.0 - 1.0
  reinforcements: <int>
  half_life_days: 365 | 180 | 90 | 60 | 30 | 14
  superseded_by: <slug>   # optional; marks entry inactive
-->
```

**Placement:** immediately after the `<!-- Author: ... -->` comment, before the H1 title. If no Author comment exists, at the top of the file.

**Fields (all optional except category; defaults apply if missing):**

- `category` (default `fact`) -- one of `correction` / `preference` / `fact` / `entity`
- `confidence` (default `0.8`) -- 0.0 to 1.0; 1.0 = operator-stated verbatim
- `reinforcements` (default `0`) -- bumped each time the doctrine is re-validated
- `half_life_days` (default per category; see table) -- override allowed
- `superseded_by` (default empty) -- entry treated as inactive when set

## 2. Category half-life defaults

| Category | Default half-life | When to use |
|---|---|---|
| `correction` | 365d | operator-stated rule that overrides prior behavior; rare to obsolete |
| `preference` | 365d (operator-canonical) OR 180d (codified preference) | persistent stylistic / identity rules (e.g. agent-identity-eve, authorship-RKOJ-ELENO) |
| `fact` | 90d (shipped doctrine), 60d (recent rewrite), 30d (one-off finding) | factual claims about how the system works; decays as system evolves |
| `entity` | 30d | references to specific PIDs, accounts, dates, transient state |

Operator can override per entry with explicit `half_life_days:` line.

## 3. Decay formula (canonical)

```
effective_confidence = confidence * exp(-(age_days / half_life_days) * ln(2)) * sqrt(reinforcements + 1)
```

- `age_days` computed from `**Created:**` header field, falling back to filename date, falling back to file mtime
- `exp(-(age/half) * ln(2))` is the standard half-life decay: at `age == half`, multiplier == 0.5
- `sqrt(reinforcements + 1)` boosts entries re-validated multiple times; first reinforcement gives 1.41x, 4th gives 2.24x, etc.

Implementation: `automations/brain-decay-score.ps1 -Action Score` (already shipped iter 5).

## 4. `_INDEX.md` `EffConf` column (forthcoming)

Once annotation rate >= 15/174 (current: 9/174), add an `EffConf` column to `_INDEX.md` between `Status` and `Tags`:

```
| Slug | Title | Status | EffConf | Tags | Created | Updated |
```

The `EffConf` value is computed by `brain-decay-score.ps1` and refreshed weekly by the SinisterToolAutotrigger cron (already configured at tool-autotrigger-config.json with `schedule: cron:7d` for brain-decay-score).

## 5. Three operator-actionable surfaces

1. **`brain-decay-score.ps1 -Action Score -TopDecayed 10`** -- weekly review queue (most-stale first)
2. **`brain-decay-score.ps1 -Action Reinforce -Slug <s>`** -- bump when a doctrine is re-validated (e.g. cited in a new doctrine's "Composes with")
3. **`brain-decay-score.ps1 -Action Supersede -Slug <old> -By <new>`** -- prune-as-add when a newer doctrine subsumes an older one (e.g. eve-ui-uniformity-doctrine -> eve-exe-uniform-ui-infinite-accounts iter 9)

## 6. Opportunistic backfill protocol (NOT mass-backfill)

Per gradual-growth-memory-push-eve-exe-ready-2026-05-24 R3 (grow gradually + never stop + prune-as-add):

- When a lane TOUCHES a brain entry (reads it for context, cites it in a new entry, or modifies it), ADD the decay frontmatter at that moment.
- Do NOT batch-annotate all 174 entries in one pass -- that violates rule 6 (laser focus) and rule 8 (no big-bang).
- Target growth: +5 annotations per iter when active; expected to reach 25-30% (~50 entries) within 10 iters.

## 7. Anti-patterns

1. Changing the formula without bumping doctrine version + announcing via fleet-update -- breaks `EffConf` reproducibility.
2. Treating un-annotated entries as low-priority -- defaults (`fact / 0.8 / 30d`) are reasonable; absence of annotation just means "not yet curated."
3. Annotating with `confidence: 1.0` for non-operator-stated entries -- reserve 1.0 for direct operator verbatim.
4. Setting `half_life_days < 14` -- noise; below 2 weeks decay outpaces realistic re-validation cadence.
5. Editing the frontmatter manually without going through `brain-decay-score.ps1` -- bypasses idempotency + history.

## 8. Composes with

- `memory-backbone-3-tier-hybrid-better-than-jcode-2026-05-24` (this doctrine implements its Tier 2)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R3 opportunistic adoption discipline)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 6 + 8 quality bars for backfill cadence)
- `forever-improve-review-doctrine-2026-05-24` (decay-score Top-N surfaces feed forever-improve)
- `sanctum-scope-discipline-2026-05-24` (brain hygiene is Sanctum-level work)
- `automations/brain-decay-score.ps1` (the implementation)

## 9. Verification

```powershell
# Annotation rate today
powershell -File automations/brain-decay-score.ps1 -Action Score -TopDecayed 1 2>&1 | Select-String 'annotated:'

# Sample a single entry
powershell -File automations/brain-decay-score.ps1 -Action Score -TopDecayed 5 -As Json | ConvertFrom-Json | Select Slug, Cat, EffConf, Annotated
```
