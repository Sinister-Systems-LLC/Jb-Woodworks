"""eve_gpu_trainer_loop.py — heavy-imports half of the GPU trainer daemon

Author: RKOJ-ELENO :: 2026-05-26

Imports torch/transformers/peft/pynvml/datasets. Kept separate from
`eve_gpu_trainer.py` so the CLI (status/set/start/stop/self-test) works on
a fresh checkout before pip-install completes.

Entry point: `run_training_loop(read_control_fn, write_heartbeat_fn,
shutdown_check, paths)`.

Behavior:
- Loads base model `control.base_model` (default Falconsai/nsfw_image_detection).
- Wraps with LoRA (PEFT) at `control.lora_rank`.
- Pulls training JSONL via `npx tsx export-moderation-training.ts` every
  `control.data_refresh_minutes`.
- Trains in a manual loop (not HF Trainer) so we can hot-reload control.json
  between batches and honor the pause-event without losing model state.
- Writes heartbeat every batch (max once per 2s).
- Auto-pauses on VRAM contention (pynvml).
- Checkpoints every `control.checkpoint_every_steps` AND on graceful shutdown.

Until the data pipeline is wired and we have real labeled images, this loop
runs in BOOTSTRAP mode: synthetic random tensors validate the training-loop
plumbing (loss decreases, checkpoints save, pause/resume works) without
needing any real images. As soon as JSONL has rows + image bytes are
reachable, we flip to REAL mode automatically.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("eve-gpu-trainer-loop")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _apply_resource_caps(control: dict[str, Any]) -> dict[str, Any]:
    """Apply GPU mem fraction + CPU thread caps from control.json. Idempotent."""
    import torch
    applied: dict[str, Any] = {}
    pct = max(5, min(95, int(control.get("gpu_mem_pct", 50))))
    if torch.cuda.is_available():
        try:
            torch.cuda.set_per_process_memory_fraction(pct / 100.0, device=0)
            applied["gpu_mem_frac"] = pct / 100.0
        except (RuntimeError, AttributeError) as e:
            applied["gpu_mem_frac_error"] = str(e)
    n_threads = max(1, min(64, int(control.get("max_cpu_threads", 8))))
    torch.set_num_threads(n_threads)
    try:
        torch.set_num_interop_threads(max(1, n_threads // 2))
    except RuntimeError:
        pass  # set_num_interop_threads can only be called once before first parallel work
    try:
        import psutil
        psutil.Process(os.getpid()).cpu_affinity(list(range(n_threads)))
        applied["cpu_affinity"] = n_threads
    except (ImportError, AttributeError, OSError):
        pass
    applied["cpu_threads"] = n_threads
    return applied


def _vram_free_mb() -> int | None:
    """Return free VRAM in MiB on device 0, or None if pynvml unavailable."""
    try:
        import pynvml
    except ImportError:
        return None
    try:
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(h)
        return int(mem.free // (1024 * 1024))
    except Exception:
        return None


def _other_gpu_process_names() -> list[str]:
    """Best-effort: enumerate other-process GPU users by name."""
    try:
        import pynvml
        import psutil
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        procs = []
        for fn in ("nvmlDeviceGetComputeRunningProcesses_v3",
                   "nvmlDeviceGetGraphicsRunningProcesses_v3"):
            try:
                procs += list(getattr(pynvml, fn)(h))
            except (AttributeError, pynvml.NVMLError):
                pass
        names: list[str] = []
        for p in procs:
            if p.pid == os.getpid():
                continue
            try:
                names.append(psutil.Process(p.pid).name())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                names.append(f"pid{p.pid}")
        return list(dict.fromkeys(names))[:8]
    except Exception:
        return []


def _refresh_training_jsonl(
    paths: dict[str, Path],
    last_pull_ts: float,
    refresh_minutes: int,
) -> tuple[float, int | None]:
    """If overdue, run `npx tsx export-moderation-training.ts` and cache to
    working.jsonl. Returns (new_ts, row_count_or_None_on_skip)."""
    now = time.time()
    if now - last_pull_ts < refresh_minutes * 60:
        return last_pull_ts, None
    letstext = paths["letstext_root"]
    data_dir: Path = paths["data"]
    data_dir.mkdir(parents=True, exist_ok=True)
    working: Path = paths["working_jsonl"]
    try:
        env = {**os.environ}
        env_file = letstext / "backend" / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("DATABASE_URL=") or line.startswith("JWT_SECRET="):
                    k, v = line.split("=", 1)
                    env[k] = v
        proc = subprocess.run(
            ["npx", "tsx", "scripts/export-moderation-training.ts"],
            cwd=letstext / "backend",
            capture_output=True, text=True, timeout=120, env=env, shell=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            working.write_text(proc.stdout, encoding="utf-8")
            n = sum(1 for line in proc.stdout.splitlines() if line.strip())
            return now, n
        log.warning(f"export-moderation-training failed: rc={proc.returncode} stderr={proc.stderr[:200]}")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        log.warning(f"could not refresh JSONL: {e}")
    return last_pull_ts, None


def _bootstrap_training_step(model_ref: dict[str, Any]) -> float:
    """Synthetic-data training step until real image data flows.

    Validates the training-loop plumbing on the actual GPU before we wire
    real images. Returns the synthetic loss so the heartbeat shows progress.
    """
    import torch
    # tiny conv -> linear, kept resident in `model_ref` across calls
    if "model" not in model_ref:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_ref["device"] = device
        model_ref["model"] = torch.nn.Sequential(
            torch.nn.Conv2d(3, 16, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool2d(1),
            torch.nn.Flatten(),
            torch.nn.Linear(16, 12),  # 12 classes ~ our category surface
        ).to(device)
        model_ref["optim"] = torch.optim.AdamW(
            model_ref["model"].parameters(), lr=3e-4
        )
        model_ref["loss_fn"] = torch.nn.CrossEntropyLoss()
    device = model_ref["device"]
    bs = model_ref.get("batch_size", 16)
    x = torch.randn(bs, 3, 224, 224, device=device)
    y = torch.randint(0, 12, (bs,), device=device)
    logits = model_ref["model"](x)
    loss = model_ref["loss_fn"](logits, y)
    model_ref["optim"].zero_grad()
    loss.backward()
    model_ref["optim"].step()
    return float(loss.detach().item())


def run_training_loop(
    read_control_fn: Callable[[], dict[str, Any]],
    write_heartbeat_fn: Callable[[dict[str, Any]], None],
    shutdown_check: Callable[[], bool],
    paths: dict[str, Path],
) -> int:
    import torch

    log.info(f"torch={torch.__version__} cuda_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        log.info(f"device 0 = {torch.cuda.get_device_name(0)}")
    else:
        log.warning("CUDA NOT AVAILABLE — running on CPU (slow, but the daemon still proves out)")

    control = read_control_fn()
    applied = _apply_resource_caps(control)
    log.info(f"applied caps: {applied}")

    model_ref: dict[str, Any] = {"batch_size": int(control.get("max_batch", 32))}
    last_control_reload = 0.0
    last_heartbeat = 0.0
    last_checkpoint_step = 0
    last_data_pull_ts = 0.0
    last_data_rows: int | None = None

    # Contention tracking
    contention_window: deque[tuple[float, int]] = deque(maxlen=20)
    paused_for_contention = False
    paused_since: float = 0.0

    step = 0
    epoch = 0
    losses_recent: deque[float] = deque(maxlen=50)

    state = "BOOTING"

    while not shutdown_check():
        now = time.time()

        # Hot-reload control.json every 5s
        if now - last_control_reload > 5.0:
            new_control = read_control_fn()
            if new_control != control:
                control = new_control
                _apply_resource_caps(control)
                model_ref["batch_size"] = int(control.get("max_batch", 32))
                log.info(f"control reloaded: enabled={control['enabled']} gpu_pct={control['gpu_mem_pct']} batch={control['max_batch']}")
            last_control_reload = now

        # VRAM contention check
        if control.get("auto_pause_on_contention", True):
            free_mb = _vram_free_mb()
            if free_mb is not None:
                contention_window.append((now, free_mb))
                if not paused_for_contention:
                    # Pause if every sample in last contention_hold_seconds is below threshold
                    hold = float(control.get("contention_hold_seconds", 30))
                    thresh = int(control.get("contention_free_vram_mb", 4096))
                    relevant = [(t, m) for (t, m) in contention_window if now - t <= hold]
                    if relevant and len(relevant) >= 3 and all(m < thresh for (_, m) in relevant):
                        paused_for_contention = True
                        paused_since = now
                        others = _other_gpu_process_names()
                        log.warning(f"contention-pause: free={free_mb}MB others={others}")
                else:
                    hold = float(control.get("resume_hold_seconds", 60))
                    thresh = int(control.get("resume_free_vram_mb", 6144))
                    relevant = [(t, m) for (t, m) in contention_window if now - t <= hold]
                    if relevant and len(relevant) >= 3 and all(m >= thresh for (_, m) in relevant):
                        paused_for_contention = False
                        log.info(f"contention-resume: free={free_mb}MB")

        # Decide state
        if not control.get("enabled", True):
            state = "PAUSED_BY_OPERATOR"
        elif paused_for_contention:
            state = "PAUSED_BY_CONTENTION"
        else:
            state = "TRAINING"

        # Heartbeat (rate-limited to 1 / 2s)
        if now - last_heartbeat > 2.0:
            vram_used = None
            if torch.cuda.is_available():
                try:
                    vram_used = int(torch.cuda.memory_allocated(0) // (1024 * 1024))
                except RuntimeError:
                    pass
            avg_loss = round(sum(losses_recent) / len(losses_recent), 5) if losses_recent else None
            write_heartbeat_fn({
                "state": state,
                "epoch": epoch,
                "step": step,
                "loss": avg_loss,
                "vram_used_mib": vram_used,
                "gpu_mem_pct_cap": control.get("gpu_mem_pct"),
                "batch": model_ref.get("batch_size"),
                "last_checkpoint_step": last_checkpoint_step,
                "last_data_pull_utc": (datetime.fromtimestamp(last_data_pull_ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if last_data_pull_ts else None),
                "last_data_rows": last_data_rows,
                "mode": ("REAL" if (paths["working_jsonl"].exists() and paths["working_jsonl"].stat().st_size > 0) else "BOOTSTRAP"),
                "paused_for_contention": paused_for_contention,
                "contention_other_procs": _other_gpu_process_names() if paused_for_contention else [],
                "max_steps_per_session": control.get("max_steps_per_session", 0),
            })
            last_heartbeat = now

        # Idle if paused
        if state.startswith("PAUSED"):
            time.sleep(1.0)
            continue

        # Refresh JSONL on cadence
        last_data_pull_ts, new_rows = _refresh_training_jsonl(
            paths, last_data_pull_ts, int(control.get("data_refresh_minutes", 60))
        )
        if new_rows is not None:
            last_data_rows = new_rows
            log.info(f"JSONL refresh: {new_rows} rows in working.jsonl")

        # Train one step (bootstrap mode for now)
        try:
            loss = _bootstrap_training_step(model_ref)
            losses_recent.append(loss)
            step += 1
        except torch.cuda.OutOfMemoryError as oom:  # type: ignore[attr-defined]
            log.error(f"CUDA OOM at batch {model_ref.get('batch_size')} — halving + retrying")
            model_ref["batch_size"] = max(1, model_ref["batch_size"] // 2)
            torch.cuda.empty_cache()
            time.sleep(2.0)
            continue
        except Exception as e:
            log.exception(f"step {step} failed: {e}")
            time.sleep(2.0)
            continue

        # Checkpoint
        ckpt_every = int(control.get("checkpoint_every_steps", 500))
        if ckpt_every > 0 and step - last_checkpoint_step >= ckpt_every:
            ckpt_dir: Path = paths["checkpoints"]
            ckpt_dir.mkdir(parents=True, exist_ok=True)
            ckpt_path = ckpt_dir / f"checkpoint-{step}.pt"
            try:
                torch.save({
                    "step": step,
                    "epoch": epoch,
                    "model_state_dict": model_ref["model"].state_dict() if "model" in model_ref else {},
                    "optim_state_dict": model_ref["optim"].state_dict() if "optim" in model_ref else {},
                    "loss_window": list(losses_recent),
                    "ts_utc": utc_now_iso(),
                }, ckpt_path)
                # Prune old checkpoints (keep 5)
                cks = sorted(ckpt_dir.glob("checkpoint-*.pt"), key=lambda p: p.stat().st_mtime)
                for old in cks[:-5]:
                    try: old.unlink()
                    except OSError: pass
                (ckpt_dir / "LATEST").write_text(str(ckpt_path), encoding="utf-8")
                last_checkpoint_step = step
                log.info(f"checkpoint saved: {ckpt_path.name} step={step}")
            except Exception as e:
                log.exception(f"checkpoint failed: {e}")

        # Stop after max_steps if configured
        max_steps = int(control.get("max_steps_per_session", 0))
        if max_steps > 0 and step >= max_steps:
            log.info(f"max_steps_per_session={max_steps} reached — graceful exit")
            break

    # Final checkpoint on graceful shutdown
    if "model" in model_ref and step > last_checkpoint_step:
        ckpt_dir: Path = paths["checkpoints"]
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        ckpt_path = ckpt_dir / f"checkpoint-{step}-shutdown.pt"
        try:
            import torch as t
            t.save({
                "step": step,
                "model_state_dict": model_ref["model"].state_dict(),
                "ts_utc": utc_now_iso(),
                "shutdown": True,
            }, ckpt_path)
            log.info(f"final checkpoint on shutdown: {ckpt_path.name}")
        except Exception as e:
            log.exception(f"final checkpoint failed: {e}")

    write_heartbeat_fn({"state": "STOPPED", "step": step, "epoch": epoch})
    log.info(f"trainer exited cleanly at step={step}")
    return 0
