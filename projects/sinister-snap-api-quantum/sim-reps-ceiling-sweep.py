"""Sim-only reps-sweep: characterize the ZZ-FM ceiling without cloud burn.

Author: RKOJ-ELENO :: 2026-05-24

Empirical chain so far has established:
  - r=1 (depth 34): real-QPU 25-35pp advantage (5 verified runs, mean 31pp)
  - r=2 (depth 68): real-QPU saturates near classical (noise wall)
  - r=3, r=4, ...: never characterized (real-QPU would saturate worse;
                   sim ceiling unknown)

This script measures sim off-diagonal mean at r=1..6 on the new top-QBC triad
(branch-contention + index-storm + verify-head) using the same 129-doc pool
TF-IDF the production `seraphim find-qbc` uses. The minimum sim value =
the maximum theoretical quantum advantage = what a future error-mitigated
or noise-free quantum kernel could achieve.

Zero cloud burn. Results written to outputs/sim-reps-ceiling-sweep.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJ_ROOT = Path(__file__).resolve().parent
SANCTUM_ROOT = PROJ_ROOT.parent.parent
SERAPHIM_TOOL = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
sys.path.insert(0, str(SERAPHIM_TOOL))

from memory_kernel import run_kernel_audit  # type: ignore

TRIAD = [
    'multi-agent-branch-contention-isolation-pattern.md',
    'multi-agent-git-index-contention-storm-2026-05-23.md',
    'verify-head-before-commit-multi-agent.md',
]

# Reuse find-qbc pool semantics (same 129-doc set; we re-derive from disk)
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
POOL = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
print(f'[sweep] pool size: {len(POOL)} docs')

REPS_VALUES = [1, 2, 3, 4, 5, 6]
results = []

for reps in REPS_VALUES:
    t0 = time.time()
    r = run_kernel_audit(
        encoding='zzfm',
        k=4,
        reps=reps,
        triad=TRIAD,
        corpus=POOL,
        sim_only=True,
    )
    dt = time.time() - t0
    row = {
        'reps': reps,
        'depth_est': 2 + reps * 8 + reps * 6 * 3,  # rough: H + RZ + 3*(CNOT,RZ,CNOT) per rep
        'classical_off_diag': r['classical_off_diag_mean'],
        'sim_off_diag': r['sim_off_diag_mean'],
        'sim_advantage_pp': (r['classical_off_diag_mean'] - r['sim_off_diag_mean']) * 100,
        'wall_seconds': round(dt, 3),
    }
    results.append(row)
    print(f"  r={reps}  sim={r['sim_off_diag_mean']:.4f}  classical={r['classical_off_diag_mean']:.4f}  "
          f"adv={row['sim_advantage_pp']:.2f}pp  ({dt:.2f}s)")

# Find ceiling
best = max(results, key=lambda x: x['sim_advantage_pp'])
print(f"\n[sweep] sim ceiling: r={best['reps']}  adv={best['sim_advantage_pp']:.2f}pp  "
      f"(sim={best['sim_off_diag']:.4f})")

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'sim-reps-ceiling-sweep.json'
OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.sim-reps-sweep.v1',
    'triad': TRIAD,
    'pool_size': len(POOL),
    'encoding': 'zzfm',
    'k': 4,
    'reps_swept': REPS_VALUES,
    'rows': results,
    'sim_ceiling': best,
    'note': 'Sim-only characterization of the ZZ-FM reps ceiling. Real-QPU '
            'at r>=2 saturates near classical baseline (noise wall) per '
            'iter-32 empirical anchor — but a future error-mitigated quantum '
            'kernel could realize the sim values here.',
}, indent=2), encoding='utf-8')
print(f'[sweep] wrote {OUT}')
