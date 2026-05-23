"""Real-QPU audit of the algorithmically-selected optimal triad.

Author: RKOJ-ELENO :: 2026-05-23

The find-optimal-triad.py search identified the rank-1 triad with sim K=4
ANGLE off-diag mean 0.1356 (vs canonical Snap-RE 0.8975 — a 6.6x reduction).
This script verifies the prediction on real WK_C180.

Rank-1 triad:
  - forge-memory-usage-2026-05-23.md (Sinister Forge memory work)
  - panel-command-center-18-wave-sweep-2026-05-21.md (Sinister Panel command-center)
  - sibling-active-launch-coordination-pattern.md (cross-agent launch coordination)

All three are multi-agent-coordination focused but from DIFFERENT lanes.
Classical TF-IDF off-diag = 0.0820 (very orthogonal). Sim K=4 ANGLE = 0.1356.

Predicted real-QPU range based on prior K=4 depth-8 noise observations:
  - Canonical Snap-RE: Δ=+0.058 → real = 0.1356 + 0.058 = ~0.194
  - Medium-doctrine: Δ=-0.010 → real = 0.1356 - 0.010 = ~0.126
  - Either way, real-QPU should land in [0.08, 0.20] — above noise floor 0.0625,
    showing genuine quantum-kernel discrimination on real hardware.

ASCII-only output (no Unicode crash risk on Windows cp1252 stdout).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
SERAPHIM_DIR = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
if str(SERAPHIM_DIR) not in sys.path:
    sys.path.insert(0, str(SERAPHIM_DIR))

import memory_kernel  # type: ignore  # noqa: E402

OPTIMAL_TRIAD = [
    'forge-memory-usage-2026-05-23.md',
    'panel-command-center-18-wave-sweep-2026-05-21.md',
    'sibling-active-launch-coordination-pattern.md',
]


def main() -> int:
    print('=' * 76)
    print(' Sinister Seraphim :: rank-1 optimal-triad real-QPU verification')
    print('=' * 76)
    print(' Triad:')
    for f in OPTIMAL_TRIAD:
        print(f'   {f}')
    print(' Predicted sim K=4 ANGLE off-diag mean: 0.1356')
    print(' Predicted real-QPU range: [0.08, 0.20] based on prior depth-8 noise')
    print()

    r = memory_kernel.run_kernel_audit(
        encoding='angle', k=4, reps=1, shots=256,
        triad=OPTIMAL_TRIAD,
        sim_only=False,
        pair_loop_cap_seconds=60.0,
        per_pair_stall_seconds=60.0,
    )

    # ALWAYS save JSON FIRST (avoid the medium-doctrine v2 Unicode-print-crash pattern)
    out = SANCTUM_ROOT / 'projects' / 'sinister-snap-api-quantum' / 'outputs' / 'optimal-triad-real-qpu-audit.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(r, f, indent=2, ensure_ascii=False)
    print(f' [SAVED FIRST] {out}')

    # Then print summary (ASCII-only — no Unicode)
    print()
    print(f' classical off-diag mean: {r["classical_off_diag_mean"]:.4f}')
    print(f' sim K=4 ANGLE off-diag:  {r["sim_off_diag_mean"]:.4f}')
    rq = r['real_qpu_off_diag_mean']
    if rq is not None:
        print(f' real-QPU off-diag mean:  {rq:.4f}')
        print(f'   delta real vs sim:     {rq - r["sim_off_diag_mean"]:+.4f}')
        print(f'   delta real vs class:   {rq - r["classical_off_diag_mean"]:+.4f}')
    else:
        print(f' real-QPU: aborted ({r["abort_reason"]})')
    print(f' connect+setup wall:      {r.get("connect_setup_wall_seconds", "n/a")}s')
    print(f' pair-loop wall:          {r["pair_loop_wall_seconds"]}s')
    print()
    print(' Pair-by-pair:')
    for p in r['pair_results']:
        ov = p.get('overlap')
        ov_s = f'{ov:.4f}' if ov is not None else 'STALLED'
        print(f'   ({p["i"]},{p["j"]}) overlap={ov_s}  wall={p["wall_seconds"]}s  job={p["job_id"]}')
    print(f' budget remaining: {r["budget_remaining_after"]:.3f}s')

    # Verdict
    print()
    print(' --- Verdict ---')
    noise_floor = 1 / 16
    if rq is not None:
        if rq > 0.4:
            print(' WARN: real-QPU above 0.4 - unexpected; sim said 0.1356 plateau should be much lower.')
        elif rq < noise_floor + 0.02:
            print(f' WARN: real-QPU at noise floor ({noise_floor:.4f}) - signal may be lost to decoherence.')
        elif abs(rq - r['sim_off_diag_mean']) < 0.10:
            print(f' SUCCESS: real-QPU within 10pp of sim - encoding signal SURVIVES and discriminates.')
        else:
            print(f' MIXED: real-QPU between noise and sim - some signal, some noise.')
    print('=' * 76)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
