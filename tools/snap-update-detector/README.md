<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- Lane: kernel-apk (Snap auto-update pipeline) -->

# snap-update-detector

## Purpose

When Snap pushes a new Snapchat APK to the Play Store, the fleet's keybox /
hook / signing pipeline can drift instantly. This tool is Phase 0 of the
five-phase Snap auto-update pipeline: it polls multiple sources on a
schedule, detects when a newer version is in the wild, persists canonical
state to `_shared-memory/snap-version-state.json`, and fires a high-priority
`fleet-updates.jsonl` row so the kernel-apk lane can react (re-pull, re-hook,
re-sign, promote). Full design at
`_shared-memory/plans/snap-auto-update-on-snap-version-2026-05-24/design.md`.

## The 5 phases

| # | Phase                              | File / location                                                                  | Status (2026-05-24)  |
|---|------------------------------------|----------------------------------------------------------------------------------|----------------------|
| 0 | Detect new Snap version            | `tools/snap-update-detector/poll.ps1`                                            | SHIPPED              |
| 1 | Re-pull APK + diff vs canonical    | `tools/snap-update-detector/pull-and-diff.ps1` (TODO)                            | scaffold / spec      |
| 2 | Frida-probe new obfuscated symbols | `tools/snap-update-detector/probe-hooks.py` (TODO)                               | scaffold / spec      |
| 3 | Validate (register + login E2E)    | `tools/snap-update-detector/validate.ps1` (TODO)                                 | scaffold / spec      |
| 4 | Promote to canonical               | `tools/snap-update-detector/promote.ps1` (TODO)                                  | scaffold / spec      |
| 5 | Notify fleet + close loop          | wired via existing `automations/fleet-update.ps1` (composes with this tool)      | scaffold / spec      |

## How to run Phase 0

Test once, no writes:

```
powershell -File tools\snap-update-detector\poll.ps1 -DryRun
```

Test once with diagnostic logging:

```
powershell -File tools\snap-update-detector\poll.ps1 -Verbose
```

Override the canonical baseline for ad-hoc checks:

```
powershell -File tools\snap-update-detector\poll.ps1 -CurrentCanonicalVersion 13.88.1.0 -DryRun
```

Schedule (every 6 hours) via Task Scheduler:

```
powershell -File automations\register-snap-detector-task.ps1
```

Note: `automations\register-snap-detector-task.ps1` does NOT exist yet --
TODO for the next iteration. For now, register manually via
`schtasks /Create /TN SinisterSnapDetector /TR "powershell -File ..." /SC HOURLY /MO 6`.

## State files written

| Path                                                   | Purpose                                                                              |
|--------------------------------------------------------|--------------------------------------------------------------------------------------|
| `_shared-memory/snap-version-state.json`               | Canonical state (current + latest-observed + is-pending + poll history).             |
| `_shared-memory/fleet-updates.jsonl` (append)          | High-priority `snap-version-detected` row when pending flips false -> true.          |
| `tools/snap-update-detector/snap-version-state.schema.json` | JSON Schema (draft-07) for the state file above.                                |
| `tools/snap-update-detector/canonical-hooks.schema.json`    | JSON Schema (draft-07) for the Phase 2 hooks-extraction output.                 |

## Composes with

- `_shared-memory/knowledge/panel-localhost-routing-2026-05-19.md` -- how
  Sinister Panel reaches the kernel-apk lane; the fleet-update row this tool
  emits is consumed there.
- `_shared-memory/knowledge/fleet-update-channel-doctrine-2026-05-24.md` --
  the polled fleet-updates.jsonl bus that downstream agents read.
- `_shared-memory/knowledge/headless-spawn-pattern-2026-05-23.md` -- how the
  scheduled task spawns this script with `-NonInteractive` flags safely.
- `_shared-memory/knowledge/sinistercast-pc-leak-doctrine-2026-05-24.md` --
  warns that any version-bump that touches the live phone session must
  re-validate the cast/leak guards before promotion.
