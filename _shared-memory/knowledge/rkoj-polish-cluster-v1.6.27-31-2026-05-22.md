<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Author: RKOJ-ELENO :: 2026-05-22

# RKOJ v1.6.27 → v1.6.31 polish cluster — collapse · pin · operator-actions · broadcast · resume-state

**Status:** doctrine, implemented
**Composes with:** `rkoj-polish-cluster-v1.6.20-25-2026-05-22`, `rkoj-stream-json-jcode-parity-2026-05-22`, `rkoj-session-continuity-pattern-2026-05-21`, `agent-identity-eve`, `forever-expanding-modular-architecture-doctrine`.

---

## TL;DR

After the v1.6.20-25 telemetry+ergonomics cluster + the v1.6.26 status-bar
live-count fix, v1.6.27–31 layered five interaction patterns that turn RKOJ
from "single-card chat" into "multi-card workstation": **card collapse**
(stack 5+ cards compactly), **pin/star** (favorites float to top),
**operator-actions in empty state** (Sanctum-wide to-do visible at spawn),
**/broadcast** (fan one prompt across all live cards), **persisted card state
across resume** (pin + cumulative cost survive close + re-open).

Each shippable in one /loop tick (~25 min cadence). Operator
`/loop keep going make it better` drove the whole cluster.

## What landed

| ver | Win | Why it matters |
|---|---|---|
| 1.6.27 | Card collapse toggle | Header strip + `▾/▸` chevron. Toggles via button or `Ctrl+M`. Hides terminal + thinking label + input + send. Min-height 280→40, max-height ∞→54. Streaming continues invisibly so operator can collapse a chatty card + still get the cost-pill tick |
| 1.6.28 | Per-card pin/star | `AgentSession.pinned: bool` field. `☆` (gray) → `★` (purple) button. `pin_changed(pane_id)` signal → AgentsView re-sorts grid with key `(not pinned, project_key, created_at)`. `/pin` slash mirrors button click |
| 1.6.29 | Operator-actions urgent rows in empty state | Markdown parser for `_shared-memory/OPERATOR-ACTION-QUEUE.md`. Finds `## 🔴 Critical` / `## 🟠 High` sections + matches `- [ ] **Title** — description` within. Top 3 surface as severity-tinted rows in the empty state. Auto-refreshes on `_rebuild_grid` |
| 1.6.30 | `/broadcast <msg>` fan-out | New `broadcast_requested(str)` signal on AgentCard. `AgentsView.broadcast(msg)` stages message into every card's input + fires `_on_send` via `QTimer.singleShot(0, ...)`. Skips cards mid-turn (no clobbering in-flight EVE response) |
| 1.6.31 | Persisted card state across resume | `_write_resume_point` payload +`pinned: bool`. `_restore_card_state_from_disk(card, session_uuid)` scans newest matching JSON + restores pin (via `card._toggle_pin()`) AND cumulative cost telemetry. Resume picks up where you left off |
| 1.6.31 | `/usage` per-mode breakdown | Groups saved sessions by `mode` (claude / claude-haiku / claude-opus), prints sessions + cost + tokens in a "By model" footer section |

## Patterns codified

### 1. Card-level state toggles (collapse + pin)

Both follow a common shape:

```python
# 1. Instance attr (default OFF):
self._collapsed: bool = False

# 2. Button in header strip:
self._collapse_btn = QPushButton("▾")  # or "☆" for pin
self._collapse_btn.clicked.connect(self._toggle_collapsed)

# 3. Toggle method flips bool + visuals + Qt-layout state:
def _toggle_collapsed(self) -> None:
    self._collapsed = not self._collapsed
    self.terminal.setVisible(not self._collapsed)
    self.input.setVisible(not self._collapsed)
    self.send_btn.setVisible(not self._collapsed)
    self._collapse_btn.setText("▸" if self._collapsed else "▾")
    if self._collapsed:
        self.setMinimumHeight(40); self.setMaximumHeight(54)
    else:
        self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        self.setMinimumHeight(280)

# 4. Keyboard shortcut for power users:
QShortcut(QKeySequence("Ctrl+M"), self, activated=self._toggle_collapsed)
```

The Qt min/max-height swap is what actually changes the layout — visibility
toggles alone don't shrink the widget. `QWIDGETSIZE_MAX` (16777215) is Qt's
"unset" sentinel.

### 2. Signal-driven cross-component sync

For pin (and earlier, cards_changed in v1.6.23), the source-of-truth widget
emits a signal; sibling widgets that need to react listen:

```python
# AgentCard:
pin_changed = pyqtSignal(str)  # pane_id

# AgentsView wires on spawn:
card.pin_changed.connect(lambda *_: self._rebuild_grid())

# _rebuild_grid sort key uses the source:
cards.sort(key=lambda c: (not c.session.pinned, c.session.project_key, ...))
```

No polling, no manual notify; the signal is the contract.

### 3. Markdown action-queue parser

`_scan_urgent_actions()` reads `OPERATOR-ACTION-QUEUE.md` and extracts
unchecked items under `🔴 Critical` / `🟠 High` sections.

Two regexes:

```python
section_re = re.compile(r"^##+\s*(🔴|🟠)\s*(\w+)", re.IGNORECASE)
item_re    = re.compile(r"^-\s+\[\s\]\s+(?:(🔴|🟠)\s+)?\*\*([^*]+)\*\*(?:\s*[—-]\s*(.*))?")
```

Tracks `current_severity` from the most recent section header; inline
emoji on the item itself overrides it. Stops at `limit` matches.

Render: severity-tinted left border (red for critical, amber for high) +
emoji + bold title (white) + 140-char detail preview (muted gray) in a
single QLabel with `Qt.TextFormat.RichText`.

### 4. Fan-out via SetPlainText + QTimer.singleShot

`/broadcast` and `/skill` both use the same pattern to re-use the normal
send pipeline (spinner + streaming + cost) instead of duplicating it:

```python
def broadcast(self, msg: str) -> int:
    n = 0
    for card in self._cards.values():
        if (card._proc is not None and
                card._proc.state() != QProcess.ProcessState.NotRunning):
            continue  # skip mid-turn cards
        card.input.setPlainText(msg)
        cur = card.input.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        card.input.setTextCursor(cur)
        QTimer.singleShot(0, card._on_send)
        n += 1
    return n
```

The 0ms timer defers `_on_send` to the next event-loop tick so the
`setPlainText` insert has rendered before the spinner appears. Without
the deferral, the input flickers between empty and filled.

### 5. Resume state restoration from latest disk save

`_restore_card_state_from_disk(card, session_uuid)` walks every JSON in
`_shared-memory/resume-points/EVE on */` looking for one matching the
session_uuid. Among matches, takes the one with the latest `saved_at`
timestamp (string compare works because ISO8601 sorts lexically).

```python
latest_ts = ""
latest_data = None
for fp in glob:
    d = json.load(fp)
    if d.get("session_uuid") != session_uuid:
        continue
    ts = d.get("saved_at", "")
    if ts > latest_ts:
        latest_ts = ts; latest_data = d
```

Then restores fields. Pin uses `card._toggle_pin()` (not a direct attr
write) so the button visual + signal both update.

Why latest, not highest cost: latest is more recent operator intent
(unpin would lower cost too). Highest-cost is used in `/usage` for a
different reason: cost is cumulative so the latest save SHOULD have the
highest, but we use max as a safety net against partial writes.

## Anti-patterns

| # | Anti-pattern | Why bad |
|---|---|---|
| 1 | Card collapse with `setVisible(False)` only (no min/max-height swap) | The widget still occupies its full minimum height in the parent layout — empty space gap. Min-height swap is what shrinks the slot |
| 2 | Pin state stored as widget property only | Lost on resume. Must live in `AgentSession` dataclass so it's serializable + survives close + re-open |
| 3 | `/broadcast` that hijacks the operator's input box without canned message | Operator can't undo. Better: emit signal, let AgentsView do the fan-out, source card prints `[/broadcast] fanning to N cards…` first |
| 4 | Operator-actions parser that ignores section headers | An item with no inline emoji + parsed without section context has no severity. Track `current_severity` as you scan lines |
| 5 | Restoring resume state via direct attribute writes | Button visuals don't update (`_pin_btn.setText` not called). Call the proper toggle method or replicate its side-effects |
| 6 | Latest-save-by-mtime | mtime is sketchy on Windows network shares. ISO8601 `saved_at` string compare is portable |
| 7 | Fanning to mid-turn cards | Clobbers in-flight EVE response. Always check `_proc.state() != NotRunning` before staging into input |
| 8 | `/usage` per-mode breakdown that always renders | Adds noise when operator only uses default model. Guard with `if len(per_mode) > 1 or any(m != "claude" ...)` |

## Quick stats this cluster

- **Versions:** v1.6.27 → v1.6.31 (5 iterations, ~25 min cadence)
- **Files touched:** `agents_tab.py` (heavy), `__init__.py` (version), `MANIFEST.json`, `CHANGELOG.md`
- **New slash commands:** `/pin` (1.6.28), `/broadcast` (1.6.30). Total registry: 21
- **New signals:** `AgentCard.pin_changed(str)` + `AgentCard.broadcast_requested(str)`
- **New AgentsView methods:** `_rebuild_operator_actions`, `_scan_urgent_actions`, `_build_action_row`, `broadcast`, `_restore_card_state_from_disk`

## Composes with

- `rkoj-polish-cluster-v1.6.20-25-2026-05-22` — direct predecessor; the
  cards_changed signal pattern + auto-save lifecycle established there
  are reused for pin + broadcast here
- `rkoj-stream-json-jcode-parity-2026-05-22` — `_handle_stream_event`
  `result` branch feeds the cost telemetry that v1.6.31 restores
- `rkoj-session-continuity-pattern-2026-05-21` — `session_uuid` is the
  dedup key for both `/usage` and `_restore_card_state_from_disk`
- `agent-identity-eve` — every saved resume-point carries `agent_identity: "EVE"`
- `forever-expanding-modular-architecture-doctrine` — every slash command
  is additively registered + auto-discovered by autocomplete
