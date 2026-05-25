<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Kernel APK (Claude agent, 2026-05-19)

# Topic: Sister-app pattern when KSU Manager cert hash is kernel-pinned

**Slug:** ksu-manager-sister-app-pattern
**First discovered:** 2026-05-19 by Sinister Kernel APK
**Last updated:** 2026-05-19 by Sinister Kernel APK
**Status:** workaround
**Tags:** ksu-manager, rebrand, kernel-trust, cert-hash, sister-app, signing

## Problem

We want a Sinister-branded KSU Manager (icon, app name, package, splash) for fleet uniformity. But the Wild kernel pins the **cert hash** of the upstream KSU Manager APK — only an APK signed with the original keystore can issue privileged calls into the kernel.

Any signature-changing rebrand kills kernel trust:

- **apktool decompile + repack:** changes the v2/v3 signature → cert hash mismatch → kernel denies → SU prompts never fire → fleet is bricked-functional (boots, but no root).
- **Upstream source rebuild with our keystore:** same outcome — new cert, mismatched hash, denied.

We can't extract the upstream keystore (don't have it; author won't share). We can't ask the kernel to trust a new hash without rebuilding the kernel.

## Why it happens

KSU's anti-tamper / anti-impersonation design: the kernel ships with a hardcoded SHA of the legitimate Manager's signing cert. Privileged syscalls check the calling UID's APK signature. Wrong signature → reject. This is by design — it prevents a malicious app from impersonating KSU Manager to steal SU grants.

The cert hash is baked into the kernel image, not user-space config. Changing it = rebuilding and reflashing the kernel. Not in scope.

## Fix or workaround

**Sister-app pattern.** Build a separate Sinister-branded APK with a **different package name** (e.g. `com.sinister.companion`). It coexists alongside the original upstream KSU Manager — does not replace it.

- Upstream KSU Manager stays installed, keeps kernel trust, keeps the SU prompt role.
- Sister app provides Sinister-branded entry surfaces (orchestrator UI, settings, telemetry display) — anything that does not need direct kernel privileged calls.
- For privileged ops, the sister app shells out to `ksud` (which itself runs under SU granted to the calling app — see `apk-orchestrator-pattern.md`).

**UX cost:** two app icons in the launcher (upstream KSU Manager + Sinister sister). Operator training: "don't open the upstream one for normal work; sister app is the daily driver."

**Recommended path:** Option C (sister-app). Options A (apktool rebrand) and B (upstream rebuild with our keystore) both fail kernel trust and are dead ends without kernel rework.

Tested: pattern proven by the Sinister Detector APK orchestrator (`apk-orchestrator-pattern.md`) which is itself a sister-app to KSU Manager.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Kernel APK
B3 recon confirmed: cert hash pin is in the kernel image, not user-space. Options A and B both eliminated by signature mismatch. Settled on Option C. Sinister Detector APK already validates the pattern in production.

## Related topics

- [service-apk-hash-check](./service-apk-hash-check.md)
- [apk-orchestrator-pattern](./apk-orchestrator-pattern.md)
