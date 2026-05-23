> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ Changelog

All notable changes to the unified RKOJ project. Format roughly Keep-a-Changelog; versions are RKOJ.exe build versions, not command-versions (each lane has its own).

## v1.6.65 — 2026-05-22

**Status dot click → /persona, mode pill click → /model. Header
click sweep complete — every visible element in the card header
is now navigable without typing.**

- `status_dot` (was QLabel) → `_ClickPill("", self, intercept="/persona")`.
  Tooltip: "Click → /persona (identity dump)".
- `mode_pill` (was QLabel) → `_ClickPill(self.session.mode, self,
  intercept="/model")`. Tooltip: "Click → /model (show/change model)".
- `/shortcuts` block now lists 7 click targets: status dot, PROJECT,
  mode pill, N turns, $X.XXXX, ⏱ elapsed, tag chip (L+R).
- Closes the header click-action sweep: any operator workflow that
  previously required `/<command>` typing can now happen via a
  single click anywhere in the card chrome.
- MANIFEST.json 1.6.64 → 1.6.65.
- `__init__.py __version__ = "1.6.65"`.

## v1.6.64 — 2026-05-22

**Elapsed pill click → /timer, project label click → /find <project>.
Completes the header click-action sweep — every pill is now navigable
without typing.**

- `_elapsed_pill` was `QLabel("--")` → now `_ClickPill("--", self,
  intercept="/timer")`. Click anytime (during a turn for live elapsed,
  or idle for the "last turn took Xs" report).
- `project_label` was a local QLabel → now `_ClickPill` with
  `intercept=f"/find {project_display}"`. Click in any card to scroll
  the grid to the next card on the same project. Repeated clicks
  cycle via the standard /find-next wrap.
- Tooltips added to both for discoverability.
- `/shortcuts` block updated with PROJECT and ⏱ elapsed click rows.
- MANIFEST.json 1.6.63 → 1.6.64.
- `__init__.py __version__ = "1.6.64"`.

## v1.6.63 — 2026-05-22

**Clickable header pills + /shortcuts updated. Turn-count pill click
→ /history; cost pill click → /cost. Operator can grok card state
without typing anything.**

- New generic `_ClickPill(QLabel)` class taking an `intercept` slash
  command string. Left-click fires `card._maybe_intercept(intercept)`
  so the existing handler logic runs unchanged.
- Turn-count pill (was QLabel) → `_ClickPill("0 turns", self, intercept="/history")`.
- Cost pill (was QLabel) → `_ClickPill("$0.0000", self, intercept="/cost")`.
- Both gain PointingHandCursor + descriptive tooltip.
- Extends v1.6.52 tag-chip click pattern to header pills.
- `/shortcuts` updated to mention:
  - Up/Down history recall (v1.6.62)
  - N turns pill click → /history
  - $X.XXXX pill click → /cost
  - tag chip L-click + R-click affordances
- MANIFEST.json 1.6.62 → 1.6.63.
- `__init__.py __version__ = "1.6.63"`.

## v1.6.62 — 2026-05-22

**Up/Down arrow history recall in input — standard bash/zsh terminal
UX. Up cycles backwards through prior user turns, Down advances.**

- New `_history_callback`, `_history_idx`, `_history_pending_text`
  fields on `_MultiLineInput`. AgentCard sets the callback to a
  lambda returning the live user-turn list (skipping notes) so
  /forget-last + /note interleaved entries don't pollute recall.
- Up at idx=-1 stashes whatever's typed into `_history_pending_text`
  and loads the most-recent entry. Subsequent Up walks older.
- Down past the most-recent restores the pending draft so operator
  doesn't lose what they were typing when they started navigating.
- Slash-popup-visible state wins over history (existing Up/Down
  bindings drive the popup unchanged).
- Multi-line composition (newline in input) disables history recall
  so Up/Down stays cursor-navigation in that mode.
- Submit clears `_history_idx` + `_history_pending_text` so the
  next session of recall starts fresh.
- MANIFEST.json 1.6.61 → 1.6.62.
- `__init__.py __version__ = "1.6.62"`.

## v1.6.61 — 2026-05-22

**Right-click tag chip → context menu with Find + Untag actions. Tags
become fully mouse-driven (no /untag typing needed).**

- `_TagChip.contextMenuEvent` opens a QMenu styled to match the
  ELEVATED/BORDER theme with the same purple hover used by the
  /slash autocomplete popup.
- Two actions:
  - "Find cards tagged 'X'" — emits `find_requested` (same as
    left-click)
  - "Remove tag 'X' from this card" — reuses the existing /untag
    intercept via `self._card._maybe_intercept(f"/untag {tag}")`
    so persistence + chip rebuild + feedback all run uniformly.
- Tooltip updated: `Left-click: /find … · Right-click: menu`.
- MANIFEST.json 1.6.60 → 1.6.61.
- `__init__.py __version__ = "1.6.61"`.

## v1.6.60 — 2026-05-22

**`/summarize-all` — fleet-wide /summarize. Stages the canned TL;DR
ask into every non-empty card + fires _on_send so parallel recaps
stream simultaneously across the workstation.**

- Extracted the 6-line canned prompt to module constant
  `_SUMMARIZE_PROMPT` so /summarize + /summarize-all share identical
  formatting (deduped between the two commands).
- New `summarize_all_requested(invoker_id)` signal on AgentCard;
  AgentsView slot `_summarize_all` iterates `_cards.values()`:
  - skips cards with no prior turns (`skipped {N} empty card(s)`)
  - skips cards mid-turn (`skipped {N} card(s) mid-turn`) — same
    no-clobber guard as /broadcast
  - stages `_SUMMARIZE_PROMPT` into each card's input + fires
    `QTimer.singleShot(0, c._on_send)` so spinner/streaming/cost
    runs uniformly per card
- 51 slash commands now (added /summarize-all).
- MANIFEST.json 1.6.59 → 1.6.60.
- `__init__.py __version__ = "1.6.60"`.

## v1.6.59 — 2026-05-22

**Persistent input drafts across resume — operator types something,
closes the card, re-opens → draft is restored to the input.**

- New `AgentSession.input_draft: str` dataclass field. Live-tracked
  via `self.input.textChanged → self._sync_input_draft` which assigns
  `session.input_draft = self.input.toPlainText()`.
- Resume-point JSON payload gets `"input_draft": self.session.input_draft`.
- `_restore_card_state_from_disk` reads the field and calls
  `card.input.setPlainText(draft)` if non-empty + prints a hint with
  char count + preview:
  ```
  ▸ input draft restored (47 chars): 'let me try refactoring this with…'
  ```
- `.clear()` after dispatch fires `textChanged` which auto-syncs the
  draft to empty — no extra wiring required.
- Pairs with v1.6.47 grep + tag persistence. Closes the last
  "things you'd expect to survive a close" gap.
- MANIFEST.json 1.6.58 → 1.6.59.
- `__init__.py __version__ = "1.6.59"`.

## v1.6.58 — 2026-05-22

**Per-tag chip colors — `blocked` is red, `wip`/`todo` is yellow,
`done`/`shipped` is green; other tags hash-stable across the palette
(purple/blue/cyan/orange/pink/indigo/lavender).**

- New `_TAG_PALETTE` (7-color list) + `_TAG_RESERVED` (6 semantic
  names) + `_tag_colors(tag) -> (fg, bg, border)` function. Uses
  stable polynomial hash `(h * 131 + ord(ch)) & 0x7fffffff` instead
  of Python's salted `hash()` so colors are identical across launches.
- `_rebuild_tags` applies the chip's per-tag color via setStyleSheet.
  Verified: `foo` hashes to the same color on every call; `blocked`
  stays red, `wip` stays yellow regardless of process restart.
- Reserved set: `blocked`, `wip`, `todo`, `done`, `shipped`, `review`.
  Semantic-by-convention so operator can scan a fleet at a glance.
- MANIFEST.json 1.6.57 → 1.6.58.
- `__init__.py __version__ = "1.6.58"`.

## v1.6.57 — 2026-05-22

**/help auto-generates from `SLASH_COMMANDS` registry — kills doc rot.
Plus consolidating brain entry for the v1.6.45-56 introspection cluster.**

- `/help` previously hardcoded 14 of the now-50 commands. New body:
  ```python
  width = max(len(cmd) for cmd, _ in SLASH_COMMANDS)
  for cmd_name, desc in sorted(SLASH_COMMANDS):
      self._append_terminal(f"  {cmd_name:<{width}}  {desc}\n")
  ```
  Width-aligned, sorted alphabetically. Adding a SLASH_COMMANDS row
  is now the only step to ship a new slash command.
- Brain entry `_shared-memory/knowledge/rkoj-introspection-cluster-v1.6.45-56-2026-05-22.md`
  codifies 7 reusable patterns (signal fan-out, 1-indexed user-turn
  numbering, additive JSON schema, click-to-jump QLabel subclass,
  shared `_fmt_duration`, body-extract methods, autogen /help) +
  7 anti-patterns. _INDEX.md row added.
- MANIFEST.json 1.6.56 → 1.6.57.
- `__init__.py __version__ = "1.6.57"`.

## v1.6.56 — 2026-05-22 — 50-slash milestone

**`/forget-last` — drop the last user/assistant pair from local
`session.turns`. Completes the history-manipulation trio:
`/retry` resends last + `/replay` resends old + `/forget-last` deletes.**

- Walks `session.turns` backwards skipping notes; pops the first
  user-keyed dict found. Notes between turns are preserved.
- Refreshes the turn-count pill immediately and writes a resume-point
  JSON with `save_reason="forget-last"` so the change survives crash.
- **Important caveat** echoed back to operator: claude --resume retains
  this turn server-side. /forget-last only affects RKOJ's local UI
  state — /history, /replay numbering, resume-point JSON. The model
  still has full conversation context.
- 50 slash commands now — milestone count matching v1.6.50 milestone
  version. Operator vocabulary fully filled in for: send / cancel /
  retry / replay / forget-last / clone / find / find-next / rename /
  tag / untag / tags / pin / save / show / diff / summarize / export /
  export-all / cost / usage / timer / uptime / stats / vault / memory
  / mcp / devices / persona / session / shortcuts / open / help /
  history / note / notes / model / needs / focus / clear / copy /
  grep / grep-clear / grep-next / grep-prev / broadcast / ping /
  skill / skills.
- MANIFEST.json 1.6.55 → 1.6.56.
- `__init__.py __version__ = "1.6.56"`.

## v1.6.55 — 2026-05-22

**`/export-all` — write every live card's transcript to one timestamped
bundle dir. Genuinely new fleet-ops capability — /broadcast can't fire
slash intercepts so this is the first way to batch-export.**

- Refactored `/export`'s inline body into `_export_to_markdown(target_dir)`
  method on AgentCard so AgentsView can call it on every card. Same
  output shape as /export, plus pane_id baked into the filename so
  multiple cards sharing a project resume_dir don't collide.
- Notes (kind=note entries) now render as blockquote sections in the
  exported markdown:
  ```
  ## Note 3
  > tried bumping retries to 5 — still flaky
  ```
- AgentsView slot `_export_all_transcripts(invoker_id)` writes all
  transcripts to `_shared-memory/rkoj-qt/exports/<timestamp>-bundle/`,
  skips empty cards, catches per-card failures without aborting the
  rest, echoes summary to invoker.
- New `export_all_requested(invoker_id)` signal on AgentCard.
- 49 slash commands now (added /export-all).
- MANIFEST.json 1.6.54 → 1.6.55.
- `__init__.py __version__ = "1.6.55"`.

## v1.6.54 — 2026-05-22

**`/uptime` — card lifetime + turn count + last activity + live state.**

- New `_spawn_ts: float` set at construction (monotonic). `_last_send_ts`
  updated in `_on_send` right after `_turn_started_ts`.
- Output:
  ```
  [/uptime]
    card lifetime : 47m 12s
    turns sent    : 14
    last activity : 3m 47s ago
    current state : idle (last turn took 8.4s)
  ```
- When a turn is in-flight, the state line reads `in-flight (Xm Ys elapsed)`
  pulling from `_turn_started_ts` to match the header pill / /timer.
- Reuses the `_fmt_duration` helper so output formatting is uniform
  across /timer / /cancel / /uptime / live elapsed pill.
- 48 slash commands now (added /uptime).
- MANIFEST.json 1.6.53 → 1.6.54.
- `__init__.py __version__ = "1.6.54"`.

## v1.6.53 — 2026-05-22

**`/summarize` — canned TL;DR prompt sent to EVE asking for a "where
are we" recap.**

- Stages a structured ask into the input + triggers `_on_send`:
  ```
  1) goal: what are we trying to do? (1 sentence)
  2) working: what's confirmed working? (2-3 bullets)
  3) blocked: what's stuck or unclear? (2-3 bullets)
  4) next: what should we try next? (1-3 bullets)
  Be concrete — reference specific files / errors / decisions.
  ```
- Empty-turns guard: prints hint instead of sending if no prior
  turns exist (claude --resume needs a session to summarize).
- Uses the same stage-into-input-then-_on_send pattern as /retry +
  /replay so spinner / streaming / cost path all run uniformly.
- 47 slash commands now (added /summarize).
- MANIFEST.json 1.6.52 → 1.6.53.
- `__init__.py __version__ = "1.6.53"`.

## v1.6.52 — 2026-05-22

**Clickable tag chips — clicking a chip in any card header behaves
like `/find <tag>` from that card. Every tag becomes a navigation
hot-spot.**

- New `_TagChip(QLabel)` class with `PointingHandCursor`, tooltip
  `Click to /find cards tagged 'wip'`, and overridden
  `mousePressEvent` that emits `find_requested(pane_id, tag_text)`.
- `_rebuild_tags` now constructs `_TagChip` instances instead of
  plain QLabels — keeps the visual styling identical.
- Wraps the standard /find / /find-next cycle so consecutive clicks
  on the same chip walk through every match in the fleet.
- Pairs with v1.6.51 `/tags` census: census tells you what tags
  exist; click jumps you there.
- MANIFEST.json 1.6.51 → 1.6.52.
- `__init__.py __version__ = "1.6.52"`.

## v1.6.51 — 2026-05-22

**`/tags` — fleet-wide tag census. Lists every tag in use + which
cards carry it. Cross-card insight for the workstation.**

- New `tags_census_requested(invoker_id)` signal on AgentCard.
- AgentsView slot `_print_tags_census` walks `self._cards.values()`,
  builds `dict[tag] -> [project_display:agent_name, ...]` via
  `collections.defaultdict(list)`, prints sorted-alphabetical census
  to the invoker's terminal:
  ```
  [/tags] 3 tag(s) across 5 card(s):
    'blocked' x 1 :: Sinister Panel:panel
    'wip'     x 2 :: Sinister Snap:snap-1, Sinister Snap:snap-2
    'review'  x 1 :: Sinister TikTok:tt-emu
  ```
- Empty-state message when no card has tags yet.
- Feedback echoes to invoker — same "stay in typing context" pattern
  as /find / /find-next.
- 46 slash commands now (added /tags).
- MANIFEST.json 1.6.50 → 1.6.51.
- `__init__.py __version__ = "1.6.51"`.

## v1.6.50 — 2026-05-22 — milestone

**`/diff <A> <B>` — unified diff between two assistant replies. Pairs
with `/clone`: run the same prompt in sibling cards, /diff the replies
to see how the models diverged.**

- Uses `difflib.unified_diff` (stdlib) with `n=2` context lines, file
  headers `reply #A` / `reply #B`.
- Same 1-indexed user-turn numbering as /replay + /show — uniform
  vocabulary across re-read / re-run / compare.
- Validation: needs ≥2 prior user turns, integer parse, range check,
  A==B guard, empty-reply guard ("cancelled / no reply captured").
- "(replies are identical)" message when difflib yields no lines
  (same prompt twice can produce identical streams).
- 45 slash commands now (added /diff).
- v1.6.50 milestone: 50 versions from v1.6.0 — 8h/12-ship operator
  iteration discipline still holding. CHANGELOG row count = 31.
- MANIFEST.json 1.6.49 → 1.6.50.
- `__init__.py __version__ = "1.6.50"`.

## v1.6.49 — 2026-05-22

**`/show <N>` — print the full prompt + reply for user-turn #N, with
visual separators. Companion to /history which truncates to 60 chars.**

- Same 1-indexed numbering as /replay so the operator vocabulary
  stays uniform: `/history` annotates `(replay:N)` → `/replay N`
  re-runs, `/show N` re-reads.
- Block layout:
  ```
  [/show] turn 3/7:
  ────── prompt ──────
  …full user text…
  ────── reply ──────
  …full assistant text…
  ────── end ──────
  ```
- Argument validation: integer parse + range check + empty-turns guard.
- Reply fallback text "(no reply captured)" for turns where claude
  failed mid-stream or was /cancel-ed before any output.
- 44 slash commands now (added /show).
- MANIFEST.json 1.6.48 → 1.6.49.
- `__init__.py __version__ = "1.6.49"`.

## v1.6.48 — 2026-05-22

**`/shortcuts` — operator-facing cheat sheet of every keyboard binding
+ click affordance.**

- Lists keyboard bindings (Ctrl+L clear, Ctrl+M collapse, F3 grep-next,
  Shift+F3 grep-prev, Esc cancel, Shift+Enter newline) + header click
  affordances (☆/★ pin, ▾/▸ collapse chevron, ✕ close).
- High discoverability for new operators. /help lists slash commands;
  /shortcuts lists the non-typed input surface.
- 43 slash commands now (added /shortcuts).
- MANIFEST.json 1.6.47 → 1.6.48.
- `__init__.py __version__ = "1.6.48"`.

## v1.6.47 — 2026-05-22

**Persistent state across resume: `/grep` pattern + `tags` chips now
survive close → re-open.**

- Resume-point JSON payload extended with `tags` (list) and
  `grep_pattern` (str). Both default-empty so the v1 schema stays
  back-compatible.
- `_restore_card_state_from_disk` reads both fields and:
  - rebuilds tag chips via `card._rebuild_tags()` (chip strip
    re-renders just like on first construction)
  - seeds `card._grep_pattern` and prints a hint:
    `▸ /grep pattern restored from last session: 'foo'`
    `  Type /grep (or just /grep) to re-apply highlights`
- `/grep` with no argument now re-applies the seeded pattern if
  present (instead of just printing usage). Workflow: close → re-open
  → operator types `/grep` once → highlights re-bind on the fresh
  scrollback as it streams.
- Why not auto-apply at restore time? On resume the terminal
  scrollback is empty until the first new reply streams. Re-applying
  an overlay against an empty document is a no-op, so we defer until
  operator triggers (or types /grep without args).
- MANIFEST.json 1.6.46 → 1.6.47.
- `__init__.py __version__ = "1.6.47"`.

## v1.6.46 — 2026-05-22

**`/replay <N>` — re-run user turn #N verbatim (1-indexed). /history
now annotates each user turn with `(replay:N)` so operator knows which
index to pass.**

- Filters `session.turns` for entries with a `user` field, stages the
  N-th into the input, and triggers `_on_send`. Doesn't pop history
  like /retry — replayed message becomes a fresh turn referring back
  to the prior context (claude --resume has the full server-side
  thread).
- Argument validation: integer parse, range check `1..len(user_turns)`,
  reject empty user text.
- /history pre-computes the user-turn index walking the full turns
  list so notes interleaved between user/assistant pairs don't
  confuse the replay numbering.
- 42 slash commands now (added /replay).
- MANIFEST.json 1.6.45 → 1.6.46.
- `__init__.py __version__ = "1.6.46"`.

## v1.6.45 — 2026-05-22

**`/tag <label>` + `/untag <label>` (or `/untag *`) — operator-defined
label chips in the card header. Also matched by `/find` so you can
search the fleet by tag.**

- New `AgentSession.tags: list[str]` dataclass field
  (`default_factory=list`). Stored on the session so resume-point JSON
  picks them up via the existing `dataclass_asdict` path.
- New header container `_tags_host` (hidden when empty), rebuilt by
  `_rebuild_tags()` which clears and re-adds purple-tinted chips
  (`color=PURPLE_PRIMARY, bg=rgba(191,90,242,30)`).
- `_focus_find` haystack now includes `" ".join(c.session.tags)` so
  `/find wip` jumps to any card tagged `wip`.
- `/tag` truncates to 24 chars; `/untag *` clears all; both call
  `_write_resume_point(save_reason="tag"|"untag")` immediately so
  the change survives a crash (same pattern as /rename).
- 41 slash commands now (added /tag + /untag).
- MANIFEST.json 1.6.44 → 1.6.45.
- `__init__.py __version__ = "1.6.45"`.

Also: shipped consolidated brain entry
`_shared-memory/knowledge/rkoj-runtime-ergonomics-cluster-v1.6.37-44-2026-05-22.md`
codifying 6 reusable patterns + 6 anti-patterns from the v1.6.37-44
mini-arc. _INDEX.md row added.

## v1.6.44 — 2026-05-22

**`/rename <new-name>` — change the agent display name on this card.
Pairs with v1.6.41 `/clone` so sibling cards become distinguishable.**

- Promoted the previously-local `title` QLabel to
  `self._title_label` so the intercept can call `setText` on it.
- Updates `session.agent_name`, refreshes the header title via
  `eve_label(new_name, "")`, and immediately writes a resume-point
  JSON with `save_reason="rename"` so the rename survives a crash.
- Truncates names longer than 60 chars to avoid pathological inputs.
- 39 slash commands now (added /rename).
- MANIFEST.json 1.6.43 → 1.6.44.
- `__init__.py __version__ = "1.6.44"`.

## v1.6.43 — 2026-05-22

**`/find-next` cycles through matches + bright purple flash on the
focused card so operator can see which one was selected.**

- **Flash**: new `AgentCard._flash_for_find(ms=1500)` applies a bright
  purple `QGraphicsDropShadowEffect` (blur=32, alpha=220) for 1.5s,
  then restores either the awaiting-input glow or no effect based
  on current `session.status`. Doesn't interfere with the persistent
  awaiting-input glow because it reads status at restore time.
- **/find-next**: re-runs the last `/find` query and advances to the
  next match (wraps). Prints `[/find-next] match 3/5 → …` so operator
  knows where they are.
- AgentsView now tracks `_last_find_query` + `_last_find_idx`.
- /find prints `match 1/N` too (uniform format with /find-next).
- 38 slash commands now (added /find-next).
- MANIFEST.json 1.6.42 → 1.6.43.
- `__init__.py __version__ = "1.6.43"`.

## v1.6.42 — 2026-05-22

**`/find <text>` — scroll the grid to a card matching project / agent /
pane_id substring. Friction-reducer for multi-card fleets.**

- New `find_requested(invoker_pane_id, query)` signal on AgentCard.
- AgentsView slot `_focus_find` searches every card's
  `project_display | agent_name | project_key | pane_id` haystack
  (case-insensitive substring) and calls
  `grid.ensureWidgetVisible(matched_card)` to scroll.
- Auto-expands the matched card if it was collapsed (no point
  scrolling to a 40-px-tall header strip).
- Feedback is echoed back to the *invoker*'s terminal, not the
  matched card — keeps operator in their typing context:
  `[/find] focused → Sinister Panel :: panel (pane_id=ab12cd34ef56)`
- 37 slash commands now (added /find).
- MANIFEST.json 1.6.41 → 1.6.42.
- `__init__.py __version__ = "1.6.42"`.

## v1.6.41 — 2026-05-22

**`/clone` (alias `/dup`) — spawn a sibling card with the same project
+ mode but a fresh session UUID.**

- Card emits new `clone_requested(project_key, mode)` signal which
  AgentsView wires to a lambda calling `self.spawn_agent(project_key,
  mode)`. No `session_uuid` passed → fresh session bootstraps normally
  (new pane_id, new heartbeat, new resume-points dir).
- Operator workflow: agent A is dialed in for project X with claude-opus,
  type `/clone`, get agent B with the same project + opus but no
  conversation history. Useful for running two parallel approaches on
  related tasks without re-picking from the New Agent dialog.
- 36 slash commands now (added /clone + alias /dup).
- MANIFEST.json 1.6.40 → 1.6.41.
- `__init__.py __version__ = "1.6.41"`.

## v1.6.40 — 2026-05-22

**`/note <text>` + `/notes` — contextual annotations interleaved in
the timeline, persisted with the session.**

- **/note <text>**: drops a dim `[HH:MM:SS] · note · <text>` line into
  the terminal. NOT sent to EVE. Stored on `session.turns` as
  `{"kind": "note", "ts": ISO, "text": ...}` so the resume-point JSON
  auto-serializes it via `_write_resume_point` and the note survives
  card close → resume.
- **/notes**: lists every note in this card with index + timestamp:
  `1. [2026-05-22 14:23:45] tried bumping retries to 5 — still flaky`
- **/history**: now renders notes inline with a distinct `··` marker
  (`  3. ·· tried bumping retries to 5`) so the conversation timeline
  reads chronologically without losing them in the user/assistant pair
  format.
- Existing filters on `t.get("user")` (in /retry + turn-pill count)
  already skip notes correctly — no other call sites needed updates.
- 35 slash commands now (added /note + /notes).
- MANIFEST.json 1.6.39 → 1.6.40.
- `__init__.py __version__ = "1.6.40"`.

## v1.6.39 — 2026-05-22

**Live `⏱ Xm Ys` elapsed-time pill in card header — passive companion
to v1.6.38 `/timer` + v1.6.37 `/cancel`.**

- New `_elapsed_pill` QLabel rendered next to the cost pill. Amber
  text (`#f0a020`), `JetBrains Mono`, 1px BORDER outline matching the
  other pills. Hidden by default.
- New `_elapsed_timer` QTimer at 1Hz; on each tick `_refresh_elapsed_pill`
  reads `_turn_started_ts` and updates the pill via `_fmt_duration`.
- `_on_send` calls `_start_elapsed()` after setting the start ts —
  pill is shown immediately at `⏱ 0.0s` and updates every second.
- `_on_finished` and `/cancel` both call `_stop_elapsed()` — pill
  vanishes the instant the turn completes. The `_last_turn_seconds`
  capture still happens for `/timer` queries.
- Operators no longer need to type `/timer` to see how long a turn
  has been running — it's right there in the header. Hung turns
  (e.g. 5m+ with no streaming) become eye-catching, so reaching
  for Esc / `/cancel` becomes reflexive.
- MANIFEST.json 1.6.38 → 1.6.39.
- `__init__.py __version__ = "1.6.39"`.

## v1.6.38 — 2026-05-22

**`/timer` — elapsed time for the in-flight turn (or last completed
duration when idle). Pairs with v1.6.37 `/cancel`.**

- Tracks `self._turn_started_ts` (monotonic) on every `_on_send` right
  before `proc.start()`. `_on_finished` and `/cancel` both freeze the
  duration into `self._last_turn_seconds` and clear the start ts.
- `/timer` reports three states:
  - in-flight: `[/timer] in-flight turn: 4m 17s elapsed (use /cancel
    or Esc to kill)`
  - idle w/ history: `[/timer] no active turn · last turn took 12.3s`
  - idle no history: `[/timer] no active turn · no completed turns yet`
- `/cancel` now appends elapsed: `[/cancel] turn cancelled after 4m 17s
  — session still resumable`.
- New `_fmt_duration()` static helper renders `<60s` as `Xs`, `<1h` as
  `Mm Ss`, else `Hh Mm`. None → `--`.
- 33 slash commands now (added /timer).
- MANIFEST.json 1.6.37 → 1.6.38.
- `__init__.py __version__ = "1.6.38"`.

## v1.6.37 — 2026-05-22

**`/cancel` + Esc keyboard shortcut — kill the in-flight turn cleanly
without taking down the card.**

- **/cancel**: kills the running `claude` QProcess, stops the spinner,
  applies markdown formatting to any partial output that already
  streamed, sets status back to `online`, and prints
  `[/cancel] turn cancelled — session still resumable`. Session UUID is
  preserved so the next message just `--resume`s normally.
- **Esc**: bound as a `QShortcut` on the card with
  `WidgetWithChildrenShortcut` context so it doesn't fight dialogs or
  global Esc handling. Routes to a `_cancel_if_running` guard that
  silently no-ops when no turn is in-flight (Esc-mashing in idle cards
  isn't noisy).
- Replaces the previous "wait for Claude to finish a runaway tool loop"
  workaround. Operator can now stop a turn the same way they would in
  a normal terminal (Ctrl+C / Esc).
- 32 slash commands now (added /cancel).
- MANIFEST.json 1.6.36 → 1.6.37.
- `__init__.py __version__ = "1.6.37"`.

## v1.6.36 — 2026-05-22

**F3 / Shift+F3 keyboard shortcuts for /grep cycling + `/minimize-all` +
`/expand-all` bulk-toggle slash commands.**

- **F3 / Shift+F3**: cycle through /grep matches without touching the
  command line. Bound as global `QShortcut` on AgentCard; both call the
  new `_grep_cycle(direction, verbose=False)` helper so they share state
  + wrap-around with the slash commands. When no /grep is active, the
  shortcuts silently no-op (only the slash forms surface the empty-state
  hint, since they were invoked deliberately).
- **/minimize-all + /expand-all**: bulk-toggle every card's collapse
  state. Card emits `minimize_all_requested` / `expand_all_requested`;
  AgentsView wires them to `collapse_all()` / `expand_all()` which
  iterate `_cards.values()` and call each card's `_toggle_collapsed()`
  only when its current state would change (idempotent). Each prints
  `collapsed N card(s)` / `expanded N card(s)` to the invoking terminal.
- /grep-next + /grep-prev descriptions now mention F3 / Shift+F3 in
  the slash autocomplete so the keyboard binding is discoverable.
- 29 slash commands now (added /expand-all + /minimize-all).
- MANIFEST.json 1.6.35 → 1.6.36.
- `__init__.py __version__ = "1.6.36"`.

## v1.6.35 — 2026-05-22

**`/grep-next` + `/grep-prev` + project-color legend in empty state.**

- **/grep-next + /grep-prev**: cycle through /grep matches without
  re-typing the pattern. `/grep` now stores match cursor positions in
  `self._grep_positions: list[int]` + index `self._grep_idx`. /grep-next
  increments (wraps to first); /grep-prev decrements (wraps to last).
  Each prints `match N / M for '<pattern>'`. Empty-state guard tells
  operator to run /grep first.
- **Project-color legend in empty state**: a row of color-chips at the
  bottom of the AgentsView empty-state, mapping each curated palette
  color to its project display name. So `🟢 Sinister Panel` /
  `🟡 Snap Emulator API` / etc. are self-documenting. Hidden when no
  curated-palette projects are registered (projects.json fallback).
- 27 slash commands now (added /grep-next + /grep-prev).
- MANIFEST.json 1.6.34 → 1.6.35.
- `__init__.py __version__ = "1.6.35"`.

## v1.6.34 — 2026-05-22

**`/grep <pattern>` + `/grep-clear`** — highlight matching text in the
terminal scrollback (yellow background) without damaging the existing
char-format layers (markdown code-fences from v1.6.16, dim timestamp
gutter from v1.6.25).

- Uses `QTextEdit.ExtraSelection` as an OVERLAY rather than modifying
  document char-formats — so /grep-clear can wipe highlights without
  nuking the markdown / dim-gutter styling underneath.
- Walks the document with `QTextDocument.find()` in a loop, building
  one `ExtraSelection` per match. Passes the full list to
  `self.terminal.setExtraSelections(extras)`.
- Scrolls the FIRST match into view via `setTextCursor(first_match)`.
- `/grep-clear` calls `setExtraSelections([])` — empties the overlay.
- 25 slash commands now (added /grep + /grep-clear).
- MANIFEST.json 1.6.33 → 1.6.34.
- `__init__.py __version__ = "1.6.34"`.

## v1.6.33 — 2026-05-22

**`/copy` + per-card project-color left stripe.**

- **/copy slash command**: copies the most recent EVE reply to the OS
  clipboard (via `QApplication.clipboard().setText(...)`). Operator
  can paste into PR descriptions / Obsidian notes / Slack without
  manually selecting text inside the QPlainTextEdit. Prints char count
  + 60-char preview as confirmation. Handles "no reply yet" + empty-
  reply cases. 23 slash commands now.
- **Per-card project-color stripe**: each AgentCard's left border is
  now a 3px project-tinted line. Sanctum=purple, Panel=green,
  Kernel-APK=amber, Snap=yellow, TikTok=red, Bumble=honey, etc.
  Curated palette for 13 known projects + deterministic HSV-from-hash
  fallback (so new projects get a stable color across runs). Operator
  scans colors to know "that's the Panel one" without reading labels.
- New module-level helpers: `_PROJECT_COLORS` dict + `_project_color()`
  function. AgentCard.__init__ applies via per-instance `setStyleSheet`
  override of `border-left` only — preserves the hairline border /
  card bg / radius from the global QSS rule.
- MANIFEST.json 1.6.32 → 1.6.33.
- `__init__.py __version__ = "1.6.33"`.

## v1.6.32 — 2026-05-22

**`/ping [<project>]` status-check fan-out + brain entry for v1.6.27-31.**

- **`/ping`**: canned 60-word-cap status request fanned to all live
  cards. Optional `<project>` arg filters to one project's cards.
  Reuses the v1.6.30 broadcast pipeline via a sentinel-prefix
  message `__PING_PROJECT__<key>__:<body>`; AgentsView.broadcast
  parses the sentinel + applies project filter before fanning.
- Registered in SLASH_COMMANDS → 22 commands.
- **Brain entry**: `rkoj-polish-cluster-v1.6.27-31-2026-05-22.md`
  consolidates the 5-iteration arc (collapse + pin + operator-actions +
  /broadcast + persisted-resume-state). 5 reusable patterns codified
  (card-level state toggles with min/max-height swap, signal-driven
  cross-component sync, markdown action-queue parser, fan-out via
  setPlainText+singleShot, resume state restoration from latest
  saved_at). 8 anti-patterns. Indexed in `_INDEX.md`.
- MANIFEST.json 1.6.31 → 1.6.32.
- `__init__.py __version__ = "1.6.32"`.

## v1.6.31 — 2026-05-22

**Persisted pin state + cumulative cost on resume + /usage per-mode breakdown.**

- **Resume preserves pin state**: `_write_resume_point` payload now
  carries `pinned: bool`. `AgentsView.spawn_agent` with `session_uuid`
  scans the latest matching JSON via `_restore_card_state_from_disk()`,
  calls `card._toggle_pin()` if it was pinned. Pin survives close →
  re-open from Sessions picker.
- **Resume preserves cumulative cost**: same helper restores
  `_total_cost_usd` / `_total_in_tokens` / `_total_out_tokens` and
  updates the header cost pill. A resumed conversation no longer
  reads `$0.0000` — it picks up where it left off.
- **/usage per-mode breakdown**: new "By model" section under the
  per-project totals when there's a non-claude mode in play, or
  multiple modes. Shows `claude` / `claude-haiku` / `claude-opus`
  sessions + cost + tokens. Operator sees which model is eating
  budget without digging into individual saves.
- MANIFEST.json 1.6.30 → 1.6.31.
- `__init__.py __version__ = "1.6.31"`.

## v1.6.30 — 2026-05-22

**`/broadcast <msg>` — fan a prompt to all live cards.** Operator wants
the same question answered by every active EVE across projects? Type
`/broadcast what's your status` in any card → every other card stages
the message + fires `_on_send`. Each card runs through its own spinner
+ streaming + cost path uniformly.

- `AgentCard` gets `broadcast_requested(str)` pyqtSignal (emits the
  message body without the `/broadcast ` prefix).
- `_maybe_intercept` handles `/broadcast` — splits off prefix, emits
  signal with body. Empty body → usage hint.
- `AgentsView.broadcast(msg) -> int` fans the message to every card:
  for each, `setPlainText(msg)` + cursor-to-end + `QTimer.singleShot(0,
  card._on_send)` so the regular flow runs. Returns count of cards
  reached.
- Skips cards mid-turn (process state != NotRunning) so we don't queue
  a clobber while EVE is still responding to the prior message.
- Registered in `SLASH_COMMANDS` (now 21 commands).
- MANIFEST.json 1.6.29 → 1.6.30.
- `__init__.py __version__ = "1.6.30"`.

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
