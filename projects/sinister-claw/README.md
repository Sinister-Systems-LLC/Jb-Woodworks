# RKOJ Mobile (formerly Sinister Claw)

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-claw` (filesystem) / **app slug:** `rkoj` :: branch `agent/sinister-claw/<topic>` :: purple accent
> **License:** AGPL-3.0-or-later
> **Platforms:** iOS + Android (React Native + Expo)

## What this is

**RKOJ Mobile** is the mobile counterpart to the **RKOJ desktop workstation** (PyQt6, see `tools/sinister-rkoj-qt/`). It lets the operator drive the entire Sinister Sanctum fleet from their phone over Tailscale — same branding, same nav shape, same chip tabs, same `EVE` persona.

Operator directive (verbatim 2026-05-21):
> *"grab also the mobile ui we were making so i can mange claude agents from my phone. ios and android. call it RKOJ and use same logo. Brand ui just like the rkoj workstaton we are making and ultimately just like the sinister panel"*

## Why "claw" renamed to "rkoj-mobile"

The original codename was **Sinister Claw** (a port of jcode's Native OpenClaw concept). The operator directive on 2026-05-21 collapsed the mobile lane into the RKOJ brand:

- `app.json` `name` / `slug` / `scheme` → `RKOJ` / `rkoj` / `rkoj`
- `package.json` name → `rkoj-mobile`
- iOS bundle id → `com.rkojeleno.rkoj.ios`
- Android package → `com.rkojeleno.rkoj`
- Icon + adaptive icon + splash + favicon → the RKOJ logo (same source PNG as `automations/window-manager/web/rkoj-logo.png`)

The filesystem path `projects/sinister-claw/source/` is preserved so git history stays linear. The on-device product is **RKOJ**.

## Branding -- one source of truth

All hex values live in `app/theme/tokens.ts`. The palette is the operator-canonical Sanctum purple (matches `tools/sinister-rkoj-qt/sinister_rkoj_qt/theme.py` + Sinister Panel CSS variables verbatim):

| Token            | Hex        |
|------------------|------------|
| `purpleAccent`   | `#A06EFF`  |
| `purpleDeep`     | `#7A3DD4`  |
| `purpleHalo`     | `#C39DFF`  |
| `lightPurple`    | `#E8D6FF`  |
| `bg`             | `#0E0A14`  |
| `bgGlass`        | `#15131A`  |
| `bgGlow`         | `#2A1F3D`  |
| `borderGlass`    | `#3A2A55`  |
| `soft`           | `#999AB0`  |
| `dim`            | `#6E6E84`  |
| `greenAccent`    | `#85C86E`  |

Consume via the hook:

```ts
import { useTheme } from "@/theme";
const { tokens, spacing, radii } = useTheme();
// use tokens.purpleAccent etc. -- never inline hex.
```

A legacy `colors` alias remains in `app/theme/colors.ts` so the pre-rebrand screens (`SanctumScreen`, `ForgeScreen`, ...) still compile.

## Nav shape (mirrors RKOJ desktop + Sinister Panel)

### Drawer left (RkojSidebar)
- **WORKSPACE**  — Overview · Agents · Projects
- **OPERATIONS** — Phones · Vault · Watchdog
- **AI**         — Brain · MCP · Skills
- **SYSTEM**     — Settings · Account

Mascot block at top: RKOJ logo + `E V E` label + `R K O J` sub-label.

### Top header (RkojHeader)
- RKOJ logo (tap = open drawer) + title `RKOJ Mobile` + subtitle `EVE · Sanctum Fleet`
- 3 chip tabs: **Agents (●)** / **Phones (#)** / **Workstation (⚙)**
- 4 action icons: alerts (!) · inbox (⏰) · search (⌕) · settings (⚙)

### Body (chip-driven)
- **Agents** — vertical list of agent cards. Each: project header + EVE label + mode pill + status dot + close (×) + terminal log SSE scroll + send-input row. CTA `+ SPAWN AGENT` opens the spawn sheet.
- **Phones** — `adb devices` list with model / serial / state / transport. Tap → bottom sheet (Identity / Heartbeat / RKA arm+kill / Open scrcpy / ADB shell / Logcat tail SSE).
- **Workstation** — grid of action tiles (Vault · Brain · Watchdog · Backups · MCP probe). Tap → calls forge bridge endpoint, renders result inline.

## Forge bridge endpoints

All API calls go to the operator's PC over Tailscale at `http://<host>:5078`. Configure via Settings (stored in `expo-secure-store` under `claw.sanctum.*`).

```
GET    /api/sanctum/heartbeats               -> Sanctum master heartbeats
GET    /api/sanctum/projects                 -> 11+ project metadata
GET    /api/sanctum/commits?limit=20         -> recent commits
GET    /api/sanctum/inbox?limit=50           -> cross-agent inbox

GET    /api/forge/agents                     -> list live agents
POST   /api/forge/spawn                      -> spawn a new agent (body: SpawnParams)
DELETE /api/forge/agents/:id                 -> terminate agent
SSE    /api/forge/agents/:id/stream          -> tail stdout/stderr (event: line)
POST   /api/forge/agents/:id/input           -> write to agent's stdin

GET    /api/devices                          -> adb devices list
GET    /api/devices/:serial                  -> identity + heartbeat detail
POST   /api/devices/:serial/shell            -> adb shell (body: {cmd})
POST   /api/devices/:serial/scrcpy           -> open scrcpy on host
POST   /api/devices/:serial/rka/arm          -> arm RKA kill-switch
POST   /api/devices/:serial/rka/kill         -> trigger RKA kill
SSE    /api/devices/:serial/logcat           -> tail logcat

GET    /api/workstation/vault/status         -> vault daemon probe
GET    /api/workstation/brain/probe          -> knowledge index probe
GET    /api/workstation/watchdog/status      -> heartbeat watcher
POST   /api/workstation/backups/run          -> trigger backup snapshot
GET    /api/workstation/mcp/probe            -> MCP server health
```

## Build for iOS / Android

The actual compile is an operator-action (Expo EAS Build or `expo run`):

```bash
cd projects/sinister-claw/source
npm install                  # installs Expo SDK + react-navigation + RN deps

# Local dev (scan QR with Expo Go on the phone)
npx expo start

# iOS simulator
npx expo run:ios

# Android emulator / device
npx expo run:android

# Production builds (requires EAS account)
npx eas build --platform ios
npx eas build --platform android
```

Bundle identifiers (set in `app.json`):
- iOS: `com.rkojeleno.rkoj.ios`
- Android: `com.rkojeleno.rkoj`

App icon source: `assets/icon.png` (mirrors `automations/window-manager/web/rkoj-logo.png`).

## File layout

```
projects/sinister-claw/source/
  app.json                    # Expo manifest (RKOJ name + bundle ids + icons)
  package.json                # rkoj-mobile, Expo SDK 51+
  index.ts                    # Expo registerRootComponent stub
  assets/
    icon.png  adaptive-icon.png  splash-icon.png  favicon.png
    rkoj-logo.png  sinister-logo.png  skull.svg
  app/
    index.tsx                 # ROOT -- drawer + header + chip-switched body + splash
    theme/
      tokens.ts               # *** SINGLE SOURCE OF TRUTH for branding ***
      colors.ts               # legacy shim onto tokens
      index.ts                # re-exports
    components/
      RkojLogo.tsx            # bitmap logo, sized
      RkojHeader.tsx          # title + 3 chip tabs + 4 action icons
      RkojSidebar.tsx         # mascot + 4-section nav
      SplashOverlay.tsx       # purple-gradient splash
      GlassPanel.tsx          # liquid-glass surface
    views/
      AgentsTabView.tsx       # multi-agent panes with SSE log + input
      PhonesTabView.tsx       # device list + bottom-sheet detail
      WorkstationTabView.tsx  # action tile grid
    api/
      sanctum.ts              # SecureStore-backed base URL + Sanctum endpoints
      forge.ts                # agent spawn / list / SSE / terminate
      devices.ts              # adb / scrcpy / RKA / logcat-SSE
      workstation.ts          # vault / brain / watchdog / backups / mcp
      forgeBridge.ts          # unified re-export
    screens/                  # legacy 7-tab screens (kept for back-compat tests)
      ...
```

## Cross-references

- `tools/sinister-rkoj-qt/` — RKOJ desktop workstation (the PyQt6 reference for chrome + chip tabs + sidebar)
- `projects/sinister-forge/source/forge/bridge/` — REST/SSE bridge on :5078 (PH3 target)
- `projects/sinister-mind/` — Mind D3 graph (PH4 WebView target)
- `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/components/` — sidebar.tsx + tab-header.tsx reference
- `automations/window-manager/web/rkoj-logo.png` — source icon
