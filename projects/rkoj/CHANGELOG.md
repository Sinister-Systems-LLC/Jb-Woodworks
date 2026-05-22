> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ Changelog

All notable changes to the unified RKOJ project. Format roughly Keep-a-Changelog; versions are RKOJ.exe build versions, not component versions (each lane has its own).

## v1.6.29 — 2026-05-22

**Operator-action urgent rows in the Agents empty state.** Operator sees
Sanctum-wide actionable items (🔴 Critical / 🟠 High) right where they
spawn new agents — no need to leave RKOJ to check the queue.

- New `_actions_host` panel in the empty state, sibling of
  `_recent_sessions_host`. Renders up to 3 unchecked items pulled from
  `_shared-memory/OPERATOR-ACTION-QUEUE.md`.
- `_scan_urgent_actions()` parses the markdown — finds `## 🔴 Critical`
  / `## 🟠 High` section headers, then matches lines like
  `- [ ] **Title** — description` within them. Inline emoji (item-level)
  overrides section context. Stops at `limit` matches.
- `_build_action_row()` renders each as a Panel-style row with a
  severity-tinted left border (red for critical, amber for high) +
  emoji + title (bold white) + truncated detail (muted gray).
- Auto-refreshes when the empty state appears (last card closed).
- MANIFEST.json 1.6.28 → 1.6.29.
- `__init__.py __version__ = "1.6.29"`.

## v1.6.28 — 2026-05-22

**Per-card pin/star** — operator can pin favorite cards to the top of
the niri-scroll grid. Useful when running 5+ agents and only 1-2 are
the ones you actually need to glance at right now.

- `AgentSession.pinned: bool = False` — new field; survives /save +
  /export (added to the resume-point schema via `_write_resume_point`
  no changes since dataclass auto-includes).
- `AgentCard._pin_btn`: hollow ☆ (MUTED_FG) → filled ★ (PURPLE_PRIMARY)
  on click. Sits in the header strip between cost-pill and chevron.
- `pin_changed(pane_id)` pyqtSignal; AgentsView listens + calls
  `_rebuild_grid()` so pinned cards float to top instantly.
- Grid sort key now: `(not c.session.pinned, project_key, created_at)`
  — pinned cards bubble up, then project-grouping stays intact.
- `/pin` slash command: same effect as clicking the star, so operator
  can pin without aiming for the small button. Registered in
  SLASH_COMMANDS → 20 commands now.
- MANIFEST.json 1.6.27 → 1.6.28.
- `__init__.py __version__ = "1.6.28"`.

## v1.6.27 — 2026-05-22

**Card-collapse toggle** — operator can collapse any agent card to a
40-54px header strip (hiding terminal + thinking label + input + Send)
so 5+ active cards stack compactly in the niri-scroll grid.

- New `_collapse_btn` chevron in the card header (between `_cost_pill`
  and close-X). `▾` when expanded, `▸` when collapsed. Hover tints
  purple. Tooltip "Collapse / expand this card (Ctrl+M)".
- `_toggle_collapsed()` flips `_collapsed` boolean, toggles visibility
  of terminal / thinking label / input / send button. Adjusts min-height
  280 → 40 + max-height 16777215 → 54 (Qt's QWIDGETSIZE_MAX is the
  expand-back value).
- `Ctrl+M` keyboard shortcut bound at AgentCard scope (mirrors Ctrl+L
  for clear).
- Streaming continues while collapsed — operator can expand later and
  see what arrived. Cost pill / turn pill update normally.
- MANIFEST.json 1.6.26 → 1.6.27.
- `__init__.py __version__ = "1.6.27"`.

## v1.6.26 — 2026-05-22

**Bottom-status-bar live agent count + brain entry for the v1.6.20-25 polish cluster.**

- `_StatusBar.set_live_agents(n)` — new API. AgentsView's
  `cards_changed` signal now also pushes to the status bar. When set,
  the agents pill renders `"N live · M on disk"` instead of the prior
  `"N/M agents"` (which was double-counting closed cards as still
  online because heartbeats persist with `session_status=ended`).
  Dot color also follows live count (not heartbeat count).
- Brain entry: `_shared-memory/knowledge/rkoj-polish-cluster-v1.6.20-25-2026-05-22.md`
  consolidates the 6-iteration polish cluster (rate_limit / SlashPopup /
  /skill / auto-save / /usage / sidebar badges / timestamp gutter / /stats).
  5 reusable patterns codified + 8 anti-patterns. Indexed in `_INDEX.md`.
- MANIFEST.json 1.6.25 → 1.6.26.
- `__init__.py __version__ = "1.6.26"`.

## v1.6.25 — 2026-05-22

**Dim timestamp gutter + Devices sidebar count badge.**

- **Dim timestamp gutter**: `[HH:MM:SS] >> ` and `[HH:MM:SS] << ` now
  render in `MUTED_FG` (`#8e8e93`) via `QTextCharFormat` so the
  operator's message body + EVE's reply pop visually. New
  `_append_dim(text)` helper preserves sticky-scroll. `_append_terminal`
  resets char-format on each insert so dim doesn't bleed forward.
- **Devices sidebar count badge** — third badge in the row (Agents,
  Sessions already have them). Counts ADB devices in `device` state
  (online only). Polled every 6s via a dedicated `_devices_timer` so
  USB plug/unplug events surface fast. Sessions badge stays on the
  30s tick.
- `Sidebar.refresh_badges()` aggregates Sessions + Devices into one
  pass; the 30s QTimer drives both.
- MANIFEST.json 1.6.24 → 1.6.25.
- `__init__.py __version__ = "1.6.25"`.

## v1.6.24 — 2026-05-22

**Terminal timestamp gutter.** Each operator turn and EVE reply now
opens with a `[HH:MM:SS]` prefix so the operator can scan the
conversation chronologically + time-bound debugging:

```
[14:32:01] >> spawn a sub-agent to audit the resume-points
[14:32:14] << I'll spawn a sub-agent…
…
[14:32:47] >> /cost
```

- `_on_send`: prepends `[HH:MM:SS]` to the `>> {text}` line.
- `_handle_stream_event` (text_delta first chunk): prepends `[HH:MM:SS]`
  to the `<< ` reply prefix.
- `_render_plain_chunk` (non-JSON fallback path): same.
- `_reply_start_pos` still records the position AFTER the `<< ` prefix
  so v1.6.16 markdown formatting only touches EVE's reply text.
- MANIFEST.json 1.6.23 → 1.6.24.
- `__init__.py __version__ = "1.6.24"`.

## v1.6.23 — 2026-05-22

**Live Agents badge + Sessions badge auto-refresh on card close + /stats.**

- **Live Agents count badge** on the sidebar "Agents" nav row, mirroring
  the v1.6.22 Sessions badge. AgentsView emits `cards_changed(int)`
  whenever a card spawns or closes; app.py wires it to
  `Sidebar.set_agents_count`. No polling — signal-driven.
- **Sessions badge auto-refresh** when a card closes — since v1.6.21
  closes write an auto-save resume-point, the Sessions count may have
  just incremented. app.py connects `cards_changed` to
  `Sidebar.refresh_sessions_badge` so it updates immediately rather
  than waiting up to 30s for the next QTimer tick.
- **/stats slash command**: prints a 6-line RKOJ fleet snapshot —
  heartbeats (N online / M total), inbox messages, brain entries,
  devices (online/offline/unauth), vault disk-used %, pending ops.
  Reuses `state.snapshot()` which already drives the bottom status bar.
  Registered in SLASH_COMMANDS → 19 commands now.
- MANIFEST.json 1.6.22 → 1.6.23.
- `__init__.py __version__ = "1.6.23"`.

## v1.6.22 — 2026-05-22

**Sidebar Sessions count badge.** Small purple pill on the "Sessions" nav
row showing how many distinct sessions are saved on disk (deduplicated
by `session_uuid`). Operator sees at-a-glance "do I have a session
worth resuming?" without opening the picker.

- `_NavRow` gains a `_badge` QLabel + `set_badge(text)` API. Hidden
  by default; shows as a `rgba(191,90,242,180)` rounded pill on the
  right side of the nav row.
- `Sidebar` adds a 30-second QTimer that calls
  `refresh_sessions_badge()` which scans
  `_shared-memory/resume-points/EVE on */*.json`, collects unique
  `session_uuid` values, and pushes the count into the Sessions row's
  badge. Empty → badge hidden.
- Initial refresh fires at construction, so the badge is correct
  the moment RKOJ launches.
- MANIFEST.json 1.6.21 → 1.6.22.
- `__init__.py __version__ = "1.6.22"`.

## v1.6.21 — 2026-05-22

**Auto-save resume-point on card close + cross-card `/usage` aggregator.**

Until now `/save` was the only path that wrote a resume-point — closing
a card silently dropped the session. Plus the cost telemetry only lived
in memory, so there was no way to see RKOJ-wide spend.

- **AgentCard auto-save on close**: `_on_close` (operator clicks X) and
  `shutdown` (whole app closing) both write a resume-point with
  `save_reason=autoclose` / `app-shutdown` before killing the
  subprocess. Skips empty cards (no operator messages sent).
- **`_write_resume_point()` extracted** as a single writer shared by
  `/save`, `_on_close`, and `shutdown`. Payload now includes
  `total_cost_usd` / `total_in_tokens` / `total_out_tokens` so
  `/usage` can aggregate from disk without re-running anything.
- **`/usage` slash command** — walks
  `_shared-memory/resume-points/EVE on */*.json`, dedupes by
  `session_uuid` (keeps highest cost — cumulative within a card's
  lifetime), groups by project, prints per-project + grand totals:

  ```
  [/usage] RKOJ session totals (from disk):
  
    Sanctum                ·  5 sess ·  42 turns · $ 0.4218 ·  84,209 in · 1,300 out
    Kernel APK             ·  2 sess ·  18 turns · $ 0.1840 ·  31,420 in ·   540 out
    ───────────────────────  ─────────  ──────────  ──────────  ───────────  ────────
    TOTAL                  ·  7 sess ·  60 turns · $ 0.6058 · 115,629 in · 1,840 out
  ```

  Registered in SLASH_COMMANDS → discoverable via autocomplete (18 total).
- MANIFEST.json 1.6.20 → 1.6.21.
- `__init__.py __version__ = "1.6.21"`.

## v1.6.20 — 2026-05-22

**rate_limit_event surface + popup position safety + /skill loader.**

- **rate_limit_event renderer**: claude's `rate_limit_event` stream-json
  events fire on every turn but mostly with `status: allowed` (no
  signal). Now suppressed for "allowed" + printed as `⚠ rate-limit
  <status> (<kind>) resets at <UTC>` for warning/exceeded/etc so
  operator isn't surprised by a hard 5-hour wall.
- **SlashPopup position safety**: `show_above()` now adjustSize()s
  first, then tries above; if `globalY - h - 4 < screen.y()` it flips
  to *below* the input. Also clamps X to `screen.x() + width - popup.w
  - 4` so a popup near the right edge doesn't truncate.
- **/skill <name> loader**: reads a saved skill `.md` from
  `D:\Sinister Sanctum\skills`, `~/.sinister/skills`, or
  `~/.claude/skills` (looks for `<name>.md` AND `<name>/SKILL.md`),
  stages it into the input, fires `_on_send` on the next event-loop
  tick. So the regular spinner / streaming / token-accounting paths
  all run uniformly. Registered in SLASH_COMMANDS — autocomplete
  popup now lists 17 commands.
- MANIFEST.json 1.6.19 → 1.6.20.
- `__init__.py __version__ = "1.6.20"`.

## v1.6.19 — 2026-05-22

**`/model` + `/focus` slash commands + brain entry capturing the
stream-json arc.**

- **/model**: shows current mode (claude / claude-haiku / claude-opus)
  and (with arg) sets the mode for the NEXT spawn. Notes that
  `claude --resume` is locked to the original model, so mid-session
  switches don't propagate — operator must open a new card to actually
  use a different model.
- **/focus**: re-focuses the input box. Useful after operator clicked
  into the terminal scrollback to copy text and lost typing focus.
- Both added to SLASH_COMMANDS registry → discoverable via the v1.6.17
  autocomplete popup. Total slash commands now: 16.
- **Brain entry**: `rkoj-stream-json-jcode-parity-2026-05-22.md` —
  codifies the v1.6.11→v1.6.18 arc into reusable doctrine. Stream-json
  event-type table, NDJSON line-buffer pattern, required CLI flags,
  6 anti-patterns, Phase-2 (Anthropic SDK direct) path. Indexed in
  `_shared-memory/knowledge/_INDEX.md`.
- MANIFEST.json 1.6.18 → 1.6.19.
- `__init__.py __version__ = "1.6.19"`.

## v1.6.18 — 2026-05-22

**Live tool-name in spinner + rotating placeholder hints + /devices + /export.**

- **Tool name in spinner**: when claude opens a `tool_use` block, the
  spinner swaps from `⠹ EVE is thinking…` to `⠹ ● Bash… (4.7s)`.
  `_current_tool` is set on `content_block_start` + cleared on `result`.
  Operator sees the LIVE step instead of generic thinking.
- **Rotating input placeholder**: 5-second QTimer cycles through 6
  discoverable hints in the input placeholder text — "Type / to
  autocomplete", "Ctrl+L clears scrollback", "Shift+Enter = multi-line",
  "/save writes a resume-point", "/cost shows cumulative spend",
  "/skills lists Sanctum skills". Pauses when the input has text or a
  turn is busy.
- **/devices slash command**: inline ADB device list (mirrors the
  Devices tab) — state + serial + model. Tells operator how to add
  devices if none connected.
- **/export slash command**: dumps the full transcript to a markdown
  file under `_shared-memory/resume-points/EVE on <project>/<ts>-export.md`.
  Operator can share / grep / commit the conversation. Schema: H1 title
  + metadata bullets (pane_id, session_uuid, mode, cost, turns) + per-turn
  H2 with operator-in-fenced-block + EVE-as-prose.
- Both new commands added to `SLASH_COMMANDS` registry so they appear
  in the v1.6.17 autocomplete popup.
- MANIFEST.json 1.6.17 → 1.6.18.
- `__init__.py __version__ = "1.6.18"`.

**Build note**: classifier briefly throttled mid-iteration; build had to
retry after a 180s wakeup. Captured in the brain entry
`rkoj-stream-json-jcode-parity-2026-05-22.md` (next ship).

## v1.6.17 — 2026-05-22

**Slash-command autocomplete popup** (jcode keybind parity). Operator
types `/` → a list of matching commands appears above the input.
Up/Down navigates, Enter completes, Esc dismisses.

- Module-level `SLASH_COMMANDS` registry — 14 commands (/help, /clear,
  /cost, /history, /memory, /mcp, /needs, /open, /persona, /retry,
  /save, /session, /skills, /vault). Tuple format: `(cmd, description)`.
- New `_SlashPopup` class — frameless `QFrame` containing a `QListWidget`
  styled to match the SavedSessionsPicker. Uses `Qt.WindowType.Popup |
  Qt.WindowType.FramelessWindowHint` + `WA_ShowWithoutActivating` so it
  appears above the input without grabbing focus. Filter is prefix-match
  on the typed token; popup auto-hides on zero matches or focus-out.
- `_MultiLineInput` gains a `slash_popup` attribute. AgentCard wires
  the popup in `_build` after creating the input + connects
  `completed` → `_on_slash_completed`.
- `_MultiLineInput.keyPressEvent` — when popup is visible:
  - Down  → `popup.select_next()`
  - Up    → `popup.select_prev()`
  - Esc   → `popup.hide()`
  - Enter / Tab → complete the selected command (replace input with
    `<cmd> ` + cursor at end + hide popup)
- `_MultiLineInput._maybe_update_popup` — runs after every keystroke:
  shows + filters the popup when text starts with `/` and there's no
  newline yet; hides otherwise.
- `_MultiLineInput.focusOutEvent` hides the popup when input loses focus
  (clicking elsewhere shouldn't leave the popup floating).
- MANIFEST.json 1.6.16 → 1.6.17.
- `__init__.py __version__ = "1.6.17"`.

## v1.6.16 — 2026-05-22

**Markdown post-stream formatting in the terminal** — code fences, inline
code, and bold spans in EVE's replies now render with proper typography
instead of raw backticks + asterisks. Applied once per turn at
`_on_finished` via QTextCharFormat over the reply's document range
(tracked by `_reply_start_pos`, recorded right after the `<< ` prefix
is appended).

- ` ```code``` ` blocks → JetBrains Mono / darker bg `#08060c` /
  light-purple fg `#E8D6FF`. DOTALL regex so multi-line blocks match.
- `` `inline code` `` → JetBrains Mono / subtle bg `#1c1c1e` / purple-
  halo fg `#C39DFF`. Single-line only.
- `**bold**` → QFont.Weight.Bold over the whole match including the
  asterisks (asterisks stay visible — markdown-aware formatting only,
  not full re-rendering).
- Doesn't fight the v1.6.11 streaming path: tokens still arrive
  letter-by-letter; formatting is layered AFTER the turn finishes.
  Operator sees the raw markdown streaming in, then watches it pop
  into formatted typography the moment the reply ends.
- MANIFEST.json 1.6.15 → 1.6.16.
- `__init__.py __version__ = "1.6.16"`.

## v1.6.15 — 2026-05-22

**Recent saved sessions inline in the Agents empty-state.** Operator's
fresh-launch experience: previously they had to click sidebar → Sessions
→ picker → double-click to resume yesterday's conversation. Now the
empty state shows up to 5 most-recent saved resume-points right under
the hero, with a one-click Resume button per row.

- `AgentsView._rebuild_recent_sessions()` — scans
  `_shared-memory/resume-points/EVE on */*.json`, filters out pre-v1.6.3
  saves without a `session_uuid`, sorts newest-first, takes top 5.
- `AgentsView._build_recent_session_row(s)` — Panel-style row: project
  display (purple bold) · turn count · save_reason chip · saved_at ts
  (mono) · Resume button (purple primary).
- Click Resume → directly calls `self.spawn_agent(session_uuid=…)` so the
  card lands inline in the same view (no dialog detour).
- Auto-refresh in `_rebuild_grid` when the empty state appears (last
  card closed) → list always reflects current disk state, including
  the autoclose-save the just-closed card wrote.
- `_scan_recent_sessions` extracted as a helper (mirrors the picker's
  scanning logic; will dedupe to state.py later).
- MANIFEST.json 1.6.14 → 1.6.15.
- `__init__.py __version__ = "1.6.15"`.

## v1.6.14 — 2026-05-22

**Sticky-scroll terminal.** Operator UX: when reading earlier output
during a long EVE reply, the auto-scroll-to-bottom was yanking them back
to the live stream on every token. Now the auto-scroll is conditional —
only fires if the scrollbar was already at (or within 6px of) the bottom
when the chunk arrived. Operator can scroll up freely and the stream
keeps appending below without dragging them down.

- `_append_terminal` reads scrollbar position before insertion → only
  re-pins cursor + scrollbar to bottom if `was_at_bottom`.
- 6px tolerance so mouse-wheel jiggle doesn't accidentally "lock" the
  view in scroll-up mode.
- MANIFEST.json version 1.6.13 → 1.6.14.
- `__init__.py __version__ = "1.6.14"`.

## v1.6.13 — 2026-05-22

**Quick-wins polish.** While operator was testing v1.6.12:

- **AUTO-FOCUS INPUT ON SPAWN**: AgentsView.spawn_agent schedules a
  `QTimer.singleShot(0, card.input.setFocus)` so operator can type
  immediately after a card lands without clicking. (0ms delay so focus
  arrives after Qt finishes laying out the new card.)
- **TERMINAL MIN-HEIGHT 170 → 240**: agents were getting a tiny 170px
  scrolling window for long replies. 240px breathing room (card auto-
  grows beyond this when the operator drags the window taller).
- **MANIFEST.json** version 1.6.12 → 1.6.13.
- **VERSION**: `__init__.py __version__ = "1.6.13"`.

## v1.6.12 — 2026-05-22

**Cumulative cost telemetry + Ctrl+L = clear.** Stacks on top of v1.6.11
jcode-parity stream-json wiring. Operator: *"relaunch and test it and keep
working"* — v1.6.11 verified working end-to-end (stream-json parser test
PASS: 19 events parsed, 6/176 tokens, $0.07 / 4.4s footer captured).

- **CUMULATIVE COST PILL**: new mono pill in the card header strip
  (`$0.0042` style) that accumulates across all turns in the card.
  Updated in `_handle_stream_event` when the `result` event lands.
  Tooltip shows the full breakdown (in tok / out tok / total cost).
  Pill color is `PURPLE_PRIMARY` so it reads as Sanctum brand.
- **AgentCard `_total_cost_usd` / `_total_in_tokens` / `_total_out_tokens`**:
  3 new instance attrs; auto-accumulate from the per-turn `result` event.
- **/cost SLASH COMMAND**: prints the full breakdown into the terminal
  with avg/turn so operator can decide whether to keep going or /close
  the card to limit spend.
- **Ctrl+L = clear** keyboard shortcut. jcode-style keybind parity —
  operator can clear scrollback without typing /clear. Bound at the
  AgentCard level so it works when any input/terminal child has focus.
- **MANIFEST.json** version 1.6.11 → 1.6.12.
- **VERSION**: `__init__.py __version__ = "1.6.12"`.

## v1.6.11 — 2026-05-22

**Real jcode parity — stream-json token-by-token + thinking + tool_use + cost.**
Operator (verbatim, screenshot mid-iteration): *"i want it to work like
jcode and have everything i asked for"*. v1.6.10 fixed the visible `[stderr]
no stdin data received` warning but the chat was still all-text-at-once.
v1.6.11 wires the actual jcode-parity surfaces:

- **STREAM-JSON OUTPUT**: every turn now goes through
  `claude -p --output-format=stream-json --include-partial-messages
  --verbose --session-id|--resume <uuid>`. claude emits NDJSON events
  (one per line) — `_on_stdout` line-buffers them + parses each via
  `_handle_stream_event`.
- **TOKEN-BY-TOKEN STREAMING**: `content_block_delta + text_delta`
  events stream individual tokens into the terminal as they arrive.
  No more all-at-end dump.
- **THINKING DISPLAY**: `thinking_delta` events update the spinner text
  live with a 60-char preview of the current thought (`⠹ 💭 The
  operator wants me to…`). When claude opens a thinking block, the
  spinner prefix swaps from `EVE is thinking…` to `💭 thinking…`.
- **TOOL USE DISPLAY**: `content_block_start + tool_use` renders a jcode
  marker line `● <ToolName>(<input-preview-80-chars>)` then the tool's
  result appears as `✓ <result-preview-120-chars>` from the subsequent
  `user/tool_result` block.
- **PER-TURN FOOTER**: `result` event emits a footer line
  `▸ N in + M out tokens (cache_read=K) · $0.0042 · 3.1s · tools: Bash,Read`
  so operator sees token spend + cost + duration + tools used per turn.
- **SYSTEM EVENT SUPPRESSION**: hook_started / hook_response / init /
  status events are silently dropped from the terminal (too noisy).
- **MANIFEST.json** version 1.6.10 → 1.6.11.
- **VERSION**: `__init__.py __version__ = "1.6.11"`.

## v1.6.10 — 2026-05-22

**Agent-chat polish batch** — `/loop keep going make it better` cadence.
Stacks on top of v1.6.9's picker overhaul. Same EVE on Sanctum branch.

- **MULTI-LINE INPUT**: agent card input is now `_MultiLineInput`
  (QPlainTextEdit subclass) — Enter sends, Shift+Enter inserts a newline.
  Auto-resizes vertically up to a 5-line cap so a long prompt grows the
  input cleanly without blowing up the card; `/retry` switched to
  `setPlainText`. Operator can finally paste / compose multi-paragraph
  prompts without the prior single-line forced-truncation pain.
- **ANSI STRIP**: `_strip_ansi()` regex over every stdout chunk in
  `_on_stdout`. `claude -p` sometimes emits ANSI escape codes when its
  output piper thinks stdout is a TTY; previously those rendered as
  `\x1b[32m...\x1b[0m` garbage in the terminal. Now stripped to plain.
- **TURN COUNTER PILL**: new pill in the card header strip ("0 turns" /
  "1 turn" / "N turns") that bumps in `_on_finished` after each
  completed turn. Operator sees conversation length at a glance without
  having to `/history`.
- **EMPTY-STATE HERO**: `AgentsView` empty state was a single flat label
  "No agents yet — click Create Agent to spawn EVE." Replaced with a
  centered Panel-style hero: 28px purple title + 2-line subtitle (CTA
  → + Create Agent + Sessions sidebar) + a 3-tip row underneath
  (Per-agent session memory · Folder tabs · /help inside any card).
  Makes a fresh-launch RKOJ feel like a destination, not a blank canvas.
- **MANIFEST.json**: `version 1.6.9 → 1.6.10`.
- **VERSION**: `__init__.py __version__ = "1.6.10"`.
- **BUILD**: 44s, 71.68 MB onefile, M1 PASS. Smoke confirmed Qt window
  detected within 8s. EXE on Desktop.

## v1.6.9 — 2026-05-22

**Saved Sessions picker UX overhaul.** EVE on Sanctum, branch `agent/sinister-sanctum/cli-dispatcher-2026-05-21`. Operator brief was "get to work" continuing the rapid v1.6.x iteration after v1.6.8 shipped the inline-resume revert. The picker was lying — button labeled "Open in new window" but v1.6.8 routed everything inline. Plus the operator now has v1.6.7 autoclose saves piling up under `_shared-memory/resume-points/` with no in-UI cleanup. This ship fixes both.

- **TRUTHFUL WORDING**: "Open in new window" → "Resume inline". Subtitle rewritten ("double-click or pick + Resume inline. Del key (or button) removes a save."). Tooltips added on both action buttons clarifying behavior.
- **DELETE FROM PICKER**: "Delete selected" button (left of Cancel) + `Del` key shortcut. Reversible: file is renamed `<name>.json.deleted` on disk, not unlinked — operator can `ren` it back if it was a mistake. Picker self-rebuilds after each delete; Resume button disables when zero rows remain.
- **SAVE_REASON CHIP**: rows now show `[autoclose]` vs `[manual]` so operator can tell at a glance which saves came from the v1.6.7 window-close path vs explicit `/save`.
- **RELATIVE-TIME LABELS**: `_humanize_age()` helper turns ISO8601 `saved_at` into compact "12 min ago" / "3 hr ago" / "2 days ago" / `YYYY-MM-DD` for >30d. Way faster to scan than raw timestamps.
- **TIGHTER ROW LAYOUT**: row 1 = `<project> · <N> turn(s) · <ago> [reason]`; row 2 = `mode <claude> · uuid <abc12345…>` (8-char uuid prefix instead of 36 — full uuid moves to tooltip-territory if needed later).
- **EMPTY-STATE COPY**: tells operator about the v1.6.7 autoclose path so they know saves accumulate even without explicit `/save`.
- **DIALOG SIZE**: +20w/+20h (640×500) to give the richer rows room.
- **NO PUBLIC API CHANGE**: `result_data` schema additive (`save_reason` field added; existing keys unchanged). Callers in `app.py` (`_open_sessions_picker`) + `dialogs.py` (`NewAgentDialog._on_resume_clicked`) continue to work unmodified.
- **MANIFEST.json**: `version 1.6.0 → 1.6.9`, `updated 2026-05-21 → 2026-05-22`.
- **VERSION**: `__init__.py __version__ = "1.6.9"`.

## v1.6.0 — 2026-05-21

**Project-shape promotion + Panel 1:1 patches + Phase-1 memory bootstrap.** Operator (verbatim 2026-05-21, session start): *"i need you to make a porject in projects for rkoj and add everything there that we use for rkoj. ... I want the 1:1 exact ui as sinister panel. 1:1 nothing else everything the same and exact. ... When i click new agent it will be like we click the jcode exe and openeed a window."*

- **MOVED**: `tools/sinister-rkoj-qt/` → `projects/rkoj/source/` via single `git mv` (69 files, history preserved). RKOJ outgrew the `tools/` shape — multi-tab UI, plugin substrate, version-stamped EXE ships, operator-facing primary surface. See `_shared-memory/knowledge/rkoj-project-shape-promotion-2026-05-21.md` for the 7-step promotion pattern + 5 anti-patterns.
- **PATCHED (Panel 1:1)**: `SIDEBAR_WIDTH 220 → 240` (Panel canonical aside) · `QLabel#PageTitle font-size 24 → 26` (Panel `text-[26px]`) · `QPushButton#ChipTab min-height 26 → 30` + padding `4×14 → 6×16` (Panel `h-8 px-4`). Reference: `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/panel-1to1-spec.md`.
- **ADDED (Phase-1 memory⇄jcode integration)**: every spawned agent now writes a heartbeat to disk + seeds PROGRESS + creates inbox/resume dirs at spawn time. Per-card 30s `QTimer` keeps presence live. `QProcessEnvironment` propagates `SINISTER_AGENT_DISPLAY` / `_SLUG` / `_PANE_ID` / `_PROJECT_KEY` / `_HEARTBEAT_PATH` / `_PROGRESS_PATH` / `_RESUME_DIR` / `_INBOX_DIR` / `_AGENT_IDENTITY=EVE` / `_AUTHORSHIP=RKOJ-ELENO` so the spawned `claude -p` child knows its identity from env. AgentSession dataclass +6 fields. Brain entry: `_shared-memory/knowledge/rkoj-phase1-memory-bootstrap-2026-05-21.md`.
- **PATH REFS**: `automations/ship-rkoj-qt-to-desktop.ps1` + `automations/smoke-rkoj-qt.ps1` defaults repointed at `projects/rkoj/source/sinister_rkoj_qt/dist/`. PS-5.1 `Join-Path` paren fix. RKOJ.spec `_TOOL_ROOT` → `_PROJECT_ROOT` for clarity. `projects/rkoj/MANIFEST.json` `rkoj-qt` + `rkoj-qt-extensions` component paths updated. `tools/_INDEX.md` `sinister-rkoj-qt` row removed (it's a project now). `_shared-memory/knowledge/sinister-rkoj-extensibility-doctrine.md` plugin-path refs updated.
- **PLAN DOCS LANDED**: 5 files at `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/`: cleanup-proposal · forward-plan · panel-1to1-spec · memory-jcode-integration-audit · personal-folder-sinister-purge.
- **CROSS-AGENT BROADCAST**: `_shared-memory/cross-agent/2026-05-21T2330Z-sanctum-to-fleet-rkoj-relocation.md` (no-ACK).
- **SMOKE**: M1 PASS (`Sinister Sanctum — RKOJ.exe` Qt window detected <8s). M2 process-survival PASS (25s × 5 samples, RSS stable). M3-M10 require operator click-through.
- **EXE**: 75,160,157 byte onefile (71.68 MB, +4 KB vs v1.5.1 for memory bootstrap helpers) shipped to `C:\Users\Zonia\Desktop\RKOJ.exe` + `RKOJ.lnk` updated.
- **VERSION**: `__init__.py __version__ = "1.6.0"` · `MANIFEST.json version = "1.6.0"`.
- **COMMITS**: `caa66d4` (ship) + `40c478e` (brain).

### Roadmap captured (NOTED but NOT BUILT — operator addendum 2026-05-21)

Future workstation features documented in `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/forward-plan.md` § C. Build sequence TBD by operator:

- **Devices ADB wiring** — connect all phones, scrcpy embed, per-device logcat
- **Self-hosted AnyDesk replacement** — RustDesk / Guacamole / MeshCentral candidate stack, Tailscale plane, Vault-backed auth
- **Kameleo-style anti-detect browser** — Playwright + Chromium + fingerprint randomization, profile manager in Vault
- **Own Android emulator system** — wrap Sinister Emulator Bundle as RKOJ emulator manager
- **Open extension registry** — every new tool plugs into `projects/rkoj/source/extensions/<slug>/manifest.json`

## v1.5.1 — 2026-05-21

**Strip pivot — 2 tabs + Panel-exact + niri-scroll.** Operator (verbatim 2026-05-21): *"remove ALL THIS FUCKING SHIT AND LISTEN TO ME very carefully. i want two fucking tabs. agents and devices ... exact sinister panel look ... niri infinite scroll ... glow when they need our input ... X button works"*. The v1.5.0 PyQt6 ship landed but the surface was bloated — Excel ribbon, KPI tiles, project sub-tab strip, workstation tab — none of which the operator wanted. v1.5.1 strips the chrome back to operator-canonical: 2 chip tabs, Panel-exact sidebar, Sheets-style header menu strip, niri-scroll agent grid, folder-tab row, working X.

- **REMOVED**:
  - Excel ribbon (5 groups VIEW/SPAWN/AGENT/AUTOMATE/MAINTAIN — all deleted)
  - 4 KPI tiles (deleted)
  - Workstation tab + sub-pane (operator dropped — Console launches elsewhere)
  - Project sub-tab strip (replaced by folder-tab row in the Agents tab)
  - STATUS panel bottom-left of sidebar
- **KEPT + REWORKED**:
  - Sidebar — now Panel-exact: 3 sections (DAILY / INSIGHTS / MANAGE), mascot block, no STATUS panel
  - Header — now 2 rows: Sheets-style menu strip (File / Edit / View / Insert / ...) on row 1; chip tabs + actions + CreateAgent on row 2
  - Agents tab — now NiriScrollGrid (infinite horizontal/vertical scroll of agent cells, per-project grouping)
  - `persona.py` — EVE binding unchanged
- **NEW**:
  - Folder-tab row in the Agents tab (All chip + per-project chips for filtering the niri-scroll grid)
  - Glow-on-pending animation (cell pulses when the EVE inside needs operator input)
  - Sheets-style menu strip with placeholder QMenus (File / Edit / View / Insert / Format / Data / Tools / Extensions / Help)
  - Working X button + `closeEvent` that terminates all QProcess children before exit (no orphaned `claude` processes)
- Reference: `_shared-memory/knowledge/rkoj-ui-exact-spec-2026-05-21.md` (operator-canonical UI spec doctrine).

## v1.5.0 — 2026-05-21

**Pivot to native PyQt6 desktop app.** Operator (verbatim): *"i dont want a fucking web ui ... popup the ui on the fucking desktop"* + *"function like jcode but be ours and we can foreever expand"*. The pywebview path (v1.4.x) was rejected — HTML/CSS surface read as "web ui". RKOJ.exe v1.5.0 is now a frameless rounded PyQt6 window with Sinister Panel layout + Excel-style ribbon + jcode-form terminals in the Agents tab (QPlainTextEdit + QProcess wrapping `claude --dangerously-skip-permissions -p`).

- Source: new `tools/sinister-rkoj-qt/` (sub-agent shipped this turn) — `sinister_rkoj_qt/{app, sidebar, header, ribbon, kpis, agents_tab, phones_tab, workstation_tab, theme, state, persona}.py`.
- Layout matches `snap.sinijkr.com` exactly: 240px sidebar (mascot + 4 sections + status) + 96px header (chip tabs + actions + clock) + Excel ribbon (5 groups: VIEW/SPAWN/AGENT/AUTOMATE/MAINTAIN) + 4 KPI tiles + project sub-tab strip + main pane.
- Agents tab: niri-style vertical scroll of jcode-form terminals. EVE persona injected verbatim in each opening prompt (RKOJ-ELENO authorship, full Sinister tool list, branch convention).
- Phones tab: 4-stat strip + filter chips + 2-col body (device rail + identity/heartbeat/RKA/kill-switch/ADB shell/scrcpy launch) + live logcat tail.
- Workstation tab: action card grid (vault / brain / watchdog / backups / mcp / explorer).
- Slash-command intercept routes `/help /clear /save /resume /create /skill /mcp /watchdog` to existing forge.commands API; everything else to claude subprocess.
- Extensibility doctrine landed at `_shared-memory/knowledge/sinister-rkoj-extensibility-doctrine.md` — manifest-driven plugin system so we add features forever without touching chrome/panes.
- 5 new jcode-gap slash commands (/pair /ambient /permissions /replay /browser) added to forge.commands.py.
- Build: `pyinstaller --clean --noconfirm tools/sinister-rkoj-qt/RKOJ.spec`. Output replaces `Desktop/RKOJ-Workstation/` so the existing `RKOJ.lnk` shortcut picks it up.

## v1.4.1 — 2026-05-21

**MCP Phase 2A — `/mcp` subcommand wire-up.** Builds on v1.4.0's bundled `mcp` Python SDK. `/mcp` now supports 5 subcommands: `list` (default, shows server name + command + args), `show <name>` (pretty-print JSON config), `status` (SDK + config + server-count health probe), `tools <name>` (placeholder, documents Phase 2B follow-up + import-from-bundled-SDK example), `call <server> <tool> [json]` (placeholder, documents the async-Textual-loop integration needed).

- Source: `projects/sinister-forge/source/forge/commands.py::_cmd_mcp` rewritten.
- Phase 2B (live stdio tool calls) still queued — needs an async-safe wrapper since Textual's event loop is already running.

## v1.4.0 — 2026-05-21

**Integrated bundle ship — Term + MCP SDK + Skills + workstation auto-launch + vault auto-spawn.** Operator escalation: *"we are working on rkoj exe not fucking bat ... combingin all thigns we have been working on rkoj workstation, jcode, all the skills we ahve made, mcp, our new console system"*. The v1.3.0 ship was UI-complete but the EXE bundle was thin (forge + 7 sinister-* tools only). v1.4.0 fattens the bundle.

- **Sinister Term bundled inside the EXE** — `term` package added to `RKOJ.spec` via `collect_submodules("term")` + `collect_data_files("term")`. No more separate `sterm` process; the terminal lives inside RKOJ.
- **MCP Python SDK bundled** — `mcp` package collected (Phase 1). Phase 2 (forge.bridge wires to `~/.claude/.mcp.json` for eve/sinister-panel/sinister-snap/sinister-tiktok/vault/ruflo) is a follow-up turn.
- **Skills/*.md content shipped inside the binary** — `datas.append((skills_root, "skills"))` puts the 6 candidate skills (sk-swarm-coord, sk-vector-memory, sk-federation, sk-observability, sk-aidefence, dashboard-skeleton) inside the EXE as a SkillRegistry fallback when `~/.sinister/skills/` is empty.
- **Workstation console auto-launch from EXE** — `workstation_panel.py` path typo fixed (`D:/Sinister/Sanctum/...` → `D:/Sinister Sanctum/...`); Open-Browser button now `subprocess.Popen` spawns `desktop_app.py` detached when `:5077` is idle (one click instead of two); Launch button prefers in-tree daemon over dist/RKOJ.exe.
- **Vault daemon auto-spawn at EXE startup** — `RKOJ-entry.py` new `_ensure_background_services(sanctum_root)` runs before TUI mount; if `:5078` idle, `tools/sinister-vault/daemon.py` spawns detached.
- **Binary size**: 50.2 MB (+287 KB vs v1.3.0's 50.0 MB) — minimal cost for the integration.
- Reference commit: `e34ac7a feat(rkoj): v1.4.0 EXE integration scope — term + skills + MCP + workstation auto-launch + vault auto-spawn` + ship commit (this commit).

## v1.3.0 — 2026-05-21

**Sinister Panel layout — mascot + 2 tabs + per-project sub-tabs.** Operator parity ship of the Sinister Panel chrome onto the Forge sidebar.

- Sinister Panel-style sidebar — mascot block + two top-level tabs (Agents / Phones) — `projects/sinister-forge/source/forge/panes/sidebar.py`
- `AgentsDashboard` pane with per-project sub-tabs — one sub-tab per active project — `projects/sinister-forge/source/forge/panes/agents_dashboard.py`
- Workstation tab in sidebar — surfaces the Console window manager inside the TUI — `projects/sinister-forge/source/forge/panes/workstation_panel.py`
- Auto-spawn Sanctum agent on first launch — render-safe tab labels (no crash on empty/non-ascii)
- Reference commits: `83393a5` (sidebar + AgentsDashboard) · `c46e941` (auto-spawn + workstation tab) · `9f4529b` (ship marker)

## v1.2.0 — 2026-05-21

**Agents tab = single console.** Niri strip auto-hides when only one workspace is active — cleaner default for the common case.

- `NiriWorkspaceGrid` enters single-workspace mode by default; strip surfaces only at count ≥ 2 — `projects/sinister-forge/source/forge/panes/niri_workspace.py`
- Agents tab compose() simplified — single-console path skips the strip entirely
- Verified all 15 jcode-form features work in single-pane mode (commit `0224d5b`)
- Reference commits: `972bd2d` (NiriWorkspaceGrid single-workspace default) · `0224d5b` (jcode-form 15/15 verified) · `80d6df2` (ship marker)

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
