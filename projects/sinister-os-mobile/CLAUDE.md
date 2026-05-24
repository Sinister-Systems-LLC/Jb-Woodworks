# CLAUDE.md — Sinister OS Mobile (Pixel 6a)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** `sinister-os-mobile` :: branch `agent/sinister-os-mobile/<short-topic>` :: purple accent
> **Lane heartbeat:** `_shared-memory/heartbeats/sinister-os-mobile.json`
> **PROGRESS log:** `_shared-memory/PROGRESS/Sinister OS Mobile.md`

This file is the lane discipline for any EVE session opened with the working directory at `D:\Sinister Sanctum\projects\sinister-os-mobile\`. It inherits from `D:\Sinister Sanctum\CLAUDE.md` (Sanctum master) — read that first, then this file.

## Mission

Build **Sinister OS Mobile**: an EVE-controlled custom Android distribution targeting the **Google Pixel 6a** (codename `bluejay`, Tensor G1 SoC). The OS must give EVE root-equivalent control of the device, preinstall the Sinister fleet (Panel, Vault, Mind, RKOJ-mobile companion, Chatbot client), and keep the operator's daily-driver experience intact (calls, signal, GApps if operator wants them).

Sister project: `projects/sinister-os/` (Linux PC replacement). The two share the EVE-control surface design + Sinister Panel theme, diverge on kernel/userspace.

## What this lane owns

- `projects/sinister-os-mobile/` — all of it
- `_shared-memory/PROGRESS/Sinister OS Mobile.md`
- `_shared-memory/heartbeats/sinister-os-mobile.json`
- Brain rows tagged `sinister-os-mobile` in `_shared-memory/knowledge/_INDEX.md`
- Branches matching `agent/sinister-os-mobile/*`

## What this lane NEVER touches

- Any other project's `source/` or `memory/`
- `~/.claude/.mcp.json` (operator-owned)
- The operator's physical Pixel 6a (until Phase 5 operator-gated cutover)
- `main` branch direct pushes (routes through `sanctum-auto-push` daemon)

## Hard rules for this lane

1. **Emulator-first.** Every build, every flash, every EVE-integration test runs on `cuttlefish` virtual device (or Android Studio AVD) BEFORE physical Pixel 6a. cvd is the canon — same pattern the emu lanes use.
2. **Phase boundaries are operator-gated.** P0 → P1 requires operator click. P1 → P2 requires operator click. Etc. Physical flash (P5) requires operator typing `sinister-os-mobile flash-pixel` interactively.
3. **No vendor binary leaks.** Pixel firmware blobs stay outside git (`.gitignore` covers `vendor/google_devices/`, `vendor/firmware/`). Public BSP fetch URLs documented, not contents.
4. **GApps + signed boot are operator-decisions.** Lane proposes options (GrapheneOS-style sandboxed GApps vs MicroG vs no Google), operator picks. AVB / locked-bootloader path is operator-gated (loses root, but matches Pixel security baseline).
5. **Doctrine self-audit per Sanctum's no-bullshit doctrine.** Every claim of "boots" / "flashes" / "EVE controls" carries a cuttlefish session + adb receipt OR a physical-device serial + operator-confirmed observation. Never claim shipped without one of those.

## EVE-control design constraints

- EVE runs as a **privileged Android system service** (`com.sinister.eve`) with `system_app` permissions baked into the ROM (`/system/priv-app/SinisterEVE/`).
- Hotword / voice surface uses an on-device whisper-cpp build (no cloud); transcription pipes to EVE service over a unix socket at `/dev/socket/sinister-eve`.
- Operator confirms destructive actions (factory reset / partition format / SIM swap) via fingerprint or in-Sinister-Panel PIN — NEVER auto-yes for those.
- Routine actions (open Panel / start Vault sync / heartbeat check / inbox poll) auto-yes per the master spawn doctrine.
- The Sinister fleet UI inherits from `projects/sinister-dashboard-skeleton/` per `CLAUDE.md` hard-canonical 2026-05-24 UI-base directive — Android components map skeleton tokens via a Jetpack Compose theme bridge.

## Branch hygiene

Standing branch namespace for this lane (no contention with Sanctum master or sinister-os PC lane):

- `agent/sinister-os-mobile/p0-spec-2026-05-24` — current
- `agent/sinister-os-mobile/p1-base-rom-select-<date>` — opens when P1 gated
- `agent/sinister-os-mobile/p2-build-env-<date>`
- `agent/sinister-os-mobile/p3-cuttlefish-vanilla-<date>`
- `agent/sinister-os-mobile/p4-eve-integration-<date>`
- `agent/sinister-os-mobile/p5-physical-flash-<date>`

## First-turn checklist for a fresh EVE on this lane

1. Read `README.md` (this folder) for orientation.
2. Read `plans/master-plan-2026-05-24.md` cover-to-cover.
3. Read `docs/architecture.md` for the layered system view.
4. Confirm current phase in `plans/master-plan-2026-05-24.md` § 12 (Phase status board).
5. Pick exactly one row from the current phase's queue. Mark `in_progress`. Do the work in cuttlefish. Commit on this lane's branch. Update PROGRESS.
6. Heartbeat + inbox poll per Sanctum Rule 9.

## Tool stack expected

- **Quantum tools** (operator directive 2026-05-24): use `seraphim` for triad-similarity audits on candidate base-ROMs (LineageOS vs GrapheneOS vs CalyxOS vs DivestOS) — quantum-kernel `K=4 ZZ-FM r=1` on the README/manifest corpus highlights structural overlap not visible in TF-IDF lexical comparison. Per `quantum-memory-kernel-fleet-action-items-2026-05-23`.
- **GitHub-first sourcing** (cold-start step 9): `automations/github-prior-art.ps1 -Topic "pixel 6a custom rom"` before building any subsystem from scratch.
- **Operator-idea-intake** (new 2026-05-24): operator drops candidate repos via `operator-idea-intake.ps1`; this lane reviews + marks adopted/rejected per directive 4.
- **understand-anything plugin** (cold-start step 0): invoke on `projects/sinister-os-mobile/` BEFORE substantive work.
- **bot fleet** (`_shared-memory/knowledge/bot-fleet-quick-reference.md`): use `triage.classify_file` for vendor-blob detection, `librarian.search` for ROM-manifest lookup, `auditor.scan_secrets` before any commit, `custodian.snapshot_now` before destructive script runs.

## Composes with

- `sinister-os-doctrine-2026-05-24` (PC sister project — shared EVE control patterns)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base + EXPAND principle)
- `agent-identity-eve` (persona)
- `agent-autonomy-push-and-completion-2026-05-23` (push agent/sinister-os-mobile/* freely)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate)
- `github-first-sourcing-doctrine-2026-05-24` (vendor before write)
