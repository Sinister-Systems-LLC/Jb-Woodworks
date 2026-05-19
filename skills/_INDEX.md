# Sinister Skills — Index

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Running catalog of every registered skill in the Sanctum. Append-only. See `README.md` for the junction-or-pointer pattern.

Two tables — **folder-shaped skills** live in `skills/<slug>/` with their own README + sources; **code-library skills** are modules called from inside tools/automations.

`Status` lifecycle: `candidate` → `fixed` → `superseded` → `archived`. Catalog reorg 2026-05-19 by master.

---

## Folder-shaped skills (`skills/<slug>/`)

| Slug | Path | What it provides | Status | Source | Imported |
|---|---|---|---|---|---|
| dashboard-skeleton | `D:\Sinister Sanctum\skills\dashboard-skeleton\` | Canonical Sinister UI source — design tokens, primitives, shared components. Intended junction to `C:\Users\Zonia\Desktop\dashboard-skeleton\`. See its `README-SANCTUM-USE.md`. | fixed | native | (founder) |
| sk-swarm-coord | `D:\Sinister Sanctum\skills\sk-swarm-coord\` | Multi-agent swarm coordination: 12 MCP tools (`swarm_*` + `agent_*`), 6 topologies (hierarchical/mesh/adaptive/etc.), 5 consensus strategies, git-worktree isolation per agent. Direct augment to Sanctum's cross-agent-coordination patterns. See `_shared-memory/case-studies/2026-05-19-sk-swarm-coord.md`. | candidate | ruflo:ruflo-swarm | 2026-05-19 |
| sk-vector-memory | `D:\Sinister Sanctum\skills\sk-vector-memory\` | Vector + semantic memory substrate: 28 MCP tools spanning `agentdb_*` (15), `embeddings_*` (10), `ruvllm_hnsw_*` (3). 384-dim ONNX MiniLM, HNSW search, RaBitQ 1-bit quantization (32× memory reduction). Upgrades the Sanctum brain from grep to semantic recall + causal edges. See `_shared-memory/case-studies/2026-05-19-sk-vector-memory.md`. | candidate | ruflo:ruflo-agentdb | 2026-05-19 |
| sk-federation | `D:\Sinister Sanctum\skills\sk-federation\` | Cross-installation agent federation: zero-trust mTLS + ed25519, 5-tier trust model, PII pipeline (14 types), Byzantine BFT consensus, budget circuit breaker (maxHops/maxTokens/maxUsd). Operator+Leo multi-machine collaboration comms layer. See `_shared-memory/case-studies/2026-05-19-sk-federation.md`. | candidate | ruflo:ruflo-federation | 2026-05-19 |
| sk-observability | `D:\Sinister Sanctum\skills\sk-observability\` | OpenTelemetry-compatible structured logging + distributed tracing + metrics for the fleet. Span correlation across agents; latency / error / resource anomaly detection. Closes the fleet-monitor visibility gap without SaaS bills. See `_shared-memory/case-studies/2026-05-19-sk-observability.md`. | candidate | ruflo:ruflo-observability | 2026-05-19 |
| sk-aidefence | `D:\Sinister Sanctum\skills\sk-aidefence\` | AI safety + PII detection + prompt-injection defense + runtime hardening (loader-hijack denylist for `LD_PRELOAD`/`NODE_OPTIONS`/`DYLD_*`, file mode 0600 enforcement, AES-256-GCM at-rest opt-in). Necessary input gate when `--dangerously-skip-permissions` is the launcher default. See `_shared-memory/case-studies/2026-05-19-sk-aidefence.md`. | candidate | ruflo:ruflo-aidefence | 2026-05-19 |

*(Each `candidate` flips to `fixed` only after operator thumbs-up on the case-study verdict file. Archive verdicts move folder to `_archive/skills/sk-<slug>/`.)*

---

## Code-library skills (modules consumed by tools/automations)

| Slug | Path | What it provides | Status | Source |
|---|---|---|---|---|
| bot_memory | `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\bot_memory.py` | Per-bot facts + embeddings store with `absorb()` / `recall()` API for durable agent memory across sessions. | fixed | native |
| inbox | `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\inbox.py` | File-based inter-agent messaging + heartbeat protocol. Each bot polls its inbox dir; presence signaled by heartbeat files. | fixed | native |
| runlog | `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\runlog.py` | Readers/writers for the `sinister-runlog/v1` manifest format — the canonical record of a session's tool calls, prompts, and outputs. | fixed | native |
| codec | `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\codec.py` | Memory codec — encode/decode the persisted memory blob format used by `bot_memory`. | fixed | native |
| crypto | `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\_shared\crypto.py` | Vault Fernet wrapper. Symmetric encrypt/decrypt for secrets stored under `_vault/`. | fixed | native |
| eveObservations | `D:\Sinister Sanctum\tools\sinister-chatbot\src\services\eveObservations.ts` | Server-side Eve derivation — `deriveEveObservations(fan)` returns top-3 observations (tone-priority `accent > success > warning > info`). Pure function ported from `dashboard-skeleton/components/eve/eve-observations-card.tsx`; flavors LLM system prompts so AI tone tracks operator's UI signal. | fixed | native |
| kameleo | `D:\Sinister Sanctum\tools\sinister-chatbot\src\services\kameleo.ts` | Antidetect browser client — axios wrapper over the Kameleo CLI (port 5050). Picks Windows + Chrome desktop fingerprints; creates / starts / stops profiles with HTTP-proxy attach; auto-tiles browser windows; exposes `findProfileByName` / `purgeAllSnapProfiles`. Requires operator to have logged in via Kameleo GUI once. | fixed | native |
| codex-review | `D:\Sinister Sanctum\tools\codex-companion\codex.py` | OpenAI-powered peer-review skill. `review(content, *, context, language, depth)` calls a Codex-grade model (gpt-4o-mini / gpt-4o / o1-mini per depth tier) and returns `{verdict: pass\|warn\|fail, findings:[...], summary}`. Every review logged append-only to `_shared-memory/codex-reviews/`. Graceful no-API-key behavior. Exposed via Sanctum Console at `POST /api/codex/review`. | fixed | native |
| viewer | `D:\