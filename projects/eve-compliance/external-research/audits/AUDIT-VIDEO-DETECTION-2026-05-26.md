# AUDIT — Video Moderation OSS Candidates (5 repos)

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: EVE Compliance · Spawned by: research sub-agent (operator directive 2026-05-26)
> Hardware target: RTX 4090, 24 GB VRAM, Python 3.12, Windows (no torch installed yet)
> Mission: select OSS to build `LetsText/backend/src/lib/video-moderation.ts` — adult-platform content scanning that ALLOWS adult nudity/sex but blocks CSAM (minors), gore/violence/strangling, self-harm, weapons-at-person, bestiality, non-consent, scat.

---

## TL;DR — recommended stack

**ENSEMBLE (P0 production path):**

1. **NudeNet** (per-frame NSFW body-part detection — coarse first pass, ONNX, no GPU required, batchable to ~50 fps on the 4090) — **ADOPT**
2. **mmaction2** (action recognition toolkit — fine-tune `SlowFast-R50` or `VideoMAE-V2` on a custom 8-class "violence/strangling/weapon-pointing/self-harm/bestiality/normal-sex/normal-nonsex/non-consent" head) — **ADOPT** as the training+inference framework
3. **VideoMAEv2** (ViT-giant pretrained backbone — best transfer learning starting point for the custom safety head trained inside mmaction2) — **ADOPT** as the backbone (weights only, not the training code)

**RESEARCH / OPTIONAL:**

4. **PySlowFast** (FAIR canonical SlowFast/X3D/MViT implementations — keep cloned for reference architectures + as fallback if mmaction2's SlowFast port misbehaves) — **ENSEMBLE** (reference only, do not productionize)
5. **InternVideo** (multimodal video-text foundation model — too heavy for per-upload inference; use the InternVideo2.5 8B model only OFFLINE for batch-labeling the bootstrap training set via zero-shot text prompts like "two people fighting violently") — **ENSEMBLE** (offline dataset labelling, not online inference)

**SKIP:** none of the 5 are skipped — but PySlowFast is "reference only" and InternVideo is "offline only", they don't both go into the live moderation request path.

---

## Frame sampling strategy (applies to all video repos)

Recommended pipeline for an N-second uploaded video:

1. **Fast pass:** decode at 1 fps → run NudeNet on every sampled frame (320n model, ONNX-CPU is ~30 ms/frame; on the 4090 batch-32 of 320×320 in <50 ms). Coarse NSFW class counts feed the audit log.
2. **Shot detection:** PySceneDetect (BSD-3, not in the 5 — add as dep) to chunk video into shots; for each shot pick the visually-central frame for the second pass.
3. **Action pass:** for each shot, sample 16 frames @ stride-2 (covers ~1 sec @ 30 fps source) → run the mmaction2-fine-tuned VideoMAEv2 ViT-B classifier (8 safety classes). Output: per-shot probability vector → aggregate to per-video verdict.
4. **Audio pass (P1):** whisper-large-v3 transcript of the audio track → run the existing `LetsText/backend/src/lib/content-moderation.ts` text moderation on the transcript to catch verbal self-harm / non-consent.

**VRAM budget on 4090:**
- NudeNet 320n ONNX: ~0.3 GB
- VideoMAEv2-ViT-B (16-frame clip, 224 px): ~3 GB inference (FP16: ~1.5 GB)
- whisper-large-v3: ~10 GB (or large-v3-turbo: ~6 GB)
- Total simultaneous: ~14 GB → comfortably fits with batch-1 video, leaves headroom for 2× concurrent video pipelines.

---

## 1. PySlowFast (facebookresearch/SlowFast) — REFERENCE / ENSEMBLE

| Field | Value |
|---|---|
| URL | https://github.com/facebookresearch/SlowFast |
| License | Apache-2.0 |
| Stars | 7.4k |
| Last commit | Repo activity tapered after MViTv2 work (~2022-2023); still gets occasional patches. Not the freshest, but stable. |
| Maintainer | FAIR / Meta (Haoqi Fan, Yanghao Li, Christoph Feichtenhofer) |
| Cloned to | `D:/Sinister Sanctum/projects/eve-compliance/external-research/repos/slowfast/` (64 MB) |

**What it detects (out of the box):**
- Action classification on Kinetics-400/600/700, Charades, AVA
- Spatio-temporal action detection (AVA — 80 atomic actions including "fight", "hit", "carry/hold-a-weapon", "fall-down")
- Architectures: SlowFast (dual-pathway 3D ResNet), Slow, I3D, X3D, MViTv1/v2, Rev-ViT, MaskFeat

**Model architecture:**
- SlowFast = two 3D-CNN pathways: slow (low frame rate, semantic) + fast (high frame rate, motion); lateral connections fuse them.
- AVA model is **the most relevant** for safety: it does person-detection + per-person action classification — so it can localize "this person is striking the other person".

**VRAM + per-second cost (4090 estimate):**
- SlowFast-R50 (8×8, 224 px, 32 frames): ~4 GB inference, ~0.5 s per 64-frame clip → ~2 sec of video per inference call.
- MViTv2-B-32×3 (Kinetics-400): ~6 GB, ~0.7 s per clip.

**Integration sketch:**
- NOT recommended as the primary trainer — code is heavyweight, requires building Detectron2 + fvcore, has hard PySlowFast-specific config system (`fvcore.config`).
- USE as: (a) drop-in reference for the SlowFast architecture when debugging mmaction2's port; (b) source of the AVA inference recipe (`tools/visualize_video.py` + `demo_net.py`) for reproducing the "per-person action" approach if mmaction2's AVA support is insufficient.
- For `LetsText/backend/src/lib/video-moderation.ts`: shell out to a Python subprocess that loads the mmaction2 model — do NOT vendor PySlowFast into the prod path.

**Verdict: ENSEMBLE (reference only)** — Apache-2.0, the canonical SlowFast implementation; we keep it cloned to crib AVA-detection code for the "person-strikes-person" + "person-holds-weapon" use cases, but production runs through mmaction2.

---

## 2. MMAction2 (open-mmlab/mmaction2) — ADOPT (primary framework)

| Field | Value |
|---|---|
| URL | https://github.com/open-mmlab/mmaction2 |
| License | Apache-2.0 |
| Stars | 5.0k (per Linux Foundation LFX: ~4.9k; project active 284 of last 365 days) |
| Last release | v1.2.0 (Oct 12 2023); 2063 commits on main; per LFX has 0 active contributors in last quarter → MAINTENANCE RISK NOTE |
| Maintainer | OpenMMLab consortium (Shanghai AI Lab + SenseTime + community) |
| Cloned to | `D:/Sinister Sanctum/projects/eve-compliance/external-research/repos/mmaction2/` (29 MB shallow) |

**What it detects (out of the box):**
- 25+ action recognition architectures including: C3D, I3D, SlowFast, R(2+1)D, TSM, TimeSformer, ActionCLIP, VideoSwin, **VideoMAE V1+V2**, MViT V2, UniFormer V1/V2.
- Spatio-temporal action detection: ACRN, SlowOnly+Fast-RCNN, SlowFast+Fast-RCNN, LFB.
- Skeleton-based action: PoseC3D, ST-GCN, CTRGCN — useful for "fighting" / "strangling" detection where body pose is the strongest signal.
- Datasets supported: Kinetics-400/600/700/710, AVA, AVA-Kinetics, UCF101, HMDB51, FineGYM, MultiSports.

**Model architecture (recommended pick for our use):**
- VideoMAE-V2 ViT-B config: `configs/recognition/videomaev2/` — 16-frame 224 px input, pre-trained on K710, fine-tunable on a custom 8-class safety dataset with ~5k-10k labelled videos per class.
- PoseC3D fallback if pure-visual is too noisy: extracts skeletons via MMPose then runs 3D-CNN on the pose heatmap — proven robust for violence/fighting on NTU-RGB+D.

**VRAM + per-second cost (4090 estimate):**
- VideoMAE-V2 ViT-B inference: ~3 GB FP32 / ~1.5 GB FP16; ~80 ms per 16-frame clip → ~13 clips/sec → covers ~25 sec of video/sec at 1-shot-per-1-sec sampling.
- VideoMAE-V2 ViT-L: ~10 GB, ~150 ms/clip → fits but tighter.

**Integration sketch:**
- New file: `LetsText/backend/src/lib/video-moderation.ts` exposes `scanVideo(path: string, agencyId: string): Promise<VideoScanResult>`.
- Inside, spawn a Python worker: `tools/video-moderation/scan.py` that boots mmaction2 once (warm), reads video chunks via decord, runs the safety classifier per shot, returns JSON.
- Schema additions to Prisma `ContentScan`: add `videoMs`, `shotCount`, `perShotVerdicts JSON`, `worstClassScore`, `worstClassLabel`. Reuse the existing strike + cooldown + admin-review queue — moderation verdicts route through the SAME compliance panel that today handles images.
- Provider abstraction: same shape as `scanImage()` so the strike-engine doesn't care if the source was image or video.

**Verdict: ADOPT** — Apache-2.0, comprehensive model zoo, has both VideoMAE-V2 + SlowFast + PoseC3D under one config system. Maintenance-risk caveat (0 active contributors last quarter per LFX) means we may need to vendor key files. Acceptable for a v1; revisit annually.

---

## 3. VideoMAEv2 (OpenGVLab/VideoMAEv2) — ADOPT (backbone weights)

| Field | Value |
|---|---|
| URL | https://github.com/OpenGVLab/VideoMAEv2 |
| License | MIT |
| Stars | 792 |
| Last commit | 2024-09-19 (checkpoints migrated to HuggingFace); 21 commits on master |
| Maintainer | OpenGVLab (Shanghai AI Lab) — Limin Wang et al. |
| Cloned to | `D:/Sinister Sanctum/projects/eve-compliance/external-research/repos/videomaev2/` (2.5 MB shallow) |
| Note | Original MCG-NJU/VideoMAE V1 is **CC-BY-NC 4.0** (NON-COMMERCIAL — do not use for the platform). V2 is clean MIT. |

**What it detects (out of the box):**
- VideoMAE-V2 is a **pre-trained backbone**, not a classifier. The checkpoint provides ViT-S/B/L/H/g (giant 1B param) weights trained via masked autoencoding on UnlabeledHybrid (1.35M unlabelled videos).
- Released distilled & fine-tuned heads on Kinetics-400/600/710, Something-Something-V2, AVA, ActivityNet — but those are generic action classes, NOT safety classes.
- The win: ViT-g distilled to ViT-B retains 86.6% K400 top-1 → strongest currently-published transfer-learning starting point for a custom safety head.

**Model architecture:**
- Plain ViT operating on tube-shaped patches (16-frame × 16-px × 16-px tubes from 224×224 video).
- Dual masking (encoder masks 75-90% of tubes, decoder masks the other set) — efficient pretraining.
- ViT-B is 86M params; ViT-g is 1B params (only run g on the 4090 with FP16 + activation-checkpointing).

**VRAM + per-second cost (4090 estimate):**
- ViT-B inference (16×224×224): ~3 GB, ~80 ms/clip.
- ViT-L: ~6 GB, ~140 ms/clip.
- ViT-g (FP16): ~14 GB, ~400 ms/clip → too heavy for live moderation; use for offline labeling only.

**Integration sketch:**
- Do NOT vendor this training codebase into production. Use mmaction2's `configs/recognition/videomaev2/` configs which already wrap the same backbone.
- Download the ViT-B-K710-distilled weights from HuggingFace `OpenGVLab/VideoMAE2` → fine-tune the classifier head on our custom safety dataset (mmaction2 trainer).
- Keep this repo cloned for: (a) the original pretraining recipe if we ever want to do self-supervised pretrain on a corpus of platform-uploaded videos (privacy-aware — would need legal sign-off); (b) the ViT-g feature-extraction recipe under `docs/TAD.md` for offline dataset labeling.

**Verdict: ADOPT** — MIT license, strongest backbone, HuggingFace-hosted weights, integrates cleanly through mmaction2. **Use weights, skip training code.**

---

## 4. InternVideo (OpenGVLab/InternVideo) — ENSEMBLE (offline labeling only)

| Field | Value |
|---|---|
| URL | https://github.com/OpenGVLab/InternVideo |
| License | Apache-2.0 |
| Stars | 2.3k |
| Last commit | 2025-12-01 (InternVideo-Next released); 2025-01 (InternVideo2.5); 2025-02 (InternVideo2-Stage2-6B); 2025-05-18 (InternVideo-Next CVPR2026 acceptance + pretraining code) → **most actively maintained of the 5** |
| Maintainer | OpenGVLab — Limin Wang et al. (same lab as VideoMAEv2) |
| Cloned to | `D:/Sinister Sanctum/projects/eve-compliance/external-research/repos/internvideo/` (35 MB shallow, monorepo with InternVideo1/InternVideo2/InternVideo2.5/InternVideo-Next/Data subdirs) |

**What it detects (out of the box):**
- InternVideo2 (6B/8B) — multimodal video-text foundation model; zero-shot video classification via text prompts ("a person being strangled", "blood and gore", "child in sexual context").
- InternVideo2.5 (Jan 2025) — video MLLM with long/rich context; can answer free-form questions about video content.
- InternVideo-Next (Dec 2025, CVPR2026) — newest backbone, no video-text supervision needed.

**Model architecture:**
- Dual-encoder (video ViT + text BERT/InternVL) with CLIP-style contrastive + video-text-matching training.
- Audio branch (BEATs backbone) is available on the multi-modality variant → useful for our P1 audio-moderation step.
- InternVideo2-Stage3-8B-HD is the strongest publicly-available zero-shot video classifier.

**VRAM + per-second cost (4090 estimate):**
- InternVideo2-1B: ~6 GB FP16, ~300 ms/clip → could run live but eats the 4090.
- InternVideo2-6B: ~14 GB FP16 — fits on the 4090 but uses 60% of VRAM; not suitable for per-upload live moderation.
- InternVideo2-8B-HD: ~22 GB FP16 — barely fits; offline-only.
- InternVideo-Next-Large: not yet benchmarked, expected similar to InternVideo2-L.

**Integration sketch:**
- NOT in the live moderation request path. The 4090 budget cannot support both this AND mmaction2 AND whisper at request time.
- USE for offline batch labeling of the bootstrap training set: feed candidate-flag images/videos through InternVideo2-6B zero-shot with text prompts → auto-label → human-verify a sample → train the lightweight mmaction2/VideoMAEv2 head on the result.
- USE for hard-case admin escalation: when the production model gives a low-confidence verdict, queue the clip for an offline InternVideo2-8B-HD pass before showing to a human reviewer — burns ~3 sec of GPU but reduces reviewer load.
- Dependency cost: requires FlashAttention2 with custom CUDA extensions (`fused_dense_lib`, `layer_norm`), DeepSpeed, NVIDIA apex — non-trivial Windows install; likely needs WSL2 or a Linux box for the offline batch worker. Document as deferred infra.

**Verdict: ENSEMBLE (offline only)** — Apache-2.0, most-active project, but architecture is too heavy for live moderation. Offline use is a force-multiplier for labeling productivity.

---

## 5. NudeNet (notAI-tech/NudeNet) — ADOPT (per-frame NSFW classifier)

| Field | Value |
|---|---|
| URL | https://github.com/notAI-tech/NudeNet |
| License | MIT (LICENSE + LICENSE.md both present in repo) |
| Stars | ~2k (community estimates; pypi shows 200k+ downloads/month) |
| Last release | v3.4.2 — 2024-07-03 |
| Maintainer | Praneeth Bedapudi (`@bedapudi6788`) — note in README: "looking for contributors / maintainers" → MAINTENANCE RISK NOTE |
| Cloned to | `D:/Sinister Sanctum/projects/eve-compliance/external-research/repos/nudenet/` (168 MB — includes bundled ONNX models + in-browser demo + Docker recipe) |

**What it detects (out of the box):**
- 18 body-part classes with bounding boxes: FEMALE_GENITALIA_EXPOSED, MALE_GENITALIA_EXPOSED, FEMALE_BREAST_EXPOSED, MALE_BREAST_EXPOSED, BUTTOCKS_EXPOSED, ANUS_EXPOSED, BELLY_EXPOSED, FEET_EXPOSED, ARMPITS_EXPOSED + covered variants + FACE_FEMALE/FACE_MALE.
- Does NOT detect: violence, weapons, age (no minor-detector — CRITICAL GAP for CSAM detection; CSAM must come from a separate hash-match service like PhotoDNA + classifier).

**Model architecture:**
- 320n: YOLOv8n trained at 320×320 — ~7 MB ONNX, ~30 ms/image CPU, ~5 ms/image GPU.
- 640m: YOLOv8m trained at 640×640 — ~25 MB ONNX, ~80 ms/image CPU, ~15 ms/image GPU. Higher accuracy.

**VRAM + per-second cost (4090 estimate):**
- 320n on CPU: 30 fps single-thread.
- 640m on GPU batch-32: ~50 ms/batch → ~640 frames/sec → covers a 10-min video at 1 fps in <1 sec.

**Integration sketch:**
- Already MIT-licensed and ONNX-ready — drop in as the FIRST PASS of the video pipeline.
- New file: `tools/video-moderation/nudenet_pass.py` — loads the 640m ONNX once, takes a list of frame ndarrays, returns per-frame detections.
- Verdict aggregation: a video is "explicit" if >X% of sampled frames have ≥1 EXPOSED class with confidence >0.7 (X tunable per-agency).
- Strike triggers: separate "explicit-content-but-allowed" log row vs. the "violent-or-illegal-content" row that fires from the mmaction2 classifier. The strike-engine should already differentiate verdict reasons (per `image-moderation.ts` schema).
- Frontend cooldown: same `cooldownUntil` 403 path as image upload.

**Verdict: ADOPT** — MIT, mature, production-deployed across many adult platforms, has bundled ONNX so zero training required. Maintenance risk (maintainer seeking new owner) is mitigated by the fact that we'd vendor v3.4.2 weights + a thin wrapper; we don't depend on future releases.

---

## Open follow-ups (for the EVE Compliance lane queue)

1. **PhotoDNA / NeuralHash for CSAM hash matching** — NEITHER of the 5 audited repos solves CSAM detection. CSAM is a HASH-MATCH problem (NCMEC PhotoDNA database) + an age-classifier problem (separate model — most are gated for child-safety reasons; e.g. Thorn's Safer is not OSS). Add as P0 of the next research turn: `meta/threatexchange/vpdq` (perceptual video hashing) — note: I saw `threatexchange/` already exists in the repos dir from the sibling image-research agent; verify VPDQ video hash support there.
2. **PySceneDetect dependency** (BSD-3) for shot boundary detection — add to `requirements.txt` of the new Python video-moderation worker.
3. **Whisper-large-v3-turbo dependency** for audio transcript pass (P1).
4. **Custom safety dataset construction** — 8 classes × ~5k labelled clips each. Bootstrap via (a) public datasets — HockeyFight, RWF-2000, UCF-Crime; (b) InternVideo2-zero-shot pre-labeling; (c) admin queue feedback loop.
5. **Provider abstraction in `video-moderation.ts`** — mirror the image-moderation pattern: pluggable `provider: 'mmaction2-local' | 'hive' | 'sightengine' | 'aws-rekognition-video'` so we can swap to a managed service if self-hosting becomes burdensome.
6. **Real-time vs batch decision** — video uploads should be moderated ASYNC (background job posts the verdict back to the conversation 5-30 sec after upload completes) — do NOT block the HTTP upload response on a 30-sec GPU pipeline. The existing async-job infra in `LetsText/backend/src/lib/jobs/` (verify path) needs to handle a new `video-moderation` job kind.

---

## Cross-references

- Operator directive (verbatim 2026-05-26): *"search github for image detection and video detection solutions. download all of them. like 10 [5 image, 5 video]. then deeply review and audit"* — this audit covers the **video** half; the image half is owned by a sibling sub-agent (repos `imagehash`, `nsfw_model`, `opennsfw2`, `private-detector`, `threatexchange` are already in the same repos dir).
- Composes with: `LetsText/docs/DEMO-IMAGE-MODERATION.md` runbook + `LetsText/backend/src/lib/image-moderation.ts` (existing image pipeline; the video pipeline is the parallel-track addition).
- Lane mission (verbatim 2026-05-24): *"The main piece of the compliance system is my AI EVE image scan ... Once flagged the image will go to compliance panel"* — extend to video with the SAME compliance-panel + good-catch/bad-catch + training-feedback loop. No new admin UX should be needed; the panel renders the worst-shot frame as a thumbnail + lets the reviewer scrub the video.
