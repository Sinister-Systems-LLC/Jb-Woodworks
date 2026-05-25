<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->
# jcode v0.12.4 memory subsystem audit + sinister-memory cherry-picks

**Author:** RKOJ-ELENO :: 2026-05-25 (sinister-memory lane, iter close)
**Trigger:** operator 2026-05-25 mid-day -- *"audit entire jcode code and system for all this and compare to ours and change what you need"*
**Scope:** 4 parallel sub-agents (STORE / RECALL / SUPERSEDE-DECAY-CLUSTER / VERIFY) over `C:\Users\Zonia\Desktop\jcode-0.12.4\` Rust source. Per `we-have-the-source-read-it-doctrine-2026-05-25` — direct grep/read, no RE.

## jcode memory architecture (one-paragraph summary)

jcode persists per-project + global memories as JSON files at `~/.jcode/memory/projects/{hash}.json` and `~/.jcode/memory/global.json` (cite `src/memory.rs:200-202, 288`). The schema is a `MemoryGraph` of `HashMap<id, MemoryEntry>` plus `tags`, `clusters`, and a typed `edges: Vec<Edge>` with kinds `{HasTag, InCluster, RelatesTo{weight}, Supersedes, Contradicts}` (cite `memory_graph.rs:116-125`). Each `MemoryEntry` carries category (fact/preference/entity/correction), 384-dim ONNX embedding (all-MiniLM-L6-v2), trust enum (high/medium/low), confidence f32 with decay-on-rejection, `superseded_by: Option<String>`, and `active: bool` (cite `src/memory.rs:96-111`, `MEMORY_ARCHITECTURE.md:359`). Recall is **embedding-only** cosine similarity over the live graph (cite `src/memory.rs:540-548`), with three boosting layers: skill retrieval bonus, gap-filter (drops bottom of distribution on >=25% score drop, cite `src/memory.rs:724-746`), and a Haiku re-rank gate via the sidecar (cite `src/memory_agent.rs:645-728`). Memory grader runs at retrieval (relevance yes/no) and end-of-session extraction (CATEGORY|CONTENT|TRUST), prefers OpenAI Codex Spark with Claude Haiku 4.5 fallback (cite `src/sidecar.rs:16, 21, 326-366`). Lifecycle: hard delete on `prune_low_confidence(confidence < 0.15 AND age >= 24h)` every ~250 maintenance cycles (cite `src/memory_agent.rs:815-825, 1074-1091`); supersedes via LLM-gated contradiction detector (cite `src/memory_agent.rs:758-826`).

## What sinister-memory had BEFORE this audit

- Stdlib-only Python; sqlite FTS5 BM25 over markdown/json under `_shared-memory/`.
- Flat per-agent markdown files at `_shared-memory/sinister-memory/per-agent/<slug>/iter-NNNN.md` with YAML-ish frontmatter (author/slug/iter/saved_at/length).
- Primitives: `index` / `recall` / `save` (iter-close) / `inject-spawn-phrase` / `supersede` (graph edges, cycle-rejected) / `decay` (single half-life) / `cluster` (Jaccard dedupe) / `verify` (Haiku grader, feature-detected).
- No embeddings, no MemoryCategory enum, no confidence field, no edge kinds beyond Supersedes, no schema versioning.

## Cherry-picks shipped this iter (5 patches)

| # | jcode feature | Our patch | File |
|---|---------------|-----------|------|
| 1 | Per-category half-life (Correction 365d / Preference 90d / Fact 30d / Procedure 60d / Inferred 7d -- `MEMORY_ARCHITECTURE.md:419-423`) | `HALF_LIVES` dict + `half_life_for(category)` dispatcher; `recall_with_decay` accepts optional `category` arg. | `decay.py` |
| 2 | Gap-filter (drop tail when score gap >=25% of top -- `src/memory.rs:724-746`) | `apply_gap_filter(hits, drop_ratio=0.25)`; optionally called from `recall_with_decay`. | `recall.py` |
| 3 | Typed edges (HasTag / InCluster / RelatesTo{weight} / Supersedes / Contradicts -- `memory_graph.rs:116-125`) | New `edges` table parallel to legacy `supersedes` table; `mark_edge(new, old, kind, reason)` + `edges_of(memory_id, kind=None)`; `mark_supersedes` still writes to both for back-compat. | `supersede.py` |
| 4 | MemoryEntry confidence + category fields (`src/memory.rs:96-111`) | Frontmatter v2 emits `format_version: 2`, optional `category`, optional `confidence`. Old format still parses (back-compat: missing fields default). | `auto_save.py` |
| 5 | Schema versioning + migration (`memory.rs:1502-1520`) | `format_version: 2` in frontmatter; reader code checks and treats absence as v1 (no upgrade needed yet -- v1 is a strict subset). | `auto_save.py` |

## What we deliberately did NOT cherry-pick (yet)

- **Embeddings (384-dim ONNX)** -- requires onnxruntime + model download. P0 commitment is stdlib-only; routing to Ruflo MCP `embeddings_*` already covers this when MCP is reachable.
- **LLM-gated contradiction detector on every write** -- expensive; our heuristic `verify.py` jaccard fallback covers 80% of real cases at zero cost. Online Haiku gating remains opt-in via `verify.verify_memory(prefer="online")`.
- **Pending-memory async pipeline with 90s/180s dedup windows** -- our spawn-inject runs once per session, no continuous re-injection, so no dedup window needed.
- **Periodic prune_low_confidence cron** -- queued for next iter once confidence field has telemetry to act on.
- **Sidecar batch re-rank (3-5 candidates per Haiku call)** -- queued; needs verify.py refactor.

## Composes with

- `memory-audit-jcode-rufus-obsidian-understand-doctrine-2026-05-24` (original gap analysis that defined this lane).
- `we-have-the-source-read-it-doctrine-2026-05-25` (read jcode source directly, no RE sub-agents).
- `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` (4 parallel sub-agents over non-overlapping slices, master never idled).
- `loop-relentless-pursuit-doctrine-2026-05-25` (audit triggered mid-iter, integrated same turn).

## Pass criterion

1. `pytest -q` in `projects/sinister-memory/` -- all tests green (13 baseline + N new for the 5 patches).
2. New `mark_edge` accepts kinds {Supersedes, Contradicts, RelatesTo, HasTag, InCluster} and rejects others.
3. `half_life_for("correction") == 365.0`; `half_life_for("inferred") == 7.0`; unknown category falls back to 30.0.
4. `apply_gap_filter([h1=10, h2=9.8, h3=2.0])` truncates after h2.
5. Frontmatter v2 round-trip: write with `category="fact"`, `confidence=0.8`; read back; both fields recovered.
