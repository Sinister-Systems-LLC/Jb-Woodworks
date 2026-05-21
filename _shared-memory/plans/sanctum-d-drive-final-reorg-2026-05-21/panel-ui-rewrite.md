# Workstation Web UI :: Sinister Panel Rewrite

> Author: RKOJ-ELENO :: 2026-05-21

## Summary

Replaced the Workstation pywebview UI (`automations/window-manager/web/`) with a
Panel-style shell that mirrors `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/`.
The shell is rounded + frameless (pywebview owns the OS chrome), runs static
HTML/CSS/JS (no React/build step), and keeps every existing API hook in
`server.py` (`/api/sessions`, `/api/devices`, `/api/launcher/spawn`,
`/api/inbox/*`, `/api/vault/*`, `/api/operator-requests`, `/api/recent-runlogs`,
`/api/cycle-points`, `/api/projects`, `/api/health`).

The `window.RkojHelpers` global is preserved verbatim so the unchanged
companion modules (`popout.js`, `palette.js`, `cycle-points.js`,
`scheduler.js`, `fleet-state.js`) keep working without edit.

## Section-by-section diff

### Sidebar (`.sp-sidebar`)
- **Before:** No persistent sidebar — header had a 3-row layout (brand + tabs
  + icon strip / Excel-style ribbon / KPI strip).
- **After:** Panel-style 240px left rail with:
  - Mascot block (uses `/static/skull.svg`; ASCII fallback if missing).
  - Brand text `SINISTER / SANCTUM` (purple accent + glow).
  - 4 nav sections (`Workspace / Operations / AI / System`) — matches Panel's
    `sidebar.tsx` `SECTIONS` array. Active item gets purple gradient bg + inset
    glow exactly like Panel.
  - Footer with avatar pill, `RKOJ-ELENO / operator` line, `EVE` role chip
    (purple-glow per CLAUDE.md operator-canonical 2026-05-21), and Sign Out
    button.

### Header (`.sp-header`)
- **Before:** 3 rows (identity+tabs+icons, Excel ribbon, KPI strip).
- **After:** Single 96px header (matches Panel `HEADER_HEIGHT`):
  - Left: dynamic title (`AGENTS` / `PHONES` / `WORKSTATION`) tinted purple
    with text-shadow, plus 3 chip-tabs (`Agents / Phones / Workstation`).
  - Right: action icons — Alerts (!), Inbox bell, Search palette (Ctrl+K),
    Settings cog, health pill, clock.
  - Border-bottom is a purple hairline (matches Panel platform tint).

### KPI strip (`.sp-kpi-strip`)
- 4 tiles below the header in a 4-col grid: `PHONES ONLINE`, `AGENTS ONLINE`,
  `VAULT USED`, `PENDING REQUESTS`. Each tile is a clickable shortcut
  (`data-target-tab`) that jumps to the relevant tab.
- Auto-refreshes every 15s via `refreshDevices` / `refreshAgents` /
  `refreshVault` / `refreshRequests`.

### Project sub-tab strip (`.sp-projstrip`)
- New strip immediately under the KPI tiles. Renders one pill per
  `automations/session-templates/projects.json` entry (15 projects today), with
  `[All N]` as the first pill. Click filters the visible agent stack on the
  Agents tab. Selection persists in `localStorage` (`sp.proj.filter`).
- Counts shown next to each pill: number of sessions whose project key matches.

### Main content
- **Agents tab (`#pane-agents`)** — niri-style infinite vertical stack of
  agent-console cards (`#agent-stack`). Each card shows dot + agent name +
  project chip + mode chip + last-seen, recent inbox tail (up to 5), and a
  per-card input row that supports slash commands (`/help`, `/clear`,
  `/compact`, `/resume`, `/create`, `/save`, `/git`, `/mcp`, `/effort`, `/fast`)
  plus normal inbox messages.
- **Phones tab (`#pane-phones`)** — auto-fill device grid (`#device-grid`) with
  one card per `adb devices -l` row: dot, model, state (device/unauthorized/...),
  transport, serial, lane. Actions: `View (scrcpy)` (calls
  `/api/devices/{serial}/view`), `Push file`, `Logs`.
- **Workstation tab (`#pane-workstation`)** — 4 glass cards: Vault (with %-fill
  meter + commit button via `RkojVault.openCommitModal`), Operator requests,
  Activity feed (recent runlogs), Cycle points.

### Theme tokens
- `theme.css` defines local `--purple-accent #A06EFF`, `--purple-deep #7A3DD4`,
  `--bg #0E0A14`, `--bg-glass #15131A`, `--border-glass #3A2A55`, `--soft
  #999AB0`, `--dim #6E6E84` (operator spec).
- `tokens.css` is preserved as-is so any callers reading `var(--accent)`
  continue to render Sanctum purple.

## Files touched

| File | Before | After |
|---|---|---|
| `automations/window-manager/web/index.html` | 1119 lines (3-row header + KPI + 2-tab) | ~310 lines (Panel shell) |
| `automations/window-manager/web/theme.css` | 3406 lines (ribbon + lg-* primitives + dev-tools rail) | ~640 lines (Panel-style only) |
| `automations/window-manager/web/app.js` | 3910 lines (legacy PaneRegistry + ribbon + devtools rail) | ~660 lines (Panel-style only, preserves `RkojHelpers`) |

## TODOs (deferred to follow-up turns)

1. **Embedded scrcpy viewer** — current implementation launches the standalone
   scrcpy process via `/api/devices/{serial}/view` (the server already handles
   it). Embedding the live MJPEG stream from `/api/devices/{serial}/screen.mjpeg`
   into the device card requires an `<img>` swap + lifecycle wiring; defer for
   next sweep.
2. **Per-agent log tail streaming** — the agent-tail box currently renders the
   last 5 inbox messages from `/api/sessions`. Live append via SSE
   (`/api/sse/changes` already exists) is a follow-up.
3. **Per-card session-close action** — the close button toasts "TODO". Wire
   `/api/spawned-windows/{pid}/close` next pass (need pid in
   `/api/sessions` response — already present, just unwired).
4. **Dev-tools rail / Excel ribbon** — intentionally removed. If the operator
   wants them back as a slide-out panel, they live in git history; a future
   pass can re-mount the `tpl-*` templates inside a Panel-style drawer.
5. **Sidebar nav -> sub-tab mapping** — every nav item currently jumps to
   `workstation`. If a finer mapping is desired (e.g. `Inbox` opens a dedicated
   pane), add new panes + wire `data-nav` -> pane id.
6. **`/login` route** — Sign Out posts to `/api/auth/logout` then redirects to
   `/login`. The login.html page lives in the same web/ folder and is untouched.

## Blockers

None found. All API endpoints used by the new app.js exist in `server.py`
(verified by grepping `@app.(get|post)` decorators). The companion JS modules
read `window.RkojHelpers` lazily so their load order stays the same.
