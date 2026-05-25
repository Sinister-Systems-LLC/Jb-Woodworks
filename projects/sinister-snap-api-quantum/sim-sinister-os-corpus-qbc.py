"""Iter 101 - Sinister-OS corpus QBC sweep (operator-added 3rd lane).

Author: RKOJ-ELENO :: 2026-05-24

Operator (verbatim 2026-05-24): 'reviwe the kernel apk, snap api emu and sinister os
and see how you can help them with our quantum tools and telll them a plan of what
they can do to use them. with 10 seconds each'.

Corpus: projects/sinister-os/ — every .md down to depth 4. ~23 docs.
C(23,3) = 1771 triads. Zero cloud burn for this sweep.
"""
from __future__ import annotations

import json
import sys
import time
from itertools import combinations
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
except Exception:
    pass

PROJ_ROOT = Path(__file__).resolve().parent
SANCTUM_ROOT = PROJ_ROOT.parent.parent
SERAPHIM_TOOL = SANCTUM_ROOT / 'tools' / 'sinister-seraphim'
sys.path.insert(0, str(SERAPHIM_TOOL))

from memory_kernel import (  # type: ignore
    _tfidf_vectors, _classical_cosine,
    _thetas_for_inversion, _sim_inversion_overlap,
)

OS_ROOT = SANCTUM_ROOT / 'projects' / 'sinister-os'

t0 = time.time()
docs_paths = []
for p in sorted(OS_ROOT.rglob('*.md')):
    rel = p.relative_to(OS_ROOT)
    depth = len(rel.parts) - 1  # 0 = top-level
    if depth > 3:
        continue
    docs_paths.append(p)

print(f'Sinister-OS corpus: {len(docs_paths)} docs')
for p in docs_paths:
    print(f'  {p.relative_to(OS_ROOT)}')

if len(docs_paths) < 3:
    print('Not enough docs. Exiting.')
    sys.exit(0)

doc_names = [str(p.relative_to(SANCTUM_ROOT)).replace('\\', '/') for p in docs_paths]
texts = [p.read_text(encoding='utf-8', errors='replace') for p in docs_paths]

print(f'\nLoaded {len(texts)} docs in {time.time()-t0:.1f}s')

t1 = time.time()
tfidf = _tfidf_vectors(texts)
print(f'TF-IDF built in {time.time()-t1:.1f}s')

N = len(docs_paths)

t2 = time.time()
pair_cl = [[0.0] * N for _ in range(N)]
pair_sim = [[0.0] * N for _ in range(N)]
thetas = [_thetas_for_inversion(v, 4) for v in tfidf]
print(f'Thetas built in {time.time()-t2:.1f}s. Pair-kernel sweep starting (C({N},2)={N*(N-1)//2})...')

t3 = time.time()
for i in range(N):
    for j in range(i + 1, N):
        pair_cl[i][j] = pair_cl[j][i] = _classical_cosine(tfidf[i], tfidf[j])
        pair_sim[i][j] = pair_sim[j][i] = _sim_inversion_overlap(thetas[i], thetas[j], 'zzfm', 4, 1)
print(f'Pair sweep done in {time.time()-t3:.1f}s')

t4 = time.time()
scores = []
for i, j, k in combinations(range(N), 3):
    cl_off = (pair_cl[i][j] + pair_cl[i][k] + pair_cl[j][k]) / 3
    sim_off = (pair_sim[i][j] + pair_sim[i][k] + pair_sim[j][k]) / 3
    adv = cl_off - sim_off
    scores.append((adv, cl_off, sim_off, (i, j, k)))
scores.sort(reverse=True)
print(f'Triad enumeration done in {time.time()-t4:.1f}s. Total triads: {len(scores)}')

total_triads = len(scores)
qbc = sum(1 for s in scores if s[0] > 0)
print()
print(f'Total triads in Sinister-OS corpus: {total_triads}  (C({N},3))')
print(f'QBC count (sim < classical): {qbc} ({100*qbc/total_triads:.2f}%)')
print(f'Max advantage: {scores[0][0]*100:+.2f}pp')
print(f'Median advantage: {scores[len(scores)//2][0]*100:+.2f}pp')
print()

print('Top-10 QBC triads:')
for rank, (adv, cl, sim, idx) in enumerate(scores[:10], 1):
    if adv <= 0:
        break
    print(f'  #{rank}  adv=+{adv*100:.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {doc_names[i]}')

anti_scores = sorted(scores)
print()
print('Top-5 anti-QBC triads:')
for rank, (adv, cl, sim, idx) in enumerate(anti_scores[:5], 1):
    print(f'  #{rank}  adv={adv*100:+.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {doc_names[i]}')

by_cl = sorted(scores, key=lambda x: x[1], reverse=True)
print()
print('Top-5 highest-classical triads:')
for rank, (adv, cl, sim, idx) in enumerate(by_cl[:5], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  adv={adv*100:+.2f}pp')
    for i in idx:
        print(f'         {doc_names[i]}')

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'sinister-os-corpus-qbc-iter101.json'

OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.sinister-os-corpus-qbc.v1',
    'corpus_name': 'sinister-os (all .md depth<=3)',
    'n_docs': N,
    'doc_names': doc_names,
    'sim_variant': 'zzfm-r1-K4',
    'total_triads': total_triads,
    'qbc_count': qbc,
    'qbc_pct': qbc / total_triads * 100 if total_triads else 0,
    'max_advantage_pp': scores[0][0] * 100,
    'median_advantage_pp': scores[len(scores)//2][0] * 100,
    'top10_qbc': [
        {'rank': r + 1, 'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'doc_indices': list(s[3]), 'docs': [doc_names[i] for i in s[3]]}
        for r, s in enumerate(scores[:10]) if s[0] > 0
    ],
    'top5_anti_qbc': [
        {'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'doc_indices': list(s[3]), 'docs': [doc_names[i] for i in s[3]]}
        for s in anti_scores[:5]
    ],
    'top5_highest_classical': [
        {'classical': s[1], 'sim': s[2], 'advantage_pp': s[0] * 100,
         'doc_indices': list(s[3]), 'docs': [doc_names[i] for i in s[3]]}
        for s in by_cl[:5]
    ],
    'wall_seconds': time.time() - t0,
}, indent=2), encoding='utf-8')

print()
print(f'[saved] {OUT}')
print(f'[total wall] {time.time()-t0:.1f}s')
