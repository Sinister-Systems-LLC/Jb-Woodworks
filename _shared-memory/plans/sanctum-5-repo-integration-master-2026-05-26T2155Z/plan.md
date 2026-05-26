# Master Plan :: 5-Repo Integration (hivemind + rmux + routa + serenedb + headroom)

**Generated:** 2026-05-26T21:55Z by sanctum (iter-24)
**Source:** `_shared-memory/knowledge/github-input-best-5-repo-synthesis-2026-05-26.md`
**Operator directive:** "deeply audit and take apart each one of these in parrallel then make a plan to complete or add whatver you come up with"

## Stage gating

This plan is the Stage-5 output for the hypothetical "github-input-best" intake batch. All 5 repos were Stage-3 deep-audited via 5 parallel sub-agents. Stage-4 synthesis at the brain entry above.

## P0 — ship iter-25 (next master turn)

| # | Item | File(s) | Acceptance | Smoke | Composes-with |
|---|---|---|---|---|---|
| P0-1 | `wait_for_sentinel` in `sinister_swarm.py` (rmux+routa convergent) | `automations/sinister_swarm.py` (~30 LOC added) | spawned slice writes `{"sentinel":"__SLICE_DONE__"}` atomically; coordinator polls `result_path` exists + parses sentinel | `python automations/sinister_swarm.py smoke --wait-mode sentinel` | jcode-parity-loop-swarm-upgrades-2026-05-26 |
| P0-2 | `wait_mode = immediate \| after_all` parameter to `fanout()` (routa) | `automations/sinister_swarm.py` (~30 LOC added, default "after_all") | `--wait-mode immediate` returns within 5s for 3 dummy slices, registers DelegationGroup at `_shared-memory/swarm-groups/<prefix>.json` | `python automations/sinister_swarm.py fanout --wait-mode immediate --slices-file <smoke-3.json>` returns <5s | full-relentless-swarm-fanout-mindset-doctrine-2026-05-25 (rule 4) |
| P0-3 | `revision` int on heartbeat JSONs (rmux+hivemind+serenedb convergent) | `automations/start-sinister-session.ps1` heartbeat-write block; `automations/loop-relentless-watchdog.ps1` consumer; `automations/detect-similar-agents.ps1` consumer | every heartbeat write bumps `revision` by 1; watchdog stall-signal #4 added: `revision_now == revision_3_ticks_ago` | `python -c "import json,pathlib; d=json.loads(pathlib.Path('_shared-memory/heartbeats/sanctum.json').read_text()); print(d.get('revision'))"` returns int | jcode-parity-loop-swarm-upgrades-2026-05-26 |

## P1 — ship iter-26 (next-next master turn)

| # | Item | File(s) | Acceptance | Smoke | Composes-with |
|---|---|---|---|---|---|
| P1-1 | `automations/sinister_perf_ema.py` NEW (hivemind port) | NEW file (~70 LOC, port `hivemind/utils/performance_ema.py:7-71`) | bias-corrected EMA returns finite >0 after 5 updates | `python -c "from automations.sinister_perf_ema import PerformanceEMA; e=PerformanceEMA(); [e.update(1) for _ in range(5)]; print(e.samples_per_second)"` | jcode-parity-loop-swarm-upgrades-2026-05-26 |
| P1-2 | `automations/eve_learn.py` NEW (headroom port) — failure-mining → CLAUDE.md auto-block | NEW file (~150 LOC); reads `_shared-memory/eve-crash-log.jsonl` + `eve-incidents.jsonl` + `eve-training-loop.jsonl` | writes fenced `<!-- AUTO:eve-learn START -->...<!-- AUTO:eve-learn END -->` block to CLAUDE.md; intent-hash dedup + 21-day TTL + min-evidence=5 + cap=15 | `python automations/eve_learn.py --dry-run --tail 50` prints proposed block | forever-improve-review-doctrine-2026-05-24, no-bullshit-tested-before-claimed-doctrine-2026-05-23 (rule 5) |
| P1-3 | Settings/config snapshot-before-mutate (headroom #4) | edit `automations/canonical-protections-check.ps1` | snapshot `~/.claude/settings.json` → `...settings.json.eve-canonical-backup` before any auto-heal | `& '...canonical-protections-check.ps1' -DryRun` shows backup path + diff | do-not-revert-operator-canonical-protections-2026-05-23 |

## P2 — backlog (WATCH-list re-evaluation per brain entry)

| # | Item | Trigger |
|---|---|---|
| P2-1 | `TimedStorage` heap-backed lock TTL (hivemind) → replace `SinisterMeshCoordSweep` schtask | after P0-2 wait_mode ships; mesh-coord proven stable |
| P2-2 | Hybrid BM25+HNSW (serenedb idea) → `sinister-memory/embed.py` | when embed.py reaches P1 maturity |
| P2-3 | `broadcast(panes, Input)` typed partial-failure (rmux) | when sinister-term needs sync multi-pane |
| P2-4 | Path-hierarchy tokenizer (serenedb) → `_shared-memory/knowledge/<slug>` routing | when brain row count > 250 |
| P2-5 | Stacked review gate Tier model (routa) → `forever-improve.ps1` extension | when tier-blur becomes painful |
| P2-6 | Demo-as-spec capability matrix (serenedb #5) → `_shared-memory/knowledge/_DEMO-MATRIX.md` | iter-30+ idle window |

## REJECT — operator hard-canonical anti-patterns (do NOT adopt)

- gRPC/protobuf for inboxes (hivemind) — JSONL stays
- 740MB C++ monolith (serenedb) — Python-first policy
- 90 tmux commands (rmux) — feature-bloat for compat we don't need
- Bilingual CLAUDE.md (routa) — English-only
- Silent drop on unknown child (routa `orchestration/mod.rs:702-705`) — dead-letter routing instead

## Verification at end of plan

When all P0 items ship + smoke green:
- `git log --oneline agent/sinister-sanctum/iter25-* | head -3` shows 3 commits (one per P0 item) OR 1 combined commit with all 3
- `python automations/sinister_swarm.py fanout --wait-mode immediate --slices-file <smoke-3.json>` returns within 5s
- Heartbeat JSONs have `revision` int field, count incremented per write

## Composes-with

- `_shared-memory/knowledge/github-input-best-5-repo-synthesis-2026-05-26.md` (this plan's parent)
- `_shared-memory/knowledge/new-project-intake-flow-doctrine-2026-05-26.md` (this plan is the Stage-5 output template)
- `_shared-memory/knowledge/jcode-parity-loop-swarm-upgrades-2026-05-26.md` (P0-1 + P0-2 + P0-3 extend the jcode parity work)
