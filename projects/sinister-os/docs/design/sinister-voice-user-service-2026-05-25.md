# sinister-voice — user-session voice oracle for Sinister OS

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** `sinister-os` (PC sub-lane primary; mobile sub-lane sec.)
> **Status:** DESIGN — implementation queued behind P3 (EVE shell)
> **Composes-with:** `docs/design/sinister-eve-service-state-machine-2026-05-25.md` (system daemon contract) + `source/eve-llm-bridge/SPEC-2026-05-25.md` (LLM IPC contract)
> **Operator hard-canonical:** *"EVE has complete control with no nonsense ... I can still play games"* (CLAUDE.md § Why)

---

## 1. What sinister-voice IS (and isn't)

**IS:** A *per-user-session* systemd `user@.service` unit running as the operator's UID. Always-on wake-word listener; on activation, transcribes a short utterance and routes the intent to the right downstream — usually the EVE-LLM bridge (`chat.send`) or the EVE system daemon (`/run/sinister/eve.sock`).

**ISN'T:**
- Not a system daemon. The `sinister-eve.service` daemon owns root-equivalent control via the curated NOPASSWD sudoers allowlist; `sinister-voice` is a UI surface that *talks* to it. Privilege separation is intentional.
- Not a cloud voice service. All wake-word + transcription happens locally. Hetzner only sees the *text intent*, never raw audio. This is operator-canonical: zero telemetry without opt-in.
- Not a phone OS surface. Pixel 6a gets a different voice surface (Compose tile + Android `SpeechRecognizer`) — covered in § 9.

## 2. Why a separate user-service (not just a binary in the EVE daemon)

Five reasons, ordered by importance:

1. **Privilege boundary.** The mic is the operator's mic, not the system's. Running it as the operator's UID means it inherits PulseAudio/PipeWire session permissions naturally and `pulsemixer` / mute-button works as expected. Running as `eve` daemon UID would require ugly `acl` workarounds on `/dev/snd/*`.
2. **Per-session state.** When the operator logs out (or a second user logs in), voice goes away with them. A system daemon would have to multiplex across users — needless complexity.
3. **CPU budget visible.** systemd `user@.service` is in the operator's cgroup, so the CPU + memory cost is attributed to the operator's session (visible in `systemd-cgtop`, attributable on a shared machine if Leo ever logs in).
4. **Crash isolation.** Wake-word ML model crashes don't take down the EVE control daemon. The mic stops working; the operator's `eve` CLI + waybar pill + games keep running.
5. **Compositor-aware.** Voice surface needs to know about screen-lock / DND / fullscreen-game state (you don't want EVE listening during a multiplayer match unless explicitly opted in). Compositor-aware checks are trivial from the user session; awkward from a system daemon.

## 3. Architecture

```
+--------------------------------------------------------+
| Operator user session (UID 1000, systemd --user)       |
|                                                        |
|  +--------------------------------------------------+  |
|  | sinister-voice.service (Type=notify)             |  |
|  |                                                  |  |
|  |  Threads:                                        |  |
|  |   1. wake_loop  — PipeWire capture -> openWakeWord (CPU)
|  |   2. transcribe — whisper.cpp tiny.en or ggerganov-distil-small
|  |   3. intent     — local NLU (regex + small classifier) -> route
|  |   4. mute_watch — listens for compositor + game events            |
|  |                                                  |  |
|  |  IPC out:                                        |  |
|  |   - /run/user/1000/sinister/voice.sock (UDS JSON-RPC, for waybar)
|  |   - /run/sinister/eve.sock          (system EVE daemon, intents)
|  |   - /run/sinister/eve-llm.sock      (LLM bridge, chat intents)
|  +--------------------------------------------------+  |
|                                                        |
|  +--------------------------------------------------+  |
|  | waybar [voice indicator]                         |  |
|  |   shows: idle / listening / transcribing / muted |  |
|  |   click: toggle mute   right-click: persona menu |  |
|  +--------------------------------------------------+  |
+--------------------------------------------------------+
```

## 4. Wake-word + transcription model choice

### 4.1 Wake-word: openWakeWord (recommended)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **openWakeWord** | Fully FOSS, CPU-only, ~0.3% idle CPU on Zen3, custom wake-words trainable in ~30 min | Tiny accuracy edge cases | **PICK** |
| picovoice Porcupine | Best accuracy | Non-commercial license restrictive; phone-home telemetry | Reject |
| Snowboy | Was great | Project archived 2020, no maintenance | Reject |
| MFCC + DTW custom | Total control | Reinventing the wheel | Reject |

**Wake word:** `"hey eve"`. Custom-trained sample bundled at `/usr/share/sinister/wakeword/hey-eve.tflite`. Threshold tunable in `~/.config/sinister/voice.toml`.

### 4.2 Transcription: whisper.cpp + Distil-Whisper small.en

| Option | Latency (utterance < 5s) | CPU | RAM | Quality | Verdict |
|---|---|---|---|---|---|
| **Distil-Whisper small.en (whisper.cpp)** | ~400ms | spike ~30% 1 core | ~600MB | great for short commands | **PICK** |
| Whisper tiny.en | ~150ms | spike ~10% 1 core | ~150MB | OK for short, struggles on names | fallback if RAM-constrained |
| Whisper base.en | ~800ms | spike ~50% | ~1.2GB | best | overkill for command-style |
| Vosk small en-us | ~200ms | low | ~150MB | mediocre, no punctuation | reject |
| Cloud (whisper-1, Deepgram) | ~600ms RTT | 0 | 0 | great | **VIOLATES OPERATOR CANONICAL** (telemetry / audio leaves machine) — reject |

**Default:** Distil-Whisper small.en, GPU-backed via `whisper.cpp` CUDA build if NVIDIA present, otherwise CPU. Configurable via `voice.toml`.

### 4.3 Local NLU (intent routing)

Tier 1 — **regex prefix** (instant, deterministic):
```
^(open|launch) (.+)        -> eve.exec_intent {"intent":"launch_app","arg":"$2"}
^(close|kill) (.+)         -> eve.exec_intent {"intent":"close_app","arg":"$2"}
^(switch to|focus) (.+)    -> eve.exec_intent {"intent":"focus_window","arg":"$2"}
^(mute|unmute|pause) eve   -> sinister-voice self-toggle
^volume (up|down|set \d+)  -> eve.exec_intent {"intent":"volume","arg":"$1"}
^(brighten|dim) screen     -> eve.exec_intent {"intent":"brightness","arg":"$1"}
^(lock|sleep|reboot|shutdown) (the )?(machine|computer|system) -> CONFIRM-CHORD then eve.exec_intent
```

Tier 2 — **classifier** (when regex misses):
Tiny scikit-learn LogReg (~50KB) trained on ~300 operator examples. Classifies into `{launch, focus, control, chat, query, unknown}`. `chat` and `query` always route to the EVE-LLM bridge `chat.send` with persona = `default` or operator's pinned persona.

Tier 3 — **fall through to chat**:
If both miss, treat the whole utterance as a chat message and send to `chat.send`. EVE-the-LLM is the universal fallback ("dictation of intent" pattern).

### 4.4 Confirm-chord for destructive intents

Destructive ops (`reboot`, `shutdown`, `lock`, anything that calls `eve.exec_intent` with `intent in {"reboot","shutdown","format","delete"}`) require a hold-to-confirm chord. Voice says *"Confirm by holding Mod+Space"*. If chord pressed within 3s, executes; else cancels. Prevents children, parrots, and ambient TV from rebooting the workstation.

## 5. systemd unit

`/etc/systemd/user/sinister-voice.service`:

```ini
[Unit]
Description=Sinister voice oracle (per-user)
After=pipewire.service pipewire-pulse.service sinister-eve.service
Wants=pipewire.service

[Service]
Type=notify
ExecStart=/usr/bin/sinister-voice --config %h/.config/sinister/voice.toml
Restart=on-failure
RestartSec=2s

# CPU budget (operator-canonical "I can still play games")
CPUQuota=12%        # hard ceiling on the user's CPU share
CPUWeight=20        # low priority vs game / IDE
IOWeight=20
MemoryHigh=800M     # soft limit
MemoryMax=1200M     # hard limit (whisper-base would breach; fallback to tiny if hit)

# Privacy
PrivateTmp=yes
ProtectHome=tmpfs   # voice does NOT touch operator's home except /etc/sinister/voice.toml
                    # readonly via BindReadOnlyPaths below
BindReadOnlyPaths=%h/.config/sinister/voice.toml /usr/share/sinister/wakeword
NoNewPrivileges=yes

[Install]
WantedBy=default.target
```

Enabled per-user via `systemctl --user enable sinister-voice.service`. Sinister OS installer flips this on for the operator's UID by default; new users opt in.

## 6. IPC out — what voice calls

### 6.1 To the EVE system daemon — `/run/sinister/eve.sock` (system control intents)

JSON-RPC per state-machine doc § 5.

```json
{"jsonrpc":"2.0","id":"v-uuid","method":"exec_intent",
 "params":{"intent":"launch_app","args":{"app":"firefox"},"source":"voice","operator_session_id":"...","utterance_hash":"sha256:..."}}
```

`source: "voice"` lets the EVE daemon apply voice-specific policy (no game-state interrupt during multiplayer; audit log every voice intent regardless of severity).

### 6.2 To the EVE-LLM bridge — `/run/sinister/eve-llm.sock` (chat intents)

Standard `chat.send` per EVE-LLM bridge SPEC-2026-05-25.md § 4.1, with extra param:

```json
{"jsonrpc":"2.0","id":"v-uuid","method":"chat.send",
 "params":{"persona":"<pinned-or-default>","message":"<utterance>",
           "context_window":"recent","source":"voice"}}
```

Reply is read aloud via espeak-ng (default; FOSS, offline) OR piper-tts (better quality, slightly heavier — operator switchable in `voice.toml`).

### 6.3 To waybar — `/run/user/1000/sinister/voice.sock` (status)

Long-lived JSON stream: `{state:"idle"|"listening"|"transcribing"|"speaking"|"muted", last_utterance:"...", last_reply_preview:"..."}` emitted on every state change. Waybar custom module subscribes and re-renders.

## 7. Compositor-aware mute (the "don't ruin my game" rule)

`mute_watch` thread subscribes to compositor events. Auto-mute conditions (configurable in `voice.toml`):

| Condition | Default action | Operator override |
|---|---|---|
| Fullscreen game detected (gamemode.target active OR Steam game running) | mute wake-word | `auto_mute_gaming = false` |
| DND mode on (Hyprland `dnd`) | mute wake-word | `auto_mute_dnd = false` |
| Screen locked | mute wake-word | `auto_mute_locked = false` |
| Operator on a call (PulseAudio sink-input from zoom/discord/slack) | mute wake-word | `auto_mute_call = false` |
| Headphones unplugged + speakers carrying audio (likely shared room) | DOWNGRADE: still wake but no TTS reply | `auto_demote_speakers = false` |

Mute is **always** indicated in waybar (red icon). Operator can manually unmute via click.

## 8. Security model

- **No audio leaves the machine.** Wake-word + transcription both local. Only the transcribed *text intent* is sent over UDS (and downstream to Hetzner only via `chat.send`, which is opt-in by chatting).
- **Audio buffer is RAM-only** (`PrivateTmp=yes`). No `/tmp/voice-*.wav` files. Wake-word runs on a rolling 1.5s ring buffer; on activation, the buffer + next 5s are passed to whisper.cpp via memory pipe.
- **Audit log: text-only.** `~/.local/share/sinister/voice/audit.jsonl` records `{ts_utc, utterance_text, intent_routed, downstream_status_code}`. Audio NEVER logged. Rotated weekly by `logrotate --user`.
- **Hard mute key.** `Mod+Shift+M` toggles a kernel-level mic mute via PipeWire (mic stream goes to `/dev/null`). When hard-muted, waybar shows a different icon ("HARD MUTED") and even `sinister-voice` cannot un-hard-mute itself; requires operator keypress.
- **Microphone permission via Wayland portal.** First launch: xdg-desktop-portal mic permission prompt. Operator grants once; revocable via portal settings.

## 9. Mobile sub-lane (Pixel 6a)

Different surface, different constraints. **Separate from this design** — voice on phone uses Android's `SpeechRecognizer` with on-device model (Pixel 6a supports it). Compose UI in Sinister-Panel-mobile. Routes intents to the Hetzner panel chat endpoint directly (no local UDS daemon — phone has no `/run/sinister`).

This design is **PC-only**. A sibling design doc `sinister-voice-mobile-2026-05-25.md` will be queued in the mobile sub-lane after mobile P1 picker lands.

## 10. Failure modes + behavior

| Failure | sinister-voice behavior | UI |
|---|---|---|
| openWakeWord model fails to load | Service crashes; systemd restarts; if 3 restarts in 60s, stops | Waybar shows red "voice failed" |
| Mic access denied by portal | Service starts but enters `DENIED` state | Waybar shows "mic blocked"; click opens portal settings |
| whisper.cpp OOM (MemoryMax breach) | Falls back to tiny.en model; logs warning | Waybar tooltip notes "downgraded model" |
| EVE system daemon socket unreachable | Intent routes fail with `transport_error`; voice replies "EVE daemon offline" via TTS | Waybar shows amber |
| EVE-LLM bridge socket unreachable | Chat intents fail with `panel_offline`; voice replies "I'm offline" via TTS | Waybar shows amber |
| Audio device disappeared (USB mic unplugged) | mute_watch detects, service idles waiting for new device | Waybar shows "no mic" |
| Operator says "hey eve" in fullscreen game | Auto-mute fires; wake-word ignored (unless `auto_mute_gaming = false`) | No state change in waybar (mute is steady) |
| TTS engine (espeak-ng / piper) missing | Reply text shown in waybar tooltip + sent to notification daemon; no audio | Waybar shows speech-bubble icon for 5s |

## 11. Config file — `~/.config/sinister/voice.toml`

```toml
[wakeword]
phrase = "hey eve"
model_path = "/usr/share/sinister/wakeword/hey-eve.tflite"
threshold = 0.6
backend = "openwakeword"

[transcription]
model = "distil-whisper-small.en"     # or "whisper-tiny.en" / "whisper-base.en"
backend = "whisper.cpp"
device = "auto"                       # "auto" / "cuda" / "cpu"
max_utterance_s = 7

[nlu]
classifier_path = "/usr/share/sinister/nlu/intent-clf.joblib"
fallback_to_chat = true

[chat]
default_persona = "default"
pinned_persona = ""                   # operator override
read_replies_aloud = true
tts_engine = "piper"                  # "piper" / "espeak-ng" / "none"
tts_voice = "en_US-libritts_r-medium"

[mute]
auto_mute_gaming = true
auto_mute_dnd = true
auto_mute_locked = true
auto_mute_call = true
auto_demote_speakers = true

[security]
require_chord_for = ["reboot", "shutdown", "format", "delete", "rm"]
chord = "Mod+Space"
chord_timeout_ms = 3000
audit_log_path = "~/.local/share/sinister/voice/audit.jsonl"
audit_retention_days = 30

[budget]
cpu_quota_pct = 12
mem_high_mb = 800
mem_max_mb = 1200
```

## 12. P3 acceptance criteria (when the gate opens)

10 tests; all must pass on a freshly installed Sinister OS VM:

1. `systemctl --user start sinister-voice.service` → `active (running)` within 3s.
2. Wake word triggers within 600ms of saying "hey eve" in quiet conditions.
3. Transcription of "launch firefox" routes to `eve.exec_intent{intent="launch_app",arg="firefox"}` and Firefox opens within 2s of utterance end.
4. Chat intent ("what's the weather like in Berlin?") routes to `chat.send`, reply TTS'd within 3s.
5. Destructive intent ("reboot the machine") prompts confirm-chord; without chord, nothing happens; with chord, `eve.exec_intent{intent="reboot"}` fires.
6. Fullscreen Steam game starts → wake-word auto-mutes within 1s; waybar updates.
7. Headphones unplugged during a chat reply → TTS suppressed mid-sentence; text shown in notification.
8. `Mod+Shift+M` hard-mute toggles within 100ms; service cannot un-hard-mute itself.
9. CPU idle (no wake) sustained < 2% on Ryzen 7 5800X3D over 60s.
10. No audio data found in `/tmp`, `~/.cache`, or `/var/log` after 1h of normal use (`find` returns nothing matching `*.wav` / `*.opus` / `*.raw`).

## 13. Cross-references

- EVE system daemon contract: `docs/design/sinister-eve-service-state-machine-2026-05-25.md` (§ 5 intent socket protocol)
- EVE-LLM bridge contract: `source/eve-llm-bridge/SPEC-2026-05-25.md` (§ 4.1 chat.send)
- Master plan § P3 (EVE shell on Sinister OS, operator-gated)
- CLAUDE.md § "EVE-as-OS-shell design constraints" (voice surface as user service)
- Mobile counterpart (queued): `mobile/docs/design/sinister-voice-mobile-2026-05-25.md` (not written; waits on mobile P1)
- Operator-canonical "I can still play games" → § 7 compositor-aware mute is the operationalization
- No-bullshit doctrine rule 1: this doc is `shipped` (design-only); implementation = `queued behind P3` (explicit in § 12)
