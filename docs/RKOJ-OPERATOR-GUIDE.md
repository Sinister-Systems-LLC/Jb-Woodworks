> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ.exe Operator Guide — v1.1.0

`◈ EVE` — the jcode-form Sinister CLI agent.

> Supersedes the older workbench-centric guide. For the full workstation overview see `docs/WORKBENCH.md`. For deep architecture see `_shared-memory/knowledge/rkoj-workbench-architecture.md`.

---

## What's new in v1.1.0

Operator ship 2026-05-21 — fleet-wide UI doctrine, Niri-pattern ergonomics, 6 new real slash impls, D-drive reorg.

### Sinister Panel chrome theme

Global Forge pane theme applied on cold-start. 7497-char `THEME_CSS` block in `projects/sinister-forge/source/forge/theme.py` — purple Sanctum accent, chrome borders, scrollback styling. Picked up automatically by every pane (Agents tab, ADB tab, individual agent panes). No flag needed.

### NiriWorkspaceGrid (Agents tab)

Scrollable workspace columns inspired by the niri Wayland compositor. Source: `projects/sinister-forge/source/forge/panes/niri_workspace.py`.

| Keybinding | Action |
|---|---|
| `Ctrl+Left` / `Ctrl+Right` | Navigate between workspace columns |
| `Ctrl+Shift+Left` / `Ctrl+Shift+Right` | Reorder the active column |
| `Ctrl+1` … `Ctrl+9` | Jump directly to column 1–9 |

### `/mermaid` command

Wires `memory-graph-render` into the TUI. Renders the brain knowledge graph (or the active session graph) as an ASCII mermaid block inside the current pane.

Example:

```
/mermaid brain --tag forge-memory
```

### 5 more real slash impls

These replace the v0.9.0 "not implemented" stubs with working implementations:

- `/todo` — append/list operator-private todos for the active project
- `/focus` — narrow the active context window to a single subsystem or tag
- `/diff` — show staged + unstaged diff for the current branch inside the pane
- `/search` — BM25 search across `_shared-memory/` + PROGRESS logs + brain
- `/export` — write the active session JSONL to a chosen path for handoff

### D-drive consolidation

Phase 1 + 2 + 3 reorg landed:
- `D:\Backups\*` consolidated under a single root
- `D:\sinister-vault` → moved into Sanctum, original path is now a junction
- `D:\Sinister\Sinister Skills` → moved into Sanctum, original path is now a junction
- 5 clean projects relocated to `projects/sinister-*` (GG2 agent owns the Phase 3 commit + MANIFEST `components` entries for those 5)

---

## 1. Elevator pitch

RKOJ.exe is EVE: the jcode-form Sinister CLI agent. Click-to-launch, talks to Claude / OpenAI / Gemini / etc., remembers across sessions, runs your skills, swarm-aware.

---

## 2. Quick start

1. Double-click `C:\Users\Zonia\Desktop\RKOJ.exe`.
2. Type `/help` to see all 69 commands.
3. Type `/start` to pick a project + mode.
4. Or type natural language directly — it spawns an EVE turn with multi-step tool reasoning.
5. `/quit` to exit.

---

## 3. Feature map

| Category | What you get |
|---|---|
| **Form & UI** | SINISTER mark on cold-start, purple status panel, `/help` overlay with 6 sections, animated spinners, EVE persona banner |
| **Backend** | Anthropic SDK direct path when `ANTHROPIC_API_KEY` is set, `claude -p` fallback otherwise, BM25 memory recall, prompt-caching of system + tool blocks, JSONL session journaling under `_shared-memory/sessions/`, 12-turn agentic loop, 150K-token turn budget guard, parallel read-only tool execution |
| **Slash commands** | 69 commands across six categories — see `/help` |
| **Skills** | `SkillRegistry` loads `~/.sinister/skills/*.md` + bundled `D:/Sinister Sanctum/skills/*.md` and registers each as a slash command |
| **Bundled tools** | `sinister-login`, `sinister-usage`, `sinister-swarm`, `sinister-model`, `sanctum-backup`, `forge-memory-bridge`, `memory-graph-render`, `sinister-jcode-shim` |

### Slash-command categories

| Category | Count | Examples |
|---|---|---|
| Commands | 17 | `/model` `/effort` `/fast` `/transport` `/alignment` `/config` `/dictate` `/git` `/context` `/changelog` |
| Session | 20 | `/clear` `/compact` `/rewind` `/fix` `/poke` `/improve` `/refactor` `/split` `/splitview` `/transfer` `/workspace` `/catchup` `/save` `/rename` |
| Memory & Swarm | 3 | `/memory` `/swarm` `/goals` |
| Auth & Accounts | 4 | `/login` `/auth` `/account` `/subscription` |
| System | 7 | `/reload` `/restart` `/rebuild` `/version` `/info` `/debug-visual` `/usage` |
| Navigation | 2 | `/projects` `/agents` |

Implemented today (v1.1.0): `/help` `/quit` `/version` `/info` `/projects` `/start` `/resume` `/agents` `/inbox` `/brain` `/login` `/usage` `/swarm` `/memory` `/forge` `/mermaid` `/todo` `/focus` `/diff` `/search` `/export`. Everything else is a jcode-parity stub that prints "not implemented in v1.1.0" and routes to the parity roadmap.

---

## 4. Environment variables

The full set lives in `docs/ENV-VARIABLES.md`. These six matter most for RKOJ:

| Variable | Effect |
|---|---|
| `ANTHROPIC_API_KEY` | Unlocks the Anthropic SDK direct path — multi-step tool reasoning, prompt caching, parallel tool calls. Without it RKOJ falls back to `claude -p`. |
| `OPENAI_API_KEY` | Codex peer review + OpenAI provider in the model picker. |
| `SANCTUM_ROOT` | Override Sanctum root location (auto-detected to `D:/Sinister Sanctum`). |
| `SINISTER_PROJECT` | Auto-spawn target project on launch (skips `/start` picker). |
| `SINISTER_MODE` | One of `resume` / `expand` / `shell`. |
| `SINISTER_DICTATE_CMD` | Path to the dictation launcher used by `/dictate`. |

Bonus: `ANTHROPIC_DIRECT_TOKEN_BUDGET` overrides the 150K-token turn cap.

---

## 5. Memory model

RKOJ blends three layers:

- **forge-memory-bridge** (`tools/forge-memory-bridge/`) — durable per-project memory in `_shared-memory/forge-memory/<project>/`. Indexed by tag, used for cross-session continuity.
- **BM25 recall** — every turn, the user message is BM25-scored against past JSONL session transcripts and brain entries; top hits are stitched into the system prompt with cache-control markers so they cache between turns.
- **JSONL session journaling** — every turn is appended to `_shared-memory/sessions/<slug>/<timestamp>.jsonl` so `/rewind`, `/transfer` and `/catchup` can replay or compact prior context.

The patterns underneath this are documented in the brain entry `_shared-memory/knowledge/jcode-agentic-loop-patterns-port-to-python.md` — the canonical reference for the 12-turn loop, the parallel-read-only batching, and how the cache-control points are placed.

---

## 6. Differences from jcode

| Axis | RKOJ.exe | jcode |
|---|---|---|
| Form factor | Click-to-launch terminal CLI with purple status panel | Same |
| `/help` overlay | 6 sections | Same |
| Command count | ~69 (15 implemented + parity stubs) | 60+ |
| Batch tool calls | Yes (parallel read-only) | Yes |
| Streaming thinking blocks | Yes | Yes |
| `session_search` | Yes (BM25 over JSONL) | Yes |
| Language | Python (3.11) | Rust |
| Auth wallet | 11-provider via `sinister-login` | jcode-internal |
| MCP stack | Ruflo + Vault MCP (Sinister-owned) | jcode MCP |
| Skills root | `~/.sinister/skills/` + `D:/Sinister Sanctum/skills/` | `~/.jcode/skills/` |

**Sidecar:** `tools/sinister-jcode-shim/` can run the real `jcode` binary with Sinister env injected — true jcode features today, Python port matures behind it.

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `/help` prints plain text, no overlay | `rich` import failed inside the EXE — `pip install rich` in the build venv and rebuild, or run from source. |
| Natural-language input hangs forever | `claude.exe` is missing from `PATH`. Set `JCODE_BIN` to a known-good Claude Code binary or install Claude Code CLI. |
| No multi-step tool reasoning | `ANTHROPIC_API_KEY` is unset — RKOJ is on the `claude -p` single-shot fallback. Set the key (see `_shared-memory/OPERATOR-ACTION-QUEUE.md`). |
| `/memory` recall returns nothing | The forge-memory index is empty. Run `python -m forge_memory_bridge import` to bootstrap from existing PROGRESS/brain content. |

---

## 8. Rebuild from source

```
cd "D:\Sinister Sanctum\automations\build\forge-exe"
pyinstaller --clean --noconfirm RKOJ.spec
cp dist/RKOJ.exe ~/Desktop/
```

Source of truth: `RKOJ-entry.py` (single-file build target). Spec: `RKOJ.spec`.

---

## 9. Help inside RKOJ

| Command | What it does |
|---|---|
| `/help` | All commands grouped by category. |
| `/help <command>` | Detail for one command. |
| `/brain <tag>` | Search brain entries by tag. |
| `/projects` | List all known projects. |
| `/agents` | Live heartbeats from the fleet. |
| `/info` | Build + env + Sanctum-root summary. |
| `/version` | Print the RKOJ build version. |

---

> Persona: **EVE**. Authorship: **RKOJ-ELENO**. Branch lane: `agent/sinister-sanctum/cli-dispatcher-2026-05-21`.
