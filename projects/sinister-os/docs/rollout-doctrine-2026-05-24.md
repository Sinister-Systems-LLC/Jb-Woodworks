# Three-Phase Rollout Doctrine — docker → laptop → main PC

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-os
> **Trigger:** Operator hard-canonical 2026-05-24 *"docker test, then laptop then main pc"*

## Purpose

Defines the three operator-gated phases for rolling Sinister OS from a docker test artifact onto bare metal. Composes with `plans/master-plan-2026-05-24.md § 12` (P0-P5 phase board) — this doctrine fills the P0a / P0b / P0c sub-divisions WITHIN P0 spec lock.

## Phase P0a — Docker test (active today)

**Scope:** All Sinister OS services + shell candidates run as docker containers on the operator's current Windows workstation.

**Acceptance criteria:**

1. `eve up` succeeds; `eve doctor` reports no blockers; `eve smoke` shows ≥ 7/10 services healthy.
2. `eve panel up` brings `sinister-panel-shell` up; operator visits `http://localhost:3082/` (currently working — HTTP 307 redirect to Next.js dashboard).
3. `eve mesh verify` + `eve doh verify` + `eve proxy verify` + `eve wg verify` + `eve panel verify` + `eve mode verify` all exit 0.
4. `bash validate-merge.sh ...` across all overlays returns 0 FAIL.
5. Operator can hot-edit panel source in `projects/sinister-panel/source/leo_dev/dashboard/` and see the change on `:3082` without restart (Next.js HMR).

**Operator-rollback signal:** any of the above breaks for > 1 hour without auto-recovery.

**Status:** ACTIVE / mostly-shipped this turn. Open: live `tailscale ping` (gated on operator Tailscale signup); panel-shell healthcheck refinement (Next.js 307 redirect classed as "unhealthy" by current check).

## Phase P0b — Laptop VM test (gated on P0a green)

**Scope:** Build the bootable Sinister OS ISO in QEMU on the operator's laptop. Run for 7 days against operator's daily-driver workflow inside the VM.

**Acceptance criteria:**

1. ISO boots in QEMU/KVM (`mkarchiso` + custom profile) without crash.
2. Hyprland starts; Sinister Panel renders at fullscreen kiosk on first login.
3. `eve` CLI works inside the VM (mesh / doh / proxy / wg / panel / mode all verify).
4. Operator runs daily workflow in the VM for 7 days; logs blockers in `docs/p0b-vm-test-log.md`.
5. NVIDIA driver (if VM is GPU-passthrough configured) survives 1 pacman -Syu without crash.
6. WireGuard fallback overlay works between VM and operator's NY/FL servers (real handshake).
7. Reboot-banner pipeline lights up when `/etc/sinister/eve.toml` cold-key is changed.

**Operator gates needed before P0b starts:**
- ISO build profile decision (single ISO + first-boot picker vs two ISO profiles).
- Package list freeze for headless variant.

**Operator-rollback signal:** more than 5 blocking issues remain unresolved after the 7-day soak.

## Phase P0c — Main PC dual-boot (gated on P0b green)

**Scope:** Install Sinister OS to a spare partition on the operator's main PC, dual-booting with the current Windows install. Operator switches GRUB default to Sinister OS only after voluntarily using it for 14 days.

**Acceptance criteria:**

1. Install completes via Calamares without bricking Windows partition.
2. All 5 "Top-5 risk gaps" from feature-parity audit are mitigated (PowerShell rewrite shipped; EVE picker bound to Hyprland Super+E; voice service running; nvidia-open-dkms stable; Vanguard decision made).
3. Operator can do 14 consecutive days of normal work without rebooting back into Windows.
4. Btrfs snapper rollback proven by INTENTIONAL break (operator-run drill).
5. Steam runs the operator's top-3 games without compat issues.

**Operator-rollback signal:** any blocker that forces > 1 hour back in Windows during the 14-day soak.

## Phase P0 → P1 → P5 (master-plan cross-link)

The master plan's P0-P5 phases still own the OS-level milestones (ISO build / installer / EVE shell / stacks / cutover). This doctrine refines P0 spec-lock into three increasingly-real test surfaces.

| Master-plan phase | This doctrine's sub-phase | Operator gate |
|---|---|---|
| P0 spec lock | P0a docker test | (in flight) |
| P0 → P1 ISO build | P0b laptop VM test | answer Q1-Q10 from master-plan § 14 |
| P1 → P2 installer | (P0c overlaps) | operator clicks "build installer" |
| P2 → P3 EVE shell | P0c main PC dual-boot | operator clicks "install to spare partition" |
| P3 → P4 stacks | (P0c continued) | operator clicks "enable Steam + creative stack" |
| P4 → P5 cutover | (P0c day 14+) | operator clicks "switch GRUB default" |

## Rollback strategy (each phase)

- **P0a:** `eve down` removes the stack; no host-level changes.
- **P0b:** delete the VM disk image; host laptop untouched.
- **P0c:** GRUB picks Windows by default for the first 14 days; operator can flip back instantly. Spare-partition install means no Windows partition shrink (unless operator opted in during P0b).

## Composes-with

- `plans/master-plan-2026-05-24.md` (P0-P5 phase board)
- `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` ITER 12
- `research/feature-parity-audit-2026-05-24.md` (Top-5 risk gaps)
- `docs/variants-design-2026-05-24.md` (desktop vs headless picked per machine)
