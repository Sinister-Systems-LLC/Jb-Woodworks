# Sinister Sanctum :: Window-Manager

Localhost-only, operator-only web console at **http://localhost:5077** for
launching + observing Claude sessions across all Sinister projects.

Purple DETECTOR-styled UI. Mirrors Sinister Panel's design tokens (no source
import). Lane-safe: stays inside `automations/window-manager/`; never touches
panel source, never edits `~/.claude/.mcp.json`.

## What it does (v1)

- **Left pane :: Projects** — every entry from `automations/session-templates/projects.json`. Click → launches `start-sinister-session.ps1 -Project X -Mode dev -NoNotepad`. Each card has 7 mode shortcuts (overview/dev/audit/deploy/push/debug/explore).
- **Center pane :: Active sessions** — every agent dir under `01_MEMORY/_inbox/<agent>/`. Online state = `online.flag` mtime < 5 min. Shows last 3 inbox messages. Inline textbox sends a new message via `_shared.inbox.inbox_send`.
- **Right pane :: Trophy case + recent runlogs** — live counts from Panel's `/api/dashboard/stats` + last 8 runlog manifests.
- **Auto-refresh** — every 30 s (configurable in `web/app.js`).
- **Health badge** — top-right of the header. Green = backend responsive.

## What it does NOT do (yet)

- No auth — localhost-only assumption.
- No embedded terminal viewer. The launched git-bash window is where you actually interact.
- No drag-rearrange / canvas / multi-session orchestration. Phase 8aj+ candidates.
- No process-level discovery of `claude.exe`. Heartbeat-based only.

## Run it

```powershell
# One-click (creates venv first run, installs deps, opens browser)
C:\Users\Zonia\Desktop\Open-Sanctum-Console.bat
```

Or manually:

```powershell
cd "D:\Sinister Sanctum\automations\window-manager"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 5077
# Then open http://localhost:5077 in any browser
```

## API surface

| Endpoint | Returns |
|---|---|
| `GET  /api/health` | `{ok, version, port, shared_ok}` |
| `GET  /api/projects` | All entries from projects.json |
| `GET  /api/sessions` | Agent presence + last 3 inbox messages per agent |
| `GET  /api/inbox/{agent}?limit=N` | Non-consuming tail of `messages.jsonl` |
| `POST /api/inbox/send` | `{to, body, sender, urgent, tags}` → enqueues via `_shared.inbox` |
| `GET  /api/recent-runlogs?limit=N` | Last N runlog manifests |
| `GET  /api/trophy` | Aggregated counts from panel + RKA |
| `POST /api/launch` | `{project, mode, no_notepad}` → spawns the PS1 launcher (detached) |

## File layout

```
window-manager/
├── server.py            FastAPI + endpoints
├── requirements.txt     fastapi / uvicorn / httpx / pydantic
├── README.md            this file
└── web/
    ├── index.html       single-page UI, 3-pane grid
    ├── app.js           vanilla state + fetch, 30s refresh
    ├── theme.css        purple panel-mirrored theme tokens
    └── skull.svg        SVG block-art skull (no APK PNG dependency)
```

## Lane discipline

- **Reads only:** `projects.json`, `_inbox/<agent>/online.flag`, `_inbox/<agent>/messages.jsonl` (tail), `script-runs/*.json`.
- **Writes via documented APIs:** `_shared.inbox.inbox_send` (writes to recipient's `messages.jsonl` + sender's `sent.jsonl`).
- **Spawns process:** `start-sinister-session.ps1` (detached PowerShell). Same surface every other Sanctum tool already uses.
- **Never writes:** panel source, product-repo source, `~/.claude/.mcp.json`, `_backups/`, `LICENSE`.

## Port choice

`5077` is unused locally: panel uses 5055 (express) / 3080 (next dev), letstext-admin uses 5099. If you actually conflict on 5077, edit `PORT = 5077` near the top of `server.py` and the URL in `Open-Sanctum-Console.bat`.

## Operator's intent (from Phase 8ai)

> "A UI-based system matching the Sinister APK / DETECTOR look + feel that manages Claude windows in the Sanctum. 'For now' = limited scope; this seeds a larger operator-internal tools surface."

Future-stretch ideas captured in `D:\Sinister Sanctum\inventions\2026-05-19-claude-window-manager.md`.
