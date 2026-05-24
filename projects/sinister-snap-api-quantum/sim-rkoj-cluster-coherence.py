"""Iter 98 — Quantum-expand Option 1: RKOJ-cluster topical-coherence audit.

Author: RKOJ-ELENO :: 2026-05-24

Per iter-97 quantum-expand recommendation: validate find-qbc on a small (N≈16)
single-topic corpus subset. The rkoj-* prefix in `_shared-memory/knowledge/`
contains ~16 docs covering different aspects of the RKOJ workbench. Question:
do any 3 of them form a quantum-discriminable triad? If so, the triad
identifies a "structural fault line" inside the rkoj doctrine — either:
  - Genuinely-different aspects that should stay distinct (healthy)
  - Internally-contradictory pairs requiring a tiebreaker doctrine entry (action)

Zero cloud burn. Read-only TF-IDF + sim sweep.
"""
from __future__ import annotations

import json
import sys
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
    _load_brain_entry, _tfidf_vectors, _classical_cosine,
    _thetas_for_inversion, _sim_inversion_overlap,
)

BRAIN_DIR = SANCTUM_ROOT / '_shared-memory' / 'knowledge'
SKIP = {'README.md', '_INDEX.md', '_TEMPLATE.md'}

# Filter brain to rkoj-* prefix
all_files = sorted(p.name for p in BRAIN_DIR.glob('*.md') if p.name not in SKIP)
rkoj_files = [f for f in all_files if f.startswith('rkoj-')]
print(f'rkoj-* docs found: {len(rkoj_files)}')

if len(rkoj_files) < 3:
    print('Not enough rkoj-* docs for triad analysis. Exiting.')
    sys.exit(0)

# Build TF-IDF over rkoj subset (smaller vocab; cleaner signal for this cluster)
docs = [_load_brain_entry(f) for f in rkoj_files]
tfidf = _tfidf_vectors(docs)
N = len(rkoj_files)

# Compute pair classical + pair sim for all ZZ-FM r=1 K=4 (production recipe)
pair_cl = [[0.0] * N for _ in range(N)]
pair_sim = [[0.0] * N for _ in range(N)]
thetas = [_thetas_for_inversion(v, 4) for v in tfidf]
for i in range(N):
    for j in range(i + 1, N):
        pair_cl[i][j] = pair_cl[j][i] = _classical_cosine(tfidf[i], tfidf[j])
        pair_sim[i][j] = pair_sim[j][i] = _sim_inversion_overlap(thetas[i], thetas[j], 'zzfm', 4, 1)

# Enumerate triads + score by (classical_off_diag - sim_off_diag) = QBC advantage
scores = []
for i, j, k in combinations(range(N), 3):
    cl_off = (pair_cl[i][j] + pair_cl[i][k] + pair_cl[j][k]) / 3
    sim_off = (pair_sim[i][j] + pair_sim[i][k] + pair_sim[j][k]) / 3
    adv = cl_off - sim_off
    scores.append((adv, cl_off, sim_off, (i, j, k)))
scores.sort(reverse=True)

total_triads = len(scores)
qbc = sum(1 for s in scores if s[0] > 0)
print(f'Total triads in rkoj-cluster: {total_triads}  (C({N},3) = {N*(N-1)*(N-2)//6})')
print(f'QBC count (sim < classical): {qbc} ({100*qbc/total_triads:.2f}%)')
print(f'Max advantage: {scores[0][0]*100:+.2f}pp')
print(f'Median advantage: {scores[len(scores)//2][0]*100:+.2f}pp')
print()

# Top-5 QBC triads
print('Top-5 QBC triads (sim < classical → quantum kernel adds discrimination):')
for rank, (adv, cl, sim, idx) in enumerate(scores[:5], 1):
    if adv <= 0:
        break
    print(f'  #{rank}  adv=+{adv*100:.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {rkoj_files[i]}')
    print()

# Top-3 anti-QBC triads (sim > classical → quantum kernel HURTS, doctrine alignment)
anti_scores = sorted(scores)  # most-negative-first
print('Top-3 anti-QBC triads (sim > classical → these docs are ALIGNED in feature space; healthy doctrine):')
for rank, (adv, cl, sim, idx) in enumerate(anti_scores[:3], 1):
    print(f'  #{rank}  adv={adv*100:+.2f}pp  cl={cl:.4f}  sim={sim:.4f}')
    for i in idx:
        print(f'         {rkoj_files[i]}')
    print()

# Highest-classical triads (most-similar by TF-IDF — operator should know about these)
print('Top-3 highest-classical triads (most-overlapping by TF-IDF; potential redundancy):')
by_cl = sorted(scores, key=lambda x: x[1], reverse=True)
for rank, (adv, cl, sim, idx) in enumerate(by_cl[:3], 1):
    print(f'  #{rank}  cl={cl:.4f}  sim={sim:.4f}  adv={adv*100:+.2f}pp')
    for i in idx:
        print(f'         {rkoj_files[i]}')
    print()

# Save JSON output
OUT_DIR = PROJ_ROOT / 'outputs'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / 'rkoj-cluster-coherence-iter98.json'
OUT.write_text(json.dumps({
    'schema': 'sinister-snap-api-quantum.rkoj-cluster-coherence.v1',
    'n_docs': N,
    'doc_names': rkoj_files,
    'total_triads': total_triads,
    'qbc_count': qbc,
    'qbc_pct': qbc / total_triads * 100,
    'max_advantage_pp': scores[0][0] * 100,
    'median_advantage_pp': scores[len(scores)//2][0] * 100,
    'top5_qbc': [
        {'rank': r + 1, 'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'docs': [rkoj_files[i] for i in s[3]]}
        for r, s in enumerate(scores[:5]) if s[0] > 0
    ],
    'top3_anti_qbc': [
        {'advantage_pp': s[0] * 100, 'classical': s[1], 'sim': s[2],
         'docs': [rkoj_files[i] for i in s[3]]}
        for s in anti_scores[:3]
    ],
    'top3_highest_classical': [
        {'classical': s[1], 'sim': s[2], 'advantage_pp': s[0] * 100,
         'docs': [rkoj_files[i] for i in s[3]]}
        for s in by_cl[:3]
    ],
}, indent=2), encoding='utf-8')
print(f'[saved] {OUT}')
