<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 90
-->
# Memory Backbone: 3-Tier Hybrid (Better-than-jcode design)

**Created:** 2026-05-24 20:38Z
**Authority:** Operator hard-canonical 2026-05-24T20:36Z (verbatim):
> *"make sure all our memory is concise efficent and better than jcodes ... link all of this into the sinister os im making as we will be siwthcin"*

This doctrine consolidates findings from 4 parallel deep-dive agents (JCODE / Ruflo / understand-anything / Obsidian) and proposes the canonical memory backbone for both current Windows-Sanctum and the Sinister OS the operator is building.

---

## The four findings (in one paragraph each)

**JCODE (`C:\Users\Zonia\Desktop\jcode-0.12.4`)** — Per-session in-memory `MemoryGraph` JSON. Entries are typed (Fact/Preference/Correction/Entity) with embeddings (384-dim ONNX MiniLM), graph edges (HasTag/RelatesTo/Supersedes/Contradicts), and exponential decay scoring with category half-lives (Correction 365d / Preference 90d / Fact 30d). BFS recall, signature+set-overlap dedup (180s window), pending-memory 120s TTL. **Pro:** rich + auditable. **Con:** per-session isolated, in-process, dies with the session, not cross-machine.

**Ruflo MCP** — 49 memory tools across 5 families (memory_/agentdb_/embeddings_/ruvllm_hnsw_/neural_). SQLite + WAL backing store; HNSW + RaBitQ 1-bit quantization (32x compression) implemented. **Pro:** production-grade infra. **Con:** mostly dormant — `.swarm/memory.db` has 1 entry, 0 patterns, RaBitQ not activated, hooks not wired. 4-8 weeks of work to canonicalize.

**understand-anything plugin** — Knowledge graph from AST + LLM extraction stored as JSON in `.understand-anything/`. Lexical (Fuse.js fuzzy) + semantic (cosine vector) dual search. Rebuilds fully per analysis (file-fingerprint-driven). **Pro:** great for codebase comprehension, live web dashboard. **Con:** code-only; not designed for our brain-style prose entries.

**Obsidian pattern** — Markdown vault + `[[wikilinks]]` + tags. Plain-text, git-friendly, no DB, human-curated. Backlinks emerge from wikilink scanning. **Pro:** durable, portable, schema-free, version-controllable. **Con:** no native semantic search (community plugins add it).

---

## The synthesis: our `_shared-memory/knowledge/` IS already an Obsidian-style vault

173 .md files. Frontmatter-style headers (`Author`, `Created`, `Tags`). Cross-references via prose `Composes with` sections. Manually-curated topic index in `_INDEX.md`. **Operator has been building an Obsidian vault for months without naming it that.**

JCODE's MemoryGraph is rich but session-bound — our brain markdown is operator-curated, persistent, cross-session, cross-machine (vault + git), inspectable (you can `grep` it), version-controllable, and survives total fleet wipe. **Markdown wins on durability.**

---

## The three-tier backbone (canonical recommendation)

### Tier 1 — Brain markdown vault (CANONICAL, no migration)
- Path: `_shared-memory/knowledge/<slug>-<date>.md`
- Format: existing convention (Author / Created / Authority / body / Composes with)
- Index: `_INDEX.md` (single table)
- Recall: `grep` (always-available) + `librarian.search()` (when MCP loaded)
- Updates pushed via `automations/fleet-update.ps1` per gradual-growth doctrine
- **Portable to Sinister OS:** Yes — plain markdown + git, runs anywhere

### Tier 2 — JCODE-style decay frontmatter (NEW, ~30 min effort)
- Add optional frontmatter to brain entries:
  ```yaml
  category: correction | preference | fact | entity
  confidence: 0.0 - 1.0
  reinforcements: <int>   # bumped each time the doctrine is re-validated
  half_life_days: 365 | 90 | 30 | 30  # default by category
  superseded_by: <slug>   # optional; marks this entry inactive
  ```
- New script `automations/brain-decay-score.ps1`: scans `_shared-memory/knowledge/`, computes `effective_confidence = confidence × e^(-age/half_life × ln(2)) × √reinforcements`, surfaces TOP-DECAYED rows for operator review
- Brain `_INDEX.md` gets a new column `EffConf` showing per-entry decayed-confidence
- **Win over jcode:** decay is OPERATOR-AUDITABLE (you can read it in plain text), CROSS-SESSION (decay state persists), CROSS-MACHINE (committed to git)
- **Portable to Sinister OS:** Yes — pure metadata + grep + arithmetic

### Tier 3 — Optional accelerators (gated, no migration)
- **`understand-anything:understand-knowledge`** on `_shared-memory/knowledge/` → live web dashboard for visual brain exploration (free; uses existing plugin)
- **Ruflo agentdb** as fleet-distributed read-through cache for cross-session semantic recall — enable hooks + RaBitQ as a 3-day low-risk sprint when operator decides it's needed (NOT required for normal operation)
- **`librarian.search()`** with brain as the corpus (already supported when MCP loaded)
- Each accelerator is OPTIONAL — Tier 1 + Tier 2 stand alone

---

## Why this is better than jcode's design

| Dimension | jcode | This 3-tier hybrid |
|---|---|---|
| Persistence across sessions | dies with session | persists in git forever |
| Persistence across machines | per-machine | git-sync to all operator machines + Leo |
| Human-auditable | requires reading JSON graph | grep + open in any text editor |
| Schema migration risk | high (MemoryGraph struct changes) | zero (markdown is its own schema) |
| Sinister OS portability | requires re-implementing in Rust + ONNX | works as-is (markdown + sh) |
| Operator-curatable | indirect (via tool calls) | direct (edit the .md) |
| Decay scoring | hardcoded in struct | frontmatter convention; tunable per-entry |
| Cold-start cost | rebuild graph + load embeddings | grep + read top _INDEX rows |
| Fleet visibility | session-scoped | brain entries visible to every spawn via cold-start step 6 |
| External-tool integration | bespoke MemoryGraph reader | any tool that reads markdown |
| DB-corruption blast radius | medium (.json file lock) | zero (one .md = one row; git history is recoverable) |
| Cost | always-on embedding inference | $0 (grep) → ~$0 (Ruflo cache when enabled) |

**jcode optimizes for in-session intelligence. This design optimizes for fleet durability + operator agency.** The 3-tier hybrid wins on every persistence/portability dimension and matches jcode on decay-aware ranking via the Tier 2 frontmatter.

---

## Sinister OS linkage (operator 20:36Z "switching to Sinister OS")

This backbone migrates to Sinister OS unchanged:
- **Brain vault** → mounted at `/var/sinister/knowledge/` (or operator-chosen path) inside Sinister OS; git-tracked the same way
- **Decay script** → straightforward port to .sh / Python; no Windows-specific calls
- **Fleet-update channel** → port `fleet-update.ps1` to .sh; the JSONL file format is OS-agnostic
- **Mesh-coordinator + bot-lifecycle** → same .ps1 → .sh port; file-lock primitives are POSIX-flock-friendly
- **EVE.exe** → re-ship as Linux binary (PyInstaller cross-compile or rewrite picker in Go for native Sinister OS feel)
- **fleet-autostart** → systemd unit instead of Windows Startup folder + scheduled task

Migration is a port, not a rewrite. Markdown stays markdown. JSONL stays JSONL. The OS-specific pieces are the launchers + cron substitutes — small surface.

---

## Implementation plan (this lane, next 3 iters)

| Iter | Ship | Effort |
|---|---|---|
| Now (this turn) | This doctrine + `_INDEX.md` row + operator-queue row update + fleet-update push | small |
| Iter N+1 | `automations/brain-decay-score.ps1` (Tier 2) + retrofit category frontmatter on 5 example brain rows + new `EffConf` column in `_INDEX.md` | medium |
| Iter N+2 | Invoke `understand-anything:understand-knowledge` on `_shared-memory/knowledge/` → publish dashboard URL in OPERATOR-ACTION-QUEUE; document `librarian.search` usage in `bot-fleet-quick-reference.md` (Tier 3) | small |
| Iter N+3 (gated on operator) | Ruflo hooks + RaBitQ activation 3-day sprint OR skip if operator says brain markdown + decay is enough | medium |

Aligns with operator R3 (gradual + never stop + prune-as-add). No big-bang migration.

---

## Anti-patterns

1. Migrating brain markdown TO Ruflo as a one-shot — loses git history, breaks every cross-link, blast-radius = whole fleet
2. Adding category frontmatter to all 173 rows at once — should be opportunistic (when an entry is touched, add the frontmatter; backfill never)
3. Treating Ruflo's "49 tools" as a checklist to enable — most are research-grade; only enable when a concrete workflow demands them
4. Letting JCODE's in-process design pressure us to add a Rust dependency for "feature parity" — we already win on durability
5. Building a separate index DB when `_INDEX.md` already does the job — that's the same redundancy the prune-as-add doctrine forbids

---

## Composes with

- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R3: gradual + never-stop + prune-as-add)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (operator-utterance-tracking + fleet-update channel are the push surfaces this doctrine relies on)
- `sanctum-scope-discipline-2026-05-24` (this is a fleet-shape decision — Sanctum-level)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (decay scoring is auditable + smoke-testable in Tier 2)
- `forever-improve-review-doctrine-2026-05-24` (decay scores drive forever-improve "what entry needs review" surface)
- Master plan: `_shared-memory/plans/sanctum-master-plan-2026-05-24T2020Z/plan.md` section 5 (this doctrine fulfills D7 of the master plan)

## Verification

```powershell
# Brain vault count + size (baseline for "should not bloat")
Get-ChildItem _shared-memory/knowledge/ -Filter '*.md' -File | Measure-Object -Property Length -Sum
# Should be ~175 files, ~2 MB total. Bloat signal: >300 files OR >10 MB.

# Tier 2 dry-run (after brain-decay-score.ps1 lands next iter)
powershell -File automations/brain-decay-score.ps1 -DryRun -TopDecayed 10
```
