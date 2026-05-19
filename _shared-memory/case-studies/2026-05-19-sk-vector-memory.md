# Case study :: sk-vector-memory (forked from ruvnet/ruflo)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19T13:30Z
> **Tags:** review, external, ruflo, sk-vector-memory, agentdb, candidate

## 1. What it is

`ruflo-agentdb` is the substrate plugin for Ruflo memory. Three CLI-MCP families: `agentdb_*` (15 tools — hierarchical store/recall, semantic routing, pattern store/search, causal edges, context synthesis, batch ops, consolidation, feedback, sessions), `embeddings_*` (10 tools — 384-dim ONNX MiniLM-L6-v2, HNSW, hyperbolic Poincare, neural substrate, RaBitQ 1-bit quantization 32× memory reduction), and `ruvllm_hnsw_*` (3 tools — WASM-backed pattern router, ≤11 high-priority patterns). 10-check smoke contract. ADR-0001 implementation, v0.3.0 against `@claude-flow/cli` v3.6.x.

Sanctum fork at `skills/sk-vector-memory/`; upstream at `_shared-memory/external-imports/ruflo/plugins/ruflo-agentdb/`.

## 3. Strengths

- **The biggest leverage on Sanctum's existing brain.** Today's brain is markdown + flat grep (29 topics in `_shared-memory/knowledge/_INDEX.md`). Semantic recall over 300+ topics is qualitatively different from grep, especially when phrasing varies.
- **Causal edges** map the brain's implicit structure explicitly. Many existing topics (e.g., `scrcpy-virtual-display-detected` → `kameleo-fingerprint-min-1280`) carry causal links in prose; making them queryable is a brain upgrade.
- **RaBitQ 1-bit quantization** is the practical edge — 32× memory reduction means a 30-topic brain fits in ~1 MB instead of ~32 MB; a 1000-topic brain fits in ~33 MB instead of ~1 GB.
- **Composable** — `ruflo-rag-memory`, `ruflo-intelligence`, `ruflo-browser` all consume this substrate. If Sanctum forks any of those later, the substrate is already in place.
- **MIT license + open spec.**

## 2. Weaknesses + risks

(numbering tracks the template; #3 comes before #2 above by my mistake — left for audit transparency)

- **Heaviest of the 5 forks.** ONNX runtime + WASM + agentdb storage adds ~50-100 MB on disk. Sanctum's existing footprint is small; this expands it materially.
- **Brain replacement risk.** If agentdb data lives at `D:\sinister-vault\repos\sanctum-agentdb\` and the operator deletes that without realizing, semantic recall fails silently. The markdown brain stays canonical (deliberate redundancy) but writes must hit both.
- **Coupling with the entire Ruflo plugin family.** The substrate exists primarily for downstream Ruflo plugins. Sanctum may want a thinner alternative (raw embeddings + sqlite) for just-the-brain. ruflo-agentdb is overkill for 30 topics; pays off only when the brain grows.
- **Index drift.** Markdown is human-edited; agentdb is bot-written. If they drift (a topic marked `fixed` in markdown but still `workaround` in agentdb tags), recall returns stale verdicts.
- **Smoke contract not on Sanctum's scheduler.** Same gap as sk-swarm-coord — without periodic smoke, upstream breakage is invisible.

## 4. Better-than-found proposal (~80 LOC outline)

1. **Markdown-as-source-of-truth adapter (`tools/sanctum-brain-bridge/`) ~40 LOC** — watches `_shared-memory/knowledge/*.md`; on save, parses status / tags / discoveries; calls `agentdb_store` to update the vector index. Markdown stays human-edited; agentdb is always derivable.
2. **Librarian-bot rewiring ~20 LOC** — `bots/agents/librarian/server.py` swap of the `recall()` implementation from grep to `embeddings_search`. Same API; faster + smarter results.
3. **RaBitQ-or-not flag ~10 LOC** — gate the 1-bit quantization behind an opt-in flag. Quantization trades accuracy for memory; for a 30-topic brain, vanilla embeddings are fine and easier to debug.
4. **Weekly smoke + brain-drift report ~10 LOC** — schedule.json entry: run `scripts/smoke.sh` weekly, write `_shared-memory/external-imports/ruflo/agentdb-smoke-<UTC>.md`. Compare markdown topic count vs agentdb store count; surface drift.

Net: ~80 LOC of glue. Keeps markdown sacred; vector index becomes derived state.

## 5. Recommendation

**KEEP-WITH-CHANGES.** Strongest long-term ROI of the 5 forks because the brain is the asset that compounds across all Sinister projects. The "work forever" pitch literally relies on the brain getting smarter month over month; vector recall is the unlock.

Sequence on operator thumbs-up:
1. Land the markdown-as-truth adapter (highest leverage, lowest risk).
2. Smoke-test against current 30-topic brain (verify recall on operator-known queries).
3. Once smoke green, swap librarian bot's `recall()` implementation.
4. Optional: enable RaBitQ once brain crosses 200 topics.

Pair with Codex peer-review (auth boundary: writes to D:\sinister-vault\ — touches storage; deep tier per standing rule).

---

## Operator decision

(blank — operator drops 👍 / 👎 / free text)
