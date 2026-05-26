# Parallel Execution Plan — iter-78 through iter-86 (2026-05-26)

> **Author:** RKOJ-ELENO :: 2026-05-26 (sinister-term lane)
> **Operator directives (verbatim 2026-05-26 ~22:00Z):** "creatre a plan to complete all of this in parrallel" + "and then do it full autonmous"
> **Composes with:** `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` · `one-terminal-per-project-no-overlap-2026-05-25` · `loop-relentless-pursuit-2026-05-25` · `safe-quality-loops-doctrine-2026-05-24`

## Conflict surface analysis

| iter | New file(s) | commands.py touch? | other shared |
|---|---|---|---|
| 78 | `term/jsonl_index.py` | YES — refactor 4 builtins | none |
| 79 | none | YES — extend cmd_touch/me/peer/agents | heartbeat schema |
| 80 | none | YES — sort in cmd_inbox + cmd_inbox_of + cmd_ask | none |
| 81 | none | YES — new cmd_plans | none |
| 82 | none + `_shared-memory/plans/<slug>/dag.json` spec | YES — new cmd_dag | DAG schema |
| 83 | `automations/render_fleet_topology.py` | optional — small cmd_topology | none |
| 84 | `_shared-memory/groups/*.json` | YES — cmd_ask group fan-out + new cmd_groups | none |
| 85 | `automations/build_brain_index.py` + `_BRAIN_INDEX.json` | YES — cmd_recall refactor | none |
| 86 | `automations/delegate_watchdog.py` + `_shared-memory/completions/` | none (pure automation) | inbox schema |

**The bottleneck:** `projects/sinister-term/source/term/commands.py` is touched by 78/79/80/81/82/83/84/85 (8 of 9 iters). Per `one-terminal-per-project-no-overlap-2026-05-25` this file CANNOT be edited by parallel sub-agents — mesh-coord would lock + the loser blocks 5+ min.

## Two-wave execution

### Wave 1 — 3 parallel sub-agents, INDEPENDENT FILES (no commands.py touch)

| Slice | Iter | Owned path | Effort | Ships |
|---|---|---|---|---|
| W1.A | 83-A | `automations/render_fleet_topology.py` | M (3-4 hrs collapsed to one sub-agent turn) | Mermaid emitter from heartbeats + last-100 fleet-updates rows |
| W1.B | 85-A | `automations/build_brain_index.py` + `_shared-memory/knowledge/_BRAIN_INDEX.json` | M (4-5 hrs collapsed) | Index walker producing JSON with `{title, section_hash, byte_offset, tags}` per knowledge .md |
| W1.C | 86 | `automations/delegate_watchdog.py` + `_shared-memory/completions/.gitkeep` | L (6-8 hrs collapsed) | ACK + retry watchdog with idempotency key + fallback slugs |

**All 3 sub-agents are `general-purpose`** (have Edit/Write). Each owns one new path. No mesh-coord conflicts. No commands.py touches.

**Sub-agent brief format** (each): scope, owned_paths, schema/file format, smoke-test command, no-touch list.

### Wave 2 — Single agent (this lane), SERIAL sterm builtins

After Wave 1's automation files are on disk, sterm builtins are added one-at-a-time in iter order so the COMMANDS dict + /help only have one editor at a time:

1. **iter-78** JSONL tail offset index → ships `term/jsonl_index.py` + refactors cmd_watch/cmd_fleet_updates/cmd_incidents/cmd_crashlog
2. **iter-79** Heartbeat 2.0 → extends cmd_touch/me/peer/agents schema rendering
3. **iter-80** Priority inbox sort → in cmd_inbox + cmd_inbox_of + cmd_ask
4. **iter-81** `/plans` builtin → new cmd_plans
5. **iter-82** Task DAG → new cmd_dag (consumes the dag.json schema)
6. **iter-83-B** `/topology` builtin → thin wrapper invoking `automations/render_fleet_topology.py`
7. **iter-84** Broadcast groups → cmd_ask group fan-out + new cmd_groups + `_shared-memory/groups/frontend-lanes.json` + 2 others
8. **iter-85-B** `cmd_recall` refactor → consume `_BRAIN_INDEX.json` for O(log n) lookup

Each iter = one commit on `agent/sinister-term/<topic>` with `Shipped/Smoke/Refs` body per `frequent-detailed-commits-per-agent-2026-05-25`. Tests added per iter (target ~15 per iter).

### Wave 3 — Reconciliation commit (optional)

If Wave 1 sub-agents return with anything that REQUIRES a commands.py wire-up beyond what iter-83-B/85-B already cover (e.g. iter-86 wants a `/delegates` builtin to view in-flight delegates), that wire-up ships as iter-87 in this lane.

## Concurrency rules in effect

1. **Wave 1 sub-agents do NOT git add / git commit** — they only write files. The parent (this lane) does ONE atomic commit per slice after all 3 return. This avoids the concurrent-staging race that swallowed iter-77 into another agent's commit earlier today.
2. **Wave 2 iters serialize through this lane.** No sub-agents spawned for commands.py edits.
3. **mesh-coord locks** registered for each Wave 1 owned_path before sub-agent spawn; released on commit.
4. **Quality monotonic** — pytest runs after each Wave 2 iter; ship only if green AND test count goes UP.

## Estimated wall-clock

| Wave | Activity | Wall-clock |
|---|---|---|
| 0 | This plan + spawn briefs | 5 min |
| 1 | 3 parallel sub-agents writing automation files | ~5-10 min (sub-agents wall-clock in parallel) |
| 1.5 | Smoke + commit Wave 1 | 5 min |
| 2 | Serial iter-78 → iter-85-B in this lane | ~3-5 hours focused lane-time across multiple turns |
| 3 | Reconciliation if needed | 30 min |

**Total ~3-6 hours focused lane-time + 10 min sub-agent wait.** Vs serial estimate of 30-40 hours.

## Risk + mitigations

| Risk | Mitigation |
|---|---|
| Wave 1 sub-agent writes broken Python | Smoke each file via `python -c "import <module>"` before committing |
| Sub-agents collide on shared schema (e.g. inbox JSON) | Iter-86 owns inbox-schema extension; iter-80 reads same schema in Wave 2 |
| commands.py grows past brain-degradation-signal "script >1500 lines" | Wave 2 iter-81+ should consider splitting `term/builtins/` into per-builtin modules — track as iter-87+ refactor candidate |
| concurrent-staging race from other lanes (iter-77 → 7d0d49e swallow) | Use `git add -- <specific-files>` + immediate commit with retry-on-lock loop |
| Wave 1 sub-agent runs over budget | Per CLAUDE.md `safe-quality-loops` rule: stop and report partial work; ship the slice that succeeded |

## Definition of "done"

- All 3 Wave 1 files exist on disk, smoke-test as `python -c "import X" / X --help`
- All 6 Wave 2 iters merged with green pytest each
- Each commit follows `Shipped/Smoke/Refs` body format
- Resume-points written per iter
- Brain entries for any new doctrines (e.g. atomic-rename-heartbeat from iter-79)
- `_shared-memory/knowledge/_INDEX.md` updated for new entries
- This plan's status flipped to **COMPLETE** with link to final iter-86 commit

## Live status (updated each iter)

- [x] Wave 0 — plan written
- [ ] Wave 1.A — iter-83 fleet topology renderer (sub-agent in flight)
- [ ] Wave 1.B — iter-85 brain knowledge index (sub-agent in flight)
- [ ] Wave 1.C — iter-86 delegate watchdog (sub-agent in flight)
- [ ] Wave 1.5 — smoke + atomic commit
- [ ] Wave 2 iter-78 — JSONL tail offset index
- [ ] Wave 2 iter-79 — Heartbeat 2.0
- [ ] Wave 2 iter-80 — Priority inbox sort
- [ ] Wave 2 iter-81 — /plans builtin
- [ ] Wave 2 iter-82 — Task DAG /dag builtin
- [ ] Wave 2 iter-83-B — /topology builtin (thin wrapper)
- [ ] Wave 2 iter-84 — Broadcast groups
- [ ] Wave 2 iter-85-B — /recall refactor to use _BRAIN_INDEX.json
