> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# RKOJ hot-reload — ship updates while the console is running + agents don't lose context

**Slug:** rkoj-hot-reload-pattern
**First discovered:** 2026-05-19 by Sinister Sanctum master agent
**Last updated:** 2026-05-19 by Sinister Sanctum master agent
**Status:** fixed
**Tags:** hot-reload, sse, broadcast, [update], heartbeat, dev-loop, rkoj, watchdog, uvicorn, ssen

## Problem

Operator wants the live development loop where they can ship updates to the workbench (CSS, JS, palette content, agent prefs) and to the agent fleet WITHOUT either:

- restarting RKOJ.exe (would close pop-outs, drop cycle-point state, drop the operator's mid-flight context)
- killing spawned Claude windows (would erase agent context window mid-task — the entire reason they're using Opus on a long thread)

Operator (verbatim): "get to a point where i can use and test things and actively add things without disrupting my claude agents and they will heartbeat or reping or something without stopping and loosing context they will get the updates if they can."

Four moving pieces need a story: (1) backend Python source, (2) frontend HTML/CSS/JS/PNG assets, (3) spawned Claude agent windows, (4) liveness sensing so the operator can tell which agents are still warm.

## Why this is hard

- **Python source:** `uvicorn --reload` would solve it from source-mode, but the PyInstaller frozen EXE has no `.py` source paths watchdog can follow. Different reload story per artifact.
- **Frontend assets:** browsers cache aggressively on a static-mount. A naive `location.reload()` blows away every in-page state (open panels, popouts, palette cursors, form drafts).
- **Spawned Claude agents:** there's no IPC into a running `claude` REPL (same constraint as `agent-intelligence-control.md`). Updates have to ride the inbox channel and self-apply on the agent's next turn boundary.
- **Liveness:** `online.flag` mtime says "the process is alive" but not "the agent has actually turned recently." Need a separate signal.

## Fix — four tracks

### Track 1 — Backend hot-reload (source-mode only)

- `desktop_app.py` accepts `--reload`. When set AND not frozen, pass `reload=True, reload_dirs=[<window-manager>]` into `uvicorn.Config`. When set AND frozen, print a warning and ignore.
- Operator runs `.venv\Scripts\python.exe desktop_app.py --reload` for the dev loop, `RKOJ.exe` for the deploy artifact. Same code path inside, different reload story.

### Track 2 — Frontend SSE for asset changes (no context loss for CSS)

- `GET /api/sse/changes` returns `text/event-stream`. Long-poll connection per browser tab. Heartbeat comment `:hb` every 15s so dead connections drop and proxies don't buffer.
- Backend uses `watchdog` to monitor `./web/` recursively. Save -> classify by extension (`.css` -> `css`, `.js` -> `js`, `.html/.htm` -> `html`, image extensions -> `img`) -> debounce (0.4s; editors emit ~2 events per save) -> fan out to every subscriber queue via `loop.call_soon_threadsafe`.
- Frontend in `app.js` opens `new EventSource('/api/sse/changes?t=<token>')`. The `?t=` query token rides through because EventSource can't send `Authorization:` headers in modern browsers; the auth middleware already accepts query-param tokens (`request.query_params.get('t')`).
- On `file-changed`:
  - **CSS:** find the matching `<link rel="stylesheet">` by filename slug, bump its `href` with `?v=<mtime-ms>`. Browser refetches the stylesheet; **zero page reload, zero context loss**. (The bump param is mtime-derived so repeated saves dedupe naturally.)
  - **PNG/ICO/SVG:** same slug match on `<img src>` and `<link rel="icon">`. Bump src.
  - **JS:** toast `[UPDATE] new JS <path> — click toast to reload`. Operator chooses when to reload (preserves unsaved form state, popout cursor, etc.). One nag per file per session.
  - **HTML/template:** same nag pattern.
- Reconnect: 1s -> 30s exponential backoff on `onerror`. Survives a `--reload` worker respawn — the EXE/desktop window stays put; the SSE stream just re-establishes.

### Track 3 — Agent `[UPDATE]` inbox pattern (extends `[CONFIG]`)

DIRECTIVES.md ships a standing rule: every Sanctum agent, on `inbox_poll`, recognizes `[UPDATE] <subkind>` and self-applies on the next turn boundary. Five subkinds:

| Subkind | Action | Use case |
|---|---|---|
| `refresh-prefs` | re-read `_shared-memory/agent-prefs.json` for own entry | Operator changed accent / model / custom-prompt |
| `branch-switch new=<branch>` | `git checkout <branch>` in cwd | Operator promoted a feature branch |
| `palette-rebuild` | refetch the Cmd+K palette index (RKOJ-spawned only) | Operator added/removed palette entries |
| `knowledge-recheck slug=<name>` | re-read a brain entry | Operator added a discovery the agent should know |
| `noop` | ack with `[ACK alive uptime=<s>]` | Heartbeat probe — operator's "are you alive" |

Sender API: `POST /api/inbox/update-ping` with `{subkind, args, to?, exclude?}`. If `to` is set, single-agent; else broadcast to every currently-online agent (same `_inbox_mod.who_is_online()` source as `/api/sessions`). Tag is always `update`.

### Track 4 — Heartbeat / re-ping pattern

- `/api/sessions` rows now carry `last_inbox_check` (mtime of the agent's inbox cursor file) and `last_turn_marker` (mtime of `messages.jsonl` or `online.flag` fallback). The operator can distinguish ALIVE (recent inbox cursor write within seconds) from STALE (process alive but no turn activity in a while).
- Ribbon adds a "Ping all (heartbeat)" tile under MAINTAIN. Calls `POST /api/inbox/update-ping` with `{subkind: "noop"}`. Agents that ack within 30s = healthy.

## API surface

| Endpoint | Method | Body | Purpose |
|---|---|---|---|
| `/api/sse/changes` | GET | – | Long-poll SSE; events: `hello`, `file-changed`, `:hb` |
| `/api/inbox/update-ping` | POST | `{subkind, args?, to?, exclude?, from_agent?}` | One or many `[UPDATE]` messages |
| `/api/sessions` | GET | – | Now includes `last_inbox_check` + `last_turn_marker` per row |

## Code locations

- Backend SSE + watchdog + `/api/inbox/update-ping`: `D:\Sinister Sanctum\automations\window-manager\server.py` (hot-reload block + sessions freshness helper).
- Backend `--reload` flag: `D:\Sinister Sanctum\automations\window-manager\desktop_app.py` (in `main()` argparse + `run_uvicorn()`).
- Frontend SSE listener: `D:\Sinister Sanctum\automations\window-manager\web\app.js` (`rkojHotReload` IIFE after `bootstrap()` call).
- Frontend "Ping all" ribbon action: same file, `ribbonGroupsFor('agents')` MAINTAIN group + `handleRibbonAction('ping-all')`.
- Directive: `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md` top (`[UPDATE]` rule section).
- Dep: `D:\Sinister Sanctum\automations\window-manager\requirements.txt` (`watchdog>=4.0`).

## Discoveries (append-only, most-recent at top)

### 2026-05-19 by Sinister Sanctum master agent
EventSource doesn't carry `Authorization:` headers in any browser (HTML5 spec gap, no `withCredentials` workaround in this codebase since auth is HWID-locked Bearer). The existing auth middleware already accepts `?t=<token>` via `request.query_params.get('t')` — frontend just appends it to the SSE URL after reading `localStorage.sinister_token`. Cleaner than rolling cookies.

### 2026-05-19 by Sinister Sanctum master agent
watchdog emits 2-3 events per save on Windows (write + rename + close). 400ms per-path debounce in `_H._maybe_emit` collapses them. Without it the CSS-bump path runs three times in 80ms and the browser dev-tools network panel becomes unreadable.

### 2026-05-19 by Sinister Sanctum master agent
The PyInstaller frozen EXE can't honor `uvicorn --reload` because the bundled `server` module has no `__file__` watchdog can resolve back to a source path. Guarded explicitly with `_frozen()` check + warning print — operator gets clear feedback if they accidentally pass the flag to RKOJ.exe.

### 2026-05-19 by Sinister Sanctum master agent
Cross-thread emit pattern: watchdog runs on its own threadpool, the SSE subscribers live on FastAPI's asyncio loop. Captured the loop in `_hot_reload_startup` (`asyncio.get_running_loop()`) and `_hr_emit` uses `loop.call_soon_threadsafe(q.put_nowait, payload)` to cross over. Pure async-from-thread; no extra deps.

## Related topics

- [agent-intelligence-control](./agent-intelligence-control.md) — the `[CONFIG]` companion pattern this extends
- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md) — the workbench RKOJ.exe this hot-reloads into
- [cross-agent-coordination](./cross-agent-coordination.md) — `/api/inbox/broadcast` precedent that `update-ping` follows
