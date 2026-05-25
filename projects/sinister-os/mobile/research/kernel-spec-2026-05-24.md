# Kernel Spec — Sinister OS Mobile (Pixel 6a / bluejay / Tensor G1)

> Author: RKOJ-ELENO :: 2026-05-24
> Status: **research / scaffolded** (no kernel code built, no cuttlefish booted, no Pixel touched — see § 9 honest status)
> Composes with: `sinister-os-mobile-doctrine-2026-05-24`, `branding-spec-2026-05-24`, `patterns-md-mobile-gap-audit-2026-05-24` (sibling lane research docs)

## § 1 Honest status (verbs at gate)

| Question | Answer |
|---|---|
| Has any kernel code been written? | **No.** Master-plan P3 (`cuttlefish vanilla`) and P4 (`EVE integration`) haven't started. |
| Has cuttlefish been built or booted? | **No.** Requires P2 build env (`repo sync` + `m otatools` green) — not started, gated on P1 ROM-select, gated on P0 operator Q1-Q10. |
| Has a Pixel 6a been touched? | **No.** Hard rule of this lane: NEVER physical Pixel 6a until P5 operator-hands-on gate. |
| What CAN be done right now (P0)? | Research-tier work: source the canonical kernel trees, map the Tensor G1 hardware blocks, scope EVE-control kernel hooks, identify cuttlefish vs Pixel divergence, build a prior-art shortlist. **This doc is that work.** |
| Verb at gate for this doc? | **scaffolded** (file exists, parse-clean, citations are public-knowledge upstream URLs). NOT acceptance-tested — no source pulled, no symbols verified by reading actual kernel sources. |

## § 2 Canonical kernel tree for Pixel 6a

| Component | Upstream URL | Version pin (master-plan § 3) | License |
|---|---|---|---|
| Pixel 6a device kernel | `android.googlesource.com/kernel/private/devices/google/bluejay` | Linux 5.10 LTS branch `android13-gs-pixel-5.10` (Tensor G1 base) | GPL-2.0 |
| Tensor G1 private modules | `android.googlesource.com/kernel/google-modules/` (many subprojects) | `android13-gs-pixel-5.10` | GPL-2.0 / vendor-proprietary mix |
| Common Android Kernel (ACK) | `android.googlesource.com/kernel/common` | Linux 5.10 LTS | GPL-2.0 |
| Kleaf build system | `android.googlesource.com/kernel/kleaf` | latest | Apache-2.0 |
| Vendor blobs (firmware) | Operator's existing Pixel 6a backup (NEVER committed; per CLAUDE.md hard rule 3) | factory image vN | Google proprietary |

**P2 fetch command** (will run when P2 unlocks):
```
repo init -u https://android.googlesource.com/kernel/manifest -b android13-gs-pixel-5.10
repo sync -c -j8 --no-tags --no-clone-bundle
# ~6-8 GB after sync, kernel-only (much smaller than full AOSP's ~120 GB)
```

## § 3 Tensor G1 hardware blocks (what makes bluejay special)

The Tensor G1 SoC (Pixel 6a / Pixel 6 / Pixel 6 Pro share the silicon) has Google-custom IP blocks not in mainline Linux. These are the kernel-level points where Pixel divergence matters:

| Block | Driver location | EVE-control implication |
|---|---|---|
| **TPU** (Edge TPU for on-device ML) | `private/google-modules/edgetpu/` | Whisper-cpp voice surface (master-plan § 7.1) can offload to TPU instead of running on AP cores. Big battery win. |
| **GXP** (Google Crash Processor) | `private/google-modules/gxp/` | Vendor crash-dump pipe; we leave it alone. |
| **AOC** (Always-on Compute) | `private/google-modules/aoc/` | Hotword detection runs HERE — not on AP. EVE voice hotword integrates here; pre-AP wake = low battery. |
| **Mali GPU** (ARM) | `private/google-modules/gpu/mali_kbase/` | Standard Mali driver; userspace consumers unchanged. |
| **Modem** (Exynos 5123) | `private/google-modules/radio/` + closed firmware | OUT-OF-SCOPE per master-plan § 2 (carrier provisioning); leave blob as-is. |
| **Display** (Samsung S6E3FC3) | `private/google-modules/display/` | Bootanimation + Liquid Glass blur perf — verify GPU-composited blur works on this panel. |
| **Power HAL** (custom) | `private/google-modules/power/` | EVE always-on voice surface needs careful battery-profile entries here. |
| **Trusty TEE** (Google's secure world) | `private/google-modules/trusty/` | AVB key custody lives here. If operator picks locked-bootloader (Q3), we use this for custom AVB key (GrapheneOS pattern). |
| **CCIC USB-PD** | `private/google-modules/usb/` | OTG / charging behavior; EVE mesh sub-agent off-loading to laptop via USB needs this stable. |

**Implication for the build:** we are NOT writing a new kernel. We are taking Google's bluejay 5.10 LTS tree, applying minimal patches (mostly sepolicy + selinux + a few permissive hooks for EVE-as-system-service), and building it. The vendor blob (`firmware-bluejay-XYZ.zip`) is pulled at flash time from the operator's existing Pixel backup per CLAUDE.md hard rule 3.

## § 4 EVE-control kernel-side hooks needed

EVE runs as a privileged system service (master-plan § 7.1), but some capabilities require kernel cooperation:

| Capability | Where it lives | Kernel patch needed |
|---|---|---|
| Reading `/proc/<pid>/stat` for any process (battery monitor) | sepolicy `system_app` context | YES — relax `read` on `proc_pid_stat` for `system_app` (currently allowed for `system_server` only) |
| Recording mic without focus-stealing (voice surface) | userspace + audio HAL | NO kernel change — userspace `AudioRecord` with `RECORD_AUDIO` is sufficient |
| Reading sensor stream for context detection (motion/light) | sepolicy `system_app` | YES — `sensorservice` access already granted to `system_app` but specific sensor types (proximity, magnetic) need explicit allow |
| Writing `/data/data/com.sinister.eve/` outside normal app sandbox (custom persistence) | mount namespace + sepolicy | NO — the system_app context handles this |
| Triggering system reboot programmatically (factory-reset confirmation flow) | sepolicy + `binder` to `power_service` | YES — bind `power_service` access (default for system_app on most ROMs; verify on bluejay) |
| Spawning a child agent process under its own UID (for sandboxed sub-EVEs) | `setuid` capability | YES — add `CAP_SETUID` to EVE's capability bounding set (this is a HARDENING TRADE-OFF; operator Q9 banking app compat decision affects this) |
| Reading other apps' memory for the cross-agent inbox (debugging) | `PTRACE_SCOPE` | NO patch in v1 — too invasive; defer to P5+ if operator wants it |

**Verdict:** the kernel patch set is small (estimated < 200 LOC across sepolicy `.te` files + 1-2 `init.bluejay.rc` deltas). NO C-level kernel patches in v1. This keeps the surface auditable + close to upstream + survivable through Google's monthly security patches.

## § 5 Cuttlefish kernel divergence (P3 testability limit)

**Critical insight that affects the test pipeline:** the master-plan's P3 cuttlefish stage tests against `aosp_cf_x86_64_phone-userdebug` — that's a virtual device with an **x86_64 KVM-friendly kernel**, NOT bluejay.

What cuttlefish CAN validate:
- Userspace (Sinister EVE service, Panel APK, Vault, theme bridge, Compose UI inheritance)
- Framework (SystemUI patches, sepolicy compiles, AIDL service registration)
- IPC (`/dev/socket/sinister-eve` unix socket, binder bindings)
- Boot flow (BOOT_COMPLETED receiver, sticky notification)
- Sinister Panel mobile chrome (the EXPAND-PR-consumed primitives from `patterns-md-mobile-gap-audit-2026-05-24`)

What cuttlefish CANNOT validate:
- TPU / AOC offload (hotword on Tensor — no chip in cvd)
- Mali GPU shaders (cvd uses SwANG / SwiftShader — Liquid Glass blur fps unverified)
- Modem behavior (cvd has none; emulated via test harness)
- Real sensor streams (mock sensors only)
- Power HAL battery curves
- Display panel timing (Liquid Glass blur perf on the actual S6E3FC3 — see master-plan § 11 risk row "cvd-to-metal surprises")
- AVB / dm-verity behavior (cvd boots unsigned)

**Mitigation strategy** (master-plan § 11 row): run cvd + a Pixel-3a-rooted-as-proxy in P3-P4. The 3a has a similar (but older) display + Mali generation; it's a "real chip, not the target chip" sanity check. Operator owns whether a 3a is available.

**Bottom line on testing:** ~70% of EVE-integration work validates on cvd. The remaining 30% (TPU / AOC / panel / battery / AVB) only validates on metal Pixel 6a — which is P5 and operator-gated.

## § 6 Patch budget + maintenance burden

Estimated kernel-side changes for v1 of Sinister OS Mobile, all on top of GrapheneOS or LineageOS bluejay kernel (operator Q1-Q3 picks base):

| Patch class | Estimated LOC | Per-month security patch survival cost |
|---|---|---|
| sepolicy `.te` allows (EVE system_app capability set) | ~80 LOC across 4-5 files | Low — sepolicy rarely conflicts with upstream |
| `init.bluejay.rc` deltas (EVE service spawn order, socket creation) | ~30 LOC | Low — init.rc is stable |
| `BoardConfig.mk` / Kconfig (CONFIG_KERNELSU or CONFIG_SECURITY_SELINUX_PERMISSIVE_BY_DEFAULT toggles, gated by Q3) | ~20 LOC | Low |
| `vendor.img` overlay (preinstall `/system/priv-app/SinisterEVE/SinisterEVE.apk`) | n/a — pure file inclusion | Zero |
| `framework-res` color overlay (Sinister purple tokens) | ~50 LOC XML | Low — themes survive minor releases |
| **TOTAL v1** | **~180 LOC + assets** | **~1-2 hours per Google monthly security patch** if base ROM is GrapheneOS (they rebase fast); LineageOS path adds ~1-2 weeks lag |

This is much smaller than what KernelSU upstream maintains (~95k LOC patch set across multiple kernel versions). Our advantage: we don't need full root capability — `system_app` + minimal sepolicy gets us 90% of EVE's needs.

## § 7 Root strategy decision (intersects with operator Q2/Q3/Q9)

Three paths, picked based on operator's banking-app-compat priority (master-plan § 10 Q9):

### § 7.1 Path A — `system_app` + minimal sepolicy (NO root, locked AVB)

- **Pros:** banking apps work · GrapheneOS-grade security · locked bootloader · custom AVB key · re-flashable but locked when sealed · operator can lose+factory-reset and EVE survives
- **Cons:** EVE cannot ptrace other apps · cannot modify other apps' data · cannot replace running system services post-boot · CAP_SETUID limited
- **Recommended default** unless operator Q9 = "banking doesn't matter"

### § 7.2 Path B — KernelSU (root via kernel) + unlocked AVB

- **Pros:** EVE has full root · can install Magisk modules · can mount /system as RW · operator can `su` from termux
- **Cons:** banking + Play Integrity fail · AVB unlocked → no hardware-backed verified boot · ~95k LOC patch set must be maintained against monthly Google security patches · biometric + key attestation degraded
- Picks if operator Q9 = "banking doesn't matter" AND Q3 = "permanent unlock"

### § 7.3 Path C — Magisk on LineageOS (root via ramdisk) + unlocked AVB

- **Pros:** familiar to operator's other lanes · large ecosystem · DenyList can hide root from some apps
- **Cons:** Magisk + AVB don't compose cleanly (so AVB unlocked) · DenyList is cat-and-mouse · LineageOS lags 1-2 weeks on monthly security patches
- Picks if operator Q1 = "carrier needs Magisk DenyList tricks" or operator Q2 = "full GApps"

**My recommendation for default lean** (subject to operator Q9 override): **Path A**. Banking + GrapheneOS-grade security baseline + locked AVB + EVE as `system_app` covers ~90% of master-plan § 7 EVE-control needs. The 10% gap (ptrace, app-data-modification) is luxury, not core.

## § 8 Prior-art shortlist

GitHub prior-art via `automations/github-prior-art.ps1 -Topic "..."` returned **zero candidates** — the script's permissive-license filter (MIT/Apache/BSD) excludes Linux kernel forks (all GPL-2.0). Documented as a non-find per the no-bullshit doctrine.

Canonical sources (general knowledge, **not verified by clone**):

| Project | URL | Why relevant | Notes |
|---|---|---|---|
| Google's bluejay kernel (upstream) | `android.googlesource.com/kernel/private/devices/google/bluejay` | The source-of-truth tree we fork from | NOT GitHub; canonical |
| Google's google-modules | `android.googlesource.com/kernel/google-modules/` | Tensor G1 private drivers (TPU/AOC/etc.) | NOT GitHub; canonical |
| GrapheneOS kernel mirror | `github.com/GrapheneOS/kernel_gs-bluejay` (or similar; needs verification) | If Q1-Q3 → Path A, this is our base | GPL-2.0; verify exact repo name when P1 fires |
| LineageOS Tensor kernel | `github.com/LineageOS/android_kernel_google_gs101` | If Q1-Q3 → Path C | GPL-2.0; verify gs101 vs bluejay subprojects |
| CalyxOS bluejay kernel | (search to verify) | Alternative Path A | GPL-2.0; smaller community |
| KernelSU (active fork) | `github.com/KernelSU-Next/KernelSU-Next` | If Q9 → Path B | GPL-2.0; ~95k LOC; bluejay support confirmed in their device matrix (verify on P1) |
| KernelSU original | `github.com/tiann/KernelSU` | Reference | GPL-2.0 |

**P1 verification action** (gates seraphim audit): when P0 → P1 fires, fetch each candidate's README + kernel-Kconfig diff against upstream, run `seraphim audit --variant zzfm-r1 --triad <a> <b> <c>` per master-plan § 4 default lean. The quantum-kernel will surface which two paths share the most patch DNA, helping us pick between Graphene-vs-Calyx if Q9 = banking-matters.

## § 9 What this lane CAN do now (still P0)

Active research-tier work this lane can autonomously pursue without depending on operator Q1-Q10:

1. **This doc** ✅ scaffolded
2. **Clone the canonical bluejay tree READ-ONLY** to `projects/sinister-os/mobile/source/upstream-bluejay-readonly/` (no patches written, just indexed for grep). Disk: ~6-8 GB. Time: ~10-20 min on a fast NVMe. **No operator gate needed** — read-only, doesn't commit binaries (sized to `.gitignore`). Useful for symbol-level greps when P3 starts.
3. **Sepolicy delta draft** — write `source/sepolicy-deltas/eve-system-app.te.draft` based on Tensor G1 sepolicy known patterns (cross-reference AOSP master `system/sepolicy/private/system_app.te`). Pure paper exercise; no compile until P3.
4. **EXPAND-PR audit for cuttlefish-specific UI primitives** — extend `patterns-md-mobile-gap-audit-2026-05-24` to call out which primitives must work on x86_64 SwiftShader (no Mali). Mostly Liquid Glass blur perf — write a `cvd-rendering-budget.md` listing tokens that may need fallback recipes.
5. **Build-env Dockerfile draft** — Google's recommended Ubuntu 22.04 LTS env spec is well-documented; we can scaffold `source/build/Dockerfile` now. Don't actually build; just spec.
6. **Update branding-spec § 4** to point at `patterns-md-mobile-gap-audit-2026-05-24.md` per the audit's § 7 recommendation.
7. **OPERATOR-ACTION-QUEUE row** — surface Q1-Q10 to operator's queue so they have a single-click answer surface (currently the questions live only in master-plan § 10).

**Items #1, #2, #5, #6, #7 are the next-3-turn queue.** Item #2 (cloning the kernel tree) is the most material toward "keep working and testing the custom kernel" — it gives this lane local greppable source.

## § 10 Composes with

- `sinister-os-mobile-doctrine-2026-05-24` (lane doctrine)
- `branding-spec-2026-05-24` (UI inheritance) — branding's purple override applies at framework-res level (not kernel)
- `patterns-md-mobile-gap-audit-2026-05-24` (Compose theme bridge gap audit; sibling research)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs at gate; this doc is **scaffolded**, not shipped)
- `github-first-sourcing-doctrine-2026-05-24` (prior-art search ran, returned zero due to GPL filter, documented as non-find)
- `agent-autonomy-push-and-completion-2026-05-23` (this lane pushes agent/sinister-os-mobile/* freely; no kernel push needed at P0)
- Sister lanes: `sinister-os` (PC) shares EVE control IPC patterns — kernel surface differs (Linux desktop vs Android), but sepolicy thinking transfers
