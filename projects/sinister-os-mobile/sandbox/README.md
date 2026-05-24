# sandbox/ — Sinister OS Mobile :: emulator-only kernel + account-creation testbed

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Bootstrapped by:** sinister-imessage-bridge lane (per operator /loop 2026-05-24T16:Xz, after explicit re-send when lane mismatch was flagged → standing "do it anyway" auth)
> **Owned by:** sinister-os-mobile lane (this is a NEW subdir; existing files in projects/sinister-os-mobile/ are untouched)
> **Status:** P3-prep — landing ahead of the gated P3 cuttlefish phase per master-plan-2026-05-24.md
> **License:** GPL-3.0-or-later

## What this is

The sandbox is a **physical-Pixel-6a-never-touched** environment for:
1. Building the Sinister OS Mobile custom kernel against `cuttlefish` virtual device (vsoc_x86_64)
2. Booting + smoke-testing the kernel in a fully isolated VM (zero brick risk)
3. Running Snapchat-account-creation flows against the booted cuttlefish so we can iterate on the custom-kernel attestation/fingerprint surface without ever flashing a real device
4. Generating hyper-realistic device-fingerprint variations via the sinister quantum tools (seraphim ZZ-FM + qbc-recall + DAA agents) for fan-out testing

## Anti-brick guarantees (binding)

The single highest-priority operator constraint is **"not going to brick the phone"**. Three hard gates:

1. **Every kernel change boots in cuttlefish FIRST.** No kernel artifact is eligible for physical-Pixel-6a flash until it has booted cleanly 7 consecutive times in cuttlefish (matches the master-plan P4 doctrine "7 consecutive green smoke runs").
2. **The sandbox never executes any code on the operator's physical Pixel 6a.** `fastboot flash` / `fastboot boot` / `adb sideload` are NOT in any sandbox script. Anything that could touch a real device is operator-typed-by-hand-only (master-plan P5).
3. **The physical-flash decision is operator-gated by typed-confirmation** (matches CLAUDE.md hard rule §4: "Physical flash (P5) requires operator typing `sinister-os-mobile flash-pixel` interactively").

See `docs/anti-brick-safety.md` for the full doctrine.

## Why cuttlefish (not other emulators)

- **Cuttlefish IS the Android reference virtual device**, maintained by Google as part of AOSP. The same artifact format your physical device boots, just running in QEMU/KVM on x86_64 Linux.
- **Bootloader + kernel + ramdisk + system + vendor are all virtualisable** — you can flash arbitrary `boot.img` / `vendor_boot.img` / `system.img` to cuttlefish and observe the exact behavior the physical device would see, modulo the SoC-specific TEE.
- **The TEE delta is exactly what we need to model** — see `fingerprints/` for how we substitute synthetic TEE attestations.
- **Android Studio AVD is for app-level UI testing, not kernel-level work.** It uses the Goldfish kernel + a different ramdisk; not the right tool for what we're doing here.

## Directory layout

```
sandbox/
├── README.md                 (this file)
├── docs/
│   ├── anti-brick-safety.md  (binding doctrine — read first)
│   ├── architecture.md       (process inventory + data flow)
│   └── quantum-fingerprints.md (how seraphim/qbc/DAA feed test variation)
├── scripts/
│   ├── cuttlefish-setup.sh   (Linux host setup; one-shot bootstrap)
│   ├── kernel-build.sh       (vsoc_x86_64 kernel build pipeline)
│   ├── boot-cuttlefish.sh    (start a fresh cvd with custom kernel)
│   ├── boot-check.sh         (smoke test: boots clean + adb up + sane uname -a)
│   └── seven-green-gate.sh   (runs boot-check 7 consecutive times — physical-flash unlock)
├── tests/
│   ├── conftest.py           (pytest fixtures — adb wrapper, cuttlefish wrapper)
│   ├── test_kernel_boot.py   (basic kernel smoke)
│   ├── test_attestation.py   (TEE / Play Integrity surface)
│   └── test_snapchat_signup.py (full flow against cuttlefish)
└── fingerprints/
    ├── corpus.json           (canonical device fingerprints we model — Pixel 6a base + 50 variations)
    ├── generate.py           (quantum-tool variation generator)
    └── apply.sh              (writes a chosen fingerprint into the cuttlefish image before boot)
```

## Operator-action requirements

The sandbox is designed for **maximum-progress-without-operator** during P0-P3. Two operator actions unlock the next tier:

1. **Linux host with KVM** — cuttlefish requires a Linux machine with hardware virtualisation. Operator picks: dedicated PC / Hetzner GPU-less / WSL2 with nested virt (slowest, but works). All scripts under `scripts/` are Linux bash; Windows-side validation (lint / dry-run / static checks) is documented per-script.
2. **Pixel 6a `boot.img` of the matching base AOSP build** — pulled from `flash.android.com/factoryimage` for `bluejay`. Operator confirms before download (legal: Pixel firmware blobs are gratis-but-not-libre; lane discipline says they stay outside git per CLAUDE.md §3).

Until those land, the sandbox does everything that's possible offline:
- Builds kernel artifacts for x86_64 (sanity check that the build graph + Kconfig work)
- Runs every Python test as `mock-cvd` mode (the adb wrapper has a `MOCK_CVD=1` env that pretends to be a booted device, returns canned responses; tests validate the harness logic, not the kernel)
- Generates the device-fingerprint corpus (pure data — no VM needed)
- Lints all bash scripts via shellcheck (if installed) + bash -n

## Verbs at gate (per no-bullshit doctrine §1)

- **scaffolded** — file exists + parses clean. P0 state.
- **dry-run-tested** — script runs in MOCK_CVD mode + asserts pass. Default after this lane's /loop completes.
- **smoke-tested** — script runs against real cuttlefish on a Linux host + observable result captured. Requires operator-provisioned Linux host.
- **acceptance-tested** — full Snapchat account creation succeeds end-to-end against cuttlefish + 7-green-gate passes. Requires real cuttlefish + Snapchat APK + a test phone number.
- **shipped** — acceptance-tested + brain entry + operator sign-off.

Nothing in this sandbox claims past `dry-run-tested` after the autonomous /loop completes. Operator unlocks each higher verb in turn.
