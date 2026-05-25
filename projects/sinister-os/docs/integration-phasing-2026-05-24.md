# Integration phasing — Sinister OS x github-prior-art

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Status:** lane-canonical (sinister-os)
> **Composes with:** Sanctum `github-first-sourcing-doctrine-2026-05-24`, `rollout-doctrine-2026-05-24.md` (phases P0a/P0b/P0c gates), `no-function-loss-doctrine-2026-05-24.md` (cutover criteria), `research/feature-parity-audit-2026-05-24.md` (per-feature port status).

## Why phase the prior-art adoption

The github-prior-art sweep (massive-expansion iter 8 agent D output) surfaced 4 high-fit upstream projects:

| Project | Role in Sinister OS | License | Adoption tier |
|---|---|---|---|
| **Bazzite** | Steam Deck / gamer-focused Fedora atomic remix — desktop variant base | MIT | Phase-1 (vendor) |
| **Hyprland** | Wayland compositor — operator-facing shell | BSD-3-Clause | Phase-2 (vendor + config) |
| **archiso** | ISO build tooling — used for installer + live ISO | GPL-2.0 | Phase-1 (vendor + customize) |
| **kiosk-linux** | Minimal kiosk-shell pattern — informs the EVE-shell privileged service model | MIT | Phase-3 (pattern-only, no direct dep) |

Adopting all four at once = scope explosion (no-bullshit doctrine rule 8 quality-degradation signal). Phasing keeps quality monotonic.

## Phase boundaries (composes with `rollout-doctrine-2026-05-24.md`)

### Phase 0a — Docker test bench (current)

- **Goal:** prove the variant compose overlays (`compose.desktop.yml` / `compose.headless.yml`) parse + merge cleanly.
- **Prior-art adoption:** NONE yet. Compose overlays use existing operator stack only.
- **Gate to Phase 0b:** `validate-merge.sh` 0 FAIL across all overlays; smoke test of `eve mode set headless` + `eve mode set desktop` round-trip.

### Phase 0b — Laptop VM bench

- **Goal:** boot a Sinister OS ISO in QEMU/KVM on the laptop; install completes; `eve` CLI works.
- **Prior-art adoption:** archiso (vendor as a git submodule under `source/iso-build/upstream/archiso/`). Sinister-specific customizations live in `source/iso-build/sinister/` — never edit upstream files in-place. Customizations layer via archiso's `customize_airootfs.sh` mechanism.
- **Gate to Phase 0c:** ISO boots to login prompt in <90s on laptop VM; rollback path tested (btrfs snapshot pre-install + restore post-install) succeeds.

### Phase 0c — Main PC dual-boot (operator-gated)

- **Goal:** ISO installs to a dedicated partition on operator's main PC; dual-boot loader (rEFInd or systemd-boot) preserves Windows.
- **Prior-art adoption:** none new this phase; archiso + Sinister customizations from Phase 0b carry forward.
- **Operator-gated.** Phase opens only after operator clicks the gate row in OPERATOR-ACTION-QUEUE.

### Phase 1 — Headless variant ships first

- **Goal:** server variant (no GUI, panel + ssh + agent host) runs on the laptop for ≥3 days.
- **Prior-art adoption:** **kiosk-linux pattern** for the privileged service model. Sinister-control daemon (`sinister-eve.service`) borrows kiosk-linux's `User=eve` + `NoNewPrivileges=true` + `ReadWritePaths=/etc/sinister /var/lib/sinister` systemd unit shape. The unit lives at `source/sinister-control/systemd/sinister-eve.service`. NO direct dep on kiosk-linux source; we copy the pattern.
- **Gate to Phase 2:** 72-hour uptime; mesh-link to Sanctum holds; per-agent spawn from headless panel works.

### Phase 2 — Desktop variant ships

- **Goal:** Hyprland compositor + Sinister Panel kiosk + native apps (Steam, IDE, browser) on the laptop dual-boot.
- **Prior-art adoption:**
  - **Bazzite** — vendor as a base layer if going atomic (rpm-ostree); else cherry-pick the Steam/Proton-GE setup scripts. Decision deferred to Phase 1.5 review.
  - **Hyprland** — vendor as a binary dep (Arch package), config customized in `source/desktop/hyprland/sinister.conf` (Sinister purple accent, status bar showing mesh + Tailnet + DoH state).
- **Gate to Phase 3:** desktop variant boots + Hyprland renders the panel kiosk + Steam plays a test game.

### Phase 3 — Cross-variant feature unification

- **Goal:** desktop + headless share the same `sinister-control` daemon API + the same `eve` CLI. Hot-reconfig (no-reboot config changes) works on both.
- **Prior-art adoption:** none new — this phase is internal refactor.

### Phase 4 — Cutover dress rehearsal

- **Goal:** operator runs both variants in parallel for ≥7 days (laptop headless + main-PC desktop dual-boot). No-function-loss audit passes per `no-function-loss-doctrine-2026-05-24.md`.

### Phase 5 — Cutover (operator-clicked)

- **Goal:** main PC becomes Sinister OS primary. Windows partition retained for quarantined apps via VM passthrough.

## Adoption rules (per github-first-sourcing doctrine)

1. **Vendor as submodule under `source/<area>/upstream/<project>/`** — never copy-edit upstream files. All customizations layer on top.
2. **Pin to a specific upstream tag/commit** — record in `source/<area>/upstream-pins.md`. Bump deliberately, never silently.
3. **Track upstream-rebase debt** — when we modify upstream behavior via overlay/patch, note it in `source/<area>/sinister-divergence.md` so future bumps can re-validate.
4. **License surface per `docs/proprietary-blobs.md`** — every upstream project's license + commit-hash gets recorded.

## Anti-patterns

1. Adopting all 4 upstreams in one phase — guaranteed scope explosion.
2. Forking + editing upstream files directly — kills our ability to rebase on upstream improvements.
3. Vendoring without a pin — future builds become non-reproducible.
4. Skipping the Phase 0a / 0b / 0c progression — risks shipping a broken installer to the main PC.

## Validation gates (per phase)

| Phase | Smoke command | Pass condition |
|---|---|---|
| 0a | `bash source/docker-stack/validate-merge.sh` | exit 0, "0 FAIL" |
| 0b | `qemu-system-x86_64 ... -cdrom sinister.iso` | login prompt in <90s |
| 0c | (operator-gated dual-boot install) | both Windows + Sinister boot OK |
| 1 | `systemctl status sinister-eve` + 72h uptime | active (running), no restart events |
| 2 | `hyprctl monitors` + Steam game launch | Hyprland reports operator's display + Proton plays a known-good game |
| 3 | `eve config set --hot accent #dc2626` | accent propagates to running UI surfaces without reboot |
| 4 | parity audit | zero `missing` rows; zero unwaived `degraded` rows |
| 5 | (operator click) | main PC boots Sinister OS as primary |

## Update cadence

- Reviewed at every phase gate.
- Bumps to vendored upstreams (Bazzite / Hyprland / archiso version pins) trigger a row in this doc + the per-area `upstream-pins.md`.
