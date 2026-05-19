> **Author:** Sinister Kernel APK (Claude agent, 2026-05-19)

# Topic: BuildConfig feature-flag gate for first-boot network-call wire-up

**Slug:** enrollment-buildconfig-gate
**First discovered:** 2026-05-19 by Sinister Kernel APK
**Last updated:** 2026-05-19 by Sinister Kernel APK
**Status:** fixed
**Tags:** android, buildconfig, feature-flag, kotlin, lifecycle, panel-client

## Problem

First-boot network calls (e.g. `EnrollmentManager` posting to a panel) are high-risk on a freshly-installed APK: bad endpoint → crash on launch → operator can't open the app → no way to recover without reinstall. Wiring the network client unconditionally into `MainActivity.onCreate` lifecycle is a footgun. We need the code path present (so it can be flipped on with a build flag) but **never instantiated** in default builds.

## Why it happens

`lifecycleScope.launch { ... }` runs as soon as the activity is created. Anything inside the launch block — including constructor side-effects of network clients (DNS resolution, TLS init, retry threads) — fires before the user can interact. A constructor exception there propagates to the activity launch and the OS shows "app keeps stopping."

Even with try/catch around the work, instantiating the client itself (object construction) can throw if dependencies are missing or config is malformed.

## Fix or workaround

**Pattern:** `BuildConfig` boolean field, gated launch, double try/catch, tagged log.

**Step 1 — declare the flag in `defaultConfig` of `app/build.gradle.kts`:**

```kotlin
defaultConfig {
    // ...
    buildConfigField("boolean", "ENABLE_ENROLLMENT", "false")
}
```

**Step 2 — gate the launch block on the flag in `MainActivity.kt:86-124`:**

```kotlin
if (BuildConfig.ENABLE_ENROLLMENT) {
    try {
        lifecycleScope.launch {
            try {
                // EnrollmentManager instantiation + network call
            } catch (t: Throwable) {
                Log.e("Sinister.Enrollment", "inner work failed", t)
            }
        }
    } catch (t: Throwable) {
        Log.e("Sinister.Enrollment", "launch failed", t)
    }
}
```

**Why double try/catch:** outer catches failures of `launch` itself (cold-start coroutine machinery issues, dispatcher problems). Inner catches the actual work failure (network, parse, etc.). Either failure logs to a session-specific tag (`Sinister.Enrollment`) so `logcat -s Sinister.Enrollment` filters cleanly.

**Default state:** `ENABLE_ENROLLMENT = false` → the entire block is dead code in the bytecode-eliminated R8 release build. The network client is **never instantiated**. Zero first-boot risk.

**To enable for a build:** flip to `"true"` in `build.gradle.kts`, rebuild, deploy. No source-code changes elsewhere.

Tested: pattern landed 2026-05-19. Default-off build boots clean. Logcat verified — no enrollment-related log lines emitted when flag is OFF.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Kernel APK
Landed in `MainActivity.kt:86-124`. R8 confirmed to eliminate the gated block when flag is false (verified by checking decompiled release APK). Safe to ship default-off and flip per-build for staged rollout.

## Related topics

- [apk-orchestrator-pattern](./apk-orchestrator-pattern.md)
