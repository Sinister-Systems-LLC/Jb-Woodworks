# Sinister OS Mobile — Architecture (layered view)

> Author: RKOJ-ELENO :: 2026-05-24

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            OPERATOR / EVE                                │
│  Voice / Sinister Panel UI / Hotword / Hardware buttons / Fingerprint    │
├──────────────────────────────────────────────────────────────────────────┤
│                       SINISTER OVERLAY LAYER                             │
│                                                                          │
│  com.sinister.eve         com.sinister.panel       com.sinister.vault    │
│  (system_app priv)        (user app, theme-bridge) (sync client)         │
│      │  AIDL              │   Compose +            │ Syncthing-bound     │
│      │  /dev/socket/      │   skeleton tokens      │ /data/sinister/     │
│      │  sinister-eve      │                        │                     │
│                                                                          │
│  com.sinister.mind        com.sinister.chatbot     com.sinister.rkoj     │
│  (memory bot Android)     (chat ui client)         (workbench mobile)    │
├──────────────────────────────────────────────────────────────────────────┤
│                       ANDROID APP FRAMEWORK                              │
│  ActivityManager / PackageManager / WindowManager / NotificationManager  │
│  (vendor: AOSP or GrapheneOS-hardened — TBD P1)                          │
├──────────────────────────────────────────────────────────────────────────┤
│                       SYSTEM SERVER + HALs                               │
│  audio HAL / camera HAL / sensor HAL / radio HAL / wifi HAL              │
│  (Google's Pixel 6a vendor blobs — kept binary, sourced at flash time)   │
├──────────────────────────────────────────────────────────────────────────┤
│                       LINUX KERNEL (5.10 LTS)                            │
│  Pixel kernel + private/google-modules + minimal Sinister kernel mods    │
│  (optionally KernelSU for root-capable variant — Q9 operator decision)   │
├──────────────────────────────────────────────────────────────────────────┤
│                       BOOTLOADER + AVB                                   │
│  fastboot / Verified Boot 2.0 / vbmeta / dm-verity                       │
│  (custom AVB key path documented; operator-gated decision)               │
├──────────────────────────────────────────────────────────────────────────┤
│                       HARDWARE                                           │
│  Pixel 6a — Tensor G1, 6 GB, 128 GB UFS, 6.1" OLED, Titan M2             │
└──────────────────────────────────────────────────────────────────────────┘
```

## Mesh layer (lateral to the stack above)

```
EVE on Pixel 6a  ←Tailscale→  EVE on Hetzner  ←Tailscale→  EVE on Operator-PC
       ↓                            ↓                            ↓
   on-device                    cloud worker                  workbench
   (voice / UI)                 (heavy lifts)                 (canon)
```

EVE service routes work to the right node based on battery + thermal + work-class.

## EVE control flow (single voice utterance example)

```
1. wake-word "hey eve" detected by whisper-cpp on AON core
2. Tensor G1 AP wakes; whisper continues; transcript → EVE service via /dev/socket/sinister-eve
3. EVE service parses intent; routes:
   - "open panel"           → Activity intent to com.sinister.panel
   - "start vault sync"     → AIDL call to com.sinister.vault
   - "spawn a worker"       → mesh dispatch to Hetzner EVE node
   - "factory reset"        → operator confirm via fingerprint, then settings provider write
4. EVE responds via Notification + TTS (on-device)
5. Heartbeat to _shared-memory/heartbeats/sinister-os-mobile.json via vault-synced path
```

## Sinister fleet on-device map

| App | Package | UI surface | Backend |
|---|---|---|---|
| EVE service | `com.sinister.eve` | (no UI; foreground notification) | AIDL + unix socket |
| Sinister Panel | `com.sinister.panel` | Compose + skeleton theme | Sanctum vault REST/WS |
| Sinister Vault | `com.sinister.vault` | thin Compose | Syncthing (gomobile bind) |
| Sinister Mind | `com.sinister.mind` | Compose | local SQLite + remote brain |
| Chatbot | `com.sinister.chatbot` | Compose | Sanctum chatter route |
| RKOJ mobile | `com.sinister.rkoj` | Compose (operator workbench mobile-view) | Sanctum REST |

## What's NOT in v1

- Bespoke launcher (operator uses Pixel Launcher or Lawnchair).
- Bespoke camera app (Pixel camera stays).
- Bespoke dialer / messaging (AOSP defaults; can revisit P6 backlog).
- Bespoke browser (Vanadium from GrapheneOS if that's our base; else Chromium upstream).

## Open architecture questions (resolved during P0-P1)

- Should EVE service own the voice surface, or should voice be its own `com.sinister.voice` package? (Lean: own package, EVE consumes events. Cleaner separation, easier to test.)
- Compose theme bridge — Material 3 dynamic color vs skeleton tokens override? (Lean: skeleton tokens win for fleet consistency per UI hard-canonical 2026-05-24.)
- Background work — WorkManager vs Foreground Service vs JobScheduler? (Lean: foreground service for EVE + voice; WorkManager for periodic vault sync.)
- Battery — duty-cycle voice listening 100% / 50% / hotword-only? (Operator Q5.)
