# AUDIT — Open-Weight VLMs for EVE Compliance Image Moderation

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: `eve-compliance` · Sibling: `AUDIT-IMAGE-DETECTION-2026-05-26.md`
> Pointer: operator referenced `sketchvlm.github.io` "and things like it" — VLM class
> Hardware target: single RTX 4090 (24 GB VRAM) · Categories: CSAM, gore, strangling/violence, self-harm, weapon-at-person, bestiality, non-consent, scat (adult nudity/sex is ALLOWED)

---

## Candidate matrix (5 open-weight VLMs)

| # | Model | HF id | License | VRAM fp16 / int4 | Latency / img (4090) | Strengths | Weaknesses | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen2-VL-7B-Instruct** | `Qwen/Qwen2-VL-7B-Instruct` | Apache-2.0 (commercial-OK) | ~17 GB / ~6 GB (AWQ-int4) | ~1.5-2.5 s | Best-in-class OCR + scene reasoning; strong at nuanced consent/violence prompts; dynamic-resolution input | Will refuse explicit-nudity prompts on default safety RLHF; needs careful system-prompt jailbreak for adult-allowed surface | **ADOPT (primary VLM)** |
| 2 | **LLaVA-OneVision-7B** | `llava-hf/llava-onevision-qwen2-7b-ov-hf` | Apache-2.0 | ~16 GB / ~6 GB | ~1-2 s | Multi-image + video frames; widely supported in vLLM/TGI; lower refusal rate than Qwen2-VL on borderline content | Weaker fine-grained scene reasoning than Qwen2-VL; OCR mediocre | ENSEMBLE (fallback) |
| 3 | **InternVL 2.5-8B** | `OpenGVLab/InternVL2_5-8B` | MIT (commercial-OK) | ~18 GB / ~7 GB | ~2-3 s | SOTA on Chinese benchmarks + strong on Western too; excellent at gore/weapon detection per published evals; supports tile-based hi-res | Tile pre-processing adds 200-400ms; heavier safety filter than LLaVA | ENSEMBLE (gore/weapon specialist) |
| 4 | **MiniCPM-V 2.6 / 8B** | `openbmb/MiniCPM-V-2_6` | Apache-2.0 (weights) + custom for commercial above $? — REVIEW | ~16 GB / ~5 GB | ~0.8-1.5 s | Smallest VRAM footprint; fastest; OCR-strong; runs on phones via llama.cpp | Slightly weaker on nuanced reasoning vs Qwen2-VL-7B; license has a commercial-revenue clause needing review | ENSEMBLE (latency tier) |
| 5 | **CogVLM2-Llama3-8B** | `THUDM/cogvlm2-llama3-chat-19B` (note: 19B variant; 8B is older v1) | CogVLM License + Llama3 (commercial-OK with ack) | ~24 GB / ~10 GB — TIGHT on 4090 | ~3-5 s | Strongest grounding/bounding-box outputs; good zero-shot violence | 19B actual size exceeds clean 4090 budget; v1 8B is older arch; complex licensing stack | SKIP (VRAM + license overhead) |

**Picked primary: Qwen2-VL-7B-Instruct (AWQ int4).** Apache-2.0, ~6 GB VRAM at int4, best nuanced reasoning, leaves 18 GB headroom on the 4090 to co-host the Falconsai ViT + LoRA adapter.

---

## Integration sketch — Position (b) Tie-breaker

The Falconsai ViT-base scanner stays the first-pass classifier (~50 ms/img, ~1 GB VRAM). When ViT confidence falls in the **mid-band 0.4-0.7** for ANY of the dangerous categories (CSAM, gore, strangling, self-harm, weapon-at-person, bestiality, non-consent, scat) — historically ~5-8% of scans — the image is routed to Qwen2-VL-7B (int4) with a structured prompt: *"Classify this image against these 8 categories with reasoning. Return JSON: `{category, confidence, evidence, consent_inference}`."* The VLM's verdict overrides the ViT band into a hard `safe` / `flag-for-review` / `auto-block` decision. **Why (b) over (c):** the operator's mission line says *"once flagged the image will go to compliance panel"* — that's a SYNCHRONOUS user-facing decision, so the value is in better real-time triage, not nightly retrospective auditing. Nightly auditor (c) can be a phase-2 add-on that re-scores last-7-days low-confidence-passed scans to catch ViT false-negatives and seed the LoRA training JSONL.

---

## SketchVLM specifically

**What:** SketchVLM (`sketchvlm.github.io`, 2025) is a prompting framework that has GPT-4V/Gemini draw SVG overlay annotations on images to improve grounded reasoning — it is NOT an open-weight model and NOT a classifier; it's a closed-API decoration layer. **Why skip:** depends on closed APIs we'd have to pay per-call, doesn't run locally, doesn't classify (it annotates), and gives us no LoRA-fine-tunable surface for our 8 category taxonomy. **One idea worth stealing:** the structured-region-output pattern — when we later need bounding-box-level moderation (e.g. "blur only the weapon, not the whole image"), we should prompt Qwen2-VL or InternVL to emit `<box>x1,y1,x2,y2</box>` tags around offending regions, exactly like SketchVLM's SVG approach but using the bounding-box grounding both Qwen2-VL and InternVL natively support. That unlocks selective-redaction UX without a separate detection model.

---

## Next steps (queued, NOT executed)

1. Download `Qwen/Qwen2-VL-7B-Instruct-AWQ` (~6 GB) into the ViT training rig
2. Smoke-test on 50 hand-labeled images from the existing letstext seed-moderation set
3. Wire mid-band-router in `backend/src/lib/image-moderation.ts` (env-gated: `EVE_VLM_TIEBREAK=true`)
4. Add per-category prompt templates to `eve-compliance/prompts/vlm-categories.md`
5. Log VLM verdicts to the same training JSONL the ViT LoRA consumes — double-signal training data

