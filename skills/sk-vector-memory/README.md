# sk-vector-memory — vector + semantic memory substrate (Ruflo agentdb fork)

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19 :: forked from ruvnet/ruflo (MIT) ruflo-agentdb plugin
> **Status:** candidate (pending operator thumb per case-study `_shared-memory/case-studies/2026-05-19-sk-vector-memory.md`)
> **Upstream snapshot:** `_shared-memory/external-imports/ruflo/plugins/ruflo-agentdb/`

## What it is

The substrate for semantic memory across the Ruflo plugin ecosystem. Wraps 3 CLI-MCP families:

- **`agentdb_*`** (15 tools) — hierarchical store/recall, semantic routing, pattern store/search, causal edges, context synthesis, batch ops, consolidation, feedback, sessions
- **`embeddings_*`** (10 tools) — 384-dim ONNX (all-MiniLM-L6-v2), HNSW search, hyperbolic (Poincare), neural substrate, RaBitQ 1-bit quantization (32× memory reduction)
- **`ruvllm_hnsw_*`** (3 tools) — WASM-backed pattern router for ≤11 high-priority patterns

Ships with a 10-check smoke contract (`scripts/smoke.sh`) for verification.

## Why Sanctum needs it

The Sanctum brain (`_shared-memory/knowledge/`) is markdown-based + flat-text grep today. That works fine for ~30 topics; at 300+ topics it'll be slow and miss semantic recall. ruflo-agentdb gives Sanctum:

- **Semantic recall** over the brain (instead of grep) — agent asks "what do we know about anti-detect?" and gets the scrcpy / kameleo / virtual-display entries even when "anti-detect" isn't a literal tag.
- **Causal edges** — link knowledge entries by causal relationship (`scrcpy-virtual-display-detected` *causes* `kameleo-fingerprint-min-1280`), enabling chain-of-fixes traversal.
- **Cross-bot pattern store** — the existing per-bot `learned.md` files (operator-private; bot_memory.py reads them) can be backed by HNSW search for instant similarity lookup across all 13 bots.
- **RaBitQ quantization** — 32× memory reduction means the entire brain can stay in-RAM for hot lookups; today even loading all .md files takes 100+ ms.

## How Sanctum uses it (post operator-thumb)

1. `librarian` bot's `recall()` API switches from grep-over-md to `embeddings_search` for the primary path; markdown stays as the canonical store + audit trail.
2. New brain-entry writes append both a markdown row (per existing `DIRECTIVES.md` standing rule) AND an `agentdb_store` call so semantic lookup is updated immediately.
3. Codex peer-review results indexed via causal edges so "what fixed last time we hit a similar Codex finding" becomes a one-call lookup.
4. RKOJ's command palette gains semantic search — `Cmd+K "vault stuck"` returns the right brain entry even if you don't remember the slug.

## Dependencies

- Ruflo MCP registered + `ruflo-core` (auto-pulled).
- ONNX runtime (bundled with ruflo).
- Local storage: agentdb data goes under `D:\sinister-vault\repos\sanctum-agentdb\` (Vault tier 1) so it's collaborative + audit-logged.

## License + attribution

- Upstream: MIT (RuvNet).
- Sanctum fork: stays MIT.
- Original code at `_shared-memory/external-imports/ruflo/plugins/ruflo-agentdb/`.
- Sanctum-specific bindings (vault-storage adapter, librarian-bot rewiring) live in this folder only.

## See also

- `_shared-memory/case-studies/2026-05-19-sk-vector-memory.md` — verdict file
- `bots/agents/_shared/bot_memory.py` — existing per-bot memory module (complementary; will use agentdb as backend after fork lands)
- `bots/agents/librarian/server.py` — the RAG bot whose recall API gets the agentdb upgrade
- `_shared-memory/knowledge/README.md` — the brain that gets semantic search
