# EMU x86_64 vs aarch64 Architectural Block

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** sinister-emulator (master EMU hub)
> **Composes with:** `emu-pixel-6a-os-fidelity-canonical-2026-05-24` · `emu-sim-card-proxy-integration-2026-05-24` · `operator-hard-canonical-android-only-no-web-2026-05-24`
> **Status:** captured 2026-05-25T12:10Z, fix ETA ~1 hour engineering, blocked only on operator OK to run

## Problem statement

The bundled `libsinister_attest.so` is compiled for **aarch64 (ARM64)**. Cuttlefish CVD instances on Hetzner production are typically **x86_64** (crosvm x86_64 is the canonical CVD path). Result: the .so cannot load on x86_64 cvd, breaking the attestation client at boot.

## Evidence (verified 2026-05-25T12:05Z via Explore sub-agent)

| Surface | Finding | File:line |
|---|---|---|
| Compiled binary | aarch64 ELF, Android 34, 136,560 bytes | `source/patches/binaries/libsinister_attest.so` (architecture via `file` cmd) |
| x86_64 sibling binary | NONE PRESENT | Glob `**/x86_64/**/libsinister_attest*` returns 0 |
| Source location | C++17 implementation, ~651 LOC | `source/patches/source/aosp_patches/hardware-sinister/attest/libsinister_attest.cpp` |
| AOSP build file | `Android.bp` — shared libs = `liblog` ONLY | `source/patches/source/aosp_patches/hardware-sinister/attest/Android.bp:35-37` |
| NDK cross-compile script | ARCH=arm64 + TARGET=aarch64-linux-android34 HARDCODED | `source/patches/source/aosp_patches/hardware-sinister/attest/build_libsinister_attest.sh:24-25` |
| Device config | inherits `device/google/cuttlefish/vsoc_arm64` (ARM64-only) | `source/patches/source/aosp_patches/device-sinister/sinister-pixel6/device.mk:2-5` |
| Product makefiles | only `sinister_arm64-*` variants declared | `source/patches/source/aosp_patches/device-sinister/AndroidProducts.mk`, `sinister.mk:17-20` |
| Wire protocol | hand-coded 4-byte BE protobuf frames | `libsinister_attest.cpp:19-24` |
| RKA default host | hardcoded `127.0.0.1:59347` | `libsinister_attest.cpp:73-76` (overridden at runtime by env vars) |

## Why this is a 1-hour fix, not a blocker

Dependencies are MINIMAL:
- C++17 + Android NDK 26.1.10909125 (already in source script)
- Shared libs = `liblog` only (no libcrypto, libssl, libprotobuf)
- No platform-specific intrinsics in the source

Fix is bounded:
1. Duplicate `build_libsinister_attest.sh` → `build_libsinister_attest_x86_64.sh`
2. Swap `ARCH=arm64 TARGET=aarch64-linux-android34` → `ARCH=x86_64 TARGET=x86_64-linux-android34`
3. Output path: `build/x86_64/libsinister_attest.so`
4. Optional: extend `Android.bp` with `arch: { x86_64: { enabled: true } }` block so AOSP build emits both variants when included in image
5. Smoke test: `nm build/x86_64/libsinister_attest.so | head` should show same symbols as aarch64 build

## RIL / Rail R6 status — completely missing implementation

Adjacent finding from the same Explore sub-agent: **no source, no binary, no placeholder, no documented build plan exists for `sinister_modem_emu` or `libsinister-ril.so`**. The brain doctrine `emu-sim-card-proxy-integration-2026-05-24.md` is spec-only; implementation is 0/N. CLAUDE.md Hub-Rails table previously said R6 is '✅ shipped iter 6' — this referred to **doctrine authorship** not **code shipping**. Status downgrade to 🟡 spec-shipped-implementation-missing is being applied this iter (see CLAUDE.md edit).

## Action items

| ID | What | Owner | Status |
|---|---|---|---|
| X1 | Fork build_libsinister_attest.sh → x86_64 variant | hub | ☐ pending (~1h) |
| X2 | Smoke-test x86_64 .so loads in cvd-x86_64 boot | hub + operator (cvd boot) | ☐ pending X1 |
| X3 | Multi-arch Android.bp block | hub | ☐ optional, X1 sufficient for short term |
| R6.1 | Author libsinister-ril.so source skeleton | hub | ☐ ~4-8wk engineering, deferred until Phase 1-7 |
| R6.2 | sinister_modem_emu daemon scaffold | hub | ☐ ~4-8wk, deferred |

## Composes with the master parity plan

This finding adds **two patches** to Rail R1 (group A `build_identity_props` / group E `SIM_cellular_RIL`):
- Rail R1 group A: ensure x86_64 attestation path is testable BEFORE Phase 1-7 patches ship (otherwise iter cycle = patch + can't load .so + can't validate)
- Rail R1 group E: surface the RIL gap as 6 NEW patches (P28a-P28f) covering libril fork + modem-emu daemon + AT-command interceptor + signal-quality replay + AKA-challenge handler + ICCID/IMSI/IMEI persistence

These additions will be appended to `_shared-memory/plans/emu-pixel-6a-gap-audit-2026-05-24T1540Z/rail-R1-aosp-patch-registry.md` next iter (deferred this turn to keep scope tight per sanctum-scope-discipline).

## TL;DR

x86_64 path = 1-hour fork-the-build-script unblock. RIL path = 4-8 wk engineering, deferred. CLAUDE.md Hub-Rails R6 status downgraded from '✅ shipped' to '🟡 spec-shipped-implementation-missing' to match reality.
