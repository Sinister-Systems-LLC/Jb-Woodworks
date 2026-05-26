# Brain Entry :: GitHub Input/Best — 5-Repo Deep-Audit Synthesis 2026-05-26

> **Author:** RKOJ-ELENO :: 2026-05-26
> **Status:** active (5 ADOPT-NOW items extracted; queued for iter-25 ship)
> **Decay:** preference / 0.9 / 365
> **Composes with:**
> - `we-have-the-source-read-it-doctrine-2026-05-25.md`
> - `github-first-sourcing-doctrine-2026-05-24.md`
> - `new-project-intake-flow-doctrine-2026-05-26.md` (this is the canonical impl going forward)
> - `jcode-parity-loop-swarm-upgrades-2026-05-26.md`
> - `agent-freeze-1-10min-rootcause-fix-2026-05-26.md`
> - `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md`

## Operator directive (verbatim 2026-05-26)

*"I need you to revbiew these github repos i have been looking at deeply and see where we can use their ideas in our work. deeply audit and take apart each one of these in parrallel then make a plan to complete or add whatver you come up with."*

## Approach

5 parallel sub-agents (per `FULL-RELENTLESS-SWARM-FAN-OUT-MINDSET`), each read source directly (no RE), cited FILE:LINE, returned a 5-idea gap table + verdicts + integration sketches. All under 600 words each.

Per-repo brain entries deferred to next iter; this file is the cross-repo synthesis.

## Per-repo one-liners

| Repo | One-line pitch (Sanctum terms) | Top ADOPT-NOW |
|---|---|---|
| `hivemind-master` | Decentralized PyTorch over Internet — peer-to-peer DHT + fault-tolerant averaging | `PerformanceEMA` (bias-corrected throughput) + `TimedStorage` (heap-backed TTL dict) |
| `rmux-main` | Rust-rewritten tmux w/ daemon-backed typed SDK — `wait_for_text` API replaces polling | `revision counter` on heartbeats + `wait_for_sentinel` to kill polling loop + `EnsureSession` idempotent spawn |
| `routa-main` | Workspace-first multi-agent coordination — Kanban IS the bus + ACP wake-via-prompt-injection | `wait_mode = immediate \| after_all` for `sinister_swarm.fanout` + child-completion wake + orchestration-shell pattern (`start-sinister-session.ps1` → Python) + baby-step commit budget |
| `serenedb-main` | Postgres-wire single-binary fusing BM25 + HNSW + columnar OLAP into one inverted index | WAL recovery for inverted index (idea-only, not code) + demo-as-spec discipline (capability matrix) |
| `headroom-main` | Local-first Rust+Python compression layer + failure-mining for CLAUDE.md auto-writes | `headroom learn` failure-mining → `automations/eve_learn.py` writes auto block into CLAUDE.md + config snapshot+restore for `do-not-revert` guarantee |

## Convergent themes (multiple repos recommend the same primitive)

### Theme A — Replace polling with event/sentinel waits
- **rmux** `wait_for_text` (`crates/rmux-sdk/src/handles/pane.rs:210-219`)
- **routa** `wake_parent` via ACP prompt-injection (`crates/routa-core/src/orchestration/mod.rs:794-862`)
- **hivemind** ForkProcess + MPFuture `await_ready` (`hivemind/dht/dht.py:22-77`)
- **Sanctum action:** add `wait_for_sentinel(result_path, needle, timeout)` to `sinister_swarm.py`; producer-side: each spawned slice writes `{"sentinel":"__SLICE_DONE__"}` atomically.

### Theme B — Revision counters + monotonic state (vs mtime guessing)
- **rmux** `PaneSnapshot { revision }` (`crates/rmux-sdk/src/snapshot.rs:32-51`)
- **hivemind** `PerformanceEMA` bias-corrected EMA (`hivemind/utils/performance_ema.py:7-71`)
- **serenedb** `Snapshot::GetSequenceNumber` MVCC (`server/search/inverted_index_shard.h:76-122`)
- **Sanctum action:** add `revision` int to heartbeat JSON (incremented on every write); consumers (`detect-similar-agents`, `auto-start-if-no-agent`, `loop-relentless-watchdog`) compare `revision_now == revision_60s_ago` for genuine idle/stuck detection.

### Theme C — Failure-mining + auto-doctrine
- **headroom** `headroom learn` writes auto-block into CLAUDE.md (`headroom/learn/analyzer.py:1-58` + `headroom/learn/plugins/claude.py`)
- **routa** local issue records before GitHub (`AGENTS.md:85-95`)
- **Sanctum action:** new `automations/eve_learn.py` reads `eve-crash-log.jsonl` + `eve-incidents.jsonl` + `eve-training-loop.jsonl`, classifies recoveries with intent-hash dedup + 21-day TTL + min-evidence=5, writes fenced `<!-- AUTO:eve-learn -->` block in CLAUDE.md.

### Theme D — Long-file → orchestration-shell pattern
- **routa** ADR-0006 orchestration-shell + `entrix analyze long-file` (`docs/adr/0006-orchestration-shell-pattern.md`)
- **headroom** workspace crate split (`Cargo.toml:1-18`)
- **Sanctum action:** `automations/start-sinister-session.ps1` is 700+ lines. Plan extraction of `Build-Phrase`, `Prompt-AgentModes`, `agent-branch-router` calls into Python workflow modules per `no-bat-no-ps1-doctrine`.

### Theme E — Idempotent spawn / single-source-of-truth state
- **rmux** `EnsureSession { CreateOrReuse, ReuseOnly, CreateOnly }` (`crates/rmux-sdk/src/ensure.rs:17-99`)
- **hivemind** `TimedStorage` heap-backed dict (`hivemind/utils/timed_storage.py:50-60`)
- **Sanctum action:** codify `auto-start-if-no-agent-doctrine` Stage 3 (auto-spawn target via `start-sinister-session.ps1`) as an `EnsureSession`-style policy + replace `SinisterMeshCoordSweep` schtask with in-process TTL eviction.

## ADOPT-NOW shortlist (P0 next iter)

Ranked by impact × low-cost:

1. **`wait_for_sentinel` in `sinister_swarm.py`** (rmux + routa converge) — removes the polling loop; sub-second wake vs 25ms-25s jitter. Patch shape in `sinister_swarm.py` ~30 LOC.
2. **`wait_mode = immediate` flag in `fanout()`** (routa) — unlocks "master never idles" rule 4 of `FULL-RELENTLESS-SWARM-FAN-OUT-MINDSET`. ~30 LOC.
3. **Revision counter on heartbeats** (rmux + hivemind + serenedb converge) — replaces mtime polling everywhere. Edit `start-sinister-session.ps1` heartbeat writer + consumers. ~10 LOC each.
4. **`PerformanceEMA` for runaway-iter detection** (hivemind) — `automations/sinister_perf_ema.py` port of 65-line file; consumed by `loop-relentless-watchdog.ps1`. Drop-in.
5. **`eve_learn.py` failure-mining** (headroom) — `automations/eve_learn.py` writes auto-block into CLAUDE.md from `eve-incidents.jsonl`. Composes with `forever-improve.ps1 -Action Review`. ~150 LOC.

## WATCH-list (re-evaluate after P0 ships)

- **`TimedStorage` heap-backed lock TTL** (hivemind) — replaces `SinisterMeshCoordSweep` schtask; revisit after wait-sentinel lands.
- **Hybrid BM25+HNSW** (serenedb) — wait until `projects/sinister-memory/src/sinister_memory/embed.py` matures.
- **`broadcast(panes, Input)` typed partial-failure** (rmux) — `fleet-update.ps1` covers 80%; revisit if sinister-term needs sync multi-pane.
- **Pluggable analyzers (path-hierarchy tokenizer)** (serenedb) — useful for `_shared-memory/knowledge/<slug>` routing; not urgent.
- **Stacked review gate (Harness Monitor → Entrix Fitness → Gate Specialist)** (routa) — `forever-improve.ps1` works; revisit if tier-blur becomes painful.

## REJECT (operator hard-canonical anti-patterns)

- **gRPC + protobuf for inboxes** (hivemind) — our JSONL inboxes are Grep-able; don't binarize.
- **740 MB C++ monolith** (serenedb) — violates `no-bat-no-ps1-doctrine` Python-first policy.
- **90 tmux-compatible commands** (rmux) — feature-bloat for source-compat we don't need.
- **Hidden daemon re-exec via env flag** (rmux `INTERNAL_DAEMON_FLAG`) — couples CLI + daemon lifecycle; our `eve.py` + per-mintty Claude have cleaner separation.
- **191 PyPI releases burning 10GB** (headroom) — release cadence outpaced cleanup; our `forever-improve.ps1 Tally/Drain` is the right answer.
- **bilingual CLAUDE.md mid-paragraph** (routa) — Sanctum stays English-only.
- **Silent drop on "Report from unknown child agent ... ignoring"** (routa `orchestration/mod.rs:702-705`) — Sanctum routes to dead-letter, not warn-and-drop.

## Composes-with reasoning

- `new-project-intake-flow-doctrine-2026-05-26.md` — this synthesis IS the Stage 4 output for a hypothetical "github-input-best" lane. Future operator drops use the canonical 6-stage pipeline.
- `jcode-parity-loop-swarm-upgrades-2026-05-26.md` — ADOPT items #1, #2 directly extend `sinister_swarm.py` jcode parity; ADOPT #3 extends loop-watchdog parity.
- `we-have-the-source-read-it-doctrine-2026-05-25.md` — all 5 sub-agents READ source, no RE.
- `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25.md` — 5 parallel sub-agents = textbook fan-out within `MAX_SLICES=5` cap.
- `automate-everything-no-operator-admin-2026-05-25.md` — operator clicked nothing; all 5 audits + synthesis ran autonomously.

## Next-iter plan (iter-24/iter-25)

See `_shared-memory/plans/sanctum-5-repo-integration-master-2026-05-26T2155Z/plan.md` (created same iter as this brain entry).

P0 (iter-25): ship ADOPT-NOW #1 + #2 + #3 (wait_for_sentinel + wait_mode + revision counter).
P1 (iter-26): ship ADOPT-NOW #4 (PerformanceEMA) + #5 (eve_learn.py).
P2 (iter-27+): WATCH-list re-evaluation.
