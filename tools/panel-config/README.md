> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Tool: `panel-config`

Single source of truth for **where Sanctum surfaces look for Sinister Panel state**. One JSON, two readers (PowerShell launcher + Python window-manager). Flip `primary` / `fallback` to change routing without touching code.

## Why this exists

Before this tool, two places hard-coded their own panel URLs:

- `automations/start-sinister-session.ps1` — `Get-PanelStat` only tried `http://127.0.0.1:5055` with a 1-second timeout and silently gave up (no fallback to prod) — so the trophy case showed "panel offline" whenever the local panel wasn't booted.
- `automations/window-manager/server.py` — `/api/trophy` had a 3-step fallback chain (`localhost:5055` → `127.0.0.1:5055` → `https://snap.sinijkr.com`) but the same 1-second loop timeout defeated the fallback in practice and the response didn't say which source filled the cells.

Operator directive (2026-05-19): "update panel like i said to local host when you update." Master interpretation:

1. **Local first** (so the operator's local dev panel is the source of truth when it's up).
2. **Snap second** (so the trophy case still populates when local is down).
3. **Tag the source** in the surface so the operator can tell which is which.
4. **One knob** (this JSON) so flipping routing is a one-line edit, not a code change in two places.

## File: `panel-config.json`

```json
{
  "primary": "http://127.0.0.1:5055",
  "fallback": "https://snap.sinijkr.com",
  "timeout_ms_primary": 1500,
  "timeout_ms_fallback": 4000,
  "endpoints": {
    "stats":   "/api/dashboard/stats",
    "signer":  "/api/harvest/signer-status",
    "devices": "/api/harvest/devices",
    "actions": "/api/actions/status",
    "health":  "/api/health"
  }
}
```

| Field | Purpose |
|---|---|
| `primary` | First base URL tried (loopback by default). |
| `fallback` | Second base URL tried if primary times out / errors. |
| `timeout_ms_primary` | Fail-fast budget for primary. Default 1500 ms. |
| `timeout_ms_fallback` | Slightly more generous budget for the fallback (it's prod, may be slower). Default 4000 ms. |
| `endpoints` | Path map. Lets us rename a panel endpoint without grepping callers. |

## Source-of-truth tags

Both readers now stamp surfaces with the source:

- **Launcher trophy case header** — shows `[ TROPHY CASE ]` with `local` / `prod` / `offline` next to "live from ..."
- **`GET /api/trophy`** — response includes `"source": "local" | "prod" | "offline"`

## How to use it

- **Local dev only:** set `primary` to your local URL and `fallback` to `""`. The reader treats empty fallback as "no fallback" and shows `offline` when primary is down.
- **Prod only:** set `primary` to `https://snap.sinijkr.com` and `fallback` to `""`.
- **LAN panel:** set `primary` to `http://<lan-ip>:5055`. The schema is unchanged; only the URL moves.

## Standing rule (per `_shared-memory/DIRECTIVES.md` 2026-05-19)

Every Sanctum update that surfaces panel data must:

1. Route loopback first, snap second (the two URLs come from this file).
2. Tag the cell with which source filled it.
3. Never hardcode `http://127.0.0.1:5055` or `https://snap.sinijkr.com` again — call the loader.

## Files that consume this config

- `D:\Sinister Sanctum\automations\start-sinister-session.ps1` (`Get-PanelConfig`, `Get-PanelStat`)
- `D:\Sinister Sanctum\automations\window-manager\server.py` (`_load_panel_config`, `/api/trophy`)

If you add a new consumer, document it here.
