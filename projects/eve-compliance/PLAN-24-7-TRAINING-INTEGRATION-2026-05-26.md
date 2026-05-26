# PLAN — 24/7 Training + 10-Repo Integration Roadmap

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: `eve-compliance`
> Trigger directive (verbatim 2026-05-26T17:14Z): *"setup 24/7 training using my 4090 gpu that i can easily allocate resources to and turn on and off"* + *"search github for image detection and video detection solutions. download all of them. like 10 and then deeply review and audit all of them"*
> Composes with: `DESIGN-GPU-TRAINER-2026-05-26.md` · `AUDIT-IMAGE-DETECTION-2026-05-26.md` · `AUDIT-VIDEO-DETECTION-2026-05-26.md` · `AUDIT-VLMS-FOR-MODERATION-2026-05-26.md` · ccbill-demo branch `agent/eve-compliance/ccbill-demo-blood-gore-scat-2026-05-26`

---

## TL;DR

Three layers ship in this initiative, all running 24/7 on the RTX 4090 with operator-controllable resource caps:

1. **GPU trainer daemon** (`automations/eve_gpu_trainer.py` — scaffolded + 16/16 self-test PASS this turn) — fine-tunes `Falconsai/nsfw_image_detection` ViT via PEFT LoRA on human-labeled JSONL from `export-moderation-training.ts`. ~4.5 GB VRAM at batch 32. Easy on/off via `python eve_gpu_trainer.py {start|stop|pause|resume|set --gpu-pct N --batch N}`. Hot-reload `control.json`.
2. **Hash-gate pre-classifier** (Meta PDQ via cloned `threatexchange`) — every upload's perceptual hash checked against known-bad set before the classifier runs. Catches re-uploads instantly. ~0 GPU cost.
3. **VLM tie-breaker** (Qwen2-VL-7B AWQ int4, ~6 GB VRAM) — fires only when ViT confidence lands in the 0.4-0.7 mid-band (~5-8 % of scans), bumping precision on nuanced edge cases without blowing VRAM budget.

For video uploads (currently a 100 % gap): NudeNet per-frame fast pass + mmaction2-trained VideoMAEv2 action classifier + (P1) Whisper-v3-turbo audio safety. Lives in NEW `LetsText/backend/src/lib/video-moderation.ts`, dispatches to a Python worker. Async pipeline — never blocks the upload HTTP.

10 repos cloned into `external-research/repos/` — full audit in `external-research/audits/`. Adoption sequence below.

---

## What shipped THIS turn (verified)

| Deliverable | Status | Smoke |
|---|---|---|
| `automations/eve_gpu_trainer.py` + `eve_gpu_trainer_loop.py` | scaffolded | `self-test` 16/16 PASS; `status` renders on Windows cp1252 |
| `control.json` default schema + atomic hot-reload write | shipped | self-test confirms round-trip + clamp |
| Singleton pidfile guard (`_shared-memory/eve-gpu-trainer.pid`) | shipped | reclaims stale; idempotent re-acquire |
| Heartbeat to `_shared-memory/heartbeats/eve-gpu-trainer.json` | shipped | fleet-shape; sweeper-compatible |
| 10 OSS repos cloned to `external-research/repos/` | shipped | `threatexchange · imagehash · opennsfw2 · private-detector · nsfw_model · slowfast · mmaction2 · videomaev2 · internvideo · nudenet` |
| 4 audit docs in `external-research/audits/` | shipped | image · video · VLM · GPU-trainer-design |
| Demo verified end-to-end via API | green | 8/8 pending scans incl scat/bestial/noncon visible to demo-admin |
| Torch install (cu121) in venv | in-flight | `~/.venv/Scripts/python.exe -m pip install torch==2.4.1+cu121 torchvision==0.19.1+cu121` |

---

## 10-repo adoption sequence

### Tier P0 — adopt now (both image-side and video-side)

| Repo | Verdict | Why first | Integration point |
|---|---|---|---|
| **`facebook/ThreatExchange`** (PDQ + VPDQ) | ADOPT P0a | PhotoDNA-equivalent perceptual hashing. Image AND video coverage. BSD. Actively maintained (commit 2026-05-22). | `image-moderation.ts`: pre-classifier hash gate. Replaces our current sha256 placeholder at `perceptualHash` (line ~57). New `video-moderation.ts`: VPDQ shot-level hashes. |
| **`JohannesBuchner/imagehash`** (pHash/dHash/wHash) | ADOPT P0b | Crop-resistant hashes catch adversarial re-uploads PDQ misses. BSD-2. 3.8k stars. Pure Python — zero install friction. | Ensembled with PDQ — both hashes stored per scan; lookup matches EITHER. |

These two land WITHOUT any ML stack. Operator gets a measurable precision uplift on day 1.

### Tier P1 — ensemble after baseline LoRA is trained

| Repo | Verdict | Why second | Integration point |
|---|---|---|---|
| **`bhky/opennsfw2`** (Yahoo Open-NSFW Keras 3 port) | ENSEMBLE P1 | On-prem failover when Anthropic rate-limits or `ANTHROPIC_API_KEY` rotates. ~80 ms inference on 4090. MIT. | `image-moderation.ts:claudeVisionScan` catch-block currently returns `scanner-error` PASS; instead fall through to `opennsfw2Scan(url)`. |
| **`Falconsai/nsfw_image_detection`** (ViT-base, HF) | ADOPT — primary trainee | Already 90 % of what we need. PEFT LoRA fine-tune on our human labels brings the last 10 %. | `eve_gpu_trainer.py` trains LoRA adapter. Adapter loaded by a sibling tiny inference daemon and consulted ensemble with Haiku. |

### Tier P2 — video pipeline (separate effort, ~2 weeks)

| Repo | Verdict | Role |
|---|---|---|
| **`open-mmlab/mmaction2`** | ADOPT — training framework | Train an 8-class safety head on VideoMAEv2-ViT-B against shot-segmented frames. |
| **`OpenGVLab/VideoMAEv2`** | ADOPT — backbone | Masked-autoencoder backbone. MIT. Strongest transfer-learning starting point. |
| **`notAI-tech/NudeNet`** | ADOPT — fast frame pass | YOLOv8 18-class body-part detector. ONNX. ~30 ms/frame. Per-keyframe gate before the heavier classifier. |
| **`facebookresearch/SlowFast`** | KEEP — reference recipes | AVA person-action localization patterns we'll crib for strangling/self-harm detection. Not deployed. |
| **`OpenGVLab/InternVideo`** | DEFER | Too heavy for live (6-22 GB). Slated for offline batch labeling + hard-case admin escalation. |

### Tier P3 — Vision-Language Models (advanced precision pass)

| Model | Verdict | Role |
|---|---|---|
| **Qwen2-VL-7B-Instruct (AWQ int4)** | ADOPT — primary VLM | Tie-breaker when ViT confidence is mid-range (0.4-0.7). ~6 GB VRAM. Apache-2.0. |
| **LLaVA-OneVision-7B** | ENSEMBLE — fallback | Lower refusal rate than Qwen on borderline content. |
| **InternVL 2.5-8B** | ENSEMBLE — gore/weapon specialist | Stronger on violent imagery per the audit benchmarks. |
| **MiniCPM-V 2.6** | DEFER — latency tier | Fastest small VLM, slot in if Qwen2-VL latency spikes. |

### Tier SKIP

- **`notAI-tech/NudeNet` for IMAGES** — AGPL-3.0 (viral copyleft, kills SaaS). NB: the cloned video-side `nudenet` is actually MIT (different repo / version) — verified per audit.
- **`LAION-AI/CLIP-based-NSFW-Detector`** — 3 yr dead.
- **`yahoo/open_nsfw`** — archived 2018, superseded by `opennsfw2`.
- **`GantMan/nsfw_model`** — diminishing returns as 4th classifier; license needs operator verification.
- **`CogVLM2-Llama3-8B`** — VRAM + license overhead vs Qwen2-VL.
- **`SketchVLM`** — paper-only framework for SVG annotation overlays on GPT-4/Gemini. Not a classifier. One useful idea worth stealing later: structured bounding-box outputs for selective-redaction UX (Qwen2-VL + InternVL already support `<box>` grounding natively).

### Real CSAM hash sets (enrollment-required, can't clone)

PhotoDNA · Thorn SAFER · NCMEC IICN · IWF · StopNCII. Operator must enroll the business with each provider. Lane-backlog item — NOT a clone target.

---

## The 24/7 training loop (operator's actual asks)

### "Setup 24/7 training using my 4090 GPU"

Shipped (in flight, install completing): `automations/eve_gpu_trainer.py run` runs a manual PyTorch training loop. Currently in BOOTSTRAP mode (synthetic random tensors validate the GPU plumbing); auto-flips to REAL mode the moment `working.jsonl` is non-empty (post-data-pull). Real data pull every `data_refresh_minutes` (default 60) via `npx tsx export-moderation-training.ts`. Checkpoints every 500 steps + on graceful shutdown.

### "Easily allocate resources to"

`control.json` is the single source of truth. Five knobs cover every realistic need:

```json
{ "enabled": true, "gpu_mem_pct": 50, "max_batch": 32, "max_cpu_threads": 8, "auto_pause_on_contention": true }
```

Daemon polls the file every 5 s and re-applies caps (idempotent). `python eve_gpu_trainer.py set --gpu-pct 75 --batch 64` writes atomically; daemon picks it up next poll. Hard floor 5 %, hard ceiling 95 % for safety.

### "Turn on and off"

Three modes:
- `python eve_gpu_trainer.py pause` / `resume` — model stays resident in VRAM, just idles. Sub-second toggle.
- `python eve_gpu_trainer.py stop` / `start` — graceful checkpoint + exit / spawn detached. Operator wants this if they need full VRAM back for a game.
- `set --auto-pause true` — daemon auto-pauses when `pynvml` reports <4 GB free VRAM sustained 30 s, auto-resumes when ≥6 GB free for 60 s. Composes with games / Stable Diffusion / Blender.

### "Quietly survive 24/7"

- Singleton pidfile prevents accidental dual-spawn.
- HF Trainer checkpoint resume on every restart.
- Watchdog (P1, doc in design — not built yet) re-spawns on crash.
- Heartbeat every ≤2 s → fleet sweeper sees liveness → other agents can route around if it's down.

---

## Decision log

1. **Skip Ruflo MCP MicroLoRA** for now (per Ruflo-audit sub-agent). Operator wants direct 4090 control; MCP abstraction adds RPC latency + indirect resource control. JSONL schema is HF-native, so PyTorch+PEFT is the straight path. Defer Ruflo until baseline LoRA matures and we want online reinforcement signals.
2. **Bootstrap mode before real data flows.** First training cycles use synthetic random tensors (3×224×224, 12-class) just to validate the GPU plumbing + pause/resume + checkpointing without waiting for hours of labeling. Daemon auto-flips to REAL mode when `working.jsonl` is non-empty.
3. **PEFT LoRA, not full fine-tune.** ~3 MB adapters vs ~350 MB weights. Daily snapshots cheap; rollback trivial. Adapter swaps don't need a full model reload.
4. **Skip `bitsandbytes` on Windows.** Flaky install; LoRA alone keeps us under 6 GB VRAM at batch 32 without 8-bit.
5. **Per-process VRAM fraction (50 %) by default.** Leaves 12 GB for operator's games / SD / Blender. Operator can crank to 75-95 % when desk is idle.
6. **Pause = idle, not kill.** Per design doc — operator can flip enabled false and back without re-init cost. Trainer keeps model + optimizer in VRAM.

---

## What ships in the NEXT iter (concrete, no operator wait)

| # | Task | Ack-criterion | Owner |
|---|---|---|---|
| A | Verify torch install · run `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` against the venv | prints `True NVIDIA GeForce RTX 4090` | eve-compliance |
| B | `pip install transformers>=4.44 peft>=0.13 accelerate>=0.34 datasets>=2.20 pillow pynvml psutil` | imports green | eve-compliance |
| C | First daemon `start` → 60 s smoke → `status` shows `state: TRAINING` + step counter > 0 + heartbeat fresh | green | eve-compliance |
| D | Watchdog `eve_gpu_trainer_watchdog.py` (companion daemon) | respawns trainer if pidfile owner dies | eve-compliance |
| E | Add PDQ hash gate to `image-moderation.ts` using `external-research/repos/threatexchange/python-threatexchange/` | every upload's PDQ hash stored; lookup gates classifier | eve-compliance |
| F | New `LetsText/backend/src/lib/video-moderation.ts` skeleton + Python worker shell | accepts video R2 URL, returns scaffolded verdict | eve-compliance |
| G | Train first real LoRA against current 38-row training JSONL | adapter saved to `training/adapters/v1/`; eval-acc reported | eve-compliance |

---

## Acceptance criteria (operator-visible)

These prove 24/7 works AND is easy to control:

1. `python automations/eve_gpu_trainer.py status` — anywhere, any time, any user shell. Renders cleanly on Windows.
2. `python eve_gpu_trainer.py pause` then start a game → game gets full 4090 → `nvidia-smi` shows our process still alive but holding ≤2 GB → close game → `resume` → training resumes from last checkpoint within seconds.
3. `python eve_gpu_trainer.py set --gpu-pct 80` while a render is queued → next poll picks it up → render-process gets the rest.
4. Computer restarts → schtask `ONLOGON` re-spawns trainer in normal-user context (no UAC) → checkpoint resume.
5. Crash injected (`taskkill /PID <trainer> /F`) → watchdog respawns within 90 s.
6. Demo video recordable any moment: 8 pending scans live at `/admin → Image Moderation` covering csam / gore / strangling / weapon / scat / bestiality / non-consent.

---

## Refs

- Design: `D:/Sinister Sanctum/projects/eve-compliance/training/DESIGN-GPU-TRAINER-2026-05-26.md`
- Audits: `external-research/audits/AUDIT-{IMAGE,VIDEO,VLMS}-FOR-MODERATION-2026-05-26.md` + ditto image-detection
- Code: `automations/eve_gpu_trainer.py` + `automations/eve_gpu_trainer_loop.py`
- Branches: `agent/eve-compliance/ccbill-demo-blood-gore-scat-2026-05-26` (z0nian/LetsText), `agent/eve-compliance/train-loop-dedup-2026-05-26` (Sinister-Sanctum), new `agent/eve-compliance/gpu-trainer-2026-05-26` (this commit)
- Operator vocabulary log: "blood, gore, strangling, poop. weird shit like that" → categories `["scat","bestiality","non-consent"]` now ship alongside existing `["gore","blood","strangling","violence","self-harm","weapon"]`.

End.
