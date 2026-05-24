<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Voice Prompting POC :: Path A (push-to-record hotkey)

**Created:** 2026-05-23T22:00Z (EVE on Sanctum, /loop iter 6)
**Triggering directive:** Operator 2026-05-23: *"i want to add voice promptiong to the system. and you analyze my voice recording and use that as a prompt"*
**Status:** spec + POC scaffold (Path A, push-to-record). Implementation deferred until operator confirms hotkey + accepts transcription cost.
**Path picked:** **A** (push-to-record desktop hotkey) since operator hasn't disambiguated and A is smaller-blast-radius.

---

## Architecture (Path A)

```
┌─────────────────────────────┐    ┌────────────────────────────┐    ┌──────────────────────┐
│ HOTKEY DAEMON (background)  │    │ AUDIO -> TRANSCRIPT         │    │ CLAUDE              │
│ Win+Alt+V hold-to-record    │ -> │ Whisper API or local        │ -> │ POST as next prompt │
│ Releases on key-up          │    │ (faster-whisper / Ollama)   │    │ via session resume  │
└─────────────────────────────┘    └────────────────────────────┘    └──────────────────────┘
        │                                  │                                │
        ▼                                  ▼                                ▼
  _shared-memory/voice-inbox/        _shared-memory/voice-inbox/      claude --resume <uuid>
  recording-<UTC>.wav (raw)          recording-<UTC>.txt (transcript) with -p "<transcript>"
```

## Components

### 1. Hotkey daemon (`tools/sinister-voice/voice-recorder.py`)

- Stdlib + `keyboard` lib (light) OR pure PowerShell via `Add-Type WinMM`.
- Hotkey: `Win+Alt+V` (configurable via `~/.sinister-voice/config.json`).
- Press-and-hold to record; release to stop.
- Saves to `_shared-memory/voice-inbox/recording-<UTC>.wav`.
- Optional: visual indicator (taskbar icon or toast) while recording.

### 2. Transcription worker (`tools/sinister-voice/transcribe.py`)

- Watches `_shared-memory/voice-inbox/*.wav` (inotify-style or polling).
- For each new WAV: call Whisper API (OpenAI / Anthropic doesn't have one yet) OR local Whisper.cpp.
- Writes `recording-<UTC>.txt` alongside the WAV.
- Cost: Whisper API $0.006/min; local is free but needs ~1.5 GB model.

### 3. Claude dispatcher (`tools/sinister-voice/dispatch.py`)

- Watches `_shared-memory/voice-inbox/*.txt`.
- For each new transcript: identify active session (which Sanctum window is foreground or last-used).
- Calls `claude --resume <session-uuid> -p "<transcript>"` OR injects as next user message via the session's `/api/inject` (if RKOJ.exe is hosting).
- Marks the WAV+TXT pair as processed (move to `voice-inbox/_processed/`).

### 4. Sanctum integration

- `automations/start-sinister-session.ps1` registers the voice daemon as a background process on spawn (operator opt-in via env var `SINISTER_VOICE_ENABLED=1`).
- `_shared-memory/voice-inbox/` is gitignored (audio + transcripts are operator-private).
- `_shared-memory/voice-inbox/_metrics.json` tracks: total recordings, total minutes, total transcription cost.

## Operator decisions needed (before implementation)

1. **Transcription provider:** Whisper API ($0.006/min, ~$0.36/hour of recording) OR local Whisper.cpp (free, 1.5GB download, slower)?
2. **Hotkey:** Win+Alt+V default OK or different combo?
3. **Dispatch target:** any active Sanctum session, OR a specific one (operator-tagged)?
4. **Audit trail:** keep raw WAVs forever OR auto-delete after N days?
5. **Wake word for hands-free mode (future Path B):** worth pursuing OR keep push-to-record only?

## Path B (RKOJ.exe mic-button) — what it adds

When operator picks B (or eventually does both):
- PyQt6 button in RKOJ.exe pane header — click to record.
- Live waveform display while recording.
- Transcript appears inline in the chat history before sending to Claude.
- Better UX for in-the-moment voice (no need to switch focus to a hotkey).
- Bigger code surface (~200-300 LOC PyQt6 + audio).

A and B can coexist. A ships first (smaller). B adds polish later.

## POC scaffold shipped this iter

- This spec.
- `tools/sinister-voice/README.md` (placeholder w/ install notes).
- NOT YET shipped: `voice-recorder.py` / `transcribe.py` / `dispatch.py` — operator must answer Q1-Q5 above to determine the exact provider + UX.

## Anti-patterns

1. **Don't autostart the hotkey daemon** without operator opt-in. It captures audio; needs explicit consent.
2. **Don't store raw WAVs in git.** Per-operator-private; lives in gitignored voice-inbox/.
3. **Don't dispatch to Claude without operator-visible transcript.** Hallucinated transcripts must be reviewable before Claude acts.
4. **Don't tie to a specific transcription provider.** Abstract behind `transcribe.py` so swapping Whisper → faster-whisper → Anthropic-future-API is one edit.
5. **Don't bill Tier-3 silently.** Show running $-spent counter in `_metrics.json`; surface to OPERATOR-ACTION-QUEUE if >$1/day.

## Composes with

- `bot-fleet-quick-reference` (transcribed text could become a `librarian.search` query or `triage.classify_text` input)
- `sanctioned-bypasses-doctrine-2026-05-21` (voice is operator-own surface; permission model inherits)
- `headless-spawn-pattern-2026-05-23` (voice daemon runs hidden, no visible windows)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (no actual recording shipped this iter — spec + scaffold only)

## Maintenance

- When operator answers Q1-Q5: ship the 3 Python scripts + wire-in.
- When B is built: add a section here referencing the implementation.
- Brain entry deferred (Rule 7.5 APPROACHING; no new doctrines until consolidate).
