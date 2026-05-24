<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# sinister-voice :: voice prompting for the fleet

**Status:** scaffold only. Spec at `_shared-memory/plans/voice-prompting-poc-2026-05-23/spec.md`.

## What this will be

Push-to-record desktop hotkey (Path A) -> transcribe -> dispatch as Claude prompt.

## Why this is a scaffold

Operator hasn't yet picked:
1. Transcription provider (Whisper API vs local Whisper.cpp)
2. Hotkey binding (default Win+Alt+V?)
3. Dispatch target (any session vs operator-tagged)
4. Audit retention
5. Whether to also build Path B (RKOJ.exe mic-button)

Once those are picked, ship:
- `voice-recorder.py` (hotkey + audio capture)
- `transcribe.py` (audio -> text)
- `dispatch.py` (text -> Claude session)
- `~/.sinister-voice/config.json` (operator config)

## Install (when ready)

```powershell
# 1. Install deps
python -m pip install --user keyboard sounddevice openai

# 2. Set Whisper provider key (if Whisper API)
[Environment]::SetEnvironmentVariable('OPENAI_API_KEY','sk-...','User')

# 3. Enable on next session spawn
[Environment]::SetEnvironmentVariable('SINISTER_VOICE_ENABLED','1','User')
```

## Reference

- Spec: `_shared-memory/plans/voice-prompting-poc-2026-05-23/spec.md`
- Operator directive: 2026-05-23: *"i want to add voice promptiong to the system. and you analyze my voice recording and use that as a prompt"*
- Author: RKOJ-ELENO :: 2026-05-23
