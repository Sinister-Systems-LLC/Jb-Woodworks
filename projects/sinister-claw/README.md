# Sinister Claw

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-claw` :: branch `agent/sinister-claw/<topic>` :: purple accent
> **License:** AGPL-3.0-or-later
> **Platforms:** iOS + Android (React Native + Expo)

## What this is

**Sinister Claw** = our Sinister-branded mobile companion that lets the operator drive the entire fleet from their phone. Direct port + expansion of jcode's `Native OpenClaw` concept (operator's reference: "A native iOS application version of jcode... work with jcode on your personal machine's environment from your phone, via Tailscale. Openclaw like features will be bundled with this iOS application.")

Operator directive 2026-05-21:
> *"i want this we are going to make this for ios and android to be paired with our sinister panel all featreus there and same ui. start this in parrallel"*
> + *"make sure we are using jcode as a base and expanding on it"*

## jcode-as-base + Sinister expansion

| jcode Native OpenClaw | Sinister Claw |
|---|---|
| iOS-only (initially) | iOS + Android one codebase (Expo / React Native) |
| Tailscale tunnel to personal machine | Same — operator runs Tailscale, phone joins the tailnet, Claw POSTs to Sanctum / Forge / Mind APIs over the tunnel |
| jcode session control | Sinister Forge session control + Sinister Mind graph + Sinister Panel mirror |
| Single-agent focus | Multi-agent + multi-project (all 11 Sanctum projects in nav) |
| Generic terminal output | Sinister Panel UI mirrored 1:1 (Accounts / Videos / Devices / Phones / Plans / Forge agents / Mind graph) |
| MIT license | AGPL-3.0-or-later under RKOJ-ELENO authorship |

## Architecture

```
                              Operator's phone
                              (iOS / Android)
                                   │
                                   ▼  (over Tailscale)
                  ┌──────────────────────────────────────┐
                  │ Sinister Claw  (Expo / RN)           │
                  │ - Sinister theme (purple iOS 18      │
                  │   liquid glass, dark void)           │
                  │ - 6 tabs: Sanctum / Forge / Mind /   │
                  │   Panel / Projects / Settings        │
                  └────────────────┬─────────────────────┘
                                   │ HTTPS over Tailscale
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
   Sinister Panel              Sinister Forge        Sinister Mind
   (Hetzner production)        (operator PC :        (operator PC :
   snap.sinijkr.com            python -m forge,     :5079 Flask + D3)
   - Accounts / Videos          REST/SSE bridge      - graph JSON
   - Devices / Phones           on :5078 [NEW])      - search / filter
   - dispatch / loops           - spawn agent
                                - tail stdout/stderr
                                - terminate
```

## 7-tab nav (mirrors Sinister Panel + adds Forge/Mind)

1. **Sanctum** — fleet overview (master heartbeat, all 11 projects, recent commits, operator-action queue)
2. **Forge** — list of running agents, spawn new (mobile picker), tail per-pane stdout, kill button
3. **Mind** — embed Mind's web UI in a WebView (Flask :5079 over Tailscale)
4. **Panel** — Accounts / Videos / Devices / Phones / Dispatches (existing Panel API)
5. **Projects** — drill into one project, see its plans / PROGRESS / resume-points / brain entries
6. **Inbox** — cross-agent inbox messages addressed to the operator
7. **Settings** — Tailscale connection, theme, auth token, biometric unlock

## Phases

| Phase | What | Status |
|---|---|---|
| **PH0** | Scaffold (this commit) — Expo + RN + TypeScript + theme | ✅ |
| **PH1** | App shell: 7 tabs, navigation, Sinister theme (purple iOS 18 liquid glass) | next |
| **PH2** | Sanctum tab — read /api/heartbeats + /api/master-plan from Sanctum (new endpoints needed on master) | next |
| **PH3** | Forge bridge — Forge gains a REST/SSE server on :5078 that mobile can hit; List + spawn + tail + kill | week+ |
| **PH4** | Mind tab — WebView pointing at http://<sanctum-pc-tailnet>:5079/ | next |
| **PH5** | Panel tab — re-use existing snap.sinijkr.com endpoints (already JSON-API capable) | week+ |
| **PH6** | Projects tab — read projects.json + per-project resume-points + plans | week+ |
| **PH7** | Inbox tab — read _shared-memory/inbox/me/ + acknowledge UI | week+ |
| **PH8** | Settings tab — Tailscale magic-DNS picker + auth token + biometric (FaceID/fingerprint) | week+ |
| **PH9** | Push notifications — Sanctum master sends to operator's device when an agent breakthrough lands | week+ |
| **PH10** | Background sync — even when app closed, fetch last-N PROGRESS top-lines for operator's wake-up screen | week+ |
| **PH11** | Operator's voice command — Siri Shortcuts / Google Assistant intents that spawn a Forge agent | week+ |

## Tech stack

- **Expo** (React Native + Hermes) — one codebase, ships to TestFlight + Play Internal in ~minutes
- **TypeScript** — type safety across the API client + screens
- **React Navigation** — bottom-tab nav (7 tabs)
- **react-native-reanimated** — iOS-style spring animations
- **expo-blur** — real backdrop-filter blur for the liquid-glass aesthetic
- **expo-secure-store** — auth token storage
- **WebView** (Expo) — embed Sinister Mind's D3 graph + Sinister Panel
- **EventSource polyfill** — SSE for live Forge subprocess output

## License + authorship

AGPL-3.0-or-later. Every file: `Author: RKOJ-ELENO :: <date>`. Inspired-by attribution for jcode in `NOTICES.md` (jcode is MIT, openclaw concept is an architecture pattern not literal code).

## Cross-references

- `projects/sinister-forge/` — Forge needs a REST/SSE bridge for mobile (PH3)
- `projects/sinister-mind/` — Mind's :5079 already serves a web UI; Claw WebView embeds it (PH4)
- `projects/sinister-panel/source/` — existing JSON API; Claw reuses (PH5)
- `_shared-memory/knowledge/research-import-pipeline.md` — jcode openclaw arrived via this pipeline
- `Desktop\Sinister Start.bat` — operator's PC entry point (Claw is the phone counterpart)
