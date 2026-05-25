#!/usr/bin/env python3
"""gpu_bot_fleet.py -- route bot/agent inference to the local 4090 via Ollama.

Author: RKOJ-ELENO :: 2026-05-25
Operator hard-canonical 2026-05-25 ~07:00Z (verbatim):
    "make sure you get the rate limiting in check and we can run all agents
     with no issues. add things like when i launch a agent it balances it out
     over the other claude account we have or use more hardware like i said
     to do. i have a 4090 we need to be using that."

What it does:
    Detects the local NVIDIA 4090 (or any CUDA GPU) and a locally-running
    Ollama server, then provides a thin routing surface so other Sanctum
    automations (account_balancer, launch_rate_limit_governor, EVE.exe
    Settings) can offload tasks to local inference instead of burning Max-20x
    Claude quota.

Composes with:
    automations/account_balancer.py            -- consumes --route when usage hot
    automations/launch_rate_limit_governor.py  -- pre-spawn gate that may
                                                  recommend gpu-bot routing
    automations/resource_quota_governor.py     -- ensures Ollama doesn't
                                                  starve operator's interactive cores
    _shared-memory/knowledge/bot-fleet-quick-reference.md  -- existing local bots
    _shared-memory/gpu-bot-fleet-log.jsonl     -- audit log

Doctrine binding:
    NO new .bat / NO new .ps1 (operator 2026-05-25T02:45Z).
    Author RKOJ-ELENO header (operator 2026-05-21).
    Operator clicks nothing (operator 2026-05-25 ~02:55Z) -- --install-ollama
    will attempt winget directly, never surface "please run" prompts.
    We have the source: this file reads Ollama via HTTP only, no shell scrape.

CLI:
    --status                  print GPU + Ollama + bot-fleet state (always exit 0)
    --health                  exit 0 if GPU+Ollama healthy, 1 with diagnostic else
    --route <task-name>       route a stdin-piped prompt to local Ollama
    --model <name>            override default model (else auto-pick first available)
    --install-ollama          attempt winget install Ollama.Ollama (best-effort)
    --json                    structured output (paired with --status / --health)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SANCTUM_ROOT = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
LOG_FILE = SANCTUM_ROOT / "_shared-memory" / "gpu-bot-fleet-log.jsonl"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL_PREFS = [
    "llama3.1:8b",
    "llama3.1:8b-instruct",
    "llama3:8b",
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
    "mistral:7b",
    "phi3:medium",
]
REQUEST_TIMEOUT_S = 60


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        event = {"ts": utc_now_iso(), **event}
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # logging failures are NEVER fatal for a routing tool
        pass


def detect_gpu() -> dict:
    """Return GPU info dict; empty dict if nvidia-smi unavailable."""
    smi = shutil.which("nvidia-smi")
    if not smi:
        return {"present": False, "reason": "nvidia-smi not on PATH"}
    try:
        proc = subprocess.run(
            [
                smi,
                "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"present": False, "reason": f"nvidia-smi failed: {exc}"}
    if proc.returncode != 0:
        return {"present": False, "reason": f"nvidia-smi rc={proc.returncode}: {proc.stderr.strip()}"}
    gpus = []
    for line in proc.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        name, mem_total, mem_used, util = parts[0], parts[1], parts[2], parts[3]
        try:
            mem_total_mb = int(float(mem_total))
            mem_used_mb = int(float(mem_used))
            util_pct = int(float(util))
        except ValueError:
            continue
        gpus.append(
            {
                "name": name,
                "memory_total_mb": mem_total_mb,
                "memory_used_mb": mem_used_mb,
                "memory_free_mb": mem_total_mb - mem_used_mb,
                "utilization_pct": util_pct,
                "is_4090": "4090" in name,
            }
        )
    return {"present": bool(gpus), "gpus": gpus}


def _http_get(url: str, timeout: int = 5) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, str(exc)


def _http_post(url: str, body: dict, timeout: int = REQUEST_TIMEOUT_S) -> tuple[int, str]:
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method="POST", headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return 0, str(exc)


def detect_ollama() -> dict:
    status, body = _http_get(f"{OLLAMA_URL}/api/tags", timeout=4)
    if status == 0:
        return {"reachable": False, "url": OLLAMA_URL, "reason": body}
    if status != 200:
        return {"reachable": False, "url": OLLAMA_URL, "reason": f"HTTP {status}: {body[:200]}"}
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return {"reachable": True, "url": OLLAMA_URL, "models": [], "reason": "non-json response"}
    models = []
    for m in payload.get("models", []) or []:
        models.append(
            {
                "name": m.get("name"),
                "size_gb": round((m.get("size") or 0) / (1024**3), 2),
                "modified_at": m.get("modified_at"),
            }
        )
    return {"reachable": True, "url": OLLAMA_URL, "models": models}


def pick_default_model(available: list[str]) -> str | None:
    if not available:
        return None
    for pref in DEFAULT_MODEL_PREFS:
        for name in available:
            if name == pref or name.startswith(pref + "-") or name.startswith(pref):
                return name
    return available[0]


def cmd_status(json_out: bool) -> int:
    gpu = detect_gpu()
    ollama = detect_ollama()
    available_models = [m["name"] for m in ollama.get("models", []) if m.get("name")]
    default_model = pick_default_model(available_models)
    state = {
        "gpu": gpu,
        "ollama": ollama,
        "default_model": default_model,
        "log_file": str(LOG_FILE),
        "ollama_url": OLLAMA_URL,
    }
    if json_out:
        print(json.dumps(state, indent=2))
        return 0
    print("=== gpu_bot_fleet status ===")
    if gpu.get("present"):
        for g in gpu.get("gpus", []):
            tag = " [4090]" if g.get("is_4090") else ""
            print(
                f"GPU{tag}: {g['name']} | mem {g['memory_used_mb']}/{g['memory_total_mb']} MB"
                f" | util {g['utilization_pct']}%"
            )
    else:
        print(f"GPU: NOT DETECTED ({gpu.get('reason', 'unknown')})")
    if ollama.get("reachable"):
        print(f"Ollama: reachable at {OLLAMA_URL} | models={len(available_models)}")
        for m in ollama.get("models", []):
            print(f"  - {m['name']} ({m['size_gb']} GB)")
        if not available_models:
            print("  (no models pulled -- operator can: ollama pull llama3.1:8b)")
    else:
        print(f"Ollama: UNREACHABLE at {OLLAMA_URL} ({ollama.get('reason', 'unknown')})")
    print(f"Default model: {default_model or '(none available)'}")
    return 0


def cmd_health(json_out: bool) -> int:
    gpu = detect_gpu()
    ollama = detect_ollama()
    healthy = bool(gpu.get("present")) and bool(ollama.get("reachable"))
    diagnostic = []
    if not gpu.get("present"):
        diagnostic.append(f"gpu-unavailable: {gpu.get('reason', 'unknown')}")
    if not ollama.get("reachable"):
        diagnostic.append(
            f"ollama-unreachable: run winget install Ollama.Ollama "
            f"(detail: {ollama.get('reason', 'unknown')})"
        )
    elif not ollama.get("models"):
        diagnostic.append("no-models-pulled: run ollama pull llama3.1:8b")
        healthy = False
    payload = {
        "healthy": healthy,
        "gpu_ok": bool(gpu.get("present")),
        "ollama_ok": bool(ollama.get("reachable")),
        "models_ok": bool(ollama.get("models")),
        "diagnostic": diagnostic,
    }
    if json_out:
        print(json.dumps(payload, indent=2))
    else:
        print("HEALTHY" if healthy else "UNHEALTHY")
        for d in diagnostic:
            print(f"  - {d}")
    return 0 if healthy else 1


def cmd_route(task_name: str, model: str | None, json_out: bool) -> int:
    prompt = sys.stdin.read().strip()
    if not prompt:
        print("route: no prompt on stdin", file=sys.stderr)
        return 2
    ollama = detect_ollama()
    if not ollama.get("reachable"):
        print(f"route: ollama unreachable ({ollama.get('reason')})", file=sys.stderr)
        log_event(
            {
                "event": "route_failed",
                "task": task_name,
                "reason": "ollama-unreachable",
                "detail": ollama.get("reason"),
            }
        )
        return 3
    available = [m["name"] for m in ollama.get("models", [])]
    chosen = model or pick_default_model(available)
    if not chosen:
        print("route: no models available -- pull one with `ollama pull llama3.1:8b`", file=sys.stderr)
        log_event({"event": "route_failed", "task": task_name, "reason": "no-models"})
        return 4
    if model and model not in available:
        print(f"route: requested model {model} not in {available}", file=sys.stderr)
        log_event(
            {"event": "route_failed", "task": task_name, "reason": "model-not-pulled", "model": model}
        )
        return 5
    body = {"model": chosen, "prompt": prompt, "stream": False}
    started = time.time()
    status, resp_body = _http_post(f"{OLLAMA_URL}/api/generate", body, timeout=REQUEST_TIMEOUT_S)
    duration_s = round(time.time() - started, 2)
    if status != 200:
        print(f"route: ollama HTTP {status}: {resp_body[:300]}", file=sys.stderr)
        log_event(
            {
                "event": "route_failed",
                "task": task_name,
                "reason": "ollama-http-error",
                "status": status,
                "duration_s": duration_s,
            }
        )
        return 6
    try:
        payload = json.loads(resp_body)
    except json.JSONDecodeError:
        print(f"route: non-json ollama response: {resp_body[:300]}", file=sys.stderr)
        return 7
    response_text = payload.get("response", "")
    prompt_tok = payload.get("prompt_eval_count")
    gen_tok = payload.get("eval_count")
    log_event(
        {
            "event": "routed",
            "task": task_name,
            "model": chosen,
            "duration_s": duration_s,
            "prompt_tokens": prompt_tok,
            "response_tokens": gen_tok,
        }
    )
    if json_out:
        print(
            json.dumps(
                {
                    "model": chosen,
                    "response": response_text,
                    "duration_s": duration_s,
                    "prompt_tokens": prompt_tok,
                    "response_tokens": gen_tok,
                },
                indent=2,
            )
        )
    else:
        print(response_text)
    return 0


def cmd_install_ollama() -> int:
    """Best-effort install via winget. Operator clicks nothing per doctrine."""
    winget = shutil.which("winget")
    if not winget:
        print("install-ollama: winget not on PATH; cannot auto-install", file=sys.stderr)
        log_event({"event": "install_skipped", "reason": "no-winget"})
        return 2
    print("install-ollama: invoking `winget install Ollama.Ollama --silent --accept-source-agreements --accept-package-agreements`")
    proc = subprocess.run(
        [
            winget,
            "install",
            "Ollama.Ollama",
            "--silent",
            "--accept-source-agreements",
            "--accept-package-agreements",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
    log_event({"event": "install_attempted", "rc": proc.returncode})
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="GPU bot fleet router (Ollama + 4090)")
    p.add_argument("--status", action="store_true", help="print GPU + Ollama state")
    p.add_argument("--health", action="store_true", help="exit 0 if healthy else 1")
    p.add_argument("--route", metavar="TASK_NAME", help="route stdin prompt to local Ollama")
    p.add_argument("--model", help="override default model")
    p.add_argument("--install-ollama", action="store_true", help="best-effort winget install")
    p.add_argument("--json", action="store_true", help="structured output")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.install_ollama:
        return cmd_install_ollama()
    if args.route:
        return cmd_route(args.route, args.model, args.json)
    if args.health:
        return cmd_health(args.json)
    # default to --status
    return cmd_status(args.json)


if __name__ == "__main__":
    sys.exit(main())
