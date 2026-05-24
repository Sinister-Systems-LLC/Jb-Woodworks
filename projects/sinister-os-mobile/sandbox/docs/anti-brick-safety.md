# Anti-brick safety doctrine (binding)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Authority:** binding for the sandbox subdir and any downstream lane that consumes its artifacts
> **Operator constraint (verbatim):** *"so its exact what we need to create perfect snapchat accounts and its not going to brick the phone most importantly"*

The physical Pixel 6a is operator-personal-property. A bricked Pixel 6a is expensive (~$500 device cost + lost calls/signal/2FA continuity). This doctrine guarantees the sandbox NEVER touches the physical device until 5 explicit safety gates have all turned green.

## The 5 gates

| # | Gate | Enforcement |
|---|---|---|
| 1 | **VM-only execution.** All build/boot/test work targets cuttlefish (`vsoc_x86_64`). `fastboot`/`adb sideload`/`heimdall` are NOT installed inside the sandbox image and NOT referenced by any sandbox script. | Static grep gate in `scripts/seven-green-gate.sh` rejects if any sandbox file contains the literal strings `fastboot` (uppercased/lowercased), `sideload`, or `heimdall`. |
| 2 | **7 consecutive green cuttlefish boots.** A kernel artifact is "physical-eligible" only after `seven-green-gate.sh` has logged 7 clean boots in a row (same artifact, no rebuilds between). | `seven-green-gate.sh` writes one line per run to `sandbox/.seven-green-log.jsonl`; physical-flash advisory script reads + counts consecutive `result=pass` rows. |
| 3 | **Operator typed-confirmation for physical flash.** No script in this sandbox emits a `fastboot flash` command. The physical-flash procedure is a manual checklist in `docs/physical-flash-checklist.md` (lands at P5, not in this /loop) that operator follows by hand. | Convention: any path that approaches physical hardware writes a `physical-touch.lock` file the sandbox refuses to overwrite. |
| 4 | **Kernel rollback artifact preserved.** The current stock Pixel 6a boot.img (signed Google factory image) is downloaded + verified-by-hash before any custom kernel work begins; stored at `_vault/sinister-os-mobile/bluejay-stock-boot.img.sha256`. If a custom kernel bricks the device, fastboot-bootloader-mode + this stock boot.img is the unbrick path. | Sandbox script `scripts/verify-rollback-asset.sh` is a precondition for `seven-green-gate.sh`. If the rollback asset is missing/hash-mismatched, the 7-green gate refuses to even count. |
| 5 | **TEE delta is modeled, not assumed away.** Cuttlefish's TEE is software-emulated (`tipc`/`trusty` virtual device); the physical Pixel 6a uses Titan M2 hardware. Snapchat's Play Integrity check pulls hardware-backed attestation. Any test that PASSES in cuttlefish but DEPENDS on a hardware-backed signature is marked `requires-hw-attestation` and counted separately. | Test harness fixtures in `tests/conftest.py` set `pytest.skip(reason="requires-hw-attestation")` when `CVD_TEE_BACKEND=swemu` + the test asks for HW-backed. |

## What "brick" specifically means here

| Severity | What happens | Recoverable? |
|---|---|---|
| **Soft brick** | Device boots into bootloader but won't boot to OS | Yes — `fastboot flash boot stock-boot.img` from bootloader-mode |
| **Hard brick** | Device doesn't respond to power button OR USB | Sometimes — EDL/9008 mode + vendor-only tools; very-Pixel-specific, often vendor-locked |
| **Anti-rollback fuse triggered** | A signed kernel rolled back below the anti-rollback version → device permanently refuses to boot that branch | NO — burned eFuse, irrecoverable |

Gate 4 (rollback artifact preserved) protects against soft brick. Gates 1-3 prevent ever reaching the path where hard brick or fuse-burn becomes possible.

## What is NOT a brick

- Kernel panic in cuttlefish — that's the whole point of cuttlefish. We crash freely there.
- adb disconnect after a bad kernel — restart cvd, root cause is `dmesg` from before the crash.
- Failed Snapchat signup — that's an account-creation logic problem, not a device problem.

## Operator-typed-by-hand contract (P5 only — not in this /loop)

When the sandbox eventually gates a kernel for physical flash (P5 phase, gated by operator), the procedure is:

1. Operator opens `docs/physical-flash-checklist.md`
2. Operator reads each step out loud (no script-driven automation)
3. Operator runs each `fastboot` command at the terminal manually
4. Sandbox observes (via adb) but does not initiate

There is no `--auto-flash` flag anywhere. There never will be.

## Composes with

- master-plan-2026-05-24.md §11 (Phase 5 — physical flash, operator-gated)
- master-plan-2026-05-24.md §13 (Safety + reversibility wall, lane-level)
- no-bullshit-tested-before-claimed-doctrine-2026-05-23 (verbs-at-gate)
- agent-autonomy-push-and-completion-2026-05-23 (autonomy WITHIN the sandbox; gates are the constraint)

## Updated: 2026-05-24
