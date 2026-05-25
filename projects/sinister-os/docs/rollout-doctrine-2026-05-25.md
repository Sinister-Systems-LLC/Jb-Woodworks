# Sinister OS — three-phase rollout doctrine

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: sinister-os
> Composes-with: `plans/master-plan-2026-05-24.md` §12 (Phase board), massive-expansion plan iter 12

## Operator directive (verbatim, 2026-05-24T21:08Z)

> *"test docker → laptop → main pc"*

Three phases. Each phase is operator-gated; **no auto-promotion**. Each phase has acceptance criteria (must hit ALL to advance) and rollback criteria (any ONE forces rollback). Composes with CLAUDE.md "VM-only testing" + "Phase boundaries are operator-gated" hard rules.

## P0a — Docker test (LOCAL, low risk)

**Purpose.** Prove the variant stacks (`compose.desktop.yml`, `compose.headless.yml`, `compose.mesh.yml`, `compose.doh.yml`, `compose.hardened.yml`, `compose.wg-fallback.yml`, `compose.panel-shell.yml`) start clean and run their healthchecks for 30 min sustained on the operator's main Windows box (Docker Desktop / Podman).

**Where.** Operator's main PC, in Docker; never touches the host OS init system.

**Acceptance (ALL).**
- `validate-merge.sh` 0 FAIL across all 8 overlays.
- `docker compose -f docker-compose.yml -f compose.<variant>.yml up -d` exit 0 for desktop + headless + mesh.
- Every service healthcheck PASS for ≥30 min continuous (vault-api, yjs-server, panel-shell, mesh, doh).
- `eve mode get` returns the variant set; `eve mode set` round-trips.
- reboot-banner pipeline: writing `/var/lib/sinister/reboot-required.json` causes vault KV `mesh/banner/reboot-required` to populate within 2s (P0a smoke; manual curl).
- Container egress respects per-variant policy (headless: no UI services exposed; desktop: panel-shell on :3000).

**Rollback (ANY).**
- Any overlay parse-fail or healthcheck flap >3× in 30 min.
- Memory or CPU thrash >150% of declared deploy.resources limits.
- Operator interrupt.

**Gate to P0b.** Operator click in EVE.exe picker: *"P0a docker → green; promote sinister-os to P0b laptop VM."*

## P0b — Laptop VM test (ISOLATED HARDWARE)

**Purpose.** Prove the ISO installer + Hyprland shell + EVE-as-shell wiring boot on real hardware, in a disposable VM-OR-spare-laptop scope.

**Where.** Operator's laptop, dual-boot OR full VM (QEMU/KVM/VirtualBox per CLAUDE.md). Never overwrites operator's daily-driver partition.

**Acceptance (ALL).**
- `iso/build.sh` produces a bootable ISO; SHA recorded in `_shared-memory/PROGRESS/Sinister OS.md`.
- Installer brings the VM to Hyprland login in ≤4 min cold-boot.
- EVE-as-shell privileged daemon (`sinister-eve.service`) starts on boot; UNIX socket `/run/sinister/eve.sock` is listening.
- `sudoers` allowlist (eve user, NOPASSWD curated) works for `apt`, `systemctl`, `nmcli`, `xdotool`.
- Hot-reconfig classifier returns `hot` for accent-token change; panel CSS updates within 5s (no reboot).
- Reboot-banner shows correctly when classifier returns `reboot` (manual `reboot-required.sh` trigger).
- Network: tailnet up, doh resolving, panel reachable from operator's main PC via mesh.

**Rollback (ANY).**
- Boot loop OR systemd target failure on 2 consecutive boots.
- EVE socket not listening within 60s of login.
- sudoers misconfig that bricks operator's recovery path.
- Proprietary-blob surprise (driver pulled in without surfacing in `docs/proprietary-blobs.md` per CLAUDE.md hard rule 4).

**Gate to P0c.** Operator click: *"P0b laptop → green; promote sinister-os to P0c main-PC dual-boot test."* PLUS operator-physical action: laptop survives 24h continuous use as the operator's actual workflow.

## P0c — Main-PC dual-boot test (PRODUCTION-EQUIVALENT, HIGHEST RISK)

**Purpose.** Prove sinister-os runs the operator's actual daily workflow without functional loss (per directive *"i loose no function that i use on this pc"*).

**Where.** Operator's main PC. **Dual-boot only**, never wiping the Windows install. btrfs snapper enabled BEFORE first sinister-os boot so `eve rollback` is one keystroke.

**Acceptance (ALL).**
- `feature-parity-audit-2026-05-25.md` table shows 100% of operator-flagged Windows features covered (or explicit "deferred + reason" with operator OK).
- Operator can run their daily-driver workflow for 7 continuous days without rebooting to Windows.
- Hot-reconfig works for ≥3 operator-driven changes (accent, panel layout, service add/remove).
- Reboot banner correctly fires + clears for ≥1 real kernel upgrade.
- All cross-machine session resume works (operator closes Hyprland on laptop, opens on main PC).
- `eve rollback` tested + verified rolls system back to last-known-good in <30s without reboot.

**Rollback (ANY).**
- Any functional loss the operator flags as critical (audio, controller, specific app).
- Boot regression that requires recovery USB.
- Mesh disconnect >5 min cumulative per 24h.
- Operator says "switch back" — switch back, no questions.

**Gate to P5 cutover.** Out-of-scope this doctrine; see master-plan §12 Phase 5.

## Cross-cutting rules (all phases)

1. **VM-only-or-isolated** — CLAUDE.md hard rule 1.
2. **Operator-gated** — no auto-promotion between phases. The picker prompts at each gate.
3. **Surfaced surprises** — any proprietary blob, any allowlist expansion, any unexpected dependency surface gets a row in `docs/proprietary-blobs.md` BEFORE the phase claims green.
4. **Rollback drills** — each phase tests `eve rollback` at least once before claiming green.
5. **No half-ass** — composes with operator 2026-05-24 *"we dont do shit half ass"*. Partial coverage (e.g. desktop overlay PASS but headless overlay FAIL) does NOT advance the phase.
6. **Receipts in PROGRESS** — every phase claim carries the smoke-test command + exit code in `_shared-memory/PROGRESS/Sinister OS.md` per no-bullshit doctrine.

## Open questions surfaced for operator (next sync)

- **GPU driver path on main PC.** NVIDIA proprietary vs nouveau — operator preference?
- **Daily-driver app list.** What's the canonical "must not lose" list? (Steam, Adobe, specific browsers, MS Office, VR drivers, etc.) → drives `feature-parity-audit-2026-05-25.md` priority order.
- **Btrfs vs ZFS on root.** Snapper assumes btrfs; if operator prefers ZFS, `eve rollback` rewires to `zfs rollback`.

## What this doctrine does NOT cover

- Phase P1-P5 of `master-plan-2026-05-24.md` — that's the high-level project arc; this doctrine is the **promotion gate** between phase 0 sub-stages.
- Per-app installation recipes — those live in `plans/p4-stacks-*` when P4 opens.
- Cutover / Windows-removal — P5 only; explicitly out-of-scope until operator gates it.
