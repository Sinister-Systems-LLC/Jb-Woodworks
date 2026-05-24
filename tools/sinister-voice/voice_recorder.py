"""sinister-voice :: push-to-record hotkey daemon (Path A POC stub).

Author: RKOJ-ELENO :: 2026-05-24
Spec: _shared-memory/plans/voice-prompting-poc-2026-05-23/spec.md
Status: STUB — operator must opt-in via SINISTER_VOICE_ENABLED=1.

Safe by default: does NOT autostart. Does NOT record without explicit consent.
Does NOT install hotkey hook without operator config.

Run modes:
    python voice_recorder.py --selftest   # confirm imports, hotkey lib status
    python voice_recorder.py --record-once # 5-sec test record (operator-explicit)
    python voice_recorder.py --daemon     # hotkey loop (NEEDS env var SET)

Dependencies (operator-installed when ready):
    pip install --user keyboard sounddevice soundfile

If keyboard lib not installed -> daemon won't start; selftest reports gap.
If sounddevice not installed -> record-once / daemon both fail-fast with message.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path


SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
VOICE_INBOX = SANCTUM_ROOT / "_shared-memory" / "voice-inbox"
ENABLED = os.environ.get("SINISTER_VOICE_ENABLED", "0") == "1"
HOTKEY = os.environ.get("SINISTER_VOICE_HOTKEY", "win+alt+v")


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())


def selftest() -> int:
    """Probe deps + config without recording. Exit 0 always."""
    print("=== sinister-voice selftest ===")
    print(f"sanctum_root: {SANCTUM_ROOT}")
    print(f"voice_inbox:  {VOICE_INBOX}  ({'exists' if VOICE_INBOX.exists() else 'will be created on first record'})")
    print(f"enabled (SINISTER_VOICE_ENABLED): {ENABLED}")
    print(f"hotkey  (SINISTER_VOICE_HOTKEY):  {HOTKEY}")
    print()
    print("Dep status:")
    for mod_name in ("keyboard", "sounddevice", "soundfile"):
        try:
            __import__(mod_name)
            print(f"  [OK]   {mod_name}")
        except ImportError:
            print(f"  [MISS] {mod_name}  -> pip install --user {mod_name}")
    print()
    return 0


def record_once(duration_sec: float = 5.0) -> int:
    """Operator-explicit one-shot record. Writes WAV to voice_inbox/."""
    try:
        import sounddevice as sd
        import soundfile as sf
    except ImportError as exc:
        print(f"[FAIL] missing dep: {exc.name}. Run: pip install --user sounddevice soundfile", file=sys.stderr)
        return 2
    VOICE_INBOX.mkdir(parents=True, exist_ok=True)
    out_path = VOICE_INBOX / f"recording-{_ts()}.wav"
    print(f"[recording {duration_sec}s -> {out_path}] ...")
    samplerate = 16000  # Whisper-friendly
    audio = sd.rec(int(duration_sec * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    sf.write(str(out_path), audio, samplerate)
    print(f"[OK] wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


def daemon() -> int:
    """Hotkey-bound push-to-record loop. Operator must explicitly enable."""
    if not ENABLED:
        print("[FAIL] SINISTER_VOICE_ENABLED is not set to 1. Refusing to start daemon.", file=sys.stderr)
        print("  To enable: [Environment]::SetEnvironmentVariable('SINISTER_VOICE_ENABLED','1','User') + restart shell", file=sys.stderr)
        return 2
    try:
        import keyboard
        import sounddevice as sd
        import soundfile as sf
    except ImportError as exc:
        print(f"[FAIL] missing dep: {exc.name}. Run: pip install --user keyboard sounddevice soundfile", file=sys.stderr)
        return 2
    VOICE_INBOX.mkdir(parents=True, exist_ok=True)
    samplerate = 16000
    recording = []
    is_recording = [False]
    stream_ref = [None]

    def on_press(_e):
        if is_recording[0]:
            return
        is_recording[0] = True
        recording.clear()
        print(f"[REC] hotkey down -> recording...")

        def _callback(indata, frames, t, status):
            if is_recording[0]:
                recording.append(indata.copy())

        stream_ref[0] = sd.InputStream(samplerate=samplerate, channels=1, dtype="int16", callback=_callback)
        stream_ref[0].start()

    def on_release(_e):
        if not is_recording[0]:
            return
        is_recording[0] = False
        if stream_ref[0]:
            try:
                stream_ref[0].stop()
                stream_ref[0].close()
            except Exception:
                pass
        if recording:
            import numpy as np
            audio = np.concatenate(recording, axis=0)
            out_path = VOICE_INBOX / f"recording-{_ts()}.wav"
            sf.write(str(out_path), audio, samplerate)
            print(f"[REC] released -> wrote {out_path}")

    keyboard.on_press_key(HOTKEY.split("+")[-1], on_press, suppress=False)
    keyboard.on_release_key(HOTKEY.split("+")[-1], on_release, suppress=False)
    print(f"[daemon] listening on hotkey {HOTKEY}. Ctrl+C to exit.")
    print(f"[daemon] writes to {VOICE_INBOX}")
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("[daemon] exit")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv or argv[0] in ("--selftest", "-t"):
        return selftest()
    if argv[0] in ("--record-once", "-r"):
        return record_once()
    if argv[0] in ("--daemon", "-d"):
        return daemon()
    if argv[0] in ("--help", "-h", "/?"):
        print(__doc__)
        return 0
    print(f"[FAIL] unknown mode: {argv[0]}. Try --selftest / --record-once / --daemon / --help", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
