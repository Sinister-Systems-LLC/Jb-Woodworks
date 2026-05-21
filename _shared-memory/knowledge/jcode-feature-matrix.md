# jcode Feature Matrix :: where every jcode capability lives in our Sinister stack

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Operator directives:**
> - *"i want all jcode features etc and i want our own terminal system. just like he has"* + *"all with our sinister braning"* (2026-05-21)
> - *"https://github.com/niri-wm/niri make sure we do what jcode does and use tools like this in our own way"* (2026-05-21T13:50Z)
> - *"https://github.com/1jehuang/mermaid-rs-renderer … take code you need intergrate with our things. make it all our theme branding etc"* (2026-05-21T13:55Z)
> **Origin:** jcode-0.12.3 (1jehuang, MIT). Read-only reference at `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\`. Our re-implements are AGPL-3.0-or-later with attribution in NOTICES per canonical-20.
> **Goal:** ONE place mapping every jcode capability → where it lives in our stack → owner agent → status. Stops us from re-deciding "should I port X or delegate to Ruflo" every cold-start.

## Status legend

- ✅ **shipped** · 🚧 **in-flight** · 📋 **planned** · 🔄 **delegated**

## The matrix (29 rows — expanded 2026-05-21T13:50Z with sinister-login wallet shipped)

| # | jcode capability | Our home | Status | Owner | Notes |
|---|---|---|---|---|---|
| 1 | Multi-LLM provider routing | `automations/agent-host-routing.md` + Forge `:host` cmd | ✅ doc / 📋 UI | sanctum + forge | doc commit `bce833f` |
| 1b | `jcode login --provider X` (11 providers) | `tools/sinister-login/` v0.1.0 | ✅ shipped | sanctum | env-var-first wallet; 11 providers: claude/openai/gemini/copilot/azure/alibaba-coding-plan/fireworks/minimax/lmstudio/ollama/openai-compatible. Stdlib-only. Opt-in TCP probe. Refuses plaintext-on-disk by default. CLI: `sinister login providers/current/doctor/env/add/matrix`. Wired into `sinister-cli` umbrella. 21/21 unittests green. |
| 2 | Multi-pane scrolling TUI | Forge `panes/agent_pane.py` (PH2-PH3) | ✅ scaffold | forge | Textual Log widget virtual-scroll |
| 3 | Forever-scroll buffer per agent | Forge `panes/agent_pane.py` | ✅ scaffold | forge | context-pruner.ps1 archives long-term |
| 4 | Ctrl+W new-agent picker | Forge `panes/picker.py` (PH3) | ✅ shipped | forge | ports `start-sinister-session.ps1` Q1-Q5 |
| 5 | Animated boot art | Forge `art.py` (PH5) | 📋 planned | forge | Vault Boy rotating frames; 1.2s |
| 6 | Cascadia Code typography + jcode palette | Forge `theme.py` (PH11) | ✅ scaffold / 📋 polish | forge | purple `#7A3DD4` + dim cyan |
| 7 | Status bar + breadcrumbs | Forge `panes/status_bar.py` + Term shell PH7 | ✅ Forge stub / ✅ Term PH7 | forge + sinister-term | cwd / git branch / heartbeat pill |
| 8 | Semantic memory (HNSW + embeddings) | Ruflo `agentdb_*` (28 tools) | 🔄 delegated | sanctum (bridge) | DO NOT re-implement HNSW |
| 9 | Auto-recall during turn | `tools/forge-memory-bridge/recall()` → Ruflo `agentdb_pattern-search` | 🚧 v0.1.1 shipped | sanctum | TF-IDF default; MCP fast-path optional |
| 10 | Manual memory write | `tools/forge-memory-bridge/write()` + Forge `:memory write` + Term `/jcode-memory-write` | 🚧 bridge / 📋 UI | sanctum (bridge) + forge + sinister-term | Term `/mw` alias uses it |
| 11 | Background memory consolidation | `automations/memory-consolidate.ps1` → Ruflo `agentdb_consolidate` | 🚧 shipped + install-task | sanctum | nightly cron |
| 12 | Memory-graph visualization | `tools/memory-graph-render/` → mermaid → `mermaid-rs-renderer` → PNG | 🚧 shipped | sanctum (render) + forge (RKOJ embed) + mind (web view) | PNGs at `inventions/memory-graphs/` |
| 13 | Single-binary distribution | Forge + Term `pip install -e .` + entry-points | ✅ both | forge + sinister-term | pyproject.toml |
| 14 | Per-keypress latency <2ms | Term v0 Python+prompt_toolkit; Term v1 Rust port (deferred) | ✅ v0 / 📋 v1 | sinister-term | Rust port = 30-day proving period |
| 15 | Mermaid diagram panels (in-TUI) | Forge PH7 RKOJ tab embeds PNGs | 📋 planned | forge | NOT in-TUI; embed via web view |
| 16 | Swarm-mode (multi-agent) | Ruflo `hive-mind_*` + Sanctum `inbox/` + `cross-agent/` | ✅ disk + 🚧 MCP | sanctum + all | hive `hive-1779361043392-k9b2bw` queen=sanctum |
| 17 | Telemetry (phones home) | **NOT PORTED** — data sovereignty | ✅ omitted | n/a | local only |
| 18 | Plugin / skill hot-reload | Forge `forge/plugins/` watchdog (PH8) + `_shared-memory/skills/` | 📋 planned | forge + sanctum | file-change → reload |
| 19 | Per-agent identity / accent / project header | `automations/session-templates/agent-prefs.json` + Forge `app.py` | ✅ both | sanctum + forge | bold project name per pane |
| 20 | Mid-turn keybind: open new agent | Forge Ctrl+W / Term Ctrl+F (planned) | ✅ Forge / 📋 Term | forge + sinister-term | Term keybind opens Forge inline |
| 21 | RKOJ Workstation integration | Forge PH7 (`panes/rkoj_panel.py`) F2-toggle to RKOJ :5077 | 📋 planned | forge + rkoj | embed as sidebar (Q2 default) |
| 22 | Cold-start resume | CONTRACT 7 + `automations/resume-point-write.ps1` | ✅ shipped | sanctum + all | inaugural Sanctum resume-point this session |
| 23 | Tool-use boundary hooks | Forge PH13 `claude-hooks` integration | 📋 planned | forge | wraps `claude-hooks-2.4.0` |
| 24 | Skill discovery from external repos | Forge PH12 `Skill_Seekers` integration | 📋 planned | forge | wraps `Skill_Seekers-3.6.0` |
| 25 | Structured semantic grep | Forge PH14 `agentgrep` (operator-gated cargo install) | 📋 planned | forge | operator-gate |
| 26 | Browser-bridge (web-as-tool) | `_shared-memory/knowledge/agent-browser-bridge-pattern.md` (Forge PH15) | 🚧 doc | sanctum (doc) | NOT clone-and-run |
| 27 | **Scrollable-tiling multi-pane** (niri-wm pattern) | Forge `panes/*` PH2-PH3 + `_shared-memory/knowledge/scrollable-tiling-pattern.md` (TODO) | 📋 planned | forge | Operator: niri-wm/niri pattern; mine the column-scroll UX (Wayland code itself doesn't port) |
| 28 | **Sinister-branded mermaid renderer (Rust)** | `tools/sinister-mermaid-render/` (TODO: fork 1jehuang/mermaid-rs-renderer) | 📋 planned | sanctum (fork) | Operator: rebrand Sinister purple boot art + AGPL-3.0 + RKOJ-ELENO; used by `memory-graph-render/` Stage 3 |

## Composes-with map

`forever-expanding-modular-architecture-doctrine.md` (meta) → `sibling-active-launch-coordination-pattern.md` (runtime) → `jcode-feature-matrix.md` (THIS — capability map) → individual implementation tools (`forge-memory-bridge/` + `memory-graph-render/` + `memory-consolidate.ps1` + `agent-host-routing.md` + `start-sinister-session.ps1` + Forge source tree + Term source tree + Mind source tree + Ruflo MCP)

## What we deliberately did NOT port

- jcode telemetry (data sovereignty)
- Single-EXE Rust binary (Python preferred for velocity; Rust deferred to Forge Q1 + Term Track B)
- MIT license (we use AGPL-3.0-or-later per canonical-20)
- External package registry (skills come from disk + Ruflo, not marketplace)

## Update protocol

Edit-by-any-agent. When you ship a feature: flip Status column, update Owner if lane shifted, add commit hash + date to Notes.

## Cross-references

- `projects/sinister-forge/source/PLAN.md` — Forge PH1-PH15
- `_shared-memory/plans/sinister-forge-2026-05-21/jcode-memory-feature.md` — original jcode-memory mining
- `_shared-memory/plans/sinister-forge-2026-05-21/sanctum-audit-findings.md` — Sanctum Audit Agent TOP-5
- `_shared-memory/knowledge/sibling-active-launch-coordination-pattern.md`
- `_shared-memory/knowledge/jcode-memory-graph-visualization-pattern.md`
- `_shared-memory/knowledge/agent-browser-bridge-pattern.md`
- `_shared-memory/knowledge/sinister-freeze-project-doctrine.md`
- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`
- `automations/agent-host-routing.md`
- `automations/session-contracts.md`
