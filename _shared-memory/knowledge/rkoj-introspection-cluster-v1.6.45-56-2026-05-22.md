<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Author: RKOJ-ELENO :: 2026-05-22

# RKOJ v1.6.45 → v1.6.56 introspection cluster — tags · history · diff · export-all · summarize · uptime · forget-last

**Status:** doctrine, implemented
**Composes with:** `rkoj-runtime-ergonomics-cluster-v1.6.37-44-2026-05-22`, `rkoj-polish-cluster-v1.6.27-31-2026-05-22`, `rkoj-polish-cluster-v1.6.20-25-2026-05-22`, `rkoj-stream-json-jcode-parity-2026-05-22`, `rkoj-session-continuity-pattern-2026-05-21`, `agent-identity-eve`, `forever-expanding-modular-architecture-doctrine`.

---

## TL;DR

After v1.6.37–44 filled the runtime ergonomics gap (`/cancel`/Esc, /timer,
live elapsed pill, /note, /clone, /find, /rename), v1.6.45–56 turned RKOJ
into a self-introspecting workstation. Operators can now label cards
(`/tag` + clickable chips → /find), navigate conversations by index
(`/show <N>`, `/replay <N>`, `/diff <A> <B>`), inspect operational state
(`/uptime`, /stats, /timer, /shortcuts), summarize with EVE (`/summarize`),
batch-export the fleet (`/export-all`), and edit history (`/forget-last`).
Tags + grep state now persist across resume.

12 versions × ~25-min /loop ticks (one carrying a 50-slash milestone +
the v1.6.50 build-version milestone) = a coherent introspection layer.
Operator vocabulary now hits 50 verbs.

## What landed

| ver | Win | Why it matters |
|---|---|---|
| 1.6.45 | `/tag` + `/untag` chips | `AgentSession.tags: list[str]` field. Purple-tinted chip group in header (hidden when empty), persisted via resume-point JSON. `/untag *` clears all. /find haystack extended with tags |
| 1.6.46 | `/replay <N>` | Re-run user turn #N verbatim. Doesn't pop history (unlike /retry). /history annotates each user turn `(replay:N)` so operator knows the index |
| 1.6.47 | Persistent /grep + tags across resume | Resume-point JSON adds `grep_pattern` + `tags`. On restore: tags rebuild via `_rebuild_tags`, grep pattern seeds `_grep_pattern` (deferred re-apply since scrollback is fresh). `/grep` with no arg reuses seeded pattern |
| 1.6.48 | `/shortcuts` cheat sheet | Keyboard bindings (Ctrl+L, Ctrl+M, F3, Shift+F3, Esc, Shift+Enter) + click affordances (☆/★ pin, ▾/▸ collapse, ✕ close). Complements /help (typed commands) |
| 1.6.49 | `/show <N>` | Full prompt+reply text for user-turn N with `── prompt ──` / `── reply ──` separators. 1-indexed numbering uniform with /replay |
| 1.6.50 | `/diff <A> <B>` — milestone | `difflib.unified_diff` (stdlib), n=2 context, `reply #A` / `reply #B` headers. Pairs with /clone: run same prompt in sibling cards, /diff sees how models diverged. v1.6.0→v1.6.50 in ~14h of /loop ticks |
| 1.6.51 | `/tags` fleet census | Cross-card walk via `tags_census_requested` signal. `defaultdict(list)` of tag → [project:agent_name]. Sorted alphabetical output echoed to invoker |
| 1.6.52 | Clickable tag chips | New `_TagChip(QLabel)` subclass with `PointingHandCursor` + `mousePressEvent` emitting `find_requested`. Every chip becomes a /find <tag> hot-spot, repeated clicks cycle through matches |
| 1.6.53 | `/summarize` TL;DR | Stages structured 4-section ask (goal/working/blocked/next) into input + triggers `_on_send`. Empty-turns guard. Uses standard stage-then-send pattern so spinner/streaming/cost run uniformly |
| 1.6.54 | `/uptime` | Card lifetime + turn count + last-activity-ago + current state. `_spawn_ts` set at __init__; `_last_send_ts` updated in `_on_send`. Reuses `_fmt_duration` helper from v1.6.38 |
| 1.6.55 | `/export-all` bundle | Refactored /export body into `_export_to_markdown(target_dir)` method. `export_all_requested` signal fans to AgentsView slot writing every card's transcript to `_shared-memory/rkoj-qt/exports/<ts>-bundle/`. Notes export as markdown blockquotes |
| 1.6.56 | `/forget-last` — 50-slash milestone | Walks `session.turns` backwards skipping notes, pops first user-keyed dict. Refreshes turn-pill + writes resume-point `save_reason="forget-last"`. Clear caveat: claude --resume retains the turn server-side |

## Patterns codified

### 1. Card → AgentsView signal fan-out becomes the dominant extensibility surface

Every new "fleet command" (commands that need cross-card data) follows this shape:

```python
# AgentCard side
some_thing_requested = pyqtSignal(str)  # invoker_pane_id

if head == "/foo":
    self.some_thing_requested.emit(self.session.pane_id)
    return True

# AgentsView wiring in spawn_agent
card.some_thing_requested.connect(self._foo_slot)

# AgentsView slot
def _foo_slot(self, invoker_id: str) -> None:
    invoker = self._cards.get(invoker_id)
    if invoker is None: return
    # ... walk self._cards.values(), compute, echo to invoker
    invoker._append_terminal("[/foo] result …\n")
```

This cluster added 4 more signals using this exact shape:
`clone_requested`, `find_requested`, `tags_census_requested`,
`export_all_requested`. The `echo to invoker` discipline is critical —
operator stays in their typing context.

### 2. 1-indexed user-turn numbering invariant

`/replay <N>`, `/show <N>`, `/diff <A> <B>`, `/history (replay:N)` all
filter via `[t for t in session.turns if t.get("user")]` and 1-index
into that filtered list. Notes interleave but don't count. Operator
vocabulary is uniform across re-read / re-run / compare.

```python
user_turns = [t for t in self.session.turns if t.get("user")]
if idx < 1 or idx > len(user_turns):
    self._append_terminal(f"out of range (1..{len(user_turns)})\n")
    return True
target = user_turns[idx - 1]
```

Always validate range + integer-parse + empty-state guards.

### 3. Resume-point JSON additive schema

`pinned` (v1.6.31) → `tags` (v1.6.47) → `grep_pattern` (v1.6.47).
Each new field defaults to empty in the dataclass + the writer, so
older saves load cleanly into newer code. The restore reader uses
`.get(key, default)` for the same reason.

The schema-version stays at `sinister.resume-point.v1` — additive
changes don't bump it. Bump only on **structural** changes that break
the reader (e.g. renaming `turns` to `entries` would force v2).

### 4. Click-to-jump via QLabel subclass

```python
class _TagChip(QLabel):
    def __init__(self, text, card):
        super().__init__(text)
        self._card = card
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._card.find_requested.emit(self._card.session.pane_id, self.text())
        super().mousePressEvent(ev)
```

Same shape works for any future chip: cost-pill click → /cost output,
elapsed-pill click → /timer, project-label click → /find <project>.

### 5. `_fmt_duration` as the shared duration formatter

`/timer`, `/cancel` ("after Xm Ys"), header elapsed pill, `/uptime`
all use the same `_fmt_duration(seconds)`: `<60s` → `Xs`; `<1h` →
`Mm Ss`; else `Hh Mm`. None → `--`. Centralizing in a `@staticmethod`
keeps duration output uniform across the UI.

### 6. Body-extracted methods enable fan-out

`/export`'s inline body became `_export_to_markdown(target_dir)`
(v1.6.55) so `/export-all` in AgentsView could call it on every card.
General rule: **if a slash command does substantive work, extract a
private method.** Future fleet-wide siblings come for free.

Also applies to: `_grep_cycle` (extracted v1.6.36 for F3 reuse),
`_export_to_markdown` (v1.6.55), `_cancel_if_running` (v1.6.37 for
Esc-vs-/cancel split), `_rebuild_tags` (v1.6.45).

### 7. Auto-generating /help kills doc rot

`/help` used to hardcode 14 commands; with 50 commands shipped the
list drifted. v1.6.57 fixed `/help` to iterate `SLASH_COMMANDS`
sorted alphabetically with `max(len(cmd))` width alignment. Adding
a registry row is the only step to ship a new slash command.

## Anti-patterns avoided

1. **Don't broadcast a slash command.** /broadcast stages into
   `card.input` + calls `_on_send`, which routes through
   `_maybe_intercept`. So `/broadcast /export` might work — but the
   semantics are confused. Build a dedicated fleet-wide command
   (`/export-all`, `/tags`) with its own signal.
2. **Don't echo /find results to the matched card.** Echo to the
   invoker. Operator typing context > target side feedback.
3. **Don't manipulate claude --resume's server-side history.**
   /forget-last only edits local state; clarify in the operator
   feedback so expectations match.
4. **Don't write Notes to a sidecar.** Use `session.turns` with
   `kind="note"` — extends the same JSON, surfaces in /history +
   /export automatically.
5. **Don't bump schema-version for additive resume-point fields.**
   `.get(key, default)` on read covers it.
6. **Don't grab Esc / Ctrl+C globally for cancel.** Use
   `WidgetWithChildrenShortcut` scoping (v1.6.37 lesson reaffirmed).
7. **Don't manually keep /help in sync.** Auto-generate from registry.

## Cumulative slash command count + signal count

- v1.6.26 baseline: 21 slashes / 2 signals
- v1.6.36 (F3 cluster): 32 slashes / 5 signals
- v1.6.44 (ergonomics cluster): 39 slashes / 6 signals
- v1.6.56 (this cluster): **50 slashes / 8 signals**

Signals on AgentCard now: `closed`, `status_changed`, `pin_changed`,
`broadcast_requested`, `minimize_all_requested`, `expand_all_requested`,
`clone_requested`, `find_requested`, `tags_census_requested`,
`export_all_requested`.

## Header pill inventory

status_dot · project_label · title · mode_pill · turn_pill · cost_pill ·
elapsed_pill (v1.6.39, hidden when idle) · tag chips (v1.6.45, hidden
when empty) · pin star · collapse chevron · close X.

## What's next (queued for v1.6.57+)

- `/help` auto-generation (LANDED in v1.6.57 alongside this brain entry)
- Color-per-tag instead of all-purple chips
- Tag chip overflow / wrap to second line
- Fleet-wide `/summarize-all` (TL;DR over every card's conversation)
- `/jump <pattern>` cursor-only navigation (no highlight overlay)
- Persistent operator-typed text across resume (input drafts)

## Operator iteration takeaway

v1.6.37–44 (runtime ergonomics) + v1.6.45–56 (introspection) = **20
shippable iterations in ~7 hours of /loop ticks**, each adding a
verb to operator vocabulary AND wiring it through the existing signal
mesh. The 25-min cadence held perfectly: every iteration produces
one ship, one CHANGELOG entry, one push. Brain entries every ~8–12
versions consolidate patterns without disrupting the ship cadence.

**Single-thread iteration discipline wins when:** each iteration is
< 25 min of execution, the signal mesh is the dominant extensibility
surface, ship-and-update is faster than plan-and-batch.
