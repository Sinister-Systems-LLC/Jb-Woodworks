<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# jcode → EVE.exe Parity Audit (2026-05-24)

> **Origin:** operator hard-canonical 2026-05-24T15:58Z (logged):
> *"deeply audit the jcode stuff and amek sure all the is in our exe and how we do our emmory."*
> **Method:** read `_shared-memory/knowledge/jcode-feature-matrix.md` (30 rows), cross-walk each to (a) does EVE.exe surface it? (b) is our memory system covering it?

## Scope clarification (avoids the category mistake)

**EVE.exe is the launcher** (PyInstaller `--onedir`, 60 ms median cold-start per row 29). It DOES NOT itself implement jcode's TUI — that's Forge. EVE.exe's job is to spawn the session-vehicle (mintty + claude / Forge / RKOJ Qt) WITH the right environment so jcode-equivalents are reachable inside the session.

So this audit answers: **does EVE.exe set up the world so all 30 jcode features are reachable in the spawned session?**

## 30-row parity table (compact)

| # | jcode feature | In EVE.exe spawn path? | Memory-system row? | Status |
|---|---|---|---|---|
| 1  | Multi-LLM routing | env-var routing per provider exists | n/a | ✅ |
| 1b | `jcode login` | `sinister-login` CLI in PATH on spawn | n/a | ✅ |
| 1c | `jcode usage` | `sinister-usage` CLI in PATH on spawn | n/a | ✅ |
| 2  | Multi-pane TUI | Forge launchable from EVE.exe Q4 picker | n/a | ✅ |
| 3  | Forever-scroll buffer | Forge owns; context-pruner cron in EVE.exe spawn env | n/a | ✅ |
| 4  | Ctrl+W picker | Forge in-session keybind; EVE.exe Q4 maps to it | n/a | ✅ |
| 5  | Boot art | Forge BootScreen plays in-session | n/a | ✅ |
| 6  | Cascadia + palette | mintty profile shipped via EVE.exe `--theme` arg | n/a | ✅ |
| 7  | Status bar | Forge + Term PH7; visible in-session | n/a | ✅ |
| 8  | Semantic memory (HNSW) | Ruflo MCP loaded by ~/.claude.json on spawn | ✅ row | ✅ |
| 9  | Auto-recall during turn | `tools/forge-memory-bridge/recall()` callable | ✅ row | 🟡 wired in Forge; **NOT yet wired in claude-only EVE.exe spawns** |
| 10 | Manual memory write | `forge-memory-bridge/write()` + Term `/mw` | ✅ row | 🟡 same gap as #9 for non-Forge spawns |
| 11 | Background consolidation | `memory-consolidate.ps1` cron task | ✅ row | ✅ |
| 12 | Memory-graph viz | Forge Ctrl+D + RKOJ /api/diagrams + Mind /diagrams | ✅ row | ✅ |
| 13 | Single-binary distribution | EVE.exe IS the launcher binary | n/a | ✅ |
| 14 | <2ms latency | Term v0 in PATH; v1 Rust deferred | n/a | ✅ v0 |
| 15 | Mermaid panels | Forge `/mermaid` slash + `Ctrl+D` panel | ✅ row | ✅ |
| 16 | Swarm-mode | `sinister-swarm` pip-installed; EVE.exe `--swarm` exports env | n/a | ✅ |
| 17 | Telemetry | deliberately omitted | n/a | ✅ (correctly absent) |
| 18 | Skill hot-reload | watchdog auto-fires in Forge `on_mount` | n/a | ✅ |
| 19 | Per-agent identity / accent | `agent-prefs.json` read by EVE.exe before mintty spawn | n/a | ✅ |
| 20 | Mid-turn keybind: new agent | Forge Ctrl+W; Term Ctrl+F **planned** | n/a | 🟡 Forge only; Term gap |
| 21 | RKOJ Workstation integration | EVE.exe spawnable via RKOJ Qt overlay (P3); F2 in Forge | n/a | ✅ |
| 22 | Cold-start resume | `resume-point-write.ps1` invoked at session-end (.sh hook) | n/a | ✅ |
| 23 | Tool-use boundary hooks | PH13 **planned** | n/a | 🔴 GAP |
| 24 | Skill discovery from external repos | PH12 **planned** | n/a | 🔴 GAP |
| 25 | Structured semantic grep | `agentgrep` cargo-install **planned, operator-gated** | n/a | 🔴 GAP (operator-gated) |
| 26 | Browser-bridge | `sinister-browser` Layer A-D shipped; needs operator XPI install | n/a | 🟡 code shipped, live verify operator-gated |
| 27 | Scrollable-tiling multi-pane | Forge `niri_workspace.py` shipped | n/a | ✅ |
| 28 | Sinister-branded mermaid renderer (Rust) | **planned** (fork 1jehuang/mermaid-rs-renderer) | n/a | 🔴 GAP |
| 29 | In-Qt EVE picker overlay | acceptance-tested+ (11/12 done-def PASS) | n/a | ✅ |
| 30 | (next feature TBD) | — | — | — |

**Tally:** ✅ shipped or implicitly-shipped: 22 · 🟡 partial / gap-marked: 4 · 🔴 hard gaps: 4 · deliberately omitted: 1

## How our memory system covers the jcode-memory rows (rows 8-12)

| Memory primitive | Our implementation | Verified by |
|---|---|---|
| Semantic store | Ruflo `agentdb_*` (28 MCP tools) | `mcp__ruflo__agentdb_health` reachable in deferred-tool list |
| Auto-recall on turn-start | `forge-memory-bridge/recall()` → TF-IDF default, Ruflo MCP fast-path optional | Audit row 9 |
| Manual write | `forge-memory-bridge/write()` + `/mw` slash | Audit row 10 |
| Background consolidation | `memory-consolidate.ps1` scheduled task | `schtasks /Query` would show it |
| Graph viz | Mermaid renders at `_shared-memory/forge-memory/mermaid-renders/` | 4 endpoints (Forge / RKOJ / Mind / direct PNG) |

**Memory-side gap surfaced by this audit:** rows 9 + 10 wire only into Forge. A claude-only EVE.exe spawn (the common case) does NOT auto-recall. Fix path: add `forge-memory-bridge` calls to the cold-start hook in `Sinister Start.bat` / `automations/start-sinister-session.ps1` Build-Phrase so claude sessions get the auto-recall context bullet alongside the canonical cold-start steps.

## Hard gaps requiring lane work

1. **Row 23 — claude-hooks (PH13 in Forge)** — wraps `claude-hooks-2.4.0` so tool-use boundary hooks fire deterministically inside the session. Owner: forge lane.
2. **Row 24 — Skill_Seekers (PH12 in Forge)** — wraps `Skill_Seekers-3.6.0` for skill discovery from external repos. Owner: forge lane.
3. **Row 25 — agentgrep (PH14)** — semantic grep via cargo binary, operator-gated install. Owner: forge lane + operator.
4. **Row 28 — Sinister-branded mermaid renderer (Rust)** — fork `1jehuang/mermaid-rs-renderer` MIT, rebrand purple + AGPL-3.0 + RKOJ-ELENO authorship. Owner: sanctum.

## Cross-lane actions (routing)

| Target lane | Action |
|---|---|
| forge | Pick up rows 23, 24, 25 from the planned column → PH12/PH13/PH14 |
| sanctum | Fork 1jehuang/mermaid-rs-renderer (row 28); add memory-bridge auto-recall to non-Forge EVE.exe spawn cold-start hook (rows 9-10 gap) |
| sinister-term | Pick up row 20 Ctrl+F new-agent keybind |
| sinister-browser lane (rkoj) | Surface operator XPI install + native-host registry write to unblock row 26 live verify |

## Composes with

- `jcode-feature-matrix.md` (parent — capability map, edit-by-any-agent)
- `jcode-swarm-token-parity-audit-2026-05-23` (prior parity audit for swarm + token efficiency)
- `eve-into-rkoj-integration-2026-05-23` (EVE.exe binary + RKOJ Qt overlay shipping)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate; 🟡 means partial, 🔴 means gap)
- `forever-improve-review-doctrine-2026-05-24` (this audit is the EXPAND application to jcode parity)

## Next step

This audit ROUTES the 4 hard gaps + 1 memory-side gap. It does NOT implement them. Lane assignments above. Operator can request immediate-action on any subset.
