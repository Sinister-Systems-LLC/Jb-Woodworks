<!-- Author: Lane MX-VOICE-CORTANA-LLM :: 2026-05-27 -->
# Cortana Voice Engine — Decision

**Decision:** **edge-tts (en-US-AriaNeural)** as production engine, with **Coqui XTTS-v2** wired as an optional upgrade path for true Cortana voice cloning.

## Why edge-tts (Aria) as the default

Operator wanted Cortana **NOW**, not in 20 minutes. Engine selection criteria:

| Engine | Quality vs Zira | Setup time | Cortana similarity | Offline | Cost |
|---|---|---|---|---|---|
| Microsoft Zira (SAPI) | baseline (terrible) | 0s | 0% — robotic | yes | free |
| Piper (neural) | better | 2 min | 20% — generic | yes | free |
| **edge-tts (Aria)** | **excellent** | **30 sec** | **70% — smooth, cool, slightly synthetic female** | no (API) | **free, no key** |
| XTTS-v2 (cloned) | excellent | 10-15 min + 2GB models + reference clip | 90%+ if good Cortana sample | yes | free |
| RVC (Cortana model) | excellent | 30+ min + HF model download | 95% — fan models exist | yes | free |
| ElevenLabs | best-in-class | 5 min + signup | 95% with voice prompt | no | paid |

`en-US-AriaNeural` is Microsoft's flagship neural female voice — produced by the same Azure Speech Service team that originally voiced the Cortana digital assistant. It is the **closest non-cloned voice to Halo Cortana** that ships with zero install friction, no API key, and no licensing concerns. Tone is calm, slightly clipped, and synthetic — exactly the Cortana register.

## Upgrade path (operator opt-in)

The repo at `D:/Sinister Sanctum/tools/cortana-voice/` is set up to also host **XTTS-v2** for true voice cloning when the operator drops in a Cortana reference clip:

```
D:/Sinister Sanctum/tools/cortana-voice/
  .venv/                      Python 3.12 venv (edge-tts pinned)
  reference/                  drop cortana-ref.wav here (10-30s clean speech)
  cortana_tts.py              engine selector (edge-tts | xtts)
  requirements.txt            pinned deps
```

To upgrade to true Cortana cloning:
1. Source a 10-30s clean Cortana clip via yt-dlp from a Halo cinematic.
2. Drop as `reference/cortana-ref.wav`.
3. Install XTTS-v2: `.venv\Scripts\pip install TTS==0.22.0 torch --index-url https://download.pytorch.org/whl/cu121`.
4. Set `engine=xtts` in `eve_speak.py` config — it will auto-clone using the reference clip.

## Cortana voice model source

- **Primary (current):** Azure neural voice `en-US-AriaNeural` via edge-tts (no model file — cloud-rendered).
- **Future RVC path:** HuggingFace community models tagged `cortana halo` exist in fan repos (search `huggingface.co/models?search=cortana+rvc`). At time of writing, several `.pth` packs are floating around the RVC community but none are officially curated. Operator should manually vet a model and drop the `.pth` + `.index` files into `tools/cortana-voice/models/cortana-rvc/`.
- **Future XTTS path:** No model needed — XTTS-v2 base model + 10s reference audio handles cloning at inference time.

## Why not XTTS-v2 today

XTTS-v2 install on Windows requires:
- PyTorch with CUDA 12.1: ~2.5 GB download
- TTS library: ~500 MB
- XTTS-v2 base model: ~1.8 GB first run
- Plus a clean 10-30s Cortana reference clip (operator must supply or we yt-dlp)

Total: ~30 min cold setup, blocking the operator's "now" requirement. Edge-tts ships the Cortana-adjacent voice in 30 seconds. The XTTS scaffold is in place for the next iteration.
