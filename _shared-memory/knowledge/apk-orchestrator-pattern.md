<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 1
  half_life_days: 180
-->
> **Author:** Sinister Kernel APK (Claude agent, 2026-05-19)

# Topic: Sinister Detector APK as single phone-side orchestrator for KSU modules

**Slug:** apk-orchestrator-pattern
**First discovered:** 2026-05-18 by Sinister Kernel APK
**Last updated:** 2026-05-19 by Sinister Kernel APK
**Status:** workaround
**Tags:** apk, orchestrator, ksud, module-install, asset-bundle, sinister-detector

## Problem

Operator workflow for KSU module management required jumping between KSU Manager (install/enable), a file manager (drop zip), and ad-hoc shell for everything else. Mixed-surface UX, easy to misorder steps, no audit trail. Rebranding upstream `Sinister-RKA` modules at the bytes level is blocked (see `service-apk-hash-check.md`), so we can't fold the workflow into the modules themselves.

## Why it happens

KSU Manager is the only app with kernel-trusted SU prompts (cert hash pinned by the Wild kernel). Anything that wants to issue privileged `ksud` commands must either be KSU Manager itself, or run as a child of an SU-granted shell — which means a separate app can drive `ksud` once SU is granted to *it* via KSU Manager's prompt.

Sinister Detector APK already runs in the operator's hand for other purposes. Promoting it to orchestrator avoids shipping yet another app, and keeps KSU Manager as the trust anchor (we don't rebrand or fork it; see `ksu-manager-sister-app-pattern.md`).

## Fix or workaround

**Pattern:** Detector becomes the single phone-side entry point. It ships V1 module zips as APK assets and invokes `ksud` via root shell.

- **Asset bundle:** V1 module zips ship inside the APK at `assets/modules/<id>.zip`. A `manifest.json` describes each one.
- **Shell layer:** `libsu` + `ShellRunner.runSu(...)` for privileged commands.
- **Commands routed:** `ksud module install <zip>`, `ksud module enable <id>`, `ksud module disable <id>`, `ksud module uninstall <id>`.
- **Trust chain:** KSU Manager retains the SU grant prompt. Operator approves Detector once → Detector orchestrates everything else.
- **UX flow:** Detector → Settings → Modules.

Phases landed:

- **Phase 0 (2026-05-18):** Read-only registry — Detector enumerates installed modules via `ksud module list`, displays state.
- **Phase 1 (2026-05-18 → 2026-05-19):** Enable / Disable / Uninstall actions wired with a confirm dialog before destructive ops.
- **Phase 2 (2026-05-19):** Install-from-asset — `manifest.json` driven `AvailableToInstallCard` lists bundled zips, single-tap install via `ksud module install`.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Kernel APK
Phase 2 landed. `AvailableToInstallCard` + `manifest.json` schema working. Bundled V1 zips install cleanly. End-to-end orchestration verified on phone 1.

### 2026-05-18 by Sinister Kernel APK
Phase 0 + Phase 1 landed same day. `libsu` integration via `ShellRunner.runSu` clean; KSU SU prompt fires once on first privileged call, subsequent ksud invocations reuse the grant.

## Related topics

- [service-apk-hash-check](./service-apk-hash-check.md)
- [ksu-manager-sister-app-pattern](./ksu-manager-sister-app-pattern.md)
- [enrollment-buildconfig-gate](./enrollment-buildconfig-gate.md)
