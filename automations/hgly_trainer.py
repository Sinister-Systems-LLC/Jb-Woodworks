#!/usr/bin/env python3
"""hgly_trainer.py - continuous LoRA fine-tune trainer for Sinister Hieroglyphics.

Author: RKOJ-ELENO :: 2026-05-25

Operator hard-canonical 2026-05-25 ~13:30Z (verbatim):
  "...train it 24/7 with my 4090. i want the most efficet codfing language you can."

PURPOSE
=======
Phase 0 skeleton for the continuous LoRA fine-tune trainer of
Qwen2.5-Coder-7B-Instruct on the operator's RTX 4090 (24 GB VRAM).

The trainer is the inner loop of the Sinister Hieroglyphics master plan
(see _shared-memory/plans/sinister-hieroglyphics-master-2026-05-25T1340Z/plan.md
Phase 9). It must:

  - read a corpus of (prompt, completion) JSONL rows from
    _shared-memory/hgly-corpus/
  - run one LoRA fine-tune epoch every ~60 minutes
  - evaluate against a held-out test set
  - if eval drops vs best, REVERT-TO-PEAK via loop_checkpoint.py
  - else save the new adapter as the new peak

SUBCOMMANDS
===========
  probe        - check 4090 / VRAM / CUDA / torch / unsloth / peft availability
  corpus       - enumerate _shared-memory/hgly-corpus/ + report size + dedupe
  train-once   - run ONE LoRA fine-tune epoch (dry-run by default until corpus ready)
  eval         - score latest adapter against held-out test set
  loop         - orchestrator: train-once + eval + revert-to-peak on regression
  status       - JSON status snapshot

DESIGN
======
  - Python (no .bat / no .ps1 per no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25).
  - All heavy imports gated behind try/except so the module loads on any host;
    probe surfaces missing deps with actionable hints.
  - --dry-run on every subcommand for smoke testing without GPU work.
  - Default base model: unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit
    (4-bit quantized fits in ~6 GB VRAM, leaving ~18 GB for LoRA training).
  - LoRA rank 16 (smaller = faster but less capacity; operator-overridable).
  - Output dir: _shared-memory/hgly-adapters/<run_id>/iter<N>/
  - Eval set: projects/sinister-hieroglyphics/tests/eval/eval-set.json
    (autocreated with 5 placeholder prompts on first run).
  - Composes with loop_checkpoint.py (save / restore_best).
  - Integrates with quality-monotonic-loop.ps1 by appending kind=hgly-eval
    rows to _shared-memory/quality-loop-log.jsonl.

UTILIZATION BUDGET (RTX 4090, 24 GB VRAM)
=========================================
  60% LoRA fine-tune  (the main loop)
  15% rollouts        (corpus generation via sinister_swarm.py)
  10% eval            (held-out test set scoring)
  10% operator reserve (game / browser / IDE)
   5% thermal slack   (no sustained 100% util to avoid throttling)

  Enforced via --utilization-cap (default 0.85, clamped to [0.5, 0.95]).
  The cap maps to torch.cuda memory-fraction at training startup.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import platform
import sys
import time
import traceback
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LANE = "sinister-hieroglyphics"
DEFAULT_BASE_MODEL = "unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit"
DEFAULT_LORA_RANK = 16
DEFAULT_UTIL_CAP = 0.85
UTIL_CAP_MIN = 0.50
UTIL_CAP_MAX = 0.95
DEFAULT_LOOP_INTERVAL_SECONDS = 60 * 60  # 60 min

PLACEHOLDER_EVAL = [
    {
        "id": "ex001",
        "prompt": "Translate the hieroglyphic operator `>>=` (bind) into a one-line Python comprehension.",
        "ref": "[f(x) for x in xs]",
    },
    {
        "id": "ex002",
        "prompt": "Given the glyph sequence `Q.C.7B -> LoRA(r=16)`, emit the equivalent peft LoraConfig.",
        "ref": "LoraConfig(r=16, lora_alpha=32, target_modules=['q_proj','k_proj','v_proj','o_proj'])",
    },
    {
        "id": "ex003",
        "prompt": "Decode `[ckpt:peak] <- regress` into the Sanctum revert-to-peak primitive.",
        "ref": "loop_checkpoint.restore_best(lane, run_id, sanctum_root)",
    },
    {
        "id": "ex004",
        "prompt": "Render the glyph `swarm.fanout(n=5, task=corpus.gen)` as a sinister_swarm.py CLI call.",
        "ref": "python automations/sinister_swarm.py fanout --workers 5 --task corpus.gen",
    },
    {
        "id": "ex005",
        "prompt": "Express `util.cap(0.85) & thermal.slack(0.05)` as a torch.cuda fraction call.",
        "ref": "torch.cuda.set_per_process_memory_fraction(0.85)",
    },
]


# ---------------------------------------------------------------------------
# Gated heavy imports (probe-friendly)
# ---------------------------------------------------------------------------

_DEPS: dict[str, dict[str, Any]] = {}


def _probe_import(name: str, attr: Optional[str] = None) -> dict[str, Any]:
    info: dict[str, Any] = {"name": name, "available": False, "version": None, "error": None}
    try:
        mod = __import__(name, fromlist=["__version__"] if attr is None else [attr])
        info["available"] = True
        ver = getattr(mod, "__version__", None)
        if ver is None and hasattr(mod, "version"):
            try:
                ver = mod.version()
            except Exception:
                ver = None
        info["version"] = ver
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


def _probe_torch_cuda() -> dict[str, Any]:
    info: dict[str, Any] = {"cuda_available": False, "device_count": 0, "devices": []}
    try:
        import torch  # type: ignore
        info["torch_version"] = torch.__version__
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["cuda_version"] = torch.version.cuda
            count = torch.cuda.device_count()
            info["device_count"] = count
            for i in range(count):
                props = torch.cuda.get_device_properties(i)
                info["devices"].append({
                    "index": i,
                    "name": props.name,
                    "total_memory_gb": round(props.total_memory / (1024**3), 2),
                    "major": props.major,
                    "minor": props.minor,
                    "is_4090": "4090" in props.name,
                })
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _sanctum_root() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    # automations/ lives directly under the sanctum root
    return here.parent.parent


def _corpus_dir() -> pathlib.Path:
    return _sanctum_root() / "_shared-memory" / "hgly-corpus"


def _adapters_dir() -> pathlib.Path:
    return _sanctum_root() / "_shared-memory" / "hgly-adapters"


def _eval_dir() -> pathlib.Path:
    return _sanctum_root() / "projects" / "sinister-hieroglyphics" / "tests" / "eval"


def _eval_set_path() -> pathlib.Path:
    return _eval_dir() / "eval-set.json"


def _quality_log_path() -> pathlib.Path:
    return _sanctum_root() / "_shared-memory" / "quality-loop-log.jsonl"


def _state_path() -> pathlib.Path:
    return _sanctum_root() / "_shared-memory" / "hgly-trainer-state.json"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _new_run_id() -> str:
    return f"hgly-{_utc_now_iso()}"


def _clamp_util(v: float) -> float:
    return max(UTIL_CAP_MIN, min(UTIL_CAP_MAX, float(v)))


def _ensure_eval_set() -> dict[str, Any]:
    ed = _eval_dir()
    ed.mkdir(parents=True, exist_ok=True)
    p = _eval_set_path()
    created = False
    if not p.exists():
        payload = {
            "lane": LANE,
            "version": 1,
            "author": "RKOJ-ELENO",
            "created_utc": _utc_now_iso(),
            "note": "placeholder eval set; Phase 1 corpus work will replace with held-out real prompts",
            "examples": PLACEHOLDER_EVAL,
        }
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        created = True
    return {"path": str(p), "created": created, "count": len(PLACEHOLDER_EVAL)}


def _read_state() -> dict[str, Any]:
    p = _state_path()
    if not p.exists():
        return {"lane": LANE, "iter": 0, "best_score": None, "best_iter": None, "run_id": None, "adapter_path": None}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"lane": LANE, "iter": 0, "best_score": None, "best_iter": None, "run_id": None, "adapter_path": None, "corrupt": True}


def _write_state(state: dict[str, Any]) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_quality_log(row: dict[str, Any]) -> None:
    p = _quality_log_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _emit(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


# ---------------------------------------------------------------------------
# Subcommand: probe
# ---------------------------------------------------------------------------

def cmd_probe(args: argparse.Namespace) -> int:
    result: dict[str, Any] = {
        "subcommand": "probe",
        "dry_run": bool(args.dry_run),
        "utc": _utc_now_iso(),
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "sanctum_root": str(_sanctum_root()),
        "deps": {},
        "gpu": {},
        "paths": {
            "corpus_dir": str(_corpus_dir()),
            "adapters_dir": str(_adapters_dir()),
            "eval_set": str(_eval_set_path()),
            "quality_log": str(_quality_log_path()),
        },
        "config": {
            "default_base_model": DEFAULT_BASE_MODEL,
            "default_lora_rank": DEFAULT_LORA_RANK,
            "default_util_cap": DEFAULT_UTIL_CAP,
            "util_cap_clamp": [UTIL_CAP_MIN, UTIL_CAP_MAX],
        },
        "budget": {
            "lora_pct": 60,
            "rollouts_pct": 15,
            "eval_pct": 10,
            "operator_reserve_pct": 10,
            "thermal_slack_pct": 5,
        },
    }
    for name in ("torch", "unsloth", "peft", "transformers", "datasets", "bitsandbytes", "accelerate", "trl"):
        result["deps"][name] = _probe_import(name)
    result["gpu"] = _probe_torch_cuda()

    # Surface actionable hints
    missing = [n for n, info in result["deps"].items() if not info["available"]]
    hints: list[str] = []
    if missing:
        hints.append(
            "Install missing deps (4090 venv): pip install torch --index-url https://download.pytorch.org/whl/cu121 "
            "&& pip install unsloth peft transformers datasets bitsandbytes accelerate trl"
        )
    if result["gpu"].get("cuda_available") is False:
        hints.append("CUDA not available - confirm NVIDIA driver + CUDA 12.1+ runtime installed.")
    elif not any(d.get("is_4090") for d in result["gpu"].get("devices", [])):
        hints.append("No RTX 4090 detected; trainer will still run but utilization budget assumes 24GB VRAM.")
    result["hints"] = hints
    result["ready"] = (not missing) and result["gpu"].get("cuda_available", False)

    _emit(result)
    return 0


# ---------------------------------------------------------------------------
# Subcommand: corpus
# ---------------------------------------------------------------------------

def _scan_corpus(corpus_dir: pathlib.Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "dir": str(corpus_dir),
        "exists": corpus_dir.exists(),
        "file_count": 0,
        "row_count": 0,
        "byte_total": 0,
        "unique_prompts": 0,
        "dup_prompts": 0,
        "files": [],
    }
    if not corpus_dir.exists():
        return out

    seen: set[str] = set()
    dups = 0
    rows = 0
    files = sorted(corpus_dir.glob("**/*.jsonl"))
    for fp in files:
        try:
            data = fp.read_bytes()
        except Exception:
            continue
        out["byte_total"] += len(data)
        file_rows = 0
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = ""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            file_rows += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            prompt = obj.get("prompt") or obj.get("input") or ""
            h = hashlib.sha256(prompt.encode("utf-8", errors="replace")).hexdigest()[:16]
            if h in seen:
                dups += 1
            else:
                seen.add(h)
        rows += file_rows
        out["files"].append({"path": str(fp.relative_to(corpus_dir)), "bytes": len(data), "rows": file_rows})

    out["file_count"] = len(files)
    out["row_count"] = rows
    out["unique_prompts"] = len(seen)
    out["dup_prompts"] = dups
    return out


def cmd_corpus(args: argparse.Namespace) -> int:
    corpus_dir = _corpus_dir()
    if not corpus_dir.exists() and not args.dry_run:
        corpus_dir.mkdir(parents=True, exist_ok=True)
    scan = _scan_corpus(corpus_dir)
    result = {
        "subcommand": "corpus",
        "dry_run": bool(args.dry_run),
        "utc": _utc_now_iso(),
        "scan": scan,
        "note": (
            "Corpus is empty - Phase 1 (sinister_swarm.py fan-out corpus generation) populates this dir."
            if scan["row_count"] == 0 else None
        ),
    }
    _emit(result)
    return 0


# ---------------------------------------------------------------------------
# Subcommand: train-once
# ---------------------------------------------------------------------------

def cmd_train_once(args: argparse.Namespace) -> int:
    util_cap = _clamp_util(args.utilization_cap)
    state = _read_state()
    run_id = args.run_id or state.get("run_id") or _new_run_id()
    iter_n = int(state.get("iter") or 0) + 1
    out_dir = _adapters_dir() / run_id / f"iter{iter_n:04d}"

    plan = {
        "subcommand": "train-once",
        "dry_run": bool(args.dry_run),
        "utc": _utc_now_iso(),
        "lane": LANE,
        "run_id": run_id,
        "iter": iter_n,
        "base_model": args.base_model,
        "lora_rank": args.lora_rank,
        "utilization_cap": util_cap,
        "out_dir": str(out_dir),
        "corpus_dir": str(_corpus_dir()),
    }

    corpus_scan = _scan_corpus(_corpus_dir())
    plan["corpus_summary"] = {
        "file_count": corpus_scan["file_count"],
        "row_count": corpus_scan["row_count"],
        "unique_prompts": corpus_scan["unique_prompts"],
    }

    if args.dry_run:
        plan["status"] = "dry-run-no-op"
        plan["next_step"] = "remove --dry-run + populate corpus + install deps to run real training"
        _emit(plan)
        return 0

    # Real-training path - all heavy imports gated here
    try:
        import torch  # type: ignore
    except Exception as exc:
        plan["status"] = "missing-dep-torch"
        plan["error"] = f"{type(exc).__name__}: {exc}"
        _emit(plan)
        return 2

    if not torch.cuda.is_available():
        plan["status"] = "no-cuda"
        plan["error"] = "torch.cuda.is_available() == False"
        _emit(plan)
        return 3

    if corpus_scan["row_count"] == 0:
        plan["status"] = "empty-corpus"
        plan["error"] = "no rows in _shared-memory/hgly-corpus/ - run corpus generation first"
        _emit(plan)
        return 4

    try:
        torch.cuda.set_per_process_memory_fraction(util_cap)
    except Exception:
        pass

    try:
        from unsloth import FastLanguageModel  # type: ignore
        from peft import LoraConfig  # type: ignore
    except Exception as exc:
        plan["status"] = "missing-dep-unsloth-or-peft"
        plan["error"] = f"{type(exc).__name__}: {exc}"
        _emit(plan)
        return 5

    out_dir.mkdir(parents=True, exist_ok=True)
    plan["status"] = "scaffold-only"
    plan["note"] = (
        "Phase 0 ships scaffold; Phase 9 fills in the FastLanguageModel.from_pretrained + "
        "LoraConfig + SFTTrainer body. LoraConfig sig confirmed: r=lora_rank."
    )
    # Touch a stub adapter manifest so downstream tooling has a path to reference
    (out_dir / "adapter_manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "iter": iter_n,
                "base_model": args.base_model,
                "lora_rank": args.lora_rank,
                "utc": _utc_now_iso(),
                "status": "scaffold-only",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    state["iter"] = iter_n
    state["run_id"] = run_id
    state["adapter_path"] = str(out_dir)
    _write_state(state)

    _emit(plan)
    return 0


# ---------------------------------------------------------------------------
# Subcommand: eval
# ---------------------------------------------------------------------------

def _score_placeholder(eval_set: dict[str, Any]) -> float:
    """Deterministic placeholder eval score so the loop scaffold is testable
    without a real model. Returns a stable score in [0, 100] derived from
    the eval set hash (so unchanged corpus -> unchanged score)."""
    blob = json.dumps(eval_set.get("examples", []), sort_keys=True).encode("utf-8")
    h = hashlib.sha256(blob).hexdigest()
    return round((int(h[:6], 16) % 5001) / 100.0 + 25.0, 2)  # 25.00 - 75.00


def cmd_eval(args: argparse.Namespace) -> int:
    eset = _ensure_eval_set()
    eval_set = json.loads(_eval_set_path().read_text(encoding="utf-8"))
    state = _read_state()
    run_id = args.run_id or state.get("run_id") or _new_run_id()
    iter_n = int(state.get("iter") or 0)

    result: dict[str, Any] = {
        "subcommand": "eval",
        "dry_run": bool(args.dry_run),
        "utc": _utc_now_iso(),
        "lane": LANE,
        "run_id": run_id,
        "iter": iter_n,
        "eval_set": eset,
        "adapter_path": state.get("adapter_path"),
    }

    if args.dry_run:
        score = _score_placeholder(eval_set)
        result["score"] = score
        result["mode"] = "placeholder"
        result["status"] = "dry-run"
        _append_quality_log({
            "ts": _utc_now_iso(),
            "kind": "hgly-eval",
            "lane": LANE,
            "run_id": run_id,
            "iter": iter_n,
            "score": score,
            "mode": "placeholder-dry-run",
        })
        _emit(result)
        return 0

    # Real eval - gated heavy imports
    try:
        import torch  # type: ignore  # noqa: F401
    except Exception as exc:
        result["status"] = "missing-dep-torch"
        result["error"] = f"{type(exc).__name__}: {exc}"
        _emit(result)
        return 2

    # Phase 0: emit a placeholder score even in non-dry mode so loop testing works
    # before adapters exist. Phase 9 replaces with real adapter-load + generate + score.
    score = _score_placeholder(eval_set)
    result["score"] = score
    result["mode"] = "placeholder-non-dry"
    result["status"] = "scaffold-only"
    _append_quality_log({
        "ts": _utc_now_iso(),
        "kind": "hgly-eval",
        "lane": LANE,
        "run_id": run_id,
        "iter": iter_n,
        "score": score,
        "mode": "placeholder-non-dry",
    })
    _emit(result)
    return 0


# ---------------------------------------------------------------------------
# Subcommand: loop
# ---------------------------------------------------------------------------

def _call_loop_checkpoint_restore(lane: str, run_id: str) -> dict[str, Any]:
    """Compose with loop_checkpoint.py for revert-to-peak."""
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        import loop_checkpoint  # type: ignore
        return loop_checkpoint.restore_best(lane, run_id, str(_sanctum_root()))
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()}


def cmd_loop(args: argparse.Namespace) -> int:
    interval = max(60, int(args.interval_seconds))
    max_iters = int(args.max_iters) if args.max_iters else None
    state = _read_state()
    run_id = args.run_id or state.get("run_id") or _new_run_id()
    state["run_id"] = run_id
    _write_state(state)

    summary = {
        "subcommand": "loop",
        "dry_run": bool(args.dry_run),
        "lane": LANE,
        "run_id": run_id,
        "interval_seconds": interval,
        "max_iters": max_iters,
        "quality_monotonic_loop_ps1": str(_sanctum_root() / "automations" / "quality-monotonic-loop.ps1"),
        "iterations": [],
    }

    i = 0
    while True:
        i += 1
        iter_entry: dict[str, Any] = {"i": i, "utc": _utc_now_iso()}

        # Step 1: train-once
        train_args = argparse.Namespace(
            dry_run=args.dry_run,
            base_model=args.base_model,
            lora_rank=args.lora_rank,
            utilization_cap=args.utilization_cap,
            run_id=run_id,
        )
        # Capture train return code without re-emitting JSON spam in loop mode
        prev_stdout = sys.stdout
        try:
            sys.stdout = open(os.devnull, "w")
            train_rc = cmd_train_once(train_args)
        finally:
            sys.stdout.close()
            sys.stdout = prev_stdout
        iter_entry["train_rc"] = train_rc

        # Step 2: eval
        eval_args = argparse.Namespace(dry_run=args.dry_run, run_id=run_id)
        prev_stdout = sys.stdout
        try:
            sys.stdout = open(os.devnull, "w")
            eval_rc = cmd_eval(eval_args)
        finally:
            sys.stdout.close()
            sys.stdout = prev_stdout
        iter_entry["eval_rc"] = eval_rc

        # Step 3: read latest eval row + compare to best
        state = _read_state()
        latest_score: Optional[float] = None
        log = _quality_log_path()
        if log.exists():
            try:
                with log.open("r", encoding="utf-8") as f:
                    lines = [ln for ln in f.readlines() if ln.strip()]
                for ln in reversed(lines):
                    try:
                        row = json.loads(ln)
                    except Exception:
                        continue
                    if row.get("kind") == "hgly-eval" and row.get("run_id") == run_id:
                        latest_score = float(row.get("score") or 0)
                        break
            except Exception:
                pass
        iter_entry["score"] = latest_score

        best = state.get("best_score")
        if latest_score is not None:
            if best is None or latest_score >= float(best):
                state["best_score"] = latest_score
                state["best_iter"] = state.get("iter")
                _write_state(state)
                iter_entry["action"] = "new-peak"
            else:
                # Regression - revert to peak via loop_checkpoint
                iter_entry["action"] = "regression-revert"
                if not args.dry_run:
                    restore = _call_loop_checkpoint_restore(LANE, run_id)
                    iter_entry["restore"] = restore
                else:
                    iter_entry["restore"] = {"dry_run": True}

        summary["iterations"].append(iter_entry)

        if args.dry_run:
            # In dry-run, run a single iter then exit
            break
        if max_iters and i >= max_iters:
            break
        time.sleep(interval)

    _emit(summary)
    return 0


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    state = _read_state()
    gpu = _probe_torch_cuda()
    result = {
        "subcommand": "status",
        "dry_run": bool(args.dry_run),
        "utc": _utc_now_iso(),
        "lane": LANE,
        "state": state,
        "gpu": gpu,
        "paths": {
            "corpus_dir": str(_corpus_dir()),
            "adapters_dir": str(_adapters_dir()),
            "eval_set": str(_eval_set_path()),
            "quality_log": str(_quality_log_path()),
            "state_file": str(_state_path()),
        },
    }
    _emit(result)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dry-run", action="store_true", help="smoke test without real GPU work")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hgly_trainer",
        description="Continuous LoRA fine-tune trainer for Sinister Hieroglyphics (RTX 4090).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="check 4090 / VRAM / CUDA / torch / unsloth / peft availability")
    _add_common(p_probe)

    p_corpus = sub.add_parser("corpus", help="enumerate hgly-corpus + report size + dedupe stats")
    _add_common(p_corpus)

    p_train = sub.add_parser("train-once", help="run ONE LoRA fine-tune epoch")
    _add_common(p_train)
    p_train.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    p_train.add_argument("--lora-rank", type=int, default=DEFAULT_LORA_RANK)
    p_train.add_argument("--utilization-cap", type=float, default=DEFAULT_UTIL_CAP)
    p_train.add_argument("--run-id", default=None)

    p_eval = sub.add_parser("eval", help="load latest adapter + score against eval set")
    _add_common(p_eval)
    p_eval.add_argument("--run-id", default=None)

    p_loop = sub.add_parser("loop", help="train-once + eval + revert-to-peak on regression, every interval")
    _add_common(p_loop)
    p_loop.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    p_loop.add_argument("--lora-rank", type=int, default=DEFAULT_LORA_RANK)
    p_loop.add_argument("--utilization-cap", type=float, default=DEFAULT_UTIL_CAP)
    p_loop.add_argument("--interval-seconds", type=int, default=DEFAULT_LOOP_INTERVAL_SECONDS)
    p_loop.add_argument("--max-iters", type=int, default=None)
    p_loop.add_argument("--run-id", default=None)

    p_status = sub.add_parser("status", help="emit JSON status snapshot")
    _add_common(p_status)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "probe": cmd_probe,
        "corpus": cmd_corpus,
        "train-once": cmd_train_once,
        "eval": cmd_eval,
        "loop": cmd_loop,
        "status": cmd_status,
    }
    fn = dispatch[args.cmd]
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
