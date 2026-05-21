# Sinister project group

15 projects under the "Sinister" brand. The ecosystem the operator has built for Snapchat / TikTok / Bumble account-creation, RKA attestation, phone-stack tooling, panel infrastructure, and supporting helpers.

## Projects

| Project | One-line state |
|---|---|
| [Snap-Signer](./Snap-Signer/) | Phone-stack hunt. Pure-API SS03 wall. Yurikey52 + PI 0/3 blockers. |
| [Sinister-Panel](./Sinister-Panel/) | Live at snap.sinijkr.com. 4 containers healthy. 24/7 Automation Cockpit. |
| [Sinister-APK](./Sinister-APK/) | APK build/install tooling. |
| [Sinister-RKA](./Sinister-RKA/) | RKA daemon. ⚠️ Yurikey51 root cert expires 2026-05-24. |
| [Sinister-Snap-EMU](./Sinister-Snap-EMU/) | Pure-API workstream. PM10-N: AppRegisterBegin grpc=12. |
| [Sinister-TikTok-EMU](./Sinister-TikTok-EMU/) | TikTok sister-track. RESUME-HERE.md (213 KB) canonical. |
| [Sinister-Bumble-EMU](./Sinister-Bumble-EMU/) | Bumble EMU API. Same-shape track. |
| [Library-of-Alexandria](./Library-of-Alexandria/) | Mirror/aggregation. Most recent anchor 2026-05-17 PM late. |
| [Kernel-SU-Setup](./Kernel-SU-Setup/) | Sinister-Detector v0.95.0 + Rooting Guide + KPM modules. |
| [Sinister-Sandbox](./Sinister-Sandbox/) | Scratch space. |
| [Sinister-TG](./Sinister-TG/) | Telegram-related tooling. |
| [Sinister-iMessage-Bridge](./Sinister-iMessage-Bridge/) | iMessage bridging. |
| [Sinister-Workstation-Setup](./Sinister-Workstation-Setup/) | Workstation bootstrap. |
| [Sinister-Emulator-Bundle](./Sinister-Emulator-Bundle/) | AOSP emulator track (HOLDING). |
| [sinister-helper](./sinister-helper/) | Helper utility scripts. |

## Per-project layout

Each project dir has:
- `source/` — directory **junction** to the canonical Desktop location (transparent — git/builds/bats all work)
- `_README.md` — project-specific one-pager
- `_vault/` — Obsidian vault entry (wiki-links to source memory + hub cross-references)

## Group vault

Open `_vault/_index.md` in Obsidian for the group-level navigator.

## Cross-references

- Hub capsules: `..\..\Sinister Skills\03_PROJECTS\<project>.md`
- Hub memory: `..\..\Sinister Skills\01_MEMORY\<project>\`
- Drive master vault: `..\..\_vault\`

## ⚠️ Active blockers (across the group)

1. **Yurikey51 root cert expires 2026-05-24** — operator action by 2026-05-23 (source Yurikey52 from yuriservice)
2. **PI 0/3 on P1 + P2** — interactive Settings re-auth on both phones
