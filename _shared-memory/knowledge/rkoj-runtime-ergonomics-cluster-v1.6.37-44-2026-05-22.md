<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Author: RKOJ-ELENO :: 2026-05-22

# RKOJ v1.6.37 → v1.6.44 runtime ergonomics cluster — cancel · timer · note · clone · find · rename

**Status:** doctrine, implemented
**Composes with:** `rkoj-polish-cluster-v1.6.27-31-2026-05-22`, `rkoj-polish-cluster-v1.6.20-25-2026-05-22`, `rkoj-stream-json-jcode-parity-2026-05-22`, `rkoj-session-continuity-pattern-2026-05-21`, `agent-identity-eve`, `forever-expanding-modular-architecture-doctrine`.

---

## TL;DR

After v1.6.27–31 made RKOJ a "multi-card workstation," v1.6.32–36 cleaned
the message stream (markdown, /grep, dim gutter), and v1.6.36 added F3
grep cycling + bulk collapse. The v1.6.37–44 cluster filled the next
operator gap: **mid-turn control + per-card identity + multi-card
navigation**. Operators can now stop runaway turns (`/cancel`/Esc), see
how long they've been running at a glance (live elapsed pill + /timer),
annotate the timeline without sending to EVE (/note), fork a productive
setup (/clone), rename + label cards so siblings are distinguishable
(/rename), and navigate large fleets with /find + /find-next + a purple
flash highlight.

8 versions × ~25-min /loop ticks = ~3.3 hours of self-paced ergonomics
fill. Operator `/loop keep going make it better` drove the whole cluster.

## What landed

| ver | Win | Why it matters |
|---|---|---|
| 1.6.37 | `/cancel` + Esc kill in-flight turn | `_proc.kill()` + waitForFinished + restore status to `online`. Markdown applied to partial stream. Session UUID preserved so next message just `--resume`s. Esc bound as `QShortcut(WidgetWithChildrenShortcut)` routes to `_cancel_if_running` (silent no-op when idle) |
| 1.6.38 | `/timer` reports elapsed | `_turn_started_ts: float | None` set right before `proc.start()`. `_on_finished` + `/cancel` freeze into `_last_turn_seconds`. Static `_fmt_duration` helper: `<60s` → `Xs`; `<1h` → `Mm Ss`; else `Hh Mm` |
| 1.6.39 | Live elapsed-time pill | New header `_elapsed_pill: QLabel` (amber `#f0a020`, JetBrains Mono) + `QTimer` at 1Hz. `_start_elapsed()` shown in `_on_send`; `_stop_elapsed()` in `_on_finished` + `/cancel`. Hung turns become eye-catching so Esc/cancel reflex emerges without typing /timer |
| 1.6.40 | `/note` + `/notes` annotations | Notes stored as `{"kind": "note", "ts": ISO, "text": ...}` on `session.turns`. Existing `t.get("user")` filters in /retry + turn-pill already skip notes correctly. /history renders inline with `··` marker. Resume-point serializes automatically |
| 1.6.41 | `/clone` spawns sibling card | New `clone_requested(project_key, mode)` signal on AgentCard. AgentsView wires lambda → `spawn_agent(pk, m)`. Fresh UUID, no history. Lets operator fork an in-tune setup without re-picking from New Agent dialog |
| 1.6.42 | `/find <text>` scrolls to match | `find_requested(invoker_id, query)` signal. AgentsView `_focus_find` searches `project_display|agent_name|project_key|pane_id` haystack (case-insensitive substring), auto-expands collapsed match, calls `grid.ensureWidgetVisible`. Feedback echoes to invoker not match — operator stays in typing context |
| 1.6.43 | `/find-next` + flash | `_last_find_query` + `_last_find_idx` on AgentsView. Empty-query signal payload = "advance". New `AgentCard._flash_for_find(ms=1500)` applies bright purple `QGraphicsDropShadowEffect` then restores awaiting-input glow or no effect based on `session.status` at restore time |
| 1.6.44 | `/rename <new-name>` | Promoted local `title` QLabel to `self._title_label`. Updates `session.agent_name` + `setText(eve_label(...))` + immediate `_write_resume_point(save_reason="rename")` so rename survives crash. 60-char truncation. Pairs with /clone so siblings distinguish |

## Patterns codified

### 1. Card → AgentsView signal pattern (the "fleet command" pattern)

Three slash commands now follow this shape:

```python
# AgentCard:
clone_requested = pyqtSignal(str, str)   # project_key, mode
find_requested  = pyqtSignal(str, str)   # invoker_pane_id, query
broadcast_requested = pyqtSignal(str)    # message body

if head == "/clone":
    self.clone_requested.emit(self.session.project_key, self.session.mode)
    return True

# AgentsView (in spawn_agent):
card.clone_requested.connect(
    lambda pk, m: self.spawn_agent(project_key=pk, mode=m)
)
card.find_requested.connect(self._focus_find)
card.broadcast_requested.connect(self.broadcast)
```

Slot **always echoes feedback to the invoker**, not to the target card.
That keeps operator's eyes on the card they're typing in.

### 2. Mid-turn lifecycle hook trio: start / freeze / stop

Three state slots get touched in lockstep on every turn:

```python
# _on_send (start):
self._turn_started_ts = time.monotonic()   # for /timer
self._start_elapsed()                      # for live pill
self._set_status("busy")

# _on_finished (natural end):
if self._turn_started_ts is not None:
    self._last_turn_seconds = time.monotonic() - self._turn_started_ts
    self._turn_started_ts = None
self._stop_elapsed()
self._set_status("online")

# /cancel (forced kill — same freeze pattern, plus markdown):
elapsed = time.monotonic() - self._turn_started_ts
self._last_turn_seconds = elapsed
self._turn_started_ts = None
self._proc.kill(); self._proc.waitForFinished(1500)
self._stop_thinking(); self._stop_elapsed()
self._apply_markdown_format(self._reply_start_pos, end_pos)
self._set_status("online")
```

The "freeze then act" ordering matters — UI work and child-process
shutdown should NOT race the duration snapshot.

### 3. Keyboard shortcut scoping for top-level windows

`Esc` is high-collision in Qt (closes dialogs, exits modal popups).
Solved by scoping the shortcut to the card:

```python
from PyQt6.QtCore import Qt as _Qt
_esc = QShortcut(QKeySequence("Esc"), self,
                 activated=self._cancel_if_running)
_esc.setContext(_Qt.ShortcutContext.WidgetWithChildrenShortcut)
```

`WidgetWithChildrenShortcut` ensures Esc fires only when focus is inside
the card or its children — dialogs above the card swallow Esc first.

### 4. Non-destructive effect overlay

`/find` flash temporarily applies a brighter `QGraphicsDropShadowEffect`
without nuking the persistent awaiting-input glow. The restore-callback
reads `session.status` at fire time and decides whether to re-apply the
glow or clear the effect entirely:

```python
def _flash_for_find(self, ms: int = 1500) -> None:
    eff = QGraphicsDropShadowEffect(self)
    eff.setBlurRadius(32); ...; self.setGraphicsEffect(eff)
    def _restore():
        if self.session.status == "awaiting-input":
            self._apply_glow()
        else:
            self._remove_glow()
    QTimer.singleShot(ms, _restore)
```

Same trick works for any "transient visual" overlay (notify-on-completion
flash, error-shake, etc.).

### 5. Session-turns schema extension

session.turns is a `list[dict]` and was historically `{"user": ..., "assistant": ...}`. v1.6.40 added a third shape:

```python
{"kind": "note", "ts": "2026-05-22T10:23:45", "text": "..."}
```

Worked WITHOUT touching:
- `/retry` (uses `t.get("user")` — notes have no user key → skipped)
- turn-pill count (same filter)
- /history (extended with `t.get("kind") == "note"` branch)
- `_write_resume_point` (serializes whole list — schema-agnostic)

The pattern: **extend `session.turns` with a new `kind` rather than
adding parallel list fields.** Keeps the JSON one shape, downstream
filters opt into new kinds explicitly.

### 6. Immediate-persist on mutation (the "rename" pattern)

For mutations operator expects to survive crashes (rename, pin, mode
change), call `_write_resume_point(save_reason="<verb>")` synchronously
inside the intercept rather than waiting for `_on_close` autosave.
`save_reason` field in the JSON makes the audit trail readable.

## Anti-patterns avoided

1. **Don't grab Esc globally.** Use `WidgetWithChildrenShortcut`.
2. **Don't grab Ctrl+C as cancel.** It collides with QTextEdit copy.
3. **Don't write notes to a separate sidecar file.** Resume-point
   serializes `session.turns` already — extend the schema.
4. **Don't auto-show "no active turn" on Esc-mash.** Silent no-op when
   idle keeps the UI quiet.
5. **Don't echo /find results to the matched card.** Echo to the
   invoker so operator stays in typing context.
6. **Don't double-track elapsed time.** One `_turn_started_ts` slot
   feeds both /timer and the live pill.

## Cumulative slash command count

- v1.6.26 baseline: 21
- v1.6.36 (F3 cluster): 32
- v1.6.44 (this cluster): **39**

The header pills also grew: status dot + project label + title + mode
+ turn-count + cost + **elapsed** (v1.6.39, hidden when idle).

## What's next (queued for v1.6.45+)

- `/tag <label>` — small colored badge in card header, /find-able
- Persistent /grep across resume (write `_grep_pattern` to resume-point)
- `/diff <a> <b>` — compare two replies side-by-side
- `/replay <N>` — re-run a specific previous turn by index
- `/jump-to <ts>` — scroll to a specific timestamp gutter line

## Operator iteration takeaway

This cluster reinforces the v1.6.27–31 finding: **8 ships × 25 min ≈
3.5 hours produces a coherent UX layer** when each iteration adds one
verb to operator vocabulary AND wires it through the existing signal
mesh. The signal mesh (card → AgentsView fan-out) is now the dominant
extensibility surface — every new "fleet command" follows the same
shape (signal on AgentCard, slot on AgentsView, feedback to invoker).
