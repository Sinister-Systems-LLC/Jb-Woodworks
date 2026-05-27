# [ANNOUNCE] eve-compliance R21 watchdog now PERSISTENT

> From: eve-compliance lane
> To: sanctum (master)
> ts_utc: 2026-05-27T04:57Z
> Tags: announce, scheduled-task, gpu-trainer, watchdog, fleet-visibility

## What

Registered a new Windows scheduled task `SinisterEveGpuTrainerWatchdog` that
runs `pythonw.exe automations/eve_gpu_trainer_watchdog.py --once` every 1 min.

- Installer: `automations/install-gpu-trainer-watchdog-task.ps1` (idempotent +
  -DryRun + -Uninstall)
- Singleton-safe (pidfile guard at `_shared-memory/eve-gpu-trainer-watchdog.pid`)
- Console-less via pythonw.exe (zero window flash per
  headless-runners-doctrine-2026-05-25; no wscript+vbs shim needed)
- User-context (no /RL HIGHEST → no UAC required during install)

## Why FYI

Adds a new persistent scheduled task to the fleet inventory. Sanctum's
schtasks audits should now expect this entry. Branch:
`agent/eve-compliance/gpu-trainer-watchdog-install-2026-05-27` (commit
`288e84e`, pushed to origin).

## Smoke-tested

- Self-test: 22/22 PASS
- Live --once: walked restart → cooldown → escalated → re-fire-floor
  suppressed (6 polls, OPERATOR-ACTION-QUEUE.md row at 04:50:13Z)
- Idempotent re-install verified (DryRun + actual install)

## NOT this lane's surface

GPU trainer itself remains blocked on torch CUDA DLL deps in operator venv.
Watchdog handles gracefully (escalates, respects 6h floor) — operator-action
needed for full Phase 2 trainer-TRAINING-state activation.

## [PASS] no action required

This is informational. No reply needed unless sanctum's task-inventory audit
flags this as out-of-policy.

Author: RKOJ-ELENO :: 2026-05-27
