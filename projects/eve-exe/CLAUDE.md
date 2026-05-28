# CLAUDE.md — Eve EXE

**Author:** memory-structure-rollout :: 2026-05-27

Per-lane CLAUDE.md for the `eve-exe` project. Inherits sanctum-wide doctrine
from `D:\Sinister Sanctum\CLAUDE.md`. Add lane-specific rules below.

## Lane scope
- Tag: (scaffolded — fill in lane purpose)
- Tier: (unset)
- Sibling lanes: (none)

## Memory infra
- PROGRESS:        `_shared-memory/PROGRESS/Eve EXE.md`
- Heartbeat:       `_shared-memory/heartbeats/eve-exe.json`
- Resume points:   `_shared-memory/resume-points/Eve EXE/`
- Inbox:           `_shared-memory/inbox/eve-exe/`

## MX-EVE-ICON-BORDERLESS (2026-05-27)
- Icon master: `build/icon.ico` + `build/icon.png` (256x256, transparent-padded square).
- Source PNG: `C:/Users/Zonia/Desktop/2026-05-23T133146Z-banner-hero-statement.png` (992x1056, RGB no alpha — caveat below).
- `electron-builder.json` pins `win.icon` to `build/icon.ico` so MX-EVE-FULL picks it up.
- Borderless CAVEAT: source PNG has no alpha channel; only the padding around the hero is transparent, the hero contents remain a solid rectangle. Re-export the source with a transparent background and rerun this lane for a true logo-shape icon.

## MX-EVE-FRAMELESS (TODO — pending Electron source land)
The eve-exe project currently has only `src/integration/` (TypeScript glue, no Electron main process). When the Electron main lands, create the BrowserWindow with:
```ts
new BrowserWindow({
  frame: false,
  titleBarStyle: 'hidden',
  // transparent: true   // enable only if renderer fully supports it
  webPreferences: { preload: '...', contextIsolation: true },
});
```
Renderer must include a drag-region (CSS `-webkit-app-region: drag`) and custom min/max/close buttons that IPC to `BrowserWindow.minimize/maximize/close`. Preserve the `bootstrapEveIntegration(ipcMain, '.../runtime-integration.json')` call from `src/integration/index.ts`.
