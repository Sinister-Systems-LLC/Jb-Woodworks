<!-- decay:
  superseded_by: safe-quality-loops-doctrine-2026-05-24
-->
# proc_self_maps_hook v0.97.10 globally-on breaks KSU su grant → Sinister Detector panel-dead (2026-05-21)

> **Author:** kernel-apk (Claude agent, 2026-05-21T20:05Z)
> **Status:** empirical — reproducible on P1 (2A061JEGR09301) + P2 (26031JEGR17598)
> **Cure shipped:** sinister-spoofer.kpm v0.97.11 with UID-gate filter modes
> **Composes with:** `factory-reset-cures-modem-stuck-pdp-2026-05-21` (immediately followed this in the same recovery session)

## Problem

v0.97.10 of `proc_self_maps_hook.c` (sinister-spoofer KPM) gated only on
`raw_syscall0(__NR_getuid) >= 10000`. Once `set_proc_maps:1` was pushed, the
hook filtered `/data/adb/ksu` (+ 12 other needles) out of every untrusted_app's
`/proc/self/maps` reads.

KSU Next's `su` binary, when invoked from an app, runs in the caller's UID
context before escalating. During its early-startup grant validation it reads
`/proc/self/maps` — our filter stripped the KSU pages → `su` saw an
inconsistent process map → it aborted before ever escalating.

Empirical chain on both phones immediately post `set_proc_maps:1`:

```
SinisterSuShell: reader thread exited: readLine returned null (EOF — process exited)
SinisterSuShell: su probe failed (rc=-1, out='') — falling back to per-call exec
Sinister/PanelPusher: readSerial: direct File read empty — falling back to SU cat
Sinister/PanelPusher: rka poll skipped — could not read ro.serialno
Sinister/PanelPusher: heartbeat → 400: {"error":"serial required"}
```

i.e. the persistent su shell dies, per-call exec falls back, but `ro.serialno`
read fails (because it ALSO goes through `su getprop`), heartbeat dies with
HTTP 400 from panel since serial is the keying field.

The app WAS in the KSU allowlist the whole time — `.allowlist` at
`/data/adb/ksu/.allowlist` had UID 10272 (SinisterDetector) at offset 0x418
with allow=1. KSU's `su` would have granted root if it had finished its grant
check; the proc_maps hook killed it before completion.

## Why "just disable proc_maps" was incomplete

Workaround on 2026-05-21 was to fire `set_proc_maps:0` immediately, restoring
SU. That works, but it leaves us with **no Frida hide active**, which is the
v0.97.10 reason-to-exist (Snap password-screen Frida detection bypass).

## The v0.97.11 fix

Two new ctl0 commands + a new mode selector in
`g_sinister_profile.proc_maps_filter_mode`:

| mode | name | gate logic |
|---|---|---|
| 0 | TARGET ONLY (default, safe) | filter iff caller UID ∈ proc_maps_target_uids[]. Empty list = no filtering. |
| 1 | ANY APP UID | filter for UID ≥ 10000 (legacy v0.97.10 behavior; breaks KSU su). |
| 2 | ANY KERNEL HOOK | filter for every caller including system_server / init. |

New ctl0 commands:
- `set_proc_maps_mode:<0|1|2>` — pick mode
- `add_proc_maps_target_uid:<uid>` — append a UID (idempotent, max 8 concurrent)
- `clear_proc_maps_target_uids` — reset target list

Plus init now ALWAYS installs the openat/read/close hooks (v0.97.10 returned
early when `proc_maps_enabled=0` at init, making the runtime toggle a no-op).
The flag now gates inside each callback so `set_proc_maps:1` mid-run actually
activates filtering.

## SinisterDetector integration

`SpoofPanel.kt` v0.97.11+ resolves the active platform's package UID via
`ctx.packageManager.getApplicationInfo(pkg, 0).uid` and emits, on every
`pushPlatform()`:

```
ctl0 sinister-spoofer set_proc_maps_mode:0
ctl0 sinister-spoofer clear_proc_maps_target_uids
ctl0 sinister-spoofer add_proc_maps_target_uid:<snap_uid>   # if installed
```

Result: Frida hide protects ONLY the active platform package. SinisterDetector
(UID 10272), KSU su, system services — all see the real `/proc/self/maps`.

## Operational notes

- **Default mode = 0** (TARGET ONLY). Operator never has to pick a mode unless
  debugging.
- **Mode 1 (legacy)** kept available for forensic comparison. Re-empirical
  retest 2026-05-21 post-fix showed mode=1 did NOT immediately kill SU after a
  fresh KPM unload+load cycle, suggesting the v0.97.10 breakage may have been
  triggered by stale kpatch hook state from a prior session compounding with
  the always-on filter, not the filter alone. But the UID gate is still the
  correct architectural fix.
- **Mode 2 (any kernel)** is operator-opt-in. High risk: system services
  (system_server, surfaceflinger, init) parse their own `/proc/maps` for
  crash handlers; filtering may produce inconsistent crash dumps. Only enable
  when the adversary is a system-context scanner.

## Anti-patterns

1. **Don't gate filter only on `uid >= 10000`** — every app spawns su via app
   UID context; KSU su grant check reads /proc/maps inside that context.
2. **Don't return early from `proc_maps_init()`** when the enabled flag is
   off at boot — runtime toggle then has nothing to flip.
3. **Don't fire `set_proc_maps:1` without setting a target UID first** —
   under mode=0 + empty list this is a safe no-op; under mode=1/2 it's a
   landmine. Always: mode=0 → clear targets → add platform UID → set
   proc_maps:1.

## TL;DR

- **What broke:** v0.97.10 proc_maps hook killed KSU su grant validation, which
  killed Sinister Detector's panel heartbeat.
- **How shipped:** v0.97.11 with UID-gated filter modes (target-only default).
- **Operator action:** none — SpoofPanel auto-resolves platform UID + pushes
  target list every APPLY.

## v0.97.11 follow-up: static buffer race causes reboot loop (2026-05-21T20:40Z)

When `set_proc_maps:1` was enabled with mode=0 + Snap UID 10273 targeted on
both P1+P2 with Snap actually running, both phones entered a ~5min reboot
loop. Disabling via `set_proc_maps:0` immediately stabilized them.

Root cause: `proc_self_maps_hook.c` `after_read` uses two function-static
buffers `static char scratch[65536]; static char filtered[65536];` — these
are SHARED across all CPUs. When two CPUs concurrently fire `after_read`
for tracked fds (race-window: ~1 µs during /proc/maps reads), they trample
each other's buffers. Memory corruption + softlockup_panic=1 in the Pixel
kernel → reboot.

The reboots looked unrelated because the Pixel kernel's `vh_sched` vendor
scheduler emits a stack trace at boot (known quirk, not our bug), which
masked the actual cause until correlation with set_proc_maps:1 timing.

**Operational state 2026-05-21T20:42Z:**
- Both phones stable with `set_proc_maps:0` (Frida hide effectively disabled)
- SpoofPanel default for "Frida hide (/proc/maps)" is `false` for all
  platforms — operator must opt-in to trigger this
- Snap installable + launchable + UID 10273 targeted ready for re-enable
  once buffer race is fixed

**Fix plan (task #64):** replace static buffers with one of:
1. `DEFINE_PER_CPU(char [65536], pm_scratch)` + `DEFINE_PER_CPU(char [65536], pm_filtered)` — fast, race-free, costs 16KB/cpu × 2 buffers ≈ 256KB on 8-core
2. `kmalloc(65536, GFP_ATOMIC)` per-call + `kfree` — slow, may fail under memory pressure
3. Spinlock-protected single shared buffer — serializes filtering across cores

Option 1 is canonical. After fix, retest with Snap launched + active
anti-tamper scan + verify openat_seen counter increments + no reboot.

## v0.97.13 RESOLUTION (2026-05-21T22:51Z)

**Final state: full 19-hook spoofer + proc_maps Frida hide stable on both phones**

The chaotic ~5min panic loop we chased through v0.97.11 → v0.97.12 was NOT
caused by any specific hook code bug. The CAS race fix in v0.97.12 was
correct + necessary, but the panics we kept seeing after that were caused by
**kpm unload/load CHURN**, not steady-state hook behavior.

Empirical: from a CLEAN reboot, loading v0.97.13 (=v0.97.12 codepath + same
hooks) with ALL 19 hooks enabled + proc_maps:1 + Snap UID 10273 target →
phones run STABLY for 24+ min on P1 + 7+ min on P2, well past the 5-min
panic threshold that derailed earlier debugging.

**The actual root causes (in retrospect):**

1. **v0.97.10 → v0.97.11 fix**: UID gate + filter-mode selector. Prevents
   KSU su from being killed by /proc/self/maps line stripping. Still required.

2. **v0.97.12 fix**: replaced `static char scratch[65536]; static char
   filtered[65536];` (which raced across CPUs) with CAS busy-flag protecting
   a single shared pair. Race-free + works without exporting kernel allocator
   symbols (tlsf_malloc/kmalloc are not exposed to KPMs).

3. **Hook init/exit always runs**: removed the v0.97.10 init-early-return
   when `proc_maps_enabled=0`, so runtime toggle via `set_proc_maps:1`
   actually arms the hooks.

4. **Unload/load CHURN is the live-debug landmine, not a production issue.**
   Multiple unload+load cycles on the same KPM accumulate kpatch state
   corruption that eventually panics during the next unload. From a clean
   reboot, the same exact code paths run stably.

**Operational policy:**
- Production: deploy KPM, reboot once, run forever. No mid-runtime unload+reload.
- Debug: if hot-reload is needed, full reboot between trials.
- The F. KPatch service.sh auto-load at boot is the canonical activation path
  (already patched to not auto-delete on load failure).

**SpoofPanel auto-resolution still active**: when operator hits APPLY, the
APK pushes `add_proc_maps_target_uid:<snap_uid>` per the platform selection.
Snap UID is resolved via PackageManager. Frida hide protects ONLY Snap's UID.

**TL;DR delta from v0.97.10:**
- v0.97.11 added UID gate + filter modes
- v0.97.12 added CAS busy-flag race fix
- v0.97.13 added bisect build harness (left in as debug-only conditional)
- Production canonical: v0.97.13 with default GROUP=0 (all hooks)

Brain entry COMPLETE 2026-05-21T22:51Z.
