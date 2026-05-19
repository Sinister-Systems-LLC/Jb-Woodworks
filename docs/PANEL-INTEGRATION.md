# Panel Integration â€” how Sanctum bots interact with Sinister Panel

For Leo: this explains the boundary between Sanctum (this repo) and the
**Sinister Panel** repo (live dashboard at `snap.sinijkr.com`, deployed on
Hetzner).

## TL;DR

- **Sanctum bots READ panel state** (via HTTP probes + the `sinister-panel` MCP server's read tools)
- **Sanctum bots NEVER WRITE to panel source** â€” the panel session/agent owns that lane
- Pushing panel commits to Hetzner = operator's existing `Sinister_OneClick_Deploy.bat` (chained via Sanctum's `Deploy-Hetzner.bat`)

## What's where

| Thing | Where |
|---|---|
| Panel source code | `https://github.com/Sinister-Systems-LLC/Sinister-Panel` (working tree locally at `D:\Sinister\01_Projects\Sinister\Sinister-Panel\` or legacy `C:\Users\Zonia\Desktop\Sinister-Panel\`) |
| Panel deploy script | `<panel-source>\Sinister_OneClick_Deploy.bat` (operator-owned) |
| Panel-deploy orchestrator | `D:\Sinister Sanctum\automations\hub-scripts\deploy-all-to-hetzner.ps1` (junction to hub) |
| Panel-deploy one-click for operator | `C:\Users\Zonia\Desktop\Deploy-Hetzner.bat` (Sanctum-shipped) |
| Panel MCP server | `sinister-panel` registered in `~/.claude/.mcp.json` â€” 13 tools the panel agent exposes |
| Panel-state read endpoint | `https://snap.sinijkr.com/api/health` (returns 401 auth-gated; treated as UP by `check-hetzner-state.ps1`) |
| Live verification | `C:\Users\Zonia\Desktop\Check-Hetzner-State.bat` reports panel UP + git-ahead |
| Hub memory for panel project | `D:\Sinister\Sinister Skills\01_MEMORY\sinister-panel\{TODO.md, CLAUDE.md, SESSION-START.md, _claude_memory/}` |

## How a Sanctum bot reads panel state

```
researcher.summarize_url url=https://snap.sinijkr.com/  focus="dashboard health"
   -> stealth-browser opens the URL, scrapes rendered text, Ollama summarizes
   -> $0 (local; no Anthropic)
```

For commit-level visibility (what's deployed vs what's queued):
```
bus.run_script "check-hetzner-state"
   -> emits runlog manifest with sinister-panel { http_status, commits_ahead }
   -> bus.runlog_latest "check-hetzner-state" returns the structured result
```

## How to message the panel agent (when their session is open)

```
sinister-bus.delegate_to agent_name="sinister-panel"  prompt="<question>"
   -> if panel session is online (recent heartbeat): inbox-and-reply
   -> if offline + allow_ephemeral=true: spawns one-shot `claude --print`
```

## What Sanctum bots NEVER do

- Modify panel source files
- Touch `~/.claude/.mcp.json` `sinister-panel` entry
- Push panel commits
- Run the panel's `Sinister_OneClick_Deploy.bat` UNLESS the operator explicitly triggers it via `Deploy-Hetzner.bat`
- Robocopy/migrate panel source

## What Sanctum bots HELP with (panel-adjacent)

- **Backup:** `D:\_backups\_config\watch-list.json` now includes `sinister-panel-source` (Custodian snapshots every panel source change + 7-day retention)
- **Deploy verification:** `check-hetzner-state` confirms panel is up + git in sync
- **Cross-session messaging:** if you (Leo) need something from the panel session, use the inbox
- **Doc reference:** `09_REFERENCE/HETZNER-DEPLOYS.md` in the hub holds the canonical Hetzner service map (panel + RKA daemon)

## Panel routing (2026-05-19) — loopback-first with snap-fallback

> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

Operator directive 2026-05-19: "update panel like i said to local host when you update." All Sanctum-side surfaces that pull panel data now route **local first, snap second**, and tag the cell with which source filled it.

**Single knob:** `D:\Sinister Sanctum\tools\panel-config\panel-config.json` (see `tools/panel-config/README.md` for the schema).

```jsonc
{
  "primary":             "http://127.0.0.1:5055",   // local dev panel
  "fallback":            "https://snap.sinijkr.com", // prod (Hetzner)
  "timeout_ms_primary":  1500,
  "timeout_ms_fallback": 4000,
  "endpoints": { "stats": "/api/dashboard/stats", "health": "/api/health", ... }
}
```

**Consumers:**

- `automations/start-sinister-session.ps1` — `Get-PanelConfig` (cached) + `Get-PanelStat` set `$script:PanelSource` to `local` / `prod` / `offline`. Trophy-case section header shows the tag (`live from local panel ...` / `live from snap.sinijkr.com (fallback)` / `panel offline ...`).
- `automations/window-manager/server.py` — `_load_panel_config()` re-reads on every request (no module-level cache, so operator edits land without a server restart). `GET /api/trophy` returns `{ "source": "local" | "prod" | "offline", ... }`.

**Standing rule:** never hardcode `http://127.0.0.1:5055` or `https://snap.sinijkr.com` in a new Sanctum surface. Add a consumer that reads the JSON. Document it in `tools/panel-config/README.md`. The cell must carry a source tag the operator can read.

**To switch routing for testing:** edit `panel-config.json`. Set `primary` to the URL you want tried first; the launcher and the console pick it up on next probe (no rebuild, no restart for window-manager).

## TL;DR

- **How we won:** Clean lane between Sanctum (orchestration + read) and Panel (own source + write). Backup covers panel source. Deploy chain works via existing operator bats. Panel routing is now one JSON knob (`tools/panel-config/panel-config.json`) consumed by both the launcher and the console; both surfaces tag the cell with `local` / `prod` / `offline`.
- **What you need to do (Leo, on first clone):**
  - Read this doc + `SESSION-START/README.md`
  - Confirm `check-hetzner-state` reports panel UP (https://snap.sinijkr.com/api/health 401 = working)
  - Talk to the panel session via `sinister-bus.delegate_to agent_name="sinister-panel" prompt="..."`
  - If the trophy case says `panel offline`, edit `tools/panel-config/panel-config.json` so `primary` points at a panel you can reach
