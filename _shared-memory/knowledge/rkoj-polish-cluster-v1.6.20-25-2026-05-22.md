# Author: RKOJ-ELENO :: 2026-05-22

# RKOJ v1.6.20 → v1.6.25 polish cluster

**Status:** doctrine, implemented
**Composes with:** `rkoj-stream-json-jcode-parity-2026-05-22`, `rkoj-session-continuity-pattern-2026-05-21`, `rkoj-phase1-memory-bootstrap-2026-05-21`, `agent-identity-eve`, `forever-expanding-modular-architecture-doctrine`.

---

## TL;DR

After stream-json wired token-by-token UX (v1.6.11) and the v1.6.12–18 telemetry chain landed, v1.6.20–25 layered six polish-but-load-bearing wins on top: rate-limit warnings, auto-save on close, cross-card spend aggregation, sidebar count badges, and the dim-color timestamp gutter. Each individually small; together they turn RKOJ from "agent chat that works" into "workstation I trust to not lose state and to show me what's happening."

Operator `/loop keep going make it better` drove this cluster — 6 self-paced 25-min cadence iterations across an active build session.

## What landed

| ver | Win | Why it matters |
|---|---|---|
| 1.6.20 | `rate_limit_event` renderer | claude emits this every turn; suppressed when `status=allowed`, surfaced loud when warning/exceeded so operator isn't surprised by a hard 5-hour wall |
| 1.6.20 | SlashPopup position safety | `adjustSize()` then try-above-or-flip-below + clamp-X-to-screen-right; no off-screen autocomplete |
| 1.6.20 | `/skill <name>` loader | reads `<name>.md` or `<name>/SKILL.md` from any of 3 skill roots, stages into input, fires `_on_send` on next tick (so spinner+streaming+cost all run uniformly) |
| 1.6.21 | Auto-save on `_on_close` / `shutdown` | sessions no longer silently vanish when a card closes; mirrors AgentWindow's v1.6.7 path. `_write_resume_point()` extracted as the single writer; skips empty cards |
| 1.6.21 | `/usage` cross-card aggregator | walks every saved resume-point on disk, dedupes by `session_uuid` (keeps highest cost — cumulative within card lifetime), groups by project, prints per-project + grand totals |
| 1.6.22 | Sidebar Sessions count badge | small purple pill on "Sessions" nav row showing unique-saved-session count. 30s QTimer refresh; initial refresh at construction so accurate from launch |
| 1.6.23 | Live Agents count badge + cards_changed signal | `AgentsView.cards_changed(int)` emits on spawn / close; app.py wires to sidebar.set_agents_count AND sidebar.refresh_sessions_badge (since v1.6.21 close auto-saves, count may have incremented) |
| 1.6.23 | `/stats` slash | 6-line RKOJ fleet snapshot (heartbeats / inbox / brain / devices / vault / pending). Reuses `state.snapshot()` which already drives the bottom status bar |
| 1.6.24 | Terminal timestamp gutter | `[HH:MM:SS] >>` and `[HH:MM:SS] <<` prefixes on each operator turn / EVE reply. Scannable conversation chronology; survives `/export` |
| 1.6.25 | Dim color for timestamp gutter | `QTextCharFormat` with `MUTED_FG` `#8e8e93`; new `_append_dim()` helper preserves sticky-scroll. `_append_terminal` resets char-format each insert so dim doesn't bleed forward |
| 1.6.25 | Devices sidebar count badge | third badge (Agents/Sessions/Devices). 6s tick so USB plug/unplug surfaces fast (vs 30s Sessions tick) |

## Patterns codified

### 1. Cards_changed signal + sidebar badges

`AgentsView` is the source of truth for the live card count. Two consumers:

```python
self.agents_view.cards_changed.connect(self.sidebar.set_agents_count)
self.agents_view.cards_changed.connect(
    lambda _n: self.sidebar.refresh_sessions_badge()
)
self.agents_view.cards_changed.connect(self.status_bar.set_live_agents)
```

Emit on:
- `spawn_agent` after card lands → `self.cards_changed.emit(len(self._cards))`
- `_remove_card` after pop → `self.cards_changed.emit(len(self._cards))`

Why two consumers for the same signal: closing a card both reduces live-agent count AND increments saved-sessions count (auto-save on close).

### 2. Auto-save resume-point lifecycle

Three writers, ONE shared helper:

```
_on_close (operator clicks card X)  ──┐
shutdown   (app close, every card) ──┼──► _write_resume_point(save_reason)
/save      (operator slash)        ──┘
```

Skip empty cards: `if not any(t.get("user") for t in self.session.turns): return None`. Don't litter the picker with sessions that never sent a message.

Filename suffix differentiates intent: `<ts>.json` for manual, `<ts>-autoclose.json` for auto-on-X, `<ts>-app-shutdown.json` for app-close.

### 3. Dim text via QTextCharFormat without bleeding

QTextCursor maintains the LAST applied char format. If you set a dim format and then `insertText()`, subsequent inserts on the same cursor inherit that format unless you reset.

```python
# WRONG — second insert is also dim
cursor.setCharFormat(dim_fmt)
cursor.insertText("[12:34:56] ")
cursor.insertText("message body")   # ← also dim!

# RIGHT — reset to default between
cursor.setCharFormat(dim_fmt)
cursor.insertText("[12:34:56] ")
cursor.setCharFormat(QTextCharFormat())  # reset
cursor.insertText("message body")
```

`_append_terminal` in v1.6.25 always resets on entry so prior helpers can leave the cursor in any format.

### 4. Position-tracked post-stream markdown

Recorded once per turn the first time a `text_delta` arrives, AFTER inserting `[ts] << ` prefix:

```python
self._reply_start_pos = self.terminal.textCursor().position()
```

At end-of-turn (`_on_finished`), `_apply_markdown_format(self._reply_start_pos, end_pos)` walks code-fence + inline-code + bold regex over the reply range only. Doesn't touch operator messages or timestamps.

### 5. Cross-card aggregation via session_uuid dedup

The same conversation may have N saves (manual /save + autoclose + app-shutdown). To avoid triple-counting cost in `/usage`:

```python
per_uuid: dict[str, dict] = {}
for fp in resume_points:
    d = json.load(fp)
    uid = d.get("session_uuid")
    if not uid:  # pre-v1.6.3 saves
        continue
    cost = d.get("total_cost_usd", 0)
    prev = per_uuid.get(uid)
    if prev is None or cost > prev["cost"]:
        per_uuid[uid] = {...}  # keep highest cost
```

Cost is cumulative within a card lifetime, so the latest save has the truest cost. Highest-wins is a good proxy when "latest" is hard to define on disk.

## Anti-patterns

| # | Anti-pattern | Why bad |
|---|---|---|
| 1 | Sidebar badges polled at 1s | Wasteful (file IO every second). 6s for Devices (USB plug events), 30s for Sessions (saves are slower events) |
| 2 | Status bar reads heartbeats for "agents" count | Over-counts — ended cards keep their heartbeat file. Use signal-driven live-card count from AgentsView |
| 3 | _on_close auto-save WITHOUT skipping empty cards | Picker fills with junk |
| 4 | Stream-json `result` event ignored | Cost telemetry lost. Always aggregate in `_handle_stream_event` `t == "result"` branch |
| 5 | Dim QTextCharFormat applied without reset after | Subsequent inserts inherit dim color → operator message body also gray, unreadable |
| 6 | Skill loader that just emits text → input | Bypasses spinner / streaming / cost pipeline. Stage into input + fire `_on_send` via `QTimer.singleShot(0, ...)` so all the existing UX runs |
| 7 | rate_limit_event always rendered | Floods terminal with `status: allowed` no-signal lines. Filter to non-allowed only |
| 8 | Cross-card aggregator SUM instead of dedup-by-uuid | Triple-counts cost when manual /save + autoclose + app-shutdown all exist for the same conversation |

## Quick stats this cluster

- **Versions:** v1.6.20 → v1.6.25 (6 iterations, ~25 min cadence)
- **Files touched:** `agents_tab.py` (heavy), `sidebar.py` (badges), `app.py` (status-bar wiring), `__init__.py` (version), `MANIFEST.json`, `CHANGELOG.md`
- **New slash commands:** /skill (1.6.20), /usage (1.6.21), /stats (1.6.23). Total registry: 19
- **New sidebar badges:** Sessions (1.6.22), Agents (1.6.23), Devices (1.6.25). All three nav rows now badged
- **New signals:** `AgentsView.cards_changed(int)` — fan-out to sidebar (2 receivers) + status bar (1 receiver)

## Composes with

- `rkoj-stream-json-jcode-parity-2026-05-22` — base streaming + cost telemetry; `/usage` reads what `result` events produce
- `rkoj-session-continuity-pattern-2026-05-21` — session_uuid is the dedup key in /usage
- `rkoj-phase1-memory-bootstrap-2026-05-21` — bootstrap creates the resume_dir that auto-save writes into
- `agent-identity-eve` — every saved resume-point carries `agent_identity: "EVE"` for cross-fleet discovery
- `forever-expanding-modular-architecture-doctrine` — every slash command is additively registered + auto-discovered by autocomplete
