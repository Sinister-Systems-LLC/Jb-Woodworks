> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: RKOJ workstation UI doctrine — 3-row header + 2 tabs + workstation-always-visible

**Slug:** rkoj-workstation-ui-layout
**First discovered:** 2026-05-19 14:30 by Sinister Sanctum master (UI redesign sweep)
**Last updated:** 2026-05-19 14:30 by Sinister Sanctum master
**Status:** fixed
**Tags:** rkoj, ui, layout, workstation, header, ribbon, kpi, two-tab, agents-tab, adb-tab, sanctum-purple, liquid-glass, doctrine, design-system

## Problem

The pre-redesign RKOJ UI was a thin top-bar + Excel-ribbon-with-4-tiles + empty body that said "no Claude windows tracked yet — spawn from Agents tab" when no agents were running. Operator feedback: "we are getting better still many things to change and do. i just want the two tabs i told you to make with a complex header with functions we can use to open many windows agent commands etc. I need a workstation style with one tab for agents and creating and managing agents and all my features and ideas for that and the adb side of things to view the phones."

Three concrete problems:
1. Header is too thin / underused — only ~44px tall, 4 tiles, no place for window-management or agent-command quick-actions
2. Agents tab is empty when no agents are spawned (placeholder text, no workstation feel)
3. ADB Devices tab needed first-class phone-viewer treatment, not "secondary feature buried in dev-tools rail"

## Why it happens

Organic UI growth. The initial 2-tab+ribbon design (from the RKOJ.exe sprint earlier today) was a minimum-viable scaffold. Features got added (cycle points, scheduler, codex, vault, knowledge, progress, fleet-state, daemon-liveness) but each landed in its own corner — dev-tools rail drawer, Cmd+K command, hash route. The result: lots of features, none of them visible on the active tab when an operator first opens RKOJ.

## Fix or workaround — the workstation doctrine

### Tab structure (immutable)

EXACTLY 2 top-level tabs, always:
- `ADB DEVICES` — phone-viewer surface
- `AGENTS` — agent-management workstation

No third tab. No nested tabs. No sidebar replacing tabs. If a feature feels like it needs its own tab, it actually wants either (a) a card on the active tab, (b) a popout window, or (c) a Cmd+K command. The 2-tab limit is the lid.

### Header structure — 3 rows, ~150px tall

ROW 1 (~44px, identity + window controls):
- LEFT: skull logo + `RKOJ` wordmark + `WORKBENCH` subtitle (small caps)
- CENTER: 2-tab pill group (active = Sanctum purple Liquid Glass pill)
- RIGHT: icon strip with `!` bell (operator-requests count) + `🔔` inbox (cross-agent count) + `⌘K search` + `● online v8aj.1` health pill + `+ window` popout picker + `⚙ settings` cog + clock

ROW 2 (~62px, Excel-style ribbon, 5 groups full-width):
- **VIEW** — Split / Popout / Toggle rail / Layout
- **SPAWN** — `+ Agent` / Cycle resume / `+ Window` / Broadcast
- **AGENT** — Intelligence / Ping all / Codex review / Inbox
- **AUTOMATE** — Schedule / Run script / Fix memory / Vault commit
- **MAINTAIN** — Build EXE / Health / Restart / Logs

Each tile: 44px tall, icon + 14px label below, optional 11px kbd-shortcut chip in bottom-right corner. Hover: `translateY(-1px)` + soft glow. Active: Sanctum purple bg.

ROW 3 (~64px, hero KPI strip, 4 stat cards full-width):
- PHONES ONLINE · AGENTS ONLINE · VAULT USED · PENDING REQUESTS
- Big number (24px bold) + small label (11px uppercase, letter-spacing 1px)
- Color-coded: green for healthy, amber for warning, red for danger
- Click → opens the corresponding pane (devices / sessions / vault drawer / requests pane)
- Refreshes every 10s via FleetState SSE (NOT a new poller)

### Agents tab body — always-visible workstation

TOP (`.lg-card-hero`, ~280px tall): launcher wizard
- Project picker (populated from `/api/launcher/options`)
- Mode chips (overview / dev / audit / deploy / push / debug / explore)
- Fast toggle (Sonnet vs Opus)
- Custom-prompt textarea (3 rows, optional)
- LAUNCH button (Sanctum purple, 44px tall, right-aligned)
- Recent launches strip (max 5, click → relaunch with captured params)

MIDDLE (2-column grid, 60% / 40%):
- LEFT 60%: Active sessions strip card + Activity feed card (both FleetState-driven, no new pollers)
- RIGHT 40%: Cycle points card + Schedule card + Codex summary card (click → opens existing `tpl-codex-fullpane`)

BOTTOM (5-tile shelf, 1 row, ~100px tall): Knowledge / Vault / Progress / Skills+Tools+Inventions / Daemon liveness

### ADB Devices tab body — phone-viewer surface

TOP (sticky, ~56px): lane-filter chips (Snap / TikTok / Bumble / Untagged / All) + bulk actions (Scan all / Push file to lane / Push frida to lane / Reboot selected) + device count badge

MIDDLE (responsive device grid, ~280px card width): each card has device name + lane chip + status pill, body (model/Android/battery/attestation/modules/proxy/selinux), `[EMBED SCREEN]` button (inline MJPEG), `[VIEW]` button (full scrcpy popup), command input row + RUN, collapsed command history (last 10), actions popover (PUSH FILE / PUSH FRIDA / SET PROXY / SHELL DUMP / LOGS).

BOTTOM (~200px): recent ADB events feed (filterable by serial)

### Constraints (forever rules for this surface)

- Sanctum purple `#7A3DD4` is the master-surface accent (binding for Sanctum console)
- Liquid Glass primitives only (`.lg-card / -hero / -rail / -pill / -pill-active / -button / -input / -popover`)
- Motion vars: 150ms (subtle) / 300ms (standard) / 600ms (sweeping) with `cubic-bezier(0.22, 1, 0.36, 1)` ease
- `prefers-reduced-motion` media query disables transforms
- No lucide-react, no magic-wand Eve icons — inline SVG or Unicode glyphs only
- Hot-reload preserved: `/api/sse/changes` SSE channel + CSS link href-bump must keep working
- FleetState SSE is the single data source for sessions / windows / inbox / heartbeats — no new pollers
- Endpoints already exist (server.py is stable; do not add new endpoints for UI-side work)
- Popout system: `BroadcastChannel('rkoj-state')` cross-window sync + `#popout=<view>` URL hash; every new pane should be popout-capable

### What NOT to do (anti-patterns)

- Don't add a third tab. If a feature feels like it needs one, refactor it into a card on AGENTS or ADB DEVICES.
- Don't bury features in the dev-tools rail. Surface them directly on the active tab.
- Don't introduce new polling — use FleetState.subscribe.
- Don't replace the 2-tab top with a sidebar (that was the pre-RKOJ design the operator killed).
- Don't add bespoke material recipes. Reuse Liquid Glass primitives.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 14:30 by Sinister Sanctum master (UI redesign)
Shipped the 3-row header + Agents workstation + ADB phone-viewer per the doctrine above. 2199 LOC added across `web/index.html` + `web/app.js` + `web/theme.css`, 371 LOC removed (replaced empty placeholders with workstation panels). All Liquid Glass primitives + Sanctum purple + motion vars preserved. Syntax checks (`node --check` + `HTMLParser.feed`) all clean. Hot-reload via `/api/sse/changes` verified intact. EXE rebuild from this state is Phase 2 of the same sweep.

### Why this matters
A single Claude session is bounded by its context window. But the operator opens RKOJ every day. The visible UI structure determines what features the operator USES vs forgets. A workstation that surfaces every feature on tab-open (vs hiding them in drawers) means the fleet's compound knowledge actually reaches the operator's hands. This doctrine is what makes RKOJ a "workbench" instead of a "console with a sidebar".

## Related topics

- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md)
- [rkoj-hot-reload-pattern](./rkoj-hot-reload-pattern.md)
- [fleet-state-single-source](./fleet-state-single-source.md)
- [daemon-liveness-heartbeats](./daemon-liveness-heartbeats.md)
- [rkoj-embedded-device-viewer](./rkoj-embedded-device-viewer.md)
- [agent-intelligence-control](./agent-intelligence-control.md)
- [cross-agent-coordination](./cross-agent-coordination.md)
