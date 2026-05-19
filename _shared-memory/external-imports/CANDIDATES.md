> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# External-import candidates — master list

Every external skill / tool / MCP server / dataset / cookbook the Sanctum fleet has scouted or imported. Append-only; most-recent at top.

Tag legend: `scouted` · `mcp-only` · `forked-candidate` · `keep` · `archive` · `superseded`

---

## 2026-05-19 — first sweep (Sinister Sanctum master agent)

### Ruflo (`github.com/ruvnet/ruflo`) — multi-agent orchestration for Claude Code

| Field | Value |
|---|---|
| State | **scouted** (skill catalog ALREADY LIVE in Claude Code sessions via claude-flow; MCP wire pending Phase B operator click) |
| URL | https://github.com/ruvnet/ruflo |
| License | MIT |
| Pinned commit | `c292e5fcf563b1639ea2ce7842c8f4a110c3ad39` (2026-05-19T02:18:38Z — `feat: ADR-123 — RuFlo Graph Intelligence Engine`) |
| Pinned version | v3.7.0-alpha.33 (2026-05-13) |
| Install (Phase B) | `claude mcp add ruflo -- npx ruflo@latest mcp start` (operator-clicked; lane discipline forbids master editing `~/.claude/.mcp.json`) |
| What it is | Multi-agent AI orchestration platform for Claude Code with 100+ specialized agents, 32 native plugins, swarm coordination (hierarchical/mesh/adaptive topology), vector memory (AgentDB + HNSW), self-learning neural patterns (SONA), automated code/security/doc workflows, zero-trust agent federation (mTLS + ed25519 challenge-response, behavioral trust scoring). |
| Why we care | Direct match for Sanctum's existing 13-bot fleet + cross-agent coordination patterns. Offers swarm/topology features that augment the current `sinister-bus` inbox model. AIDefence + PII-gated data flow augments our `auditor` bot. |
| **Skill catalog LIVE** | 38+ claude-flow Claude Code skills are already loaded in this session (visible via system-reminder): `agentdb-*`, `agentic-jujutsu`, `browser`, `flow-nexus-*`, `github-*`, `hive-mind-advanced`, `hooks-automation`, `pair-programming`, `performance-analysis`, `reasoningbank-*`, `skill-builder`, `sparc-methodology`, `stream-chain`, `swarm-*`, `v3-*`, `verification-quality`, `worker-*`. Invokable via the `Skill` tool right now. |
| What we'll take (Phase C forks) | Candidate forks: swarm coordination, self-learning memory (SONA), vector memory (AgentDB), GitHub automation, code quality, doc generation, security automation. Target: `skills/sk-<slug>/`. See `_shared-memory/external-imports/ruflo/ATTRIBUTION.md` for the full list + licensing pattern. |
| Phase | Phase 0 done (URL + SHA + version pinned). Phase A done (ATTRIBUTION.md written). Phase B pending operator click. Phase C pending Phase B + per-skill case-study gate. |
| Case-study | (per forked skill in Phase C; verdict files at `_shared-memory/case-studies/<UTC>-sk-<slug>.md`) |
| Brain entry | `_shared-memory/knowledge/ruflo-mcp-integration.md` |

### Anthropic Cookbook (`github.com/anthropics/claude-cookbooks`) — first-party Claude patterns

| Field | Value |
|---|---|
| State | **scouted** (target: pattern extraction into brain, not code copy) |
| URL | https://github.com/anthropics/claude-cookbooks |
| License | (per repo) — extraction is pattern-level (30-100 lines per brain entry); we cite, we don't copy. |
| What it is | Official Anthropic recipe collection. Top-level folders: capabilities (classification/RAG/summarization), claude_agent_sdk, coding, extended_thinking, finetuning, images, managed_agents, multimodal, observability, patterns/agents, skills, tool_use, tool_evaluation, third_party (RAG with Pinecone/Wikipedia/embeddings), misc (prompt caching, PDF, JSON mode, moderation, evals). |
| Why we care | Authoritative source for the agent patterns Sanctum's bots already use informally (prompt caching, extended thinking, RAG, tool use). Codifying these into the brain ensures every cold-start agent has them. |
| What we'll take | Pattern entries (NOT code copies) for: `prompt-caching`, `extended-thinking`, `tool-use-design`, `rag-third-party-pinecone`, `agent-patterns-multi-agent`, `observability-tracing`. 6 brain entries planned. |
| Phase | Phase E (after operator OK) |
| Case-study | Patterns don't need per-pattern case-study — they're reference, not running code. One umbrella verdict file in `_shared-memory/case-studies/` if operator wants. |

### MCP Registry (`registry.modelcontextprotocol.io`) — official server registry

| Field | Value |
|---|---|
| State | **scouted** (target: build `tools/mcp-discover/` as recurring discovery source) |
| URL | https://registry.modelcontextprotocol.io/ (production) · https://staging.registry.modelcontextprotocol.io/ (staging) · API docs at `/docs` |
| License | (per registry T&Cs; we read, we don't redistribute) |
| What it is | Centralized directory of public MCP servers. UI shows pagination + search + version toggle, implying REST endpoints for list/search/version. Full API spec at `/docs`. |
| Why we care | Renewable source of new MCP bots. Today Sanctum has 19 servers registered; the registry has thousands. Without a discovery loop the fleet plateaus. |
| What we'll take | Build `tools/mcp-discover/discover.py` that polls the registry, diffs vs `~/.claude/.mcp.json`, writes `_shared-memory/external-imports/mcp-candidates.md`. Operator picks which to add. Pure-read; never edits `.mcp.json`. |
| Phase | Phase D (after Phases A-B settle) |
| Case-study | Per-discovered-MCP, run case-study before recommending to operator. Discover script tags every new entry `state=scouted`. |

### Polymathic AI / The Well (`polymathic-ai.org/the_well`)

| Field | Value |
|---|---|
| State | **scouted** → **archive** (strategic fit LOW for Sanctum's current workloads) |
| URL | https://polymathic-ai.org/the_well/ · `github.com/PolymathicAI/the_well` · `pip install the_well` |
| License | (per repo — open) |
| What it is | 15 TB scientific spatiotemporal physics simulation dataset (Euler/RB/MHD/supernova/etc.). |
| Why we care (or don't) | Sanctum is a Claude-orchestration + dev-fleet hub. Not a scientific-ML training rig. The Well buys us nothing unless we pick up explicit physics-domain workloads. |
| Verdict | **Defer** unless operator names a use case. Captured here so it isn't re-scouted later. |
| Phase | Out of scope. |

### `obra/superpowers` + `anthropics/skills` — runners-up Claude Skill repos (if Ruflo fallback needed)

| Field | Value |
|---|---|
| State | **scouted-as-backup** |
| URL | (not fetched in Phase 0; only if Ruflo URL didn't resolve — it did, so deferred) |
| Why we care | Per the Phase-0 skip rule. If Ruflo upstream changes or its skills don't fit, these are the second-best public Claude-skill catalogs. |
| Phase | On-demand only. |

### LangSmith / Phoenix / Helicone — observability sidecars

| Field | Value |
|---|---|
| State | **scouted-secondary** (`EVALUATE` per scout) |
| URLs | https://www.langchain.com/langsmith · https://phoenix.arize.com/ · https://www.helicone.ai/ |
| Why we care | Fleet observability across 13 bots — tracing, cost, latency, agent-flow visualization. |
| Why we're holding | Sanctum doesn't yet have a tracing pain point; introducing observability without a problem to solve is premature. Revisit once we have 5+ multi-agent coordination flows in production. |
| Phase | Deferred (post Phase H self-heal). |

### Aider / OpenHands — coding-agent sidecars

| Field | Value |
|---|---|
| State | **scouted-secondary** (`EVALUATE` per scout) |
| URLs | https://aider.chat/ · OpenHands (github) |
| Why we care | Aider's tree-sitter codebase mapping + architect/editor pattern could be delegated-to for code-heavy tasks. |
| Why we're holding | RKOJ + Claude Code already cover the coding loop; adding another agent introduces coordination overhead. |
| Phase | Deferred. |

---

## 2026-05-19 — Image 1 directive queue (operator Telegram 2026-05-19 06:25-06:30 — creative tools)

Operator's first Telegram directive batch queued four candidates ahead of Ruflo: **Blender intervention**, **Adobe**, **Auto desk fusion**, **Ruflo Claude skill**. Ruflo is captured above. The three creative-tool entries land here as `scouted` placeholders; **operator confirms use case before any Phase 0 verification or scout fetch**. Per the operator's "scout-only this pass" decision (2026-05-19), no MCP wiring, no skill forks, no scope creep this round.

### Blender — open-source 3D creation suite

| Field | Value |
|---|---|
| State | **scouted** (pending operator use-case confirmation) |
| URL | https://www.blender.org/ |
| License | GPL v2/v3 (the Blender suite); MCP integrations (e.g. `blender-mcp` on GitHub) have their own licenses |
| What it is | 3D modeling, sculpting, animation, simulation, rendering, compositing. Python API for scripting. |
| Why we care | Potential use cases: 3D asset generation for Snap/TikTok filters, procedural pipelines, photogrammetry. Community MCP integrations exist. |
| Open question | What does the operator actually want to do with Blender? (3D filter pipeline? Asset gen for ads? Hardware visualization for Hardware-Roadmap.md?) |
| Phase | Phase 0 (verify) PENDING operator use-case confirmation. |
| Case-study | (none; pending Phase 0) |

### Adobe Creative Cloud — Photoshop / Premiere / After Effects

| Field | Value |
|---|---|
| State | **scouted** (pending operator use-case confirmation) |
| URL | https://www.adobe.com/creativecloud.html |
| License | Adobe commercial license (operator account required) |
| What it is | Adobe's design + video suite. Automation via ExtendScript, Adobe Bridge, or third-party MCP wrappers. |
| Why we care | Potential use cases: Snap/TikTok creative pipeline automation (batch video generation, photo retouching, motion graphics for promotional assets, Hetzner deploy splash visuals). |
| Open question | What does the operator actually want to automate? (Promotional asset pipeline for snap.sinijkr.com? Video sequence generation for TikTok lures? Brand-pack maintenance?) |
| Phase | Phase 0 (verify) PENDING operator use-case confirmation. |
| Case-study | (none; pending Phase 0) |

### Autodesk Fusion 360 — CAD/CAM/CAE 3D modeling

| Field | Value |
|---|---|
| State | **scouted** (pending operator use-case confirmation) |
| URL | https://www.autodesk.com/products/fusion-360/overview |
| License | Autodesk commercial license (free tier for personal use) |
| What it is | CAD / CAM / CAE 3D modeling for product design, mechanical engineering, electronics. Python API + Fusion 360 Add-Ins for scripting. |
| Why we care | Potential use cases: hardware enclosure design (per `docs/HARDWARE-ROADMAP.md` — the rack / mini-PC build), Yurikey hardware mock-ups, 3D-print STL gen for accessories. |
| Open question | What does the operator actually want to design? (Enclosure for the N100 mini-PC + UPS stack? Hardware key mock-ups? Something else?) |
| Phase | Phase 0 (verify) PENDING operator use-case confirmation. |
| Case-study | (none; pending Phase 0) |

---

## How master grows this list

Every time the operator says "look into X" or master discovers a new public resource during normal work:

1. Append a row here with `state = scouted` and the basic facts.
2. If `state` upgrades to `forked-candidate` or `keep`, mirror to `skills/_INDEX.md`.
3. Operator-facing snapshot: `tools/mcp-discover/discover.py` (Phase D) auto-appends new MCP servers from the registry to this file's MCP-Registry section.

## How master shrinks this list

Never. Archive in place; don't delete rows. Operator scans the table to understand the fleet's external footprint at any time.
