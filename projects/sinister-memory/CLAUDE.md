# CLAUDE.md — Sinister Memory

**Author:** RKOJ-ELENO :: 2026-05-25
**Lane:** sinister-memory
**Root:** `D:\Sinister Sanctum\projects\sinister-memory\`
**Status:** scaffolded 2026-05-25 per operator hard-canonical 2026-05-25T07:29:17Z — *"add to eve exe a project start for Sinister Memory and complie all thigsn he needs there"*

## Lane scope

`sinister-memory` is the **fleet-wide persistent memory layer** — the durable knowledge graph that survives session restarts, agent rotations, and across-machine sync with Leo. Composes with the existing 11 Sanctum memory primitives (brain/PROGRESS/operator-utterances/fleet-updates/inbox/etc.) by providing a **typed, queryable, decay-aware** index on top.

Inspired-by audit at `_shared-memory/knowledge/memory-audit-jcode-rufus-obsidian-understand-2026-05-24.md`. Cherry-picks: Haiku verify-grader wrapper · Supersedes-edge graph · cluster-dedupe pass.

## In-scope for this lane

- `src/sinister_memory/` — Python package providing `store`, `recall`, `supersede`, `decay`, `cluster`, `verify` primitives. Pure-Python, no daemon (queries live from disk; writes via atomic-rename).
- `tests/` — pytest suite hitting every primitive with synthetic and real-brain-row fixtures.
- `docs/` — design notes (architecture / decay-model / verify-grader prompts / cherry-pick rationale).
- Integration: hooks into existing `_shared-memory/knowledge/_INDEX.md` + Ruflo MCP `agentdb_*` tools + `forge-memory` CLI.

## Out-of-scope for this lane (route to owner)

- Operator utterance tracking → `_shared-memory/operator-utterances.jsonl` (operator-utterance-tracking-doctrine-2026-05-24) owned by sanctum.
- Fleet-update mesh → `automations/fleet-update.ps1` owned by sanctum.
- Brain `_INDEX.md` schema → owned by sanctum (this lane consumes, doesn't redefine).

## Cold-start for any agent spawned in this lane

1. Read root `D:\Sinister Sanctum\CLAUDE.md` for fleet-wide doctrine.
2. Read this file for lane scope.
3. Read `_shared-memory/knowledge/memory-audit-jcode-rufus-obsidian-understand-2026-05-24.md` for the gap analysis that defines this lane's work.
4. Read `src/sinister_memory/__init__.py` to see current primitives surface.
5. Check `_shared-memory/PROGRESS/Sinister Memory.md` for iter history.

## Branch + push

- Branch convention: `agent/sinister-memory/<short-topic>-<utc-date>`
- Push target: Sinister-Sanctum (umbrella; per single-repo-push-policy-2026-05-25 carve-outs)

## Composes with

- `memory-audit-jcode-rufus-obsidian-understand-doctrine-2026-05-24` (gap-analysis source)
- `loop-relentless-pursuit-doctrine-2026-05-25` (lane default loop=relentless)
- `frequent-detailed-commits-per-agent-2026-05-25` (commit format)
- `sanctum-scope-discipline-doctrine-2026-05-24` (route out-of-scope work to owners)
