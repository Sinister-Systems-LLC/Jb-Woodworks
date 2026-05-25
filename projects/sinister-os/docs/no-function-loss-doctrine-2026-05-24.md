# No-function-loss doctrine — Sinister OS

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** lane-canonical (sinister-os)
> **Composes with:** `research/feature-parity-audit-2026-05-24.md` (the table), `rollout-doctrine-2026-05-24.md` (per-phase gates), Sanctum `safe-quality-loops-doctrine-2026-05-24` (reversibility wall #2).

## Operator directive (verbatim 2026-05-24T~21:08Z)

> *"make sure i loose no function that i use on this pc"*

The operator's daily-driver Windows install drives a fleet of workflows. Cutover to Sinister OS is operator-gated (Phase 5 master-plan). Until then, every Sinister OS variant (desktop / headless / dual-boot) MUST preserve every operator function — or surface a status `degraded` row in the parity audit with a clear replacement plan + ETA.

## The rule (3 lines)

1. **Cutover gate is feature-parity, not feature-superset.** A variant ships when the per-row replacement status in `research/feature-parity-audit-2026-05-24.md` is `parity` (replacement matches Windows behavior) or `superset` (replacement improves on Windows). `degraded` rows MUST be resolved or operator-accepted with explicit waiver.
2. **No silent removal.** When a Windows-only application has no Linux equivalent (e.g. a niche AutoHotkey macro, a Win32-only driver utility), the row goes `quarantined` — keep accessible via a Windows VM running inside Sinister OS, NOT discarded. Operator chooses cutover only after every quarantined row has a launch path.
3. **Rollback always available.** Each phase ships with a one-keystroke rollback (btrfs snapper + `eve rollback`), per `rollout-doctrine-2026-05-24.md`. Operator can revert to the previous known-good state in <30s without a reboot if a feature regression is found post-cutover.

## Replacement-status taxonomy (used in the parity table)

| Status | Meaning | Cutover-blocking? |
|---|---|---|
| `superset` | Linux replacement does everything Windows did + more. | no |
| `parity` | Linux replacement matches Windows behavior 1:1 in the operator's workflow. | no |
| `degraded` | Linux replacement works but loses a feature (e.g., color profiles, HDR, specific game). | yes — surface to operator queue with mitigation plan |
| `quarantined` | No Linux native; runs in Windows-VM (KVM/QEMU GPU passthrough) inside Sinister OS. | no — VM-launch is a valid replacement |
| `missing` | No replacement identified yet; research needed. | yes — blocks the row from cutover |
| `waived` | Operator explicitly chose to drop this feature. | no |

## Per-category audit (high-level — full table in `research/feature-parity-audit-2026-05-24.md`)

### Daily-driver workflows

- **Browser + GitHub + Claude Code** → Firefox / Chromium native, GitHub CLI, Claude Code via npm/cargo → **parity**.
- **PowerShell automations (1000+ lines under `automations/`)** → port to bash/python on Linux variant OR run via PowerShell Core (`pwsh`) which exists natively on Linux → **parity** (per-script port required).
- **EVE.exe + Claude Code spawn pipeline** → desktop variant ships Hyprland + the picker; headless variant exposes spawn over web-panel + ssh → **parity** (desktop) / **superset** (headless adds remote-spawn).

### Creative + game

- **Steam (Proton)** → desktop variant ships Steam via Flatpak with Proton-GE → **parity** for ~95% of operator's library (per ProtonDB).
- **OBS / streaming tools** → native Linux package → **parity**.
- **Audio production (FL Studio, etc)** → degraded — run via Wine or quarantined Windows-VM. Surfaced to operator queue.

### Drivers + peripherals

- **NVIDIA GPU** → proprietary driver supported; surface in `docs/proprietary-blobs.md` per lane rule 4 → **parity** with Windows for game + compute use.
- **Yurikey50/51/52 hardware keys** → libusb access works identical on Linux → **parity**.
- **Phone bridge (Pixel 6a P1/P2 via scrcpy)** → scrcpy is Linux-native → **superset** (better latency on Linux per scrcpy upstream notes).

### Banking + accounting

- **OS-level password manager (Windows Hello / TPM)** → Linux TPM2 + fido2 → **parity** with Yurikey hardware step.
- **Tax software / quickbooks** → quarantined Windows-VM if no native equivalent identified → **quarantined**.

## Pass criterion for cutover (Phase 5)

Operator clicks cutover ONLY when:

1. Parity audit shows **zero `missing` rows** (every feature has at least a quarantine path).
2. Operator has tested the desktop variant in dual-boot for ≥7 days without a `degraded → operator-blocker` row firing.
3. Rollback path verified end-to-end: btrfs snapshot rolls back a deliberate regression in <30s.
4. The headless variant has been operating the server-side workload (panel + agents) on the laptop for ≥3 days with zero unscheduled downtime.

## Anti-patterns

1. Removing a Windows-only workflow and calling it "ported" without surfacing the regression in the parity table.
2. Claiming `parity` when the Linux replacement requires the operator to learn a new UI for a daily-driver task (that's `degraded — UX friction`).
3. Quarantining without verifying the Windows-VM launch path works (must boot + run the app + close cleanly).
4. Hiding `degraded` rows in commit messages — they MUST land in the parity table for operator visibility.

## Update cadence

- Parity table reviewed at every phase gate (P1 → P2 → P3 → P4 → P5).
- New `missing` or `degraded` rows trigger an inbox row to the operator action queue.
- This doctrine reviewed when the parity table churns by ≥5 rows or quarterly, whichever comes first.
