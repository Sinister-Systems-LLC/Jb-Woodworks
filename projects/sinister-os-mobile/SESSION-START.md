# SESSION-START — Sinister OS Mobile (Pixel 6a)

> Author: RKOJ-ELENO :: 2026-05-24

If your spawn landed in this directory, you are EVE on the **sinister-os-mobile** lane. Read in this order before doing anything else:

## Cold-start (project-scoped, runs AFTER Sanctum master cold-start in `D:\Sinister Sanctum\CLAUDE.md`)

1. **`understand-anything:understand-explain`** on this directory (`projects/sinister-os-mobile/`). MANDATORY per Sanctum CLAUDE.md cold-start step 0.
2. **This project's `CLAUDE.md`** — lane discipline + EVE-control design + branch namespace + tool stack.
3. **`README.md`** — one-pager orientation.
4. **`plans/master-plan-2026-05-24.md`** — the canonical 5-phase plan (P0-P5). Find current phase in § 12 Phase status board.
5. **`docs/architecture.md`** — layered system view (ROM base / kernel / HAL / system_server / Sinister overlay).
6. **`_shared-memory/PROGRESS/Sinister OS Mobile.md`** — what shipped, what's in-flight, what's queued for this lane.
7. **`_shared-memory/heartbeats/sinister-os-mobile.json`** — last heartbeat (write a fresh one this turn).
8. **`_shared-memory/inbox/sinister-os-mobile/`** — operator + cross-lane messages.

## Brain entries that govern this lane

- `sinister-os-mobile-doctrine-2026-05-24` (this project's canonical doctrine)
- `sinister-os-doctrine-2026-05-24` (sister PC project — shared design DNA)
- `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` (UI base + EXPAND)
- `quantum-memory-kernel-fleet-action-items-2026-05-23` (seraphim audit recipe)
- `github-first-sourcing-doctrine-2026-05-24` (vendor before write)

## First meaningful action

1. Surface yourself: heartbeat to `_shared-memory/heartbeats/sinister-os-mobile.json` + inbox poll.
2. Read § 12 Phase status board in `plans/master-plan-2026-05-24.md`. Confirm current phase = **P0 (spec lock)**.
3. Pick one row from P0 queue. Mark `in_progress`. Do the work.
4. Update `_shared-memory/PROGRESS/Sinister OS Mobile.md` with verified deliverables (no-bullshit verbs).
5. End-of-turn: commit on `agent/sinister-os-mobile/p0-spec-2026-05-24` (cut this branch first turn if it doesn't exist), push, schedule next iter if /loop is active.

## Hard rules (quick recap; full set in CLAUDE.md)

- Emulator-first (`cuttlefish` / AVD), NEVER physical Pixel 6a until P5.
- Phase boundaries operator-gated.
- No vendor binary leaks committed.
- No-bullshit verbs at gate (`scaffolded` / `parse-clean` / `smoke-tested` / `acceptance-tested` / `shipped`).
- UI work inherits from `projects/sinister-dashboard-skeleton/dashboard-skeleton/` per the 2026-05-24 UI-base hard-canonical.

## Composes with sibling lanes

- `sinister-os` (PC) — share EVE-control IPC patterns + voice surface design + Sinister Panel theme tokens.
- `sinister-kernel-apk` — Android root + KernelSU expertise; consult before any kernel-side EVE-control hook.
- `sinister-panel` — Sinister Panel mobile-companion view; layout & routes flow from here.
- `sinister-vault` — on-device vault client (Syncthing) for operator data continuity.

Operator: type `EVE-on-sinister-os-mobile` as the spawn label so the heartbeat picker labels this window correctly.
