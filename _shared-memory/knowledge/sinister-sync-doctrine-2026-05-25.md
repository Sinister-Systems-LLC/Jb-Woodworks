<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: doctrine
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->
# Sinister Sync — Project Hive-Mind Doctrine (operator hard-canonical 2026-05-25T~03:25Z)

> Operator verbatim (1): *"ok lets swarm here i need more power and resources we need to get eveexe done how can we do that like super charge a projoect to finish it fast and realy realy good. you have the power do it and make it a new feature called Sinister Sync"*
>
> Operator verbatim (2 — design intent clarification): *"the idea behind it is you sync your brain with the project and super charge it like make each project become alive like a hive mind"*

**Binding fleet-wide.** Sinister Sync is the canonical name for project-scoped hive-mind context sharing: every agent on a given project consumes + contributes to the same live brain so velocity compounds instead of duplicating.

## The 5-layer architecture (composition of shipped building blocks)

| Layer | Building block (already shipped) | Sinister Sync role |
|---|---|---|
| **L1: Per-project knowledge graph** | `understand-anything` plugin (CLAUDE.md cold-start step 0) | Single canonical AST + import-graph + recent-changes summary, regenerated on commit hook. Stored at `_shared-memory/sinister-sync/<project-key>/graph.json`. |
| **L2: Semantic project memory** | Ruflo `mcp__ruflo__agentdb_hierarchical-store` + `hierarchical-recall` | Namespaced `project:<key>` store; every meaningful agent observation auto-writes; cold-start auto-recalls top-K relevant rows. |
| **L3: Live broadcast bus** | Ruflo `mcp__ruflo__hive-mind_broadcast` + `hive-mind_memory` + sinister-bus inbox | When agent A discovers X, agent B (same project) gets it in <5s via broadcast; durable copy in inbox. |
| **L4: Cold-start pre-warm** | `start-sinister-session.ps1` `Build-Phrase` already injects `DETECT-SIMILAR-AGENTS:` + `RESUME CONTEXT` | EXTEND to also inject `SINISTER-SYNC PROJECT-BRAIN:` = top-N graph nodes + top-K semantic recalls + tail of project-broadcast bus. |
| **L5: Swarm orchestrator** | Existing `Agent` tool (subagent_type=Explore/general-purpose) + `SWARM MODE on` flag | Per-spec deliverable: spawn N parallel sub-agents, each pre-loaded with same L1-L4 context, splitting work across non-overlapping slices. Aggregate findings before commit. |

## "Project becomes alive" — what it looks like to the operator

1. Operator opens N=3 EVE.exe sessions on the same project (e.g. `sanctum/eve-exe`).
2. Each session's first response shows `Sinister Sync: 47 graph nodes loaded | 12 semantic recalls | last 5 broadcasts shown`.
3. Agent A picks deliverable #1; agent B picks #2; agent C picks #3 (auto-coordinated via `DETECT-SIMILAR-AGENTS` + L3 broadcast claims).
4. When A finishes, B+C see the result in their next message via L3 broadcast tail; their plans auto-update with the new information.
5. Output: 3x velocity on EVE.exe completion without duplicate work or merge conflicts.

## Implementation slices (per-layer ship plan)

- **S1 — L1 wire-up (lane: sanctum):** `automations/sinister-sync-build.ps1` invokes `understand-anything:understand` per-project, writes graph to `_shared-memory/sinister-sync/<key>/graph.json`, summary to `summary.md`. Trigger: pre-push hook + `EVE.exe` menu key.
- **S2 — L2 namespace seeding (lane: sanctum-helper):** Per-project Ruflo namespace `project:<key>`; backfill from existing `_shared-memory/PROGRESS/<lane>.md` + `_shared-memory/plans/<key>-*/plan.md` via a one-shot seed script.
- **S3 — L3 broadcast wire (lane: sanctum):** Add `sinister-sync-broadcast` topic to existing fleet-updates channel; agents subscribe by project-key match.
- **S4 — L4 cold-start injection (lane: sanctum):** `start-sinister-session.ps1` adds 1 new phrase block: `SINISTER-SYNC PROJECT-BRAIN:` between `RESUME CONTEXT` and `RECENT BRAIN UPDATES`. Reads `_shared-memory/sinister-sync/<key>/summary.md` + Ruflo recall + broadcast tail.
- **S5 — L5 swarm orchestrator (lane: sanctum-master):** Operator-callable: `EVE.exe → menu key → Sinister Sync Swarm → pick project → pick N → pick deliverable splitter strategy`. Spawns N sessions backed by same L1-L4 context, auto-claims non-overlapping slices.

## EVE.exe priority case (operator's first concrete ask)

Operator wants EVE.exe finished fast. Sinister Sync applied to `sanctum/eve-exe` lane = 3+ parallel agents picking from the EVE.exe backlog with shared context. Concrete next-step for sanctum-master: ship S4 first (cold-start injection is the smallest reversible change that unlocks 80% of value), then S5 (swarm orchestrator) targeting the EVE.exe deliverable list at `_shared-memory/plans/sanctum-eve-exe-*/plan.md` (whichever is current).

## Composes with

- `quantum-fleet-100x-master-plan-2026-05-25T0128Z` — Sinister Sync IS quantum swimlane "shared-context multiplier"; this doctrine names + binds the architecture.
- `mesh-coordination-and-resource-lifecycle-2026-05-24` — mesh-locks remain the per-file lock primitive; Sinister Sync is the per-PROJECT context primitive. They compose: mesh = atomic guard, Sync = informed prioritization.
- `loop-relentless-pursuit-doctrine-2026-05-25` — rule 8 SHIP-THIS-TURN benefits massively from shared context (agents don't re-read same file 4 times).
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` — Sinister Sync is the next evolution of memory-push: instead of broadcasting to ALL agents, scope to project-key match.
- `forever-improve-review-doctrine-2026-05-24` — improvement-log auto-tagged with project-key feeds L2.
- `fleet-freeze-and-zombie-windows-diagnosis-2026-05-25` — Sinister Sync swarm spawns MUST honor freeze-diagnostic thresholds (max claude.exe = 5; max conhost = 30). Sync-spawned agents count.

## Anti-patterns (do NOT do)

1. **Don't auto-spawn N=10 agents on one project** without freeze-diagnostic threshold gate. 3-5 is the sane cap; gated by current `Get-Process claude` count.
2. **Don't write to project namespace without project-key validation.** Every L2/L3 write requires `project_key` field matching a `projects.json` row.
3. **Don't lose lane discipline.** Sinister Sync = SHARED CONTEXT, NOT shared LANE. Sanctum-master is still the only lane that ships sanctum-scope changes.
4. **Don't replace `understand-anything` step 0.** Sinister Sync EXTENDS it — L1 graph IS the understand-anything output. The cold-start step stays.

## Pass criterion

A new agent spawned on project X via EVE.exe shows in its first response: `Sinister Sync: <graph-node-count> nodes | <recall-count> recalls | <broadcast-count> recent broadcasts` AND the agent picks a deliverable that doesn't duplicate any in-flight sibling agent's work (cross-checked via L3 + DETECT-SIMILAR-AGENTS).

## L6 — Cross-project federation (operator hard-canonical 2026-05-25T~03:32Z extension)

Operator verbatim (extending Sinister Sync from per-project to fleet-wide): *"make sure we are using all tools that we have and everything is mapped out and all agents and projects act as one forever expoanding entity"*.

L1-L5 give each project a hive mind. L6 federates ALL projects into ONE entity:

| Mechanism | Implementation |
|---|---|
| **Fleet graph union** | `_shared-memory/sinister-sync/_fleet/graph-union.json` = merge of all per-project L1 graphs + edges across projects (cross-project imports, shared tools, shared brain entries). Rebuilt by `sinister-sync-build.ps1 -Mode FleetUnion` after each per-project rebuild. |
| **Fleet semantic namespace** | Ruflo `project:_fleet` namespace = aggregator that recalls across all `project:<key>` rows; useful when an agent in project A needs to know if project B already solved a similar problem. |
| **Cross-project broadcast tier** | Existing `fleet-updates.jsonl` channel IS L6 broadcast. Promote: every per-project broadcast above `priority=normal` auto-mirrors into fleet-updates with `kind=sync_cross_project`. |
| **Tool-reach mapping** | One canonical doc lists every available tool per category (MCP / CLI / brain / inbox / bot) with one-line description + which lane owns it. Already partially shipped at `_shared-memory/knowledge/bot-fleet-quick-reference.md`; extend to cover all 250+ ps1 automations + every Ruflo MCP tool. Cold-start phrase pre-warms a top-K relevant subset per spawn. |
| **Forever-expansion invariant** | Adding a new project / tool / brain entry MUST emit an L6 update event so all active agents pick up the new capability within next loop tick. No tool gets shipped "in a corner" — fleet awareness is required. |

L6 ship plan (sanctum scope): `automations/sinister-sync-fleet-union.ps1` (graph union + fleet namespace seeder) + `cold-start phrase v3` adding `SINISTER-SYNC FLEET-VIEW:` block (top-K cross-project relevant items, K bounded ~10).

## Open for sanctum-master

- S1 → S5 implementation order is suggested; sanctum may reorder based on EVE.exe ship pressure.
- Operator wants EVE.exe finished FAST — fastest path = S4 (cold-start pre-warm) + S5 (swarm) shipped this loop.
- L6 federation = follow-up iteration after S1-S5 land; operator's "forever expanding entity" framing means L6 is the long-term invariant, not the iter-1 deliverable.
- Inbox rows: `_shared-memory/inbox/sanctum/2026-05-25T0327Z-from-sinister-os-sinister-sync-design.json` (per-project) and any future L6 follow-up.
