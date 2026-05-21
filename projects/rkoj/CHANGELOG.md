> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ Changelog

All notable changes to the unified RKOJ project. Format roughly Keep-a-Changelog; versions are RKOJ.exe build versions, not component versions (each lane has its own).

## v1.1.0 — 2026-05-21

**Sinister Panel chrome, Niri workspace grid, 6 new slash impls, D-drive consolidation.** Operator ship of fleet-wide UI doctrine + ergonomic upgrades + workstation reorg.

- Sinister Panel chrome theme applied globally — 7497-char `THEME_CSS` block in `projects/sinister-forge/source/forge/theme.py`, picked up by every Forge pane on cold-start
- `NiriWorkspaceGrid` in the Agents tab — scrollable workspace columns with `Ctrl+Left/Right` (column nav), `Ctrl+Shift+Left/Right` (column reorder), `Ctrl+1..9` (jump-to-column); lives in `projects/sinister-forge/source/forge/panes/niri_workspace.py`
- `/mermaid` command — wires `memory-graph-render` into the TUI; renders brain-graph or session-graph as an ASCII mermaid block inside the active pane
- 5 more real slash impls: `/todo` `/focus` `/diff` `/search` `/export` (replacing v0.9.0 stubs; no `_cmd_*` lane-discipline violations)
- D-drive reorg Phase 1+2+3 — `D:\Backups\*` consolidated; `D:\sinister-vault` and `D:\Sinister\Sinister Skills` moved into Sanctum with backward-compat junctions; 5 clean projects relocated to `projects/sinister-*`
- Reference commits: `f722550` `d7e38c0` and the Phase 3 commit (GG2 agent, lands separately)

## v1.0.0 — 2026-05-21

**Forge TUI is now the default `RKOJ.exe` entry mode.** Operator directive (image 27 escalation): one project, one EXE, jcode-form base expanded with every skill / bot / tool the fleet has built.

- Forge TUI launches by default on `RKOJ.exe` (no flag needed)
- Sidebar visible on launch — Agents tab + ADB tab populated immediately
- `--shell` flag falls back to the v0.x `>` prompt (parachute mode)
- `RKOJ.exe info` prints manifest from `projects/rkoj/MANIFEST.json`
- Umbrella `projects/rkoj/` created in Sanctum — README + MANIFEST + INTEGRATION + this CHANGELOG
- EVE persona binding across heartbeats, commit trailers, pane headers
- Authorship migrated to RKOJ-ELENO on all new files

## v0.9.0 — 2026-05-21 (pre-umbrella)

Real implementations replacing earlier stubs.

- `/clear` — clears pane scrollback + resets context window
- `/compact` — invokes Anthropic compaction; preserves system prompt + last N turns
- `/context` — prints active context window stats (tokens used / budget / cache hit rate)
- `/save NAME` — persists conversation to `~/.sinister/sessions/NAME.jsonl`
- `/unsave NAME` — deletes a saved session
- `/rename OLD NEW` — renames a saved session
- `/rewind N` — rolls pane back N turns, refreshes prompt from journal
- jcode sidecar shim (`tools/sinister-jcode-shim/`) — translates jcode-style flags to SDK args

## v0.8.0

- `/help` overlay form — discoverable command list inside the TUI
- `/start` picker — choose project (sanctum / forge / freeze / ...) at boot
- 40+ jcode command stubs landed (69 total command surface)

## v0.7.0

- `anthropic_direct.py` — direct SDK path
  - parallel tool use
  - prompt caching (ephemeral + persistent breakpoints)
  - extended-thinking panel (delta-stream)
  - budget guard (token-cost ceilings per pane)
  - JSONL journaling for every request/response

## v0.6.0

- Anthropic SDK direct path added as alternative to `claude` subprocess
- Multi-step tool reasoning loop with retry + backoff

## v0.5.0

- jcode-shell rewrite
- `/resume` reconstructs context from the most recent JSONL journal
- forge-memory-bridge integration (BM25 + TF-IDF)
- `claude -p` invocation pattern for one-shot prompts inside scripts

## Conventions

- Versions before v1.0.0 lived in the sinister-forge lane CHANGELOG; this file consolidates them at the umbrella level going forward.
- Each component (forge, term, workstation, tools/*) keeps its own per-lane CHANGELOG; this file only tracks the integrated `RKOJ.exe` build.
- "EVE persona" + "RKOJ-ELENO authorship" are operator-canonical 2026-05-21 (see `_shared-memory/knowledge/agent-identity-eve.md`).
