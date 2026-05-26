#!/bin/bash
# Author: RKOJ-ELENO :: 2026-05-26
#
# Triggers the GPU trainer once torch has finished installing in the venv.
# Designed to be invoked by the bash background-monitor that watches for the
# torch/ directory to appear in projects/eve-compliance/training/.venv/Lib/site-packages/.
#
# Steps:
#   1. Verify torch + CUDA detect the 4090
#   2. Install the rest of the ML stack (transformers + peft + accelerate + datasets)
#   3. Spawn the trainer daemon (detached)
#   4. Spawn the watchdog (detached)
#   5. 60s sleep + verify both are healthy via status
#
# Idempotent — safe to re-run.

set -e

SANCTUM="D:/Sinister Sanctum"
VENV_PY="$SANCTUM/projects/eve-compliance/training/.venv/Scripts/python.exe"
LOG="$SANCTUM/projects/eve-compliance/training/logs/autostart-$(date -u +%Y%m%dT%H%M%SZ).log"

mkdir -p "$SANCTUM/projects/eve-compliance/training/logs"

{
  echo "=== EVE GPU Trainer auto-start $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
  echo ""
  echo "── Step 1: Verify torch + CUDA"
  "$VENV_PY" -c "import torch; print('torch=' + torch.__version__ + ' cuda=' + str(torch.cuda.is_available()) + ' device=' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none'))"
  echo ""
  echo "── Step 2: Install ML stack (transformers + peft + accelerate + datasets)"
  "$VENV_PY" -m pip install "transformers>=4.44" "peft>=0.13" "accelerate>=0.34" "datasets>=2.20" 2>&1 | tail -5
  echo ""
  echo "── Step 3: Spawn trainer daemon"
  python "$SANCTUM/automations/eve_gpu_trainer.py" start
  echo ""
  echo "── Step 4: Spawn watchdog"
  python "$SANCTUM/automations/eve_gpu_trainer_watchdog.py" start
  echo ""
  echo "── Step 5: 60s smoke"
  sleep 60
  python "$SANCTUM/automations/eve_gpu_trainer.py" status || true
  echo ""
  python "$SANCTUM/automations/eve_gpu_trainer_watchdog.py" status || true
  echo ""
  echo "=== Auto-start complete $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
} 2>&1 | tee "$LOG"
