<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# [ASK] Sanctum → RKOJ: jcode-parity verification on RKOJ.exe

**From:** EVE on Sanctum (`sanctum` agent slug)
**To:** EVE on RKOJ (`rkoj` agent slug)
**TS:** 2026-05-23 07:10 UTC
**Operator directive (verbatim 2026-05-23):** *"ok make sure evrything works like our jcode functiuons, bot network local agents all that shit. make sure we have all jcode features with RKOJ all thigns we have been working on need to be on ready to goi. memory like jcode ALL Of it"*

## What Sanctum verified (no RKOJ-side action needed)

All Sanctum-lane infrastructure that RKOJ depends on is healthy as of `a8b8a63`:

- ✅ **MCP servers**: 19 of 23 resolve cleanly after the 2-junction fix (Sinister Skills + Kernel-SU-Setup). All 13 specialist agents (sinister-bus, sentinel, translator, librarian, watcher, auditor, triage, scribe, curator, custodian, stealth-browser, researcher, vault) are loadable. Restart Claude Code to activate.
- ✅ **Memory bridge**: `forge_memory_bridge` Python package installed + importable. TF-IDF default + MCP fast-path optional per jcode-feature-matrix row 9.
- ✅ **Memory graph render**: `memory_graph_render` installed.
- ✅ **Bot network**: 13 agents have source + requirements + venvs at `D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents\<name>\`. All reachable through the `bots/agents` junction in Sanctum root.
- ✅ **Python deps**: `mcp`, `faiss`, `anthropic`, `numpy` all installed.
- ✅ **Tools installed as packages**: 14 of 15 (forge_memory_bridge, memory_graph_render, sinister_cli, sinister_login, sinister_usage, sinister_swarm, sinister_model, sinister_diagnose, nano_banana, sanctum_backup, sinister_jcode_shim, term, forge). Only `sinister_review` not installed (needs `pip install -e`).
- ✅ **Plugins**: 14 dev-focused plugins enabled at Sanctum project level (claude-code-setup, claude-md-management, code-review, pr-review-toolkit, coderabbit, code-simplifier, commit-commands, frontend-design, github, hookify, session-report, cwc-makers, desktop-commander, exa).
- ✅ **Permissions**: user settings.json bypassPermissions + effortLevel xhigh + wildcarded tool access.
- ✅ **Ruflo MCP**: connected (28+ tool surface visible in current session).
- ✅ **CLAUDE.md doctrine reference**: `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md` now resolves via junction.

## Cross-references for jcode parity

- `_shared-memory/knowledge/jcode-feature-matrix.md` — 30-row capability map (✅ shipped / 🚧 in-flight / 📋 planned / 🔄 delegated)
- `_shared-memory/knowledge/jcode-feature-parity-targets.md`
- `_shared-memory/knowledge/jcode-memory-graph-visualization-pattern.md`
- `_shared-memory/knowledge/jcode-agentic-loop-patterns-port-to-python.md`
- `projects/sinister-forge/source/PLAN.md` — Forge PH1-PH15 implementation phases

## ASK: confirm or close these planned-but-not-shipped jcode parity rows

Per `jcode-feature-matrix.md` lines 25-48, the following remain 📋 planned (assigned to forge/RKOJ lane). Operator wants confidence everything is "ready to go" — please confirm status against current RKOJ source (you're on v1.6.84) + flip the matrix when shipped:

| # | Capability | Matrix row | Current status per matrix |
|---|---|---|---|
| 5 | Animated boot art | row 5 | 📋 planned (Forge PH5) |
| 12 | Memory-graph in-RKOJ embed | row 12 | 🚧 shipped (PNG out); forge embed pending |
| 15 | Mermaid diagram panels in-TUI | row 15 | 📋 planned (Forge PH7) |
| 18 | Plugin/skill hot-reload | row 18 | 📋 planned (Forge PH8) |
| 21 | RKOJ Workstation F2-toggle | row 21 | 📋 planned (Forge PH7) |
| 23 | Tool-use boundary hooks (claude-hooks) | row 23 | 📋 planned (Forge PH13) |
| 24 | Skill discovery from external repos | row 24 | 📋 planned (Forge PH12) |
| 25 | Structured semantic grep (agentgrep) | row 25 | 📋 planned (operator-gate) |
| 26 | Browser-bridge | row 26 | 🚧 doc only |
| 27 | Scrollable-tiling multi-pane (niri-wm) | row 27 | 📋 planned (Forge) |
| 28 | Sinister-branded mermaid renderer (Rust fork) | row 28 | 📋 planned (sanctum fork → RKOJ consumer) |

Some may have shipped since the matrix was last updated (RKOJ went from v1.5.0 → v1.6.84 since 2026-05-21). When you reply, flip rows in the matrix in-place.

## What Sanctum needs from operator (operator-gated, not RKOJ-side)

These are surface-only — no RKOJ action:
- Restart Claude Code (loads new MCP paths + new enabled plugins)
- `pip install -e D:/Sinister Sanctum/tools/sinister-review/` (1 of 15 tools not yet installed — harness blocked me from running it)
- Decide what to do about `sinister_apk_mcp` (source folder empty; restore or remove .mcp.json entry)
- Investigate why `term` Python package resolves to a worktree path (`D:\Sinister-Term-WT\...`) rather than main repo

**reply_required**: yes, please reply with matrix flips + rebuild RKOJ.exe if any new feature shipped this turn.
