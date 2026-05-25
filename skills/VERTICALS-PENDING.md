# Sinister Sanctum — All Fleet Verticals (Compiled Reference)

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Maintained by:** `automations/agent-verticals-audit.py --agent all-agents`
> **Operator hard-canonical 2026-05-25:** Every new agent audits this file first before project setup.
> **Refresh:** run `python automations/agent-verticals-audit.py --agent <slug>` to get a per-agent view.

This file compiles EVERY available vertical in the Sinister Sanctum fleet — shipped bots, skills,
tools, candidate Ruflo skills (pending operator thumb), and scouted externals. When a new agent
is spawned, it reads this file FIRST to understand what the fleet can provide and plan how to
use these verticals in its project.

---

## Shipped Bots (free, always available via Ruflo MCP)

| Slug | Tier/Cost | What it does |
|------|-----------|--------------|
| sentinel | Tier 1 / $0 | Date alarms (Yurikey expiry, deadlines) |
| translator | Tier 1 / $0 | MCP-tool catalog search across 268+ tool names |
| librarian | Tier 2 / $0 (Ollama) | RAG over 8,500+ md archive — semantic recall |
| watcher | Tier 1 / $0 | Source-drift detection via SHA256 manifest compare |
| auditor | Tier 1 / $0 | Secrets scan + dedup + freshness check |
| sinister-bus | Tier 1 / $0 | Orchestrator + runlog + codec + vault + memory garden + inbox messaging |
| triage | Tier 2 / $0 (Ollama) | File classifier (16 categories) |
| scribe | Tier 3 / ~$0.02 | Daily-digest writer (Claude Haiku) |
| curator | Tier 3 / ~$0.05 | Code-library scout (helper-function extractor) |
| custodian | Tier 1 / $0 | Active backup to D:\\_backups\\ (SHA256 dedup) |
| stealth-browser | Tier 1 / $0 | Undetected Chromium via nodriver + CDP |
| researcher | Tier 2 / $0 | Scrape → Ollama summarize chain |
| vault | Tier 1 / $0 | Unified facade: daemon, Gitea, Syncthing, filesystem |

**When to use:** Route classification → triage. Semantic search → librarian. Secrets check → auditor. Backups → custodian. Cross-agent inbox → sinister-bus. Daily summary → scribe.

---

## Shipped Skills (usable now, import or call directly)

| Slug | Where | What it does |
|------|-------|--------------|
| dashboard-skeleton | `skills/dashboard-skeleton/` | Canonical Sinister UI: tokens, Liquid Glass, 16 doctrine primitives |
| bot_memory | `bots/agents/_shared/bot_memory.py` | Per-bot absorb()/recall() durable memory |
| inbox | `bots/agents/_shared/inbox.py` | File-based inter-agent messaging + heartbeat |
| runlog | `bots/agents/_shared/runlog.py` | sinister-runlog/v1 manifest reader/writer |
| codec | `bots/agents/_shared/codec.py` | Memory codec: encode/decode persisted bot state blobs |
| crypto | `bots/agents/_shared/crypto.py` | Vault Fernet wrapper: AES-128-CBC + HMAC-SHA256 |
| codex-review | `tools/codex-companion/codex.py` | OpenAI peer-review: review(content, ...) → verdict/findings |
| sinister-memory | `projects/sinister-memory/` | FTS5 BM25 recall + iter-close auto-save + spawn-phrase inject |

---

## Shipped Tools (operator-facing, mostly registered)

| Slug | Status | What it does |
|------|--------|--------------|
| sinister-vault | pending schtask | 1TB collaborative storage (daemon :5078, Gitea, Syncthing) |
| session-launcher | registered | Themed cold-start spawner (EVE.exe) |
| sanctum-console | pending schtask | Flagship workbench (RKOJ.exe) |
| capture-invention | registered | CLI for capturing invention cards |
| codex-companion | registered | OpenAI peer-review POST /api/codex/review + CLI |
| sinister-phone-viewer | registered | Per-phone scrcpy + ADB (physical display only) |
| sanctum-git | pending first-run | Local Gitea at :3000 + git-mirror |
| panel-config | registered | Panel loopback-first routing knob |
| sinister-memory | registered (pip -e) | `sinister-memory recall/save/index/inject-spawn-phrase` CLI |

---

## CANDIDATE Skills — Ruflo-Backed (PENDING OPERATOR THUMB)

These 5 skills are forked from Ruflo (MIT). Each has a case-study at `_shared-memory/case-studies/2026-05-19-<slug>.md`.
**Status: candidate → shipped requires operator thumb-up on the case-study verdict file.**

### sk-vector-memory
- **What:** 28 MCP tools — agentdb_* (15), embeddings_* (10), ruvllm_hnsw_* (3). 384-dim ONNX MiniLM + HNSW search + RaBitQ 1-bit quantization (32× memory reduction).
- **Why your agent needs it:** Semantic recall over the brain (not grep). Causal edges linking knowledge entries. 32× memory reduction = entire brain in-RAM.
- **Dependencies:** Ruflo MCP registered + ONNX runtime (bundled).
- **Case-study:** `_shared-memory/case-studies/2026-05-19-sk-vector-memory.md`
- **Activation:** Operator thumb → set status=shipped in `skills/_REGISTRY.yaml`.

### sk-swarm-coord
- **What:** 12 MCP tools (`swarm_*` + `agent_*`). 6 topologies (hierarchical/mesh/adaptive). 5 consensus strategies. Git-worktree isolation per agent.
- **Why your agent needs it:** Multi-agent work splits with conflict-free file ownership. Consensus voting for architecture decisions.
- **Dependencies:** Ruflo MCP.
- **Case-study:** `_shared-memory/case-studies/2026-05-19-sk-swarm-coord.md`

### sk-observability
- **What:** OpenTelemetry-compatible structured logging + distributed tracing + metrics. Span correlation across agents. Latency/error/resource anomaly detection. No SaaS.
- **Why your agent needs it:** Trace every tool call and cross-agent inbox message. Get flame graphs of agent runs. Detect when a bot stops responding.
- **Dependencies:** Ruflo MCP + OpenTelemetry collector (auto-spawned).
- **Case-study:** `_shared-memory/case-studies/2026-05-19-sk-observability.md`

### sk-aidefence
- **What:** AI safety scanning + PII detection (14 types) + prompt-injection defense + adaptive threat learning + runtime hardening (loader-hijack denylist, file mode 0600, AES-256-GCM at-rest).
- **Why your agent needs it:** Every cold-start phrase + inbox message gets scanned before acting. PII redacted from logs before git push. Necessary gate when `--dangerously-skip-permissions` is the launcher default.
- **Dependencies:** Ruflo MCP + Ruflo 3.6.25+.
- **Case-study:** `_shared-memory/case-studies/2026-05-19-sk-aidefence.md`

### sk-federation
- **What:** Cross-installation agent federation. Zero-trust mTLS + ed25519. 5-tier trust model. PII pipeline (14 types). Byzantine BFT consensus. Budget circuit breaker.
- **Why your agent needs it:** When Leo's machine is paired — cross-machine memory sync, collaborative agent deployment.
- **Status:** Recommended PARK until 2-machine workload exists.
- **Case-study:** `_shared-memory/case-studies/2026-05-19-sk-federation.md`

---

## Scouted Externals (operator-click to activate)

| Slug | Install | What it does |
|------|---------|--------------|
| playwright | `automations/install-mcp-servers.ps1` | Browser automation + screenshots (structured) |
| context7 | operator-click | Live library docs — kills hallucinations |
| sequential-thinking | operator-click | Reasoning-chain scaffold for complex prompts |
| memory (KG) | operator-click | Cross-session knowledge graph (graph.json) |

---

## Pending / In-Progress Projects

| Project | Status | Notes |
|---------|--------|-------|
| sinister-crawler | building | Telegram bot for ideas/research/transcription |
| sinister-chatbot | building | Snapchat AI via Eve + Kameleo |
| sanctum-git | pending first-run | Gitea self-host needs Docker + wizard |
| sinister-vault schtask | pending | SinisterVault task not registered |

---

## How to use this file (new agent protocol)

1. **Read this file** in cold-start BEFORE writing any code.
2. **Identify** which bots, skills, tools are directly relevant to your lane.
3. **Create a verticals plan** at `_shared-memory/plans/<your-lane>-verticals-<utc>/plan.md` listing which verticals you'll integrate and in what order.
4. **Check case-studies** for any candidate skill you want to use — coordinate with operator for thumb-up.
5. **Ship integrations iteratively** — wire one vertical per iter, smoke-test, then next.

> Maintained by sinister-memory lane. Re-run `python automations/agent-verticals-audit.py --agent <slug>` to get a tailored view. Auto-updated when new skills land in `skills/_REGISTRY.yaml`.
