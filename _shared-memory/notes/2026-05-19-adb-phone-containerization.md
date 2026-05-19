> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# ADB phone containerization — agent reference card

**TL;DR:** Each phone is a container. Nothing the PC runs leaks to phones unless YOU explicitly push it to a specific serial. Always `adb -s <SERIAL>`. Never bare `adb shell` when more than one phone is attached.

## Why this matters

Phones P1, P2, P3... share an ADB transport on the PC but they are **independent execution environments**. State that lives on the PC (frida-server, proxies, env vars, scripts) must NOT be assumed to exist on a phone. And state pushed to one phone must NOT be assumed on another.

Specifically:
- frida-server running on PC ≠ frida-gadget on phone. Different binaries. PC having it doesn't mean P1 has it.
- mitmproxy on PC ≠ phone configured for that proxy. The phone needs `settings put global http_proxy 192.168.x.y:8080` AND a CA cert installed in its system trust store.
- ANTHROPIC_API_KEY in PC env ≠ usable on phone. Phones don't have your shell env.
- Anti-tamper bypasses that work on PC (e.g. dummy SafetyNet response) don't work on phone unless the bypass is *pushed* and *running* on the phone.

## Patterns every agent must follow

### 1. Always target by serial

```bash
adb devices              # list serials first
adb -s <SERIAL> shell <cmd>
adb -s <SERIAL> push <local> <remote>
adb -s <SERIAL> pull <remote> <local>
```

Never bare `adb shell` with >1 phone attached.

### 2. Per-phone state tracking

Each phone has a memory file: `D:\Sinister Sanctum\_shared-memory\notes\phones\<SERIAL>.md`. Read before pushing anything; update after. Suggested template:

```markdown
# Phone: <SERIAL> (label: P1 / P2 / ...)

**OS:** Android 14, KernelSU 0.7.0
**Attestation:** Yurikey51 (expires 2026-05-24)
**Last connected:** YYYY-MM-DD HH:MM
**Owner agent:** snap-emu / tiktok-emu / master
**Installed modules:**
  - frida-server-15.x (pushed 2026-05-18, /data/local/tmp/frida-server)
  - LukeShield 1.2 (system module)
  - DETECTOR APK v0.95.0
**Current proxy:** none / 192.168.1.50:8080 / ...
**Notes:**
  - <free-form>
```

### 3. Pushing frida (example)

```bash
# PUSH to P1 ONLY
P1=<P1_SERIAL>
adb -s $P1 push frida-server-16.5.0-android-arm64 /data/local/tmp/frida-server
adb -s $P1 shell "chmod 755 /data/local/tmp/frida-server"
adb -s $P1 shell "/data/local/tmp/frida-server -D &"

# Verify
adb -s $P1 shell "ps -A | grep frida"

# Update phone memory
# D:\Sinister Sanctum\_shared-memory\notes\phones\$P1.md
# Append: frida-server-16.5.0 pushed YYYY-MM-DD HH:MM by <agent-name>
```

### 4. Per-phone proxy configuration

```bash
# Phone-by-phone, NOT system-wide
adb -s $P1 shell "settings put global http_proxy 192.168.1.50:8080"
adb -s $P2 shell "settings delete global http_proxy"   # clear on the other one
```

### 5. Forbidden commands

| Command | Why forbidden | Use this instead |
|---|---|---|
| `adb kill-server` | Affects ALL phones at once | `adb -s <serial> reconnect` |
| `adb start-server` | Restarts global daemon | n/a, individual reconnects |
| `adb shell <cmd>` (multiple phones attached) | Targets first device unpredictably | `adb -s <serial> shell <cmd>` |
| `adb forward tcp:N tcp:N` without serial | Forwards on default device | `adb -s <serial> forward tcp:N tcp:N` |
| `adb logcat` (no serial) | Bleeds logs from one phone into another's debug session | `adb -s <serial> logcat` |

### 6. Sanctum Console enforcement (when shipped)

The Sanctum Console's "Phone viewer" sidebar tool will:
- List phones from `adb devices` and require serial-targeting for every UI action
- Show per-phone memory cards (the .md files above)
- Refuse to issue any `adb <cmd>` that doesn't include `-s <serial>`
- Display a live tail of `adb -s <serial> logcat` per-phone (separate tabs, no bleed)

Until the UI ships, agents enforce this discipline manually.

## Lane discipline (which agent touches which phone)

- **snap-emu agent** owns P1, P2 when used for Snap operations
- **tiktok-emu agent** owns P1, P2 when used for TikTok operations
- **kernel-apk agent** owns ALL phones for module install / kernel updates
- **master agent** does NOT push anything to phones without explicit operator OK
- Cross-platform conflicts on the same phone (e.g. Snap + TikTok wanting different proxies) → operator decides, agents coordinate via inbox before acting

## Quick reference card

Pin this next to your terminal:

```
adb devices                           # see serials
adb -s <SER> shell                    # interactive on ONE phone
adb -s <SER> push X Y                 # push file to ONE phone
adb -s <SER> shell "<cmd>"            # run command on ONE phone
adb -s <SER> logcat -d -s <tag>       # filtered log dump
adb -s <SER> reconnect                # reset only this phone
```

That's it. No magic. Just always `-s <SERIAL>`.
