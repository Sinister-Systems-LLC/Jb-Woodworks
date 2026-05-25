"""Iter 101 - Quantum-expand Option 2: Snap-EMU rule corpus QBC sweep.

Author: RKOJ-ELENO :: 2026-05-24

Operator authorized 10s real-QPU for verification (paired w/ Kernel-APK run).
This script does the SIM-only sweep first to identify top-QBC triad,
then real-QPU verify follows via run-real-qpu-corpus-triad.py.

Corpus: 46 living-mds + 53 snap-signer-tree docs = 99 docs, ~3.2 MB.

Question: 3 Snap signer/living-md rules forming a conflict triangle?
Quantum kernel catches semantic-related rules with low lexical overlap.

Zero cloud burn for THIS script. Read-only TF-IDF + sim sweep.
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

EMU_LIVING = SANCTUM_ROOT / 'projects' / 'sinister-snap-emu' / 'source' / 'living-mds'
EMU_SIGNER = SANCTUM_ROOT / 'projects' / 'sinister-snap-emu' / 'source' / 'snap-signer-tree' / 'docs'

t0 = time.time()
docs_paths = []
docs_paths.extend(sorted(EMU_LIVING.glob('*.md')))
docs_paths.extend(sorted(EMU_SIGNER.glob('*.md')))
print(f'Snap-EMU corpus: {len(docs_paths)} docs')
print(f'  living-mds   : {sum(1 for p in docs_paths if p.parent.name == "living-mds")}')
print(f'  signer-tree  : {sum(1 for p in docs_paths if p.parent.name == "docs")}')

if len(docs_paths) < 3:
    print('Not enough docs. Exiting.')
    sys.exit(0)

doc_names = [str(p.relative_to(SANCTUM_ROOT)).replace('\\', '/') for p in docs_paths]
texts = [p.read_text(encoding='utf-8', errors='replace') for p in docs_paths]

print(f'Loaded {len(texts)} docs in {time.time()-t0:.1f}s')

t1 = time.time()
tfidf = _tfidf_vectors(texts)
print(f'TF-IDF built in {time.time()-t1:.1f}s')

N = len(docs_paths)

t2 = time.time()
pair_cl = [[0.0] * N for _ in range(N)]
pair_sim = [[0.0] * N for _ in range(N)]
thetas = [_thetas_for_inversion(v, 4) for v in tfidf]
print(f'Thetas built in {time.time()-t2:.1f}s. Pair-kernel sweep starting (C({N},2)={N*(N-1)//2} pairs)...')

t3 = time.time()
for i in range(N):
    for j in range(i + 1, N):
        pair_cl[i][j] = pair_cl[j][i] = _classical_cosine(tfidf[i], tfidf[j])
        pair_sim[i][j] = pair_sim[j][i] = _sim_inversion_overlap(thetas[i], thetas[j], 'zzfm', 4, 1)
    if (i+1) % 10 == 0:
        elapsed = time.time() - t3
        rate = (i+1) / elapsed if elapsed > 0 else 0
        eta = (N - i - 1) / rate if rate > 0 else 0
        print(f'  pair-row {i+1}/{N}  ({elapsed:.0f}s elapsed, ~{eta:.0f}s eta)')

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
print(f'Total triads in Snap-EMU corpus: {total_triads}  (C({N},3))')
print(f'QBC count (sim < classical): {qbc} ({100*qbc/total_triads:.2f}%)')
print(f'Max advantage: {scores[0][0]*100:+.2f}pp')
print(f'Median advantage: {scores[len(scores)//2][0]*100:+.2f}pp')
print()

# Top-10 QBC triads
print('Top-10 QBC triads:')
for rank, (adv, cl, sim, idx) in enumerate(scores[:10], 1):
    if adv <= 0:
        break
    print(f'  #{rank}  adv=+{adv*100:.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {doc_names[i]}')

# Top-5 anti-QBC (most-aligned)
anti_scores = sorted(scores)
print()
print('Top-5 anti-QBC triads (aligned by feature space):')
for rank, (adv, cl, sim, idx) in enumerate(anti_scores[:5], 1):
    print(f'  #{rank}  adv={adv*100:+.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {doc_names[i]}')

# Top-5 highest-classical
by_cl = sorted(scores, key=lambda x: x[1], reverse=True)
print()
print('Top-5 highest-classical triads (most-overlapping by TF-IDF):')
for rank, (adv, cl, sim, idx) in enumerate(by_cl[:5], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  adv={adv*100:+.2f}pp')
    for i in idx:
        print(f'         {doc_names[i]}')

OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'snap-emu-corpus-qbc-iter101.json'

OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.snap-emu-corpus-qbc.v1',
    'corpus_name': 'snap-emu (living-mds + snap-signer-tree/docs)',
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
         'doc_indices': list(s[3]),
         'docs': [doc_names[i] for i in s[3]]}
        for r, s in enumerate(scores[:10]) if s[0] > 0
    ],
    'top5_anti_qbc': [
        {'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'doc_indices': list(s[3]),
         'docs': [doc_names[i] for i in s[3]]}
        for s in anti_scores[:5]
    ],
    'top5_highest_classical': [
        {'classical': s[1], 'sim': s[2], 'advantage_pp': s[0] * 100,
         'doc_indices': list(s[3]),
         'docs': [doc_names[i] for i in s[3]]}
        for s in by_cl[:5]
    ],
    'wall_seconds': time.time() - t0,
}, indent=2), encoding='utf-8')

print()
print(f'[saved] {OUT}')
print(f'[total wall] {time.time()-t0:.1f}s')
