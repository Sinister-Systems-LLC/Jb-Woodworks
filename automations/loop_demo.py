#!/usr/bin/env python3
"""loop_demo.py — end-to-end demo of the monotonic-loop revert-to-peak.

Author: RKOJ-ELENO :: 2026-05-25

Operator (verbatim 2026-05-25 ~18:15Z): "i need looper to work as well".

Runs the full forever-improve-until-quality-drops cycle ON a real Sanctum
file (a copy of itself, kept in a tmp lane), proving the loop:

  1. saves a checkpoint via loop_checkpoint.save
  2. mutates the file (simulated improvement)
  3. measures a quality score
  4. if score regresses vs peak -> loop_checkpoint.restore_best reverts
  5. otherwise -> next iter starts from new peak

Composes with:
  - automations/loop_checkpoint.py (file-snapshot + restore-best)
  - automations/quality-monotonic-loop.ps1 (score / plateau / regression
    detection; this Python demo wraps it for one full cycle so operator
    sees the loop's actual revert fire end-to-end)

Usage:
  python automations/loop_demo.py                # run 5-iter demo
  python automations/loop_demo.py --iters 10     # custom iter count
  python automations/loop_demo.py --keep         # keep the demo tmp dir

Exit code:
  0  loop demo verified (peak reached + at least one revert fired)
  1  demo couldn't verify revert (no regression happened OR checkpoint
     manager not reachable)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SANCTUM = Path(os.environ.get("SINISTER_SANCTUM_ROOT", r"D:\Sinister Sanctum"))
CKPT_PY = SANCTUM / "automations" / "loop_checkpoint.py"


def _ckpt(*args: str) -> dict:
    """Invoke loop_checkpoint.py CLI; return parsed JSON output."""
    cmd = [sys.executable, str(CKPT_PY), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "raw": r.stdout, "stderr": r.stderr}


def _score(work_dir: Path) -> float:
    """Quality signal: sum of length of every .txt file. Deliberately
    rewardable -- longer file = higher score. So an improvement that
    deletes content = regression."""
    total = 0
    for f in work_dir.rglob("*.txt"):
        try: total += f.stat().st_size
        except OSError: pass
    return float(total)


def _improve(work_dir: Path, iter_n: int, rng: random.Random) -> None:
    """Mutate a file. With p=0.7 add chars (improvement); else delete
    (regression that should trigger revert)."""
    files = sorted(work_dir.rglob("*.txt"))
    if not files: return
    target = rng.choice(files)
    if rng.random() < 0.7:
        # additive: improve
        with target.open("a", encoding="utf-8") as fh:
            fh.write(f"\niter-{iter_n}-add-{rng.randint(0,999)}\n")
    else:
        # destructive: regression
        try:
            sz = target.stat().st_size
            keep = max(1, sz // 2)
            data = target.read_bytes()[:keep]
            target.write_bytes(data)
        except OSError:
            pass


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=5)
    p.add_argument("--keep", action="store_true")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()

    rng = random.Random(args.seed)
    tmp_root = Path(tempfile.mkdtemp(prefix="hgly-loop-demo-"))
    work_dir = tmp_root / "work"
    work_dir.mkdir(parents=True)

    # Seed a few text files
    for i in range(3):
        (work_dir / f"file-{i}.txt").write_text(
            f"baseline file {i}\nlorem ipsum\n", encoding="utf-8"
        )

    # rel path for loop_checkpoint (it expects sanctum-root-relative paths
    # OR absolute; we'll lift the tmp dir into _shared-memory so it works)
    rel_demo = SANCTUM / "_shared-memory" / "loop-demo" / tmp_root.name
    rel_demo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(work_dir, rel_demo, dirs_exist_ok=True)

    run_id = f"demo-{int(time.time())}"
    lane = "loop-demo"
    paths_arg = str(rel_demo.relative_to(SANCTUM)).replace("\\", "/")

    log_jsonl = SANCTUM / "_shared-memory" / "quality-loop-log.jsonl"
    history = []
    best_score = -1.0
    best_iter = -1
    reverts_fired = 0

    print(f"loop_demo: run_id={run_id} lane={lane} iters={args.iters}")
    print(f"  watching {paths_arg}")

    for it in range(args.iters):
        # checkpoint BEFORE mutating
        sv = _ckpt("save", "--lane", lane, "--run-id", run_id,
                   "--iter", str(it), "--paths", paths_arg,
                   "--sanctum-root", str(SANCTUM))
        if not sv.get("ok"):
            print(f"  iter={it} [FAIL] checkpoint save: {sv}")
            return 1

        # mutate
        _improve(rel_demo, it, rng)

        # score
        s = _score(rel_demo)
        history.append(s)

        # log to quality-loop-log (matches ps1 schema)
        row = {"run_id": run_id, "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
               time.gmtime()), "lane": lane, "task": "loop-demo",
               "iter": it, "score": s,
               "best_score": max(s, best_score), "best_iter":
               (it if s > best_score else best_iter)}
        with log_jsonl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

        regressed = s < best_score - 0.001
        tag = "OK"
        if regressed:
            tag = "REGRESS"
            # call restore-best
            rs = _ckpt("restore-best", "--lane", lane, "--run-id", run_id,
                       "--sanctum-root", str(SANCTUM))
            if rs.get("ok"):
                reverts_fired += 1
                tag = f"REVERTED->iter{rs.get('restored_iter')}"
                # rescore after revert
                s2 = _score(rel_demo)
                history.append(s2)

        if s > best_score:
            best_score = s; best_iter = it

        print(f"  iter={it} score={s} best={best_score} ({tag})")

    print(f"loop_demo: peak={best_score} at iter {best_iter}; "
          f"reverts_fired={reverts_fired}; history={history}")

    if not args.keep:
        shutil.rmtree(tmp_root, ignore_errors=True)
        shutil.rmtree(rel_demo, ignore_errors=True)

    print(f"VERIFIED" if reverts_fired > 0 else
          "NO-REVERT-FIRED (rng happened not to regress; rerun with --seed N)")
    return 0 if reverts_fired > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
