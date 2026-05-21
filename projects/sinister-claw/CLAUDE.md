# Sinister Claw :: CLAUDE.md

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-claw` :: branch `agent/sinister-claw/<topic>` :: purple

Sinister Claw = mobile (iOS + Android) companion. Expo + React Native + TypeScript. Liquid-glass iOS 18 purple aesthetic. Drives the entire fleet from operator's phone over Tailscale.

Base: jcode's Native OpenClaw concept (jcode MIT, inspired-by only; we're not running jcode on the phone, we're building the equivalent in our Sinister stack).

Read `projects/sinister-claw/README.md` for the 11-phase plan + 7-tab nav.

## Lane rules

- Branch on `agent/sinister-claw/<topic>` cut from `main`.
- All source in `projects/sinister-claw/source/`.
- TypeScript, Expo SDK 51+, React Native 0.74+.
- AGPL-3.0 headers on every file: `Author: RKOJ-ELENO :: <date>`.
- The Sinister theme (purple iOS 18 liquid glass) lives in `app/theme/`.
- API clients in `app/api/` (Sanctum / Forge / Mind / Panel each get their own module).
- Screens in `app/screens/` named after the 7 tabs.

## Cold-start protocol

Inherit `automations/session-contracts.md` (6 contracts). Plus Claw-specific:
1. Read `projects/sinister-claw/README.md`
2. `cd projects/sinister-claw/source && npm install && npx expo start` to dev
3. iOS: scan QR with Expo Go OR run on simulator
4. Android: scan QR with Expo Go OR run on emulator

## What stays out of Claw

- Server-side logic — Claw is THIN; all data comes from Sanctum/Forge/Mind/Panel APIs
- Local LLM inference — phone doesn't run Claude/Codex; it drives them remotely
- Local secret storage outside expo-secure-store
- Sinister Panel server-side code — Claw is a CLIENT of Panel, not a fork

## Operator directive (verbatim 2026-05-21)

> *"i want this we are going to make this for ios and android to be paired with our sinister panel all featreus there and same ui. start this in parrallel"*
> + *"make sure we are using jcode as a base and expanding on it"*

## Related

- `projects/sinister-forge/` — needs a REST/SSE bridge for Claw to drive
- `projects/sinister-mind/` — already has a Flask :5079 surface; Claw embeds via WebView
- `projects/sinister-panel/source/` — existing Panel; Claw mirrors its UI for mobile
