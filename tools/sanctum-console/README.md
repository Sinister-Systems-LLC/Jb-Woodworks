# sanctum-console

The Sanctum's web-based window manager and operator dashboard. FastAPI backend with a themed browser UI for surveying running agents, projects, and recent sessions.

## What it does

Serves a local web console that:

- Lists projects, lanes, and active agents.
- Surfaces recent session activity and capture stubs.
- Hosts the Sanctum theme (skull glyph + purple ramp) as the visual home base.

Run it locally and it binds to `http://127.0.0.1:<port>`; opening the desktop shortcut launches the server and pops the console in the default browser.

## How to invoke (operator-facing)

Double-click the desktop shortcut:

```
C:\Users\Zonia\Desktop\Open-Sanctum-Console.bat
```

The .bat activates the bundled `.venv`, starts the FastAPI server, and opens the console.

## Implementation files (absolute paths)

- `D:\Sinister Sanctum\automations\window-manager\server.py`
- `D:\Sinister Sanctum\automations\window-manager\web\index.html`
- `D:\Sinister Sanctum\automations\window-manager\web\app.js`
- `D:\Sinister Sanctum\automations\window-manager\web\theme.css`
- `D:\Sinister Sanctum\automations\window-manager\web\skull.svg`
- `D:\Sinister Sanctum\automations\window-manager\requirements.txt`
- `D:\Sinister Sanctum\automations\window-manager\.venv\` (local virtualenv)
- `C:\Users\Zonia\Desktop\Open-Sanctum-Console.bat`

## Dependencies

- Python 3.10+
- FastAPI + Uvicorn (see `requirements.txt`)
- Modern desktop browser (Edge / Chrome / Firefox)

## Lane

master / Sanctum orchestration

## Captured

2026-05-19

## Status

shipped

## Linked-inventions

- (none yet)

## Changelog

- **2026-05-19** — Initial registration. Web UI shipped. **In-flight upcoming features:** desktop EXE wrapper via pywebview, LAN-accessible mode with token auth, QR code for phone hand-off, responsive mobile UI consuming the panel-side iOS blue token set.
