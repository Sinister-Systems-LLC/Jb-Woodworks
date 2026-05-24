"""Iter 40 conjecture test: classical baseline -> sim headroom correlation.

Author: RKOJ-ELENO :: 2026-05-24

Iter 39 produced a 3-point trend suggesting that higher classical TF-IDF
baseline correlates with more sim headroom above r=1. Three data points
isn't statistically meaningful — this script extends to 12 triads
spanning the full classical range observed in top-50 QBC (0.16 to 0.58).

Method:
  - Load outputs/top50-qbc.json (produced by `seraphim find-qbc --top-n 50`)
  - Select 12 triads at varied classical percentiles
  - Sweep r=1..6 sim for each
  - Compute headroom (= ceiling_pp - r1_pp) per triad
  - Tabulate + compute Pearson correlation between classical and headroom

Zero cloud burn. Output: outputs/conjecture-classical-vs-headroom.json
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

from memory_kernel import run_kernel_audit  # type: ignore

# Reuse find-qbc pool semantics
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
POOL = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
print(f'[conjecture] pool size: {len(POOL)} docs')

# Load top-50 dump
top50 = json.load(open(PROJ_ROOT / 'outputs' / 'top50-qbc.json', encoding='utf-8'))
triads_all = top50['top_n_triads']

# Sort by classical and pick 12 spanning the range
triads_sorted = sorted(triads_all, key=lambda t: t['classical_off_diag_mean'])
# Pick at percentiles 0%, 9%, 18%, ..., 100% (12 evenly-spaced points)
n_picks = 12
idxs = [round(i * (len(triads_sorted) - 1) / (n_picks - 1)) for i in range(n_picks)]
selected = [triads_sorted[i] for i in idxs]

print(f'[conjecture] selected {len(selected)} triads at classical percentiles 0,9,...,100')
for t in selected:
    print(f"  cls={t['classical_off_diag_mean']:.4f}  sim(r1)={t['sim_off_diag_mean']:.4f}  "
          f"adv={t['advantage']*100:.2f}pp  rank={t['rank']}")

REPS_VALUES = [1, 2, 3, 4, 5, 6]
results = []

print('\n[conjecture] sweeping...')
t_total_0 = time.time()
for picked in selected:
    triad = picked['docs']
    rows = []
    for reps in REPS_VALUES:
        r = run_kernel_audit(
            encoding='zzfm',
            k=4,
            reps=reps,
            triad=triad,
            corpus=POOL,
            sim_only=True,
        )
        rows.append({
            'reps': reps,
            'classical': r['classical_off_diag_mean'],
            'sim': r['sim_off_diag_mean'],
            'adv_pp': (r['classical_off_diag_mean'] - r['sim_off_diag_mean']) * 100,
        })
    classical = rows[0]['classical']
    r1_adv = rows[0]['adv_pp']
    best = max(rows, key=lambda x: x['adv_pp'])
    ceiling_pp = best['adv_pp']
    ceiling_rep = best['reps']
    headroom_pp = ceiling_pp - r1_adv
    pct_at_r1 = r1_adv / ceiling_pp * 100 if ceiling_pp > 0 else float('nan')
    results.append({
        'rank': picked['rank'],
        'classical': classical,
        'r1_adv_pp': r1_adv,
        'ceiling_pp': ceiling_pp,
        'ceiling_rep': ceiling_rep,
        'headroom_pp': headroom_pp,
        'pct_at_r1': pct_at_r1,
        'docs': triad,
        'all_reps': rows,
    })
    print(f"  cls={classical:.4f}  r1={r1_adv:6.2f}pp  ceiling={ceiling_pp:6.2f}pp@r{ceiling_rep}  "
          f"headroom=+{headroom_pp:5.2f}pp  ({pct_at_r1:5.1f}% at r1)")

dt = time.time() - t_total_0
print(f'\n[conjecture] total wall: {dt:.2f}s ({len(results)*len(REPS_VALUES)} sim runs)')

# Pearson correlation between classical and headroom
def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    dy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / (dx * dy) if dx * dy > 0 else float('nan')

cls_arr = [r['classical'] for r in results]
hr_arr = [r['headroom_pp'] for r in results]
ceil_arr = [r['ceiling_pp'] for r in results]
r1_arr = [r['r1_adv_pp'] for r in results]

corr_cls_hr = pearson(cls_arr, hr_arr)
corr_cls_ceiling = pearson(cls_arr, ceil_arr)
corr_cls_r1 = pearson(cls_arr, r1_arr)

print(f'\n[conjecture] Pearson correlations:')
print(f'  classical vs headroom: {corr_cls_hr:+.4f}')
print(f'  classical vs ceiling:  {corr_cls_ceiling:+.4f}')
print(f'  classical vs r=1 adv:  {corr_cls_r1:+.4f}')

OUT = PROJ_ROOT / 'outputs' / 'conjecture-classical-vs-headroom.json'
OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.conjecture-classical-headroom.v1',
    'pool_size': len(POOL),
    'n_triads': len(results),
    'reps_swept': REPS_VALUES,
    'results': results,
    'correlations': {
        'pearson_classical_vs_headroom': corr_cls_hr,
        'pearson_classical_vs_ceiling': corr_cls_ceiling,
        'pearson_classical_vs_r1_adv': corr_cls_r1,
    },
    'conjecture': 'higher classical baseline -> more sim headroom above r=1',
    'verdict_hint': 'STRONG support if pearson_classical_vs_headroom > +0.7; WEAK if 0.4-0.7; refuted if < 0.4',
    'note': 'Sim-only across 12 triads at varying classical percentiles. Zero cloud burn.',
}, indent=2), encoding='utf-8')
print(f'[conjecture] wrote {OUT}')
