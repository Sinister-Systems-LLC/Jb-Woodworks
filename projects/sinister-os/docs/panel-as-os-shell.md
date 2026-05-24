# Panel-as-OS-Shell — Wiring Design

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** P1 design lock (operator-redirected 2026-05-24: "make everything look like my sinister panel").

## The decision

The **Sinister Panel** (Next.js 15 + React 19 + Tailwind 4 dashboard at `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/`) becomes the **default desktop shell** of Sinister OS.

When the operator boots Sinister OS, they see the Panel — full-screen, no chrome, no taskbar, no Windows-style desktop metaphor. The Panel **is** the desktop.

## Why this approach (vs alternatives)

| Path | Pros | Cons | Verdict |
|---|---|---|---|
| **Web kiosk (Hyprland + Chromium --kiosk)** | Re-uses the existing Panel source unmodified; ships in P1; trivially upgradable (rebuild + ship); zero new framework | Chromium overhead (~250 MB RAM); window-management hand-off requires custom IPC for "open app X" actions | **CHOSEN** |
| Tauri wrapper | Native menus, smaller footprint, better OS integration | Adds a Rust build to the critical path; Tauri-on-Wayland still has rough edges; would require maintaining a parallel Tauri config | Defer to P3 once Panel UX is locked |
| Electron wrapper | Best ecosystem | Heaviest runtime; Anthropic-style telemetry concerns; redundant with Chromium kiosk | Rejected |
| Custom GTK4 / Qt shell | Lightest | Throws away the Panel React codebase | Rejected — directly contradicts operator directive |

## How it works (P1)

```
┌─────────────────────────────────────────────────────────────────┐
│ tty1 (root)                                                     │
│   └── /root/.automated_script.sh                                │
│       └── exec Hyprland                                         │
│           └── hyprland.conf: exec-once = sinister-panel-kiosk.sh│
│               ├── starts: node /srv/sinister-panel/server.js    │
│               │           (Next.js standalone, port 3080)       │
│               └── exec chromium --kiosk --ozone-platform=wayland│
│                          http://127.0.0.1:3080/                 │
└─────────────────────────────────────────────────────────────────┘
```

Hotkey escape hatches (defined in `airootfs/etc/skel/.config/hypr/hyprland.conf`):

| Hotkey | Action |
|---|---|
| `Super+Q` | Open a terminal (kitty, foot, or xterm fallback) |
| `Super+Shift+Q` | Kill the active window (drops back to Panel) |
| `Super+Return` | Re-launch Panel kiosk (recovery if killed) |
| `Super+Ctrl+R` | Reload Hyprland config |

## P2 work — wiring Panel actions to system actions

The Panel UI shows "Fleet / Proxies / Browsers / EVE AI / Admin" buttons. P2 makes those buttons actually do things on the local OS:

1. **Add `panel-backend` systemd service** — packages `panel/backend/` (existing Python service per `panel/docker-compose.yml`) as a system service listening on `127.0.0.1:5055`. The Panel's `next.config.mjs` already rewrites `/api/*` to `BACKEND_URL` (default `http://localhost:5055`), so once the backend is up, the rewrite path works as-is.
2. **Add Sinister Bus DBus bridge** — `sinister-bus` MCP exposed over DBus so the Panel can call `sinister.bus.Heartbeat()` etc. without HTTP friction.
3. **Add `eve-launch` URL scheme** — `eve://open?project=sinister-forge` registered as a desktop handler so the Panel can launch apps via `<a href>`.
4. **Embed EVE chat overlay** — the existing Panel chat UI talks to the EVE daemon socket via a Next.js API route at `/api/eve/chat`.

## P3 work — EVE-as-system-shell

The Panel kiosk + EVE daemon together replace what Explorer.exe + UAC + Task Scheduler do on Windows:

- File browser tab in Panel reads/writes through `eve.fs.*` DBus methods (scoped to operator's home + `/srv/sinister`).
- System settings tab calls `eve.system.*` methods (network, audio, display).
- Voice surface (`tools/sinister-voice`) is always-on; wake-word "EVE" pipes to the daemon socket.
- Hotkey overlay (GTK4 `eve-overlay`) is the only popup UI other than the Panel — it appears for destructive-action confirmation.

## P4 work — the gaming + creative stack inside Panel

A "Games" tab in Panel that talks to Steam, Lutris, Heroic via their CLIs through `eve.apps.*`:

- Game library aggregator (similar to Playnite's data model)
- Launch / install / update / verify-integrity via the per-launcher CLI
- Proton-GE version manager
- Per-game gamescope launch options stored in the Panel's existing database

## Risks / open questions

1. **Chromium memory footprint** — kiosk Chromium on a 16 GB machine running games alongside is fine. On 8 GB it's tight. Mitigation: P3 swap to Tauri if measured RAM under 8 GB becomes a problem.
2. **Panel security model** — kiosk Chromium running as the eve user with sudoers NOPASSWD means a Panel XSS = root. Mitigation: strict CSP (already in Next.js defaults), no untrusted user input rendered HTML, run Panel under AppArmor.
3. **Recovery if Panel crashes** — `sinister-panel-kiosk.sh` will be re-runnable via `Super+Return`. P2 will add a systemd unit that auto-restarts the Node server.
4. **Cross-lane drift** — Panel is owned by the `sinister-panel` lane. This lane (sinister-os) must NEVER edit Panel source. `bake-panel.sh` enforces this by copying source to a build-staging dir and patching the copy.
