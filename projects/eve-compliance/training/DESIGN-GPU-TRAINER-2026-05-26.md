# DESIGN — 24/7 GPU Trainer for EVE Image Moderation

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: `eve-compliance`
> Operator directive verbatim 2026-05-26: *"setup 24/7 training using my 4090 gpu that i can easily allocate resources to and turn on and off"*
> Target hardware: RTX 4090 (24 GB VRAM) · Win10 · Python 3.12
> Composes with: `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` · `eve_compliance_train_loop.py` (singleton pidfile + signal-driven shutdown pattern) · `auto-start-if-no-agent-doctrine-2026-05-25`

---

## TL;DR

- **Primary path:** PyTorch 2.x + HuggingFace Transformers + PEFT (LoRA) fine-tune of `Falconsai/nsfw_image_detection` (ViT-base, 224px, already an NSFW classifier — we adapt it on our human-labeled JSONL).
- **Fallback:** ONNX Runtime + a frozen ViT backbone, training only the classifier head (used if the LoRA path hits dependency hell on Windows).
- **Resource control:** JSON control file polled every 5 s — `gpu_mem_pct`, `max_batch`, `max_cpu_threads`, `enabled`. Pause = sleep between batches, NOT process kill. Model + optimizer stay resident.
- **On/off:** normal-user Python process. `python automations/eve_gpu_trainer.py {start|stop|status|set}`. Singleton pidfile reused from `eve_compliance_train_loop.py`.
- **Game/SD coexistence:** `pynvml` polls free VRAM every 5 s. <4 GB free for 30 s → auto-pause; ≥6 GB free for 60 s → auto-resume.
- **24/7:** watchdog (`eve_gpu_trainer_watchdog.py`) re-spawns on crash; checkpoint every 500 steps + on SIGTERM; resume from latest ckpt; pull fresh JSONL every 1 h via `npx tsx`.

---

## 1. Architecture choice

### Option A — PyTorch + HF Trainer + PEFT/LoRA (RECOMMENDED, primary)

**Base model:** `Falconsai/nsfw_image_detection` (HuggingFace). It's a `google/vit-base-patch16-224` fine-tuned for NSFW classification — already 90 %+ of the way to what we need. We adapt it on our human-labeled good-catch/bad-catch JSONL via LoRA so the base weights stay frozen (tiny disk + memory cost per adapter).

- Repo: https://huggingface.co/Falconsai/nsfw_image_detection
- PEFT docs: https://huggingface.co/docs/peft/index
- HF Trainer (resume/checkpoint/eval/logging built-in): https://huggingface.co/docs/transformers/main_classes/trainer

**Install cost (Win10 Python 3.12, ~6 GB on disk):**

```
pip install "torch==2.4.1+cu121" "torchvision==0.19.1+cu121" --index-url https://download.pytorch.org/whl/cu121
pip install "transformers>=4.44" "peft>=0.13" "accelerate>=0.34" "datasets>=2.20" "pillow" "pynvml" "psutil"
```

Note: skip `bitsandbytes` on Windows — it's flaky. LoRA alone gets us under 6 GB VRAM at batch 32 without 8-bit.

**VRAM budget (ViT-base @ 224px, LoRA rank=8, fp16):**

| Batch | VRAM (model+grad+optimizer+activations) |
|------:|----------------------------------------|
| 16    | ~2.8 GB                                 |
| 32    | ~4.5 GB                                 |
| 64    | ~8.0 GB                                 |
| 128   | ~15 GB (only if 4090 is otherwise idle) |

**Per-epoch time at 50k rows, batch 32, on a 4090:** ~6–9 min (mostly image-decode bound — bottleneck is `PIL` + R2 download, not compute). We sustain ~150 steps/sec on the GPU itself.

**Why this beats B and C:**
- HF `Trainer.train(resume_from_checkpoint=True)` gives us 24/7 reliability for free.
- LoRA adapters are ~3 MB each — we can keep a dated adapter for every nightly run and roll back if precision regresses.
- The same PyTorch process can ALSO run the classifier head as inference for the compliance API once trained (no separate inference server).

### Option B — ONNX Runtime fine-tune (FALLBACK)

Use only if (a) PEFT/LoRA stack refuses to install on the 4090 Win10 setup, or (b) we need to ship the trained model to a non-GPU edge. Freeze the ViT backbone, replace the head with a 2-layer MLP, train the head only. Loses LoRA's flexibility (can't adapt attention layers) but installs in 90 s and uses ~1.5 GB VRAM at batch 32.

- onnxruntime-training docs: https://onnxruntime.ai/docs/get-started/training-pytorch.html

### Option C — LLaVA/Qwen-VL teacher → student distillation (REJECTED for now)

Right idea long-term, but: (a) Qwen2-VL-7B alone is ~16 GB VRAM in fp16 — leaves no headroom for actual training; (b) we already have human labels, so we don't need a teacher; (c) adds a second model dependency we don't currently need. **Re-evaluate when we have >500 k unlabeled images and want to bootstrap.**

### Recommendation: **Option A.**

Reference repos to crib from:
- https://github.com/huggingface/peft/tree/main/examples/image_classification (PEFT image-classification LoRA recipe — direct match)
- https://github.com/huggingface/transformers/tree/main/examples/pytorch/image-classification (canonical HF script — our `train_step` lifts from here)
- https://github.com/microsoft/LoRA (the original paper's reference impl)

---

## 2. Resource control mechanism (3 layers)

### Layer 1 — GPU memory cap

```python
import torch
torch.cuda.set_per_process_memory_fraction(frac, device=0)  # frac in [0.0, 1.0]
```

Docs: https://pytorch.org/docs/stable/generated/torch.cuda.set_per_process_memory_fraction.html. Driven by `control.json` `gpu_mem_pct`. `50` → frac=0.5 → 12 GB cap on a 24 GB 4090. Re-applied on every config reload (it's idempotent and cheap).

### Layer 2 — CPU cap

```python
import torch, os, psutil
torch.set_num_threads(n_threads)
torch.set_num_interop_threads(max(1, n_threads // 2))
p = psutil.Process(os.getpid())
p.cpu_affinity(list(range(n_threads)))  # pin to first N cores
```

Docs: https://pytorch.org/docs/stable/generated/torch.set_num_threads.html · https://psutil.readthedocs.io/en/latest/#psutil.Process.cpu_affinity

### Layer 3 — Pause/resume (toggle without losing model state)

A watcher thread polls `control.json` every 5 s. The train loop checks a `paused` `threading.Event` between every batch:

```python
while not stopping:
    if pause_event.is_set():
        time.sleep(1.0)
        continue
    batch = next(dataloader)
    loss = step(batch)
```

Pause does NOT free the model, optimizer, or dataloader — they sit in VRAM/RAM. When `enabled` flips back to `true`, training resumes at the next batch with zero re-init cost. Operator can flip it from a desktop shortcut, a hotkey, or `eve_gpu_trainer.py set --enabled false` — all just write the same JSON file.

### Sample `control.json` schema

```json
{
  "$schema": "training/control.schema.json",
  "version": 1,
  "enabled": true,
  "gpu_mem_pct": 50,
  "max_batch": 32,
  "max_cpu_threads": 8,
  "checkpoint_every_steps": 500,
  "data_refresh_minutes": 60,
  "auto_pause_on_contention": true,
  "contention_free_vram_mb": 4096,
  "contention_hold_seconds": 30,
  "resume_free_vram_mb": 6144,
  "resume_hold_seconds": 60,
  "max_steps_per_session": 0,
  "logging": { "level": "INFO", "wandb": false }
}
```

`max_steps_per_session: 0` = unlimited (24/7). Everything else has a hot-reload semantic — the watcher logs the diff every reload.

---

## 3. On/off without admin/elevation

Per `no-bat-no-ps1-doctrine`, **no `.bat`, no `.ps1`, no SYSTEM schtask.** Everything is `python …`.

```
python automations/eve_gpu_trainer.py start
python automations/eve_gpu_trainer.py stop
python automations/eve_gpu_trainer.py status
python automations/eve_gpu_trainer.py set --gpu-pct 70 --batch 64 --enabled true
python automations/eve_gpu_trainer.py pause      # convenience for set --enabled false
python automations/eve_gpu_trainer.py resume     # convenience for set --enabled true
```

- `start` spawns the daemon detached (`subprocess.Popen` with `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS` on Windows so it survives the launcher terminal), writes pid to `_shared-memory/eve-gpu-trainer.pid`.
- `stop` reads the pidfile, sends `CTRL_BREAK_EVENT` (Windows) or `SIGTERM` (Unix). Daemon catches it, finishes the current batch, writes checkpoint, releases pid.
- `set` writes `control.json` atomically (write to temp, `os.replace`). Live daemon picks it up within 5 s.
- Singleton pidfile reuses the exact `acquire_singleton_lock` / `release_singleton_lock` / `_pid_alive` helpers from `eve_compliance_train_loop.py:380-432` — copy them, don't refactor, to keep the lanes independent.

**Auto-start at login (optional, normal-user):** `schtasks /Create /TN "SinisterEveGpuTrainer" /SC ONLOGON /TR "python D:\Sinister Sanctum\automations\eve_gpu_trainer.py start" /RL LIMITED /F` — `/RL LIMITED` keeps it in the user context (no UAC). Documented but NOT installed by default; operator opts in via `eve_gpu_trainer.py install-autostart`.

---

## 4. 24/7 reliability

### Watchdog

Second tiny Python script `automations/eve_gpu_trainer_watchdog.py`:

```
loop forever:
    if not _pid_alive(read_pidfile()):
        log "trainer dead — respawning"
        subprocess.Popen([sys.executable, "eve_gpu_trainer.py", "start"])
        wait 30s for heartbeat to appear
    sleep 60s
```

Its own pidfile + heartbeat (`_shared-memory/heartbeats/eve-gpu-trainer-watchdog.json`). Started by the same `eve_gpu_trainer.py install-autostart` schtask (two `TR` entries).

### Checkpointing

HF `Trainer` flag `save_steps=500` + `save_total_limit=5`. SIGTERM handler also calls `trainer.save_model()` before exit. Latest pointer written to `training/checkpoints/LATEST` (just contains the path). Resume on next start: `Trainer.train(resume_from_checkpoint="auto")`.

### Data refresh

Background thread runs every `data_refresh_minutes` (default 60):

```
cd C:/Users/Zonia/Desktop/LetsText
npx tsx backend/scripts/export-moderation-training.ts > training/data/labeled-<utc>.jsonl
```

Concatenate-and-dedup against the working set (`training/data/working.jsonl`). Dedup key = `id` (scan id). DataLoader watches mtime of `working.jsonl`; on change it rebuilds the dataset for the next epoch. Stale files in `training/data/_archive/` for replay.

---

## 5. Operator UX

### Sample `python eve_gpu_trainer.py status` output

```
EVE GPU Trainer · running (pid 18432) · uptime 47h 12m
─────────────────────────────────────────────────────────────
 gpu               RTX 4090 (24576 MiB total)
 vram_used         3287 MiB (13%)   cap 12288 MiB (50%)
 cpu_threads       8 / 24            affinity 0-7
 enabled           True              auto_pause_on_contention True
 state             TRAINING          (paused: False, contention: False)
─────────────────────────────────────────────────────────────
 model             Falconsai/nsfw_image_detection + LoRA r=8
 epoch             14    step 7250    loss 0.0184    eval_acc 0.927
 batch_size        32    lr 3e-5      grad_accum 1
 last_checkpoint   training/checkpoints/checkpoint-7000  (2 min ago)
 last_data_pull    2026-05-26T18:32Z  (working.jsonl: 8214 rows)
 heartbeat         _shared-memory/heartbeats/eve-gpu-trainer.json (4s ago)
─────────────────────────────────────────────────────────────
 control.json      training/control.json (mtime: 11 min ago)
 watchdog          running (pid 18411)
```

### Heartbeat schema (`_shared-memory/heartbeats/eve-gpu-trainer.json`)

Same shape as other fleet heartbeats so existing sweeper sees it:

```json
{
  "slug": "eve-gpu-trainer",
  "agent_display": "EVE GPU Trainer",
  "ts_utc": "2026-05-26T19:00:14Z",
  "pid": 18432,
  "state": "TRAINING",
  "vram_used_mib": 3287,
  "vram_cap_mib": 12288,
  "epoch": 14,
  "step": 7250,
  "loss": 0.0184,
  "eval_acc": 0.927,
  "last_checkpoint": "training/checkpoints/checkpoint-7000",
  "last_data_pull_utc": "2026-05-26T18:32:01Z",
  "next_checkpoint_in_steps": 250
}
```

---

## 6. Composing with operator's other GPU workloads

### `pynvml` API for other-process VRAM

```python
import pynvml
pynvml.nvmlInit()
h = pynvml.nvmlDeviceGetHandleByIndex(0)
mem = pynvml.nvmlDeviceGetMemoryInfo(h)     # .total .used .free  (bytes)
procs = pynvml.nvmlDeviceGetComputeRunningProcesses_v3(h)
gfx_procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses_v3(h)
for p in procs + gfx_procs:
    # p.pid, p.usedGpuMemory (bytes, may be None on Windows graphics ctx)
    ...
```

Docs: https://docs.nvidia.com/deploy/nvml-api/ · Python wrapper: https://pypi.org/project/pynvml/

### Contention policy

A `contention_watch` thread polls every 5 s. Tracks `free_mb` in a deque of last 12 samples (60 s window).

- **Pause trigger:** every sample in the last 30 s shows `free_mb < contention_free_vram_mb` (default 4096). → `pause_event.set()`, log "contention-pause: free=2.8GB other-procs=[steam.exe, sd-webui.exe]".
- **Resume trigger:** every sample in the last 60 s shows `free_mb >= resume_free_vram_mb` (default 6144). → `pause_event.clear()`, log "contention-resume".

Operator can disable the whole mechanism with `auto_pause_on_contention: false` (e.g. if they're confident they want the trainer to fight for VRAM during a render).

Also enumerate other-process PIDs into the heartbeat (`contention.other_pids`, `contention.other_proc_names`) so the operator sees WHICH process kicked us out without opening Task Manager.

---

## Open questions (parent decides)

1. **Storage location for checkpoints + working JSONL** — `D:\Sinister Sanctum\projects\eve-compliance\training\` keeps it lane-local but D: is the 1 TB drive that already hosts the vault. Alternative: dedicated path on C: if D: I/O contends with vault sync. Default: D:, override via `control.json` `paths.root`.
2. **Eval split** — fixed 10 % holdout from current working.jsonl, OR rolling-window last-1000-rows-as-eval? Default to fixed holdout with deterministic seed (42).
3. **Adapter naming** — `lora-<utc>` per checkpoint vs. single rolling adapter? Default: rolling adapter for the live serving path, archived snapshots dated for rollback.
4. **Inference handoff** — does the LetsText backend call the trainer's classifier inference endpoint, or do we export the merged model and load it in the Node `image-moderation.ts` provider abstraction? Default: keep them decoupled — trainer writes `training/adapters/CURRENT/` and a sibling tiny Python inference daemon (or `onnxruntime-node`) serves it.

These are NOT blockers — defaults above ship a working daemon. Operator iterates.

---

## Acceptance criteria (verify these before claiming shipped)

- `python eve_gpu_trainer.py start` from a cold-boot user shell — daemon comes up, writes heartbeat <30 s, prints pid.
- `python eve_gpu_trainer.py set --enabled false` — within 10 s heartbeat shows `state: PAUSED`, VRAM use drops only to model+optimizer baseline (~2 GB at batch 32), no GPU compute.
- `python eve_gpu_trainer.py set --enabled true` — within 10 s heartbeat shows `state: TRAINING`, step counter increments.
- Launch a Stable Diffusion XL session → free VRAM drops below 4 GB → within 60 s daemon auto-pauses, heartbeat shows `contention.paused=true` + other-proc names.
- Close SD → free VRAM recovers above 6 GB for 60 s → daemon auto-resumes from where it paused.
- `taskkill /PID <trainer-pid> /F` → watchdog respawns within 90 s → resumes from latest checkpoint.
- Operator runs `python eve_gpu_trainer.py stop` during training → daemon finishes current batch, writes checkpoint, releases pidfile, exits 0 within 30 s.

End.
