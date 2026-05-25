"""Iter 113 - Reps-ceiling sweep on brain top-20 triads.

Author: RKOJ-ELENO :: 2026-05-25

Demonstrates concept #3 from python-simulator-concepts-expansion.md:
'systematically sweep r in {1..5} on the brain corpus, find r* per triad,
ask if r* values are clustered by doctrine family'.

Uses find_qbc_triads(ceiling_reps=...) — already supported by memory_kernel.
Re-uses ZZ-FM K=4 (the iter-110 baseline) so reps are the only varying axis.

Output:
  - per-triad ceiling_pp, ceiling_rep (the r* that maximizes QBC advantage)
  - headroom_pp (ceiling_pp - base_advantage_pp at r=1)
  - cluster the top-20 by r* to see if certain semantic families prefer
    deeper circuits
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
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
    print('[iter113] reps-ceiling sweep r in {1,2,3} K=4 ZZ-FM top-20...')
    t0 = time.time()
    result = find_qbc_triads(
        encoding='zzfm',
        k=4,
        reps=1,
        top_n=20,
        corpus_mode='full',
        ceiling_reps=[2, 3],
    )
    wall = time.time() - t0

    triads = result['top_n_triads']

    rstar_counter: Counter[int] = Counter(int(t['ceiling_rep']) for t in triads if 'ceiling_rep' in t)
    headroom_max = max((t.get('headroom_pp', 0) for t in triads), default=0)
    headroom_med = sorted(t.get('headroom_pp', 0) for t in triads)[len(triads) // 2] if triads else 0

    out = {
        'schema': 'sinister-seraphim.iter113-reps-ceiling-sweep.v1',
        'ts_utc_label': 'iter113-2026-05-25',
        'encoding': 'zzfm',
        'k': 4,
        'reps_swept': [1, 2, 3],
        'corpus_mode': 'full',
        'pool_size': result['pool_size'],
        'top_20_triads': triads,
        'rstar_distribution': dict(rstar_counter),
        'headroom_max_pp': headroom_max,
        'headroom_median_pp': headroom_med,
        'wall_seconds': wall,
    }

    out_path = PROJ_ROOT / 'outputs' / 'iter113-reps-ceiling-sweep.json'
    out_path.write_text(json.dumps(out, indent=2))

    print(f'[iter113] DONE wall={wall:.1f}s')
    print(f'  pool_size={result["pool_size"]}')
    print(f'  r* distribution across top-20 triads:')
    for r in sorted(rstar_counter):
        print(f'    r* = {r}: {rstar_counter[r]} triads')
    print(f'  Max headroom (pp): {headroom_max:.2f}')
    print(f'  Median headroom (pp): {headroom_med:.2f}')
    print()
    print('Top-5 triads by ceiling_pp (r* + headroom_pp):')
    by_ceiling = sorted(triads, key=lambda t: t.get('ceiling_pp', 0), reverse=True)[:5]
    for t in by_ceiling:
        files = [Path(x).name for x in t['docs']]
        print(f'  ceiling={t.get("ceiling_pp",0):+.2f}pp at r*={t.get("ceiling_rep")} '
              f'(base_adv={t["advantage"]*100:+.2f}pp, headroom=+{t.get("headroom_pp",0):.2f}pp)')
        for f in files: print(f'        {f}')
    print(f'[saved] {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
