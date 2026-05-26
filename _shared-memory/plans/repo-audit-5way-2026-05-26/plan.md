# 5-Repo Audit + Integration Plan (2026-05-26)

> **Author:** RKOJ-ELENO :: 2026-05-26 (sinister-term lane, operator directive)
> **Operator directive (verbatim 2026-05-26 ~21:45Z):** "make sure each new project takes my idea, deeply reviews it with all knowledge we have prior and then does a lot of github research to look for repos that have code we can use to get it working. then compile all that and see where we can make things better… deeply audit and take apart each one of these in parallel then make a plan to complete or add whatever you come up with."

## Repos audited (5 parallel Explore sub-agents)

| Repo | Path | Language | What it is |
|---|---|---|---|
| rmux | `C:\Users\Zonia\Desktop\Github Input\Best\rmux-main` | Rust (~120K LOC, 12 crates) | Modern tmux replacement with daemon-backed SDK + ratatui widget. Detachable agent terminals. |
| mermaid-rs-renderer (mmdr) | `…\mermaid-rs-renderer-master` | Rust (pure, no JS) | Mermaid diagram renderer (23 diagram types) → SVG/PNG. Parser + IR + 3-stage layout + render. |
| hivemind | `…\hivemind-master` | Python (~11.4K LOC) | Decentralized deep-learning swarm: DHT + Mixture-of-Experts + butterfly all-reduce. |
| serenedb | `…\serenedb-main` | C++ | Embedded analytics DB: RocksDB LSM + IResearch inverted index + VPack encoding + WAL. |
| routa | `…\routa-main` | TypeScript (Next.js) + Rust (Axum) | Multi-agent coordination platform: JSON-RPC dispatcher + Kanban-backed task DAG + trace records. |

## Cross-cutting findings — patterns that 2+ audits agreed are valuable

| Pattern | rmux | mmdr | hivemind | serenedb | routa | Verdict |
|---|---|---|---|---|---|---|
| **Append-only log + offset index** (for jsonl tails) | ✓ event ring | | | ✓ tick watermarks | | **HIGH** — S effort, fixes /watch + /fu + /incidents + /crashlog linear scan |
| **Heartbeat enrichment** (capabilities + load + expiration) | ✓ session leases | | ✓ DHT TTL + load | | | **HIGH** — S effort, unlocks work-stealing |
| **Priority routing** (high/normal/low queues) | | | ✓ runtime selectors | | ✓ priority subscriptions | **HIGH** — S effort, easy add to /inbox sort |
| **Task DAG with deps** (parallel-safe execution) | ✓ command queue groups | ✓ DAG renderer | ✓ Task DAG file format | | ✓ wait-group semantics | **HIGH** — M effort, unblocks parallel ships |
| **Atomic multi-writer** (rename-into-place) | | | | ✓ lockfile + atomic rename | ✓ idempotency keys | **MED** — M effort, eliminates heartbeat race conditions |
| **Capability matching** (route to right specialist) | | | ✓ tiered peer roles | | ✓ scoring heuristics | **MED** — M effort, smarter [DELEGATE] routing |
| **Broadcast groups** (`@frontend-lanes` fan-out) | | | | | ✓ workspace-scoped SSE | **MED** — M effort, /ask @group |
| **Plan/topology visualization** | | ✓ flowchart/DAG/mindmap | | | | **MED** — M effort, fleet topology + plan DAG renderers |
| **Pure state machine + detached I/O** | ✓ rmux-core isolation | | | | | **LOW** — L effort, architectural |

## Iter-78 through iter-86 ship queue (priority order, ready-to-execute)

Each iter is a single PR. All composable with the existing sterm builtin pattern (`cmd_<name>` + tests + /help + dispatch + COMMANDS row).

### Iter-78: JSONL tail offset index → /watch + /fu + /incidents + /crashlog speedup [S]
**Source:** serenedb tick watermarks (flush_feature.h:47-81) + rmux event ring + coalescing.
**Ship:** New module `term/jsonl_index.py` maintaining `_shared-memory/_OFFSETS.json` with `{path, byte_offset, line_count, last_record_ts}` for each tracked jsonl. Refactor `cmd_watch`, `cmd_fleet_updates`, `cmd_incidents`, `cmd_crashlog` to seek to offset + stream last-N instead of full read.
**Tests:** 12-15. **Effort:** S (1-2 hrs). **Value:** O(1) tails on big logs; currently linear-scan of fleet-updates.jsonl (~5MB) per `/fu` call.

### Iter-79: Heartbeat 2.0 — add `capabilities` + `load` + `expiration` fields [S]
**Source:** hivemind DHT declarations (`dht_handler.py:22-78`) + rmux session leases.
**Ship:** Extend the heartbeat schema sterm writes via `cmd_touch` (and the auto-heartbeat on each keystroke): add `capabilities: [str]`, `load: {queue_depth, current_task}`, `expiration_ts`. Update `cmd_peer` + `cmd_agents` to render the new fields with `(stale-expired)` badge after TTL.
**Tests:** 10-12. **Effort:** S (1-2 hrs). **Value:** Setup for work-stealing (iter-81); makes `/agents` instantly show who's swamped vs idle.

### Iter-80: Priority inbox sort — `priority=high|normal|low` field [S]
**Source:** routa lane-automation-state.ts:20-44 scoring heuristics + hivemind runtime priority.
**Ship:** `cmd_inbox` + `cmd_inbox_of` sort by `priority` (DESC) then `mtime` (DESC). Default priority `normal` when missing. New `/ask` flag `--priority high` writes the field.
**Tests:** 10-12. **Effort:** S (1 hr). **Value:** Critical [DELEGATE]s no longer get buried under chat noise.

### Iter-81: `/plans` builtin — list `_shared-memory/plans/<slug>/plan.md` with age + size [S]
**Source:** companion to `/progress-of` triad. Operator request from this turn.
**Ship:** `cmd_plans` lists all plan directories sorted by mtime, `/plans <substring>` drills into one plan, `/plans --owner sinister-term` filters to lane.
**Tests:** 14-16. **Effort:** S (1-2 hrs). **Value:** "what plans are in flight?" answer from inside sterm.

### Iter-82: Task DAG file format — `_shared-memory/plans/<slug>/dag.json` [M]
**Source:** hivemind Task DAG + routa wait-group semantics + mmdr DAG renderer.
**Ship:** New schema (`tasks: [{id, type, owner_path, status}]` + `dependencies: [{from, to}]`). New builtin `/dag <plan-slug>` renders ASCII tree + status. Adjacent .md still authoritative for narrative.
**Tests:** 18-22. **Effort:** M (3-4 hrs). **Value:** Parallel-safe execution; fan-out planner knows what's blocked.

### Iter-83: Fleet topology Mermaid renderer [M]
**Source:** mmdr parser + IR + flowchart serializer (`ir.rs:1-200`, `lib.rs:205-227`).
**Ship:** New automation `automations/render_fleet_topology.py` that reads `_shared-memory/heartbeats/*.json` + last 100 fleet-updates.jsonl rows → emits Mermaid flowchart DSL → renders to SVG via mmdr binary (if installed) or just writes the .mmd file for the dashboard to render. New sterm builtin `/topology` prints ASCII or saves SVG.
**Tests:** 12-15. **Effort:** M (3-4 hrs). **Value:** Operator can see who's talking to who at a glance.

### Iter-84: Broadcast groups — `_shared-memory/groups/<group>.json` manifest [M]
**Source:** routa workspace scoping + the `@group` syntax.
**Ship:** Pre-defined groups: `@frontend-lanes` (panel, dashboard, sterm), `@backend-lanes` (kernel-apk, snap-api, …), `@all`. `cmd_ask` parses `@group` prefix, fans out via `term.swarm.broadcast` to each member. `/groups` builtin lists members.
**Tests:** 15-18. **Effort:** M (3-4 hrs). **Value:** `/ask @frontend-lanes "fix the theme"` works in one command.

### Iter-85: Knowledge brain index — `_shared-memory/knowledge/_BRAIN_INDEX.json` [M]
**Source:** serenedb VPack offset tables + IResearch consolidation policy.
**Ship:** New automation `automations/build_brain_index.py` walks `knowledge/*.md`, extracts title + section hashes + byte offsets + tags (from filename suffix). Speeds up `cmd_recall` (currently linear-greps all .md files; now seek-and-stream from index). Rebuilt incrementally on each push by a post-commit hook.
**Tests:** 18-22. **Effort:** M (4-5 hrs). **Value:** `/recall` from O(n) grep to O(log n) lookup; ~50x faster on the 150+ brain entries.

### Iter-86: ACK + retry router for [DELEGATE] messages [L]
**Source:** routa session fallback (delegation.rs:55-98) + hivemind matchmaking timeouts.
**Ship:** Each [DELEGATE] inbox message includes `{ackTimeoutMs, fallbackSlugs, idempotencyKey}`. New automation `automations/delegate_watchdog.py` (60s schtask) scans for delegates with no `_shared-memory/completions/<sessionId>/<delegateId>.json` after the timeout; auto-resends to first available `fallbackSlug`. Idempotency key prevents duplicate execution if both children eventually run.
**Tests:** 22-26. **Effort:** L (6-8 hrs). **Value:** Critical delegates never silently die; auto-retries with escalation.

## Out-of-scope from this audit (parked)

- **Pure-Rust port of sterm to a daemon-backed SDK** (rmux pattern) — would unlock multi-pane sterm sessions but L+++ effort, defer to Track B when Track A stabilizes.
- **Full DHT for agent discovery** (hivemind kademlia) — overkill for our 12-lane file-based fleet.
- **Embedded RocksDB for shared-memory** (serenedb LSM) — daemon dependency; we want zero-daemon reads.
- **gRPC/Protobuf wire format** (hivemind + routa) — JSON is fine at our scale.
- **Postgres + Drizzle ORM** (routa) — flat files are the source of truth; no SQL layer needed.

## What ships THIS turn (still in iter-77 envelope)

- ✅ `automations/clean-stale-git-locks.py` — removes >120s-stale `.git/*.lock` files; eliminates 1-10min terminal freezes (operator-reported pain)
- ✅ `SinisterStaleLockCleaner` schtask registered (1-min cadence, current-user, RunLevel default)
- ✅ Brain entry: `_shared-memory/knowledge/stale-git-lock-auto-cleanup-2026-05-26.md`
- ✅ This plan: `_shared-memory/plans/repo-audit-5way-2026-05-26/plan.md`
- ✅ `/queue` builtin shipped (iter-77, +25 tests, pytest 648)

## Estimated total effort: iter-78 through iter-86 = ~30-40 hrs of focused lane-time

Composes with `loop-relentless-pursuit-2026-05-25` and `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25`: iter-78/79/80 are independent and could be a swarm fan-out from sterm into 3 parallel sub-agents next session.

## Trigger-on flow (operator's "this needs to be flow when i create project")

When a new project is spawned via EVE picker OR any agent receives a non-trivial directive:

1. **Re-read operator's idea** (verbatim from `_shared-memory/operator-utterances.jsonl`).
2. **Deep brain review** — `forge-memory recall <topic> --limit 8` + grep `_shared-memory/knowledge/` for prior art on the topic.
3. **GitHub research** — invoke `automations/github-prior-art.ps1 -Topic <feature>` (already exists; see CLAUDE.md cold-start step 9).
4. **Parallel repo audits** — for the top 5 prior-art candidates, fan-out 5 Explore sub-agents with the audit template (this turn's template at `_shared-memory/templates/repo-audit-template-2026-05-26.md` — TODO future iter to extract this template).
5. **Synthesize** — aggregate findings into a plan doc under `_shared-memory/plans/<slug>/`.
6. **Ship in iter order**, S → M → L, with smoke-tested commits per `frequent-detailed-commits-per-agent-2026-05-25`.

Per `full-relentless-swarm-fanout-2026-05-25`: the synthesis step ALSO runs in parallel with the next-iter shipping; don't serialize.
