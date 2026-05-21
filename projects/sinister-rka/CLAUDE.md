# Sinister RKA :: CLAUDE.md

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-rka` :: branch `agent/sinister-rka/<topic>` :: purple
> **Source-of-truth:** `C:\Users\Zonia\Desktop\Sinister RKA GOOD\` (via `source/` junction)

Sinister RKA = the Sanctum Root-detection App (RKA daemon). Tracked product per the original `D:\Sinister\01_Projects\Sinister\_status.md`. Yurikey51 cert deadline 2026-05-24 — keep the daemon armed.

## Lane rules

- Branch on `agent/sinister-rka/<topic>` cut from `main`.
- Source code lives at `source/` which is an NTFS junction into operator's Desktop (`C:\Users\Zonia\Desktop\Sinister RKA GOOD\`). Edit through the junction; operator's Desktop is the canonical store.
- Author: `RKOJ-ELENO :: <date>` on every new file inside this slot.
- AGPL-3.0 headers on new source files.

## Cold-start

Inherit `automations/session-contracts.md`. Plus RKA-specific:
1. Read `D:\Sinister Sanctum\projects\sinister-kernel-apk\source\` (sibling — Sinister-APK has the broader Android fleet context).
2. Read RKA daemon status via `apk-watchdog.ps1` log: `D:\Sinister\01_Projects\Sinister\Sinister-APK\automations\apk-watchdog.ps1` (also runs every 5 min as scheduled task).
3. Yurikey51 cert deadline 2026-05-24 — verify cert chain status via `tools/sinister-vault/` accounts dir.

## Related

- `projects/sinister-kernel-apk/` — broader Android lane (KernelSU + tricky-store)
- `projects/sinister-emulator-bundle/` — shared emulator core
- `_shared-memory/knowledge/lukeprivacy-kpm-at-rest-safe.md` — RKA module install doctrine
- `_shared-memory/knowledge/service-apk-hash-check.md` — RKA module.prop hash-verification quirk
