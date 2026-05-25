#!/usr/bin/env python3
"""Sinister Sanctum — Quantum probe (10-second hard cap).

Author: RKOJ-ELENO :: 2026-05-24

Runs `seraphim audit --variant zzfm-r1 --sim-only --corpus full` with a strict
10-second wall-clock budget and emits a compact JSON result suitable for
downstream consumers (chatbot reply-entropy seeder, smoke-test harness,
operator dashboards). Sim-only by design — never burns the WK_C180 cloud
budget on a fast smoke probe.

Usage:
  python automations/quantum-probe-10s.py                 # human-readable
  python automations/quantum-probe-10s.py --json          # machine-readable

Operator directive (verbatim 2026-05-24): "for starting NOW, i want you to
get a test up to run the quantum tools from sinister quantum. with a 10
second cap to help with everything i said above."
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SANCTUM_ROOT = Path(__file__).resolve().parent.parent
SERAPHIM_DIR = SANCTUM_ROOT / "tools" / "sinister-seraphim"
DEFAULT_VARIANT = "zzfm-r1"
HARD_CAP_SECONDS = 10


def run_probe(variant: str, cap: int) -> dict:
    cli = SERAPHIM_DIR / "cli.py"
    if not cli.exists():
        return {"ok": False, "error": f"seraphim CLI not found at {cli}", "variant": variant}

    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, str(cli), "audit", "--variant", variant, "--sim-only", "--corpus", "full"],
            cwd=str(SERAPHIM_DIR),
            capture_output=True,
            text=True,
            timeout=cap,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": f"timeout after {cap}s",
            "variant": variant,
            "elapsed_s": round(time.monotonic() - started, 3),
        }

    elapsed = round(time.monotonic() - started, 3)
    out = proc.stdout or ""

    # Parse the human-readable audit output. Pattern (verified 2026-05-24):
    #   variant=<v>  (...)
    #     triad: a.md, b.md, c.md
    #     classical off-diag mean: <float>
    #     sim off-diag mean:       <float>    Δ vs classical = +<float>
    #     real-QPU:                skipped (--sim-only)
    triad_m = re.search(r"triad:\s*([^\n]+)", out)
    classical_m = re.search(r"classical off-diag mean:\s*([\d.]+)", out)
    sim_m = re.search(r"sim off-diag mean:\s*([\d.]+)", out)
    # Δ symbol gets mojibake'd on Windows cp1252 stdout — match the suffix only.
    delta_m = re.search(r"vs classical\s*=\s*([+\-][\d.]+)", out)

    result = {
        "ok": proc.returncode == 0 and classical_m is not None and sim_m is not None,
        "variant": variant,
        "elapsed_s": elapsed,
        "cap_s": cap,
        "exit_code": proc.returncode,
        "triad": [t.strip() for t in triad_m.group(1).split(",")] if triad_m else [],
        "classical_offdiag_mean": float(classical_m.group(1)) if classical_m else None,
        "sim_offdiag_mean": float(sim_m.group(1)) if sim_m else None,
        "sim_vs_classical_delta": float(delta_m.group(1)) if delta_m else None,
        "raw_tail": out.strip().splitlines()[-6:] if out else [],
    }
    if proc.returncode != 0 and proc.stderr:
        result["stderr_tail"] = proc.stderr.strip().splitlines()[-6:]
    return result


def main() -> int:
    p = argparse.ArgumentParser(description="Sinister quantum probe (10s capped sim audit)")
    p.add_argument("--variant", default=DEFAULT_VARIANT)
    p.add_argument("--cap", type=int, default=HARD_CAP_SECONDS, help="wall-clock cap in seconds")
    p.add_argument("--json", action="store_true", help="emit JSON only")
    args = p.parse_args()

    res = run_probe(args.variant, args.cap)

    if args.json:
        print(json.dumps(res, separators=(",", ":")))
        return 0 if res.get("ok") else 1

    print(f"[quantum-probe-10s] variant={res['variant']} elapsed={res['elapsed_s']}s cap={res['cap_s']}s")
    if res.get("ok"):
        print(f"  triad: {', '.join(res['triad'])}")
        print(f"  classical off-diag mean: {res['classical_offdiag_mean']}")
        delta = res.get("sim_vs_classical_delta")
        delta_str = f"{delta:+}" if delta is not None else "n/a"
        print(f"  sim off-diag mean:       {res['sim_offdiag_mean']}   delta = {delta_str}")
        print(f"  exit=0 OK")
        return 0
    print(f"  FAIL — {res.get('error', 'unknown')}")
    if "stderr_tail" in res:
        for line in res["stderr_tail"]:
            print(f"  stderr> {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
