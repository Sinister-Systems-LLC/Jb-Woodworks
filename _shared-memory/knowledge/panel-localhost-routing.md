> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Panel surfaces must route loopback-first with snap-fallback + source tag

**Slug:** panel-localhost-routing
**First discovered:** 2026-05-19 11:00 by Sinister Sanctum master
**Last updated:** 2026-05-19 11:00 by Sinister Sanctum master
**Status:** fixed
**Tags:** panel, localhost, routing, launcher, window-manager, trophy-case, source-tag, sanctum, master-sweep

## Problem

Two Sanctum-side surfaces show "live panel data" (trophy case in `start-sinister-session.ps1`, `/api/trophy` in `window-manager/server.py`) but each hardcoded its own URL list and timeout:

- Launcher: only tried `http://127.0.0.1:5055` with 1-second timeout, no fallback. Whenever the operator's local panel wasn't booted, the trophy case rendered `panel offline` even though `https://snap.sinijkr.com` was up.
- Window-manager: had a 3-step fallback chain but the same 1-second loop timeout meant the loop rarely advanced past loopback before the request committed to "offline." The response didn't say which source filled the cells.

Operator directive 2026-05-19: "update panel like i said to local host when you update." Translation: every Sanctum surface that pulls panel data must try local first, snap second, and tell the operator which one filled the cell.

## Why it happens

Two different language readers (PowerShell + Python) duplicated the same wiring decision in two places. Each made the wrong call (give-up-on-loopback) without communicating with the other. No central knob meant flipping routing was a two-file code edit.

## Fix or workaround (tested 2026-05-19)

1. New tool `D:\Sinister Sanctum\tools\panel-config\panel-config.json` holds `primary` / `fallback` / per-source timeouts / endpoint path map. Tool card at `tools/panel-config/README.md`.
2. Launcher `Get-PanelConfig` (cached) + reworked `Get-PanelStat` tries primary, then fallback, sets `$script:PanelSource` to `local` / `prod` / `offline`. Trophy case header shows that tag.
3. Window-manager `_load_panel_config` reads the JSON at request time (no module-level cache; lets operator edit live). `/api/trophy` response now includes `source: "local" | "prod" | "offline"`.
4. Hardcoded URL fallback kept as the safety net if JSON parse fails — never trust the disk fully.

```powershell
# verify launcher tagging
& 'D:\Sinister Sanctum\automations\start-sinister-session.ps1' -Project sanctum -Mode overview -Fast -NoNotepad -NoLaunch
# trophy-case header: "[ TROPHY CASE ]   live from snap.sinijkr.com  (prod)"  when local down
# trophy-case header: "[ TROPHY CASE ]   live from local panel       (local)" when local up
```

```bash
# verify console tagging
curl -s http://127.0.0.1:5077/api/trophy | jq '.source'
# "local" | "prod" | "offline"
```

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 11:00 by Sinister Sanctum master
First write. Centralized `panel-config.json`; both consumers now read it. Status flipped straight to `fixed` because the fix is deployed, not just a workaround. If a future agent finds a third caller hardcoding `127.0.0.1:5055`, point it at `Get-PanelConfig` / `_load_panel_config` and append a discovery here.

## Related topics

- [adb-containerization](./adb-containerization.md) — separate "per-thing isolation" pattern; panels too should look isolated from each other
- [exe-silent-crash-no-popup](./exe-silent-crash-no-popup.md) — the silent-crash discipline (None-check before .write) is the same family of "verify before assuming" bug
