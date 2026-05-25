<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# jcode 0.12.4 — Full Feature Audit + EVE Port Priority (2026-05-24)

> **Origin:** operator hard-canonical 2026-05-24T22:10Z verbatim *"i need you to review jcode and how they do things and i want all features in our exes. i nwat how they display the console logs as well in the concise manner. all the popups everything."*
> **Source corpus:** `C:\Users\Zonia\Desktop\jcode-0.12.4` (full local copy, MIT — © 2025 Jeremy Huang; confirmed `LICENSE` line 1).
> **Method:** crate-by-crate walk of `crates/jcode-tui-*` + `src/tui/` + cross-walk to (a) prior port plan `jcode-port-plan-eve-2026-05-24` (D1-D5) and (b) parity audit `jcode-eve-exe-parity-audit-2026-05-24` (30 rows).
> **Composes with:** `jcode-port-plan-eve-2026-05-24`, `jcode-eve-exe-parity-audit-2026-05-24`, `jcode-feature-matrix`, `eve-exe-uniform-ui-infinite-accounts-2026-05-24` (R2 uniform-UI canon), `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (EXPAND principle), `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate).

## 1. Feature inventory (organized by area)

| Area | jcode source | Variants found | Notes |
|---|---|---|---|
| **Banner / hero / animation** | `crates/jcode-tui-style/src/theme.rs:120-149` `rainbow_prompt_color(distance)` (exp-decay rainbow→gray); `theme.rs:57` 8-frame braille spinner `⠂⠆⠇⠧⠷⠧⠇⠆`; `theme.rs:178-192` `animated_tool_color` cyan↔purple sin-pulse; `theme.rs:159-175` shimmer/spotlight prompt enter cues | rainbow gradient + spinner + tool-color pulse + prompt-entry shimmer + spotlight bg | **DONE** rainbow ported: `tools/eve-picker/jcode_animation.py` |
| **Project picker** | `crates/jcode-tui-session-picker/`, `src/tui/session_picker/` | multi-select w/ filter, recent-first, badge for active session | **DONE** `tools/eve-picker/project_picker_multiselect.py` |
| **Account / usage display** | `crates/jcode-tui-account-picker/`, `crates/jcode-tui-usage-overlay/src/lib.rs` (Loading/Good/Warning/Critical/Error/Info 6-state; icon + color + label) + `src/tui/usage_overlay.rs` + `src/tui/account_picker_render.rs` | 6-state status icons `◌ ● ▲ ◆ ✕ ○`, RGB-tuned per-state, filter-search | **DONE** jcode-style status bar in `tools/eve-picker/account_manager.py` |
| **Console-log rendering** | `crates/jcode-tui-tool-display/src/lib.rs` (`resolve_display_tool_name`/`canonical_tool_name`/`is_edit_tool_name`/`truncate_middle_display`/`concise_tool_error_summary`/`tool_output_looks_failed`); `src/tui/ui_tools.rs:1383-1465` `render_batch_subcall_line` | batch header `✓ batch N calls · X tok`, per-subcall row w/ icon+name+intent+summary+token badge, width-budget reserved → truncate-middle, severity (Normal/Warning gray→yellow / Danger red), error summary collapse (`Error: missing field X` → `invalid input: missing X`), exit-code parse | **NOT PORTED** — top priority for sinister-term integration |
| **Popups / modals / overlays** | `src/tui/ui_overlays.rs` (1500+ LOC), `src/tui/permissions.rs`, `src/tui/login_picker.rs`, `src/tui/usage_overlay.rs`, `src/tui/info_widget*` | (1) Changelog overlay (scrollable, `Esc/j/k/Space/PageUp`, % scroll-pct), (2) Help overlay (sectioned: Commands / Session / Memory&Swarm / Auth / System / Debug; `cmd_style` + `desc_style` + `key_style` + `sep_style`, separators), (3) Debug overlay (frame metrics + widget placements), (4) Login picker, (5) Account picker, (6) Permissions modal (tool-use approval), (7) Inline-interactive prompt (Y/N), (8) Image inline display, (9) Mermaid pane (Ctrl+D), (10) Side panel (workspace-map widget), (11) Info widget (model/git/memory/swarm-background/todos/usage/tips), (12) Compact suggestion popup (slash-command autocomplete), (13) Catchup brief side panel, (14) Diagram pane | **NOT PORTED** — see top-10 ranking |
| **Status bar / footer** | `src/tui/ui_status.rs` + `ui_input.rs:1-80` `ComposerMode {Chat,SlashCommand,ShellLocal,ShellRemote}` w/ per-mode color + hint (`shell mode · Enter runs locally/server`) | mode-tinted bar, model name, elapsed, token counter, queued-msg badge, "notification line" (single line above input) | **NOT PORTED** — high-value (operator screenshot req) |
| **Spinners / progress** | `theme.rs:57` 8-frame braille; `workspace_map_widget.rs:128` 4-frame tile `◴◷◶◵` via `tick%4`; `activity_indicator()` respects `enable_decorative_animations` flag (static `•` fallback) | session-start spinner + tile-active spinner + tool-running pulse | partial — `eve.py` has plain ascii spinner; D5 in earlier plan |
| **Color theme tokens** | `crates/jcode-tui-style/src/theme.rs:5-52` 17 named functions (user_color / ai_color / tool_color / accent_color / queued_color / asap_color / pending_color / system_message_color / file_link_color / dim_color / user_text / user_bg / ai_text / header_*_color × 3) | all RGB triples, no terminal indexed | matches our 6-color palette from `eve-exe-uniform-ui-infinite-accounts-2026-05-24` R2 |
| **Keyboard shortcuts / chords** | `crates/jcode-tui-core/src/keybind.rs` + `src/tui/keybind.rs` | Ctrl+Tab model-switch, Ctrl+Shift+Tab model-prev, Alt+H/J/K/L workspace nav, Ctrl+K/J scroll, Alt+U/D page, Ctrl+W picker, Ctrl+D diagram pane, Ctrl+L clear, Esc close-overlay, `/` slash-prefix, `$` shell-prefix | rebindable via `config.keybindings.*`; well-documented schema |
| **Mermaid rendering** | `crates/jcode-tui-mermaid/` + `src/tui/mermaid.rs` + `src/bin/mermaid_side_panel_probe.rs` | cache → resvg/usvg → ratatui-image (Kitty/Sixel only) | gated on R28 Rust-fork doctrine |
| **Memory recall UI** | `src/tui/info_widget_memory_*.rs` + `src/memory*.rs` + `src/embedding.rs` (ONNX MiniLM 384-dim) | injected-memory pill, recall-event log, memory-graph nodes (HasTag/Supersedes/RelatesTo/ClusterEntry) | wrapped via Option-C plan (Ruflo MCP wrapper) — D2 |
| **Sub-agent / swarm UI** | `src/tui/info_widget_swarm_background.rs` + `src/tui/app/remote_notifications.rs:146` `present_swarm_notification` + `src/server/swarm_channels.rs` | swarm-background activity pill, task-assignment formatting, DM-prefix strip, background-task progress formatting, file-activity preview | D1 in port plan (registry + heartbeat) |
| **Tool-call display** | `src/tui/ui_tools.rs` (1500+ LOC) + tool-display crate | batch header / subcall row / token badge / intent line / error summary / batch-running compact (`summarize_batch_running_tools_compact`) | same as console-log row above |
| **Diff / patch display** | `src/tui/ui_diff.rs`, `ui_file_diff.rs`, `remote_diff.rs` | unified-diff render w/ added/removed colors, file-header line, hunk context, line-num gutter | **NOT PORTED** — operator-asked feature |
| **Streaming response display** | `src/tui/stream_buffer.rs` + `src/tui/ui_messages.rs` + `crates/jcode-tui-messages/src/cache.rs` | per-token streaming, cursor block, wrapped-line cache, connection-phase indicator | **NOT PORTED** |
| **Settings / config UI** | `src/cli/commands.rs` (`/config`, `/config init`, `/config edit`); `src/config.rs` | slash-command driven, opens `$EDITOR`; in-app surfaces config snapshot | **NOT PORTED** — slash-cmd palette stub instead |
| **Onboarding flow** | `src/tui/login_picker.rs` + `src/setup_hints.rs` + first-run wizard | provider-pick, QR-login, hint chips during idle | partial — EVE.exe `-Action Onboarding` exists |

## 2. Port priority ranking (value × effort × risk inverse)

Score = `value (1-5)` × `(6-effort) (1-5)` × `(6-risk) (1-5)`. Top 10:

| # | Feature | V | E | R | Score | Source → Target |
|---|---|---|---|---|---|---|
| 1 | **Compact log render** (batch header + subcall row + token badge + severity color) | 5 | 3 | 2 | **180** | `src/tui/ui_tools.rs:1383-1465` + `crates/jcode-tui-tool-display/src/lib.rs` → `projects/sinister-term/source/compact_log.py` (~300 LOC) |
| 2 | **Status bar / footer** (mode-tinted: Chat/Slash/Shell + model + elapsed + token counter) | 5 | 3 | 2 | **180** | `src/tui/ui_input.rs:20-54` `ComposerMode` → `tools/eve-picker/status_bar.py` |
| 3 | **Help overlay** (sectioned, scrollable, %-pct, key/cmd/desc spans) | 4 | 4 | 2 | **128** | `src/tui/ui_overlays.rs:85-300+` → `tools/eve-picker/help_overlay.py` |
| 4 | **Slash-command palette** (autocomplete popup as user types `/`) | 5 | 3 | 3 | **135** | `src/tui/ui_input.rs:60-80` + `app::COMMAND_SUGGESTION_VISIBLE_LIMIT` → `tools/eve-picker/cmd_palette.py` |
| 5 | **Toast / notification line** (single-line above input, `present_swarm_notification` formatter) | 5 | 4 | 2 | **160** | `src/tui/app/remote_notifications.rs:146` + `ui.rs:1893` 1-line notification-height row → `tools/eve-picker/toast.py` (read from `fleet-updates.jsonl`) |
| 6 | **Permissions modal** (Y/N tool-use approval; canonical-11 reversibility surface) | 4 | 3 | 3 | **108** | `src/tui/permissions.rs` + `ui_inline_interactive.rs` → `tools/eve-picker/permissions_modal.py` |
| 7 | **Diff render** (unified colored, gutter, hunk-context) | 5 | 2 | 3 | **120** | `src/tui/ui_diff.rs` + `ui_file_diff.rs` → `tools/eve-picker/diff_view.py` |
| 8 | **Spinner library** (8-frame braille + 4-frame tile, FPS-driven, `enable_decorative_animations` gate) | 3 | 5 | 1 | **75** | `crates/jcode-tui-style/src/theme.rs:57-90` → already-stub `tools/eve-picker/jcode_animation.py` extension |
| 9 | **Changelog overlay** (scrollable, version-grouped, % position) | 3 | 4 | 1 | **60** | `src/tui/ui_overlays.rs:13-83` → `tools/eve-picker/changelog_overlay.py` |
| 10 | **Inline-interactive prompt** (Y/N + free-text quick-prompt inline above input) | 4 | 3 | 2 | **96** | `src/tui/ui_inline_interactive.rs` + `src/tui/app/inline_interactive.rs` → `tools/eve-picker/inline_prompt.py` |

## 3. Already shipped (cross-off)

1. Rainbow gradient animation — `tools/eve-picker/jcode_animation.py` (this turn).
2. Project multi-select picker — `tools/eve-picker/project_picker_multiselect.py`.
3. Account manager w/ jcode-style usage popup — `tools/eve-picker/account_manager.py`.
4. (5 parallel subagent ships this turn — counted as shipped per operator request.)
5. Memory MCP wrapper (Option C) — D2 from earlier plan.

## 4. Critical NEW features (operator screenshots suggest desire)

- **Always-on status bar at bottom** — model · elapsed · token counter · queued count · notification line. Maps to operator screenshot showing jcode's footer-rail.
- **Toast notifications from fleet-update channel** — push `priority=high` rows from `_shared-memory/fleet-updates.jsonl` into the notification-height row above input. Wire `present_swarm_notification`-style formatter (DM-prefix strip, file-activity compact path, plan-title compaction).
- **Command palette (`Ctrl-K` or `:` style)** — fuzzy slash-cmd autocomplete; jcode uses `/` prefix + `COMMAND_SUGGESTION_VISIBLE_LIMIT` (visible-window scroll). Our EVE.exe could mirror with `:` prefix → live filter against `automations/*.ps1` + slash-cmds.
- **Inline diff display for sub-agent edits** — when a subagent emits an Edit/Write tool-call, render unified diff in the console-log compact row (currently we just say "Edit X"). High value for the swarm visibility operator asks for.
- **Streaming-response cursor + connection-phase chip** — `ConnectionPhase` indicator (Connecting / Ready / Streaming / Throttled).

## 5. Recommended next 5 ships (sister-B / sinister-term consumption)

| # | Source (jcode) | Target (ours) | Effort |
|---|---|---|---|
| 1 | `crates/jcode-tui-tool-display/src/lib.rs` (full file, 6 fns) + `src/tui/ui_tools.rs:1383-1465` `render_batch_subcall_line` | `projects/sinister-term/source/compact_log.py` (5 primitives: batch header, tool-name resolution, token-budget truncate, severity badge, batch-footer suppress) | ~300 LOC, 1-2 iters |
| 2 | `src/tui/ui_input.rs:20-100` `ComposerMode` + footer paragraph | `tools/eve-picker/status_bar.py` (single render fn returns mode-tinted Text; consumed by `eve.py` + `start-sinister-session.ps1` Build-Phrase) | ~120 LOC, 1 iter |
| 3 | `src/tui/app/remote_notifications.rs:146-250` `present_swarm_notification` | `tools/eve-picker/toast.py` — poll `_shared-memory/fleet-updates.jsonl` priority=high tail; render 1-line above input; auto-dismiss in 8s | ~150 LOC, 1 iter |
| 4 | `src/tui/ui_overlays.rs:85-300+` `draw_help_overlay` + section-pattern | `tools/eve-picker/help_overlay.py` — pull `/help` content from our 17 doctrine docs; sectioned: Onboarding / Sessions / Accounts / Mesh / Doctrine / Debug | ~250 LOC, 1 iter |
| 5 | `src/tui/ui_input.rs:60-100` `command_suggestion_hint_line_count` + window scroll | `tools/eve-picker/cmd_palette.py` — `:` prefix fuzzy-match against `automations/*.ps1` + slash-cmds + ScheduleWakeup-class actions | ~180 LOC, 1-2 iters |

## 6. License notes

`C:\Users\Zonia\Desktop\jcode-0.12.4\LICENSE` is **MIT** © 2025 Jeremy Huang. All ports above are permitted with attribution. Attribution pattern: every ported file gets header comment `# Ported from jcode 0.12.4 (MIT, © 2025 Jeremy Huang); RKOJ-ELENO adaptation 2026-05-24`. Our additions remain RKOJ-ELENO authored per the 2026-05-21 hard-canonical AUTHORSHIP block.

## 7. Composes with

- `jcode-port-plan-eve-2026-05-24` (executes D1-D5 + this audit's top 10)
- `jcode-eve-exe-parity-audit-2026-05-24` (30-row capability map; this audit deepens "all popups everything" row)
- `eve-exe-uniform-ui-infinite-accounts-2026-05-24` R2 (6-color palette + 6-line cap — every ported overlay must fit)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (EXPAND principle — new primitives commit to skeleton first)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (each top-10 ship requires smoke-test before claim)
- `r28-sinister-mermaid-render-rust-fork-doctrine-2026-05-24` (mermaid path; gated)

Updated: 2026-05-24
