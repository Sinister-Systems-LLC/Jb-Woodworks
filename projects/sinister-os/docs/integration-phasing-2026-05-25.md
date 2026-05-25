# Integration phasing — github-prior-art consumption plan

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: sinister-os
> Composes with: `docs/rollout-doctrine-2026-05-25.md`, github-first-sourcing-doctrine-2026-05-24, massive-expansion plan iter 14.

## Operator directive (verbatim — fleet-wide hard-canonical 2026-05-24)

> *"everytimg we start a porject or look for complex feature i want us to always aerach giuthub for pre madecode that we can use and then build ours based off of per project to save time. i want everything to be as speeedy efficent and concise as possible"*

Sinister OS is exactly the kind of complex multi-surface project where rolling everything from scratch is six-month yak-shave with zero ROI. The github-prior-art sweep surfaced four high-leverage upstreams; this doc is the phase-by-phase plan to consume them.

## Upstream registry

| # | Upstream | Role | License | First-use phase |
|---|---|---|---|---|
| 1 | [archiso](https://gitlab.archlinux.org/archlinux/archiso) | ISO build pipeline (mkarchiso + airootfs overlay) | GPLv2+ | P0b |
| 2 | [Hyprland](https://github.com/hyprwm/Hyprland) | Wayland compositor + ipc | BSD-3 | P0b |
| 3 | [Bazzite](https://github.com/ublue-os/bazzite) | Reference for atomic-OS-with-gamescope / image-based desktop | Apache-2 | P0c (reference only; no fork) |
| 4 | [kiosk-linux examples](https://github.com/topics/kiosk-linux) | Reference patterns for compositor-as-shell, auto-login, single-app modes | varied | P0a + P3 |

## Consumption rules (DO and DON'T)

- **DO** import via vendoring with a `UPSTREAM.md` note recording: upstream SHA, license, why we picked it, what we changed.
- **DO** keep upstream config files in `source/integrations/<name>/upstream-<sha>/` and our overlays in `source/integrations/<name>/sinister-overlay/`.
- **DO** open a `_shared-memory/external-imports/CANDIDATES.md` row before vendoring (per Sanctum doctrine).
- **DON'T** silent-fork. Forks live in `source/integrations/<name>/` with a clear UPSTREAM.md; never sneak diffs into upstream code without doc.
- **DON'T** consume more than one upstream per iter — too many merges-in-flight breaks `validate-merge.sh`.

## Phase plan

### P0a (docker) — kiosk-linux pattern study only

- **Scope.** No vendoring in P0a; docker doesn't host a compositor.
- **Action.** Read kiosk-linux topic landing examples; extract patterns into `docs/kiosk-linux-patterns-2026-05-25.md` (a digest, not vendor).
- **Acceptance.** Digest doc exists; ≥3 patterns captured (auto-login, single-app focus lock, compositor-managed reboot UX).

### P0b (laptop VM) — archiso + Hyprland vendor

- **Scope.** Vendor archiso + Hyprland. Build the actual ISO.
- **Action.**
  1. `git submodule add` upstream archiso pinned to a release tag → `source/integrations/archiso/upstream-<sha>/`.
  2. Sinister overlay: `source/integrations/archiso/sinister-overlay/airootfs/etc/sinister/*` + custom `profiledef.sh`.
  3. `git submodule add` Hyprland (or build from package) → `source/integrations/hyprland/upstream-<sha>/`.
  4. Sinister overlay: `source/integrations/hyprland/sinister-overlay/hyprland.conf` with operator binds + sinister-control hooks.
  5. Build pipeline: `iso/build.sh` invokes `mkarchiso -v -w work -o out source/integrations/archiso/sinister-overlay/`.
- **Acceptance.**
  - ISO size <2 GB.
  - ISO boots in QEMU within 60s to Hyprland.
  - Hyprland binds (Mod+Return = kitty, Mod+B = sinister-panel, Mod+E = eve-repl) all work.
  - UPSTREAM.md files exist for both with SHA + license + change list.
- **Anti-pattern guard.** No upstream code copied without UPSTREAM.md row. No silent overlay drift.

### P0c (main PC dual-boot) — Bazzite reference comparison

- **Scope.** Don't fork Bazzite; use its design as the reference for any atomic-OS direction we add.
- **Action.**
  1. Read Bazzite's `Containerfile` + `system_files/` structure.
  2. Write `docs/bazzite-comparison-2026-05-25.md` mapping each Bazzite pattern to either: (a) we adopt the same approach, (b) we diverge — reason, (c) we don't need this slice.
  3. Decide explicitly: do we want image-based atomic updates (`rpm-ostree` style) for sinister-os, or stick with traditional package management + btrfs snapper? Document.
- **Acceptance.**
  - Comparison doc exists; every Bazzite high-level decision has our explicit stance.
  - Operator gate: choice between atomic-OS vs traditional+snapper documented; operator signs off OR overrides.

### P3 (eve-shell) — kiosk-linux patterns applied

- **Scope.** Apply the digest from P0a + Hyprland-as-shell to the actual EVE-as-shell binding.
- **Action.**
  1. `sinister-eve.service` privileged daemon (per CLAUDE.md EVE-as-OS-shell design constraints).
  2. Hyprland exec-once → `eve-ui` (the operator's first-class shell, not just a backdrop).
  3. Wake-word + voice surface → `sinister-voice` user service.
  4. Hotkey binds: voice trigger, eve-confirm, eve-deny, eve-undo.
- **Acceptance.**
  - From cold boot, operator sees a useful EVE shell in <10s.
  - Wake-word path → transcription → EVE socket → action proposal → confirm hotkey works in a single round trip <2s.

## Tracking + governance

- Every new vendor PR uses a commit prefix: `sinister-os: vendor <upstream> @ <sha>`.
- Every UPSTREAM.md row gets cross-referenced from `_shared-memory/external-imports/CANDIDATES.md`.
- License surface gets a row in `docs/proprietary-blobs.md` if it's anything other than permissive OSS.

## Risk register

1. **Submodule rot.** Upstream tags evolve; we lag. Mitigation: quarterly review row in `forever-improve` queue.
2. **Overlay drift.** Operator hand-edits a file in the overlay tree that should have been a config knob. Mitigation: pre-commit hook checks overlay tree for hand-edits to upstream-rooted files.
3. **License contamination.** Mixed GPLv2/Apache/BSD. Mitigation: `docs/license-matrix-2026-05-25.md` (next iter); for now, all four upstreams are compatible-with-redistribution.
4. **"Just use Bazzite" temptation.** Adopting an upstream wholesale is fast but cedes architectural control. Mitigation: this phasing explicitly says **reference only**, no fork.
