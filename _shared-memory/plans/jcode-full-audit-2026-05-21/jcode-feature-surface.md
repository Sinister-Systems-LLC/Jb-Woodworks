# jcode Full Feature Surface :: comprehensive audit for Sinister re-implementation

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Origin:** jcode v0.12.3 (1jehuang, MIT) at `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\`
> **Target license for our re-implementations:** AGPL-3.0-or-later with NOTICES attribution per canonical-20
> **Companion doc (28-row capability map):** `_shared-memory/knowledge/jcode-feature-matrix.md`
> **Operator directive (2026-05-21):** *"i want all jcode features etc and i want our own terminal system. just like he has"* + *"all with our sinister braning"*

This document is the **deep dive**. The 28-row matrix is the **short-pointer**. Together they cover every subcommand, tool, config flag, plugin hook, MCP, UI feature, telemetry, and gap.

Brain entries shipped this session that this audit builds on:
- `jcode-feature-matrix.md` (the short pointer)
- `forever-expanding-modular-architecture-doctrine.md`
- `sibling-active-launch-coordination-pattern.md`
- `agent-browser-bridge-pattern.md`
- `jcode-memory-graph-visualization-pattern.md`
- `sinister-freeze-project-doctrine.md`
- `sinister-cli-naming-convention.md`
- `sinister-swarm-jcode-parity-pattern.md`

Already shipped in `tools/` this session:
- `forge-memory-bridge/` v0.1.1
- `memory-graph-render/` v0.1.0
- `sinister-swarm/` v0.1.0
- `sinister-cli/` v0.1.0

---

## 1. Repo overview

### Top-level structure (jcode-0.12.3)

```
jcode-0.12.3/
  Cargo.toml          # workspace root (single bin `jcode`, 4 dev bins)
  Cargo.lock          # 222KB
  README.md           # 30KB — main feature surface
  AGENTS.md           # 2KB — repo conventions
  OAUTH.md            # 16KB — full auth doc
  TELEMETRY.md        # 17KB — opt-in schema v5 detail
  PLAN_MCP_SKILLS.md  # 3KB — original MCP+skills plan
  RELEASING.md        # 6KB
  LICENSE             # MIT (1KB)
  build.rs            # 12KB
  codemagic.yaml      # iOS CI
  terminal-capabilities.md
  jcode_demo_jaguar.{avif,mp4}  # demo media
  screenshot.png
  src/                # 100+ Rust files (.rs); the main bin
  crates/             # 48 workspace crates (see Section 3)
  docs/               # 35+ design docs (AMBIENT, MEMORY, SWARM, SAFETY, etc.)
  scripts/            # 60+ helper bash/py/ps1 scripts (install, bench, smoke)
  tests/              # integration tests
  packaging/linux/    # .deb / .rpm
  ios/                # native iOS app (Swift, Package.swift)
  figma/              # design specs (.svg + plugin)
  assets/             # demo / readme / niri-screenshot.png
  telemetry-worker/   # Cloudflare Worker (Node) backend for opt-in telemetry
  mockups/
  .jcode/skills/      # repo-local skills (optimization/ shipped)
  .claude/mcp.json    # fallback MCP config (compatibility w/ Claude Code)
```

### License + version

| Field | Value |
|---|---|
| License | **MIT** (single LICENSE file, 1069 bytes) |
| Crate version | `0.12.3` (per Cargo.toml `[package].version`) |
| Build description | *"Possibly the greatest coding agent ever built — blazing-fast TUI, multi-model, swarm coordination, 30+ tools"* |
| Rust edition | 2024 |
| Default features | `["pdf"]` (PDF parsing on by default; embeddings off) |

### Build system

**Cargo workspace** with 48 member crates + the root binary `jcode`. The root `Cargo.toml` defines:

- 1 primary bin: `jcode` (`src/main.rs`)
- 4 dev bins (behind `dev-bins` feature): `test_api`, `jcode-harness`, `session_memory_bench`, `mermaid_side_panel_probe`, `tui_bench`
- Feature flags: `default = ["pdf"]`, plus `jemalloc`, `jemalloc-prof`, `embeddings`, `mmdr-size-api`, `pdf`, `dev-bins`
- Release profiles: `release` (opt-level=1, 256 codegen units, incremental), `release-lto` (thin LTO, distribution), `selfdev` (opt-level=0 for fast self-dev rebuilds)
- Platform deps: Windows uses `windows-sys` (Threading/Foundation), macOS uses `global-hotkey 0.7`

Heavyweight subtrees (ONNX/tokenizers for local embedding) are gated behind `embeddings` feature — 163 crates that slow `cargo check`, off by default.

### Main entry-points

| Path | Purpose |
|---|---|
| `src/main.rs` | bin entry; calls `cli::dispatch` |
| `src/lib.rs` | library root (re-exports) |
| `src/cli/mod.rs` + `src/cli/dispatch.rs` | clap subcommand router |
| `src/cli/args.rs` | full clap derive struct (Args + Command enum) |
| `src/cli/tui_launch/tui_launch.rs` | default TUI launch path |
| `src/server/mod.rs` + `src/server.rs` | persistent daemon (`jcode serve`) |
| `src/agent.rs` | agent runtime (turn execution, streaming, tools) |
| `src/tool/mod.rs` | tool registry (32+ built-in tools) |
| `src/mcp/mod.rs` | MCP client / manager |
| `src/memory/mod.rs` + `src/memory.rs` | semantic memory graph |
| `src/tui/app/mod.rs` | TUI app state machine |
| `crates/jcode-desktop` | desktop superapp host (iced-based per docs) |
| `ios/Sources/` | iOS native client |
| `telemetry-worker/` | Cloudflare Worker telemetry backend |

---

## 2. EVERY jcode CLI subcommand (`jcode <X>`)

Pulled directly from `src/cli/args.rs` clap derive (`enum Command`). Each row maps to a Sinister equivalent.

| # | jcode subcommand | Flags / options | What it does | jcode code location | Sinister equivalent | Suggested Sinister name |
|---|---|---|---|---|---|---|
| 1 | (no subcommand) | global flags | Launch TUI | `src/cli/tui_launch/` | Forge `forge` entry | `sinister forge` (umbrella) |
| 2 | `serve` | `--temporary-server`, `--owner-pid`, `--temp-idle-timeout-secs` | Start background daemon | `src/server.rs` | 📋 NOT YET | `sinister serve` |
| 3 | `connect` | — | Connect to running server | `src/cli/dispatch.rs` | 📋 NOT YET | `sinister connect` |
| 4 | `run <message>` | `--json`, `--ndjson` | One-shot non-interactive | `src/cli/commands.rs` | 📋 NOT YET (sinister-bus `inbox_post` is closest) | `sinister run "msg"` |
| 5 | `login` | `--provider`, `--account`, `--no-browser`, `--print-auth-url`, `--callback-url`, `--auth-code`, `--complete`, `--json`, `--no-validate`, `--google-access-tier`, `--api-base`, `--api-key`, `--api-key-env` | Provider OAuth/API-key | `src/cli/login/` | 📋 NOT YET (we use Claude Code's auth) | `sinister login --provider <x>` |
| 6 | `repl` | — | REPL mode (no TUI) | `src/cli/dispatch.rs` | 📋 NOT YET | `sinister repl` |
| 7 | `update` | — | Self-update binary | `src/update.rs` | 📋 sanctum's `verify-auto-push.ps1` is git-side only | `sinister update` |
| 8 | `version` | `--json` | Build/version info | `src/cli/dispatch.rs` | ✅ `sinister-cli` umbrella shows version per subcommand | `sinister version` |
| 9 | `usage` | `--json` | Provider usage / token quota | `src/usage.rs` | 📋 NOT YET | `sinister usage` |
| 10 | `self-dev` (alias `selfdev`) | `--build` | Canary self-mod session | `src/cli/selfdev.rs` | 📋 NOT YET (operator-gated; lane-violation risk) | `sinister selfdev` (operator-gated) |
| 11 | `debug <cmd> [arg]` | `-S/--session`, `-s/--socket`, `-w/--wait` | Inspect running server (list, sessions, message, tool, state, history) | `src/cli/debug.rs` | ✅ partial via `sinister-bus.heartbeat` + `inbox_poll` | `sinister debug` |
| 12 | `auth status` | `--json` | Show configured auth | `src/cli/commands.rs` | 📋 NOT YET | `sinister auth status` |
| 13 | `auth doctor` | `<provider>`, `--validate`, `--json` | Diagnose provider auth | `src/cli/commands.rs` | 📋 NOT YET | `sinister auth doctor` |
| 14 | `provider list` | `--json` | List provider IDs | `src/cli/commands.rs` | ✅ doc at `automations/agent-host-routing.md` | `sinister provider list` |
| 15 | `provider current` | `--json` | Show resolved provider | — | 📋 NOT YET | `sinister provider current` |
| 16 | `provider add <name>` | `--base-url`, `-m/--model`, `--context-window`, `--api-key-env`, `--api-key`, `--api-key-stdin`, `--no-api-key`, `--auth`, `--auth-header`, `--env-file`, `--set-default`, `--overwrite`, `--provider-routing`, `--model-catalog`, `--json` | Add OpenAI-compat profile to `~/.jcode/config.toml` | `src/cli/commands/provider_setup.rs` | 📋 NOT YET | `sinister provider add` |
| 17 | `memory list` | `-s/--scope`, `-t/--tag` | List memories | `src/cli/commands.rs:216` | 🚧 `forge-memory-bridge` has `list()` | `sinister memory list` |
| 18 | `memory search <query>` | `-s/--semantic` | Search memories | `src/cli/commands.rs` | 🚧 `forge-memory-bridge` has `recall()` (TF-IDF + MCP fallback) | `sinister memory search` |
| 19 | `memory export <output>` | `-s/--scope` | Dump memories to JSON | — | 📋 NOT YET (Ruflo handles export) | `sinister memory export` |
| 20 | `memory import <input>` | `-s/--scope`, `--overwrite` | Load memories from JSON | — | 📋 NOT YET | `sinister memory import` |
| 21 | `memory stats` | — | Counts / sizes | — | 📋 NOT YET | `sinister memory stats` |
| 22 | `memory clear-test` | — | Wipe test storage | — | 📋 NOT YET | `sinister memory clear-test` |
| 23 | `session rename <ref> <name>` | `--clear`, `--json` | Rename session | `src/cli/commands.rs:104` | 📋 NOT YET | `sinister session rename` |
| 24 | `ambient status` | — | Background loop status | `src/cli/commands.rs:38` | 🚧 `memory-consolidate.ps1` is partial | `sinister ambient status` |
| 25 | `ambient log` | — | Recent activity | — | 📋 NOT YET | `sinister ambient log` |
| 26 | `ambient trigger` | — | Force a cycle | — | 📋 NOT YET | `sinister ambient trigger` |
| 27 | `ambient stop` | — | Disable | — | 📋 NOT YET | `sinister ambient stop` |
| 28 | `ambient run-visible` | hidden | Internal: visible cycle TUI | — | n/a | n/a |
| 29 | `pair` | `--list`, `--revoke` | Generate pairing code for iOS/web | `src/cli/dispatch.rs` | 📋 NOT YET (Mind handles web; iOS not built) | `sinister pair` |
| 30 | `permissions` | — | Review pending ambient permission requests | `src/safety.rs` | 📋 NOT YET | `sinister permissions` |
| 31 | `transcript <text>` | `--mode`, `-S/--session` | Inject text into TUI | `src/cli/commands.rs:54` | 📋 NOT YET (Forge has `:agent send`) | `sinister transcript` |
| 32 | `dictate` | `--type` | Run configured STT command | `src/cli/commands.rs:86` | 📋 NOT YET | `sinister dictate` |
| 33 | `setup-hotkey` | `--listen-macos-hotkey` (hidden) | Install global hotkey (Alt+;) | `src/cli/dispatch.rs` | 📋 NOT YET (operator-launcher handles this on Windows) | `sinister setup-hotkey` |
| 34 | `setup-launcher` | — | Install desktop launcher entry | — | ✅ `Start-Sinister-Session.bat` | `sinister setup-launcher` |
| 35 | `browser <action>` | default `setup`; also `status` | Firefox Agent Bridge setup | `src/browser.rs` | 🚧 `agent-browser-bridge-pattern.md` doc only | `sinister browser` |
| 36 | `replay <session>` | `--swarm`, `--export`, `--speed`, `--timeline`, `--auto-edit`, `--video`, `--cols`, `--rows`, `--fps`, `--centered`, `--no-centered` | Replay saved session (incl. video export) | `src/replay/` | 📋 NOT YET (no session-replay infra) | `sinister replay` |
| 37 | `model list` | `--json`, `--verbose` | Available models | `src/cli/dispatch.rs` | 📋 NOT YET | `sinister model list` |
| 38 | `auth-test` | `--login`, `--all-configured`, `--no-smoke`, `--no-tool-smoke`, `--prompt`, `--json`, `--output` | End-to-end auth e2e | `src/cli/auth_test/` | 📋 NOT YET | `sinister auth-test` |
| 39 | `restart save` | `--auto-restore` | Snapshot open jcode windows | `src/cli/commands/restart.rs` | ✅ partial — Sanctum `automations/resume-point-write.ps1` | `sinister restart save` |
| 40 | `restart restore` | — | Restore window snapshot | — | ✅ partial — `start-sinister-session.ps1` honors `resume-points/` | `sinister restart restore` |
| 41 | `restart status` | — | Show snapshot | — | 📋 NOT YET | `sinister restart status` |
| 42 | `restart clear` | — | Wipe snapshot | — | 📋 NOT YET | `sinister restart clear` |

**Top-level global flags** (`Args` struct, applied to all subcommands):

| Flag | Purpose | Sinister equivalent |
|---|---|---|
| `-p/--provider <id>` | Pick provider (40+ accepted) | Doc only — `automations/agent-host-routing.md` |
| `-C/--cwd <dir>` | Working directory | session-templates honor this |
| `--no-update` | Skip update check | n/a |
| `--auto-update` | Auto-update on new version | n/a |
| `--trace` | Tool I/O + token usage to stderr | 📋 NOT YET |
| `--quiet` | Suppress non-error output | 📋 NOT YET |
| `--resume <id>` | Resume session by id | ✅ CONTRACT 7 resume-points |
| `--fresh-spawn` | hidden — skip resume bootstrap | n/a |
| `--no-selfdev` | Disable self-dev detection | n/a |
| `--socket <path>` | Custom server socket | 📋 NOT YET (no daemon) |
| `--debug-socket` | Broadcast TUI state | 📋 NOT YET |
| `-m/--model <id>` | Pick model | Doc only |
| `--provider-profile <name>` | Named profile from config.toml | 📋 NOT YET |

**Count:** 42 subcommands + 13 global flags. Roughly **6 already shipped**, **31 not-yet**, **5 partially** in our stack.

---

## 3. Every jcode tool / feature module

### 3a. Built-in TUI tools registered in `Registry::base_tools` (`src/tool/mod.rs:109-210`)

These are the 30+ tools the model can call mid-turn.

| # | Tool name | Crate / file | Capability | Sinister status | Sinister tool dir + 3-line plan |
|---|---|---|---|---|---|
| 1 | `read` | `src/tool/read/` | Read file with adaptive truncation | 📋 planned | `tools/sinister-read/` — wrap Claude Code Read; add context-budget truncation; mirror jcode adaptive seen-snippet skip |
| 2 | `write` | `src/tool/write.rs` | Write file (creates) | 📋 planned | n/a — Claude Code Write is sufficient |
| 3 | `edit` | `src/tool/edit.rs` | Single string replacement | 📋 planned | n/a — Claude Code Edit is sufficient |
| 4 | `multiedit` | `src/tool/multiedit.rs` | Multiple edits in one call | 📋 planned | `tools/sinister-multiedit/` — Python wrapper that batches Edit calls per file |
| 5 | `patch` | `src/tool/patch.rs` | Apply unified diff | 📋 planned | `tools/sinister-patch/` — Python diff applier; use `unidiff` lib |
| 6 | `apply_patch` | `src/tool/apply_patch.rs` | Apply prepared patch from agent | 📋 planned | merge with `sinister-patch` |
| 7 | `glob` | `src/tool/glob.rs` | Pattern file search | n/a | Claude Code Glob is sufficient |
| 8 | `grep` | `src/tool/grep.rs` | Regex content search | n/a | Claude Code Grep is sufficient |
| 9 | `ls` | `src/tool/ls.rs` | Directory listing | n/a | Bash `ls` is sufficient |
| 10 | `bash` | `src/tool/bash.rs` | Shell exec with adaptive timeout | n/a | Claude Code Bash sufficient |
| 11 | `agentgrep` | `src/tool/agentgrep/` + ext crate `agentgrep v0.1.2` | Semantic grep with file-structure annotations, adaptive truncation | 📋 planned (matrix row 25) | `tools/sinister-agentgrep/` — operator-gated cargo install of agentgrep, add Python wrapper for Forge `:grep` cmd |
| 12 | `browser` | `src/tool/browser.rs` | Firefox Agent Bridge actions (15 actions: status, setup, open, snapshot, get_content, interactables, click, type, fill_form, select, wait, screenshot, eval, scroll, upload, press) | 🚧 doc only (matrix row 26) | `tools/sinister-browser/` — Python wrapper over Playwright OR ship `agent-browser-bridge-pattern.md` as the spec; defer implementation |
| 13 | `open` | `src/tool/open.rs` | Open URL / file in OS handler | n/a | `start` (Windows) / `open` (mac) — Bash |
| 14 | `webfetch` | `src/tool/webfetch.rs` | Fetch URL + render to markdown | n/a | Claude Code WebFetch sufficient |
| 15 | `websearch` | `src/tool/websearch.rs` | Web search (multiple engines incl. Bing/DDG) | n/a | Claude Code WebSearch sufficient |
| 16 | `codesearch` | `src/tool/codesearch.rs` | Symbol-aware code search | 📋 planned | `tools/sinister-codesearch/` — wrap `ctags` + `tree-sitter` (Python); intersect with grep |
| 17 | `invalid` | `src/tool/invalid.rs` | Sentinel: agent called a bad tool name | n/a | not user-facing |
| 18 | `lsp` | `src/tool/lsp.rs` | Language server (definitions, hover, refs) | 📋 planned | `tools/sinister-lsp/` — `pylsp` + `rust-analyzer` shim; Forge `:lsp` cmd |
| 19 | `todo` | `src/tool/todo.rs` | Session todo list with poke | 📋 planned (we have ClaudeCode TodoWrite) | merge into `sinister-cli` as `sinister todos` |
| 20 | `bg` | `src/tool/bg.rs` | Background process tracker | 📋 planned | `tools/sinister-bg/` — Python wrapper over `subprocess.Popen` + pidfile |
| 21 | `swarm` (internal name `communicate`) | `src/tool/communicate/` | DM / broadcast / spawn agents | ✅ shipped this session | `tools/sinister-swarm/` v0.1.0 — already shipped (DM/broadcast/spawn/watch/status) |
| 22 | `session_search` | `src/tool/session_search.rs` | Search across prior sessions (RAG) | 📋 planned | `tools/sinister-session-search/` — grep across `_shared-memory/cross-agent/` + `PROGRESS/` |
| 23 | `memory` | `src/tool/memory.rs` | Active recall + store API for the agent | 🚧 shipped via `forge-memory-bridge` | done (matrix row 9-10) |
| 24 | `goal` | `src/tool/goal.rs` | Goal tracking | 📋 planned | merge with `sinister-cli todos` |
| 25 | `gmail` | `src/tool/gmail.rs` | Send/read mail (post-google-OAuth) | 📋 planned | `tools/sinister-gmail/` — Python `google-auth-oauthlib` |
| 26 | `schedule` (ambient) | `src/tool/ambient/` | Schedule next ambient wake | 📋 planned | merge with `memory-consolidate.ps1` |
| 27 | `selfdev` | `src/tool/selfdev/` | Self-mod tool (build/test/reload) | 📋 NOT-PLANNED (operator-gated; risky for our fleet) | n/a — sanctum-master only |
| 28 | `subagent` (task) | `src/tool/task.rs` | Spawn subagent + receive completion report | 📋 planned (we have `claims_` MCP) | `tools/sinister-subagent/` — wrap Ruflo `agent_spawn` + claims |
| 29 | `batch` | `src/tool/batch.rs` | Run multiple tool calls in parallel | n/a | Claude Code parallel tool calls already work |
| 30 | `conversation_search` | `src/tool/conversation_search.rs` | Search within current conversation | 📋 planned | `tools/sinister-conv-search/` — grep current session transcript |
| 31 | `side_panel` | `src/tool/side_panel.rs` | Write to side panel (diff/file/diagram) | 📋 planned (Forge PH7 RKOJ tab) | Forge PH7 owns; add `:side-panel <file>` cmd |
| 32 | `skill_manage` | `src/tool/skill.rs` + `src/skill.rs` | List/activate skills | 📋 planned (Forge PH12 `Skill_Seekers`) | Forge PH12 owns |
| 33 | `mcp` | `src/tool/mcp.rs` | MCP management (list/connect/disconnect) | ✅ partial — we use `~/.claude/.mcp.json` directly | `sinister-cli mcp <action>` adapter |
| 34 | `end_ambient_cycle` (ambient-only) | `src/tool/ambient/` | Mark ambient cycle done | 📋 planned | merge with `memory-consolidate.ps1` |
| 35 | `request_permission` (ambient-only) | `src/tool/ambient/` | Ask user for unsupervised-action approval | 📋 planned | `tools/sinister-safety/` — Python wrapper that posts to `OPERATOR-ACTION-QUEUE.md` |
| 36 | `send_message` (ambient-only) | `src/tool/ambient/` | DM channel from ambient cycle | ✅ shipped — `sinister-swarm dm` covers it | n/a |
| 37 | `debug_socket` (selfdev-only) | `src/tool/debug_socket.rs` | Direct debug-socket access | 📋 NOT-PLANNED (selfdev-only) | n/a |

### 3b. Workspace crates (`crates/`, 48 total)

| Crate | Purpose | Sinister equivalent status |
|---|---|---|
| `jcode-agent-runtime` | Turn execution / streaming | 📋 planned (Forge PH6 owns) |
| `jcode-ambient-types` | Ambient mode types | 📋 planned |
| `jcode-auth-types` | OAuth/key types | n/a (we use Claude Code auth) |
| `jcode-azure-auth` | Azure OpenAI specifics | 📋 NOT-PLANNED-YET |
| `jcode-background-types` | Background process types | 📋 planned |
| `jcode-batch-types` | Batch tool types | n/a |
| `jcode-build-support` | Cargo helpers | n/a (Python stack) |
| `jcode-compaction-core` | Context compaction | 📋 planned (`automations/context-pruner.ps1` partial) |
| `jcode-config-types` | Config schema | 📋 planned — see Section 4 |
| `jcode-core` | Core utilities | n/a |
| `jcode-desktop` | Desktop superapp (iced-based) | 📋 NOT-PLANNED — RKOJ workbench owns |
| `jcode-embedding` | Local ONNX embeddings | 🔄 delegated to Ruflo `embeddings_*` |
| `jcode-gateway-types` | HTTP gateway (REST/SSE bridge) | ✅ partial — `forge-bridge` SSE pattern |
| `jcode-import-core` | Import sessions from codex/claude/opencode/pi | 📋 planned |
| `jcode-memory-types` | Memory graph types | 🔄 delegated to Ruflo |
| `jcode-message-types` | Message protocol types | n/a |
| `jcode-mobile-core` | iOS/mobile shared | 📋 NOT-PLANNED — Sanctum Mind owns mobile |
| `jcode-mobile-sim` | iOS simulator workflow | n/a |
| `jcode-notify-email` | Email notify | 📋 planned (Email-Composer skill candidate) |
| `jcode-overnight-core` | `/overnight` coordinator | 📋 planned |
| `jcode-pdf` | PDF parsing | 📋 NOT-PLANNED-YET |
| `jcode-plan` | Swarm plan storage | ✅ partial — `_shared-memory/plans/` is our convention |
| `jcode-protocol` | Server/client protocol | 📋 planned (`forge-bridge` partial) |
| `jcode-provider-core/openai/openrouter/gemini` | Per-provider | 📋 NOT-PLANNED (Claude Code routes) |
| `jcode-provider-metadata` | Provider catalog | ✅ doc — `automations/agent-host-routing.md` |
| `jcode-selfdev-types` | Self-dev session types | 📋 NOT-PLANNED |
| `jcode-session-types` | Session model | ✅ partial — resume-points |
| `jcode-side-panel-types` | Side panel state | 📋 planned (Forge PH7) |
| `jcode-storage` | Disk layout (`~/.jcode/`) | ✅ partial — `_shared-memory/` |
| `jcode-swarm-core` | Swarm primitives | ✅ shipped — `sinister-swarm` |
| `jcode-task-types` | Subagent task types | ✅ partial — `claims_*` MCP |
| `jcode-terminal-launch` | Spawn new terminal windows | ✅ partial — `start-sinister-session.ps1` |
| `jcode-tool-core/tool-types` | Tool trait | 📋 planned (Forge tool registry) |
| `jcode-tui-account-picker` | Account switcher | 📋 NOT-PLANNED (we don't multi-account) |
| `jcode-tui-core` | TUI primitives | ✅ partial — Forge Textual + Term prompt_toolkit |
| `jcode-tui-markdown` | Markdown render | ✅ partial — Forge uses rich.markdown |
| `jcode-tui-mermaid` | Inline mermaid render | 🚧 partial — `memory-graph-render/` + planned fork of `mermaid-rs-renderer` |
| `jcode-tui-messages` | Message rendering | ✅ partial — Forge log widget |
| `jcode-tui-render` | Render utilities | n/a |
| `jcode-tui-session-picker` | Session picker | 📋 planned (Forge Ctrl+W picker is the picker) |
| `jcode-tui-style` | Theme | ✅ partial — Forge `theme.py` |
| `jcode-tui-tool-display` | Tool call rendering | ✅ partial — Forge |
| `jcode-tui-usage-overlay` | Token usage HUD | 📋 planned |
| `jcode-tui-workspace` | `/workspace` niri-style switcher | 📋 planned (matrix row 27 — scrollable-tiling pattern) |
| `jcode-update-core` | Auto-update | 📋 planned (`verify-auto-push.ps1`) |
| `jcode-usage-types` | Token/cost types | 📋 NOT-PLANNED-YET — see Section 8 |

---

## 4. Every jcode option / setting / config flag

### 4a. Config file location

| Platform | Path |
|---|---|
| Linux/macOS | `~/.jcode/config.toml` (overridable via `$JCODE_HOME`) |
| Windows | `%USERPROFILE%\.jcode\config.toml` or `%LOCALAPPDATA%\jcode\` |
| Per-project | `.jcode/mcp.json` (and `.claude/mcp.json` compat fallback) |

Format: **TOML**, parsed by `crates/jcode-config-types`. Sections:

```toml
[provider]
default_provider = "..."
default_model = "..."

[providers.<name>]   # Multiple OpenAI-compatible profiles
type = "openai-compatible"
base_url = "..."
api_key_env = "..."
env_file = "..."
default_model = "..."

[[providers.<name>.models]]
id = "..."
context_window = 128000

[ambient]            # AmbientConfig (visible, model, provider, min/max interval, proactive)
[autoreview]         # AutoReviewConfig (enabled, model)
[autojudge]          # AutoJudgeConfig (enabled, model)
[compaction]         # CompactionConfig (mode, threshold_tokens)
[display]            # DisplayConfig (centered, diff_mode, markdown_spacing, message_timestamps, show_diffs, show_thinking, diagram_position, native_scrollbar)
[features]           # FeatureConfig (memory enabled, swarm enabled, performance buckets)
[gateway]            # GatewayConfig (enabled, bind_addr, port)
[keybindings]        # KeybindingsConfig (~30 keybind names — see 4c)
[safety]             # SafetyConfig (auto-allowed actions, notify channels)
[update]             # UpdateChannel
[websearch]          # WebSearchConfig (engine, fallback_engines)
[agents]             # AgentsConfig (per-role model assignment)
[auth]               # AuthConfig (trusted_external_auth_sources)
```

### 4b. Environment variables (~90 total — full list from `src/config.rs:27-119`)

Grouped by family:

**Ambient mode:** `JCODE_AMBIENT_ENABLED`, `_MAX_INTERVAL`, `_MIN_INTERVAL`, `_MODEL`, `_PROACTIVE`, `_PROVIDER`, `_VISIBLE`

**Auto-review / Auto-judge:** `JCODE_AUTOJUDGE_ENABLED`, `_MODEL`, `JCODE_AUTOREVIEW_ENABLED`, `_MODEL`

**Provider/model:** `JCODE_PROVIDER`, `JCODE_MODEL`, `JCODE_OPENAI_NATIVE_COMPACTION_MODE`, `_THRESHOLD_TOKENS`, `JCODE_OPENAI_REASONING_EFFORT`, `_SERVICE_TIER`, `_TRANSPORT`, `JCODE_COPILOT_PREMIUM`, `JCODE_CROSS_PROVIDER_FAILOVER`, `JCODE_SAME_PROVIDER_ACCOUNT_FAILOVER`

**Display:** `JCODE_DISPLAY_CENTERED`, `JCODE_CENTERED_TOGGLE_KEY`, `JCODE_DIFF_LINE_WRAP`, `JCODE_DIFF_MODE`, `JCODE_MARKDOWN_SPACING`, `JCODE_MESSAGE_TIMESTAMPS`, `JCODE_PIN_IMAGES`, `JCODE_SHOW_DIFFS`, `JCODE_SHOW_THINKING`, `JCODE_PROMPT_ENTRY_ANIMATION`, `JCODE_ANIMATION_FPS`, `JCODE_DISABLED_ANIMATIONS`, `JCODE_IDLE_ANIMATION`, `JCODE_REDRAW_FPS`, `JCODE_PERFORMANCE`

**Scroll keybinds:** `JCODE_SCROLL_UP_KEY`, `_DOWN_KEY`, `_UP_FALLBACK_KEY`, `_DOWN_FALLBACK_KEY`, `_PAGE_UP_KEY`, `_PAGE_DOWN_KEY`, `_PROMPT_UP_KEY`, `_PROMPT_DOWN_KEY`, `_BOOKMARK_KEY`

**Workspace keybinds:** `JCODE_WORKSPACE_LEFT_KEY`, `_RIGHT_KEY`, `_UP_KEY`, `_DOWN_KEY`

**Other keybinds:** `JCODE_MODEL_SWITCH_KEY`, `_PREV_KEY`, `JCODE_EFFORT_INCREASE_KEY`, `_DECREASE_KEY`, `JCODE_DICTATION_KEY`, `JCODE_MOUSE_CAPTURE`

**Memory + swarm:** `JCODE_MEMORY_ENABLED`, `JCODE_SWARM_ENABLED`

**Dictation:** `JCODE_DICTATION_COMMAND`, `_MODE`, `_TIMEOUT_SECS`

**Search:** `JCODE_WEBSEARCH_ENGINE`, `_FALLBACK_ENGINES`, `JCODE_BING_API_KEY`, `_ENV`, `_MARKET`

**Notify channels:** `JCODE_DISCORD_BOT_TOKEN`, `_USER_ID`, `_CHANNEL_ID`, `_REPLY_ENABLED`, `JCODE_TELEGRAM_BOT_TOKEN`, `_CHAT_ID`, `_REPLY_ENABLED`, `JCODE_EMAIL_REPLY_ENABLED`, `JCODE_EMAIL_TO`, `JCODE_IMAP_HOST`, `JCODE_SMTP_PASSWORD`, `JCODE_NTFY_SERVER`, `_TOPIC`

**Gateway / debug:** `JCODE_GATEWAY_BIND_ADDR`, `_ENABLED`, `_PORT`, `JCODE_DEBUG_SOCKET`, `JCODE_QUEUE_MODE`, `JCODE_AUTO_SERVER_RELOAD`

**Storage:** `JCODE_HOME`, `XDG_CONFIG_HOME`, `HOME`, `JCODE_TRUSTED_EXTERNAL_AUTH_SOURCES`, `JCODE_UPDATE_CHANNEL`, `JCODE_CHAT_NATIVE_SCROLLBAR`, `JCODE_SIDE_PANEL_NATIVE_SCROLLBAR`

### 4c. Per-provider settings

Each `[providers.<name>]` section supports: `type` (openai-compatible | etc.), `base_url`, `api_key_env`, `env_file`, `default_model`, plus `[[providers.<name>.models]]` (id + context_window). Auth styles: `bearer`, `api-key` (custom header), `none`. Provider routing flag for OpenRouter-style gateways.

### 4d. Sinister equivalent setting locations

| jcode | Sinister |
|---|---|
| `~/.jcode/config.toml` | `D:\Sinister Sanctum\automations\session-templates\agent-prefs.json` + `projects.json` + `panel-config.json` |
| `JCODE_*` env vars | `automations/agent-host-routing.md` (provider) + `docs/ENV-VARIABLES.md` |
| `~/.jcode/auth.json` | `D:\sinister-vault\` (vault daemon :5078) + `~/.claude/.credentials.json` |
| MCP `~/.jcode/mcp.json` | `~/.claude/.mcp.json` (operator-owned, NEVER edit per CLAUDE.md hard-canonical) |
| `.jcode/skills/` | `_shared-memory/skills/` (planned) + Forge `forge/plugins/` |

**Gap:** we have NO equivalent of jcode's TOML config schema for things like keybinds, theme overrides, ambient interval, etc. Each Sinister tool's settings live in its own JSON or PS1 — fragmented. **P1 candidate:** unify into `automations/session-templates/sinister.toml`.

---

## 5. jcode plugins / hooks / extensions

### 5a. Plugin system architecture

jcode does **NOT** ship a generic plugin system the way Claude Code does. It instead has:

1. **Skills** — markdown files at `~/.claude/skills/<name>/SKILL.md` (compatibility) and `~/.jcode/skills/`. Each `SKILL.md` has frontmatter (`name`, `description`, `allowed-tools`) and a body. Loaded via `src/skill.rs` `SkillRegistry`. Hot-reload requested in `PLAN_MCP_SKILLS.md` (Phase 1) but not confirmed shipped.
2. **MCP servers** — external processes that register tools dynamically at runtime via `src/mcp/`. See Section 6.
3. **Custom OpenAI-compatible providers** — via `jcode provider add` (writes a `[providers.<name>]` block). Not really a "plugin" but it's runtime-extensible.

### 5b. Hook points

jcode does **NOT** have a Claude-Code-style settings.json hook system (pre-tool, post-tool, on-error, etc.). What it has instead:

| Mechanism | Where | What it does |
|---|---|---|
| **Tool wrappers** | `src/agent/tools.rs` | Adaptive truncation, context-overflow guard, safety classification |
| **Bus events** | `src/bus.rs` | Internal pub/sub for `ToolEvent`, `GitStatusCompleted`, `ManualToolCompleted` — internal only, not user-extensible |
| **Safety classifier** | `src/safety.rs` | Maps tool calls to auto-allowed vs. requires-permission tiers (matrix in `docs/SAFETY_SYSTEM.md`) — only consumer today is ambient mode |
| **Auto-review / auto-judge** | `src/tui/app/commands_review.rs` | End-of-turn second-pass review by another model; toggle with `/autoreview` `/autojudge`; pseudo-post-tool-hook |
| **Auto-poke** | `src/tui/app/commands.rs:34-200` | Triggers when incomplete todos detected; pseudo-event |
| **Ambient triggers** | `src/ambient_scheduler.rs` | Event triggers (session close, crash, git push) + timer; runs cycles |

**Sinister equivalent status:** We have `claude-hooks-2.4.0` planned for Forge PH13 — which is the *Claude Code* hook system (pre/post tool), not the jcode review-pass pattern. **Both are valuable.** The jcode pattern (auto-review with a stronger model) maps better to "judge the previous turn before letting the agent continue" — we should explicitly plan this as **P2** in our `agent-host-routing.md` (route review-passes to `gpt-5.5` per jcode `REVIEW_PREFERRED_MODEL` constant).

### 5c. Sinister hook gaps

| jcode mechanism | Sinister equivalent | Status |
|---|---|---|
| Tool wrappers (truncate, guard) | Forge tool-call wrapping (PH13) | 📋 planned |
| Bus events | Forge internal event bus | 📋 planned |
| Safety classifier | `OPERATOR-ACTION-QUEUE.md` (manual approval) | ✅ partial (manual) |
| Auto-review / auto-judge | NEW — propose `tools/sinister-review/` | 📋 NOT-PLANNED-YET |
| Auto-poke | `automations/agent-poke.ps1` | 📋 NOT-PLANNED-YET |
| Ambient triggers | `automations/memory-consolidate.ps1` (timer-only) | 🚧 partial |
| Claude-Code-style hooks (pre/post tool) | Forge PH13 `claude-hooks` integration | 📋 planned |

---

## 6. jcode MCP integrations

### 6a. MCP servers jcode ships WITH

jcode itself ships **NO bundled MCP servers**. The default `.claude/mcp.json` at the repo root is `{"servers":{}}`. The bundled MCP support is purely **client-side** — jcode IS an MCP client that connects to user-configured servers.

### 6b. MCP servers jcode integrates as a client of

Per `src/mcp/` and `PLAN_MCP_SKILLS.md`:

- jcode reads MCP server config from (in order):
  1. `~/.jcode/mcp.json` (global, primary)
  2. `.jcode/mcp.json` (per-project)
  3. `.claude/mcp.json` (Claude Code compat fallback)
  4. On first run if `~/.jcode/mcp.json` doesn't exist, jcode tries to import from `~/.claude/mcp.json` and `~/.codex/config.toml`

- Config schema (mirrors Claude Code's `.mcp.json`):
  ```json
  {
    "servers": {
      "<name>": {
        "command": "...",
        "args": ["..."],
        "env": {},
        "shared": true
      }
    }
  }
  ```

- jcode supports stdio-only MCP today (per `src/mcp/client.rs` + `protocol.rs`). HTTP/SSE transports not confirmed in v0.12.3.
- Tools from MCP servers are registered with prefix `mcp__<server>__<tool>` (matches Claude Code convention; per `src/tool/mod.rs:544-550`).
- The `mcp` built-in tool (`src/tool/mcp.rs`) lets the agent call `mcp_list`, `mcp_connect`, `mcp_disconnect`, `mcp_reload` to manage servers at runtime.

### 6c. Sinister MCP equivalents

| jcode | Sinister | Status |
|---|---|---|
| `~/.jcode/mcp.json` global | `~/.claude/.mcp.json` (operator-owned per CLAUDE.md) | ✅ shipped (Ruflo + Vault loaded) |
| Per-project `.jcode/mcp.json` | per-project `.mcp.json` (operator can add) | ✅ pattern supported |
| `mcp__<server>__<tool>` prefix | same — Ruflo tools are `mcp__ruflo__*`, Vault tools `mcp__vault__*` | ✅ identical |
| `mcp` tool (list/connect/disconnect at runtime) | NEW — propose `tools/sinister-mcp/` Python wrapper | 📋 NOT-PLANNED-YET |
| stdio-only transport | Claude Code MCP supports stdio + sse + http | ✅ superset |
| Auto-import from `~/.claude/mcp.json` and `~/.codex/config.toml` | n/a — Claude Code MCP is our primary | n/a |

**Gap:** we have NO Sinister-branded MCP wrapper tool. The Forge agent currently has no way to call `mcp_connect` mid-session (operator must edit `~/.claude/.mcp.json` + restart). **P2 candidate:** `tools/sinister-mcp/` that wraps Claude Code's MCP add/list. Note: lane discipline says `~/.claude/.mcp.json` is operator-only — sinister-mcp should be **read-only** by default, with `--write` requiring operator approval queued to `OPERATOR-ACTION-QUEUE.md`.

---

## 7. jcode UI / TUI / animation features

### 7a. Boot art / spinner / progress

- **Animated boot art:** Per matrix row 5, jcode has rotating frames (1.2s window). Implementation in `src/tui/ui_animations.rs`. `JCODE_PROMPT_ENTRY_ANIMATION` + `JCODE_IDLE_ANIMATION` env vars.
- **Frame rate:** Configurable via `JCODE_ANIMATION_FPS` / `JCODE_REDRAW_FPS`. Default targets >1000fps internal (README claim).
- **Time-to-first-frame:** 14ms (jcode README benchmark).
- Sinister equivalent: Forge `art.py` (PH5) — Vault Boy rotating frames — 📋 planned.

### 7b. Status pills / breadcrumbs / typography

- **Status pill:** Top-right shows model + provider + cache state + token budget. Source: `src/tui/ui_status.rs`.
- **Breadcrumbs:** cwd / git branch / session display name in status line.
- **Typography:** Cascadia-style monospace expected by docs; per `crates/jcode-tui-style/`. Theme is dark with purple accents.
- **Mermaid inline:** `src/tui/mermaid.rs` + `crates/jcode-tui-mermaid` — renders diagrams in chat OR side panel via the `mermaid-rs-renderer` fork (claimed 1800x faster than node-based).
- **Markdown:** `src/tui/markdown.rs` + `crates/jcode-tui-markdown`. Supports `JCODE_MARKDOWN_SPACING` mode.
- **Info widgets:** `src/tui/info_widget*.rs` (12 files: git, graph, layout, memory_render, model, overview, swarm_background, tips, todos, usage). Negative-space rendering — only shown when there's room.
- **Diff display:** `src/tui/ui_diff.rs` + `_file_diff.rs`. Modes: `inline`, `unified`, `split`. Configurable via `JCODE_DIFF_MODE`.

Sinister equivalent: Forge `theme.py` (PH11), status_bar pane (PH7+), and Term shell PH7 status line — **lane:** forge + sinister-term — ✅ partial scaffold, 📋 polish.

### 7c. Keybindings

From `src/tui/keybind.rs` + `KeybindingsConfig` defaults:

| Action | Default | Env var |
|---|---|---|
| Scroll up | `Ctrl+K` (vim) | `JCODE_SCROLL_UP_KEY` |
| Scroll down | `Ctrl+J` | `JCODE_SCROLL_DOWN_KEY` |
| Page up | `Alt+U` | `JCODE_SCROLL_PAGE_UP_KEY` |
| Page down | `Alt+D` | `JCODE_SCROLL_PAGE_DOWN_KEY` |
| Bookmark scroll | `Ctrl+G` | `JCODE_SCROLL_BOOKMARK_KEY` |
| Scroll up fallback | `Ctrl+[` | `_UP_FALLBACK_KEY` |
| Scroll down fallback | `Ctrl+]` | `_DOWN_FALLBACK_KEY` |
| Prompt scroll up | (configurable) | `_PROMPT_UP_KEY` |
| Prompt scroll down | (configurable) | `_PROMPT_DOWN_KEY` |
| Model switch next | `Ctrl+Tab` | `JCODE_MODEL_SWITCH_KEY` |
| Model switch prev | `Ctrl+Shift+Tab` | `_PREV_KEY` |
| Effort up | (configurable) | `_EFFORT_INCREASE_KEY` |
| Effort down | (configurable) | `_EFFORT_DECREASE_KEY` |
| Centered toggle | `Alt+C` | `JCODE_CENTERED_TOGGLE_KEY` |
| Workspace left/right/up/down | hjkl-style | `JCODE_WORKSPACE_*_KEY` |
| Dictation | (configurable) | `JCODE_DICTATION_KEY` |
| Mouse capture | `Alt+M` (toggle) | `JCODE_MOUSE_CAPTURE` |
| Word-back (input) | `Ctrl+W` / `Alt+B` | hardcoded |
| Word-forward (input) | `Alt+F` / `Alt+D` | hardcoded |

Plus the slash-command set listed in Section 7d.

Sinister equivalent: Forge `app.py` Textual Bindings + Term `prompt_toolkit` keybindings — ✅ partial (Forge Ctrl+W picker exists; PH3 will add more).

### 7d. Slash commands (TUI-only — separate from CLI subcommands)

From `src/tui/app/state_ui_input_helpers.rs:41-122`. **62 registered commands** + 4 hidden secret commands.

**Public slash commands (lifted verbatim):**

`/help`, `/?`, `/commands`, `/model`, `/models`, `/refresh-model-list`, `/agents`, `/subagent`, `/observe`, `/todos`, `/splitview`, `/split-view`, `/btw`, `/ssh`, `/git`, `/transcript`, `/subagent-model`, `/autoreview`, `/autojudge`, `/review`, `/judge`, `/effort`, `/fast`, `/transport`, `/alignment`, `/clear`, `/rewind`, `/poke`, `/improve`, `/refactor`, `/compact`, `/fix`, `/dictate`, `/dictation`, `/memory`, `/goals`, `/swarm`, `/overnight`, `/context`, `/version`, `/changelog`, `/info`, `/usage`, `/feedback`, `/subscription`, `/config`, `/reload`, `/restart`, `/rebuild`, `/selfdev`, `/update`, `/resume`, `/sessions`, `/catchup`, `/back`, `/save`, `/unsave`, `/rename`, `/split`, `/transfer`, `/workspace`, `/quit`, `/auth`, `/login`, `/account`, `/accounts`, `/cache`, `/debug-visual`, `/screenshot-mode`, `/screenshot`, `/record`

**Remote-only:** `/client-reload`, `/server-reload`

**Hidden:** `/z`, `/zz`, `/zzz`, `/zstatus` (premium-mode jokes per source comments)

**Sinister equivalent status:** 📋 **ALMOST ALL NOT YET**. Forge has none of these. Term has `/jcode-memory-write` + `/mw` alias only. **This is the single biggest gap.** Top 10 most-valuable for the fleet (P0):

| Slash | Why valuable |
|---|---|
| `/help` | Discoverability |
| `/model` | Provider/model switching mid-session |
| `/clear` | Start fresh without restarting |
| `/resume` + `/sessions` + `/save` + `/rename` | Session bookmark + recall (Sanctum has resume-points; not exposed as TUI cmds) |
| `/memory` + `/memory <op>` | Toggle + inspect memory bridge |
| `/swarm` + `/swarm <op>` | Wraps `sinister-swarm` |
| `/compact` + `/transfer` | Context compaction handoff |
| `/observe` + `/todos` | Side-panel inspectors |
| `/config` | Quick config edit |
| `/usage` | Token / cost view |

### 7e. Theme system

`crates/jcode-tui-style` defines a theme struct. Color overrides via config — we don't see a full theme file format in v0.12.3, but `JCODE_DISABLED_ANIMATIONS`, `JCODE_PERFORMANCE` (low/medium/high), and `JCODE_NATIVE_SCROLLBAR` toggles affect rendering.

Sinister equivalent: Forge `theme.py` — purple `#7A3DD4` + dim cyan + Cascadia. ✅ partial. **No runtime theme switching yet** — should be P3.

### 7f. Niri workspace integration

Per matrix row 27 + README + assets/niri-screenshot.png + crate `jcode-tui-workspace`. jcode adopts niri-wm's column-scroll UX — `/workspace` slash command lets users page horizontally between sessions. Source: `src/tui/app/workspace_client.rs` + remote.rs.

Sinister equivalent: 📋 planned — Forge `panes/*` PH2-PH3 + `_shared-memory/knowledge/scrollable-tiling-pattern.md` (TODO). **P1 candidate:** ship the scrollable-tiling brain doc this session if not already done.

---

## 8. jcode telemetry / cost / accounting

### 8a. Telemetry (opt-in, Cloudflare Worker backend)

Per `TELEMETRY.md` + `telemetry-worker/` directory. Schema v5 (current). Events:

- **install** — UUID + version + OS + arch (once per machine)
- **upgrade** — version + from_version
- **auth_success** — coarse provider + method
- **onboarding_step** — funnel buckets (e.g. `first_prompt_sent`) + `milestone_elapsed_ms`
- **feedback** — `/feedback` freeform text + rating (legacy)
- **session_start / session_end** — outcome, duration, tool category counts
- **autonomy / pain-attribution** — schema-v5 per-turn timing + outcome + pain markers
- **multi-sessioning** — concurrent session counts + workflow cadence

Backend: `telemetry-worker/` is a Cloudflare Worker (Node + wrangler) with SQL migrations (`schema.sql`, `health.sql`).

**Critical line from README:** *"This data helps prioritize development without collecting prompts or code."*

**Sinister equivalent:** ✅ **PORTED-AS-OMISSION** (matrix row 17). Per CLAUDE.md hard-canonical (data sovereignty), we do NOT phone home. Local logs only.

### 8b. Cost tracking per session / per provider

jcode tracks:
- **Token usage** per turn + cumulative session (input/output/cache) — `src/usage.rs`
- **Cost** in dollars (per-provider pricing tables in `src/provider/pricing.rs`) — `crates/jcode-usage-types`
- **Cache state** — warns when Anthropic's 5-minute cache goes cold (README)
- **Display** — `src/tui/usage_overlay.rs` + `info_widget_usage.rs` (negative-space HUD)
- **CLI:** `jcode usage [--json]` returns provider limits
- **Subscription state:** `/subscription` slash command, `src/subscription_catalog.rs`

### 8c. Sinister equivalents

| jcode | Sinister | Status |
|---|---|---|
| Token accounting | n/a — Claude Code shows per-turn but no fleet-wide aggregation | 📋 NOT-PLANNED-YET |
| Cost in dollars | n/a | 📋 NOT-PLANNED-YET |
| Cache warning | n/a | 📋 NOT-PLANNED-YET |
| Usage HUD | n/a | 📋 NOT-PLANNED-YET |
| Subscription catalog | n/a (we use whatever Claude Code is wired to) | 📋 NOT-PLANNED-YET |

**Proposal:** `tools/sinister-usage/` — Python script that scans Claude Code's local session logs (`~/.claude/projects/<hash>/`) + aggregates tokens. Build difficulty 6, ROI 4 (we don't pay per token under Pro plan). **P3.**

---

## 9. The full master gap-list

Single sortable table. **One row per jcode feature/capability/subcommand/tool/slash-command.** Numbers continue across sections so each row is unique.

| # | jcode feature | Sinister status | Owner lane | Build difficulty (1-10) | ROI for fleet (1-10) | Priority tier |
|---|---|---|---|---|---|---|
| 1 | TUI launch (default) | partial (Forge scaffold) | forge | 7 | 9 | P0 |
| 2 | `serve` daemon | NOT-PLANNED-YET | NEW (sanctum) | 8 | 5 | P2 |
| 3 | `connect` client | NOT-PLANNED-YET | sanctum | 4 | 4 | P3 |
| 4 | `run` one-shot | NOT-PLANNED-YET | sanctum | 3 | 7 | P1 |
| 5 | `login --provider` | NOT-PLANNED (using Claude auth) | sanctum | n/a | 1 | P3 |
| 6 | `repl` mode | NOT-PLANNED-YET | sinister-term | 2 | 5 | P2 |
| 7 | `update` self-update | NOT-PLANNED-YET | sanctum | 3 | 4 | P3 |
| 8 | `version` info | shipped | sanctum | done | done | done |
| 9 | `usage` quota view | NOT-PLANNED-YET | sanctum | 5 | 4 | P3 |
| 10 | `selfdev` canary | NOT-PLANNED (operator-gated) | sanctum | 9 | 3 | P3 |
| 11 | `debug` socket CLI | partial (heartbeats) | sanctum | 5 | 6 | P1 |
| 12 | `auth status` | NOT-PLANNED-YET | sanctum | 2 | 3 | P3 |
| 13 | `auth doctor` | NOT-PLANNED-YET | sanctum | 4 | 3 | P3 |
| 14 | `provider list/current/add` | partial (doc) | sanctum | 4 | 5 | P2 |
| 15 | `memory list/search/export/import/stats` CLI | partial (bridge has list/recall) | sanctum | 4 | 8 | P0 |
| 16 | `session rename` | NOT-PLANNED-YET | sanctum | 3 | 5 | P2 |
| 17 | `ambient status/log/trigger/stop/run-visible` | partial (timer-only) | sanctum | 5 | 7 | P1 |
| 18 | `pair` for iOS/web | NOT-PLANNED-YET | mind | 7 | 6 | P2 |
| 19 | `permissions` review queue | partial (OPERATOR-ACTION-QUEUE.md is manual) | sanctum | 5 | 7 | P1 |
| 20 | `transcript` inject text | NOT-PLANNED-YET | forge | 3 | 6 | P2 |
| 21 | `dictate` STT trigger | NOT-PLANNED-YET | NEW | 6 | 5 | P3 |
| 22 | `setup-hotkey` global hotkey | NOT-PLANNED-YET | NEW | 5 | 6 | P2 |
| 23 | `setup-launcher` desktop entry | shipped (Start-Sinister-Session.bat) | sanctum | done | done | done |
| 24 | `browser` Firefox bridge | partial (doc only) | sanctum | 7 | 6 | P2 |
| 25 | `replay` session player + video export | NOT-PLANNED-YET | NEW | 9 | 4 | P3 |
| 26 | `model list` | NOT-PLANNED-YET | sanctum | 2 | 4 | P3 |
| 27 | `auth-test` end-to-end | NOT-PLANNED-YET | sanctum | 4 | 3 | P3 |
| 28 | `restart save/restore/status/clear` | partial (resume-points) | sanctum | 4 | 7 | P1 |
| 29 | Tool: `read` adaptive truncation | NOT-PLANNED (Claude Code has Read) | n/a | n/a | n/a | n/a |
| 30 | Tool: `write` | n/a | n/a | n/a | n/a | n/a |
| 31 | Tool: `edit` / `multiedit` / `patch` / `apply_patch` | NOT-PLANNED (Claude Code) | n/a | n/a | n/a | n/a |
| 32 | Tool: `glob` / `grep` / `ls` | n/a (Claude Code) | n/a | n/a | n/a | n/a |
| 33 | Tool: `bash` | n/a (Claude Code) | n/a | n/a | n/a | n/a |
| 34 | Tool: `agentgrep` (struct-aware grep with adaptive context) | planned | forge | 6 | 7 | P1 |
| 35 | Tool: `browser` (15 actions) | partial | sanctum | 7 | 6 | P2 |
| 36 | Tool: `open` / `webfetch` / `websearch` | n/a (Claude Code) | n/a | n/a | n/a | n/a |
| 37 | Tool: `codesearch` (symbol-aware) | NOT-PLANNED-YET | forge | 6 | 6 | P2 |
| 38 | Tool: `lsp` | NOT-PLANNED-YET | forge | 7 | 6 | P2 |
| 39 | Tool: `todo` session list | NOT-PLANNED-YET (we have TodoWrite) | forge | 3 | 5 | P2 |
| 40 | Tool: `bg` background process | NOT-PLANNED-YET | sanctum | 4 | 5 | P2 |
| 41 | Tool: `swarm` (communicate) | shipped (sinister-swarm) | sanctum | done | done | done |
| 42 | Tool: `session_search` RAG | NOT-PLANNED-YET | sanctum | 5 | 7 | P1 |
| 43 | Tool: `memory` active recall/store | shipped (forge-memory-bridge) | sanctum | done | done | done |
| 44 | Tool: `goal` tracker | NOT-PLANNED-YET | sanctum | 3 | 4 | P3 |
| 45 | Tool: `gmail` send/read | NOT-PLANNED-YET | NEW | 5 | 3 | P3 |
| 46 | Tool: `schedule` ambient wake | partial (consolidate.ps1) | sanctum | 4 | 6 | P2 |
| 47 | Tool: `selfdev` self-mod | NOT-PLANNED (lane risk) | n/a | n/a | n/a | n/a |
| 48 | Tool: `subagent` (task spawn) | partial (claims_*) | sanctum | 5 | 7 | P1 |
| 49 | Tool: `batch` parallel calls | n/a (Claude Code parallel tool-calls) | n/a | n/a | n/a | n/a |
| 50 | Tool: `conversation_search` | NOT-PLANNED-YET | forge | 3 | 5 | P2 |
| 51 | Tool: `side_panel` write | partial (Forge PH7 RKOJ tab) | forge | 5 | 7 | P1 |
| 52 | Tool: `skill_manage` | partial (planned PH12) | forge | 5 | 6 | P2 |
| 53 | Tool: `mcp` mgmt | partial (manual ~/.claude/.mcp.json edits) | sanctum | 5 | 5 | P2 |
| 54 | Ambient: `end_ambient_cycle` | NOT-PLANNED-YET | sanctum | 3 | 5 | P2 |
| 55 | Ambient: `request_permission` | partial (OPERATOR-ACTION-QUEUE.md) | sanctum | 4 | 6 | P2 |
| 56 | Ambient: `send_message` channel | shipped (sinister-swarm dm) | sanctum | done | done | done |
| 57 | Crate: `agent-runtime` turn streaming | NOT-PLANNED-YET (Forge will own) | forge | 7 | 7 | P1 |
| 58 | Crate: `compaction-core` | partial (context-pruner.ps1) | sanctum | 6 | 7 | P1 |
| 59 | Crate: `desktop` superapp | NOT-PLANNED (RKOJ workbench owns) | rkoj | n/a | n/a | n/a |
| 60 | Crate: `mobile-core` / `mobile-sim` | NOT-PLANNED (Mind owns mobile) | mind | n/a | n/a | n/a |
| 61 | Crate: `overnight-core` | NOT-PLANNED-YET | NEW | 6 | 4 | P3 |
| 62 | Crate: `tui-workspace` (niri-style) | NOT-PLANNED-YET | forge | 7 | 7 | P1 |
| 63 | Crate: `update-core` | partial (auto-push) | sanctum | 4 | 5 | P2 |
| 64 | Crate: `tui-mermaid` (Rust mermaid render) | partial (tools/memory-graph-render) | sanctum | 8 | 7 | P1 |
| 65 | Crate: `tui-style` theme | partial (Forge theme.py) | forge | 4 | 6 | P2 |
| 66 | Crate: `tui-usage-overlay` HUD | NOT-PLANNED-YET | forge | 4 | 4 | P3 |
| 67 | Crate: `import-core` (claude/codex/opencode/pi resume) | NOT-PLANNED-YET | sanctum | 6 | 5 | P2 |
| 68 | Crate: `notify-email` | NOT-PLANNED-YET | NEW | 4 | 4 | P3 |
| 69 | Crate: `safety` classifier | partial (OPERATOR-ACTION-QUEUE.md) | sanctum | 5 | 7 | P1 |
| 70 | Crate: `terminal-launch` (spawn windows) | shipped (start-sinister-session.ps1) | sanctum | done | done | done |
| 71 | Config: `~/.jcode/config.toml` unified | NOT-PLANNED-YET | sanctum | 4 | 6 | P1 |
| 72 | Config: 90+ env vars | partial (docs/ENV-VARIABLES.md) | sanctum | 3 | 5 | P2 |
| 73 | Config: keybindings.toml | NOT-PLANNED-YET | forge + sinister-term | 4 | 5 | P2 |
| 74 | Plugin: skills hot-reload | NOT-PLANNED-YET (Forge PH8) | forge | 5 | 6 | P2 |
| 75 | Plugin: MCP runtime mgmt | partial (manual edits) | sanctum | 5 | 5 | P2 |
| 76 | Hooks: tool-wrappers (truncate, guard) | NOT-PLANNED-YET | forge | 5 | 7 | P1 |
| 77 | Hooks: auto-review (`/autoreview`) | NOT-PLANNED-YET | NEW | 6 | 8 | P1 |
| 78 | Hooks: auto-judge (`/autojudge`) | NOT-PLANNED-YET | NEW | 6 | 6 | P2 |
| 79 | Hooks: auto-poke incomplete todos | NOT-PLANNED-YET | sanctum | 4 | 5 | P2 |
| 80 | Hooks: bus events (internal pub/sub) | NOT-PLANNED-YET | forge | 5 | 6 | P2 |
| 81 | Hooks: Claude-Code-style pre/post tool (separate from jcode pattern!) | partial (PH13 planned) | forge | 5 | 7 | P1 |
| 82 | UI: animated boot art | planned (Forge art.py PH5) | forge | 4 | 7 | P1 |
| 83 | UI: status pill (model/cache/tokens) | partial (Forge PH7 stub) | forge | 4 | 6 | P2 |
| 84 | UI: breadcrumbs (cwd/branch/session) | partial (Forge + Term) | forge + sinister-term | 3 | 6 | P2 |
| 85 | UI: Cascadia typography + purple theme | partial (Forge theme.py) | forge | 3 | 7 | P1 |
| 86 | UI: mermaid inline render | partial (memory-graph-render PNG flow) | sanctum + forge | 7 | 6 | P2 |
| 87 | UI: markdown rendering | partial (rich.markdown) | forge | 3 | 5 | P2 |
| 88 | UI: 12 info widgets (negative-space HUDs) | NOT-PLANNED-YET | forge | 6 | 6 | P2 |
| 89 | UI: diff display (inline/unified/split) | NOT-PLANNED-YET | forge | 5 | 5 | P2 |
| 90 | UI: niri-style workspace | NOT-PLANNED-YET | forge | 7 | 7 | P1 |
| 91 | UI: theme system (runtime switch) | NOT-PLANNED-YET | forge | 4 | 4 | P3 |
| 92 | UI: 1000+ fps render | n/a (Python perf ceiling lower) | forge | 8 | 3 | P3 |
| 93 | UI: scroll keybinds (Ctrl+K/J + Alt+U/D + Ctrl+[/] + Ctrl+G) | partial | forge + sinister-term | 3 | 6 | P1 |
| 94 | UI: model/effort/dictation keybinds | NOT-PLANNED-YET | forge + sinister-term | 3 | 5 | P2 |
| 95 | UI: word-back / word-forward (input) | partial (prompt_toolkit defaults) | sinister-term | 2 | 5 | P2 |
| 96 | Slash: `/help`, `/?`, `/commands` | NOT-PLANNED-YET | forge + sinister-term | 2 | 8 | P0 |
| 97 | Slash: `/model` + `/models` + `/refresh-model-list` | NOT-PLANNED-YET | forge | 4 | 7 | P1 |
| 98 | Slash: `/agents` + `/subagent` + `/subagent-model` | NOT-PLANNED-YET | sanctum + forge | 5 | 7 | P1 |
| 99 | Slash: `/observe` + `/todos` (side panel) | NOT-PLANNED-YET | forge | 4 | 6 | P2 |
| 100 | Slash: `/splitview` + `/split-view` | NOT-PLANNED-YET | forge | 5 | 5 | P2 |
| 101 | Slash: `/btw` (side question) | NOT-PLANNED-YET | forge | 4 | 6 | P2 |
| 102 | Slash: `/ssh` connect remote | NOT-PLANNED-YET | NEW | 6 | 5 | P2 |
| 103 | Slash: `/git` status | NOT-PLANNED-YET | sanctum (via bash) | 2 | 5 | P2 |
| 104 | Slash: `/transcript` (open file) | NOT-PLANNED-YET | forge | 3 | 5 | P2 |
| 105 | Slash: `/autoreview` + `/autojudge` toggles | NOT-PLANNED-YET | sanctum (judge skill) | 6 | 8 | P1 |
| 106 | Slash: `/review` + `/judge` one-shot | NOT-PLANNED-YET | sanctum | 5 | 7 | P1 |
| 107 | Slash: `/effort` (reasoning_effort) | NOT-PLANNED-YET | sanctum | 3 | 5 | P2 |
| 108 | Slash: `/fast` OpenAI fast mode | NOT-PLANNED-YET | sanctum | 2 | 4 | P3 |
| 109 | Slash: `/transport` (HTTP/SSE/WS) | NOT-PLANNED-YET | sanctum | 3 | 3 | P3 |
| 110 | Slash: `/alignment` (left/centered) | NOT-PLANNED-YET | forge | 3 | 4 | P3 |
| 111 | Slash: `/clear` | NOT-PLANNED-YET | forge + sinister-term | 1 | 8 | P0 |
| 112 | Slash: `/rewind` | NOT-PLANNED-YET | forge | 5 | 6 | P2 |
| 113 | Slash: `/poke` + `/poke on/off/status` | NOT-PLANNED-YET | sanctum | 4 | 5 | P2 |
| 114 | Slash: `/improve` repo loop | NOT-PLANNED-YET | sanctum | 7 | 6 | P2 |
| 115 | Slash: `/refactor` safe loop | NOT-PLANNED-YET | sanctum | 7 | 6 | P2 |
| 116 | Slash: `/compact` context compaction | NOT-PLANNED-YET | sanctum (context-pruner) | 5 | 7 | P1 |
| 117 | Slash: `/fix` recovery | NOT-PLANNED-YET | sanctum | 5 | 6 | P2 |
| 118 | Slash: `/dictate` + `/dictation` | NOT-PLANNED-YET | NEW | 5 | 4 | P3 |
| 119 | Slash: `/memory` toggle + `/memory <op>` | NOT-PLANNED-YET (we have CLI bridge) | forge + sinister-term | 3 | 7 | P1 |
| 120 | Slash: `/goals` | NOT-PLANNED-YET | sanctum | 3 | 4 | P3 |
| 121 | Slash: `/swarm` + `/swarm <op>` | NOT-PLANNED-YET (we have sinister-swarm CLI) | forge | 3 | 8 | P0 |
| 122 | Slash: `/overnight` coordinator | NOT-PLANNED-YET | NEW | 7 | 5 | P2 |
| 123 | Slash: `/context` snapshot | NOT-PLANNED-YET | sanctum | 3 | 6 | P1 |
| 124 | Slash: `/version` + `/changelog` + `/info` | NOT-PLANNED-YET | forge | 2 | 5 | P2 |
| 125 | Slash: `/usage` provider limits | NOT-PLANNED-YET | sanctum | 4 | 4 | P3 |
| 126 | Slash: `/feedback` (jcode-specific) | NOT-PLANNED (not relevant) | n/a | n/a | n/a | n/a |
| 127 | Slash: `/subscription` (jcode-specific) | NOT-PLANNED | n/a | n/a | n/a | n/a |
| 128 | Slash: `/config` view/edit | NOT-PLANNED-YET | sanctum | 4 | 7 | P1 |
| 129 | Slash: `/reload` + `/restart` + `/rebuild` | NOT-PLANNED-YET | sanctum | 4 | 5 | P2 |
| 130 | Slash: `/selfdev` (operator-gated) | NOT-PLANNED | n/a | n/a | n/a | n/a |
| 131 | Slash: `/update` | NOT-PLANNED-YET | sanctum | 3 | 4 | P3 |
| 132 | Slash: `/resume` + `/sessions` | NOT-PLANNED-YET (we have resume-points) | sanctum | 4 | 8 | P0 |
| 133 | Slash: `/catchup` + `/back` | NOT-PLANNED-YET | sanctum | 5 | 5 | P2 |
| 134 | Slash: `/save` + `/unsave` bookmark | NOT-PLANNED-YET | sanctum | 3 | 5 | P2 |
| 135 | Slash: `/rename` | NOT-PLANNED-YET | sanctum | 2 | 4 | P3 |
| 136 | Slash: `/split` (new window) | NOT-PLANNED-YET | sanctum | 4 | 5 | P2 |
| 137 | Slash: `/transfer` compact handoff | NOT-PLANNED-YET | sanctum | 6 | 7 | P1 |
| 138 | Slash: `/workspace` niri picker | NOT-PLANNED-YET | forge | 6 | 6 | P2 |
| 139 | Slash: `/quit` | NOT-PLANNED-YET | forge + sinister-term | 1 | 6 | P0 |
| 140 | Slash: `/auth` + `/login` + `/account` + `/accounts` | NOT-PLANNED (Claude Code auth) | sanctum | n/a | 1 | P3 |
| 141 | Slash: `/cache` (TTL) | NOT-PLANNED-YET | sanctum | 4 | 5 | P2 |
| 142 | Slash: `/debug-visual`, `/screenshot-mode`, `/screenshot`, `/record` | NOT-PLANNED-YET | NEW | 5 | 4 | P3 |
| 143 | MCP: stdio client | partial (Claude Code handles) | n/a | n/a | n/a | n/a |
| 144 | MCP: `~/.jcode/mcp.json` global | n/a (we use ~/.claude/.mcp.json) | n/a | n/a | n/a | n/a |
| 145 | MCP: per-project `.mcp.json` | n/a (Claude Code supports) | n/a | n/a | n/a | n/a |
| 146 | MCP: auto-import from `~/.claude/mcp.json` + `~/.codex/config.toml` | n/a (we ARE the source) | n/a | n/a | n/a | n/a |
| 147 | MCP: `mcp_list/connect/disconnect/reload` tools | NOT-PLANNED-YET | sanctum | 5 | 5 | P2 |
| 148 | Telemetry: install / upgrade / auth events | OMITTED (data sovereignty) | n/a | n/a | n/a | n/a |
| 149 | Cost: per-session token + dollar accounting | NOT-PLANNED-YET | sanctum | 6 | 4 | P3 |
| 150 | Cost: Anthropic cache-cold warning | NOT-PLANNED-YET | sanctum | 5 | 5 | P2 |
| 151 | Cost: usage HUD overlay | NOT-PLANNED-YET | forge | 5 | 4 | P3 |
| 152 | Replay: session → video export (mp4) | NOT-PLANNED-YET | NEW | 9 | 3 | P3 |
| 153 | Replay: synchronized multi-pane swarm replay | NOT-PLANNED-YET | NEW | 9 | 3 | P3 |
| 154 | iOS native client (Tailscale + OpenClaw bundle) | NOT-PLANNED (Mind owns) | mind | 9 | 5 | P2 |
| 155 | Desktop superapp (iced-based) | NOT-PLANNED (RKOJ workbench owns) | rkoj | n/a | n/a | n/a |
| 156 | Self-update (auto-update on new release) | NOT-PLANNED-YET | sanctum | 5 | 4 | P3 |
| 157 | Auto-import sessions from codex/claude/opencode/pi | NOT-PLANNED-YET | sanctum | 6 | 5 | P2 |
| 158 | Background server health (idle timeout, owner-pid) | NOT-PLANNED-YET | sanctum | 7 | 4 | P3 |
| 159 | Niri-style scrollable tiling pattern | NOT-PLANNED-YET (matrix row 27 has doc TODO) | forge | 6 | 7 | P1 |
| 160 | Sinister-branded mermaid renderer fork | partial (matrix row 28 — fork plan) | sanctum | 7 | 6 | P2 |
| 161 | Plugin: `Skill_Seekers` external skill discovery | NOT-PLANNED-YET (Forge PH12) | forge | 5 | 6 | P2 |
| 162 | Plugin: `claude-hooks-2.4.0` integration | NOT-PLANNED-YET (Forge PH13) | forge | 5 | 7 | P1 |

**Aggregates by status:**

| Status | Count |
|---|---|
| shipped / done | 9 |
| partial | 22 |
| NOT-PLANNED-YET | 88 |
| NOT-PLANNED (skip — Claude Code covers or out of lane) | 27 |
| n/a (irrelevant) | 16 |

**By priority tier:**

| Tier | Count |
|---|---|
| P0 (ship this week) | 9 |
| P1 (ship this month) | 26 |
| P2 (ship this quarter) | 51 |
| P3 (nice-to-have) | 28 |

---

## 10. Comprehensive build plan (P0 + P1 only)

3-line specs per P0/P1 gap.

### P0 (ship this week — 9 items)

**P0-1: TUI launch (default `forge` entry)** — `projects/sinister-forge/source/forge/cli.py`. Compose: Textual app with picker (PH3) + agent pane (PH2) + RKOJ tab (PH7). Already scaffolded; finish PH3 picker keybinds + cold boot art (PH5).

**P0-2: Memory CLI list/search** — `tools/forge-memory-bridge/` extend with `cli.py` subcommands `list`, `search`, `stats`. Compose: Python click wrapping existing `recall()` + new `list_all()`. Add to `sinister-cli` umbrella as `sinister memory <op>`.

**P0-3: Slash `/help` + `/?` + `/commands`** — Forge `forge/slash_commands/help.py`. Compose: scans registered commands dict, renders rich Table. Mirror in Term shell as `/help`.

**P0-4: Slash `/clear`** — Forge `forge/slash_commands/clear.py` + Term shell. Compose: wipes agent pane buffer; preserves resume-point. Single-line implementation per pane.

**P0-5: Slash `/swarm` + `/swarm <op>`** — Forge `forge/slash_commands/swarm.py`. Compose: invokes `sinister-swarm` CLI as subprocess; pretty-prints JSON output. Maps `/swarm list/dm/broadcast/spawn/watch/status` → subprocess call.

**P0-6: Slash `/resume` + `/sessions`** — Forge `forge/slash_commands/resume.py`. Compose: scans `_shared-memory/resume-points/<agent>/*.json`, renders picker, applies on selection. Mirror Term shell.

**P0-7: Slash `/quit`** — Forge + Term. One-liner per pane (Ctrl+D or close button); already partially works.

**P0-8: Forge `agentgrep` operator-gated install + Forge `:grep` slash** — `tools/sinister-agentgrep/` with `install.ps1` that runs `cargo install --git https://github.com/1jehuang/agentgrep` ONLY after operator approval queued to `OPERATOR-ACTION-QUEUE.md`. Forge `/grep <pattern>` wraps the binary.

**P0-9: Document & ship the `scrollable-tiling-pattern.md` brain entry** — `_shared-memory/knowledge/scrollable-tiling-pattern.md`. Operator already directed this (matrix row 27). 200-line writeup of niri column-scroll + Forge PH2-PH3 mapping. **Not source code — pure knowledge.**

### P1 (ship this month — 26 items)

**P1-1: Slash `/model` + `/models` + `/refresh-model-list`** — Forge `forge/slash_commands/model.py`. Compose: reads `automations/agent-host-routing.md` model list, renders picker, on select writes to `agent-prefs.json` per-pane.

**P1-2: Slash `/memory` toggle + `/memory <op>`** — Forge slash + Term. Compose: wraps `tools/forge-memory-bridge/`; `/memory on/off` toggles auto-recall; `/memory write "..."` calls store(); `/memory search "..."` calls recall().

**P1-3: Slash `/context` snapshot** — Forge slash + Term `:context`. Compose: dumps current resume-point + active todos + last 5 messages as markdown to side panel.

**P1-4: Slash `/compact` + `/transfer`** — `tools/sinister-compact/` Python script. Compose: invokes a summarization agent (Ruflo `agent_spawn` with summarizer prompt) → writes compact context to `_shared-memory/cross-agent/<timestamp>-handoff.md` → spawns fresh session pointed at handoff.

**P1-5: Slash `/agents` + `/subagent` + `/subagent-model`** — Forge slash. Compose: shows per-role model assignment (defined in `agent-prefs.json`); `/subagent <task>` invokes `mcp__ruflo__claims_claim` + `agent_spawn`.

**P1-6: Slash `/autoreview` + `/autojudge` + `/review` + `/judge`** — `tools/sinister-review/` Python (NEW). Compose: end-of-turn callback hook (PH13 hook integration); spawns `gpt-5.5` review agent that reads last turn's diff/output; writes verdict to side panel. `/review` is one-shot.

**P1-7: Tool: `agentgrep` integration** — covered by P0-8 above. P1 polish: add file-structure JSON output, adaptive truncation per-session-seen-list.

**P1-8: Tool: `session_search`** — `tools/sinister-session-search/` Python. Compose: glob `_shared-memory/cross-agent/*.md` + `PROGRESS/*.md` + grep with rank. Add to `sinister-cli` as `sinister sessions search <q>`.

**P1-9: Tool: `subagent` proper task spawn** — extend `sinister-swarm spawn` with `--report-back` flag. Compose: spawns + claims a task ID; receives completion report DM via inbox; logs to `PROGRESS/`.

**P1-10: Tool: `side_panel`** — Forge PH7 RKOJ tab gets a panel-write API; expose as MCP tool? Defer — Forge owns. P1 = scaffold the write API + slash bridge.

**P1-11: Hooks: tool-wrappers (truncate, guard)** — Forge PH13 partial. Compose: wraps every tool call with adaptive truncation (≤8KB default) + safety classifier (auto-allow ls/read/grep; require-permission for bash with rm/mv).

**P1-12: Hooks: Claude-Code-style pre/post-tool** — Forge PH13 full. Compose: integrate `claude-hooks-2.4.0` package; expose `settings.json` `hooks` array; pre-tool can veto, post-tool can transform output. Already in plan; just finish.

**P1-13: UI: animated boot art** — Forge `art.py` (PH5). Compose: Vault Boy rotating frames (1.2s window); pure Textual widget. Already planned.

**P1-14: UI: status pill polish** — Forge PH7 + Term PH7. Compose: tokens used / model / cache state pill in top-right. Reads from agent-prefs.json + per-pane state.

**P1-15: UI: Cascadia typography + purple theme polish** — Forge `theme.py`. Compose: load `#7A3DD4` primary, dim cyan accent, Cascadia Code Pro font hint in screen.css. Polish-pass; already ✅ scaffolded.

**P1-16: UI: niri-style workspace** — Forge PH2-PH3 + new `panes/workspace.py`. Compose: horizontal column-scroll between session panes via Ctrl+Alt+H/L; reads `WORKSPACE_*_KEY` env vars (Sinister-equivalent names).

**P1-17: UI: scroll keybinds (Ctrl+K/J + Alt+U/D + Ctrl+[/] + Ctrl+G)** — Forge `panes/agent_pane.py` Textual Bindings. Compose: 8 keybinds wired to Log widget scroll API. P1 polish — confirm vim feel.

**P1-18: Crate: `agent-runtime` turn streaming** — Forge PH6 own. Compose: streams MCP `agent_execute` SSE chunks into pane Log widget. Partial via `forge-bridge`; finish.

**P1-19: Crate: `compaction-core`** — `tools/sinister-compact/` (P1-4 above) is the seed. Compose: drop-in to Forge agent loop when turn-count > N or token-count > M.

**P1-20: Crate: `tui-mermaid` Sinister-branded renderer** — `tools/sinister-mermaid-render/`. Compose: fork `1jehuang/mermaid-rs-renderer`, swap palette to purple, AGPL-3.0 license header, RKOJ-ELENO author. Wired to `memory-graph-render/` Stage 3.

**P1-21: Crate: `safety` classifier polish** — `tools/sinister-safety/` Python. Compose: action classifier (auto-allow vs. require-permission); on require, posts to `OPERATOR-ACTION-QUEUE.md` + notifies via heartbeat.

**P1-22: Config: `automations/session-templates/sinister.toml` unified** — Sanctum-master ships this. Compose: merge agent-prefs.json + projects.json + panel-config.json into one TOML; provide migration script. Operator may prefer JSON — confirm before shipping.

**P1-23: `debug` socket CLI** — extend `sinister-bus` with `debug <op>` subcommand. Compose: `sinister bus debug state` dumps current agent state via heartbeats + inbox.

**P1-24: `ambient run-visible` partial** — `automations/memory-consolidate.ps1` runs nightly; add `ambient status` CLI that reads last-run timestamp from `_shared-memory/heartbeats/sanctum-ambient.json`.

**P1-25: `restart save/restore` polish** — Sanctum already has resume-points; add `sinister restart save` + `restore` to `sinister-cli`. Compose: thin wrapper over `automations/resume-point-write.ps1` + boot in `start-sinister-session.ps1`.

**P1-26: `transfer` compact handoff** — see P1-4 above.

---

## Sources

All source-of-truth files locally on disk at `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\` (jcode v0.12.3 release tarball, MIT). Direct file references used in this audit:

- `README.md` (30 KB — main feature surface)
- `Cargo.toml` (workspace + 48 member crates)
- `OAUTH.md` (16 KB — auth providers)
- `TELEMETRY.md` (17 KB — schema v5 events)
- `PLAN_MCP_SKILLS.md` (3 KB — original MCP+skills plan)
- `AGENTS.md` (2 KB — repo conventions)
- `docs/AMBIENT_MODE.md` (background loop)
- `docs/MEMORY_ARCHITECTURE.md` (graph-based hybrid)
- `docs/SWARM_ARCHITECTURE.md` (proposed swarm coord)
- `docs/SAFETY_SYSTEM.md` (HITL safety tiers)
- `src/cli/args.rs` (clap Args + Command + subcommand enums — full CLI surface)
- `src/cli/commands.rs` (CLI command implementations)
- `src/tool/mod.rs` (tool registry + 30+ built-in tools)
- `src/config.rs:27-119` (90+ env vars list)
- `src/tui/app/state_ui_input_helpers.rs:41-122` (62+ slash commands)
- `src/tui/app/commands.rs` (slash command handlers)
- `src/tui/keybind.rs` (TUI keybindings)
- `src/skill.rs` + `.jcode/skills/optimization/SKILL.md` (skill schema)
- `src/mcp/{mod,client,manager,protocol,tool}.rs` (MCP client + management tool)
- `crates/` (48 workspace crate names)
- `scripts/` (60+ helper scripts — install.sh, install.ps1, dev_cargo.sh, etc.)
- `telemetry-worker/{schema.sql, wrangler.toml, src/}` (Cloudflare Worker telemetry backend)
- `ios/Package.swift` + `ios/Sources/` (native iOS client)
- `.claude/mcp.json` (empty — `{"servers":{}}`)

Web-sourced cross-references (matrix row 27 + 28):
- `https://github.com/niri-wm/niri` — scrollable-tiling Wayland compositor (UX pattern reference only, code does NOT port)
- `https://github.com/1jehuang/mermaid-rs-renderer` — Rust mermaid renderer (will be forked into `tools/sinister-mermaid-render/` per operator directive)
- `https://github.com/1jehuang/agentgrep` (v0.1.2 git dep in jcode Cargo.toml; will be operator-gated installed under `tools/sinister-agentgrep/`)
- `https://github.com/1jehuang/jcode` — upstream repo (this audit is read-only)
- `https://github.com/1jehuang/handterm` — jcode's native scroll-api terminal (mentioned in README; not ported)

---

## Closing note

This audit covers **162 distinct jcode features/options/tools/slash-commands/MCP-points** across 10 sections. The matrix at `_shared-memory/knowledge/jcode-feature-matrix.md` is the short-pointer (28 rows, status-only); this document is the deep dive with priority + build-difficulty + ROI per row.

Lane discipline observed: NO source code written. NO sibling-lane brain entries touched. NO `projects/sinister-forge/source/`, `projects/sinister-term/source/`, or `automations/window-manager/` modifications. Only this one analysis markdown.

The 9 P0 gaps (Section 10) are the suggested ship-this-week order. Of those, **P0-2 (memory CLI list/search)** and **P0-3/4/7 (slash /help, /clear, /quit)** are the lowest-friction wins; **P0-5 (slash /swarm)** depends on this session's `sinister-swarm` shipping; **P0-6 (slash /resume)** depends on Sanctum's resume-point discipline already being in place; **P0-9 (scrollable-tiling brain entry)** is pure documentation per operator directive.
