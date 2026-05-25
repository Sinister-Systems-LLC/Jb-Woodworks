"""Iter 112 - K=8 ANGLE brain-corpus sweep (head-to-head vs iter-110 K=4 ZZ-FM).

Author: RKOJ-ELENO :: 2026-05-25

Operator (2026-05-25 01:20Z): "continue working ... really use the python
simulator ... expand on concepts on what we can do with all this".

Direct expansion: iter-110 ran brain self-coherence at K=4 ZZ-FM r=1
(0.067% QBC, max +24.28pp). Iter-44 doctrine says K=8 ANGLE dominates
ZZ-FM r=1 in sim on average (65x more QBC, +1.1pp max advantage). This
iter applies K=8 ANGLE to the post-2026-05-25-surge brain corpus and
compares head-to-head against the iter-110 K=4 baseline.

Why this matters:
  - K=4 has a fundamental Hilbert-space ceiling (16-dim state space).
    Many high-classical triads collapse to near-perfect sim overlap = 0
    quantum advantage.
  - K=8 expands the state space 16x (256-dim). High-classical triads
    that hit the K=4 ceiling get room to discriminate in K=8.
  - If iter-44 doctrine holds at the 200-doc scale, K=8 ANGLE should
    surface MORE QBC triads AND lift max-advantage substantially.

Backend: sim-local (CPU state-vector). Zero cloud burn.

Cost: K=8 ANGLE is FASTER than K=4 ZZ-FM despite the larger state space:
ANGLE state-build is k Kron products (no 2^k x 2^k matrix builds), then
a single dim-256 inner product per pair. Expected <30s for full brain.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

PROJ_ROOT = Path(__file__).resolve().parent
SANCTUM_ROOT = PROJ_ROOT.parent.parent
SERAPHIM_TOOL = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
sys.path.insert(0, str(SERAPHIM_TOOL))

from memory_kernel import find_qbc_triads  # type: ignore


def main() -> int:
    print('[iter112] K=8 ANGLE r=1 full-brain sweep...')
    t0 = time.time()
    result = find_qbc_triads(
        encoding='angle',
        k=8,
        reps=1,
        top_n=20,
        corpus_mode='full',
    )
    wall = time.time() - t0

    out = {
        'schema': 'sinister-seraphim.iter112-k8-angle-brain-sweep.v1',
        'ts_utc_label': 'iter112-2026-05-25',
        'encoding': result['encoding'],
        'k': result['k'],
        'reps': result['reps'],
        'corpus_mode': result['corpus_mode'],
        'pool_size': result['pool_size'],
        'triads_evaluated': result['triads_evaluated'],
        'qbc_count': result['qbc_count'],
        'qbc_pct': result['qbc_pct'],
        'max_advantage': result['max_advantage'],
        'median_advantage': result['median_advantage'],
        'top_20_triads': result['top_n_triads'],
        'wall_seconds': wall,
        'iter110_baseline_for_comparison': {
            'encoding': 'zzfm',
            'k': 4,
            'reps': 1,
            'docs_used': 200,
            'triads_evaluated': 1313400,
            'qbc_count': 875,
            'qbc_pct': 0.0666,
            'max_advantage_pp': 24.28,
            'median_advantage_pp': -41.47,
            'wall_seconds': 30.0,
        },
    }

    out_path = PROJ_ROOT / 'outputs' / 'iter112-k8-angle-brain-sweep.json'
    out_path.write_text(json.dumps(out, indent=2))

    print(f'[iter112] DONE wall={wall:.1f}s')
    print(f'  pool_size={result["pool_size"]}  triads={result["triads_evaluated"]}')
    print(f'  QBC count={result["qbc_count"]}  pct={result["qbc_pct"]:.4f}%')
    print(f'  max_adv={result["max_advantage"]*100:+.2f}pp  median={result["median_advantage"]*100:+.2f}pp')
    print(f'[saved] {out_path}')

    base = out['iter110_baseline_for_comparison']
    print()
    print('--- Head-to-head vs iter-110 K=4 ZZ-FM r=1 baseline ---')
    print(f'  QBC count:  K=4 zzfm = {base["qbc_count"]}   K=8 angle = {result["qbc_count"]}   ratio = {result["qbc_count"]/max(base["qbc_count"],1):.2f}x')
    print(f'  QBC pct:    K=4 zzfm = {base["qbc_pct"]:.4f}%   K=8 angle = {result["qbc_pct"]:.4f}%')
    print(f'  Max adv:    K=4 zzfm = {base["max_advantage_pp"]:+.2f}pp   K=8 angle = {result["max_advantage"]*100:+.2f}pp')

    return 0


if __name__ == '__main__':
    sys.exit(main())
