<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Context Cleaner v2 :: Spec

**Created:** 2026-05-23T12:45Z (EVE on Sanctum, /loop iteration 2, B.9 of `sanctum-complete-and-expand-2026-05-23T1145Z`)
**Triggering directive (operator 2026-05-23 evening verbatim):** *"have a clearer that keeps the context clean but has all we need to work on projects"*
**Status:** spec only — implementation deferred to a follow-up turn (R2; this spec is R1)
**Composes with:** `bot-fleet-quick-reference` (token math) + `no-bullshit-tested-before-claimed-doctrine` (no scaffolds claimed shipped) + `forge-memory-usage` (working memory orthogonality) + `forever-expanding-modular-architecture` (quality-degradation limits) + `multi-agent-branch-contention-isolation-pattern` (cross-agent state preserved)

---

## Problem statement

A long-running Sanctum session accumulates:

- 5-12 unrelated `pre_warm_reads` from old resume-points (each 500-2K tokens)
- 20+ truncated tool results that landed in context but aren't needed for current work
- Stale PROGRESS sections from sibling lanes the current agent doesn't own
- Resume-point chains that exceed 20 entries per lane (Rule 7.5 signal)
- Inbox messages from lanes the current agent doesn't coordinate with
- Brain doctrine sections that aren't relevant to the current turn

The operator's "clean context but has everything we need" requirement is structurally: **route every read through a relevance gate, where relevance is task-keyword + lane-ownership + recency**.

The current `automations/context-pruner.ps1` (v1, shipped earlier) handles file deletion only — it does not score, does not preview, does not respect lane ownership.

## Architecture (v2)

### Three-layer pipeline

```
┌───────────────────┐   ┌────────────────────┐   ┌──────────────────┐
│ SOURCE            │   │ RELEVANCE GATE     │   │ EMIT              │
│ (filesystem walk) │ → │ (score + filter)   │ → │ (dry-run /       │
│                   │   │                    │   │  archive /       │
│ - resume-points   │   │ keyword match      │   │  delete /        │
│ - PROGRESS logs   │   │ lane ownership     │   │  pre_warm hint)  │
│ - heartbeats      │   │ age weighting      │   │                  │
│ - inboxes         │   │ Rule-7.5 ceilings  │   │                  │
│ - brain entries   │   │                    │   │                  │
│ - plans           │   │                    │   │                  │
└───────────────────┘   └────────────────────┘   └──────────────────┘
```

### Inputs (CLI flags)

```
context-pruner.ps1
  -Lane <slug>              # whose context this is for (default: master)
  -TaskKeywords <words>     # e.g. "bot-fleet token-reduction" (drives relevance)
  -Mode <dry|archive|delete> # default: dry
  -PreserveHours <n>        # never touch <n> hours of state (default 24)
  -CapPerLane <n>           # max retained per-lane (default 20)
  -Json                     # emit machine-readable plan
```

### Relevance score (0.0 - 1.0)

For each file `f`:

```
score(f) = w_lane * lane_match(f) + w_keyword * keyword_match(f) + w_recency * recency_score(f) + w_pinned * pinned(f)
```

Default weights:
- `w_lane = 0.35` — files owned by `-Lane` win the lane test (1.0); cross-lane test files (0.4); other-lane files (0.0)
- `w_keyword = 0.35` — BM25-ish match against `-TaskKeywords` over file content (cap at 1.0)
- `w_recency = 0.20` — `1.0` if mtime < 6h, linearly decays to `0.0` at 30 days
- `w_pinned = 0.10` — `1.0` if file is in `_shared-memory/pinned.txt`; `0.0` otherwise

Files with `score < 0.30` are pruning candidates.

### Per-class retention policies

| Class | Path pattern | Default keep | Override |
|---|---|---|---|
| Resume-points | `resume-points/<lane>/*.json` | last 20 per lane | `-CapPerLane` |
| PROGRESS logs | `PROGRESS/<lane>.md` | always (per CLAUDE.md Rule 9) | none |
| Heartbeats | `heartbeats/<slug>.json` | last 1 per slug | none |
| Inboxes (read) | `inbox/<lane>/*.json` (older than 7d + responded-to) | archive to `_archive/` | `-PreserveHours` |
| Brain entries | `knowledge/*.md` | always (lane-owned indexing) | none |
| Plans (closed) | `plans/<name>/` (with `STATUS: closed`) | move to `_archive/` after 14d | none |
| Telemetry | `telemetry/daily-*.json` | last 30 days | none |
| `script-runs/` | `script-runs/*.json` | last 100 | none |
| `qrng-provenance/` | (gitignored, not touched) | per-lane responsibility | none |

### Pre-warm hygiene (the resume-point cap)

When `automations/resume-point-write.ps1` writes a new resume-point, it includes a `pre_warm_reads` array. Spec for keeping this lean:

1. **Cap at 5 entries** (currently uncapped — observed 8+).
2. **Order by score** (highest first), drop the rest.
3. **Always include** the latest plan-artifact + latest PROGRESS entry + the file with most-recent meaningful edit (regardless of score).
4. **Never include** files from other lanes unless `cross_lane_carry_forward[]` lists them (operator-pinned).

### Dirty-tree carry-forward rules

When a master agent resumes mid-storm (multi-agent contention with uncommitted sibling work):

1. **Read-only of sibling files is safe** — Read tool calls preserve other agents' work.
2. **NEVER `git add -A`** — only add named paths in your lane's scope.
3. **NEVER `git checkout <file>`** on a sibling-owned file — that discards their work.
4. **Heartbeat / inbox writes are concurrent-safe** by design (additive append; new turns add rows, never overwrite).
5. **If a sibling file blocks your commit** (locked, race, etc.) → defer the commit, write a marker file in `_shared-memory/deferred/<your-slug>.json` listing what you tried to stage, schedule retry.

### Triggers (when to run)

| Event | Trigger | Mode |
|---|---|---|
| Operator clicks K in launcher | One-shot | interactive (preview + confirm) |
| End of every turn | hook | `dry` (writes report to `_shared-memory/context-pruner/last-dry-run.json`) |
| Resume-point chain > 20 per lane | Rule 7.5 signal | `archive` (auto) |
| Brain row count > 145 | Rule 7.5 approaching | `dry` + surface to operator queue |
| OPERATOR-ACTION-QUEUE > 25 open | Rule 7.5 approaching | `dry` + surface |
| Inbox unread > 25 per lane | Rule 7.5 approaching | `dry` + surface |
| Daily cron 03:00 local | scheduled | `archive` |

### UX (launcher K option)

```
$ context-pruner -Lane sanctum -TaskKeywords "bot-fleet token"

=== CONTEXT CLEANER (lane=sanctum, mode=dry) ===

23 candidates for pruning (total ~47KB freed):

  RESUME-POINTS (3 → archive)
    [score 0.12] resume-points/Sinister Sanctum/2026-05-21T152018Z.json (3d old, other-lane keywords)
    [score 0.15] resume-points/Sinister Sanctum/2026-05-21T152723Z.json (3d, other-lane keywords)
    [score 0.18] resume-points/Sinister Sanctum/2026-05-21T154102Z.json (3d, other-lane keywords)

  INBOX (12 → archive — older than 7d + responded)
    [score 0.05] inbox/sanctum/2026-05-19T*-various.json (12 files, all 4d+ old + closed)

  PLANS (1 → archive)
    [score 0.20] plans/sanctum-complete-2026-05-23T0455Z/ (status: superseded, 8h old)

  KEEP (always):
    [score 1.00] PROGRESS/Sinister Sanctum.md (canonical)
    [score 0.95] plans/sanctum-complete-and-expand-2026-05-23T1145Z/ (active)
    [score 0.92] knowledge/bot-fleet-quick-reference.md (task-relevant)
    ...

Proceed? [y/N/preview-each]
```

### Telemetry

Every run emits to `_shared-memory/context-pruner/log.jsonl`:
```json
{"ts":"...","lane":"sanctum","mode":"dry","candidates":23,"freed_bytes":47104,"task_keywords":"bot-fleet token"}
```

C.13 telemetry rollup pulls this into the daily report (`context_pruner_activity` field).

---

## Anti-patterns

1. **Don't delete on first run.** Default mode is `dry`. Operator must opt into `delete`. Reversibility matters more than disk savings.
2. **Don't apply to brain entries.** `_shared-memory/knowledge/*.md` is the long-term memory; pruning would lose hard-won doctrines. Brain has its own ceiling (Rule 7.5) handled by `brain-index-orphan-check.ps1`.
3. **Don't apply to PROGRESS logs.** They're append-only by canonical Rule 9. Truncating loses ship history.
4. **Don't apply across lanes.** A sanctum-lane run with `-Lane sanctum` MUST NOT touch `_shared-memory/PROGRESS/<other-lane>.md` or `_shared-memory/inbox/<other-lane>/`. Strict ownership.
5. **Don't run mid-turn.** Pruning during active work risks deleting state the current task references. Run between turns or via the K launcher option.
6. **Don't compete with auto-push daemon.** If `index.lock` exists, defer + retry.

---

## Open questions for operator (not blocking spec, blocks implementation)

1. **Pinned-file mechanism.** Should there be a `_shared-memory/pinned.txt` operator-editable list of "never prune" paths? Or operator-side via per-lane `keep.txt`?
2. **Archive vs delete default.** Spec says `dry → archive → delete` ladder; archive moves to `_archive/<class>/<original-path>`. Operator OK with that path?
3. **Daily cron timing.** 03:00 local OK? Coordinate with `sanctum-auto-push` (30-min cron) so they don't clash on lock.
4. **K launcher option scope.** Should K prune only the active lane (per launcher `-Project`) or full fleet (master-only)?
5. **Interactive preview UX.** preview-each = show file head + size + score before yes/no? Or summary table only?

---

## Implementation roadmap (when this spec is approved)

| Phase | Deliverable | Effort | Reversibility |
|---|---|---|---|
| P1 | `context-pruner.ps1 v2` scoring + dry-run mode | 60 min | R0 (read-only) |
| P2 | `-Mode archive` (moves to `_archive/`) | 30 min | R1 (reversible) |
| P3 | Hook: end-of-turn dry-run + last-run.json | 20 min | R1 |
| P4 | Launcher K wires to v2 (interactive preview) | 30 min | R1 |
| P5 | Daily cron at 03:00 (archive mode) | 15 min | R1 |
| P6 | `-Mode delete` (only after 30d in archive) | 20 min | R2 |
| P7 | Telemetry rollup integration | 10 min | R0 |

Total: ~3 hours over 2-3 turns. Doable in one /loop iteration once spec is approved.

---

## Self-application

This spec applies to the Sanctum lane FIRST. Per-project lanes inherit via the same launcher K option (lane scope per `-Project`). Brain doctrine `no-bullshit-tested-before-claimed-doctrine-2026-05-23` Rule 7.5 the spec implements: when any of the 10 quality signals fire, prune first, expand second.
