"""Iter 45 — which triads favor K=8 ANGLE vs ZZ-FM r=1?

Author: RKOJ-ELENO :: 2026-05-24

Iter 44 established K=8 ANGLE dominates ZZ-FM r=1 in sim on the AVERAGE
(65× more QBC, +1.1pp max advantage). But the comparison was aggregate.
This iter asks: for a SPECIFIC triad, which encoding wins?

Method:
  - Union of top-100 QBC triads under K=8 ANGLE and ZZ-FM r=1
  - For each triad: measure adv under BOTH encodings
  - Compute Δ = K8_ANGLE_adv - ZZ_FM_r1_adv
  - Bucket triads by Δ sign → look for structural correlates

Output: outputs/encoding-preference-sweep.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PROJ_ROOT = Path(__file__).resolve().parent
SANCTUM_ROOT = PROJ_ROOT.parent.parent
SERAPHIM_TOOL = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
sys.path.insert(0, str(SERAPHIM_TOOL))

from memory_kernel import find_qbc_triads, _sim_inversion_overlap, _thetas_for_inversion, _load_brain_entry, _tfidf_vectors  # type: ignore

print('[iter45] computing K=8 ANGLE top-100 and ZZ-FM r=1 top-100...')
t0 = time.time()
r_k8 = find_qbc_triads(encoding='angle', k=8, reps=1, top_n=100, corpus_mode='pool')
r_zz = find_qbc_triads(encoding='zzfm', k=4, reps=1, top_n=100, corpus_mode='pool')
print(f'  K=8 ANGLE: {r_k8["qbc_count"]} QBC total; top-100 surfaced')
print(f'  ZZ-FM r=1: {r_zz["qbc_count"]} QBC total; top-100 surfaced')

# Union of doc-tuples (sorted to dedupe)
union = {}
for t in r_k8['top_n_triads']:
    key = tuple(sorted(t['docs']))
    union[key] = {'docs': t['docs'], 'k8_adv': t['advantage'], 'classical': t['classical_off_diag_mean']}
for t in r_zz['top_n_triads']:
    key = tuple(sorted(t['docs']))
    if key in union:
        union[key]['zz_adv'] = t['advantage']
    else:
        union[key] = {'docs': t['docs'], 'zz_adv': t['advantage'], 'classical': t['classical_off_diag_mean']}

# For triads only in ONE top-100, compute the missing advantage under the OTHER encoding.
# Re-use find-qbc's pool exactly so TF-IDF vectors match.
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}
BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
files = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
topics = {}
for f in files:
    topics.setdefault(f.split('-')[0], []).append(f)
pool = []
for prefix, group in sorted(topics.items()):
    pool.extend(group[:4])
print(f'  pool size: {len(pool)}')

docs_all = [_load_brain_entry(f) for f in pool]
tfidf = _tfidf_vectors(docs_all)
doc_idx = {f: i for i, f in enumerate(pool)}

def sim_for(triad_docs, encoding, k, reps=1):
    idxs = [doc_idx[d] for d in triad_docs]
    thetas_list = [_thetas_for_inversion(tfidf[i], k) for i in idxs]
    pair_sims = []
    for ii in range(3):
        for jj in range(ii+1, 3):
            pair_sims.append(_sim_inversion_overlap(thetas_list[ii], thetas_list[jj], encoding, k, reps))
    return sum(pair_sims) / len(pair_sims)

def classical_for(triad_docs):
    from memory_kernel import _classical_cosine  # type: ignore
    idxs = [doc_idx[d] for d in triad_docs]
    pair_cls = []
    for ii in range(3):
        for jj in range(ii+1, 3):
            pair_cls.append(_classical_cosine(tfidf[idxs[ii]], tfidf[idxs[jj]]))
    return sum(pair_cls) / len(pair_cls)

print(f'\n[iter45] computing both-encoding advantages for {len(union)} unique triads in union...')
n_filled = 0
for key, data in union.items():
    cl = data['classical']
    if 'k8_adv' not in data:
        sim = sim_for(data['docs'], 'angle', 8, 1)
        data['k8_adv'] = cl - sim
        n_filled += 1
    if 'zz_adv' not in data:
        sim = sim_for(data['docs'], 'zzfm', 4, 1)
        data['zz_adv'] = cl - sim
        n_filled += 1
    data['delta_k8_minus_zz'] = data['k8_adv'] - data['zz_adv']

print(f'  filled {n_filled} missing advantage values')
dt = time.time() - t0
print(f'  total: {dt:.2f}s')

# Bucket by Δ sign
k8_wins = [d for d in union.values() if d['delta_k8_minus_zz'] > 0]
zz_wins = [d for d in union.values() if d['delta_k8_minus_zz'] < 0]
ties = [d for d in union.values() if abs(d['delta_k8_minus_zz']) < 1e-6]

print(f'\n[iter45] bucket summary:')
print(f'  K=8 ANGLE wins: {len(k8_wins)}  ({100*len(k8_wins)/len(union):.1f}%)')
print(f'  ZZ-FM r=1 wins: {len(zz_wins)}  ({100*len(zz_wins)/len(union):.1f}%)')
print(f'  ties:           {len(ties)}')

# Mean / extremes by bucket
def stats(triads, label):
    if not triads: return
    cls = [t['classical'] for t in triads]
    deltas = [t['delta_k8_minus_zz'] for t in triads]
    print(f'  {label}:')
    print(f'    classical: min={min(cls):.4f}  max={max(cls):.4f}  mean={sum(cls)/len(cls):.4f}')
    print(f'    delta:     min={min(deltas):+.4f}  max={max(deltas):+.4f}  mean={sum(deltas)/len(deltas):+.4f}')

stats(k8_wins, 'K=8 wins')
stats(zz_wins, 'ZZ-FM wins')

# Extreme cases — top-3 by K8 lead and top-3 by ZZ lead
sorted_by_delta = sorted(union.values(), key=lambda d: d['delta_k8_minus_zz'])
print('\n  Top-3 triads where ZZ-FM r=1 wins most (most negative delta):')
for t in sorted_by_delta[:3]:
    print(f"    Δ={t['delta_k8_minus_zz']:+.4f}  cl={t['classical']:.4f}  k8={t['k8_adv']:+.4f}  zz={t['zz_adv']:+.4f}")
    print(f"      {' + '.join(d.replace('.md','')[:35] for d in t['docs'])}")

print('\n  Top-3 triads where K=8 ANGLE wins most (most positive delta):')
for t in sorted_by_delta[-3:][::-1]:
    print(f"    Δ={t['delta_k8_minus_zz']:+.4f}  cl={t['classical']:.4f}  k8={t['k8_adv']:+.4f}  zz={t['zz_adv']:+.4f}")
    print(f"      {' + '.join(d.replace('.md','')[:35] for d in t['docs'])}")

# Pearson: does classical predict the sign of delta?
def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    dy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / (dx * dy) if dx * dy > 0 else float('nan')

all_cls = [t['classical'] for t in union.values()]
all_delta = [t['delta_k8_minus_zz'] for t in union.values()]
all_k8 = [t['k8_adv'] for t in union.values()]
all_zz = [t['zz_adv'] for t in union.values()]
print(f'\n[iter45] Pearson correlations across all {len(union)} triads:')
print(f"  classical vs delta(k8-zz): {pearson(all_cls, all_delta):+.4f}")
print(f"  classical vs k8_adv:       {pearson(all_cls, all_k8):+.4f}")
print(f"  classical vs zz_adv:       {pearson(all_cls, all_zz):+.4f}")
print(f"  k8_adv vs zz_adv:          {pearson(all_k8, all_zz):+.4f}")

OUT = PROJ_ROOT / 'outputs' / 'encoding-preference-sweep.json'
OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.encoding-preference.v1',
    'pool_size': len(pool),
    'n_union': len(union),
    'k8_wins_count': len(k8_wins),
    'zz_wins_count': len(zz_wins),
    'ties_count': len(ties),
    'pearson_classical_vs_delta': pearson(all_cls, all_delta),
    'pearson_classical_vs_k8': pearson(all_cls, all_k8),
    'pearson_classical_vs_zz': pearson(all_cls, all_zz),
    'pearson_k8_vs_zz': pearson(all_k8, all_zz),
    'triads': list(union.values()),
}, indent=2), encoding='utf-8')
print(f'\n[iter45] wrote {OUT}')
