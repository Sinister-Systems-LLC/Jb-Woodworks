# Sinister OS — Desktop vs Headless Variant Design

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-os
> **Trigger:** Operator hard-canonical 2026-05-24 *"we need a ui based versioin of this with desktop etc for my main pcs. but we also need a server based system that is all just no ui based and all things you need to see are dontrolled from our sinister web panel."*
> **Research-agent source:** D (general-purpose; see `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` ITER 8).

## 1. Variant architecture decision

**Two separate ISO build profiles + a runtime toggle.**

- `iso-build/profiles/desktop/` — full Hyprland + Sinister Panel kiosk + native apps (Steam, IDEs, creative)
- `iso-build/profiles/headless/` — multi-user.target only, Sinister Panel served on mesh, no GUI
- `iso-build/profiles/_base/` — shared packagelist
- Runtime toggle: `eve mode get|set desktop|headless` writes `/etc/sinister/mode.toml` and swaps systemd default-target (operator-gated to P3+; today the toggle is a docker-stack profile selector).

**Justification:** Two profiles let the headless ISO stay genuinely lean (no Hyprland / Mesa / Pipewire pulled in at all → ~600 MB smaller, smaller attack surface). The runtime toggle still lets operator demote a desktop install to headless without reimaging.

## 2. compose.desktop.yml — shipped this turn

See `source/docker-stack/compose.desktop.yml`. Adds (to the existing panel-shell):
- `SINISTER_MODE=desktop` env
- `DISPLAY` / `WAYLAND_DISPLAY` / `XDG_RUNTIME_DIR` envs
- `/tmp/.X11-unix` socket mount
- `sinister-audio-bridge` + `sinister-controller-relay` placeholder services (profile-gated `desktop-extra`)

## 3. compose.headless.yml — shipped this turn

See `source/docker-stack/compose.headless.yml`. Strips desktop services + forces `0.0.0.0:3082` bind so the panel is mesh-reachable. systemd target hint label only (real target swap is P3+).

## 4. eve mode toggle CLI

Shipped as `eve mode get|set desktop|headless` patch to `source/docker-stack/eve` (subcommand only — manages `/etc/sinister/mode.toml` state file, does NOT touch systemd targets in docker context).

Future P3+ install of the CLI at `/usr/local/bin/eve-mode` will additionally:

```bash
case "$2" in
  desktop)
    printf 'mode = "desktop"\nset_at = "%s"\n' "$(date -Iseconds)" > /etc/sinister/mode.toml
    systemctl set-default graphical.target
    ln -sf /opt/sinister/docker-stack/compose.desktop.yml /opt/sinister/docker-stack/compose.active.yml
    systemctl enable --now sinister-stack.service
    ;;
  headless)
    printf 'mode = "headless"\nset_at = "%s"\n' "$(date -Iseconds)" > /etc/sinister/mode.toml
    systemctl set-default multi-user.target
    systemctl disable --now sddm.service hyprland.service 2>/dev/null || true
    ln -sf /opt/sinister/docker-stack/compose.headless.yml /opt/sinister/docker-stack/compose.active.yml
    systemctl enable --now sinister-stack.service
    ;;
esac
```

## 5. Honest scope ledger

**Today (P0 / this lane / VM-safe):**

- compose.desktop.yml + compose.headless.yml SCAFFOLDED (yaml parse PASS)
- this design doc SHIPPED
- `eve mode get|set` patch SHIPPED to docker-stack/eve (manages mode.toml only)
- validate-merge.sh re-run includes the two new overlays

**Gated to P1 (operator click):**

- Real archiso ISO builds against the two profiles
- QEMU boot tests of each ISO
- Package-list freeze for headless variant (audit Mesa / Hyprland / Pipewire absence)

**Gated to P3 (operator click):**

- Real `systemctl set-default` swap
- Real Hyprland enable/disable
- Real `eve mode` install to `/usr/local/bin/eve-mode`

**Gated to P5 (operator-click cutover):**

- Running `eve mode set` on the operator's main PCs

Per lane Rule 1 + Rule 2 (`projects/sinister-os/CLAUDE.md`), none of this touches bare metal without explicit operator gates.

## Composes-with

- `compose.hardened.yml` — security baseline (both variants compose with)
- `compose.panel-shell.yml` — panel-as-shell scaffold (target service for both variant overlays)
- `compose.mesh.yml` / `compose.doh.yml` / `compose.wg-fallback.yml` — geo-mesh layers (both variants inherit)
- `projects/sinister-os/plans/master-plan-2026-05-24.md` § 12 (phase board)
- `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` ITER 9
